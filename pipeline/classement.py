"""Catégorie d'importance d'une publication, de 1 à 4, justifiée (VS-D13).

Phase 1, séance 6 : champs « categorie », « justification_categorie », « mise_en_avant » et
« sens_pratique » du bloc « classement » d'une fiche v2 (docs/FICHE_V2.md). Ce module n'est pas
appelé par la veille hebdomadaire ; il est mesuré par banc/banc_appreciation.py.

L'IA propose, à partir du titre et du résumé. Le code borne :
- une catégorie invalide ou sans justification est ramenée à 3, la valeur prudente ;
- une catégorie 1 sans « mise_en_avant » complète est ramenée à 2 ;
- un chiffre de la justification qui ne figure ni dans le titre ni dans le résumé est signalé.
"""
from .extraction import _absents, _nombres, _texte
from .ia import lire_json

LIBELLES = {1: "évolution potentielle des pratiques", 2: "apport scientifique important",
            3: "actualisation des connaissances", 4: "veille complémentaire"}
PRUDENTE = 3
SENS = ("confirme", "remet_en_question")
MISE_EN_AVANT = ("nouveaute", "remise_en_question", "peut_modifier_les_pratiques", "certitude",
                 "confirmations_necessaires")
LIBELLES_TYPE = {"recommandation": "recommandation", "revue_systematique": "revue systématique",
                 "meta_analyse": "méta-analyse", "essai_randomise": "essai randomisé",
                 "etude_diagnostique": "étude diagnostique"}
SORTIE = 3000


def requete_classement(ref, consigne, type_etude=None, etape="classement"):
    lignes = [f"IDENTIFIANT : {ref['id']}", f"TITRE : {ref.get('titre', '')}", f"REVUE : {ref.get('revue', '')}"]
    if type_etude in LIBELLES_TYPE:
        lignes.append(f"TYPE D'ÉTUDE (issu du tri) : {LIBELLES_TYPE[type_etude]}")
    lignes += ["RÉSUMÉ :", str(ref.get("resume") or "").replace("<<<", "‹‹‹").replace(">>>", "›››")]
    return {"id": f"{etape}:{ref['id']}", "consigne": consigne, "contenu": "\n".join(lignes), "max_sortie": SORTIE}


def lire_classement(reponse, ref):
    """Contrôle la réponse de l'IA. Renvoie (classement | None, bilan)."""
    bilan = {"lisible": False, "ecarts": [], "alerte_ia": None}
    try:
        brut = lire_json(reponse)
    except Exception as e:
        bilan["ecarts"].append(f"réponse illisible ({e})")
        return None, bilan
    if not isinstance(brut, dict):
        bilan["ecarts"].append("réponse illisible (pas un objet)")
        return None, bilan
    bilan["lisible"] = True
    bilan["alerte_ia"] = _texte(brut.get("alerte"))
    categorie = brut.get("categorie")
    justification = _texte(brut.get("justification_categorie"))
    if isinstance(categorie, bool) or categorie not in LIBELLES:
        bilan["ecarts"].append(f"catégorie invalide, ramenée à {PRUDENTE}")
        categorie = PRUDENTE
    if not justification or len(justification) < 20:
        if categorie != PRUDENTE:
            bilan["ecarts"].append(f"catégorie sans justification, ramenée à {PRUDENTE}")
        categorie, justification = PRUDENTE, justification or None
    mise = brut.get("mise_en_avant") if isinstance(brut.get("mise_en_avant"), dict) else None
    mise = {c: _texte(mise.get(c)) for c in MISE_EN_AVANT} if mise else None
    if categorie == 1 and not (mise and all(mise.values())):
        bilan["ecarts"].append("catégorie 1 sans mise en avant complète, ramenée à 2")
        categorie = 2
    if categorie != 1:
        mise = None
    sens = brut.get("sens_pratique") if brut.get("sens_pratique") in SENS else None
    source = _nombres(f"{ref.get('titre', '')}\n{ref.get('resume', '')}")
    redige = " ".join([justification or ""] + list((mise or {}).values()))
    absents = _absents(redige, source)
    if absents:
        bilan["ecarts"].append(f"chiffre absent du titre et du résumé : {absents[0]}")
    return {"categorie": categorie, "libelle": LIBELLES[categorie], "justification_categorie": justification,
            "mise_en_avant": mise, "sens_pratique": sens}, bilan
