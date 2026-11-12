"""Extraction structurée des données d'une publication, chaque donnée avec son emplacement.

Phase 1, séance 5 : bloc « extraction » d'une fiche v2 (docs/FICHE_V2.md). Ce module n'est pas
appelé par la veille hebdomadaire ; il est mesuré par banc/banc_extraction.py.

L'IA propose des données, chacune avec le repère d'un bloc et un passage. Le code décide :
- le passage doit se retrouver mot pour mot dans le texte lu ; l'emplacement publié est celui où
  il se trouve réellement, et l'extrait publié est recopié du texte lu, pas de la proposition ;
- les nombres d'une donnée doivent figurer dans son passage, ou au moins dans le bloc cité ;
- les valeurs fermées (rang, sens de la mesure, en faveur de) sont ramenées à la valeur la plus
  prudente quand elles sont invalides ou incohérentes entre elles ; une évolution avant-après
  dans un seul groupe n'est jamais notée « en faveur de » l'intervention ; un sens que le passage
  cité ne permet pas de lire est ramené à « non rapporté ».
Une donnée qui ne passe pas ces contrôles est refusée et comptée : elle n'est ni corrigée ni
publiée. Le passage n'est publié que si la licence du texte lu le permet (VS-D15).
"""
import hashlib
import re

from . import texte
from .controle import _NOMBRE, _formes, _nombres_en_lettres, _petits_entiers_en_lettres, nombres_du_texte
from .ia import lire_json

CHAMPS_SIMPLES = ("question", "population", "effectif", "intervention", "comparateur")
RANGS = ("principal", "secondaire", "non_precise")
SENS = ("augmente", "diminue", "pas_de_difference", "non_rapporte")
FAVEUR = ("intervention", "comparateur", "aucun", "indetermine")
MAX_RESULTATS = 40

# Plafonds de réponse : larges, car un modèle qui « réfléchit » consomme des jetons avant d'écrire.
SORTIE_RESUME = 6000
SORTIE_INTEGRAL = 20000

LIBELLES_TYPE = {"recommandation": "recommandation", "revue_systematique": "revue systématique",
                 "meta_analyse": "méta-analyse", "essai_randomise": "essai randomisé",
                 "etude_diagnostique": "étude diagnostique"}


def version_consigne(consigne):
    """Empreinte courte d'une consigne, pour savoir avec laquelle une extraction a été produite."""
    return hashlib.sha256(consigne.encode("utf-8")).hexdigest()[:8]


# --- Requête ----------------------------------------------------------------------------------

def requete_extraction(ref, doc, consigne, type_etude=None, etape="extraction"):
    integral = any(b["type"] == "section" for b in doc["blocs"])
    lignes = [f"IDENTIFIANT : {ref['id']}"]
    if type_etude in LIBELLES_TYPE:
        lignes.append(f"TYPE D'ÉTUDE (issu du tri) : {LIBELLES_TYPE[type_etude]}")
    lignes.append("TEXTE FOURNI : " + ("texte intégral" if integral else
                                       "titre et résumé uniquement ; le reste de l'article n'est pas fourni"))
    lignes += ["", texte.texte_pour_ia(doc)]
    return {"id": f"{etape}:{ref['id']}", "consigne": consigne, "contenu": "\n".join(lignes),
            "max_sortie": SORTIE_INTEGRAL if integral else SORTIE_RESUME}


# --- Contrôle des nombres ---------------------------------------------------------------------

def _nombres(source):
    """Tous les nombres qu'un texte source permet d'écrire, sous leurs lectures possibles."""
    return (nombres_du_texte(source, source_anglaise=True) | nombres_du_texte(source, source_anglaise=False)
            | _petits_entiers_en_lettres(source) | _nombres_en_lettres(source))


def _absents(champ, autorises):
    return [m.group(0) for m in _NOMBRE.finditer(champ or "") if not (_formes(m.group(0), False) & autorises)]


def _texte(v):
    """Une valeur proposée par l'IA, ramenée à un texte propre ou à None."""
    if v is None or isinstance(v, (dict, list, bool)):
        return None
    v = re.sub(r"\s+", " ", str(v)).strip()
    return v if v and v.lower() not in ("null", "none", "non rapporté", "non rapporte") else None


