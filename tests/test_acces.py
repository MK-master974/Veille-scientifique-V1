"""Tests de l'accès au texte intégral et de la mesure des niveaux d'accès, sans réseau.

Les XML ci-dessous sont fabriqués pour les tests : ils ne reprennent le texte d'aucun article.
"""
import importlib.util
from pathlib import Path

import pytest

from pipeline import acces

RACINE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("mesure_acces", RACINE / "banc" / "mesure_acces.py")
mesure = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mesure)

PHRASE = "Texte fabriqué pour le test, sans rapport avec un article réel. "


def article(sections=("Introduction", "Methods", "Results", "Discussion"), longueur=40, tableaux=1):
    corps = "".join(f"<sec><title>{t}</title><p>{PHRASE * longueur}</p></sec>" for t in sections)
    tables = "<table-wrap><table><tr><td>a</td></tr></table></table-wrap>" * tableaux
    return (f"<article><front><article-meta/></front><body>{corps}{tables}</body>"
            "<back><ref-list><ref id='r1'/><ref id='r2'/></ref-list></back></article>")


# --- Licences ---------------------------------------------------------------------------------

@pytest.mark.parametrize("brute, attendu", [
    ("cc by", "CC BY"), ("CC BY 4.0", "CC BY"), ("cc-by", "CC BY"),
    ("cc by-nc", "CC BY-NC"), ("cc by-nc-nd", "CC BY-NC-ND"), ("cc by-nc-sa", "CC BY-NC-SA"),
    ("cc by-nd", "CC BY-ND"), ("cc by-sa", "CC BY-SA"), ("cc0", "CC0"),
    ("https://creativecommons.org/licenses/by-nc-nd/4.0/", "CC BY-NC-ND"),
    ("http://creativecommons.org/publicdomain/zero/1.0/", "CC0"),
    ("All rights reserved", "autre"), ("", "inconnue"), (None, "inconnue"),
])
def test_classe_licence(brute, attendu):
    assert acces.classe_licence(brute) == attendu


def test_les_perimetres_s_emboitent():
    strict, inter, large = (set(acces.PERIMETRES[n]) for n in ("strict", "intermediaire", "large"))
    assert strict < inter < large
    assert strict == {"CC0", "CC BY"}
    assert "autre" not in large and "inconnue" not in large


# --- Structure d'un texte ---------------------------------------------------------------------

def test_decrire_texte_complet():
    m = acces.decrire_texte(article())
    assert m["corps"] and m["sections"] == 4 and m["methode"] and m["resultats"]
    assert m["tableaux"] == 1 and m["references"] == 2
    assert m["caracteres"] >= acces.SEUIL_CARACTERES


def test_decrire_texte_sans_corps_ou_illisible():
    m = acces.decrire_texte("<article><front/><back><ref-list><ref id='r1'/></ref-list></back></article>")
    assert m["corps"] is False and m["caracteres"] == 0 and m["references"] == 1
    assert acces.decrire_texte("<article><body>") is None
    assert acces.decrire_texte(None) is None


def test_decrire_texte_ne_garde_aucun_texte():
    m = acces.decrire_texte(article())
    assert all(isinstance(v, (bool, int)) for v in m.values())


# --- Niveau d'accès ---------------------------------------------------------------------------

def test_niveau_selon_la_licence_et_le_perimetre():
    texte = acces.decrire_texte(article())
    strict, large = acces.PERIMETRES["strict"], acces.PERIMETRES["large"]
    assert acces.niveau_acces("PMC1", "CC BY", texte, strict)[0] == 1
    assert acces.niveau_acces("PMC1", "CC BY-NC-ND", texte, strict)[0] == 3
    assert acces.niveau_acces("PMC1", "CC BY-NC-ND", texte, large)[0] == 1
    # Une licence inconnue ou propriétaire ne donne jamais mieux que « résumé uniquement ».
    assert acces.niveau_acces("PMC1", "inconnue", texte, large)[0] == 3
    assert acces.niveau_acces("PMC1", "autre", texte, large)[0] == 3


def test_niveau_sans_version_ou_sans_texte():
    strict = acces.PERIMETRES["strict"]
    assert acces.niveau_acces("", "CC BY", None, strict) == (3, "aucune version dans PubMed Central")
    assert acces.niveau_acces("PMC1", "CC BY", None, strict)[0] == 3


def test_niveau_partiel():
    strict = acces.PERIMETRES["strict"]
    court = acces.decrire_texte(article(sections=("Text",), longueur=2, tableaux=0))
    sans_corps = acces.decrire_texte("<article><front/></article>")
    assert acces.niveau_acces("PMC1", "CC BY", court, strict)[0] == 2
    assert acces.niveau_acces("PMC1", "CC BY", sans_corps, strict)[0] == 2


