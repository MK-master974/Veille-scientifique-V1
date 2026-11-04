import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from pipeline import collecte, controle, etapes, regles, semaines
from pipeline.config import charger_catalogue, charger_consigne, domaines_du_catalogue

ICI = Path(__file__).parent
TZ = ZoneInfo("Europe/Paris")


# --- semaines ---------------------------------------------------------------------------------

def test_semaine_precedente_lundi_matin():
    s = semaines.semaine_precedente(datetime(2026, 11, 2, 0, 30, tzinfo=TZ))
    assert (s.id, s.lundi, s.dimanche) == ("2026-S44", date(2026, 10, 26), date(2026, 11, 1))


def test_semaine_precedente_dimanche_soir_utc():
    # Dimanche 23 h 30 UTC = lundi 0 h 30 à Paris : on traite bien la semaine qui vient de finir.
    s = semaines.semaine_precedente(datetime(2026, 11, 1, 23, 30, tzinfo=ZoneInfo("UTC")))
    assert s.id == "2026-S44"


def test_aller_retour_identifiant():
    assert semaines.depuis_id("2026-S01").lundi == date(2025, 12, 29)
    assert semaines.depuis_id("2026-S44").dimanche == date(2026, 11, 1)


# --- collecte ---------------------------------------------------------------------------------

def test_requete_pubmed():
    q = collecte.requete_pubmed(semaines.depuis_id("2026-S44"))
    assert "2026/10/26:2026/11/01[edat]" in q
    assert "randomized controlled trial[pt]" in q and "hasabstract" in q
    assert "NOT (retracted publication[pt]" in q


def test_analyse_xml_pubmed():
    refs = collecte.analyser_xml_pubmed((ICI / "echantillon_pubmed.xml").read_text())
    assert [r["pmid"] for r in refs] == ["99000001"]      # rétracté et sans résumé exclus
    r = refs[0]
    assert r["titre"] == "Exercise therapy for chronic low back pain: a systematic review."
    assert r["doi"] == "10.9999/jtp.2026.001"
    assert r["resume"].startswith("BACKGROUND: Chronic")
    assert r["auteurs"] == ["Martin A", "Test Collaboration"]
    assert (r["annee"], r["mois"], r["volume"], r["numero"], r["pages"]) == ("2026", "10", "12", "4", "101-110")
    assert r["mesh"] == ["Low Back Pain"]


# --- règles -----------------------------------------------------------------------------------

@pytest.mark.parametrize("tri,attendu", [
    ({"type_etude": "recommandation"}, "solide"),
    ({"type_etude": "recommandation", "accord_experts": True}, "modere"),
    ({"type_etude": "meta_analyse", "grade": "modere"}, "solide"),
    ({"type_etude": "meta_analyse", "grade": "faible"}, "modere"),
    ({"type_etude": "revue_systematique", "grade": "tres_faible"}, "preliminaire"),
    ({"type_etude": "revue_systematique", "majorite_essais_randomises": True}, "modere"),
    ({"type_etude": "revue_systematique"}, "preliminaire"),
    ({"type_etude": "essai_randomise", "effectif": 240}, "modere"),
    ({"type_etude": "essai_randomise", "effectif": "1 024"}, "modere"),
    ({"type_etude": "essai_randomise", "effectif": 60}, "preliminaire"),
    ({"type_etude": "essai_randomise", "effectif": 20}, None),
    ({"type_etude": "etude_diagnostique", "design_diagnostique": "prospective", "effectif": 150}, "modere"),
    ({"type_etude": "etude_diagnostique", "design_diagnostique": "retrospective"}, "preliminaire"),
])
def test_etiquette_depart(tri, attendu):
    assert regles.etiquette_depart(tri) == attendu


def test_etiquette_jamais_remontee():
    assert regles.plafonner_etiquette("solide", "modere") == "modere"
    assert regles.plafonner_etiquette("preliminaire", "solide") == "preliminaire"
    assert regles.plafonner_etiquette("n'importe quoi", "modere") == "modere"


def test_change_la_pratique_reserve():
    assert regles.verdict_autorise("change_la_pratique", "essai_randomise", "modere") == "a_surveiller"
    assert regles.verdict_autorise("change_la_pratique", "meta_analyse", "modere") == "a_surveiller"
    assert regles.verdict_autorise("change_la_pratique", "meta_analyse", "solide") == "change_la_pratique"
    assert regles.verdict_autorise("change_la_pratique", "recommandation", "modere") == "change_la_pratique"


# --- contrôle des chiffres ---------------------------------------------------------------------

REF = {"id": "pm1", "titre": "Exercise for knee osteoarthritis", "annee": "2026", "pmid": "1",
       "resume": "Twelve trials (n = 1,234) were included. Pain decreased by 1.5 points (95% CI 0.8 to 2.2; "
                 "p < 0.001) at 12 weeks. Two reviewers screened studies.", "mesh": []}


