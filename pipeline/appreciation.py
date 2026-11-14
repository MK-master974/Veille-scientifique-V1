"""Appréciation méthodologique d'une publication, par l'outil adapté à son type d'étude.

Phase 1, séance 6 : bloc « appreciation » d'une fiche v2 (docs/FICHE_V2.md). Ce module n'est pas
appelé par la veille hebdomadaire ; il est mesuré par banc/banc_appreciation.py.

L'IA juge chaque domaine de l'outil et cite le passage qui fonde son jugement. Le code décide :
- un jugement favorable (« faible risque », « oui ») n'est gardé que si son passage se retrouve mot
  pour mot dans le texte lu ; sinon le domaine devient « non évaluable » ;
- quand seul le résumé est lu, une absence ne prouve rien : un jugement défavorable ou incertain
  sans passage vérifié devient lui aussi « non évaluable » ;
- le jugement global n'est jamais celui de l'IA : le code le calcule à partir des domaines, selon
  la règle de chaque outil ;
- la certitude GRADE n'est reprise que si le passage cité la nomme ;
- séance 7 (VS-D44) : pour AMSTAR 2, « non » exige un passage qui montre que le critère n'est pas
  rempli ; un texte silencieux donne « non rapporté ». Le code calcule une fourchette du jugement
  global (le pire et le meilleur possibles) au lieu d'un « non évaluable » sec ; quand aucune grille
  ne convient, la réponse est « aucune grille applicable ».
- ROBINS-I (VS-D54), pour un essai quasi randomisé ou une étude interventionnelle non randomisée :
  tout jugement exige son passage. « Sérieux » ou « critique » sans passage devient « non rapporté »
  (la case « pas d'information » de l'outil), comme « non » pour AMSTAR 2 ; « faible » ou « modéré »
  sans passage est refusé. La grille a sa propre consigne, appreciation_robins_i.txt.
« Non évaluable » veut dire : ce qui a été lu ne permet pas de juger. Ce n'est pas une preuve faible.
"""
import re

from . import texte
from .extraction import _absents, _nombres, _repere, _texte
from .ia import lire_json

NON_EVALUABLE = "non_evaluable"
NON_RAPPORTE = "non_rapporte"            # AMSTAR 2, ROBINS-I : le texte intégral ne dit rien sur le critère
INCONNUS = (NON_EVALUABLE, NON_RAPPORTE)
AUCUN = "aucun"                          # aucune grille applicable

# Outil selon le type d'étude (types du moteur actuel, pipeline/regles.py).
OUTILS = {"essai_randomise": "rob2", "etude_diagnostique": "quadas2", "revue_systematique": "amstar2",
          "meta_analyse": "amstar2", "recommandation": "agree2"}

