"""Tests de l'assemblage du corpus de référence, sans réseau."""
import importlib.util
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("assembler_essais", RACINE / "banc" / "assembler_essais.py")
banc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(banc)

QUESTIONS = """PromptID,PMCID,Outcome,Intervention,Comparator
1,100,pain,exercise training,usual care
2,100,function,exercise training,usual care
3,200,pain,drug A,placebo
4,200,mortality,drug A,placebo
5,300,pain,physiotherapy,sham
6,300,gait speed,physiotherapy,sham
7,300,quality of life,physiotherapy,sham
"""
PASSAGE = "The intervention group improved more than the control group at twelve weeks (p = 0.01)."
CORRIGES = f"""UserID,PromptID,PMCID,Valid Label,Valid Reasoning,Label,Annotations,Label Code,In Abstract,Evidence Start,Evidence End
1,1,100,1,1,significantly decreased,"{PASSAGE}",-1,1,10,90
2,1,100,1,1,significantly decreased,"{PASSAGE}",-1,1,10,90
1,2,100,1,1,significantly increased,"{PASSAGE}",1,0,10,90
1,3,200,1,1,no significant difference,"{PASSAGE}",0,1,10,90
1,4,200,1,1,no significant difference,"{PASSAGE}",0,1,10,90
1,5,300,1,1,no significant difference,"{PASSAGE}",0,1,10,90
1,6,300,1,1,significantly increased,"{PASSAGE}",1,1,10,90
2,6,300,1,1,no significant difference,"{PASSAGE}",0,1,10,90
1,7,300,0,1,significantly increased,"{PASSAGE}",1,1,10,90
"""


def _candidats():
    return banc.candidats(banc.lire_csv(QUESTIONS), banc.lire_csv(CORRIGES))


def test_seules_les_questions_de_reeducation_sont_gardees():
    par_article = _candidats()
    assert "100" in par_article        # exercice : pertinent, deux questions valides
    assert "200" not in par_article    # médicament : hors champ


def test_desaccord_et_corrige_non_valide_sont_ecartes():
    # Article 300 : la question 6 a deux corrigés contradictoires, la 7 un corrigé refusé.
    # Il ne reste qu'une question, donc l'article n'est pas candidat.
    assert "300" not in _candidats()


def test_corrige_et_passage_sont_repris_tels_quels():
    q = {x["id"]: x for x in _candidats()["100"]}
    assert q["1"]["corrige"] == {"code": -1, "libelle": "diminution significative"}
    assert q["1"]["annotateurs"] == 2
    assert q["1"]["passages"] == [PASSAGE]
    assert q["2"]["dans_le_resume"] is False


def test_choix_selon_la_licence_et_la_retractation():
    par_article = _candidats()
    libre = lambda pmcid: {"licence": "CC BY", "reference": "Réf.", "retracte": False, "pmid": "1"}
    ferme = lambda pmcid: {"licence": "CC BY-NC", "reference": "Réf.", "retracte": False, "pmid": "1"}
    retracte = lambda pmcid: {"licence": "CC BY", "reference": "Réf.", "retracte": True, "pmid": "1"}
    assert [c["pmcid"] for c in banc.choisir(par_article, 8, libre)] == ["PMC100"]
    assert banc.choisir(par_article, 8, ferme) == []
    assert banc.choisir(par_article, 8, retracte) == []


# --- Repérage des tableaux d'évaluation -------------------------------------------------------

_spec2 = importlib.util.spec_from_file_location("extraire_tableaux", RACINE / "banc" / "extraire_tableaux.py")
tab = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(tab)

XML_REVUE = """<article><body>
<table-wrap id="T2"><label>Table 2</label><caption><p>Risk of bias (RoB 2) of included trials</p></caption>
<table><tr><th>Study</th><th>Randomisation</th><th>Overall</th></tr>
<tr><td>Dupont 2019 <xref ref-type="bibr" rid="B7">[7]</xref></td><td>Low risk</td><td>Some concerns</td></tr></table>
</table-wrap>
<table-wrap id="T1"><label>Table 1</label><caption><p>Characteristics</p></caption>
<table><tr><td>Age</td><td>54</td></tr></table></table-wrap>
</body><back><ref-list><ref id="B7"><element-citation><pub-id pub-id-type="pmid">12345678</pub-id></element-citation></ref></ref-list></back></article>"""


def test_le_tableau_d_evaluation_est_repere_et_les_renvois_resolus():
    import xml.etree.ElementTree as ET
    trouves, figures, nb_refs = tab.tableaux(ET.fromstring(XML_REVUE), "rob2")
    assert nb_refs == 1 and figures == []
    assert [t["label"] for t in trouves] == ["Table 2"]
    assert trouves[0]["lignes"][1] == ["Dupont 2019 [7][PMID 12345678]", "Low risk", "Some concerns"]


