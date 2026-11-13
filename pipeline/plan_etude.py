"""Plan réel d'une publication, établi avant le choix de la grille d'appréciation.

Phase 1, séance 7 (VS-D44). Ce module n'est pas appelé par la veille hebdomadaire ; il est mesuré
par banc/banc_appreciation.py.

Le type d'étude donné par le tri vient du titre, du résumé et des types PubMed. Il peut être faux :
un essai « randomisé » dont l'affectation suit l'alternance ou la disponibilité d'un chirurgien est
quasi randomisé, et la grille des essais randomisés ne lui convient pas. Ici, l'IA lit la méthode,
choisit un plan dans une liste fermée et cite le passage qui le montre. Le code décide :
- le passage doit se retrouver mot pour mot dans le texte lu, sinon le plan reste « non déterminé » ;
- la grille se déduit du plan par une table, jamais de l'IA ;
- quand aucune grille ne convient, ou quand la grille qui conviendrait n'est pas encore écrite, la
  réponse est « aucune grille applicable » : aucune note n'est forcée.
"""
from . import texte
from .extraction import _absents, _nombres, _repere, _texte
from .ia import lire_json

NON_DETERMINE = "non_determine"
PLANS = ("essai_randomise", "essai_quasi_randomise", "interventionnel_non_randomise", "observationnel",
         "etude_diagnostique", "modele_de_prediction", "revue_interventions", "revue_descriptive",
         "recommandation", "autre")
LIBELLES = {
    "essai_randomise": "essai randomisé",
    "essai_quasi_randomise": "essai quasi randomisé",
    "interventionnel_non_randomise": "étude interventionnelle non randomisée",
    "observationnel": "étude observationnelle",
    "etude_diagnostique": "étude diagnostique",
    "modele_de_prediction": "développement ou validation d'un modèle de prédiction",
    "revue_interventions": "revue d'interventions",
    "revue_descriptive": "revue descriptive ou qualitative",
    "recommandation": "recommandation",
    "autre": "autre plan"}
DEFINITIONS = {
    "essai_randomise": "les participants sont affectés aux groupes par un procédé aléatoire décrit (séquence générée, tirage au sort, randomisation par blocs, enveloppes)",
    "essai_quasi_randomise": "l'affectation suit une règle non aléatoire : alternance, ordre d'arrivée, date, numéro de dossier, disponibilité, planning, choix d'un soignant ; l'article peut se dire « randomisé » à tort",
    "interventionnel_non_randomise": "une intervention est assignée par les chercheurs ou les soignants sans aléa, avec ou sans groupe de comparaison, y compris un avant-après",
    "observationnel": "cohorte, cas-témoins, étude transversale, série ou rapport de cas, enquête, étude qualitative : aucune intervention assignée par les chercheurs",
    "etude_diagnostique": "mesure la capacité d'un test, d'un signe, d'un score, d'un algorithme ou d'un examen DÉJÀ DÉFINI à repérer une maladie ou un état, en le comparant à une référence, chez des participants qui ont ou n'ont pas cette maladie ; évaluer un outil existant, même commercial ou fondé sur l'intelligence artificielle, ou un score à critères fixés à l'avance, relève de ce plan",
    "modele_de_prediction": "construit, ajuste ou entraîne un modèle, un algorithme ou un score À PARTIR DES DONNÉES DE L'ÉTUDE (régression, apprentissage automatique, pondération ou seuils choisis sur les données) pour prédire ou diagnostiquer, avec ou sans validation ; un modèle ou un score déjà défini avant l'étude, que l'étude se borne à évaluer contre une référence, n'est pas dans ce plan ; CAS MIXTE : si l'étude évalue aussi, contre une référence, un outil, un score ou des seuils déjà définis, choisis « etude_diagnostique », la grille QUADAS-2 s'appliquant à cette évaluation",
    "revue_interventions": "revue systématique ou méta-analyse qui compare des interventions, des traitements ou des programmes entre eux ou à un témoin, à partir d'essais ou d'études comparatives",
    "revue_descriptive": "revue systématique ou non, qui décrit (fréquence, diagnostic, imagerie, mécanismes, expériences vécues, séries et rapports de cas) ou qui rapproche des groupes, des lieux ou des expositions (urbain et rural, par exemple) sans comparer d'interventions",
    "recommandation": "recommandation de pratique, consensus d'experts, ligne directrice",
    "autre": "aucun des plans ci-dessus, ou le texte ne permet pas de trancher ; aussi une preuve de concept technique sans aucun participant atteint de la maladie ou de l'état recherché (volontaires sains, simulation, laboratoire)"}

