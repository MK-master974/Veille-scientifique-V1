"""Collecte des références de la semaine : PubMed (API E-utilities) et HAS (flux RSS).

L'IA ne cherche jamais elle-même : toutes les références viennent d'ici,
avec leurs métadonnées officielles (identifiants, titre, résumé, revue).
"""
import hashlib
import html
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from .reseau import requete

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
FLUX_HAS = "https://www.has-sante.fr/feed/Rss2.jsp?id=p_3081452"

TYPES_RECHERCHES = (
    "systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt] "
    "OR guideline[pt] OR practice guideline[pt] OR Diagnosis/Narrow[filter]"
)
TYPES_EXCLUS = (
    "retracted publication[pt] OR retraction of publication[pt] OR comment[pt] OR letter[pt] "
    "OR editorial[pt] OR clinical trial protocol[pt] OR preprint[pt] OR published erratum[pt]"
)


def requete_pubmed(semaine, langues=("eng", "fre")):
    """Construit la requête PubMed pour une semaine (date d'entrée dans PubMed)."""
    debut = semaine.lundi.strftime("%Y/%m/%d")
    fin = semaine.dimanche.strftime("%Y/%m/%d")
    filtre_langue = " OR ".join(f"{lg}[la]" for lg in langues)
    return (
        f"({debut}:{fin}[edat]) AND ({TYPES_RECHERCHES}) AND hasabstract "
        f"AND ({filtre_langue}) "
        f"NOT ({TYPES_EXCLUS}) "
        f"NOT (animals[mh] NOT humans[mh])"
    )


def _parametres_ncbi(cfg):
    p = {"tool": "veille-sante"}
    if cfg.get("email_contact"):
        p["email"] = cfg["email_contact"]
    if os.environ.get("NCBI_API_KEY"):
        p["api_key"] = os.environ["NCBI_API_KEY"]
    return p


def _pause():
    time.sleep(0.12 if os.environ.get("NCBI_API_KEY") else 0.4)


def collecter_pubmed(semaine, cfg, journal=print):
    base = _parametres_ncbi(cfg)
    terme = requete_pubmed(semaine, cfg["collecte"].get("langues", ["eng", "fre"]))
    rep = requete("POST", f"{EUTILS}/esearch.fcgi", data={
        **base, "db": "pubmed", "term": terme, "usehistory": "y",
        "retmax": 0, "retmode": "json",
    }).json()["esearchresult"]
    total = int(rep["count"])
    maximum = int(cfg["collecte"].get("max_references", 6000))
    journal(f"PubMed : {total} références trouvées pour {semaine.id}")
    if total > maximum:
        journal(f"PubMed : plafond de {maximum} références atteint, le reste est ignoré")
    references = []
    pas = 200
    for debut in range(0, min(total, maximum), pas):
        _pause()
        xml_txt = requete("POST", f"{EUTILS}/efetch.fcgi", data={
            **base, "db": "pubmed", "query_key": rep["querykey"], "WebEnv": rep["webenv"],
            "retstart": debut, "retmax": pas, "retmode": "xml",
        }).text
        references.extend(analyser_xml_pubmed(xml_txt))
    return references


def _texte(element):
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


_MOIS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _date_pub(article):
    pd = article.find("Article/Journal/JournalIssue/PubDate")
    if pd is None:
        return "", ""
    annee = _texte(pd.find("Year")) or _texte(pd.find("MedlineDate"))[:4]
    mois = _texte(pd.find("Month"))
    if mois and not mois.isdigit():
        mois = str(_MOIS.get(mois[:3].lower(), ""))
    return annee, mois