def _repere(v):
    """« [S3] », « s3 »… → « S3 » : le repère tel que le document le porte."""
    v = _texte(v)
    return re.sub(r"[\[\]\s]", "", v).upper() or None if v else None


def _localiser(brut, doc, chiffres, autorises_doc, publier_passages):
    """Vérifie le passage et les nombres d'une donnée.

    Renvoie (source, motif de refus, écarts, extrait). L'extrait est le passage vérifié, recopié du
    texte lu ; il sert aux contrôles même quand la licence ne permet pas de le publier.
    """
    repere = _repere(brut.get("repere"))
    bloc, extrait = texte.trouver_passage(doc, brut.get("passage"), repere)
    if bloc is None:
        return None, extrait, [], None
    ecarts = []
    if repere not in (None, bloc["repere"]):
        ecarts.append("emplacement corrigé : le passage se trouve dans un autre bloc que celui annoncé")
    dans_passage, dans_bloc = _nombres(extrait), None
    for champ in chiffres:
        for nombre in _absents(champ, dans_passage):
            dans_bloc = dans_bloc if dans_bloc is not None else _nombres(bloc["texte"])
            if _formes(nombre, False) & dans_bloc:
                ecarts.append(f"chiffre hors du passage, présent dans le bloc cité : {nombre}")
            elif _formes(nombre, False) & autorises_doc:
                return None, f"chiffre absent du bloc cité : {nombre}", [], None
            else:
                return None, f"chiffre absent du texte lu : {nombre}", [], None
    source = {"emplacement": bloc["emplacement"], "passage": extrait if publier_passages else None}
    return source, None, ecarts, extrait


# --- Cohérence d'un résultat ------------------------------------------------------------------

# Un sens (« augmente », « diminue ») doit pouvoir se lire dans le passage cité : un mot de direction,
# ou au moins deux nombres à comparer (ligne de tableau, valeur de chaque groupe). Les valeurs de p ne
# comptent pas. Rejouée sur les journaux des trois lancements du banc du 12/11/2026, cette règle repère
# les sept sens annoncés sans appui (« there were statistically significant differences in… ») parmi
# 451 résultats, sans fausse alerte.
_DIRECTION = re.compile(
    r"higher|\blower|greater|\bless\b|fewer|\bmore\b|increas|decreas|reduc|improv|declin|\brose\b|\bfell\b|drop|\bgain|"
    r"loss\b|lost\b|superior|inferior|better|worse|faster|slower|longer|shorter|larger|smaller|weaker|stronger|"
    r"elevat|enhanc|diminish|outperform|exceed|favou?r|benefi|above|below|attenuat|prolong|shorten|delay|accelerat|"
    r"\bplus\b|\bmoins\b|augment|diminu|baiss|hausse|amélior|supérieur|inférieur|réduit|réduc|meilleur|\bpire\b", re.I)
_VALEUR_P = re.compile(r"\bp\s*(?:-?\s*value)?\s*[<>=≤≥]\s*[\d.,]+", re.I)
_UN_NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")


def sens_etaye(passage):
    """Vrai si le passage permet de lire dans quel sens va une différence."""
    if _DIRECTION.search(passage or ""):
        return True
    return len(_UN_NOMBRE.findall(_VALEUR_P.sub(" ", passage or ""))) >= 2


# La consigne demande d'écrire « (groupe A, après contre avant) » pour une évolution dans un seul groupe.
_AVANT_APRES = re.compile(r"apr[eè]s contre avant|avant[- ]apr[eè]s|post contre pr[eé]", re.I)

# Un signe « moins » s'écrit de plusieurs façons dans les articles : tiret, signe moins, trait d'union
# typographique (« ‐0.011 »).
_MOINS = "-−–‐‑‒"
_SIGNE = re.compile(rf"[{_MOINS}]?\s?\d+(?:[.,]\d+)?")