def fiche_valide(**surcharges):
    f = {
        "titre_fr": "Exercice et gonarthrose",
        "etiquette": "solide", "justification_etiquette": "GRADE modéré.",
        "verdict": "confirme",
        "flash": "La douleur baisse de 1,5 point à 12 semaines chez 1 234 patients.",
        "standard": {"resultats": "−1,5 point (IC 95 % 0,8 à 2,2 ; p < 0,001).",
                     "impact_clinique": "Conforte l'exercice en première intention.",
                     "limites": ["Deux évaluateurs seulement."]},
        "complet": {"type": "Méta-analyse", "population": "1 234 patients", "intervention_comparateur": "Exercice",
                    "criteres_jugement": "Douleur", "methode": "12 essais", "grade": "", "limites": []},
        "vulgarise": None, "chiffres_cites": ["1,5", "12", "1 234"], "incertitudes": None,
    }
    f.update(surcharges)
    return f


def test_chiffres_sources_acceptes():
    assert controle.chiffres_non_sources(fiche_valide(), REF) == []


def test_chiffre_invente_rejete():
    f = fiche_valide(flash="La douleur baisse de 2,5 points à 12 semaines.")
    assert controle.chiffres_non_sources(f, REF) == ["flash : 2,5"]


def test_pourcentage_converti_rejete():
    f = fiche_valide(flash="La douleur baisse de 15 % à 12 semaines.")
    assert controle.chiffres_non_sources(f, REF) == ["flash : 15"]


def test_controle_fiche_complete():
    tri = {"type_etude": "meta_analyse", "pertinence": 2, "domaines": ["kine/msk-membre-inf"],
           "etiquette_depart": "modere"}
    fiche, erreurs = controle.controler_fiche(fiche_valide(verdict="change_la_pratique"),
                                              {**REF, "source": "pubmed", "url": "u", "doi": ""}, tri)
    assert erreurs == []
    assert fiche["etiquette"] == "modere"            # plafonnée à l'étiquette de départ
    assert fiche["verdict"] == "a_surveiller"        # « change » interdit sans étiquette solide


def test_controle_structure_incomplete():
    f = fiche_valide()
    f["standard"]["impact_clinique"] = ""
    tri = {"type_etude": "meta_analyse", "pertinence": 2, "domaines": ["kine/sport"], "etiquette_depart": "solide"}
    fiche, erreurs = controle.controler_fiche(f, {**REF, "source": "pubmed", "url": "u"}, tri)
    assert fiche is None and "impact clinique manquant" in erreurs


def test_grande_nouveaute_ajoutee():
    tri = {"type_etude": "recommandation", "pertinence": 3, "domaines": ["kine/sport"], "etiquette_depart": "solide"}
    fiche, _ = controle.controler_fiche(fiche_valide(verdict="change_la_pratique"),
                                        {**REF, "source": "has", "url": "u"}, tri)
    assert "transversal/grandes-nouveautes" in fiche["domaines"]


# --- lecture du tri ---------------------------------------------------------------------------

def test_lire_tri_filtre_domaines_inconnus():
    valides = set(domaines_du_catalogue(charger_catalogue()))
    texte = json.dumps({"inclure": True, "type_etude": "essai_randomise", "pertinence": 2,
                        "domaines": ["kine/sport", "kine/inexistant", "transversal/grandes-nouveautes"],
                        "effectif": 120})
    t = etapes.lire_tri(texte, {"id": "pm1"}, valides, {})
    assert t["domaines"] == ["kine/sport"] and t["etiquette_depart"] == "modere"


def test_lire_tri_effectif_trop_faible():
    valides = set(domaines_du_catalogue(charger_catalogue()))
    texte = '```json\n{"inclure": true, "type_etude": "essai_randomise", "pertinence": 2, ' \
            '"domaines": ["kine/sport"], "effectif": 18}\n```'
    assert etapes.lire_tri(texte, {"id": "pm1"}, valides, {})["inclure"] is False


def test_consigne_tri_contient_catalogue():
    texte = charger_consigne("tri", charger_catalogue())
    assert "kine/msk-rachis : Masso-kinésithérapie > Musculosquelettique — rachis" in texte
    assert "transversal/" not in texte.split("CATALOGUE")[-1]


# --- synthèses --------------------------------------------------------------------------------

def test_synthese_ia_invalide_completee():
    fiches = [
        {"id": "a", "verdict": "change_la_pratique", "titre_fr": "A", "flash": "Effet de 3 points.",
         "standard": {"resultats": ""}},
        {"id": "b", "verdict": "a_surveiller", "titre_fr": "B", "flash": "Signal.", "standard": {"resultats": ""}},
    ]
    texte = json.dumps({"ce_qui_change_la_pratique": [{"id": "b", "phrase": "Mauvais verdict."}],
                        "a_surveiller": [{"id": "b", "phrase": "Un signal de 7 points."}],
                        "remis_en_question": []})
    s, repli = etapes.lire_synthese(texte, fiches)
    assert repli is True
    assert s["ce_qui_change_la_pratique"] == [{"id": "a", "phrase": "Effet de 3 points."}]
    assert s["a_surveiller"] == [{"id": "b", "phrase": "Signal."}]   # « 7 » absent des fiches
