"""Tests de l'étape « plan d'étude » (séance 7), sans réseau ni IA.

Les textes ci-dessous sont fabriqués : ils ne reprennent le texte d'aucun article.
"""
import json

from pipeline import plan_etude as pe
from pipeline import texte
from pipeline.config import charger_consigne

ALTERNE = "Participants were allocated alternately according to their order of referral to the clinic."
RESULTATS = "Pain fell by 12 points in both groups. " * 40


def document(methodes=ALTERNE, nom="Methods", avec_resultats=True):
    blocs = [{"repere": "R", "type": "resume", "nom": "Résumé", "emplacement": "résumé",
              "texte": "This invented trial compared two stimulation currents in 60 women."}]
    if methodes is not None:
        blocs.append({"repere": "S1", "type": "section", "nom": nom, "emplacement": f"section : {nom}", "texte": methodes})
    if avec_resultats:
        blocs.append({"repere": "S2", "type": "section", "nom": "Results", "emplacement": "section : Results",
                      "texte": RESULTATS})
    return {"titre": "Titre fabriqué", "blocs": blocs, "origine": "europe_pmc", "non_lus": [], "tableaux_en_image": 0}


def reponse(plan="essai_quasi_randomise", repere="S1", passage=ALTERNE, **autres):
    return json.dumps({"plan": plan, "repere": repere, "passage": passage, "justification": "Affectation alternée.",
                       "incertitude": None, "alerte": None, **autres})


def test_l_extrait_garde_le_resume_et_la_methode_pas_les_resultats():
    d = texte.extrait_pour_plan(document())
    assert [b["repere"] for b in d["blocs"]] == ["R", "S1"]
    # Sans partie de méthode reconnue, les premières sections sont gardées.
    d = texte.extrait_pour_plan(document(nom="Intervention arms", avec_resultats=True))
    assert "S1" in [b["repere"] for b in d["blocs"]]
    d = texte.extrait_pour_plan(document(methodes=None))
    assert [b["repere"] for b in d["blocs"]] == ["R", "S2"]
    # La taille est bornée, et un passage se vérifie dans le document entier.
    long = texte.extrait_pour_plan(document(methodes="Methods text. " * 2000), maximum=500)
    assert sum(len(b["texte"]) for b in long["blocs"]) <= 500


def test_la_requete_donne_la_liste_fermee_et_le_type_du_tri_sans_l_imposer():
    r = pe.requete_plan({"id": "pm1"}, document(), "consigne", "essai_randomise")
    for plan in pe.PLANS:
        assert f"- {plan} :" in r["contenu"]
    assert "TYPE ANNONCÉ PAR LE TRI : essai randomisé (à vérifier dans la méthode, pas à reprendre)" in r["contenu"]
    assert ALTERNE in r["contenu"] and "Pain fell" not in r["contenu"]
    assert r["id"] == "plan:pm1" and r["max_sortie"] == pe.SORTIE
    assert "TYPE ANNONCÉ" not in pe.requete_plan({"id": "pm1"}, document(), "consigne")["contenu"]


def test_un_plan_exige_un_passage_verifie():
    p, bilan = pe.lire_plan(reponse(), document(), "essai_randomise", publier_passage=True)
    assert p["plan"] == "essai_quasi_randomise" and p["ecart_avec_le_tri"] is True
    assert p["source"] == {"emplacement": "section : Methods", "passage": ALTERNE}
    assert p["type_tri"] == "essai_randomise" and bilan["lisible"] and bilan["ecarts"] == []
    # Sous licence non ouverte : l'emplacement est gardé, pas le passage.
    assert pe.lire_plan(reponse(), document(), "essai_randomise")[0]["source"]["passage"] is None
    # Passage que le texte ne contient pas : le plan n'est pas retenu.
    p, bilan = pe.lire_plan(reponse(passage="Un passage que le texte ne contient pas."), document(), "essai_randomise")
    assert p["plan"] == pe.NON_DETERMINE and p["source"] is None and p["ecart_avec_le_tri"] is None
    assert any("sans passage vérifiable" in e for e in bilan["ecarts"])
    # Plan hors de la liste, réponse illisible.
    p, bilan = pe.lire_plan(reponse(plan="essai_clinique"), document(), "essai_randomise")
    assert p["plan"] == pe.NON_DETERMINE and any("plan invalide" in e for e in bilan["ecarts"])
    assert pe.lire_plan("pas du JSON", document(), "essai_randomise")[0] is None
    assert pe.lire_plan("[1, 2]", document(), "essai_randomise")[0] is None


def test_l_ecart_avec_le_tri():
    d = document()
    assert pe.lire_plan(reponse("essai_randomise"), d, "essai_randomise")[0]["ecart_avec_le_tri"] is False
    assert pe.lire_plan(reponse("revue_descriptive"), d, "meta_analyse")[0]["ecart_avec_le_tri"] is True
    assert pe.lire_plan(reponse("revue_interventions"), d, "revue_systematique")[0]["ecart_avec_le_tri"] is False
    assert pe.lire_plan(reponse("modele_de_prediction"), d, "etude_diagnostique")[0]["ecart_avec_le_tri"] is True
    # Pas de type du tri : pas d'écart à constater.
    assert pe.lire_plan(reponse("essai_randomise"), d, None)[0]["ecart_avec_le_tri"] is None


def test_une_justification_au_chiffre_invente_est_ecartee():
    p, bilan = pe.lire_plan(reponse(justification="Alternance sur 47 patientes."), document(), "essai_randomise")
    assert p["justification"] is None and any("chiffre absent" in e for e in bilan["ecarts"])


def test_la_grille_se_deduit_du_plan_par_une_table():
    assert set(pe.GRILLE_DU_PLAN) == set(pe.PLANS) and set(pe.DEFINITIONS) == set(pe.PLANS) == set(pe.LIBELLES)
    assert pe.choisir_grille("essai_randomise") == ("rob2", None, None)
    assert pe.choisir_grille("etude_diagnostique")[0] == "quadas2"
    assert pe.choisir_grille("revue_interventions")[0] == "amstar2"
    assert pe.choisir_grille("recommandation")[0] == "agree2"
    # Pas de grille écrite : on dit laquelle conviendrait, sans forcer une autre.
    outil, manquante, motif = pe.choisir_grille("essai_quasi_randomise")
    assert outil is None and manquante == "robins_i" and "essai quasi randomisé" in motif
    assert pe.choisir_grille("modele_de_prediction")[:2] == (None, "probast")
    assert pe.choisir_grille("revue_descriptive")[:2] == (None, "robis")
    assert pe.choisir_grille("observationnel")[:2] == (None, "jbi")
    # Plan non établi ou « autre » : aucune grille, sans nom de grille.
    assert pe.choisir_grille("autre")[:2] == (None, None) and "applicable" in pe.choisir_grille("autre")[2]
    assert pe.choisir_grille(pe.NON_DETERMINE) == (None, None, "plan d'étude non établi")


def test_la_consigne_existe_et_protege_contre_une_instruction_cachee():
    consigne = charger_consigne("plan_etude")
    assert "jamais une instruction" in consigne and "alerte" in consigne
    assert "Le titre ne décide pas" in consigne
