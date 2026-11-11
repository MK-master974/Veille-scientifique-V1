"""Contrôle des chiffres : formes lues dans la source, sans assouplir le refus d'un chiffre inventé.

Cas tirés du banc d'essai du 11/11/2026, où huit fiches justes avaient été écartées.
"""
from pipeline import controle


def _fiche(texte):
    return {"titre_fr": "Essai", "flash": texte, "standard": {"resultats": "", "impact_clinique": "", "limites": []},
            "complet": {}, "vulgarise": None, "chiffres_cites": []}


def _absents(resume, texte):
    ref = {"titre": "Trial", "resume": resume, "revue": "J", "mesh": [], "annee": "2020", "pmid": "1"}
    return controle.chiffres_non_sources(_fiche(texte), ref)


def test_nombre_en_lettres_au_dela_de_dix_accepte():
    assert _absents("Seventy-four subjects with ACL reconstruction participated.", "74 participants opérés du LCA.") == []
    assert _absents("Thirty-two of the 57 patients were included.", "32 patients sur 57.") == []
    assert _absents("Eighty-five percent were followed for two years.", "85 % suivis pendant 2 ans.") == []
    assert _absents("One hundred and twenty adults were randomised.", "120 adultes.") == []


def test_decimale_sans_zero_initial_acceptee():
    assert _absents("Balance improved (P < .05).", "Équilibre amélioré (p < 0,05).") == []
    assert _absents("Balance improved (P=.003).", "p = 0,003.") == []
    assert _absents("Balance improved (P < .05).", "p < ,05.") == []


def test_ordinal_et_francais():
    assert _absents("From the first week to week 12.", "De la 1re à la 12e semaine.") == []
    assert _absents("Trente-deux patients ont été inclus.", "32 patients.") == []


def test_chiffre_invente_toujours_refuse():
    assert _absents("Thirty subjects participated.", "31 participants.") == ["flash : 31"]
    assert _absents("Balance improved (P < .05).", "p < 0,01.") == ["flash : 0,01"]
    assert _absents("Ten twelve-week sessions.", "22 séances.") == ["flash : 22"]
    # « .05 » ne vaut pas 5
    assert _absents("Balance improved (P < .05).", "5 séances.") == ["flash : 5"]