# Domaines de chaque outil : clé, puis ce que l'IA doit juger.
DOMAINES = {
    "rob2": [
        ("randomisation", "Processus de randomisation : séquence aléatoire, affectation masquée, groupes comparables au départ"),
        ("ecarts_aux_interventions", "Écarts par rapport aux interventions prévues : insu des participants et des soignants, analyse en intention de traiter"),
        ("donnees_manquantes", "Données manquantes sur le critère : perdus de vue, données disponibles pour presque tous les participants"),
        ("mesure_du_critere", "Mesure du critère : méthode adaptée, même mesure dans les groupes, évaluateurs en insu"),
        ("selection_du_resultat", "Sélection du résultat rapporté : protocole ou plan d'analyse enregistré avant, résultat conforme à ce plan"),
    ],
    "quadas2": [
        ("biais_selection_des_patients", "Risque de biais, sélection des patients : échantillon consécutif ou aléatoire, pas de plan cas-témoins, pas d'exclusions inappropriées"),
        ("biais_test_evalue", "Risque de biais, test évalué : interprété sans connaître le résultat de la référence, seuil fixé à l'avance"),
        ("biais_reference", "Risque de biais, test de référence : classe correctement la maladie, interprété sans connaître le résultat du test évalué"),
        ("biais_flux_et_delais", "Risque de biais, flux et délais : délai approprié entre les deux tests, même référence pour tous, tous les patients analysés"),
        ("applicabilite_selection_des_patients", "Applicabilité, patients : les patients inclus correspondent à la question posée"),
        ("applicabilite_test_evalue", "Applicabilité, test évalué : le test, sa réalisation et son interprétation correspondent à la question posée"),
        ("applicabilite_reference", "Applicabilité, test de référence : la maladie définie par la référence correspond à la question posée"),
    ],
    "amstar2": [
        ("q01_pico", "La question et les critères d'inclusion comprennent population, intervention, comparateur et critères"),
        ("q02_protocole", "Les méthodes ont été établies avant la revue (protocole enregistré ou publié) et les écarts sont justifiés"),
        ("q03_plans_d_etude", "Le choix des plans d'étude inclus est expliqué"),
        ("q04_recherche", "La recherche documentaire est complète : au moins deux bases, mots-clés ou équation, restrictions justifiées"),
        ("q05_selection_en_double", "La sélection des études est faite en double"),
        ("q06_extraction_en_double", "L'extraction des données est faite en double"),
        ("q07_etudes_exclues", "La liste des études exclues est fournie, avec les raisons"),
        ("q08_description_des_etudes", "Les études incluses sont décrites en détail"),
        ("q09_risque_de_biais", "Le risque de biais de chaque étude incluse est évalué par une technique satisfaisante"),
        ("q10_financement_des_etudes", "Les sources de financement des études incluses sont rapportées"),
        ("q11_methodes_statistiques", "Si méta-analyse : les méthodes de combinaison statistique sont appropriées"),
        ("q12_impact_du_biais", "Si méta-analyse : l'effet du risque de biais des études sur le résultat groupé est évalué"),
        ("q13_biais_dans_l_interpretation", "Le risque de biais des études est pris en compte dans l'interprétation et la discussion"),
        ("q14_heterogeneite", "L'hétérogénéité observée est expliquée et discutée"),
        ("q15_biais_de_publication", "Si méta-analyse : le biais de publication est recherché et son effet discuté"),
        ("q16_conflits_d_interets", "Les conflits d'intérêts et le financement de la revue sont déclarés"),
    ],
    # ROBINS-I, version 1 (Sterne et al., BMJ 2016) : sept domaines, pour un critère donné, en jugeant l'effet
    # de l'attribution à l'intervention.
    "robins_i": [
        ("confusion", "Biais de confusion : des facteurs pronostiques ont-ils pu influencer à la fois l'intervention reçue et le résultat ? Facteurs de confusion importants mesurés et pris en compte par la conception ou l'analyse (ajustement, appariement, stratification) ; groupes comparables au départ"),
        ("selection_des_participants", "Sélection des participants : l'entrée dans l'étude ou dans l'analyse dépend-elle de caractéristiques observées après le début de l'intervention ? Le début du suivi coïncide-t-il avec le début de l'intervention ?"),
        ("classement_des_interventions", "Classement des interventions : groupes d'intervention définis clairement, statut de chaque participant fixé au début de l'intervention, sans dépendre du résultat"),
        ("ecarts_aux_interventions", "Écarts par rapport aux interventions prévues : écarts dus au contexte de l'étude (co-interventions déséquilibrées entre les groupes, changements de groupe) et leur prise en compte dans l'analyse"),
        ("donnees_manquantes", "Données manquantes : résultat disponible pour presque tous les participants, manquants peu nombreux et équilibrés entre les groupes, ou analyse qui en tient compte"),
        ("mesure_du_critere", "Mesure du critère : méthode adaptée et identique dans les groupes ; évaluateurs ignorant l'intervention reçue, ou critère objectif peu sujet à interprétation"),
        ("selection_du_resultat", "Sélection du résultat rapporté : résultat choisi parmi plusieurs mesures, analyses ou sous-groupes ? Protocole ou plan d'analyse établi avant, résultats conformes à ce plan"),
    ],
    "agree2": [
        ("champ_et_objectifs", "Champ et objectifs : objectifs, questions de santé et population décrits précisément"),
        ("participation_des_groupes", "Participation des groupes concernés : professionnels et patients associés, utilisateurs définis"),
        ("rigueur_d_elaboration", "Rigueur d'élaboration : recherche systématique des preuves, lien explicite entre preuves et recommandations, relecture externe"),
        ("clarte_et_presentation", "Clarté et présentation : recommandations précises, options de prise en charge présentées"),
        ("applicabilite", "Applicabilité : freins, outils de mise en œuvre, ressources, critères de suivi"),
        ("independance_editoriale", "Indépendance éditoriale : financeur sans influence, conflits d'intérêts déclarés et gérés"),
    ],
}

