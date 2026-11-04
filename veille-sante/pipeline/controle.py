"""Contrôle automatique des fiches avant publication.

Une fiche non conforme est écartée et journalisée, jamais publiée.
"""
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

from . import regles
from .reseau import requete

# Nombres écrits en toutes lettres acceptés pour les petits entiers (0 à 10).
_MOTS_NOMBRES = {
    0: ("zero", "zéro", "no", "none", "aucun"),
    1: ("one", "single", "un", "une", "seul", "seule"),
    2: ("two", "both", "deux", "twice", "double", "dual"),
    3: ("three", "trois", "triple", "thrice"),
    4: ("four", "quatre"),
    5: ("five", "cinq"),
    6: ("six",),
    7: ("seven", "sept"),
    8: ("eight", "huit"),
    9: ("nine", "neuf"),
    10: ("ten", "dix"),
}

_NOMBRE = re.compile(r"(?<![\w.])[-−–]?\d+(?:[   ]\d{3})*(?:[.,]\d+)?")

CHAMPS_VERIFIES = (
    ("titre_fr",),
    ("flash",),
    ("standard", "resultats"),
    ("standard", "impact_clinique"),
    ("standard", "limites"),
    ("complet", "population"),
    ("complet", "intervention_comparateur"),
    ("complet", "criteres_jugement"),
    ("complet", "methode"),
    ("complet", "limites"),
    ("vulgarise", "flash"),
    ("vulgarise", "standard"),
    ("chiffres_cites",),
)


def _sans_accents(txt):
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")


def _formes(nombre_brut, source_anglaise):
    """Toutes les lectures possibles d'un nombre écrit (virgule décimale ou séparateur de milliers)."""
    n = nombre_brut.replace("−", "-").replace("–", "-")
    n = re.sub(r"[   ]", "", n)
    formes = set()
    if "," in n and "." not in n:
        entier, _, dec = n.partition(",")
        formes.add(f"{entier}.{dec}")              # virgule décimale
        if len(dec) == 3 and source_anglaise:
            formes.add(entier + dec)               # séparateur de milliers (1,234)
    else:
        formes.add(n)
    canon = set()
    for f in formes:
        f = f.lstrip("-")
        try:
            v = float(f)
        except ValueError:
            continue
        canon.add(repr(v))
    return canon


def nombres_du_texte(texte, source_anglaise=False):
    trouves = set()
    for m in _NOMBRE.finditer(texte or ""):
        trouves |= _formes(m.group(0), source_anglaise)
    return trouves


def _petits_entiers_en_lettres(texte):
    mots = set(re.findall(r"[a-zà-ÿ]+", _sans_accents((texte or "").lower())))
    return {repr(float(n)) for n, variantes in _MOTS_NOMBRES.items()
            if any(_sans_accents(v) in mots for v in variantes)}


def nombres_autorises(ref):
    morceaux = [ref.get("titre", ""), ref.get("resume", ""), ref.get("revue", ""),
                " ".join(ref.get("mesh", []))]
    source = "\n".join(morceaux)
    autorises = nombres_du_texte(source, source_anglaise=True)
    autorises |= nombres_du_texte(source, source_anglaise=False)
    autorises |= _petits_entiers_en_lettres(source)
    for meta in (ref.get("annee"), ref.get("pmid")):
        if meta:
            autorises |= nombres_du_texte(str(meta))
    return autorises


def _valeur(fiche, chemin):
    v = fiche
    for cle in chemin:
        if not isinstance(v, dict):
            return None
        v = v.get(cle)
    return v


def _textes(valeur):
    if valeur is None:
        return []
    if isinstance(valeur, str):
        return [valeur]
    if isinstance(valeur, (list, tuple)):
        return [str(x) for x in valeur]
    return [str(valeur)]


def chiffres_non_sources(fiche, ref):
    """Nombres présents dans la fiche mais absents de la source."""
    autorises = nombres_autorises(ref)
    absents = []
    for chemin in CHAMPS_VERIFIES:
        for texte in _textes(_valeur(fiche, chemin)):
            for m in _NOMBRE.finditer(texte):
                if not (_formes(m.group(0), False) & autorises):
                    absents.append(f"{'.'.join(chemin)} : {m.group(0)}")
    return absents


def _non_vide(v):
    return isinstance(v, str) and v.strip() != ""


def verifier_structure(fiche):
    erreurs = []
    if not _non_vide(fiche.get("titre_fr")):
        erreurs.append("titre_fr manquant")
    if fiche.get("etiquette") not in regles.ETIQUETTES:
        erreurs.append("etiquette invalide")
    if fiche.get("verdict") not in regles.VERDICTS:
        erreurs.append("verdict invalide")
    if not _non_vide(fiche.get("flash")):
        erreurs.append("flash manquant")
    elif len(fiche["flash"].split()) > 60:
        erreurs.append("flash trop long")
    std = fiche.get("standard")
    if not isinstance(std, dict):
        erreurs.append("standard manquant")
    else:
        if not _non_vide(std.get("resultats")):
            erreurs.append("standard.resultats manquant")
        if not _non_vide(std.get("impact_clinique")):
            erreurs.append("impact clinique manquant")
        if not isinstance(std.get("limites"), list) or not std["limites"]:
            erreurs.append("limites manquantes")
    comp = fiche.get("complet")
    if not isinstance(comp, dict):
        erreurs.append("complet manquant")
    else:
        for champ in ("population", "intervention_comparateur", "criteres_jugement", "methode"):
            if not _non_vide(comp.get(champ)):
                erreurs.append(f"complet.{champ} manquant")
    vulg = fiche.get("vulgarise")
    if vulg is not None and not (isinstance(vulg, dict) and _non_vide(vulg.get("flash"))):
        erreurs.append("vulgarise mal formé")
    return erreurs


