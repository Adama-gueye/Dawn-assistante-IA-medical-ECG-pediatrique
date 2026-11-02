from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import verify_password, hash_password, create_access_token
from app.deps import get_current_user
from app import models, schemas

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def se_connecter(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    seConnecter() — authentifie un Utilisateur (Administrateur ou Medecin)
    par email + mot de passe, quel que soit son role.
    """
    user = db.query(models.Utilisateur).filter(models.Utilisateur.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    if not user.est_actif:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte desactive")

    token = create_access_token({"sub": str(user.id), "role": user.type})
    return schemas.Token(access_token=token, role=user.type)


@router.post("/logout")
def se_deconnecter(current_user: models.Utilisateur = Depends(get_current_user)):
    """
    seDeconnecter() — cote JWT stateless, la deconnexion reelle se fait en
    supprimant le token cote client. Cet endpoint existe pour la symetrie
    avec le diagramme et pourra plus tard gerer une liste de revocation.
    """
    return {"detail": "Deconnecte"}


@router.get("/me", response_model=schemas.ProfilOut)
def whoami(current_user: models.Utilisateur = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.ProfilOut)
def modifier_profil(
    payload: schemas.ProfilUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """
    Modifie nom / prenom (tous roles) et specialite (medecin uniquement).
    L'email (identifiant de connexion) et le numero d'ordre ne se changent pas ici.
    """
    data = payload.model_dump(exclude_unset=True)
    if "specialite" in data:
        if current_user.type != "medecin":
            raise HTTPException(status_code=400, detail="La specialite ne concerne que les medecins")
        current_user.specialite = data.pop("specialite")
    for champ, valeur in data.items():
        if valeur is not None:
            setattr(current_user, champ, valeur.strip())
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/changer-mot-de-passe")
def changer_mot_de_passe(
    payload: schemas.ChangerMotDePasse,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Change le mot de passe apres verification de l'ancien (400 si incorrect, pour ne pas deconnecter le client)."""
    if not verify_password(payload.ancien_mot_de_passe, current_user.mot_de_passe):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    if payload.nouveau_mot_de_passe == payload.ancien_mot_de_passe:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit etre different de l'ancien")
    if len(payload.nouveau_mot_de_passe.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Mot de passe trop long (72 octets maximum)")
    current_user.mot_de_passe = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return {"detail": "Mot de passe mis a jour"}
