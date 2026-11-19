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


# --- Plafond de file d'attente du fournisseur (panne du 16 novembre 2026, semaine 2026-S46) -----

class FileLimitee(FauxLot):
    """Comme OpenAI le 16/11/2026 : un lot plus gros que le plafond de la file d'attente est refusé."""
    plafond = 0
    etape = None          # si renseignée, seuls les lots de cette étape sont soumis au plafond
    en_file = []          # nombre de lots déjà en attente au moment de chaque soumission

    @staticmethod
    def taille(requetes):
        return sum(ia.estimer_jetons(r["consigne"] + r["contenu"]) for r in requetes)

    def soumettre_lot(self, requetes, modele, description=""):
        FileLimitee.en_file.append(sum(1 for lot in FauxLot.soumis.values() if lot["vu"] <= 1 and not lot.get("refuse")))
        return super().soumettre_lot(requetes, modele, description)

    def etat_lot(self, lot_id):
        lot = FauxLot.soumis[lot_id]
        concerne = self.etape is None or lot["requetes"][0]["id"].startswith(self.etape)
        if concerne and self.taille(lot["requetes"]) > self.plafond:
            lot["refuse"] = True
            return "echec", {"id": lot_id, "status": "failed",
                             "errors": {"data": [{"code": "token_limit_exceeded"}]}}
        return super().etat_lot(lot_id)


def derouler(site, **reglages):
    """Fait tourner la veille d'heure en heure, comme GitHub Actions, jusqu'à la fin ou 40 lancements."""
    v = None
    for n in range(40):
        v = nouvelle_veille(site, maintenant=datetime(2026, 11, 2 + n // 14, 6 + n % 14, 17, tzinfo=TZ),
                            mode="lot", **reglages)
        v.avancer()
        if v.etat["etape"] == "termine":
            break
    return v


def test_decouper_en_paquets():
    reqs = [{"id": str(n), "consigne": "c" * 30, "contenu": "x" * 270} for n in range(10)]   # 100 jetons chacune
    assert [len(p) for p in run.decouper_en_paquets(reqs, 250)] == [2, 2, 2, 2, 2]
    assert [len(p) for p in run.decouper_en_paquets(reqs, 1000)] == [10]
    assert [len(p) for p in run.decouper_en_paquets(reqs, None)] == [10]
    assert [len(p) for p in run.decouper_en_paquets(reqs, 50)] == [1] * 10      # une requête trop grosse part seule
    assert [len(p) for p in run.decouper_en_paquets(reqs, 600)] == [5, 5]       # tailles voisines, pas [6, 4]
    assert [len(p) for p in run.decouper_en_paquets(reqs, 900)] == [5, 5]       # pas [9, 1]
    assert all(sum(100 for _ in p) <= 600 for p in run.decouper_en_paquets(reqs, 600))
    assert [r["id"] for p in run.decouper_en_paquets(reqs, 250) for r in p] == [str(n) for n in range(10)]


def test_gros_lot_decoupe_sous_le_plafond(env, monkeypatch):
    """Le lot de rédaction dépasse le plafond : découpé en lots plus petits, il passe au tarif différé."""
    FauxLot.soumis, FileLimitee.en_file = {}, []
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: FileLimitee(str(REPONSES)))
    monkeypatch.setattr(run.collecte, "collecter", lambda s, c, journal=print: list(REFS))
    modele = charger_config()["ia"]["modele_redaction"]
    # Taille d'une requête de rédaction de la démonstration, pour régler plafond et découpage.
    v0 = nouvelle_veille(env, mode="direct")
    while v0.etat["etape"] != "redaction":
        getattr(v0, f"etape_{v0.etat['etape']}")()
    refs = {r["id"]: r for r in v0._lire("references.json", [])}
    selection, _ = run.etapes.selectionner(v0._lire("tri.json", {}), 1200)
    reqs = run.etapes.requetes_redaction(selection, refs, v0.libelles, run.charger_consigne("redaction"))
    assert len(reqs) >= 2
    plus_grosse, total = max(FileLimitee.taille([r]) for r in reqs), FileLimitee.taille(reqs)
    for f in (env.parent / "travail").rglob("*"):
        if f.is_file():
            f.unlink()

    FileLimitee.plafond = max(plus_grosse, total - 1)          # le lot entier ne passe pas
    FileLimitee.etape = "redaction"
    v = derouler(env, jetons_max_par_lot={modele: plus_grosse})
    assert v.etat["etape"] == "termine"
    assert json.loads((env / "data" / "semaines" / "2026-S44.json").read_text())["fiches"]
    assert len(v.etat["lots"]["redaction"]["paquets"]) >= 2
    assert all(p["etat"] == "termine" for p in v.etat["lots"]["redaction"]["paquets"])
    assert not any("prix plein" in ligne for ligne in v.etat["journal"])
    assert max(FileLimitee.en_file) == 0                        # jamais deux lots en file en même temps


