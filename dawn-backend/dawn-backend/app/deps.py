from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.Utilisateur:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expiree",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.est_actif:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte desactive")
    return user


def require_medecin(user: models.Utilisateur = Depends(get_current_user)) -> models.Medecin:
    if user.type != "medecin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reserve aux medecins")
    return user


def require_administrateur(user: models.Utilisateur = Depends(get_current_user)) -> models.Administrateur:
    if user.type != "administrateur":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reserve aux administrateurs")
    return user
