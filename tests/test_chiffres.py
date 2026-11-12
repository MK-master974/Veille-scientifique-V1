"""Tests des corrigés « chiffres relevés » du corpus de référence (VS-D32, VS-D34), sans réseau.

Les règles de comparaison de deux nombres sont fixées avant toute mesure : ces tests les figent.
Les textes ci-dessous sont fabriqués : ils ne reprennent le texte d'aucun article.
"""
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent


def _charger(nom):
    spec = importlib.util.spec_from_file_location(nom, RACINE / "banc" / f"{nom}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chiffres = _charger("chiffres")
assembler = _charger("assembler_chiffres")


def chiffre(nature, valeur, ident="c1", dans=True):
    return {"id": ident, "nature": nature, "libelle": "", "valeur": valeur, "dans_l_article": dans}


# --- Comparaison de deux nombres --------------------------------------------------------------

@pytest.mark.parametrize("nature, corrige, texte, attendu", [
    # Le signe est ignoré, l'arrondi toléré.
    ("effet", "29.6", "MD −29,56 (−53,14 à −5,98)", True),
    ("effet", "29.6", "MD 29,7", False),
    ("ic_bas", "0.55", "−0,55 à 1,08", True),
    ("effet", "0.3", "SMD 0,26", True),
    # Un nombre moins précis : une seule décimale de moins, deux chiffres significatifs au moins.
    ("sensibilite", "0.943", "sensibilité 0,94", True),
    ("effet", "0.26", "SMD 0,3", False),
    ("effet", "2.63", "3 études", False),
    ("effet", "29.56", "30", False),
    # Fraction et pourcentage, pour une proportion seulement.
    ("sensibilite", "0.94", "sensibilité 94 %", True),
    ("sensibilite", "0.94", "sensibilité 94,3 %", True),
    ("sensibilite", "94", "sensitivity 0.943", True),
    ("specificite", "0.80", "80 %", True),
    ("specificite", "0.80", "8 %", False),
    ("effet", "0.94", "94", False),
    # Milliers : espace, virgule anglaise ; pas de confusion avec un autre nombre.
    ("effectif", "1029", "1 029 participants", True),
    ("effectif", "1029", "1 029 participants", True),
    ("effectif", "1029", "1,029 participants", True),
    ("effectif", "265", "n = 265", True),
    ("effectif", "265", "2650 patients", False),
    ("effectif", "265", "26,5", False),
    # Point médian et décimale sans zéro initial.
    ("effet", "29.6", "29·6", True),
    ("effet", "0.05", "p = .05", True),
])
def test_un_chiffre_est_retrouve_selon_les_regles_fixees(nature, corrige, texte, attendu):
    assert chiffres.present(chiffre(nature, corrige), texte) is attendu


def test_un_chiffre_du_corrige_s_ecrit_sans_ambiguite():
    assert chiffres.valeur_corrige(chiffre("effectif", "1029")) == (1029.0, 0)
    assert chiffres.valeur_corrige(chiffre("sensibilite", "0.80")) == (0.8, 2)
    for mal_ecrit in ("1,029", "-0.5", "94 %", "environ 3", ""):
        with pytest.raises(ValueError):
            chiffres.valeur_corrige(chiffre("effet", mal_ecrit))


# --- Corpus -----------------------------------------------------------------------------------

def corpus_type():
    return {"groupes": [{
        "type_etude": "etude_diagnostique",
        "source": {"pmid": "90000001", "pmcid": "PMC9000001", "licence": "CC BY", "tableau": "Table 2"},
        "cas": [{"pmid": "11111111", "pmcid": "PMC1111111", "licence": "CC BY", "reference": "Étude fabriquée",
                 "chiffres": [chiffre("effectif", "265", "n"), chiffre("sensibilite", "0.94", "se"),
                              chiffre("specificite", "0.80", "sp", dans=False)]}]}]}


def test_la_forme_du_corpus_est_controlee():
    assert chiffres.verifier_forme(corpus_type()) == []
    mauvais = corpus_type()
    cas = mauvais["groupes"][0]["cas"][0]
    cas["chiffres"][0]["valeur"] = "1,029"
    cas["chiffres"][1]["nature"] = "inconnue"
    cas["chiffres"][2]["id"] = "n"
    mauvais["groupes"][0]["source"]["tableau"] = ""
    defauts = " ; ".join(chiffres.verifier_forme(mauvais))
    assert "mal écrite" in defauts and "nature inconnue" in defauts and "en double" in defauts
    assert "sans « tableau »" in defauts


def test_le_corpus_du_depot_est_bien_forme():
    corpus = chiffres.charger()
    assert chiffres.verifier_forme(corpus) == []
    for cas in chiffres.cas_du_corpus(corpus):
        assert cas["licence"] in ("CC BY", "CC0"), cas["pmid"]
        assert cas["source"]["licence"] in ("CC BY", "CC0"), cas["pmid"]


# --- Mesure -----------------------------------------------------------------------------------

def extraction(effectif, resultats):
    source = {"emplacement": "résumé", "passage": None}
    return {"question": None, "population": None, "intervention": None, "comparateur": None,
            "effectif": {"valeur": effectif, "source": source} if effectif else None,
            "resultats": [{"critere": c, "valeur": v, "intervalle": i, "source": source} for c, v, i in resultats],
            "evenements_indesirables": {"rapportes": False, "valeur": None, "source": None}}


def test_la_mesure_cherche_chaque_chiffre_dans_la_zone_attendue():
    cas = chiffres.cas_du_corpus(corpus_type())[0]
    e = extraction("265 participants", [("Sensibilité du test A", "94 %", None), ("Prévalence", "80 %", None)])
    etats = {x["id"]: x["etat"] for x in chiffres.mesurer_cas(cas, e)}
    assert etats == {"n": "retrouve", "se": "retrouve", "sp": "retrouve"}

    # L'effectif écrit dans un résultat, et non dans le champ « effectif » : noté « ailleurs ».
    e = extraction(None, [("Sensibilité chez 265 participants", "0,94", None)])
    etats = {x["id"]: x["etat"] for x in chiffres.mesurer_cas(cas, e)}
    assert etats == {"n": "ailleurs", "se": "retrouve", "sp": "absent"}

    assert {x["etat"] for x in chiffres.mesurer_cas(cas, None)} == {"sans_extraction"}


def test_le_score_ecarte_les_chiffres_absents_de_l_article():
    cas = chiffres.cas_du_corpus(corpus_type())[0]
    e = extraction("265 participants", [("Sensibilité", "0,71", None)])
    s = chiffres.score(chiffres.mesurer_cas(cas, e))
    # « sp » est absent de l'article : écarté avant la mesure, compté à part (VS-D34).
    assert s["chiffres"] == 3 and s["confirmes_dans_l_article"] == 2
    assert s["ecartes_car_absents_de_l_article"] == 1
    assert s["retrouves"] == 1 and s["absents"] == 1 and s["part"] == 0.5
    assert chiffres.score([])["part"] is None
    assert chiffres.SEUIL_RETROUVES == 0.80


# --- Lecture du tableau d'une revue source ----------------------------------------------------

REVUE = """<article><body><sec><title>Results</title><p>Texte fabriqué.</p>
<table-wrap id="t1"><label>Table 2</label><caption><p>Diagnostic accuracy of each study</p></caption>
<table><thead><tr><th>Study</th><th>Sample size</th><th>Index test</th><th>Sensitivity</th><th>Specificity</th></tr></thead>
<tbody>
<tr><td rowspan="2">Martin et al. <xref ref-type="bibr" rid="r1">[1]</xref></td><td rowspan="2">265</td><td>Test A</td><td>0.94</td><td>0.80</td></tr>
<tr><td>Test B</td><td>0.71</td><td>0.92</td></tr>
<tr><td>Durand 2019</td><td>120</td><td>Test A</td><td>0.88</td><td>0.75</td></tr>
<tr><td>Pooled</td><td>385</td><td>Test A</td><td>0.91</td><td>0.78</td></tr>
</tbody></table></table-wrap></sec></body>
<back><ref-list>
<ref id="r1"><element-citation><person-group><name><surname>Martin</surname></name></person-group><year>2021</year><pub-id pub-id-type="pmid">11111111</pub-id></element-citation></ref>
<ref id="r2"><element-citation><person-group><name><surname>Durand</surname></name></person-group><year>2019</year><pub-id pub-id-type="doi">10.1000/ABC</pub-id></element-citation></ref>
</ref-list></back></article>"""


def test_les_lignes_d_un_tableau_sont_rattachees_a_l_etude_citee():
    tabs, refs = assembler.tableaux(ET.fromstring(REVUE))
    assert refs["r1"] == {"pmid": "11111111", "doi": "", "auteur": "Martin", "annee": "2021", "titre": ""}
    assert refs["r2"]["doi"] == "10.1000/abc"
    lignes = tabs[0]["lignes"]
    assert [l["cites"] for l in lignes] == [[], ["r1"], ["r1"], ["r2"], []]
    # La seconde ligne de Martin hérite de la première (cellule fusionnée) ; « Durand 2019 » est
    # reconnu par son nom, sans renvoi ; la ligne « Pooled » n'appartient à aucune étude.
    assert lignes[2]["herite"] is True and lignes[3]["herite"] is False
    texte = assembler.texte_des_lignes(tabs, {"r1"})
    assert "0.71" in texte and "0.88" not in texte and "0.91" not in texte
    assert chiffres.present(chiffre("sensibilite", "0.94"), texte)
    assert not chiffres.present(chiffre("sensibilite", "0.88"), texte)
    assert assembler.score_donnees(tabs[0], "diagnostic")[0] >= 3
    assert assembler.meme_libelle("TABLE 2.", " table 2") and not assembler.meme_libelle("Table 2", "Table 12")


def test_une_reference_sans_identifiant_garde_son_doi_ecrit_et_son_titre():
    xml = """<article><body><table-wrap><label>Table 1</label><table><tbody>
    <tr><td>Review</td><td>Pooled effect (95% CI)</td></tr>
    <tr><td>Bernard et al.</td><td>SMD 0.41 (0.12 to 0.70)</td></tr>
    <tr><td>Petit et al.</td><td>SMD 0.10 (-0.20 to 0.40)</td></tr>
    </tbody></table></table-wrap></body><back><ref-list>
    <ref id="a"><mixed-citation><person-group><name><surname>Bernard</surname></name></person-group>
      <article-title>An invented title about exercise and balance in older adults</article-title> <year>2024</year>
      doi: 10.1000/xyz.123.</mixed-citation></ref>
    <ref id="b"><mixed-citation><person-group><name><surname>Petit</surname></name></person-group><year>2020</year></mixed-citation></ref>
    <ref id="c"><mixed-citation><person-group><name><surname>Petit</surname></name></person-group><year>2022</year></mixed-citation></ref>
    </ref-list></back></article>"""
    tabs, refs = assembler.tableaux(ET.fromstring(xml))
    assert refs["a"]["doi"] == "10.1000/xyz.123"
    assert refs["a"]["titre"].startswith("An invented title")
    # Sans année dans la ligne, le nom seul suffit s'il ne désigne qu'une référence : « Bernard » oui,
    # « Petit » non (deux références portent ce nom).
    assert [l["cites"] for l in tabs[0]["lignes"]] == [[], ["a"], []]


def test_la_demande_du_depot_est_lisible():
    demandes = json.loads((RACINE / "banc" / "candidats_chiffres.json").read_text(encoding="utf-8"))["demandes"]
    assert demandes and demandes[-1]["mode"] in ("reperer", "lire", "verifier")
