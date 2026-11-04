"""Chargement de la configuration, du catalogue et des consignes de l'IA."""
import json
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_PIPELINE = Path(__file__).resolve().parent
DOSSIER_SITE = RACINE / "site"
DOSSIER_TRAVAIL = Path(os.environ.get("VEILLE_TRAVAIL", RACINE / "travail"))


def charger_config(chemin=None):
    chemin = Path(chemin or os.environ.get("VEILLE_CONFIG") or RACINE / "config.json")
    with open(chemin, encoding="utf-8") as f:
        cfg = json.load(f)
    # Les secrets et réglages propres à l'installation passent par l'environnement.
    for cle_env, cle_cfg in (("EMAIL_CONTACT", "email_contact"), ("URL_SITE", "url_site")):
        if os.environ.get(cle_env):
            cfg[cle_cfg] = os.environ[cle_env]
    if os.environ.get("ONESIGNAL_APP_ID"):
        cfg.setdefault("notifications", {})["onesignal_app_id"] = os.environ["ONESIGNAL_APP_ID"]
    return cfg


def charger_catalogue():
    with open(DOSSIER_PIPELINE / "catalogue.json", encoding="utf-8") as f:
        return json.load(f)


def domaines_du_catalogue(catalogue):
    """Renvoie {"kine/msk-rachis": "Masso-kinésithérapie > Musculosquelettique — rachis", ...}."""
    domaines = {}
    for prof in catalogue["professions"]:
        for sc in prof["sous_champs"]:
            domaines[f"{prof['id']}/{sc['id']}"] = f"{prof['nom']} > {sc['nom']}"
    return domaines


def charger_consigne(nom, catalogue=None):
    texte = (DOSSIER_PIPELINE / "prompts" / f"{nom}.txt").read_text(encoding="utf-8")
    if catalogue is not None:
        lignes = "\n".join(f"{k} : {v}" for k, v in domaines_du_catalogue(catalogue).items()
                           if not k.startswith("transversal/"))
        texte = texte.replace("{{CATALOGUE}}", lignes)
    return texte