# Plan → (outil d'appréciation, grille qui conviendrait mais qui n'est pas encore écrite).
GRILLE_DU_PLAN = {
    "essai_randomise": ("rob2", None),
    "essai_quasi_randomise": (None, "robins_i"),
    "interventionnel_non_randomise": (None, "robins_i"),
    "observationnel": (None, "jbi"),
    "etude_diagnostique": ("quadas2", None),
    "modele_de_prediction": (None, "probast"),
    "revue_interventions": ("amstar2", None),
    "revue_descriptive": (None, "robis"),
    "recommandation": ("agree2", None),
    "autre": (None, None)}
# Plans compatibles avec le type donné par le tri (types du moteur actuel, pipeline/regles.py).
COMPATIBLE_AVEC_LE_TRI = {"essai_randomise": {"essai_randomise"}, "etude_diagnostique": {"etude_diagnostique"},
                          "revue_systematique": {"revue_interventions"}, "meta_analyse": {"revue_interventions"},
                          "recommandation": {"recommandation"}}
LIBELLES_TRI = {"essai_randomise": "essai randomisé", "etude_diagnostique": "étude diagnostique",
                "revue_systematique": "revue systématique", "meta_analyse": "méta-analyse",
                "recommandation": "recommandation"}
SORTIE = 1500
MAX_JUSTIFICATION = 300


def requete_plan(ref, doc, consigne, type_tri=None, etape="plan"):
    """Requête « plan d'étude » : le résumé et les parties de méthode du texte lu."""
    lignes = [f"IDENTIFIANT : {ref['id']}",
              "PLANS PERMIS (clé : définition)"]
    lignes += [f"- {plan} : {DEFINITIONS[plan]}" for plan in PLANS]
    if type_tri in LIBELLES_TRI:
        lignes.append(f"TYPE ANNONCÉ PAR LE TRI : {LIBELLES_TRI[type_tri]} (à vérifier dans la méthode, pas à reprendre)")
    lignes += ["", texte.texte_pour_ia(texte.extrait_pour_plan(doc))]
    return {"id": f"{etape}:{ref['id']}", "consigne": consigne, "contenu": "\n".join(lignes), "max_sortie": SORTIE}


def lire_plan(reponse, doc, type_tri=None, publier_passage=False):
    """Contrôle la réponse de l'IA. Renvoie (plan | None, bilan).

    « plan » : plan (« non_determine » si le passage n'est pas vérifié), source, type_tri,
    ecart_avec_le_tri, justification, incertitude. publier_passage : vrai seulement sous licence
    CC BY ou CC0 (VS-D15).
    """
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
    plan, source = brut.get("plan"), None
    if plan not in PLANS:
        if plan is not None:
            bilan["ecarts"].append(f"plan invalide ({plan!r}), ramené à « non déterminé »")
        plan = NON_DETERMINE
    else:
        bloc, extrait = texte.trouver_passage(doc, brut.get("passage"), _repere(brut.get("repere")))
        if bloc is None:
            bilan["ecarts"].append(f"plan {plan} sans passage vérifiable ({extrait}), ramené à « non déterminé »")
            plan = NON_DETERMINE
        else:
            source = {"emplacement": bloc["emplacement"], "passage": extrait if publier_passage else None}
    ecart = None
    if plan != NON_DETERMINE and type_tri in COMPATIBLE_AVEC_LE_TRI:
        ecart = plan not in COMPATIBLE_AVEC_LE_TRI[type_tri]
    justification = _texte(brut.get("justification"))
    if justification and _absents(justification, _nombres(texte.texte_lu(doc))):
        bilan["ecarts"].append("justification écartée : chiffre absent du texte lu")
        justification = None
    incertitude = _texte(brut.get("incertitude"))
    return {"plan": plan, "source": source, "type_tri": type_tri, "ecart_avec_le_tri": ecart,
            "justification": justification[:MAX_JUSTIFICATION] if justification else None,
            "incertitude": incertitude[:MAX_JUSTIFICATION] if incertitude else None}, bilan


def choisir_grille(plan):
    """(outil, grille_manquante, motif) pour un plan. Sans outil, le motif dit pourquoi."""
    outil, manquante = GRILLE_DU_PLAN.get(plan, (None, None))
    if outil:
        return outil, None, None
    if plan == NON_DETERMINE:
        return None, None, "plan d'étude non établi"
    if manquante:
        return None, manquante, f"aucune grille écrite pour ce plan ({LIBELLES[plan]}) : {manquante} serait la grille adaptée"
    return None, None, f"aucune grille applicable à ce plan ({LIBELLES[plan]})"
