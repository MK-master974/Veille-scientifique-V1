"""Tests de bout en bout du moteur, sans réseau : IA simulée, données publiées dans un dossier temporaire."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from pipeline import ia, run
from pipeline.config import charger_catalogue, charger_config
from pipeline.semaines import depuis_id

RACINE = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("Europe/Paris")
LUNDI_8H = datetime(2026, 11, 2, 8, 0, tzinfo=TZ)
REFS = json.loads((RACINE / "demo" / "references.json").read_text(encoding="utf-8"))
REPONSES = RACINE / "demo" / "reponses.json"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "DOSSIER_TRAVAIL", tmp_path / "travail")
    monkeypatch.setenv("VEILLE_REPONSES_DEMO", str(REPONSES))
    monkeypatch.setenv("VEILLE_SANS_RESEAU", "1")
    monkeypatch.setattr(run.collecte, "collecter", lambda semaine, cfg, journal=print: list(REFS))
    site = tmp_path / "site"
    (site / "data").mkdir(parents=True)
    return site


def nouvelle_veille(site, maintenant=LUNDI_8H, **reglages):
    cfg = charger_config()
    cfg["ia"].update({"fournisseur": "demo", "mode": "direct", **reglages})
    return run.Veille(depuis_id("2026-S44"), cfg, charger_catalogue(), dossier_site=site, maintenant=maintenant)


def test_chaine_complete_demo(env, monkeypatch):
    monkeypatch.setenv("VEILLE_FOURNISSEUR", "demo")
    v = nouvelle_veille(env)
    v.avancer()
    assert v.etat["etape"] == "notification" and v.publie_ce_lancement
    sem = json.loads((env / "data" / "semaines" / "2026-S44.json").read_text())
    assert len(sem["fiches"]) == 4
    par_id = {f["id"]: f for f in sem["fiches"]}
    assert par_id["pm42951276"]["verdict"] == "remet_en_question"
    assert par_id["pm42029397"]["etiquette"] == "preliminaire"
    # la méta-analyse en réseau part de « solide » (GRADE modéré) et l'IA l'abaisse à « modéré »
    assert par_id["pm42272562"]["etiquette"] == "modere"
    # une recommandation à fort impact qui change la pratique devient une grande nouveauté
    assert "transversal/grandes-nouveautes" in par_id["has8ff2e4eb7c"]["domaines"]
    assert sem["syntheses"]["kine/sport"]["a_surveiller"] == [] and \
        sem["syntheses"]["kine/sport"]["remis_en_question"][0]["id"] == "pm42951276"
    assert sem["syntheses"]["kine/respi"]["nb_fiches"] == 0
    index = json.loads((env / "data" / "index.json").read_text())
    assert index["derniere"] == "2026-S44" and index["annees_recherche"] == [2026]
    assert len(json.loads((env / "data" / "recherche" / "2026.json").read_text())) == 4

    # Lancement suivant avant 7 h 30 : on attend l'heure d'envoi des notifications.
    v2 = nouvelle_veille(env, maintenant=datetime(2026, 11, 3, 6, 0, tzinfo=TZ))
    v2.avancer()
    assert v2.etat["etape"] == "notification"
    v3 = nouvelle_veille(env, maintenant=datetime(2026, 11, 2, 9, 17, tzinfo=TZ))
    v3.avancer()
    assert v3.etat["etape"] == "termine"


def test_chiffre_invente_ecarte(env, monkeypatch, tmp_path):
    reponses = json.loads(REPONSES.read_text())
    reponses["redaction"]["pm42029397"]["flash"] = "Les chutes baissent de 23 % chez 677 personnes."
    faux = tmp_path / "reponses.json"
    faux.write_text(json.dumps(reponses))
    monkeypatch.setenv("VEILLE_REPONSES_DEMO", str(faux))
    monkeypatch.setenv("VEILLE_FOURNISSEUR", "demo")
    v = nouvelle_veille(env)
    v.avancer()
    rejets = json.loads((v.dossier / "rejets.json").read_text())
    assert [r["id"] for r in rejets] == ["pm42029397"]
    assert "23" in rejets[0]["motifs"][0]


def test_collecte_attend_lundi_5h_utc(env, monkeypatch):
    monkeypatch.setenv("VEILLE_FOURNISSEUR", "demo")
    v = nouvelle_veille(env, maintenant=datetime(2026, 11, 2, 0, 30, tzinfo=TZ))
    v.avancer()
    assert v.etat["etape"] == "collecte"


def test_echeance_depassee(env, monkeypatch):
    monkeypatch.setenv("VEILLE_FOURNISSEUR", "demo")
    v = nouvelle_veille(env, maintenant=datetime(2026, 11, 4, 9, 0, tzinfo=TZ))
    with pytest.raises(run.Echec):
        v.avancer()


class FauxLot(ia.FournisseurDemo):
    """Simule le traitement différé d'OpenAI : un lot n'est prêt qu'au lancement suivant."""
    lot_possible = True
    soumis = {}

    def soumettre_lot(self, requetes, modele, description=""):
        ident = f"lot_{len(FauxLot.soumis)}"
        FauxLot.soumis[ident] = {"requetes": requetes, "vu": 0}
        return ident

    def etat_lot(self, lot_id):
        lot = FauxLot.soumis[lot_id]
        lot["vu"] += 1
        return ("termine" if lot["vu"] > 1 else "en_cours"), {"id": lot_id, "request_counts": {}}

    def resultats_lot(self, details):
        return self.direct(FauxLot.soumis[details["id"]]["requetes"], "x")


def test_mode_lot_sur_plusieurs_lancements(env, monkeypatch):
    FauxLot.soumis = {}
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: FauxLot(str(REPONSES)))
    etapes_vues = []
    for heure in range(6, 20):
        v = nouvelle_veille(env, maintenant=datetime(2026, 11, 2, heure, 17, tzinfo=TZ), mode="lot")
        v.avancer()
        etapes_vues.append(v.etat["etape"])
        if v.etat["etape"] == "termine":
            break
    assert etapes_vues[0] == "tri"                 # collecte faite, lot de tri soumis
    assert "redaction" in etapes_vues and "notification" in etapes_vues
    assert etapes_vues[-1] == "termine"
    assert len(FauxLot.soumis) == 3                # tri, rédaction, synthèses
    assert json.loads((env / "data" / "semaines" / "2026-S44.json").read_text())["fiches"]


def test_budget_limite_le_tri(env, monkeypatch):
    monkeypatch.setenv("VEILLE_FOURNISSEUR", "demo")
    v = nouvelle_veille(env, budget_max_usd_semaine=0.0004)
    v.avancer()
    assert v.etat["stats"].get("non_triees_budget", 0) > 0


def test_panne_ia_declenche_une_alerte(env, monkeypatch):
    class Panne(ia.FournisseurDemo):
        def direct(self, requetes, modele, simultanes=8):
            return {r["id"]: (None, {"erreur": "HTTP 400 modèle inconnu"}) for r in requetes}
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: Panne(str(REPONSES)))
    monkeypatch.setattr(run.collecte, "collecter", lambda s, c, journal=print: list(REFS) * 2)
    v = nouvelle_veille(env)
    with pytest.raises(run.Echec, match="modèle inconnu"):
        v.avancer()
    assert not (env / "data" / "semaines" / "2026-S44.json").exists()
