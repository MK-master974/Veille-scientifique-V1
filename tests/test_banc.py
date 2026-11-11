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
