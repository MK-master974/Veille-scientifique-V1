"""Tests de l'étude des protocoles et des suppléments (VS-D49), sans réseau ni IA.

Les articles ci-dessous sont fabriqués : ils ne reprennent le texte d'aucun article.
"""
import importlib.util
import json
from pathlib import Path

import pytest
import requests

RACINE = Path(__file__).resolve().parent.parent


def _charger(nom):
    spec = importlib.util.spec_from_file_location(nom, RACINE / "banc" / f"{nom}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


supp = _charger("supplements")
lancer = _charger("lancer")

ARTICLE = """<article xmlns:xlink="http://www.w3.org/1999/xlink"><front><article-meta><title-group><article-title>Revue fabriquée</article-title></title-group></article-meta></front>
<body><sec><title>Methods</title><p>The protocol was registered in PROSPERO (CRD42020123456) and an invented trial NCT01234567 is mentioned.
The list of excluded studies is given in Additional file 2. See also Appendix A. The protocol was not amended.</p></sec></body>
<back><sec sec-type="supplementary-material"><supplementary-material id="s1" xlink:href="additional-file-1.docx"><caption><p>Search strategy</p></caption></supplementary-material>
<supplementary-material id="s2"><media xlink:href="additional-file-2.xlsx"/></supplementary-material></sec></back></article>"""


def test_analyser_compte_les_supplements_les_registres_et_les_mentions():
    m = supp.analyser(ARTICLE)
    assert m["elements_supplementaires"] == 2 and m["extensions"] == {"docx": 1, "xlsx": 1}
    assert m["registres"] == {"PROSPERO": 1, "ClinicalTrials.gov": 1}
    assert m["mentions"] == {"fichier_supplementaire": 2, "liste_des_exclus": 1, "protocole": 2}   # « Additional file », « Appendix »
    # Aucun numéro de registre ni passage d'article dans la mesure : des nombres et des noms de famille seulement.
    assert "CRD42020123456" not in json.dumps(m) and "invented" not in json.dumps(m)
    assert supp.analyser("<article>") is None and supp.analyser(None) is None
    assert supp.analyser("<article><body><p>Rien.</p></body></article>") == {
        "elements_supplementaires": 0, "extensions": {}, "registres": {}, "mentions": {
            "fichier_supplementaire": 0, "liste_des_exclus": 0, "protocole": 0}}


class Reponse:
    def __init__(self, code, entetes):
        self.status_code, self.headers, self.ferme = code, entetes, False

    def close(self):
        self.ferme = True


def test_le_paquet_europe_pmc_se_mesure_sans_se_telecharger(monkeypatch):
    rep = Reponse(200, {"Content-Length": "5120"})
    monkeypatch.setattr(supp, "requete", lambda *a, **k: rep if k.get("stream") else pytest.fail("pas en flux"))
    assert supp.paquet_europe_pmc("PMC1") == {"present": True, "code": 200, "octets": 5120} and rep.ferme

    def absent(*a, **k):
        erreur = requests.HTTPError("404")
        erreur.response = Reponse(404, {})
        raise erreur
    monkeypatch.setattr(supp, "requete", absent)
    assert supp.paquet_europe_pmc("PMC1") == {"present": False, "code": 404}
    monkeypatch.setattr(supp, "requete", lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError("panne")))
    assert supp.paquet_europe_pmc("PMC1") == {"present": None, "code": None}


def test_l_etude_se_deroule_en_entier(monkeypatch, tmp_path, capsys):
    cas = [{"pmid": "1", "outil": "amstar2"}, {"pmid": "2", "outil": "amstar2"}, {"pmid": "3", "outil": "quadas2"}]
    monkeypatch.setattr(supp.banc_appreciation, "charger_cas", lambda: cas)
    monkeypatch.setattr(supp.acces, "decrire_europe_pmc", lambda pmids, journal=print: (
        {"1": {"pmcid": "PMC1", "licence": "CC BY"}, "2": {"pmcid": "PMC2", "licence": "CC BY-NC-ND"}}, 0))
    monkeypatch.setattr(supp.acces, "texte_integral_xml", lambda pmcid: (ARTICLE, "ok"))
    monkeypatch.setattr(supp, "paquet_europe_pmc", lambda pmcid: {"present": True, "code": 200, "octets": 10})
    monkeypatch.setattr(supp.time, "sleep", lambda s: None)
    assert supp.main(["--sortie", str(tmp_path)]) == 0
    detail = json.loads((tmp_path / "resultats-supplements.json").read_text(encoding="utf-8"))
    par = {x["pmid"]: x for x in detail["articles"]}
    # Seul l'article sous licence ouverte est lu ; les autres le sont à peine nommés.
    assert par["1"]["lu"] and not par["2"]["lu"] and not par["3"]["lu"]
    am = detail["resume"]["par_outil"]["amstar2"]
    assert am["articles"] == 2 and am["lus_en_entier"] == 1 and am["avec_element_supplementaire"] == 1
    assert am["avec_paquet_europe_pmc"] == 1 and am["avec_numero_de_registre_ou_de_protocole"] == 1
    assert am["familles_de_registre"] == {"PROSPERO": 1, "ClinicalTrials.gov": 1}
    assert detail["resume"]["cout_usd"] == 0 and "CRD42020123456" not in capsys.readouterr().out


def test_le_lanceur_connait_l_etude_sans_ia():
    script, arguments = lancer.commande({"banc": "supplements", "budget_usd": 5}, "res")
    assert script == "supplements.py" and arguments == ["--sortie", "res", "--budget", "0.0"]