# Valeurs permises par outil, de la plus favorable à la moins favorable. « non_evaluable » en plus.
VALEURS = {"rob2": ("faible", "quelques_reserves", "eleve"), "quadas2": ("faible", "incertain", "eleve"),
           "amstar2": ("oui", "oui_partiel", "non", NON_RAPPORTE), "agree2": ("elevee", "moyenne", "faible"),
           "robins_i": ("faible", "modere", "serieux", "critique", NON_RAPPORTE)}
# Ce que mesure l'axe « jugement » : jamais une certitude des preuves (VS-D44).
NATURE_DU_JUGEMENT = {"rob2": "risque_de_biais", "quadas2": "risque_de_biais", "robins_i": "risque_de_biais",
                      "amstar2": "fiabilite_de_la_methode", "agree2": "fiabilite_de_la_methode"}
FAVORABLES = {"rob2": ("faible",), "quadas2": ("faible",), "amstar2": ("oui", "oui_partiel"), "agree2": ("elevee", "moyenne"),
              "robins_i": ("faible", "modere")}
# Jugements défavorables qui exigent le passage montrant le défaut, sur texte intégral : sans lui, le domaine
# devient « non rapporté » (un silence n'est pas un défaut).
DEFAVORABLES_A_PROUVER = {"amstar2": ("non",), "robins_i": ("serieux", "critique")}
SANS_OBJET = "sans_objet"                 # AMSTAR 2 : questions réservées aux méta-analyses
AMSTAR_SI_META_ANALYSE = ("q11_methodes_statistiques", "q12_impact_du_biais", "q15_biais_de_publication")
AMSTAR_CRITIQUES = ("q02_protocole", "q04_recherche", "q07_etudes_exclues", "q09_risque_de_biais",
                    "q11_methodes_statistiques", "q13_biais_dans_l_interpretation", "q15_biais_de_publication")

# Jugement global de chaque outil, du moins bon au meilleur : l'échelle des « crans » du banc d'essai.
ECHELLES = {"rob2": ("eleve", "quelques_reserves", "faible"), "quadas2": ("eleve", "incertain", "faible"),
            "amstar2": ("tres_faible", "faible", "moderee", "elevee"), "agree2": ("faible", "moyenne", "elevee"),
            "robins_i": ("critique", "serieux", "modere", "faible")}
# Jugement global de l'outil → qualité méthodologique de la fiche v2.
QUALITE = {"rob2": {"faible": "elevee", "quelques_reserves": "moyenne", "eleve": "faible"},
           "quadas2": {"faible": "elevee", "incertain": "moyenne", "eleve": "faible"},
           "amstar2": {"elevee": "elevee", "moderee": "moyenne", "faible": "faible", "tres_faible": "faible"},
           "agree2": {"elevee": "elevee", "moyenne": "moyenne", "faible": "faible"},
           "robins_i": {"faible": "elevee", "modere": "moyenne", "serieux": "faible", "critique": "faible"}}
GRADES = ("eleve", "modere", "faible", "tres_faible")
_NOMME_GRADE = re.compile(r"grade|certainty|certitude|quality of (?:the )?evidence|qualité de(?:s)? preuves?", re.I)