def controler_fiche(fiche_ia, ref, tri, cfg_preuve=None):
    """Applique les règles et contrôles. Renvoie (fiche_publiable | None, erreurs)."""
    erreurs = verifier_structure(fiche_ia)
    if erreurs:
        return None, erreurs
    absents = chiffres_non_sources(fiche_ia, ref)
    if absents:
        return None, ["chiffres absents de la source : " + "; ".join(absents[:6])]

    depart = tri["etiquette_depart"]
    etiquette = regles.plafonner_etiquette(fiche_ia["etiquette"], depart)
    verdict = regles.verdict_autorise(fiche_ia["verdict"], tri["type_etude"], etiquette)
    vulgarise = fiche_ia.get("vulgarise") if tri.get("pertinence") == 3 else None

    fiche = {
        "id": ref["id"],
        "source": ref["source"],
        "pmid": ref.get("pmid", ""),
        "doi": ref.get("doi", ""),
        "url": ref["url"],
        "titre": ref["titre"],
        "titre_fr": fiche_ia["titre_fr"].strip(),
        "revue": ref.get("revue", ""),
        "revue_abrege": ref.get("revue_abrege", ""),
        "annee": ref.get("annee", ""),
        "mois": ref.get("mois", ""),
        "volume": ref.get("volume", ""),
        "numero": ref.get("numero", ""),
        "pages": ref.get("pages", ""),
        "auteurs": ref.get("auteurs", [])[:30],
        "type": tri["type_etude"],
        "pertinence": tri["pertinence"],
        "domaines": tri["domaines"],
        "etiquette": etiquette,
        "justification_etiquette": fiche_ia.get("justification_etiquette", "").strip(),
        "verdict": verdict,
        "flash": fiche_ia["flash"].strip(),
        "standard": {
            "resultats": fiche_ia["standard"]["resultats"].strip(),
            "impact_clinique": fiche_ia["standard"]["impact_clinique"].strip(),
            "limites": [str(x).strip() for x in fiche_ia["standard"]["limites"] if str(x).strip()],
        },
        "complet": {k: (v.strip() if isinstance(v, str) else v)
                    for k, v in fiche_ia["complet"].items()},
        "vulgarise": vulgarise,
        "incertitudes": fiche_ia.get("incertitudes") or None,
    }
    if regles.est_grande_nouveaute(fiche) and "transversal/grandes-nouveautes" not in fiche["domaines"]:
        fiche["domaines"] = fiche["domaines"] + ["transversal/grandes-nouveautes"]
    return fiche, []


# --- Vérifications externes (Crossref) -------------------------------------------------

def _similarite(a, b):
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", _sans_accents((s or "").lower()))
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def verifier_doi(fiche, email=""):
    """Renvoie (doi_conserve, motif_exclusion). Une panne réseau ne pénalise pas la fiche."""
    doi = fiche.get("doi")
    if not doi:
        return "", None
    params = {"mailto": email} if email else {}
    try:
        rep = requete("GET", f"https://api.crossref.org/works/{doi}", params=params, tentatives=2)
        titre_cr = " ".join(rep.json()["message"].get("title") or [])
        if titre_cr and _similarite(titre_cr, fiche["titre"]) < 0.6:
            doi = ""          # DOI incohérent : on ne garde que le lien PubMed
    except Exception as e:
        if "404" in str(e):
            doi = ""
    try:
        rep = requete("GET", "https://api.crossref.org/works",
                      params={**params, "filter": f"updates:{fiche['doi']}", "rows": 20}, tentatives=2)
        for notice in rep.json()["message"].get("items", []):
            for maj in notice.get("update-to", []):
                if maj.get("type") in ("retraction", "removal", "withdrawal"):
                    return doi, "article rétracté (Crossref)"
    except Exception:
        pass
    return doi, None


def verifier_externe(fiches, email="", journal=print, simultanes=5):
    gardees, exclues = [], []

    def un(fiche):
        return fiche, verifier_doi(fiche, email)

    with ThreadPoolExecutor(simultanes) as ex:
        for fiche, (doi, motif) in ex.map(un, fiches):
            if motif:
                exclues.append({"id": fiche["id"], "motif": motif})
                continue
            if fiche.get("doi") and not doi:
                journal(f"{fiche['id']} : DOI non confirmé par Crossref, lien PubMed seul")
            fiche["doi"] = doi
            gardees.append(fiche)
    return gardees, exclues
