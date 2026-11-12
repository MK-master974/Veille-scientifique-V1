"""Chiffres déjà relevés par les auteurs d'une revue : lecture du corpus et comparaison de nombres.

Renforcement du corpus de référence (VS-D32). Pour une étude diagnostique ou une méta-analyse, le
corrigé est fait des chiffres que les auteurs d'une revue en accès libre ont relevés dans leurs
tableaux : effectif, sensibilité, spécificité, effet groupé, bornes de l'intervalle de confiance.

Ce module ne contient que des fonctions pures, testées sans réseau. Les règles de comparaison sont
fixées avant toute mesure (VS-D34) et servent trois fois, à l'identique :
- le chiffre du corrigé est-il bien dans la ligne du tableau de la revue source (recopie) ?
- est-il dans l'article lui-même (sinon il est écarté du score, et compté à part) ?
- est-il dans les données extraites par l'IA (c'est la mesure) ?

Règles de comparaison de deux nombres :
1. le signe est ignoré : une revue écrit souvent « 29,6 » là où l'article écrit « −29,56 » ;
2. l'arrondi est toléré : « 29,56 » correspond à « 29,6 », et « 0,943 » à « 0,94 ». Un nombre moins
   précis que le corrigé n'est accepté que s'il lui manque une seule décimale et s'il garde au moins
   deux chiffres significatifs : « 3 » ne correspond pas à « 2,63 » ;
3. pour une proportion (sensibilité, spécificité, valeurs prédictives, aire sous la courbe), une
   fraction et un pourcentage se valent : « 0,94 » correspond à « 94 % » ;
4. rien d'autre n'est toléré : aucun calcul, aucune conversion d'unité.
"""
import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CORPUS = RACINE / "banc" / "corpus" / "chiffres_releves.json"

# Seuil fixé par le porteur du projet le 12 novembre 2026 (VS-D34), sur le texte intégral.
SEUIL_RETROUVES = 0.80

# Nature d'un chiffre → zone de l'extraction où il est attendu, et s'il s'agit d'une proportion.
NATURES = {
    "effectif": ("effectif", False),              # participants de l'étude ou de la revue
    "nombre_etudes": ("effectif", False),         # études incluses dans la revue
    "sensibilite": ("resultats", True),
    "specificite": ("resultats", True),
    "valeur_predictive_positive": ("resultats", True),
    "valeur_predictive_negative": ("resultats", True),
    "aire_sous_la_courbe": ("resultats", True),
    "rapport_de_vraisemblance": ("resultats", False),
    "effet": ("resultats", False),                # effet groupé d'une méta-analyse
    "ic_bas": ("resultats", False),
    "ic_haut": ("resultats", False),
}
TYPES_ETUDE = ("etude_diagnostique", "meta_analyse", "revue_systematique")

_MOINS = "-−–‐‑‒"
# Espaces qui séparent les milliers dans un nombre : insécable, fine insécable, fine.
_ESPACES = "   "
# Un nombre écrit en chiffres : « 1 029 », « 1,029 », « 0.94 », « .05 », « 29·6 » (point médian).
_NOMBRE = re.compile(rf"(?<![\w.,·])[{_MOINS}]?(?:\d+(?:[{_ESPACES}]\d{{3}})*(?:[.,·]\d+)?|[.,·]\d+)")
# « 1 029 » écrit avec une espace ordinaire : lu aussi comme un seul nombre, en plus de « 1 » et « 029 ».
_MILLIERS_ESPACES = re.compile(r"(?<![\w.,·])\d{1,3}(?: \d{3})+(?!\d)")
_CORRIGE = re.compile(r"\d+(?:\.\d+)?")