SORTIE_RESUME = 5000
SORTIE_INTEGRAL = 12000
MAX_JUSTIFICATION = 400


# --- Requête ----------------------------------------------------------------------------------

def requete_appreciation(ref, doc, consigne, type_etude, etape="appreciation", outil=None, critere=None):
    """Requête d'appréciation. Renvoie None si aucun outil ne correspond au type d'étude.

    « outil » impose la grille (choisie d'après le plan d'étude) ; à défaut, elle se déduit du type
    d'étude donné par le tri. « critere » nomme le critère à juger, quand l'outil juge un critère
    donné (ROBINS-I) ; à défaut, le critère principal de l'étude.
    """
    outil = outil or OUTILS.get(type_etude)
    if outil is None:
        return None
    integral = any(b["type"] == "section" for b in doc["blocs"])
    valeurs = list(VALEURS[outil]) + ([SANS_OBJET] if outil == "amstar2" else []) + [NON_EVALUABLE]
    lignes = [f"IDENTIFIANT : {ref['id']}", f"OUTIL À APPLIQUER : {outil}",
              "VALEURS PERMISES : " + " | ".join(valeurs),
              "DOMAINES À JUGER (clé : ce qu'il faut juger)"]
    lignes += [f"- {cle} : {libelle}" for cle, libelle in DOMAINES[outil]]
    if critere:
        lignes.append(f"CRITÈRE À JUGER : {critere}")
    lignes.append("TEXTE FOURNI : " + ("texte intégral" if integral else
                                       "titre et résumé uniquement ; le reste de l'article n'est pas fourni"))
    lignes += ["", texte.texte_pour_ia(doc)]
    return {"id": f"{etape}:{ref['id']}", "consigne": consigne, "contenu": "\n".join(lignes),
            "max_sortie": SORTIE_INTEGRAL if integral else SORTIE_RESUME}


# --- Jugement global, calculé par le code -----------------------------------------------------

def _global_sans_inconnu(outil, domaines):
    """Jugement global quand chaque domaine a une valeur connue."""
    if outil == "amstar2":
        failles = sum(1 for c in AMSTAR_CRITIQUES if domaines[c] == "non")
        if failles > 1:
            return "tres_faible"
        if failles == 1:
            return "faible"
        autres = [v for c, v in domaines.items() if c not in AMSTAR_CRITIQUES]
        return "moderee" if sum(1 for v in autres if v == "non") > 1 else "elevee"
    cles = [c for c, _ in DOMAINES[outil] if not (outil == "quadas2" and c.startswith("applicabilite"))]
    return min((domaines[c] for c in cles), key=ECHELLES[outil].index)


def fourchette(outil, domaines):
    """(pire, meilleur) : le jugement global si chaque domaine non évalué ou non rapporté valait le pire
    jugement possible, puis le meilleur. Calculé par le code, sans IA.

    - RoB 2 : le plus mauvais domaine l'emporte.
    - QUADAS-2 : le plus mauvais des quatre domaines de risque de biais l'emporte ; l'applicabilité
      est gardée à part.
    - AMSTAR 2 : niveau de confiance selon les faiblesses. Plus d'une faiblesse critique : très
      faible ; une seule : faible ; plus d'une faiblesse non critique : modérée ; sinon élevée.
    - AGREE II : le plus mauvais domaine l'emporte.
    - ROBINS-I : le plus mauvais domaine l'emporte (faible si tous sont faibles, modéré si tous sont
      faibles ou modérés, sérieux si l'un est sérieux sans aucun critique, critique si l'un est critique).
    """
    pire_valeur, meilleur_valeur = ("non", "oui") if outil == "amstar2" else (ECHELLES[outil][0], ECHELLES[outil][-1])
    cles = [c for c, _ in DOMAINES[outil]]

    def remplacer(valeur):
        return {c: (valeur if domaines.get(c, NON_EVALUABLE) in INCONNUS else domaines[c]) for c in cles}

    return (_global_sans_inconnu(outil, remplacer(pire_valeur)),
            _global_sans_inconnu(outil, remplacer(meilleur_valeur)))


