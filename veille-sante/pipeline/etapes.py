"""Préparation des requêtes d'IA et lecture de leurs réponses, étape par étape."""
from . import regles
from .controle import controler_fiche, nombres_du_texte, _formes, _NOMBRE
from .ia import lire_json

MAX_RESUME = 6000


def _entete_reference(ref):
    lignes = [
        f"IDENTIFIANT : {ref['id']}",
        f"TITRE : {ref['titre']}",
        f"REVUE : {ref.get('revue', '')} ({ref.get('annee', '')})",
        f"TYPES DE PUBLICATION : {', '.join(ref.get('types_publication', []))}",
    ]
    if ref.get("mesh"):
        lignes.append(f"MOTS-CLÉS MeSH : {', '.join(ref['mesh'][:25])}")
    lignes.append("RÉSUMÉ :")
    lignes.append(ref.get("resume", "")[:MAX_RESUME])
    return "\n".join(lignes)


# --- Tri ------------------------------------------------------------------------------------

def requetes_tri(references, consigne):
    return [{"id": f"tri:{r['id']}", "consigne": consigne, "contenu": _entete_reference(r),
             "max_sortie": 4000} for r in references]


def lire_tri(texte, ref, domaines_valides, cfg_preuve):
    """Renvoie un dict de tri normalisé (avec "inclure" et éventuellement "motif_exclusion")."""
    try:
        t = lire_json(texte)
    except Exception as e:
        return {"id": ref["id"], "inclure": False, "motif_exclusion": f"réponse de tri illisible ({e})"}
    res = {"id": ref["id"], "inclure": bool(t.get("inclure"))}
    if not res["inclure"]:
        res["motif_exclusion"] = (t.get("motif_exclusion") or "non pertinent")[:300]
        return res
    type_etude = t.get("type_etude")
    if type_etude not in regles.TYPES:
        return {**res, "inclure": False, "motif_exclusion": f"type d'étude non retenu ({type_etude})"}
    try:
        pertinence = min(3, max(1, int(t.get("pertinence"))))
    except (TypeError, ValueError):
        pertinence = 1
    domaines = []
    for d in t.get("domaines") or []:
        d = str(d).strip()
        if d in domaines_valides and not d.startswith("transversal/") and d not in domaines:
            domaines.append(d)
    if not domaines:
        return {**res, "inclure": False, "motif_exclusion": "aucun domaine du catalogue"}
    tri = {
        **res,
        "type_etude": type_etude,
        "pertinence": pertinence,
        "domaines": domaines[:4],
        "effectif": t.get("effectif"),
        "grade": t.get("grade") if t.get("grade") in regles.GRADES else None,
        "majorite_essais_randomises": t.get("majorite_essais_randomises"),
        "accord_experts": t.get("accord_experts"),
        "design_diagnostique": t.get("design_diagnostique"),
        "incertitude": t.get("incertitude"),
    }
    depart = regles.etiquette_depart(tri, cfg_preuve)
    if depart is None:
        return {"id": ref["id"], "inclure": False,
                "motif_exclusion": "effectif inférieur au minimum ou type non évaluable"}
    tri["etiquette_depart"] = depart
    return tri


def selectionner(tris, maximum):
    retenus = sorted((t for t in tris.values() if t.get("inclure")), key=regles.priorite_selection)
    return retenus[:maximum], retenus[maximum:]


# --- Rédaction ------------------------------------------------------------------------------

