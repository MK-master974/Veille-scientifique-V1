"""Construit un site de démonstration : le vrai moteur, avec une IA simulée qui rejoue
des fiches rédigées à la main (demo/reponses.json) à partir de publications réelles.

Usage : python scripts/demo.py [dossier_sortie]   (par défaut : apercu/)
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))


def construire(sortie):
    sortie = Path(sortie).resolve()
    travail = Path(tempfile.mkdtemp(prefix="veille-demo-"))
    os.environ.update({
        "VEILLE_TRAVAIL": str(travail),
        "VEILLE_FOURNISSEUR": "demo",
        "VEILLE_REPONSES_DEMO": str(RACINE / "demo" / "reponses.json"),
        "VEILLE_SANS_RESEAU": "1",
    })
    from pipeline.config import charger_catalogue, charger_config
    from pipeline.run import Veille
    from pipeline.semaines import depuis_id
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if sortie.exists():
        shutil.rmtree(sortie)
    shutil.copytree(RACINE / "site", sortie, ignore=shutil.ignore_patterns("data"))

    cfg = charger_config()
    cfg["demonstration"] = True
    cfg["ia"]["mode"] = "direct"
    semaine = depuis_id("2026-S44")
    lundi_matin = datetime(2026, 11, 2, 8, 0, tzinfo=ZoneInfo("Europe/Paris"))
    veille = Veille(semaine, cfg, charger_catalogue(), dossier_site=sortie, maintenant=lundi_matin)
    refs = json.loads((RACINE / "demo" / "references.json").read_text(encoding="utf-8"))
    veille._ecrire("references.json", refs)
    veille.passer("tri")
    veille.avancer()
    rejets = json.loads((travail / semaine.id / "rejets.json").read_text(encoding="utf-8"))
    fiches = json.loads((travail / semaine.id / "fiches.json").read_text(encoding="utf-8"))
    shutil.rmtree(travail, ignore_errors=True)
    return fiches, rejets, veille.etat


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else RACINE / "apercu"
    fiches, rejets, etat = construire(dossier)
    for ligne in etat["journal"]:
        print(ligne)
    print(f"{len(fiches)} fiches publiées, {len(rejets)} écartées")
    for r in rejets:
        print("  écartée :", r["id"], r["motifs"])
    sys.exit(1 if rejets else 0)