def jugement_global(outil, domaines):
    """Jugement global de l'outil à partir des jugements par domaine ({clé: valeur}).

    Quand les domaines non évalués ou non rapportés ne changent pas le résultat, c'est la valeur
    acquise ; sinon « non évaluable », et la fourchette dit ce qui reste possible.
    """
    pire, meilleur = fourchette(outil, domaines)
    return pire if pire == meilleur else NON_EVALUABLE


def etiquette_candidate(type_etude, qualite, grade=None, outil=None):
    """RÈGLE CANDIDATE de l'étiquette de façade, à arbitrer par le porteur du projet (VS-D14).

    Elle part de la qualité méthodologique et garde deux règles déjà validées : un essai isolé
    n'est jamais « solide » ; une étude diagnostique non plus. Une étude non randomisée jugée avec
    ROBINS-I, étude isolée elle aussi, ne l'est pas davantage. Une certitude GRADE faible ou très
    faible, rapportée par les auteurs, plafonne l'étiquette.
    """
    if qualite == NON_EVALUABLE:
        return NON_EVALUABLE
    etiquette = {"elevee": "solide", "moyenne": "modere", "faible": "preliminaire"}[qualite]
    if (type_etude in ("essai_randomise", "etude_diagnostique") or outil == "robins_i") and etiquette == "solide":
        etiquette = "modere"
    if grade == "faible" and etiquette == "solide":
        etiquette = "modere"
    if grade == "tres_faible":
        etiquette = "preliminaire"
    return etiquette


# --- Lecture de la réponse --------------------------------------------------------------------

def sans_grille(plan, motif, grille_manquante=None):
    """Appréciation quand aucune grille ne s'applique : aucune note n'est forcée."""
    return {"outil": AUCUN, "grille_manquante": grille_manquante, "motif": motif, "plan_etude": plan,
            "jugement": NON_EVALUABLE, "jugement_outil": NON_EVALUABLE, "fourchette": None,
            "nature_du_jugement": None, "domaines": [], "precision_statistique": None, "grade_rapporte": None,
            "etiquette": NON_EVALUABLE, "justification_etiquette": None}