def test_licences_normalisees():
    assert tab.normaliser_licence("cc by") == "CC BY"
    assert tab.normaliser_licence("cc0") == "CC0"
    assert tab.normaliser_licence("cc by-nc") == "CC BY NC"
    assert tab.normaliser_licence(None) == "inconnue"


# --- Cohérence des fichiers du corpus -----------------------------------------------------------

import json
import re

CORPUS = RACINE / "banc" / "corpus"


def test_corpus_qualite_bien_forme():
    c = json.loads((CORPUS / "qualite.json").read_text(encoding="utf-8"))
    permis = {v for valeurs in c["valeurs"].values() for v in valeurs} | {"incertain"}
    for groupe in c["groupes"]:
        assert groupe["source"]["licence"] in ("CC BY", "CC0")
        assert re.fullmatch(r"\d+", groupe["source"]["pmid"])
        for cas in groupe["cas"]:
            if cas.get("statut") == "identifiant à résoudre":
                continue
            assert re.fullmatch(r"\d+", cas["pmid"])
            jugements = []
            for v in cas["corrige"].values():
                jugements += list(v.values()) if isinstance(v, dict) else [v]
            assert all(j in permis for j in jugements), cas["reference"]


def test_pieges_bien_formes():
    p = json.loads((CORPUS / "pieges.json").read_text(encoding="utf-8"))
    assert {c["id"] for c in p["cas"]} == {"piege-retractation", "piege-resume-seul", "piege-instruction-cachee"}
    fictif = next(c for c in p["cas"] if c["id"] == "piege-instruction-cachee")
    assert fictif["fictif"] is True and "pmid" not in fictif
    assert all(c["attendu"] for c in p["cas"])


def test_essais_effet_sans_texte_d_article():
    e = json.loads((CORPUS / "essais_effet.json").read_text(encoding="utf-8"))
    assert len(e["cas"]) == 8
    for cas in e["cas"]:
        assert cas["licence"] in ("CC BY", "CC0")
        assert set(cas) <= {"pmcid", "licence", "reference", "retracte", "pmid", "questions"}
        for q in cas["questions"]:
            assert all(len(p) <= banc.PASSAGE_MAX for p in q["passages"])


# --- Banc d'essai : comparaisons ----------------------------------------------------------------

_spec3 = importlib.util.spec_from_file_location("banc_essai", RACINE / "banc" / "banc.py")
essai = importlib.util.module_from_spec(_spec3)
_spec3.loader.exec_module(essai)


def test_comparaison_du_sens_de_l_effet():
    assert essai.evaluer_effet("augmentation", 1) == "correct"
    assert essai.evaluer_effet("aucune", 0) == "correct"
    assert essai.evaluer_effet("diminution", 1) == "sens_inverse"
    assert essai.evaluer_effet("aucune", -1) == "incorrect"
    assert essai.evaluer_effet("non_indique", 1) == "non_indique"
    assert essai.evaluer_effet("peut-être", 1) == "illisible"


def test_etiquette_maximale_selon_la_revue():
    assert essai.etiquette_maximale("RoB 2", {"global": "élevé"}) == "preliminaire"
    assert essai.etiquette_maximale("RoB 2", {"global": "faible"}) == "modere"
    tous_faibles = {"biais": {"a": "faible", "b": "faible"}}
    assert essai.etiquette_maximale("QUADAS-2", tous_faibles) == "modere"
    assert essai.etiquette_maximale("QUADAS-2", {"biais": {"a": "faible", "b": "incertain"}}) == "preliminaire"
    assert essai.etiquette_maximale("AMSTAR 2", {"confiance_globale": "élevée"}) == "solide"
    assert essai.etiquette_maximale("AMSTAR 2", {"confiance_globale": "très faible"}) == "preliminaire"


def test_classement_de_l_etiquette():
    eleve = {"global": "élevé"}
    assert essai.evaluer_qualite("RoB 2", eleve, "modere") == "trop_favorable"
    assert essai.evaluer_qualite("RoB 2", eleve, "preliminaire") == "conforme"
    assert essai.evaluer_qualite("RoB 2", {"global": "faible"}, "preliminaire") == "plus_prudent"
    assert essai.evaluer_qualite("RoB 2", eleve, None) == "sans_fiche"


def test_tous_les_cas_du_corpus_sont_demandes():
    e, q, p = essai.charger_corpus()
    pmids = essai.pmids_du_corpus(e, q, p)
    assert len(pmids) == len(set(pmids)) and all(x.isdigit() for x in pmids)
    assert "40704879" in pmids and "17442840" in pmids
    fictif = essai.reference_fictive(next(c for c in p["cas"] if c.get("fictif")))
    assert fictif["id"] == "fictif-instruction" and fictif["resume"]