def requetes_redaction(selection, refs_par_id, libelles, consigne):
    reqs = []
    for tri in selection:
        ref = refs_par_id[tri["id"]]
        infos = [
            _entete_reference(ref),
            "",
            "CLASSEMENT (issu du tri) :",
            f"- type d'étude : {regles.LIBELLES_TYPE[tri['type_etude']]}",
            f"- pertinence : {tri['pertinence']}",
            f"- domaines : {', '.join(libelles.get(d, d) for d in tri['domaines'])}",
            f"- étiquette de départ : {tri['etiquette_depart']}",
        ]
        if tri.get("effectif") is not None:
            infos.append(f"- effectif relevé : {tri['effectif']}")
        if tri.get("grade"):
            infos.append(f"- GRADE relevé : {tri['grade']}")
        sortie = 10000 if tri["pertinence"] == 3 else 8000
        reqs.append({"id": f"redaction:{tri['id']}", "consigne": consigne,
                     "contenu": "\n".join(infos), "max_sortie": sortie})
    return reqs


def lire_redaction(texte, ref, tri, cfg_preuve):
    try:
        brut = lire_json(texte)
    except Exception as e:
        return None, [f"réponse de rédaction illisible ({e})"]
    return controler_fiche(brut, ref, tri, cfg_preuve)


# --- Synthèses ------------------------------------------------------------------------------

def fiches_par_domaine(fiches):
    groupes = {}
    for f in fiches:
        for d in f["domaines"]:
            groupes.setdefault(d, []).append(f)
    for d in groupes:
        groupes[d].sort(key=regles.cle_tri)
    return groupes


def requetes_synthese(groupes, libelles, consigne, max_fiches=40):
    reqs = []
    for domaine, fiches in groupes.items():
        lignes = [f"SOUS-CHAMP : {libelles.get(domaine, domaine)}", f"NOMBRE DE FICHES : {len(fiches)}", ""]
        for f in fiches[:max_fiches]:
            lignes.append(f"- id={f['id']} | verdict={f['verdict']} | étiquette={f['etiquette']} | "
                          f"{f['titre_fr']} | {f['flash']}")
        reqs.append({"id": f"synthese:{domaine}", "consigne": consigne,
                     "contenu": "\n".join(lignes), "max_sortie": 6000})
    return reqs


def synthese_simple(fiches):
    """Synthèse déterministe, sans IA, à partir des résumés flash."""
    item = lambda f: {"id": f["id"], "phrase": f["flash"]}
    change = [f for f in fiches if f["verdict"] == "change_la_pratique"]
    remet = [f for f in fiches if f["verdict"] == "remet_en_question"]
    autres = [f for f in fiches if f["verdict"] in ("confirme", "a_surveiller")]
    return {
        "ce_qui_change_la_pratique": [item(f) for f in change[:5]],
        "a_surveiller": [item(f) for f in autres[:5]],
        "remis_en_question": [item(f) for f in remet[:5]],
    }


def lire_synthese(texte, fiches):
    """Valide la synthèse de l'IA ; complète avec la synthèse simple si un bloc est invalide."""
    simple = synthese_simple(fiches)
    par_id = {f["id"]: f for f in fiches}
    try:
        brut = lire_json(texte)
    except Exception:
        return simple, True
    verdicts_permis = {
        "ce_qui_change_la_pratique": {"change_la_pratique"},
        "a_surveiller": {"a_surveiller", "confirme", "change_la_pratique", "remet_en_question"},
        "remis_en_question": {"remet_en_question"},
    }
    resultat, repli = {}, False
    for bloc, permis in verdicts_permis.items():
        items = []
        for it in (brut.get(bloc) or [])[:5]:
            f = par_id.get(str(it.get("id", "")))
            phrase = str(it.get("phrase", "")).strip()
            if not f or f["verdict"] not in permis or not phrase or len(phrase.split()) > 45:
                continue
            autorises = nombres_du_texte(" ".join([f["titre_fr"], f["flash"], f["standard"]["resultats"]]))
            if any(not (_formes(m.group(0), False) & autorises) for m in _NOMBRE.finditer(phrase)):
                continue
            if f["id"] not in {x["id"] for x in items}:
                items.append({"id": f["id"], "phrase": phrase})
        if not items and simple[bloc]:
            items, repli = simple[bloc], True
        resultat[bloc] = items
    return resultat, repli
