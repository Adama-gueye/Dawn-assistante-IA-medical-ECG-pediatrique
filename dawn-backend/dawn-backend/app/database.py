from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# NB: pool_pre_ping evite les connexions mortes apres une periode d'inactivite (utile en dev)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ajouter_colonnes_manquantes():
    """
    create_all() ne modifie jamais une table existante : une colonne ajoutée au modèle (ex. messages_ecg.resultat_json)
    manque alors en base et fait échouer les INSERT. On ajoute ici les colonnes absentes (nullables uniquement, sans risque
    pour les données). Pour des changements plus complexes (renommage, suppression), utiliser Alembic.
    """
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            existantes = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in existantes:
                    continue
                if not col.nullable and col.server_default is None and not col.primary_key:
                    continue  # colonne obligatoire sans défaut : migration manuelle nécessaire
                type_sql = col.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS "{col.name}" {type_sql}'))
