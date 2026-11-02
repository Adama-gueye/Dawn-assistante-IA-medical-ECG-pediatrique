"""
Cree le premier compte Administrateur, necessaire pour pouvoir ensuite
creer des comptes Medecin via l'API (creerCompteMedecin est reserve a
l'Administrateur).

Usage :
    python seed_admin.py
"""
import getpass

from app.database import SessionLocal, Base, engine
from app.security import hash_password
from app import models

Base.metadata.create_all(bind=engine)


def main():
    db = SessionLocal()
    try:
        email = input("Email de l'administrateur : ").strip()
        if db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first():
            print("Un compte existe deja avec cet email.")
            return

        nom = input("Nom : ").strip()
        prenom = input("Prenom : ").strip()
        mot_de_passe = getpass.getpass("Mot de passe : ")

        admin = models.Administrateur(
            nom=nom, prenom=prenom, email=email,
            mot_de_passe=hash_password(mot_de_passe), niveau="super_admin",
        )
        db.add(admin)
        db.commit()
        print(f"Administrateur cree : {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