def test_bloc_acces_suit_le_format_de_la_fiche_v2():
    texte = acces.decrire_texte(article())
    strict = acces.PERIMETRES["strict"]
    lu = acces.bloc_acces("PMC1", "CC BY", texte, strict, "2026-11-12")
    assert set(lu) == {"niveau", "origine_texte", "url_texte", "licence", "consulte_le",
                       "parties_lues", "parties_non_lues"}
    assert lu["niveau"] == 1 and lu["licence"] == "CC BY" and "texte intégral" in lu["parties_lues"]
    resume_seul = acces.bloc_acces("PMC1", "CC BY-NC-ND", texte, strict, "2026-11-12")
    assert resume_seul["niveau"] == 3 and resume_seul["origine_texte"] is None
    assert resume_seul["licence"] is None and resume_seul["url_texte"] is None
    assert resume_seul["parties_lues"] == ["titre", "résumé"]


# --- Lecture des réponses ---------------------------------------------------------------------

def test_lire_europe_pmc():
    reponse = {"resultList": {"result": [
        {"pmid": "111", "pmcid": "PMC9", "license": "cc by", "isOpenAccess": "Y", "inEPMC": "Y"},
        {"pmid": "222", "isOpenAccess": "N"},
        {"id": "sans-pmid"},
    ]}}
    infos = acces.lire_europe_pmc(reponse)
    assert set(infos) == {"111", "222"}
    assert infos["111"]["pmcid"] == "PMC9" and infos["111"]["licence"] == "CC BY"
    assert infos["111"]["acces_ouvert"] is True and infos["222"]["acces_ouvert"] is False
    assert infos["222"]["pmcid"] == "" and infos["222"]["licence"] == "inconnue"
    assert acces.lire_europe_pmc({}) == {} and acces.lire_europe_pmc(None) == {}


def test_lire_pmcids_pubmed():
    xml = """<PubmedArticleSet>
      <PubmedArticle><MedlineCitation><PMID>111</PMID></MedlineCitation><PubmedData><ArticleIdList>
        <ArticleId IdType="pubmed">111</ArticleId><ArticleId IdType="pmc">PMC9</ArticleId>
        <ArticleId IdType="doi">10.1/x</ArticleId></ArticleIdList></PubmedData></PubmedArticle>
      <PubmedArticle><MedlineCitation><PMID>222</PMID></MedlineCitation><PubmedData><ArticleIdList>
        <ArticleId IdType="pubmed">222</ArticleId></ArticleIdList></PubmedData></PubmedArticle>
    </PubmedArticleSet>"""
    assert acces.lire_pmcids_pubmed(xml) == {"111": "PMC9"}


# --- Mesure -----------------------------------------------------------------------------------

def ligne(pmid, licence="inconnue", pmcid="", texte=None, kine=False, type_="essai_randomise", pubmed=""):
    return {"id": f"pm{pmid}", "pmid": pmid, "type": type_, "kine": kine, "decrit_europe": True,
            "pmcid_europe": pmcid, "pmcid_pubmed": pubmed or pmcid, "licence": licence,
            "acces_ouvert": bool(pmcid), "etat_texte": "ok" if texte else ("absent" if pmcid else "non_demande"),
            "texte": texte}


def test_resumer_compte_les_niveaux_par_perimetre():
    complet = acces.decrire_texte(article())
    lignes = [
        ligne("1", "CC BY", "PMC1", complet, kine=True),
        ligne("2", "CC BY-NC-ND", "PMC2", complet),
        ligne("3", "inconnue", "PMC3", None, type_="meta_analyse"),
        ligne("4", pubmed="PMC4"),
    ]
    r = mesure.resumer(lignes, prix_entree_par_million=1.0)
    assert r["fiches"] == 4 and r["fiches_kine"] == 1
    assert r["pmc_europe"] == 3 and r["pmc_pubmed"] == 4 and r["pmc_pubmed_seul"] == 1
    assert r["perimetres"]["strict"]["toutes"] == {"1": 1, "2": 0, "3": 3}
    assert r["perimetres"]["large"]["toutes"] == {"1": 2, "2": 0, "3": 2}
    assert r["perimetres"]["strict"]["kine"] == {"1": 1, "2": 0, "3": 0}
    assert r["par_type"]["meta_analyse"] == {"fiches": 1, "strict": 0, "large": 0}
    assert r["textes"]["nombre"] == 2 and r["textes"]["avec_methode_et_resultats"] == 2
    assert r["textes"]["cout_entree_usd"] >= 0


