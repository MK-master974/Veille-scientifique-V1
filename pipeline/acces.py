"""Accès au texte intégral légal d'une publication et niveau d'accès documentaire.

Phase 1, séance 4. Ce module n'est pas appelé par la veille hebdomadaire : il sert à la mesure
des niveaux d'accès (banc/mesure_acces.py) et servira à la future chaîne d'analyse, pour remplir
le bloc « acces » d'une fiche v2 (docs/FICHE_V2.md).

Sources interrogées, toutes ouvertes et sans clé :
- Europe PMC, recherche : identifiant PMC, licence déclarée, accès ouvert ;
- Europe PMC, texte intégral en XML : seulement pour les articles qu'il diffuse en accès ouvert ;
- PubMed, efetch : identifiant PMC connu de PubMed, pour recouper.

Le texte d'un article n'est jamais gardé : seules des mesures de sa structure le sont. Aucun
accès payant, aucune authentification ni aucune restriction n'est contourné.
"""
import re
import time
import xml.etree.ElementTree as ET

import requests

from .collecte import EUTILS, _parametres_ncbi, _pause
from .reseau import requete

EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"

# Périmètres de licences étudiés lors de la mesure du 12 novembre 2026.
PERIMETRES = {
    "strict": ("CC0", "CC BY"),
    "intermediaire": ("CC0", "CC BY", "CC BY-SA", "CC BY-NC", "CC BY-NC-SA"),
    "large": ("CC0", "CC BY", "CC BY-SA", "CC BY-NC", "CC BY-NC-SA", "CC BY-ND", "CC BY-NC-ND"),
}

# Périmètre retenu par le porteur du projet le 12 novembre 2026 (VS-D21) : une fiche n'est analysée
# sur le texte intégral que si l'article est sous licence CC BY ou CC0. Les autres licences sont
# soumises à l'avis juridique commun.
PERIMETRE_RETENU = PERIMETRES["strict"]

# En dessous de ces seuils, un texte récupéré est compté « partiel » (niveau 2).
SEUIL_CARACTERES = 5000
SEUIL_SECTIONS = 2

_METHODE = re.compile(r"method|material|participants|study design|méthod|matériel", re.I)
_RESULTATS = re.compile(r"result|findings|résultat", re.I)


# --- Licences ---------------------------------------------------------------------------------

def classe_licence(brute):
    """Ramène une licence déclarée (« cc by-nc », adresse Creative Commons…) à une classe fixe."""
    texte = (brute or "").strip().lower()
    if not texte:
        return "inconnue"
    if "publicdomain/zero" in texte or re.match(r"cc[\s-]?0\b", texte) or texte in ("cc zero", "public domain"):
        return "CC0"
    mots = re.findall(r"[a-z0-9]+", texte)
    if "licenses" in mots:
        mots = mots[mots.index("licenses") + 1:]
    elif mots and mots[0] == "cc":
        mots = mots[1:]
    else:
        return "autre"
    clauses = {m for m in mots if m in ("by", "nc", "nd", "sa")}
    if "by" not in clauses:
        return "autre"
    nom = "CC BY"
    if "nc" in clauses:
        nom += "-NC"
    if "nd" in clauses:
        nom += "-ND"
    elif "sa" in clauses:
        nom += "-SA"
    return nom


# --- Structure d'un texte intégral ------------------------------------------------------------

def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def decrire_texte(xml_txt):
    """Mesure la structure d'un article au format JATS, sans en garder le texte.

    Renvoie None si le XML est illisible.
    """
    try:
        racine = ET.fromstring(xml_txt)
    except (ET.ParseError, TypeError, ValueError):
        return None
    corps = next((e for e in racine.iter() if _local(e.tag) == "body"), None)
    mesures = {"corps": corps is not None, "caracteres": 0, "sections": 0, "methode": False,
               "resultats": False, "tableaux": 0, "figures": 0, "references": 0}
    for e in racine.iter():
        nom = _local(e.tag)
        if nom == "table-wrap":
            mesures["tableaux"] += 1
        elif nom == "fig":
            mesures["figures"] += 1
        elif nom == "ref":
            mesures["references"] += 1
    if corps is None:
        return mesures
    mesures["caracteres"] = len(re.sub(r"\s+", " ", "".join(corps.itertext())).strip())
    mesures["sections"] = sum(1 for e in corps if _local(e.tag) == "sec")
    for sec in corps.iter():
        if _local(sec.tag) != "sec":
            continue
        titre = next(("".join(e.itertext()) for e in sec if _local(e.tag) == "title"), "")
        repere = f"{sec.get('sec-type') or ''} {titre}"
        if _METHODE.search(repere):
            mesures["methode"] = True
        if _RESULTATS.search(repere):
            mesures["resultats"] = True
    return mesures


# --- Niveau d'accès ---------------------------------------------------------------------------

def niveau_acces(pmcid, licence, texte, perimetre):
    """Niveau d'accès documentaire (1, 2 ou 3) et son motif, pour un périmètre de licences donné.

    1 : texte intégral lisible ; 2 : texte partiel ; 3 : résumé uniquement.
    """
    if not pmcid:
        return 3, "aucune version dans PubMed Central"
    if licence not in perimetre:
        return 3, f"licence hors périmètre ({licence})"
    if not texte:
        return 3, "texte intégral non récupéré"
    if texte["corps"] and texte["caracteres"] >= SEUIL_CARACTERES and texte["sections"] >= SEUIL_SECTIONS:
        return 1, "texte intégral lisible"
    return 2, "texte partiel : corps absent ou très court"