def lectures(brut):
    """Toutes les lectures d'un nombre écrit : liste de (valeur absolue, nombre de décimales).

    « 1,029 » se lit 1,029 (virgule décimale) ou 1 029 (séparateur de milliers) : les deux lectures
    sont gardées, car le texte peut être en français ou en anglais.
    """
    n = re.sub(rf"[{_MOINS}{_ESPACES} ]", "", brut).replace("·", ".")
    formes = []
    if "," in n and "." not in n:
        entier, _, dec = n.partition(",")
        formes.append((f"{entier or '0'}.{dec}", len(dec)))
        if len(dec) == 3 and entier:
            formes.append((entier + dec, 0))
    elif "," in n and "." in n:                      # « 1,029.5 » : la virgule sépare les milliers
        sans = n.replace(",", "")
        formes.append((sans, len(sans.partition(".")[2])))
    else:
        formes.append((n if not n.startswith(".") else "0" + n, len(n.partition(".")[2])))
    resultat = []
    for texte, decimales in formes:
        try:
            resultat.append((abs(float(texte)), decimales))
        except ValueError:
            pass
    return resultat


def nombres(texte):
    """Tous les nombres d'un texte, sous toutes leurs lectures : liste de (valeur, décimales)."""
    trouves = []
    for m in _NOMBRE.finditer(texte or ""):
        trouves.extend(lectures(m.group(0)))
    for m in _MILLIERS_ESPACES.finditer(texte or ""):
        trouves.extend(lectures(m.group(0)))
    return trouves


def _significatifs(valeur, decimales):
    """Nombre de chiffres significatifs d'un nombre écrit avec « decimales » décimales."""
    chiffres = f"{valeur:.{decimales}f}".replace(".", "").lstrip("0")
    return len(chiffres)


def _egaux(a, dec_a, c, dec_c):
    """Vrai si le nombre « a » correspond au chiffre « c » du corrigé, à l'arrondi près."""
    tolerance = 0.5 * 10 ** (-dec_c) + 1e-9
    if dec_a >= dec_c:
        return abs(a - c) <= tolerance              # le nombre est aussi précis que le corrigé, ou plus
    # Le nombre est moins précis que le corrigé : une seule décimale de moins, deux chiffres au moins.
    if dec_a == dec_c - 1 and _significatifs(a, dec_a) >= 2:
        return abs(a - c) <= 0.5 * 10 ** (-dec_a) + 1e-9
    return False


def correspond(candidat, corrige, proportion=False):
    """Vrai si un nombre lu, (valeur, décimales), correspond à un chiffre du corrigé, (valeur, décimales)."""
    a, dec_a = candidat
    c, dec_c = corrige
    if _egaux(a, dec_a, c, dec_c):
        return True
    if proportion:
        # Fraction et pourcentage : « 0,94 » et « 94 % ». Les décimales suivent la conversion.
        if _egaux(a / 100, dec_a + 2, c, dec_c) or _egaux(a * 100, max(dec_a - 2, 0), c, dec_c):
            return True
    return False


def valeur_corrige(chiffre):
    """Le chiffre du corrigé sous forme (valeur, décimales).

    Dans le corpus, un chiffre s'écrit sans signe ni séparateur de milliers, avec un point décimal
    (« 1029 », « 0.94 ») : une seule lecture est possible.
    """
    brut = str(chiffre["valeur"]).strip()
    if not _CORRIGE.fullmatch(brut):
        raise ValueError(f"chiffre mal écrit dans le corrigé : {chiffre['valeur']!r}")
    return float(brut), len(brut.partition(".")[2])


def present(chiffre, texte):
    """Vrai si le chiffre du corrigé figure dans un texte, selon les règles de comparaison."""
    cible = valeur_corrige(chiffre)
    proportion = NATURES[chiffre["nature"]][1]
    return any(correspond(n, cible, proportion) for n in nombres(texte))


# --- Corpus -----------------------------------------------------------------------------------

def charger(chemin=CORPUS):
    """Le corpus des chiffres relevés. Renvoie un corpus vide si le fichier n'existe pas encore."""
    if not Path(chemin).exists():
        return {"groupes": []}
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def cas_du_corpus(corpus):
    """Liste à plat des cas : chacun porte son type d'étude et sa revue source."""
    return [{**c, "type_etude": g["type_etude"], "source": g["source"]}
            for g in corpus.get("groupes", []) for c in g.get("cas", [])]


