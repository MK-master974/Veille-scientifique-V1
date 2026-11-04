"""Règles fixes : étiquette de preuve de départ, verdicts autorisés, ordre d'affichage.

L'IA classe et rédige ; ces règles encadrent ce qu'elle a le droit de décider.
"""

TYPES = ("recommandation", "revue_systematique", "meta_analyse", "essai_randomise", "etude_diagnostique")
ETIQUETTES = ("preliminaire", "modere", "solide")          # du plus faible au plus fort
VERDICTS = ("change_la_pratique", "remet_en_question", "confirme", "a_surveiller")
GRADES = ("eleve", "modere", "faible", "tres_faible")

LIBELLES_TYPE = {
    "recommandation": "Recommandation",
    "revue_systematique": "Revue systématique",
    "meta_analyse": "Méta-analyse",
    "essai_randomise": "Essai randomisé",
    "etude_diagnostique": "Étude diagnostique",
}


def _entier(valeur):
    try:
        return int(str(valeur).replace(" ", "").replace(" ", ""))
    except (TypeError, ValueError):
        return None


def etiquette_depart(tri, cfg_preuve=None):
    """Étiquette de départ selon le type d'étude et les caractéristiques relevées au tri.

    Renvoie None si l'étude doit être écartée (effectif trop faible).
    """
    cfg_preuve = cfg_preuve or {}
    minimum = int(cfg_preuve.get("effectif_minimum", 30))
    seuil_modere = int(cfg_preuve.get("effectif_modere", 100))
    type_etude = tri.get("type_etude")
    grade = tri.get("grade")
    effectif = _entier(tri.get("effectif"))

    if type_etude == "recommandation":
        return "modere" if tri.get("accord_experts") else "solide"

    if type_etude in ("revue_systematique", "meta_analyse"):
        if grade in ("eleve", "modere"):
            return "solide"
        if grade == "faible":
            return "modere"
        if grade == "tres_faible":
            return "preliminaire"
        if tri.get("majorite_essais_randomises") is True:
            return "modere"
        return "preliminaire"

    if type_etude == "essai_randomise":
        if effectif is not None and effectif < minimum:
            return None
        if effectif is not None and effectif >= seuil_modere:
            return "modere"
        return "preliminaire"

    if type_etude == "etude_diagnostique":
        if effectif is not None and effectif < minimum:
            return None
        return "modere" if tri.get("design_diagnostique") == "prospective" else "preliminaire"

    return None


def plafonner_etiquette(proposee, depart):
    """L'IA peut abaisser l'étiquette, jamais la remonter."""
    if proposee not in ETIQUETTES:
        return depart
    return proposee if ETIQUETTES.index(proposee) <= ETIQUETTES.index(depart) else depart


def verdict_autorise(verdict, type_etude, etiquette):
    """« Change la pratique » est réservé aux recommandations et aux revues solides."""
    if verdict not in VERDICTS:
        return "a_surveiller"
    if verdict == "change_la_pratique":
        if type_etude == "recommandation":
            return verdict
        if type_etude in ("revue_systematique", "meta_analyse") and etiquette == "solide":
            return verdict
        return "a_surveiller"
    return verdict


def est_grande_nouveaute(fiche):
    return fiche.get("pertinence") == 3 and fiche.get("verdict") in ("change_la_pratique", "remet_en_question")


def cle_tri(fiche):
    """Ordre d'affichage : verdict, puis pertinence, puis solidité."""
    return (
        VERDICTS.index(fiche.get("verdict", "a_surveiller")),
        -int(fiche.get("pertinence") or 1),
        -ETIQUETTES.index(fiche.get("etiquette", "preliminaire")),
        fiche.get("id", ""),
    )


def priorite_selection(ref_tri):
    """Ordre de sélection quand le nombre de fiches dépasse le plafond."""
    ordre_type = {"recommandation": 0, "meta_analyse": 1, "revue_systematique": 1,
                  "essai_randomise": 2, "etude_diagnostique": 3}
    return (-int(ref_tri.get("pertinence") or 1), ordre_type.get(ref_tri.get("type_etude"), 9),
            ref_tri.get("id", ""))
