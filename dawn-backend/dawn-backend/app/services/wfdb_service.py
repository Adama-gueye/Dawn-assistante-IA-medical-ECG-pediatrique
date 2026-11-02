"""
Extraction des metadonnees techniques d'un enregistrement WFDB (.hea/.dat).

Ne lit QUE ce qui est garanti present dans tout header WFDB valide (nombre
de derivations, frequence d'echantillonnage, duree) — pas les commentaires
libres (age/sexe), dont le format varie d'un dataset a l'autre et n'est de
toute facon pas fiable en usage reel : l'age/le sexe du patient viennent du
DossierPatient (deja saisis une fois, toujours a jour), pas du fichier ECG.
"""
import os
from dataclasses import dataclass
from typing import BinaryIO

import numpy as np
import pandas as pd
import wfdb


@dataclass
class MetadonneesEcg:
    nb_derivations: int
    frequence_hz: float
    duree_secondes: float


def lire_metadonnees(chemin_base_sans_extension: str) -> MetadonneesEcg:
    """
    `chemin_base_sans_extension` : chemin du record SANS extension, ex.
    "/.../uploads/ecg/<uuid>_P00001_E01" pour les fichiers
    "<uuid>_P00001_E01.hea" et "<uuid>_P00001_E01.dat".
    """
    header = wfdb.rdheader(chemin_base_sans_extension)
    duree = round(header.sig_len / header.fs, 2) if header.fs else 0.0
    return MetadonneesEcg(
        nb_derivations=header.n_sig,
        frequence_hz=float(header.fs),
        duree_secondes=duree,
    )


def csv_vers_wfdb(
    fichier_csv: BinaryIO,
    chemin_base_sans_extension: str,
    frequence_hz: float = 500,
    a_entete: bool = True,
) -> MetadonneesEcg:
    """
    OUTIL DE TEST — convertit un CSV de signal ECG (une colonne par
    derivation, une ligne par echantillon) en une paire WFDB (.hea/.dat),
    pour tester l'analyse ECG de l'app sans attendre le modele final ni
    devoir se procurer de vrais fichiers WFDB.

    Ne PAS utiliser en usage clinique reel : un CSV n'a aucune metadonnee
    fiable, contrairement a un vrai enregistrement WFDB d'appareil.
    """
    df = pd.read_csv(fichier_csv, header=0 if a_entete else None)
    sig_names = [str(c) for c in df.columns] if a_entete else [f"lead_{i + 1}" for i in range(df.shape[1])]
    signal = df.to_numpy(dtype=float)
    if signal.ndim == 1:
        signal = signal.reshape(-1, 1)
    n_sig = signal.shape[1]

    dossier, base = os.path.split(chemin_base_sans_extension)
    wfdb.wrsamp(
        record_name=base,
        fs=frequence_hz,
        units=["mV"] * n_sig,
        sig_name=sig_names,
        p_signal=signal,
        fmt=["16"] * n_sig,
        write_dir=dossier,
    )
    return MetadonneesEcg(
        nb_derivations=n_sig,
        frequence_hz=frequence_hz,
        duree_secondes=round(signal.shape[0] / frequence_hz, 2),
    )