def analyser_xml_pubmed(xml_txt):
    """Transforme la réponse XML d'efetch en références normalisées."""
    racine = ET.fromstring(xml_txt)
    refs = []
    for art in racine.findall("PubmedArticle"):
        cit = art.find("MedlineCitation")
        pmid = _texte(cit.find("PMID"))
        a = cit.find("Article")
        types = [_texte(t) for t in a.findall("PublicationTypeList/PublicationType")]
        corrections = {c.get("RefType") for c in cit.findall("CommentsCorrectionsList/CommentsCorrections")}
        if corrections & {"RetractionIn", "ExpressionOfConcernIn"}:
            continue
        if "Retracted Publication" in types:
            continue
        morceaux = []
        for bloc in a.findall("Abstract/AbstractText"):
            label = bloc.get("Label")
            txt = _texte(bloc)
            morceaux.append(f"{label}: {txt}" if label else txt)
        resume = "\n".join(m for m in morceaux if m)
        if not resume:
            continue
        doi = ""
        for aid in art.findall("PubmedData/ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi":
                doi = _texte(aid)
        if not doi:
            for eid in a.findall("ELocationID"):
                if eid.get("EIdType") == "doi":
                    doi = _texte(eid)
        auteurs = []
        for au in a.findall("AuthorList/Author"):
            if au.find("CollectiveName") is not None:
                auteurs.append(_texte(au.find("CollectiveName")))
            else:
                nom = _texte(au.find("LastName"))
                ini = _texte(au.find("Initials"))
                if nom:
                    auteurs.append(f"{nom} {ini}".strip())
        annee, mois = _date_pub(cit)
        ji = a.find("Journal/JournalIssue")
        refs.append({
            "id": f"pm{pmid}",
            "source": "pubmed",
            "pmid": pmid,
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "titre": _texte(a.find("ArticleTitle")).rstrip(),
            "resume": resume,
            "revue": _texte(a.find("Journal/Title")),
            "revue_abrege": _texte(a.find("Journal/ISOAbbreviation")),
            "annee": annee,
            "mois": mois,
            "volume": _texte(ji.find("Volume")) if ji is not None else "",
            "numero": _texte(ji.find("Issue")) if ji is not None else "",
            "pages": _texte(a.find("Pagination/MedlinePgn")),
            "auteurs": auteurs,
            "types_publication": types,
            "langue": _texte(a.find("Language")),
            "mesh": [_texte(m.find("DescriptorName")) for m in cit.findall("MeshHeadingList/MeshHeading")],
        })
    return refs


def _texte_html(fragment):
    fragment = re.sub(r"(?is)<(script|style|nav|header|footer|form)[^>]*>.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", fragment)
    texte = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    texte = re.sub(r"[ \t\xa0]+", " ", texte)
    return re.sub(r"\n\s*\n+", "\n", texte).strip()


def collecter_has(semaine, cfg, journal=print):
    """Recommandations et guides de la HAS mis en ligne pendant la semaine."""
    tz = ZoneInfo(cfg.get("publication", {}).get("fuseau", "Europe/Paris"))
    try:
        flux = requete("GET", FLUX_HAS).text
    except Exception as e:  # la HAS ne doit pas bloquer toute la veille
        journal(f"HAS : flux indisponible ({e}), on continue sans")
        return []
    racine = ET.fromstring(flux)
    refs = []
    for item in racine.iter("item"):
        titre = _texte(item.find("title"))
        lien = _texte(item.find("link"))
        date_txt = _texte(item.find("pubDate"))
        try:
            jour = parsedate_to_datetime(date_txt).astimezone(tz).date()
        except (TypeError, ValueError):
            continue
        if not semaine.contient(jour):
            continue
        description = _texte_html(_texte(item.find("description")))
        contenu = description
        try:
            page = requete("GET", lien).text
            principal = re.search(r"(?is)<main[^>]*>(.*?)</main>", page)
            contenu = _texte_html(principal.group(1) if principal else page)[:8000] or description
        except Exception:
            pass
        ident = hashlib.sha1(lien.encode()).hexdigest()[:10]
        refs.append({
            "id": f"has{ident}",
            "source": "has",
            "pmid": "",
            "doi": "",
            "url": lien,
            "titre": titre,
            "resume": contenu,
            "revue": "Haute Autorité de santé",
            "revue_abrege": "HAS",
            "annee": str(jour.year),
            "mois": str(jour.month),
            "volume": "", "numero": "", "pages": "",
            "auteurs": ["Haute Autorité de santé"],
            "types_publication": ["Recommandation HAS"],
            "langue": "fre",
            "mesh": [],
            "date_mise_en_ligne": jour.isoformat(),
        })
    journal(f"HAS : {len(refs)} publication(s) cette semaine")
    return refs


def collecter(semaine, cfg, journal=print):
    refs = []
    if cfg["collecte"].get("pubmed", True):
        refs += collecter_pubmed(semaine, cfg, journal)
    if cfg["collecte"].get("has", True):
        refs += collecter_has(semaine, cfg, journal)
    vus, uniques = set(), []
    for r in refs:
        cle = r["doi"].lower() or r["id"]
        if cle in vus:
            continue
        vus.add(cle)
        uniques.append(r)
    # Les types les plus utiles d'abord : si le budget coupe la liste, c'est la fin qui saute.
    uniques.sort(key=priorite_collecte)
    return uniques


def priorite_collecte(ref):
    types = set(ref.get("types_publication", []))
    if ref["source"] == "has" or types & {"Guideline", "Practice Guideline"}:
        return 0
    if types & {"Systematic Review", "Meta-Analysis"}:
        return 1
    if "Randomized Controlled Trial" in types:
        return 2
    return 3


def date_collecte():
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