def verifier_forme(corpus):
    """Défauts de forme du corpus : liste de phrases, vide si tout est en ordre."""
    defauts, vus = [], set()
    for g in corpus.get("groupes", []):
        if g.get("type_etude") not in TYPES_ETUDE:
            defauts.append(f"type d'étude inconnu : {g.get('type_etude')!r}")
        source = g.get("source") or {}
        for cle in ("pmid", "pmcid", "licence", "tableau"):
            if not source.get(cle):
                defauts.append(f"revue source sans « {cle} » : {source.get('pmid')}")
        for c in g.get("cas", []):
            ident = c.get("pmid")
            if not ident or not c.get("pmcid") or not c.get("licence"):
                defauts.append(f"cas incomplet (pmid, pmcid ou licence) : {ident}")
            if ident in vus:
                defauts.append(f"cas en double : {ident}")
            vus.add(ident)
            identifiants = set()
            for x in c.get("chiffres", []):
                if x.get("nature") not in NATURES:
                    defauts.append(f"{ident} : nature inconnue {x.get('nature')!r}")
                    continue
                if x.get("id") in identifiants or not x.get("id"):
                    defauts.append(f"{ident} : identifiant de chiffre absent ou en double ({x.get('id')!r})")
                identifiants.add(x.get("id"))
                if not _CORRIGE.fullmatch(str(x.get("valeur", "")).strip()):
                    defauts.append(f"{ident} : valeur mal écrite {x.get('valeur')!r} (attendu : 1029, 0.94)")
                if x.get("dans_l_article") not in (True, False, None):
                    defauts.append(f"{ident} : « dans_l_article » doit valoir true, false ou null")
            if not c.get("chiffres"):
                defauts.append(f"{ident} : aucun chiffre")
    return defauts


# --- Mesure -----------------------------------------------------------------------------------

def zones_extraction(e):
    """Texte des deux zones d'une extraction où un chiffre du corrigé peut se trouver."""
    if e is None:
        return {"effectif": "", "resultats": ""}
    simples = [e.get(c) for c in ("effectif", "population", "question")]
    effectif = " ; ".join(d["valeur"] for d in simples if d)
    resultats = " ; ".join(" | ".join(str(r.get(c) or "") for c in ("critere", "valeur", "intervalle"))
                           for r in e.get("resultats", []))
    return {"effectif": effectif, "resultats": resultats}


def mesurer_cas(cas, e):
    """Compare l'extraction d'un article aux chiffres de son corrigé.

    Renvoie une ligne par chiffre : « retrouve » (dans la zone attendue), « ailleurs » (dans l'autre
    zone de l'extraction), ou « absent ». Seul « retrouve » compte dans le score.
    """
    zones = zones_extraction(e)
    lignes = []
    for x in cas["chiffres"]:
        attendue = NATURES[x["nature"]][0]
        autre = "resultats" if attendue == "effectif" else "effectif"
        if e is None:
            etat = "sans_extraction"
        elif present(x, zones[attendue]):
            etat = "retrouve"
        elif present(x, zones[autre]):
            etat = "ailleurs"
        else:
            etat = "absent"
        lignes.append({"id": x["id"], "nature": x["nature"], "libelle": x.get("libelle", ""),
                       "valeur": x["valeur"], "dans_l_article": x.get("dans_l_article"), "etat": etat})
    return lignes


def score(lignes):
    """Score sur les chiffres confirmés dans l'article ; les autres sont comptés à part (VS-D34)."""
    confirmes = [x for x in lignes if x["dans_l_article"] is True]
    retrouves = sum(1 for x in confirmes if x["etat"] == "retrouve")
    return {"chiffres": len(lignes), "confirmes_dans_l_article": len(confirmes),
            "ecartes_car_absents_de_l_article": sum(1 for x in lignes if x["dans_l_article"] is False),
            "non_verifies": sum(1 for x in lignes if x["dans_l_article"] is None),
            "retrouves": retrouves,
            "ailleurs_dans_l_extraction": sum(1 for x in confirmes if x["etat"] == "ailleurs"),
            "absents": sum(1 for x in confirmes if x["etat"] == "absent"),
            "part": round(retrouves / len(confirmes), 3) if confirmes else None}