def _valeurs_signees(champ):
    valeurs = []
    for m in _SIGNE.finditer(champ or ""):
        brut = re.sub(rf"[{_MOINS}]", "-", m.group(0).replace(" ", "")).replace(",", ".")
        try:
            valeurs.append(float(brut))
        except ValueError:
            pass
    return valeurs


def alertes_coherence(resultat):
    """Signaux à examiner, qui ne font pas refuser le résultat."""
    alertes = []
    estimation = _valeurs_signees(resultat.get("valeur"))
    bornes = [b for b in _valeurs_signees(resultat.get("intervalle"))]
    if len(bornes) == 3 and bornes[0] in (90.0, 95.0, 99.0):          # « IC à 95 % : 1,6 à 7,2 »
        bornes = bornes[1:]
    if len(bornes) == 2 and bornes[1] < bornes[0] and bornes[1] < 0 <= bornes[0]:
        bornes[1] = -bornes[1]                                         # « 1,6–7,2 » : un tiret, pas un signe
    if len(estimation) == 1 and len(bornes) == 2 and bornes[0] <= bornes[1] \
            and not bornes[0] <= estimation[0] <= bornes[1]:
        alertes.append("estimation hors de son intervalle")
    p = resultat.get("p") or ""
    valeurs_p = [abs(v) for v in _valeurs_signees(p)]
    if len(valeurs_p) == 1 and valeurs_p[0] <= 1:
        v, sens = valeurs_p[0], resultat.get("sens_mesure")
        non_significatif = (">" in p and v >= 0.05) or ("<" not in p and ">" not in p and v > 0.05)
        significatif = ">" not in p and v < 0.05 or ("<" in p and v == 0.05)
        if sens in ("augmente", "diminue") and non_significatif:
            alertes.append("différence annoncée, mais p non significatif")
        if sens == "pas_de_difference" and significatif:
            alertes.append("pas de différence annoncée, mais p significatif")
    return alertes


# --- Lecture de la réponse --------------------------------------------------------------------