def lire_appreciation(reponse, doc, type_etude, publier_passages=False, outil=None):
    """Contrôle la réponse de l'IA. Renvoie (appreciation | None, bilan).

    « appreciation » suit le bloc du même nom de docs/FICHE_V2.md, avec en plus « jugement_outil »
    (jugement global dans les mots de l'outil). « bilan » compte ce qui a été proposé, gardé et
    ramené à « non évaluable », avec les motifs.
    publier_passages : vrai seulement quand la licence du texte lu est CC BY ou CC0 (VS-D15).
    outil : grille imposée (choisie d'après le plan d'étude) ; à défaut, celle du type d'étude.
    """
    outil = outil or OUTILS.get(type_etude)
    bilan = {"lisible": False, "outil": outil, "proposes": 0, "gardes": 0, "refus": [], "ecarts": [], "alerte_ia": None}
    if outil is None:
        bilan["refus"].append({"domaine": "réponse", "motif": "aucun outil pour ce type d'étude"})
        return None, bilan
    try:
        brut = lire_json(reponse)
    except Exception as e:
        bilan["refus"].append({"domaine": "réponse", "motif": f"réponse illisible ({e})"})
        return None, bilan
    if not isinstance(brut, dict):
        bilan["refus"].append({"domaine": "réponse", "motif": "réponse illisible (pas un objet)"})
        return None, bilan
    bilan["lisible"] = True
    bilan["alerte_ia"] = _texte(brut.get("alerte"))
    integral = any(b["type"] == "section" for b in doc["blocs"])
    autorises_doc = _nombres(texte.texte_lu(doc))
    proposes = {str(d.get("domaine")): d for d in (brut.get("domaines") or []) if isinstance(d, dict)}
    permises = VALEURS[outil]

    domaines = []
    for cle, _ in DOMAINES[outil]:
        d = proposes.get(cle) or {}
        valeur = d.get("jugement")
        ligne = {"domaine": cle, "jugement": NON_EVALUABLE, "justification": None, "source": None}
        if valeur in (None, NON_EVALUABLE) and not d:
            bilan["ecarts"].append({"domaine": cle, "nature": "domaine absent de la réponse : non évaluable"})
        if valeur == SANS_OBJET and outil == "amstar2" and cle in AMSTAR_SI_META_ANALYSE:
            ligne["jugement"] = SANS_OBJET
            ligne["justification"] = _texte(d.get("justification"))
            domaines.append(ligne)
            continue
        if valeur not in permises:
            if valeur not in (None, NON_EVALUABLE):
                bilan["ecarts"].append({"domaine": cle, "nature": "valeur invalide, ramenée à « non_evaluable »"})
            ligne["justification"] = _texte(d.get("justification"))
            domaines.append(ligne)
            continue
        bilan["proposes"] += 1
        bloc, extrait = texte.trouver_passage(doc, d.get("passage"), _repere(d.get("repere")))
        if valeur in DEFAVORABLES_A_PROUVER.get(outil, ()) and bloc is None and integral:
            # Un silence n'est pas un défaut : un jugement défavorable exige le passage qui montre le défaut.
            bilan["ecarts"].append({"domaine": cle, "nature": f"« {valeur} » sans passage : ramené à « non rapporté »"})
            valeur = NON_RAPPORTE
        favorable = valeur in FAVORABLES[outil]
        if bloc is None and favorable:
            bilan["refus"].append({"domaine": cle, "motif": f"jugement favorable sans passage vérifiable ({extrait})"})
        elif bloc is None and not integral:
            bilan["refus"].append({"domaine": cle, "motif": "résumé seul : une absence ne permet pas de conclure"})
        else:
            ligne["jugement"] = valeur
            bilan["gardes"] += 1
            if bloc is not None:
                ligne["source"] = {"emplacement": bloc["emplacement"], "passage": extrait if publier_passages else None}
        justification = _texte(d.get("justification"))
        if justification and _absents(justification, autorises_doc):
            bilan["ecarts"].append({"domaine": cle, "nature": "justification écartée : chiffre absent du texte lu"})
            justification = None
        ligne["justification"] = justification[:MAX_JUSTIFICATION] if justification else None
        domaines.append(ligne)

    par_cle = {d["domaine"]: d["jugement"] for d in domaines}
    # AMSTAR 2 : une question réservée aux méta-analyses, sans objet, ne compte ni pour ni contre.
    pour_le_calcul = {c: ("oui" if v == SANS_OBJET else v) for c, v in par_cle.items()}
    pire, meilleur = fourchette(outil, pour_le_calcul)
    global_outil = pire if pire == meilleur else NON_EVALUABLE
    qualite = QUALITE[outil].get(global_outil, NON_EVALUABLE)

    grade = None
    g = brut.get("grade") if isinstance(brut.get("grade"), dict) else {}
    if g.get("valeur") in GRADES:
        bloc, extrait = texte.trouver_passage(doc, g.get("passage"), _repere(g.get("repere")))
        if bloc is not None and _NOMME_GRADE.search(extrait):
            grade = {"valeur": g["valeur"], "source": {"emplacement": bloc["emplacement"],
                                                       "passage": extrait if publier_passages else None}}
        else:
            bilan["refus"].append({"domaine": "grade", "motif": "certitude GRADE sans passage qui la nomme"})

    etiquette = etiquette_candidate(type_etude, qualite, grade["valeur"] if grade else None, outil)
    appreciation = {"outil": outil, "jugement": qualite, "jugement_outil": global_outil,
                    "fourchette": {"pire": pire, "meilleur": meilleur},
                    "nature_du_jugement": NATURE_DU_JUGEMENT[outil], "domaines": domaines,
                    "precision_statistique": None, "grade_rapporte": grade,
                    "etiquette": etiquette, "justification_etiquette": None}
    return appreciation, bilan