def bloc_acces(pmcid, licence, texte, perimetre, consulte_le):
    """Bloc « acces » d'une fiche v2 (docs/FICHE_V2.md)."""
    niveau, _ = niveau_acces(pmcid, licence, texte, perimetre)
    lues, non_lues = ["titre", "résumé"], []
    if niveau == 1:
        lues.append("texte intégral")
        if texte["tableaux"]:
            lues.append("tableaux")
        non_lues.append("annexes et documents supplémentaires")
    elif niveau == 2:
        lues.append("texte partiel")
        non_lues += ["parties manquantes du texte", "annexes et documents supplémentaires"]
    else:
        non_lues += ["méthode détaillée", "résultats détaillés", "tableaux", "analyses complémentaires"]
    lu = niveau < 3
    return {
        "niveau": niveau,
        "origine_texte": "europe_pmc" if lu else None,
        "url_texte": f"https://europepmc.org/article/PMC/{pmcid}" if lu else None,
        "licence": licence if lu else None,
        "consulte_le": consulte_le,
        "parties_lues": lues,
        "parties_non_lues": non_lues,
    }


# --- Lecture des réponses ---------------------------------------------------------------------

def lire_europe_pmc(reponse):
    """Réponse JSON d'une recherche Europe PMC → {pmid: description}."""
    infos = {}
    for r in ((reponse or {}).get("resultList") or {}).get("result") or []:
        pmid = str(r.get("pmid") or "")
        if not pmid:
            continue
        ouvert = r.get("isOpenAccess")
        infos[pmid] = {
            "pmcid": r.get("pmcid") or "",
            "licence_brute": r.get("license") or "",
            "licence": classe_licence(r.get("license")),
            "acces_ouvert": None if ouvert is None else str(ouvert).upper() == "Y",
            "dans_europe_pmc": str(r.get("inEPMC") or "").upper() == "Y",
            "champs": sorted(r.keys()),
        }
    return infos


def lire_pmcids_pubmed(xml_txt):
    """Réponse XML d'un efetch PubMed → {pmid: identifiant PMC}, pour les articles qui en ont un."""
    pmcids = {}
    for art in ET.fromstring(xml_txt).iter("PubmedArticle"):
        pmid = (art.findtext("MedlineCitation/PMID") or "").strip()
        for aid in art.findall("PubmedData/ArticleIdList/ArticleId"):
            if aid.get("IdType") == "pmc" and pmid and (aid.text or "").strip():
                pmcids[pmid] = aid.text.strip()
    return pmcids


# --- Réseau -----------------------------------------------------------------------------------

def decrire_europe_pmc(pmids, journal=print, paquet=20):
    """Identifiant PMC, licence et accès ouvert de chaque PMID, lus par paquets dans Europe PMC."""
    infos, echecs = {}, 0
    for i in range(0, len(pmids), paquet):
        lot = pmids[i:i + paquet]
        recherche = "(" + " OR ".join(f"EXT_ID:{p}" for p in lot) + ") AND SRC:MED"
        try:
            rep = requete("GET", f"{EUROPE_PMC}/search", params={
                "query": recherche, "format": "json", "resultType": "core", "pageSize": 100})
            infos.update(lire_europe_pmc(rep.json()))
        except (requests.RequestException, RuntimeError, ValueError) as e:
            echecs += 1
            journal(f"  Europe PMC, paquet {i // paquet + 1} : échec ({e})")
        time.sleep(0.3)
    return infos, echecs


def texte_integral_xml(pmcid):
    """XML du texte intégral diffusé par Europe PMC en accès ouvert, et l'état de la demande.

    L'état vaut « ok », « absent » (Europe PMC ne diffuse pas ce texte) ou « echec » (panne).
    """
    try:
        rep = requete("GET", f"{EUROPE_PMC}/{pmcid}/fullTextXML", tentatives=2, timeout=30)
    except requests.HTTPError as e:
        absent = e.response is not None and e.response.status_code in (403, 404)
        return None, "absent" if absent else "echec"
    except (requests.RequestException, RuntimeError):
        return None, "echec"
    return rep.text, "ok"


def pmcids_pubmed(pmids, cfg, journal=print, paquet=200):
    """Identifiant PMC connu de PubMed pour chaque PMID, pour recouper avec Europe PMC."""
    pmcids, echecs = {}, 0
    for i in range(0, len(pmids), paquet):
        lot = pmids[i:i + paquet]
        try:
            rep = requete("POST", f"{EUTILS}/efetch.fcgi", data={
                **_parametres_ncbi(cfg), "db": "pubmed", "id": ",".join(lot), "retmode": "xml"})
            pmcids.update(lire_pmcids_pubmed(rep.text))
        except (requests.RequestException, RuntimeError, ET.ParseError) as e:
            echecs += 1
            journal(f"  PubMed, paquet {i // paquet + 1} : échec ({e})")
        _pause()
    return pmcids, echecs