def lire_extraction(reponse, doc, publier_passages=False):
    """Contrôle la réponse de l'IA. Renvoie (extraction | None, bilan).

    « extraction » suit le bloc du même nom de docs/FICHE_V2.md. « bilan » compte ce qui a été
    proposé, gardé et refusé, avec les motifs : c'est lui que le banc d'essai mesure.
    publier_passages : vrai seulement quand la licence du texte lu est CC BY ou CC0 (VS-D15).
    """
    bilan = {"lisible": False, "proposees": 0, "gardees": 0, "refus": [], "ecarts": [], "alertes": [],
             "alerte_ia": None}
    try:
        brut = lire_json(reponse)
    except Exception as e:
        bilan["refus"].append({"champ": "réponse", "motif": f"réponse illisible ({e})"})
        return None, bilan
    if not isinstance(brut, dict):
        bilan["refus"].append({"champ": "réponse", "motif": "réponse illisible (pas un objet)"})
        return None, bilan
    bilan["lisible"] = True
    bilan["alerte_ia"] = _texte(brut.get("alerte"))
    autorises_doc = _nombres(texte.texte_lu(doc))

    def refuser(champ, motif):
        bilan["refus"].append({"champ": champ, "motif": motif})

    def noter(champ, ecarts, cle="ecarts"):
        bilan[cle] += [{"champ": champ, "nature": e} for e in ecarts]

    extraction = {}
    for champ in CHAMPS_SIMPLES:
        donnee = brut.get(champ)
        valeur = _texte(donnee.get("valeur")) if isinstance(donnee, dict) else None
        extraction[champ] = None
        if valeur is None:
            continue
        bilan["proposees"] += 1
        source, motif, ecarts, _ = _localiser(donnee, doc, [valeur], autorises_doc, publier_passages)
        if source is None:
            refuser(champ, motif)
            continue
        noter(champ, ecarts)
        extraction[champ] = {"valeur": valeur, "source": source}
        bilan["gardees"] += 1

    extraction["resultats"] = []
    proposes = brut.get("resultats") if isinstance(brut.get("resultats"), list) else []
    if len(proposes) > MAX_RESULTATS:
        noter("resultats", [f"{len(proposes) - MAX_RESULTATS} résultats au-delà du maximum, non lus"])
    for n, r in enumerate(proposes[:MAX_RESULTATS], 1):
        champ = f"resultats[{n}]"
        if not isinstance(r, dict) or _texte(r.get("critere")) is None:
            continue
        bilan["proposees"] += 1
        resultat = {"critere": _texte(r.get("critere")),
                    "rang": r.get("rang"), "sens_mesure": r.get("sens_mesure"),
                    "en_faveur_de": r.get("en_faveur_de"),
                    "valeur": _texte(r.get("valeur")), "intervalle": _texte(r.get("intervalle")),
                    "p": _texte(r.get("p"))}
        absents = _absents(resultat["critere"], autorises_doc)
        if absents:
            refuser(champ, f"chiffre absent du texte lu : {absents[0]}")
            continue
        chiffres = [resultat["valeur"], resultat["intervalle"], resultat["p"]]
        source, motif, ecarts, extrait = _localiser(r, doc, chiffres, autorises_doc, publier_passages)
        if source is None:
            refuser(champ, motif)
            continue
        for cle, permis, prudent in (("rang", RANGS, "non_precise"), ("sens_mesure", SENS, "non_rapporte"),
                                     ("en_faveur_de", FAVEUR, "indetermine")):
            if resultat[cle] not in permis:
                ecarts.append(f"{cle} invalide, ramené à « {prudent} »")
                resultat[cle] = prudent
        if resultat["sens_mesure"] in ("augmente", "diminue") and not sens_etaye(extrait):
            ecarts.append("sens non étayé par le passage cité : ramené à « non_rapporte »")
            resultat["sens_mesure"] = "non_rapporte"
            if resultat["en_faveur_de"] in ("intervention", "comparateur"):
                resultat["en_faveur_de"] = "indetermine"
        if _AVANT_APRES.search(resultat["critere"]) and resultat["en_faveur_de"] in ("intervention", "comparateur"):
            ecarts.append("évolution avant-après : « en faveur de » ramené à « indetermine »")
            resultat["en_faveur_de"] = "indetermine"
        if resultat["sens_mesure"] == "pas_de_difference" and resultat["en_faveur_de"] != "aucun":
            ecarts.append("pas de différence : « en faveur de » ramené à « aucun »")
            resultat["en_faveur_de"] = "aucun"
        elif resultat["sens_mesure"] in ("augmente", "diminue") and resultat["en_faveur_de"] == "aucun":
            ecarts.append("différence annoncée : « en faveur de » ramené à « indetermine »")
            resultat["en_faveur_de"] = "indetermine"
        noter(champ, ecarts)
        noter(champ, alertes_coherence(resultat), "alertes")
        resultat["source"] = source
        extraction["resultats"].append(resultat)
        bilan["gardees"] += 1

    ei = brut.get("evenements_indesirables")
    extraction["evenements_indesirables"] = {"rapportes": False, "valeur": None, "source": None}
    if isinstance(ei, dict) and ei.get("rapportes") is True:
        bilan["proposees"] += 1
        valeur = _texte(ei.get("valeur"))
        source, motif, ecarts, _ = (None, "valeur absente", [], None) if valeur is None else \
            _localiser(ei, doc, [valeur], autorises_doc, publier_passages)
        if source is None:
            # L'IA dit qu'ils sont rapportés, sans passage vérifiable : on ne tranche pas.
            refuser("evenements_indesirables", motif)
            extraction["evenements_indesirables"]["rapportes"] = None
        else:
            noter("evenements_indesirables", ecarts)
            extraction["evenements_indesirables"] = {"rapportes": True, "valeur": valeur, "source": source}
            bilan["gardees"] += 1
    return extraction, bilan


def reduire_au_reperage(extraction):
    """Extraction d'une fiche de repérage : le résultat principal, et les événements s'ils sont rapportés."""
    principaux = [r for r in extraction["resultats"] if r["rang"] == "principal"] or extraction["resultats"][:1]
    reduit = {**extraction, "resultats": principaux}
    if extraction["evenements_indesirables"].get("rapportes") is not True:
        reduit.pop("evenements_indesirables")
    return reduit