def test_lot_refuse_deux_fois_passe_en_direct(env, monkeypatch):
    """Panne du 16/11/2026 : un lot refusé deux fois ne fait plus échouer la veille."""
    FauxLot.soumis, FileLimitee.en_file = {}, []
    FileLimitee.plafond, FileLimitee.etape = 0, None            # tout lot est refusé
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: FileLimitee(str(REPONSES)))
    v = derouler(env)
    assert v.etat["etape"] == "termine"
    assert json.loads((env / "data" / "semaines" / "2026-S44.json").read_text())["fiches"]
    assert v.etat["lots"]["redaction"]["paquets"][0]["etat"] == "direct"
    assert any("redaction" in ligne and "prix plein" in ligne for ligne in v.etat["journal"])


def test_etat_d_un_ancien_lancement_reste_lisible(env, monkeypatch):
    """Un état enregistré avant le découpage (un seul lot, clé « id ») est repris sans erreur."""
    FauxLot.soumis, FileLimitee.en_file = {}, []
    FileLimitee.plafond, FileLimitee.etape = 0, None
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: FileLimitee(str(REPONSES)))
    v = nouvelle_veille(env, maintenant=datetime(2026, 11, 2, 6, 17, tzinfo=TZ), mode="lot")
    v.avancer()                                                 # collecte, lot de tri soumis
    lot = v.etat["lots"]["tri"]
    ancien = {"id": lot["paquets"][0]["id"], "tentatives": 2, "nb": lot["nb"],
              "soumis_le": lot["soumis_le"], "cout_estime": lot["cout_estime"]}
    v.etat["lots"]["tri"] = ancien
    v.sauver()
    v = derouler(env)
    assert v.etat["etape"] == "termine"
    assert v.etat["lots"]["tri"]["paquets"][0]["etat"] == "direct"


def test_plafond_depasse_reconnu():
    assert run._plafond_depasse({"errors": {"data": [{"code": "token_limit_exceeded"}]}})
    assert not run._plafond_depasse({"errors": {"data": [{"code": "autre"}]}})
    assert not run._plafond_depasse({"errors": None}) and not run._plafond_depasse({})
    assert not run._plafond_depasse({"errors": "texte inattendu"})


def test_lot_trop_gros_coupe_en_deux_sans_surcout(env, monkeypatch):
    """Sans réglage de taille, un lot refusé pour dépassement du plafond est coupé en deux et passe."""
    FauxLot.soumis, FileLimitee.en_file = {}, []
    FileLimitee.etape = "redaction"
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: FileLimitee(str(REPONSES)))
    # Plafond : la moitié du lot de rédaction passe, le lot entier non.
    v0 = nouvelle_veille(env, mode="direct")
    while v0.etat["etape"] != "redaction":
        getattr(v0, f"etape_{v0.etat['etape']}")()
    refs = {r["id"]: r for r in v0._lire("references.json", [])}
    selection, _ = run.etapes.selectionner(v0._lire("tri.json", {}), 1200)
    reqs = run.etapes.requetes_redaction(selection, refs, v0.libelles, run.charger_consigne("redaction"))
    moitie = len(reqs) // 2
    FileLimitee.plafond = max(FileLimitee.taille(reqs[:moitie]), FileLimitee.taille(reqs[moitie:]))
    assert FileLimitee.taille(reqs) > FileLimitee.plafond
    for f in (env.parent / "travail").rglob("*"):
        if f.is_file():
            f.unlink()

    v = derouler(env, jetons_max_par_lot=None)
    assert v.etat["etape"] == "termine"
    paquets = v.etat["lots"]["redaction"]["paquets"]
    assert [p["etat"] for p in paquets] == ["termine", "termine"] and all(p["divise"] for p in paquets)
    assert any("coupé en deux lots" in ligne for ligne in v.etat["journal"])
    assert not any("prix plein" in ligne for ligne in v.etat["journal"])
    assert "requetes_en_direct_apres_refus" not in v.etat["stats"]


def test_soumission_refusee_deux_fois_passe_en_direct(env, monkeypatch):
    """Le fournisseur refuse la création même du lot : la veille ne reste pas bloquée."""
    class SoumissionRefusee(FauxLot):
        def soumettre_lot(self, requetes, modele, description=""):
            raise RuntimeError("HTTP 400 sur la création du lot")

    FauxLot.soumis = {}
    monkeypatch.setattr(ia, "fournisseur", lambda cfg: SoumissionRefusee(str(REPONSES)))
    v = derouler(env)
    assert v.etat["etape"] == "termine"
    assert json.loads((env / "data" / "semaines" / "2026-S44.json").read_text())["fiches"]
    assert v.etat["lots"]["redaction"]["paquets"][0]["etat"] == "direct"
    assert any("soumission refusée" in ligne for ligne in v.etat["journal"])
    assert v.etat["stats"]["requetes_en_direct_apres_refus"] >= 1