def test_rapport_lisible_et_sans_texte_d_article():
    complet = acces.decrire_texte(article())
    r = mesure.resumer([ligne("1", "CC BY", "PMC1", complet, kine=True), ligne("2")], 1.0)
    texte = mesure.rapport(r, {"semaine": "2026-S45", "mesure_le": "12/11/2026 à 09 h 00 UTC",
                               "delai_jours": 3, "echecs": 0, "champs_europe": ["isOpenAccess", "pmid"]})
    assert "# Niveaux d'accès — semaine 2026-S45" in texte
    assert "A. CC BY et CC0 seulement" in texte and "1 (50 %)" in texte
    assert "Volume total, estimé en jetons" in texte
    assert PHRASE.strip() not in texte


def test_choisir_semaine_refuse_une_valeur_invalide():
    assert mesure.choisir_semaine("2026-S45") == "2026-S45"
    with pytest.raises(SystemExit):
        mesure.choisir_semaine("2026-S45; rm -rf /")


def test_mesure_complete_sans_reseau(monkeypatch, tmp_path):
    """Le programme entier, avec des sources simulées : aucun appel au réseau."""
    def europe(pmids, journal=print, paquet=20):
        infos = {p: {"pmcid": "", "licence": "inconnue", "acces_ouvert": False, "champs": ["pmid"]} for p in pmids}
        infos[pmids[0]] = {"pmcid": "PMC1", "licence": "CC BY", "acces_ouvert": True, "champs": ["isOpenAccess"]}
        infos[pmids[1]] = {"pmcid": "PMC2", "licence": "CC BY-NC-ND", "acces_ouvert": True, "champs": ["pmid"]}
        return infos, 0

    monkeypatch.setattr(acces, "decrire_europe_pmc", europe)
    monkeypatch.setattr(acces, "pmcids_pubmed", lambda pmids, cfg, journal=print, paquet=200: ({pmids[0]: "PMC1"}, 0))
    monkeypatch.setattr(acces, "texte_integral_xml",
                        lambda pmcid: (article(), "ok") if pmcid == "PMC1" else (None, "absent"))
    monkeypatch.setattr(mesure.time, "sleep", lambda s: None)

    assert mesure.main(["--semaine", "2026-S45", "--limite", "5", "--sortie", str(tmp_path)]) == 0
    resultat = __import__("json").loads((tmp_path / "mesure-acces-2026-S45.json").read_text(encoding="utf-8"))
    assert resultat["resume"]["fiches"] == 5
    assert resultat["resume"]["perimetres"]["strict"]["toutes"] == {"1": 1, "2": 0, "3": 4}
    assert resultat["resume"]["etats_texte"] == {"ok": 1, "absent": 1}
    assert PHRASE.strip() not in (tmp_path / "mesure-acces-2026-S45.json").read_text(encoding="utf-8")
    assert "Niveaux d'accès — semaine 2026-S45" in (tmp_path / "mesure-acces-2026-S45.md").read_text(encoding="utf-8")


def test_mesure_s_arrete_a_la_duree_maximale(monkeypatch):
    """Passé la durée maximale, les textes restants sont notés « non mesuré », sans appel au réseau."""
    fiches = [{"id": f"pm{n}", "pmid": str(n), "type": "essai_randomise", "domaines": []} for n in (1, 2, 3)]
    monkeypatch.setattr(acces, "decrire_europe_pmc", lambda pmids, journal=print, paquet=20: (
        {p: {"pmcid": f"PMC{p}", "licence": "CC BY", "acces_ouvert": True, "champs": []} for p in pmids}, 0))
    monkeypatch.setattr(acces, "pmcids_pubmed", lambda pmids, cfg, journal=print, paquet=200: ({}, 0))
    demandes = []
    monkeypatch.setattr(acces, "texte_integral_xml", lambda pmcid: (demandes.append(pmcid), (article(), "ok"))[1])
    lectures = []  # l'horloge vaut 0 au départ et à la première fiche, puis 10 secondes
    monkeypatch.setattr(mesure.time, "monotonic", lambda: (lectures.append(1), 0 if len(lectures) <= 2 else 10)[1])
    monkeypatch.setattr(mesure.time, "sleep", lambda s: None)
    lignes, _ = mesure.mesurer(fiches, {}, journal=lambda m: None, duree_max=5)
    assert demandes == ["PMC1"]
    assert [l["etat_texte"] for l in lignes] == ["ok", "non_mesure", "non_mesure"]
