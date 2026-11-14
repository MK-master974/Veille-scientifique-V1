"""Tests de l'appréciation méthodologique, de la catégorie d'importance et de leur banc d'essai.

Sans réseau ni IA. Le dernier test déroule le banc en entier avec des sources et une IA simulées.
Les textes ci-dessous sont fabriqués : ils ne reprennent le texte d'aucun article.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

from pipeline import appreciation as ap
from pipeline import classement as cl
from pipeline.config import charger_consigne

RACINE = Path(__file__).resolve().parent.parent


def _charger(nom):
    spec = importlib.util.spec_from_file_location(nom, RACINE / "banc" / f"{nom}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


banc = _charger("banc_appreciation")
lancer = _charger("lancer")

METHODE = ("The protocol was registered in PROSPERO before the search. We searched PubMed and Embase. "
           "Two reviewers independently selected studies. The certainty of evidence was rated low with GRADE.")


def document(integral=True):
    blocs = [{"repere": "R", "type": "resume", "nom": "Résumé", "emplacement": "résumé",
              "texte": "This invented review pooled 12 trials. Two reviewers independently selected studies."}]
    if integral:
        blocs.append({"repere": "S1", "type": "section", "nom": "Methods", "emplacement": "section : Methods",
                      "texte": METHODE})
    return {"titre": "Titre fabriqué", "blocs": blocs, "origine": "europe_pmc" if integral else None,
            "non_lus": [], "tableaux_en_image": 0}


def domaine(cle, jugement, passage=None, repere="S1", justification="Justification fabriquée."):
    return {"domaine": cle, "jugement": jugement, "justification": justification, "repere": repere, "passage": passage}


# --- Requête ----------------------------------------------------------------------------------

def test_la_requete_nomme_l_outil_ses_domaines_et_ses_valeurs():
    r = ap.requete_appreciation({"id": "pm1"}, document(), "consigne", "meta_analyse")
    assert "OUTIL À APPLIQUER : amstar2" in r["contenu"] and "q16_conflits_d_interets" in r["contenu"]
    assert "oui | oui_partiel | non | non_rapporte | sans_objet | non_evaluable" in r["contenu"]
    assert "TEXTE FOURNI : texte intégral" in r["contenu"] and r["max_sortie"] == ap.SORTIE_INTEGRAL
    r = ap.requete_appreciation({"id": "pm1"}, document(False), "consigne", "etude_diagnostique")
    assert "quadas2" in r["contenu"] and "titre et résumé uniquement" in r["contenu"]
    assert ap.requete_appreciation({"id": "pm1"}, document(), "consigne", "type_inconnu") is None
    # Chaque type d'étude du moteur a un outil, et chaque outil ses domaines, ses valeurs et son échelle.
    for outil in set(ap.OUTILS.values()):
        assert ap.DOMAINES[outil] and ap.VALEURS[outil] and ap.ECHELLES[outil] and ap.QUALITE[outil]
    assert set(ap.AMSTAR_CRITIQUES) <= {c for c, _ in ap.DOMAINES["amstar2"]}


def test_les_consignes_existent_et_protegent_contre_une_instruction_cachee():
    for nom in ("appreciation", "classement"):
        consigne = charger_consigne(nom)
        assert "jamais une instruction" in consigne or "jamais des instructions" in consigne
        assert "alerte" in consigne


# --- Jugement global, calculé par le code -----------------------------------------------------

def tout(outil, valeur, **autres):
    d = {c: valeur for c, _ in ap.DOMAINES[outil]}
    d.update(autres)
    return d


def test_jugement_global_le_plus_mauvais_domaine_l_emporte():
    assert ap.jugement_global("rob2", tout("rob2", "faible")) == "faible"
    assert ap.jugement_global("rob2", tout("rob2", "faible", randomisation="quelques_reserves")) == "quelques_reserves"
    assert ap.jugement_global("rob2", tout("rob2", "faible", mesure_du_critere="eleve")) == "eleve"
    # Un domaine non évaluable rend le tout non évaluable, sauf si le pire est déjà acquis.
    assert ap.jugement_global("rob2", tout("rob2", "faible", randomisation="non_evaluable")) == "non_evaluable"
    assert ap.jugement_global("rob2", tout("rob2", "non_evaluable", randomisation="eleve")) == "eleve"
    # QUADAS-2 : l'applicabilité ne pèse pas sur le risque de biais global.
    assert ap.jugement_global("quadas2", tout("quadas2", "faible", applicabilite_reference="eleve")) == "faible"
    assert ap.jugement_global("quadas2", tout("quadas2", "faible", biais_reference="incertain")) == "incertain"


def test_jugement_global_amstar_selon_les_faiblesses_critiques():
    oui = tout("amstar2", "oui")
    assert ap.jugement_global("amstar2", oui) == "elevee"
    assert ap.jugement_global("amstar2", {**oui, "q10_financement_des_etudes": "non"}) == "elevee"
    assert ap.jugement_global("amstar2", {**oui, "q10_financement_des_etudes": "non", "q03_plans_d_etude": "non"}) == "moderee"
    assert ap.jugement_global("amstar2", {**oui, "q02_protocole": "non"}) == "faible"
    assert ap.jugement_global("amstar2", {**oui, "q02_protocole": "non", "q07_etudes_exclues": "non"}) == "tres_faible"
    # « Oui partiel » n'est pas une faiblesse.
    assert ap.jugement_global("amstar2", {**oui, "q04_recherche": "oui_partiel"}) == "elevee"
    # Une question critique non évaluable empêche de conclure, sauf si deux faiblesses critiques sont acquises.
    assert ap.jugement_global("amstar2", {**oui, "q09_risque_de_biais": "non_evaluable"}) == "non_evaluable"
    assert ap.jugement_global("amstar2", {**oui, "q09_risque_de_biais": "non_evaluable", "q02_protocole": "non",
                                          "q07_etudes_exclues": "non"}) == "tres_faible"


def test_etiquette_candidate():
    assert ap.etiquette_candidate("meta_analyse", "elevee") == "solide"
    assert ap.etiquette_candidate("meta_analyse", "elevee", "faible") == "modere"
    assert ap.etiquette_candidate("meta_analyse", "moyenne", "tres_faible") == "preliminaire"
    # Deux règles déjà validées : un essai isolé et une étude diagnostique ne sont jamais « solide ».
    assert ap.etiquette_candidate("essai_randomise", "elevee") == "modere"
    assert ap.etiquette_candidate("etude_diagnostique", "elevee") == "modere"
    assert ap.etiquette_candidate("essai_randomise", "faible") == "preliminaire"
    assert ap.etiquette_candidate("meta_analyse", "non_evaluable") == "non_evaluable"


# --- Contrôle de la réponse -------------------------------------------------------------------

def test_un_jugement_favorable_exige_un_passage_verifie():
    rep = {"domaines": [
        domaine("q02_protocole", "oui", "The protocol was registered in PROSPERO before the search."),
        domaine("q04_recherche", "oui_partiel", "We searched PubMed and Embase."),
        domaine("q05_selection_en_double", "oui", "Un passage que le texte ne contient pas."),
        domaine("q07_etudes_exclues", "non", None, None, "Aucune liste des études exclues."),
        domaine("q09_risque_de_biais", "excellent", "We searched PubMed and Embase."),
        domaine("q11_methodes_statistiques", "sans_objet", None, None),
        domaine("q01_pico", "sans_objet", None, None)]}
    a, bilan = ap.lire_appreciation(json.dumps(rep), document(), "meta_analyse", publier_passages=True)
    par = {d["domaine"]: d for d in a["domaines"]}
    assert par["q02_protocole"]["jugement"] == "oui"
    assert par["q02_protocole"]["source"] == {"emplacement": "section : Methods",
                                               "passage": "The protocol was registered in PROSPERO before the search."}
    assert par["q04_recherche"]["jugement"] == "oui_partiel"
    # Favorable, mais passage introuvable : non évaluable, et le refus est compté.
    assert par["q05_selection_en_double"]["jugement"] == "non_evaluable"
    # Un silence n'est pas un défaut : « non » sans passage devient « non rapporté » (VS-D44).
    assert par["q07_etudes_exclues"]["jugement"] == "non_rapporte" and par["q07_etudes_exclues"]["source"] is None
    assert any("« non » sans passage" in x["nature"] for x in bilan["ecarts"])
    # Valeur invalide ; « sans objet » hors des questions réservées aux méta-analyses ; domaine absent.
    assert par["q09_risque_de_biais"]["jugement"] == "non_evaluable"
    assert par["q11_methodes_statistiques"]["jugement"] == "sans_objet"
    assert par["q01_pico"]["jugement"] == "non_evaluable" and par["q16_conflits_d_interets"]["jugement"] == "non_evaluable"
    assert len(a["domaines"]) == 16 and a["jugement_outil"] == "non_evaluable" and a["etiquette"] == "non_evaluable"
    assert bilan["proposes"] == 4 and bilan["gardes"] == 3
    assert any("favorable sans passage" in r["motif"] for r in bilan["refus"])


def test_non_exige_un_passage_et_un_silence_est_non_rapporte():
    rep = {"domaines": [
        domaine("q02_protocole", "non", "We searched PubMed and Embase."),      # le texte montre une recherche, pas un protocole
        domaine("q07_etudes_exclues", "non_rapporte", None, None, "Rien sur la liste des exclus."),
        domaine("q09_risque_de_biais", "non", None, None, "Aucune évaluation du risque de biais.")]}
    a, bilan = ap.lire_appreciation(json.dumps(rep), document(), "meta_analyse")
    par = {d["domaine"]: d for d in a["domaines"]}
    assert par["q02_protocole"]["jugement"] == "non" and par["q02_protocole"]["source"]["emplacement"] == "section : Methods"
    assert par["q07_etudes_exclues"]["jugement"] == "non_rapporte"
    assert par["q09_risque_de_biais"]["jugement"] == "non_rapporte"
    # Le silence ne compte pas comme une faiblesse certaine : le pire et le meilleur sont donnés.
    # q02 est un « non » certain ; les autres questions critiques sont inconnues : très faible au pire, faible au mieux.
    assert a["fourchette"] == {"pire": "tres_faible", "meilleur": "faible"}
    assert a["nature_du_jugement"] == "fiabilite_de_la_methode"


def test_fourchette_du_jugement_global():
    oui = tout("amstar2", "oui")
    # Une question critique non rapportée : entre « faible » et le meilleur niveau, pas un « non évaluable » sec.
    assert ap.fourchette("amstar2", {**oui, "q07_etudes_exclues": "non_rapporte"}) == ("faible", "elevee")
    assert ap.jugement_global("amstar2", {**oui, "q07_etudes_exclues": "non_rapporte"}) == "non_evaluable"
    # Deux faiblesses critiques acquises : les inconnues n'y changent rien.
    ferme = {**oui, "q02_protocole": "non", "q07_etudes_exclues": "non", "q09_risque_de_biais": "non_rapporte"}
    assert ap.fourchette("amstar2", ferme) == ("tres_faible", "tres_faible")
    assert ap.jugement_global("amstar2", ferme) == "tres_faible"
    # Question non critique non rapportée : seule la fourchette change quand une « non » est déjà là.
    assert ap.fourchette("amstar2", {**oui, "q03_plans_d_etude": "non", "q10_financement_des_etudes": "non_rapporte"}) == ("moderee", "elevee")
    assert ap.fourchette("amstar2", {**oui, "q03_plans_d_etude": "non", "q06_extraction_en_double": "non"}) == ("moderee", "moderee")
    # Les autres outils : le plus mauvais domaine, avec un domaine inconnu entre le pire et le meilleur.
    assert ap.fourchette("rob2", tout("rob2", "faible", randomisation="non_evaluable")) == ("eleve", "faible")
    assert ap.fourchette("rob2", tout("rob2", "faible", mesure_du_critere="quelques_reserves")) == ("quelques_reserves",) * 2
    assert ap.fourchette("quadas2", tout("quadas2", "faible", applicabilite_reference="non_evaluable")) == ("faible", "faible")
    assert ap.fourchette("agree2", tout("agree2", "elevee", applicabilite="non_evaluable")) == ("faible", "elevee")
    # Une question absente de la réponse compte comme non évaluée.
    assert ap.fourchette("amstar2", {}) == ("tres_faible", "elevee")


def test_aucune_grille_applicable_ne_force_aucune_note():
    a = ap.sans_grille({"plan": "essai_quasi_randomise"}, "aucune grille écrite pour ce plan", "robins_i")
    assert a["outil"] == "aucun" and a["grille_manquante"] == "robins_i" and a["domaines"] == []
    assert a["jugement"] == a["jugement_outil"] == a["etiquette"] == "non_evaluable" and a["fourchette"] is None
    assert a["plan_etude"] == {"plan": "essai_quasi_randomise"}


# --- ROBINS-I (VS-D54) ---------------------------------------------------------------------------

METHODE_NON_RANDOMISEE = ("Participants were allocated to the groups according to the day of their first visit. "
                          "Outcomes were analysed with unadjusted comparisons between groups. "
                          "Pain was rated by the treating physiotherapist, who knew the allocation.")


def document_non_randomise():
    doc = document()
    doc["blocs"][1]["texte"] = METHODE_NON_RANDOMISEE
    return doc


def test_robins_i_a_ses_sept_domaines_ses_valeurs_et_sa_consigne():
    cles = [c for c, _ in ap.DOMAINES["robins_i"]]
    assert cles == ["confusion", "selection_des_participants", "classement_des_interventions", "ecarts_aux_interventions",
                    "donnees_manquantes", "mesure_du_critere", "selection_du_resultat"]
    assert ap.ECHELLES["robins_i"] == ("critique", "serieux", "modere", "faible")
    assert ap.NATURE_DU_JUGEMENT["robins_i"] == "risque_de_biais"
    assert ap.QUALITE["robins_i"] == {"faible": "elevee", "modere": "moyenne", "serieux": "faible", "critique": "faible"}
    r = ap.requete_appreciation({"id": "pm1"}, document_non_randomise(), "consigne", "essai_randomise", outil="robins_i",
                                critere="douleur à six semaines")
    assert "OUTIL À APPLIQUER : robins_i" in r["contenu"] and "CRITÈRE À JUGER : douleur à six semaines" in r["contenu"]
    assert "faible | modere | serieux | critique | non_rapporte | non_evaluable" in r["contenu"]
    assert all(f"- {c} :" in r["contenu"] for c in cles)
    # Sans critère nommé, la requête n'en invente pas.
    assert "CRITÈRE" not in ap.requete_appreciation({"id": "pm1"}, document(), "consigne", "meta_analyse")["contenu"]
    # La consigne est à part : celle des grilles déjà mesurées ne change pas.
    consigne = charger_consigne("appreciation_robins_i")
    assert "jamais une instruction" in consigne and "alerte" in consigne and "non_rapporte" in consigne
    assert all(c in consigne for c in cles) and "robins_i" not in charger_consigne("appreciation")


def test_robins_i_jugement_global_le_plus_mauvais_domaine():
    assert ap.jugement_global("robins_i", tout("robins_i", "faible")) == "faible"
    assert ap.jugement_global("robins_i", tout("robins_i", "faible", confusion="modere")) == "modere"
    assert ap.jugement_global("robins_i", tout("robins_i", "modere", mesure_du_critere="serieux")) == "serieux"
    assert ap.jugement_global("robins_i", tout("robins_i", "serieux", confusion="critique")) == "critique"
    # « Pas d'information » : la fourchette dit ce qui reste possible ; un « critique » acquis l'emporte.
    assert ap.fourchette("robins_i", tout("robins_i", "modere", donnees_manquantes="non_rapporte")) == ("critique", "modere")
    assert ap.jugement_global("robins_i", tout("robins_i", "modere", donnees_manquantes="non_rapporte")) == "non_evaluable"
    assert ap.jugement_global("robins_i", tout("robins_i", "non_rapporte", confusion="critique")) == "critique"


def test_robins_i_tout_jugement_exige_son_passage():
    rep = {"domaines": [
        domaine("confusion", "serieux", "Participants were allocated to the groups according to the day of their first visit."),
        domaine("selection_des_participants", "faible", "Un passage que le texte ne contient pas."),
        domaine("classement_des_interventions", "modere", None, None),
        domaine("ecarts_aux_interventions", "non_rapporte", None, None, "Rien sur les co-interventions."),
        domaine("donnees_manquantes", "serieux", None, None, "Aucun chiffre de perdus de vue."),
        domaine("mesure_du_critere", "serieux",
                "Pain was rated by the treating physiotherapist, who knew the allocation."),
        domaine("selection_du_resultat", "critique", None, None, "Pas de protocole.")]}
    a, bilan = ap.lire_appreciation(json.dumps(rep), document_non_randomise(), "essai_randomise", outil="robins_i",
                                    publier_passages=True)
    par = {d["domaine"]: d["jugement"] for d in a["domaines"]}
    # Un défaut montré par un passage vérifié est gardé, avec sa source.
    assert par["confusion"] == "serieux" and par["mesure_du_critere"] == "serieux"
    assert a["domaines"][0]["source"]["emplacement"] == "section : Methods"
    # Favorable sans passage vérifiable : refusé, non évaluable.
    assert par["selection_des_participants"] == "non_evaluable" and par["classement_des_interventions"] == "non_evaluable"
    # Défaut sans passage : un silence n'est pas un défaut, le domaine devient « non rapporté ».
    assert par["donnees_manquantes"] == "non_rapporte" and par["selection_du_resultat"] == "non_rapporte"
    assert par["ecarts_aux_interventions"] == "non_rapporte"
    assert any("« critique » sans passage" in x["nature"] for x in bilan["ecarts"])
    # Deux domaines « sérieux » acquis : au pire critique, au mieux sérieux ; jamais mieux.
    assert a["fourchette"] == {"pire": "critique", "meilleur": "serieux"} and a["jugement_outil"] == "non_evaluable"
    assert a["outil"] == "robins_i" and a["nature_du_jugement"] == "risque_de_biais" and a["grade_rapporte"] is None


def test_robins_i_etiquette_jamais_solide_et_qualite():
    rep = {"domaines": [domaine(c, "faible", "Outcomes were analysed with unadjusted comparisons between groups.")
                        for c, _ in ap.DOMAINES["robins_i"]]}
    a, _ = ap.lire_appreciation(json.dumps(rep), document_non_randomise(), "meta_analyse", outil="robins_i")
    assert a["jugement_outil"] == "faible" and a["jugement"] == "elevee"
    # Étude isolée non randomisée : jamais « solide », quel que soit le type donné par le tri.
    assert a["etiquette"] == "modere"
    assert ap.etiquette_candidate("meta_analyse", "elevee", outil="robins_i") == "modere"
    assert ap.etiquette_candidate("meta_analyse", "faible", outil="robins_i") == "preliminaire"


def test_la_grille_peut_etre_imposee_par_le_plan():
    # Le type du tri dit « essai randomisé » ; le plan réel impose une autre grille.
    r = ap.requete_appreciation({"id": "pm1"}, document(), "consigne", "essai_randomise", outil="amstar2")
    assert "OUTIL À APPLIQUER : amstar2" in r["contenu"]
    rep = {"domaines": [domaine("q02_protocole", "oui", "The protocol was registered in PROSPERO before the search.")]}
    a, bilan = ap.lire_appreciation(json.dumps(rep), document(), "essai_randomise", outil="amstar2")
    assert a["outil"] == "amstar2" and bilan["outil"] == "amstar2" and len(a["domaines"]) == 16


def test_sur_resume_seul_une_absence_ne_prouve_rien():
    rep = {"domaines": [
        domaine("q05_selection_en_double", "oui", "Two reviewers independently selected studies.", "R"),
        domaine("q02_protocole", "non", None, None, "Aucun protocole mentionné.")]}
    a, bilan = ap.lire_appreciation(json.dumps(rep), document(False), "meta_analyse")
    par = {d["domaine"]: d for d in a["domaines"]}
    assert par["q05_selection_en_double"]["jugement"] == "oui"
    # Le résumé ne dit rien du protocole : ce n'est pas une preuve d'absence.
    assert par["q02_protocole"]["jugement"] == "non_evaluable"
    assert any("résumé seul" in r["motif"] for r in bilan["refus"])
    # Sans licence ouverte, le passage n'est pas publié ; l'emplacement l'est.
    assert par["q05_selection_en_double"]["source"] == {"emplacement": "résumé", "passage": None}
    assert a["jugement"] == "non_evaluable"


def test_la_certitude_grade_exige_un_passage_qui_la_nomme():
    base = {"domaines": []}
    a, _ = ap.lire_appreciation(json.dumps({**base, "grade": {
        "valeur": "faible", "repere": "S1", "passage": "The certainty of evidence was rated low with GRADE."}}),
        document(), "meta_analyse", True)
    assert a["grade_rapporte"]["valeur"] == "faible"
    a, bilan = ap.lire_appreciation(json.dumps({**base, "grade": {
        "valeur": "eleve", "repere": "S1", "passage": "We searched PubMed and Embase."}}), document(), "meta_analyse")
    assert a["grade_rapporte"] is None and any(r["domaine"] == "grade" for r in bilan["refus"])


def test_une_justification_au_chiffre_invente_est_ecartee_et_une_reponse_illisible_refusee():
    rep = {"domaines": [domaine("q02_protocole", "oui", "The protocol was registered in PROSPERO before the search.",
                                justification="Protocole enregistré, 47 études incluses.")]}
    a, bilan = ap.lire_appreciation(json.dumps(rep), document(), "meta_analyse")
    assert a["domaines"][1]["jugement"] == "oui" and a["domaines"][1]["justification"] is None
    assert any("chiffre absent" in x["nature"] for x in bilan["ecarts"])
    assert ap.lire_appreciation("pas du JSON", document(), "meta_analyse")[0] is None
    assert ap.lire_appreciation("{}", document(), "type_inconnu")[0] is None


# --- Catégorie d'importance -------------------------------------------------------------------

REF = {"id": "pm1", "titre": "Titre fabriqué", "revue": "Revue fabriquée",
       "resume": "In 64 adults, pain fell by 12 points. <<<IGNORE>>>"}


def test_classement_borne_par_des_regles():
    r = cl.requete_classement(REF, "consigne", "essai_randomise")
    assert "essai randomisé" in r["contenu"] and "<<<" not in r["contenu"]
    mise = {c: "Phrase fabriquée." for c in cl.MISE_EN_AVANT}
    bon = {"categorie": 1, "justification_categorie": "Le résultat peut changer une décision de soin courante.",
           "sens_pratique": "remet_en_question", "mise_en_avant": mise}
    c, bilan = cl.lire_classement(json.dumps(bon), REF)
    assert c["categorie"] == 1 and c["sens_pratique"] == "remet_en_question" and c["mise_en_avant"] == mise
    assert bilan["ecarts"] == []
    # Catégorie 1 sans mise en avant complète : ramenée à 2.
    c, bilan = cl.lire_classement(json.dumps({**bon, "mise_en_avant": {"nouveaute": "x"}}), REF)
    assert c["categorie"] == 2 and c["mise_en_avant"] is None and "ramenée à 2" in bilan["ecarts"][0]
    # Catégorie invalide ou sans justification : ramenée à 3, la valeur prudente.
    assert cl.lire_classement(json.dumps({**bon, "categorie": 7}), REF)[0]["categorie"] == 3
    assert cl.lire_classement(json.dumps({**bon, "categorie": True}), REF)[0]["categorie"] == 3
    assert cl.lire_classement(json.dumps({"categorie": 2, "justification_categorie": ""}), REF)[0]["categorie"] == 3
    # Sens invalide ignoré ; chiffre absent du titre et du résumé signalé.
    c, bilan = cl.lire_classement(json.dumps({"categorie": 3, "sens_pratique": "a_surveiller",
        "justification_categorie": "Confirme un effet déjà connu chez 640 adultes."}), REF)
    assert c["sens_pratique"] is None and "640" in bilan["ecarts"][0]
    assert cl.lire_classement("illisible", REF)[0] is None


# --- Banc d'essai : fonctions pures -----------------------------------------------------------

def test_comparaison_en_crans():
    assert banc.comparer("amstar2", "faible", "faible") == {"etat": "exact", "ecart": 0}
    assert banc.comparer("amstar2", "moderee", "faible")["etat"] == "un_cran"
    assert banc.comparer("amstar2", "tres_faible", "moderee")["etat"] == "trop_severe"
    # Plus favorable que le corrigé de deux crans : l'erreur que le seuil interdit.
    assert banc.comparer("amstar2", "elevee", "faible") == {"etat": "trop_favorable", "ecart": 2}
    assert banc.comparer("rob2", "faible", "eleve")["etat"] == "trop_favorable"
    assert banc.comparer("quadas2", "non_evaluable", "eleve")["etat"] == "non_evaluable"
    assert banc.comparer("quadas2", "faible", None)["etat"] == "sans_corrige"


def test_corrige_global_et_par_domaine():
    assert banc.cle("quelques réserves") == "quelques_reserves" and banc.cle("très faible") == "tres_faible"
    assert banc.corrige_global("amstar2", {"confiance_globale": "modérée"}) == "moderee"
    assert banc.corrige_global("rob2", {"global": "élevé"}) == "eleve"
    quadas = {"biais": {"selection_des_patients": "faible", "reference": "incertain"}, "applicabilite": {"reference": "élevé"}}
    assert banc.corrige_global("quadas2", quadas) == "incertain"
    assert banc.domaines_du_corrige("quadas2", quadas) == {
        "biais_selection_des_patients": "faible", "biais_reference": "incertain", "applicabilite_reference": "eleve"}
    amstar = banc.domaines_du_corrige("amstar2", {"questions": {"q01": "oui", "q02": "oui partiel", "q07": "non"}})
    assert amstar == {"q01_pico": "oui", "q02_protocole": "oui_partiel", "q07_etudes_exclues": "non"}
    app = {"domaines": [{"domaine": "q01_pico", "jugement": "oui"}, {"domaine": "q02_protocole", "jugement": "non"}]}
    accord = banc.accord_domaines("amstar2", app, {"questions": {"q01": "oui", "q02": "oui partiel", "q07": "non"}})
    assert (accord["compares"], accord["identiques"], accord["non_evaluables"]) == (3, 1, 1)


def test_seuils_du_porteur_du_projet():
    etats = ["exact"] * 5 + ["un_cran"] * 2 + ["trop_severe", "non_evaluable", "trop_favorable", "sans_corrige"]
    s = banc.seuils([{"etat": e} for e in etats])
    un_cran, favorable = list(s.values())
    assert un_cran == {"atteint": True, "mesure": "7 sur 10", "part": 0.7} and "70 %" in list(s)[0]
    assert favorable == {"atteint": False, "mesure": 1}
    assert list(banc.seuils([]).values())[0]["atteint"] is False


def test_les_corpus_qualite_sont_lisibles_par_le_banc():
    cas = banc.charger_cas()
    assert len(cas) >= 30 and len({c["pmid"] for c in cas}) == len(cas)
    for c in cas:
        if c["outil"] == "robins_i":
            # ROBINS-I : la grille ne se déduit pas du type du tri mais du plan d'étude ; le critère jugé est nommé.
            assert c["critere"] and c["type_etude"] in ("essai_quasi_randomise", "interventionnel_non_randomise"), c["pmid"]
            assert banc.corrige_global(c["outil"], c["corrige"]) in ap.ECHELLES["robins_i"] + (ap.NON_RAPPORTE,), c["pmid"]
        else:
            assert c["outil"] in ("rob2", "quadas2", "amstar2") and ap.OUTILS[c["type_etude"]] == c["outil"]
            assert banc.corrige_global(c["outil"], c["corrige"]) in ap.ECHELLES[c["outil"]], c["pmid"]
        for valeur in banc.domaines_du_corrige(c["outil"], c["corrige"]).values():
            assert valeur in ap.VALEURS[c["outil"]], (c["pmid"], valeur)
    for nom in ("qualite_lisible.json", "robins_i.json"):
        chemin = RACINE / "banc/corpus" / nom
        if not chemin.exists():
            continue
        for g in json.loads(chemin.read_text(encoding="utf-8"))["groupes"]:
            assert g["source"]["licence"] in ("CC BY", "CC0")
            assert all(c["licence"] in ("CC BY", "CC0") and c["pmcid"] for c in g["cas"])


def test_robins_i_au_banc_lecture_du_corrige_et_seuils():
    # « Pas d'information » de ROBINS-I se lit « non rapporté » ; les accents et les espaces ne comptent pas.
    assert banc.cle("pas d'information") == banc.cle("Pas d’information") == "non_rapporte"
    assert banc.cle("modéré") == "modere" and banc.cle("sérieux") == "serieux"
    corrige = {"confusion": "sérieux", "selection_des_participants": "faible", "mesure_du_critere": "pas d'information",
               "global": "sérieux"}
    assert banc.corrige_global("robins_i", corrige) == "serieux"
    assert banc.domaines_du_corrige("robins_i", corrige) == {"confusion": "serieux", "selection_des_participants": "faible",
                                                              "mesure_du_critere": "non_rapporte"}
    # Seuils de VS-D56 : 50 % d'identiques, plus qu'une réponse fixe, aucun jugement plus favorable de deux crans.
    attendus = ["serieux", "serieux", "serieux", "modere"]
    comparaisons = [banc.comparer("robins_i", o, a) for o, a in zip(["serieux", "serieux", "critique", "modere"], attendus)]
    s = list(banc.seuils_robins(comparaisons, attendus).values())
    assert s[0]["atteint"] is True and s[0]["mesure"] == "3 sur 4"
    # Répondre partout « sérieux » donnerait 3 identiques : 3 ne fait pas mieux, le seuil n'est pas atteint.
    assert s[1]["atteint"] is False and s[1]["mesure"] == "3 contre 3" and s[1]["reponse_fixe"] == "serieux"
    assert s[2]["atteint"] is True
    trop = [banc.comparer("robins_i", "faible", "serieux")]
    assert trop[0]["etat"] == "trop_favorable"
    assert list(banc.seuils_robins(trop, ["serieux"]).values())[2]["atteint"] is False
    # Aucun article : aucun seuil n'est atteint.
    assert not any(x["atteint"] for x in banc.seuils_robins([], []).values())


def test_lanceur_du_banc_appreciation():
    script, arguments = lancer.commande({"banc": "appreciation", "budget_usd": 50, "s45": 10, "classement": 30,
                                         "limite": 1, "sans_ia": True}, "res")
    assert script == "banc_appreciation.py"
    assert arguments == ["--sortie", "res", "--budget", "2.43", "--s45", "10", "--classement", "30", "--limite", "1",
                         "--sans-ia"]
    _, arguments = lancer.commande({"banc": "appreciation", "budget_usd": 0.6, "niveaux": "integral",
                                    "sans_declarations": True}, "res")
    assert arguments == ["--sortie", "res", "--budget", "0.6", "--niveaux", "integral", "--sans-declarations"]
    with pytest.raises(SystemExit):
        lancer.commande({"banc": "appreciation", "niveaux": "partout"}, "res")
    _, arguments = lancer.commande({"banc": "appreciation", "budget_usd": 0.25, "s45": 10, "plan_seul": True,
                                    "plan_externe": True}, "res")
    assert arguments == ["--sortie", "res", "--budget", "0.25", "--s45", "10", "--plan-seul", "--plan-externe"]
    # ROBINS-I (VS-D54) : une grille seulement, et des publications de 2026-S45 nommées.
    _, arguments = lancer.commande({"banc": "appreciation", "budget_usd": 0.45, "s45": 2, "outils": ["robins_i"],
                                    "s45_pmids": ["42980682", "42993769"]}, "res")
    assert arguments == ["--sortie", "res", "--budget", "0.45", "--s45", "2", "--outils", "robins_i",
                         "--s45-pmids", "42980682,42993769"]
    with pytest.raises(SystemExit):
        lancer.commande({"banc": "appreciation", "outils": ["probast"]}, "res")
    with pytest.raises(SystemExit):
        lancer.commande({"banc": "appreciation", "s45_pmids": ["42980682; rm"]}, "res")


# --- Le banc en entier, sources et IA simulées ------------------------------------------------

PHRASE = "This invented review searched two databases and two reviewers selected studies. "


class IASimulee:
    """Établit le plan d'après le type du tri (sauf une publication de 2026-S45 « quasi randomisée »), juge chaque
    domaine favorablement en citant le résumé, et classe tout en catégorie 3."""

    PLANS = {"essai randomisé": "essai_randomise", "étude diagnostique": "etude_diagnostique",
             "méta-analyse": "revue_interventions", "revue systématique": "revue_interventions",
             "recommandation": "recommandation"}

    def direct(self, requetes, modele, simultanes=8):
        reponses = {}
        for r in requetes:
            if r["id"].startswith("plan"):
                resume = re.search(r"\[R\] RÉSUMÉ\n(.+)", r["contenu"]).group(1)
                plan = self.PLANS[re.search(r"TYPE ANNONCÉ PAR LE TRI : ([^(]+) \(", r["contenu"]).group(1).strip()]
                if r["id"] == "plan-s45:pm42968156":
                    plan = "essai_quasi_randomise"
                rep = {"plan": plan, "repere": "R", "passage": resume[:60], "justification": "Simulée.",
                       "incertitude": None, "alerte": None}
            elif r["id"].startswith("classement"):
                rep = {"categorie": 3, "justification_categorie": "Le résultat confirme ce qui est déjà connu.",
                       "sens_pratique": "confirme", "mise_en_avant": None, "alerte": None}
            else:
                resume = re.search(r"\[R\] RÉSUMÉ\n(.+)", r["contenu"]).group(1)
                favorable = re.search(r"VALEURS PERMISES : (\w+)", r["contenu"]).group(1)
                cles = re.findall(r"^- (\w+) :", r["contenu"], re.M)
                rep = {"domaines": [{"domaine": c, "jugement": favorable, "justification": "Simulée.", "repere": "R",
                                     "passage": resume[:60]} for c in cles],
                       "grade": {"valeur": None, "repere": None, "passage": None}, "alerte": None}
            reponses[r["id"]] = (json.dumps(rep), {"prompt_tokens": 1000, "completion_tokens": 200})
        return reponses


def test_le_banc_se_deroule_en_entier(monkeypatch, tmp_path, capsys):
    article = ("<article><front><article-meta><abstract><p>" + PHRASE * 3 + "</p></abstract></article-meta></front><body>"
               + "".join(f"<sec><title>{t}</title><p>{PHRASE * 60}</p></sec>" for t in ("Methods", "Results")) + "</body></article>")
    lisibles = {c["pmid"] for g in json.loads((RACINE / "banc/corpus/qualite_lisible.json").read_text(encoding="utf-8"))["groupes"]
                for c in g["cas"]}
    monkeypatch.setattr(banc.chaine, "recuperer_pubmed", lambda pmids, cfg: [
        {"id": f"pm{p}", "source": "pubmed", "pmid": p, "titre": f"Titre fabriqué {p}", "revue": "Revue fabriquée",
         "resume": PHRASE * 3, "types_publication": []} for p in pmids])
    diagnostiques = ({c["pmid"] for c in banc.chiffres_banc.cas_du_corpus(banc.chiffres_banc.charger())
                      if c["type_etude"] == "etude_diagnostique"} - {c["pmid"] for c in banc.charger_cas()})
    monkeypatch.setattr(banc.acces, "decrire_europe_pmc", lambda pmids, journal=print, paquet=20: (
        {p: {"pmcid": f"PMC{p}", "licence": "CC BY"} for p in pmids
         if p in lisibles or p in diagnostiques or len(pmids) > 45}, 0))
    monkeypatch.setattr(banc.acces, "texte_integral_xml", lambda pmcid: (article, "ok"))
    monkeypatch.setattr(banc.ia, "fournisseur", lambda cfg: IASimulee())
    monkeypatch.setattr(banc.time, "sleep", lambda s: None)

    assert banc.main(["--sortie", str(tmp_path), "--budget", "9", "--s45", "2", "--classement", "3",
                      "--niveaux", "tout"]) == 0
    sortie = capsys.readouterr().out
    detail = json.loads((tmp_path / "resultats-appreciation.json").read_text(encoding="utf-8"))
    r = detail["resume"]
    assert r["corpus"]["avec_texte_integral"] == len(lisibles) and r["corpus"]["articles"] > len(lisibles)
    # L'IA simulée juge tout favorablement : le jugement global est le meilleur de chaque échelle. Le
    # corpus ne contient aucune revue « élevée » : plusieurs jugements sont trop favorables, et le
    # seuil « aucun jugement plus favorable de deux crans » n'est pas atteint.
    assert set(r["texte_integral"]["jugements_obtenus"]) == {"elevee", "faible"}
    assert r["texte_integral"]["etats"]["trop_favorable"] >= 8
    assert list(r["seuils"].values())[1]["atteint"] is False
    assert len(detail["s45"]) == 2 and r["categories_s45"] == {**r["categories_s45"], "classees": 5, "repartition": {"3": 5}}
    assert set(r["cout_usd"]["par_article"]) == {"plan", "resume", "integral", "s45", "classement"}
    # Étape « plan d'étude » : la grille du plan retrouve celle du corrigé pour tout le corpus lu en entier.
    pc = r["plan_etude"]["corpus"]
    assert pc["articles"] == len(lisibles) and pc["grille_du_corrige_retrouvee"] == len(lisibles)
    assert pc["plan_non_determine"] == 0 and pc["ecarts_avec_le_tri"] == 0
    # 2026-S45 : le plan quasi randomisé est jugé avec ROBINS-I depuis le 14 novembre 2026 (VS-D54), et non
    # avec la grille du tri (RoB 2). L'IA simulée juge tout « faible » : l'étiquette candidate d'une étude non
    # randomisée reste plafonnée à « modéré », comme celle d'un essai isolé.
    quasi = next(f for f in detail["s45"] if f["pmid"] == "42968156")
    assert quasi["plan_etude"]["plan"] == "essai_quasi_randomise" and quasi["plan_etude"]["ecart_avec_le_tri"] is True
    assert quasi["grille"] == "robins_i" and quasi["grille_manquante"] is None
    assert quasi["appreciation"]["outil"] == "robins_i" and quasi["appreciation"]["jugement_outil"] == "faible"
    assert quasi["appreciation"]["nature_du_jugement"] == "risque_de_biais" and quasi["appreciation"]["etiquette"] == "modere"
    assert [d["domaine"] for d in quasi["appreciation"]["domaines"]] == [c for c, _ in ap.DOMAINES["robins_i"]]
    autre = next(f for f in detail["s45"] if f["pmid"] == "42972648")
    assert autre["grille"] == "quadas2" and autre["appreciation"]["outil"] == "quadas2"
    assert r["plan_etude"]["s45"]["grilles"] == {"robins_i": 1, "quadas2": 1}
    # Fourchettes : l'IA simulée juge tout favorablement, la fourchette se réduit à un point.
    assert r["fourchettes"]["articles"] == len(lisibles) and r["fourchettes"]["largeur_moyenne"] == 1.0
    # Seuil de VS-D50 : le corrigé dans la fourchette, qui couvre deux niveaux au plus (ici, la fourchette est un point).
    seuil = list(r["fourchettes"]["seuil"].values())[0]
    assert seuil["mesure"].endswith(f"sur {len(lisibles)}") and 0 <= seuil["part"] <= 1
    # Texte intégral sous licence ouverte : le passage est gardé. Résumé seul : il ne l'est pas.
    avec = [x for x in detail["corpus"] if "integral" in x][0]
    assert avec["integral"]["appreciation"]["domaines"][0]["source"]["passage"]
    assert avec["resume"]["appreciation"]["domaines"][0]["source"]["passage"] is None
    assert "ARRÊT" not in sortie and "CATÉGORIE D'IMPORTANCE" in sortie and "PLAN D'ÉTUDE : CORPUS" in sortie

    # Essai court : un article par outil. Puis le plafond, qui arrête avant tout appel ; puis sans IA.
    assert banc.main(["--sortie", str(tmp_path), "--budget", "9", "--limite", "1"]) == 0
    court = json.loads((tmp_path / "resultats-appreciation.json").read_text(encoding="utf-8"))["resume"]
    assert court["corpus"]["articles"] == 3 and court["corpus"]["avec_texte_integral"] == 3
    assert court["lecture"] == {"niveaux": "integral", "declarations_hors_du_corps": True}
    # Plan d'étude seul, avec les études diagnostiques hors du corpus : aucune appréciation, aucune catégorie.
    capsys.readouterr()
    assert banc.main(["--sortie", str(tmp_path), "--budget", "9", "--plan-seul", "--plan-externe", "--s45", "2"]) == 0
    plan = json.loads((tmp_path / "resultats-plan.json").read_text(encoding="utf-8"))
    pr = plan["resume"]
    assert pr["lecture"]["plan_seul"] and set(pr["cout_usd"]) == {"total", "par_article"}
    assert pr["plan_etude"]["corpus"]["articles"] == len(lisibles) and pr["plan_etude"]["corpus"]["grilles_perdues"] == []
    hors = pr["plan_etude"]["hors_corpus_diagnostiques"]
    assert hors["articles"] == 7 and hors["plan_attendu_retrouve"] == 7        # 7 études diagnostiques hors du corpus « qualité »
    assert len(plan["s45"]) == 2
    sortie_plan = capsys.readouterr().out
    assert "PLAN D'ÉTUDE : HORS CORPUS" in sortie_plan
    assert "CORPUS : JUGEMENT GLOBAL" not in sortie_plan and "CATÉGORIE D'IMPORTANCE" not in sortie_plan
    # Par défaut : texte intégral seul, aucune appréciation sur résumé, donc aucun coût à ce niveau.
    assert banc.main(["--sortie", str(tmp_path), "--budget", "9", "--limite", "1"]) == 0
    seul = json.loads((tmp_path / "resultats-appreciation.json").read_text(encoding="utf-8"))
    assert seul["resume"]["lecture"]["niveaux"] == "integral" and "resume" not in seul["resume"]["cout_usd"]
    assert all("resume" not in x and "integral" in x for x in seul["corpus"])
    assert seul["resume"]["resume_seul"]["etats"] == {}
    assert banc.main(["--sortie", str(tmp_path), "--budget", "0.001"]) == 2
    # Après l'étape « plan d'étude », le coût réel est vérifié : un dépassement arrête avant les appréciations.
    # L'estimation est prudente : refus d'emblée seulement au-delà de 1,5 fois le plafond ; entre les deux, le coût
    # réel est vérifié avant chaque groupe.
    capsys.readouterr()
    assert banc.main(["--sortie", str(tmp_path), "--budget", "9", "--sans-ia"]) == 0
    estime = float(re.search(r"Coût estimé : ([\d.]+) \$", capsys.readouterr().out).group(1))
    assert banc.main(["--sortie", str(tmp_path), "--budget", str(estime / 1.2)]) == 0
    assert "Estimation prudente au-dessus du plafond" in capsys.readouterr().out
    assert banc.main(["--sortie", str(tmp_path), "--budget", str(estime / 1.6)]) == 2
    assert "ARRÊT : estimation supérieure au plafond" in capsys.readouterr().out
    with monkeypatch.context() as m:
        m.setattr(banc.ia, "cout_reel", lambda *a, **k: 10.0)
        assert banc.main(["--sortie", str(tmp_path), "--budget", "9", "--limite", "1"]) == 2
    assert "le plafond serait dépassé" in capsys.readouterr().out
    monkeypatch.setattr(banc.ia, "fournisseur", lambda cfg: pytest.fail("l'IA ne doit pas être appelée"))
    assert banc.main(["--sortie", str(tmp_path), "--sans-ia"]) == 0
