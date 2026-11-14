"""Banc d'essai de l'appréciation méthodologique et de la catégorie d'importance.

Phase 1, séances 6 et 7. Rien n'est publié et la veille hebdomadaire n'est pas concernée.

Mesures :
1. Appréciation : chaque article du corpus « qualité » est apprécié par l'outil de son type
   d'étude (RoB 2, QUADAS-2, AMSTAR 2), à partir de son résumé seul, puis de son texte intégral
   quand il est sous licence CC BY ou CC0. Le jugement global, calculé par le code, est comparé à
   celui des auteurs d'une revue, en « crans » de l'échelle de l'outil.
   Seuil fixé par le porteur du projet (VS-D39), sur le texte intégral : au moins 70 % des
   jugements à un cran au plus du corrigé, et aucun jugement plus favorable de deux crans.
2. Abstention : à partir du résumé seul, la bonne réponse est le plus souvent « non évaluable ».
3. Accord par domaine, quand le corrigé le donne.
4. Catégorie d'importance : répartition sur des publications réelles de 2026-S45. Il n'existe
   pas de corrigé de l'importance : cette mesure décrit, elle ne note pas.
5. Dix publications de 2026-S45 (kinésithérapie, licence ouverte) appréciées sur leur texte
   intégral et classées, pour la relecture par le porteur du projet.
6. Coût réel par article.
7. Séance 7 (VS-D44) : étape « plan d'étude » avant la grille. Corpus : la grille du plan est
   comparée à celle des auteurs de la revue. 2026-S45 : la grille est choisie d'après le plan, et
   « aucune grille applicable » remplace une note forcée. Le jugement global est donné aussi sous
   forme de fourchette ; mesure descriptive, sans seuil. Les seuils de VS-D39 portent sur la lecture
   stricte : tout domaine non évalué ou non rapporté compte comme le pire jugement possible.
   Plus d'appréciation sur résumé seul, sauf demande (« --niveaux tout »).
8. ROBINS-I (VS-D54) : corpus `corpus/robins_i.json`, jugements ROBINS-I déjà publiés par une revue
   sous licence CC BY. Seuil fixé par le porteur du projet (VS-D56), en lecture stricte : au moins
   50 % des jugements globaux identiques au corrigé, plus qu'une réponse fixe au niveau le plus
   fréquent du corpus, et aucun jugement plus favorable de deux crans. « --outils robins_i » ne
   mesure que cette grille ; « --s45-pmids » limite 2026-S45 aux publications nommées.

Aucun texte d'article n'est écrit dans le journal ni dans les résultats, hors courts passages
exacts d'articles sous licence CC BY ou CC0, cités avec leur identifiant (VS-D15).

Usage : python banc/banc_appreciation.py --sortie resultats [--budget 1.5] [--s45 10]
                                         [--classement 30] [--limite 0] [--sans-ia]
                                         [--outils robins_i] [--s45-pmids 42980682,42993769]
« --limite N » : N articles au plus par outil, pour un essai court et peu coûteux.
"""
import argparse
import collections
import importlib.util
import json
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from pipeline import acces, appreciation, classement, ia, plan_etude, texte  # noqa: E402
from pipeline.config import charger_config, charger_consigne  # noqa: E402
from pipeline.extraction import version_consigne  # noqa: E402

_chiffres_spec = importlib.util.spec_from_file_location("chiffres_releves_banc", RACINE / "banc" / "chiffres.py")
chiffres_banc = importlib.util.module_from_spec(_chiffres_spec)
_chiffres_spec.loader.exec_module(chiffres_banc)
_spec = importlib.util.spec_from_file_location("banc_extraction", RACINE / "banc" / "banc_extraction.py")
extraction_banc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(extraction_banc)
chaine = extraction_banc.chaine

CORPUS = RACINE / "banc" / "corpus"
# Seuils fixés par le porteur du projet le 12 novembre 2026 (VS-D39), sur le texte intégral.
SEUIL_UN_CRAN = 0.70
SEUIL_FOURCHETTE = 0.70      # fixé le 13 novembre 2026 (VS-D50)
SEUIL_IDENTIQUE_ROBINS = 0.50     # fixé le 14 novembre 2026 (VS-D56), ROBINS-I seulement
NIVEAUX = ("resume", "integral")
NIVEAUX_DEMANDES = ("tout", "integral")       # « integral » : pas d'appréciation sur résumé seul
OUTILS_DU_CORPUS = {"RoB 2": "rob2", "QUADAS-2": "quadas2", "AMSTAR 2": "amstar2", "AGREE II": "agree2",
                    "ROBINS-I": "robins_i"}
CORPUS_QUALITE = ("qualite.json", "qualite_lisible.json", "robins_i.json")
# ROBINS-I : la case « pas d'information » de l'outil se lit « non rapporté ».
PAS_D_INFORMATION = ("pas_d'information", "pas_d_information", "no_information")
# Jetons de sortie supposés par réponse. « integral » recalé le 13 novembre 2026 sur trois mesures réelles
# (0,0172 $ par article à 1 $ et 5 $ le million de jetons, soit environ 1 700 jetons de sortie) : 2 500 garde
# une marge d'environ 20 % sur le coût réel. Avant, 4 500 donnait une estimation double du coût réel.
SORTIE_ESTIMEE = {"plan": 600, "resume": 1500, "integral": 2500, "classement": 700}
# L'estimation reste prudente : l'entrée est comptée au plus haut. Elle valait 2,0 à 2,1 fois le coût réel sur
# deux lancements, et 1,6 fois attendu après le recalage de la sortie. Un lancement n'est refusé d'emblée que
# si l'estimation dépasse MARGE_ESTIMATION fois le plafond ; le coût réel déjà dépensé est ensuite vérifié
# avant chaque groupe de requêtes, et c'est lui qui arrête la dépense au plafond.
MARGE_ESTIMATION = 1.5


# --- Fonctions pures, testées sans réseau -----------------------------------------------------

def cle(valeur):
    """« quelques réserves », « très faible » → « quelques_reserves », « tres_faible ». ROBINS-I : « pas
    d'information » → « non_rapporte »."""
    sans = "".join(c for c in unicodedata.normalize("NFD", str(valeur or "")) if unicodedata.category(c) != "Mn")
    forme = sans.lower().strip().replace(" ", "_").replace("’", "'")
    return appreciation.NON_RAPPORTE if forme in PAS_D_INFORMATION else forme


def charger_cas():
    """Les cas des deux corpus « qualité », à plat. Un article présent deux fois n'est gardé qu'une fois :
    la version « lisible », plus récente, l'emporte."""
    cas = {}
    for nom in CORPUS_QUALITE:
        chemin = CORPUS / nom
        if not chemin.exists():
            continue
        for g in json.loads(chemin.read_text(encoding="utf-8"))["groupes"]:
            outil = OUTILS_DU_CORPUS.get(g["outil"])
            for c in g["cas"]:
                if c.get("pmid") and outil in appreciation.ECHELLES:
                    type_etude = "meta_analyse" if g["type_etude"] == "revue" else g["type_etude"]
                    cas[c["pmid"]] = {"pmid": c["pmid"], "outil": outil, "type_etude": type_etude,
                                      "reference": c.get("reference", ""), "corrige": c["corrige"],
                                      "source": g["source"]["pmid"], "critere": c.get("critere"),
                                      "conteste": bool(c.get("corrige_conteste"))}
    return list(cas.values())


def corrige_global(outil, corrige):
    """Jugement global du corrigé, dans les mots de l'outil. None si le corrigé n'en permet pas."""
    if outil == "amstar2":
        return cle(corrige.get("confiance_globale")) or None
    if outil in ("rob2", "robins_i"):
        return cle(corrige.get("global")) or None
    if outil == "quadas2":                            # pas de jugement global : le plus mauvais domaine
        valeurs = [cle(v) for v in (corrige.get("biais") or {}).values()]
        echelle = appreciation.ECHELLES["quadas2"]
        return min(valeurs, key=echelle.index) if valeurs and all(v in echelle for v in valeurs) else None
    return None


def comparer(outil, obtenu, attendu):
    """Écart, en crans, entre le jugement obtenu et celui du corrigé. Positif : plus favorable."""
    echelle = appreciation.ECHELLES[outil]
    if attendu not in echelle:
        return {"etat": "sans_corrige", "ecart": None}
    if obtenu not in echelle:
        return {"etat": "non_evaluable", "ecart": None}
    ecart = echelle.index(obtenu) - echelle.index(attendu)
    etat = "exact" if ecart == 0 else "un_cran" if abs(ecart) == 1 else "trop_favorable" if ecart >= 2 else "trop_severe"
    return {"etat": etat, "ecart": ecart}


def comparer_fourchette(outil, fourchette, attendu):
    """La fourchette (pire, meilleur) contient-elle le corrigé, et est-elle étroite (deux niveaux au plus) ?"""
    echelle = appreciation.ECHELLES[outil]
    if not fourchette or attendu not in echelle or fourchette["pire"] not in echelle or fourchette["meilleur"] not in echelle:
        return {"contenu": None, "largeur": None, "etroit": None}
    bas, haut = echelle.index(fourchette["pire"]), echelle.index(fourchette["meilleur"])
    return {"contenu": bas <= echelle.index(attendu) <= haut, "largeur": haut - bas + 1, "etroit": haut - bas <= 1}


def domaines_du_corrige(outil, corrige):
    """Corrigé par domaine, avec les clés du module d'appréciation : {clé: valeur}."""
    if outil in ("rob2", "robins_i"):
        return {k: cle(v) for k, v in corrige.items() if k != "global"}
    if outil == "quadas2":
        d = {f"biais_{k}": cle(v) for k, v in (corrige.get("biais") or {}).items()}
        d.update({f"applicabilite_{k}": cle(v) for k, v in (corrige.get("applicabilite") or {}).items()})
        return d
    if outil == "amstar2":
        questions = corrige.get("questions") or {}
        return {c: cle(questions[c[:3]]) for c, _ in appreciation.DOMAINES["amstar2"] if c[:3] in questions}
    return {}


def accord_domaines(outil, app, corrige):
    """Accord exact, domaine par domaine, entre l'appréciation et le corrigé."""
    attendus = domaines_du_corrige(outil, corrige)
    obtenus = {d["domaine"]: d["jugement"] for d in (app or {}).get("domaines", [])}
    lignes = [{"domaine": c, "attendu": v, "obtenu": obtenus.get(c, appreciation.NON_EVALUABLE)}
              for c, v in attendus.items()]
    return {"compares": len(lignes), "identiques": sum(1 for x in lignes if x["attendu"] == x["obtenu"]),
            "non_evaluables": sum(1 for x in lignes if x["obtenu"] == appreciation.NON_EVALUABLE),
            "non_rapportes": sum(1 for x in lignes if x["obtenu"] == appreciation.NON_RAPPORTE), "detail": lignes}


def seuils(comparaisons):
    """Compare le résultat sur texte intégral aux seuils fixés par le porteur du projet (VS-D39)."""
    juges = [c for c in comparaisons if c["etat"] != "sans_corrige"]
    proches = sum(1 for c in juges if c["etat"] in ("exact", "un_cran"))
    favorables = sum(1 for c in juges if c["etat"] == "trop_favorable")
    part = round(proches / len(juges), 3) if juges else None
    return {
        f"au moins {int(SEUIL_UN_CRAN * 100)} % des jugements à un cran au plus du corrigé, texte intégral": {
            "atteint": part is not None and part >= SEUIL_UN_CRAN, "mesure": f"{proches} sur {len(juges)}", "part": part},
        "aucun jugement plus favorable que le corrigé de deux crans": {"atteint": favorables == 0, "mesure": favorables},
    }


def seuils_robins(comparaisons, attendus):
    """Seuils fixés par le porteur du projet pour ROBINS-I (VS-D56), en lecture stricte.

    « attendus » : jugements globaux des corrigés. La réponse fixe répond partout le niveau le plus
    fréquent des corrigés : elle obtient autant d'identiques que ce niveau compte d'articles.
    """
    paires = [(c, a) for c, a in zip(comparaisons, attendus) if c["etat"] != "sans_corrige"]
    n = len(paires)
    identiques = sum(1 for c, _ in paires if c["etat"] == "exact")
    frequents = collections.Counter(a for _, a in paires).most_common(1)
    fixe = frequents[0][1] if frequents else 0
    favorables = sum(1 for c, _ in paires if c["etat"] == "trop_favorable")
    part = round(identiques / n, 3) if n else None
    return {
        f"au moins {int(SEUIL_IDENTIQUE_ROBINS * 100)} % des jugements globaux identiques au corrigé": {
            "atteint": part is not None and part >= SEUIL_IDENTIQUE_ROBINS, "mesure": f"{identiques} sur {n}", "part": part},
        "plus de jugements identiques qu'une réponse fixe au niveau le plus fréquent du corpus": {
            "atteint": n > 0 and identiques > fixe, "mesure": f"{identiques} contre {fixe}",
            "reponse_fixe": frequents[0][0] if frequents else None},
        "aucun jugement plus favorable que le corrigé de deux crans": {"atteint": n > 0 and favorables == 0,
                                                                      "mesure": favorables},
    }


def seuil_fourchette(articles):
    """Seuil fixé par le porteur du projet (VS-D50) : le corrigé est dans la fourchette, qui couvre deux niveaux au plus."""
    bons = sum(1 for x in articles if x["integral"]["contenu"] and x["integral"]["etroit"])
    part = round(bons / len(articles), 3) if articles else None
    return {f"au moins {int(SEUIL_FOURCHETTE * 100)} % des articles : le corrigé dans la fourchette, qui couvre deux "
            f"niveaux au plus": {"atteint": part is not None and part >= SEUIL_FOURCHETTE,
                                 "mesure": f"{bons} sur {len(articles)}", "part": part}}


def repartition(valeurs):
    return dict(sorted(collections.Counter(str(v) for v in valeurs).items()))


def choisir_classement(fiches, deja, nombre):
    """Fiches de 2026-S45 à classer, en plus de « deja » : kinésithérapie, types d'étude alternés."""
    par_type = collections.defaultdict(list)
    for f in sorted(fiches, key=lambda f: f["id"]):
        if f["pmid"] not in deja:
            par_type[f["type"]].append(f)
    ordre = []
    while any(par_type.values()) and len(ordre) < nombre:
        for t in sorted(par_type):
            if par_type[t] and len(ordre) < nombre:
                ordre.append(par_type[t].pop(0))
    return ordre


def afficher_appreciation(titre, app, bilan):
    print(f"\n--- {titre}")
    if app is None:
        print("  aucune appréciation lisible :", "; ".join(r["motif"] for r in bilan["refus"]))
        return
    if app["outil"] == appreciation.AUCUN:
        print(f"  aucune grille appliquée : {app['motif']}")
        return
    f = app.get("fourchette")
    print(f"  outil {app['outil']} | jugement de l'outil : {app['jugement_outil']} | qualité : {app['jugement']} | "
          f"étiquette candidate : {app['etiquette']}"
          + (f" | fourchette : {f['pire']} à {f['meilleur']}" if f else "")
          + (f" | GRADE rapporté : {app['grade_rapporte']['valeur']}" if app["grade_rapporte"] else ""))
    for d in app["domaines"]:
        ou = f"  [{d['source']['emplacement']}]" if d["source"] else ""
        print(f"  {d['domaine']} : {d['jugement']} — {d['justification'] or 'sans justification'}{ou}"
              + (f"\n      « {d['source']['passage']} »" if d["source"] and d["source"]["passage"] else ""))
    for r in bilan["refus"]:
        print(f"  REFUS {r['domaine']} : {r['motif']}")
    for x in bilan["ecarts"]:
        print(f"  écart {x['domaine']} : {x['nature']}")
    if bilan["alerte_ia"]:
        print(f"  alerte de l'IA : {bilan['alerte_ia']}")


def afficher_plan(titre, plan, bilan):
    print(f"\n--- {titre}")
    if plan is None:
        print("  plan illisible :", "; ".join(bilan["ecarts"]))
        return
    ou = f"  [{plan['source']['emplacement']}]" if plan["source"] else ""
    print(f"  plan : {plan['plan']} | type du tri : {plan['type_tri']} | écart avec le tri : "
          f"{'oui' if plan['ecart_avec_le_tri'] else 'non' if plan['ecart_avec_le_tri'] is False else 'sans objet'}{ou}")
    if plan["justification"]:
        print(f"  {plan['justification']}")
    if plan["source"] and plan["source"]["passage"]:
        print(f"      « {plan['source']['passage']} »")
    if plan["incertitude"]:
        print(f"  incertitude : {plan['incertitude']}")
    for e in bilan["ecarts"]:
        print(f"  écart : {e}")
    if bilan["alerte_ia"]:
        print(f"  alerte de l'IA : {bilan['alerte_ia']}")


def resultats_plan_seul(args, sortie, cas, plans, s45, plans_s45, externes, plans_ext, usages, cfg, modele, prix,
                        consignes, absents):
    """Résultats d'une mesure de l'étape « plan d'étude » seule, sans aucune appréciation."""
    corpus = []
    for c in cas:
        if c["doc"]:
            plan, bilan = plans[c["id"]]
            grille = plan_etude.choisir_grille(plan["plan"])[0] if plan else None
            corpus.append({"pmid": c["pmid"], "reference": c["reference"], "outil": c["outil"], "plan": plan["plan"] if plan else None,
                           "grille_du_plan": grille, "grille_du_corrige_retrouvee": grille == c["outil"],
                           "ecart_avec_le_tri": plan["ecart_avec_le_tri"] if plan else None, "detail": plan, "bilan": bilan})
    hors = []
    for x in externes:
        plan, bilan = plans_ext[x["ref"]["id"]]
        hors.append({"pmid": x["pmid"], "reference": x["reference"], "plan": plan["plan"] if plan else None,
                     "attendu": "etude_diagnostique", "retrouve": bool(plan) and plan["plan"] == "etude_diagnostique",
                     "detail": plan, "bilan": bilan})
    fiches = [{"pmid": x["ref"]["pmid"], "titre": x["ref"]["titre"], "type": x["fiche"]["type"], "pmcid": x["pmcid"],
               "licence": x["licence"], "plan_etude": plans_s45[x["ref"]["id"]][0], "bilan_plan": plans_s45[x["ref"]["id"]][1]}
              for x in s45]
    cout = round(ia.cout_reel([u for u in usages["plan"] if u], modele, prix, "direct"), 4)
    resume = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "lecture": {"plan_seul": True, "declarations_hors_du_corps": not args.sans_declarations},
        "chaine": {"modele": modele, "effort": cfg["ia"].get("effort_raisonnement"), "mode": "direct",
                   "consigne_plan_etude": version_consigne(consignes["plan_etude"])},
        "cout_usd": {"total": cout, "par_article": round(cout / len(usages["plan"]), 4) if usages["plan"] else None},
        "plan_etude": {
            "corpus": {"articles": len(corpus),
                       "grille_du_corrige_retrouvee": sum(1 for p in corpus if p["grille_du_corrige_retrouvee"]),
                       "plan_non_determine": sum(1 for p in corpus if p["plan"] in (None, plan_etude.NON_DETERMINE)),
                       "ecarts_avec_le_tri": sum(1 for p in corpus if p["ecart_avec_le_tri"]),
                       "repartition": repartition(p["plan"] for p in corpus),
                       "grilles_perdues": [p["pmid"] for p in corpus if not p["grille_du_corrige_retrouvee"]]},
            "hors_corpus_diagnostiques": {"articles": len(hors), "plan_attendu_retrouve": sum(1 for h in hors if h["retrouve"]),
                                          "repartition": repartition(h["plan"] for h in hors)},
            "s45": {"articles": len(fiches), "plans": repartition((f["plan_etude"] or {}).get("plan") for f in fiches),
                    "ecarts_avec_le_tri": sum(1 for f in fiches if (f["plan_etude"] or {}).get("ecart_avec_le_tri"))}},
        "corpus": {"articles": len(cas), "avec_texte_integral": len(corpus), "absents_de_pubmed": absents}}
    (sortie / "resultats-plan.json").write_text(json.dumps(
        {"resume": resume, "corpus": corpus, "hors_corpus": hors, "s45": fiches}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n===== RÉSUMÉ =====")
    print(json.dumps(resume, ensure_ascii=False, indent=1))
    print("\n===== PLAN D'ÉTUDE : CORPUS, GRILLE DU PLAN CONTRE GRILLE DU CORRIGÉ =====")
    for p in corpus:
        print(f"  PMID {p['pmid']} | grille du corrigé : {p['outil']} | plan : {p['plan']} | grille du plan : "
              f"{p['grille_du_plan'] or 'aucune'} | {'retrouvée' if p['grille_du_corrige_retrouvee'] else 'DIFFÉRENTE'} | "
              f"écart avec le tri : {p['ecart_avec_le_tri']}")
    print("\n===== PLAN D'ÉTUDE : HORS CORPUS, ÉTUDES DIAGNOSTIQUES DES CHIFFRES RELEVÉS =====")
    for h in hors:
        print(f"  PMID {h['pmid']} | plan : {h['plan']} | attendu : {h['attendu']} | {'retrouvé' if h['retrouve'] else 'DIFFÉRENT'}")
    print("\n===== PLAN D'ÉTUDE : DÉTAIL DES PLANS DIFFÉRENTS =====")
    for p in corpus:
        if not p["grille_du_corrige_retrouvee"]:
            afficher_plan(f"PMID {p['pmid']} — {p['reference']} — grille du corrigé : {p['outil']}", p["detail"], p["bilan"])
    for h in hors:
        if not h["retrouve"]:
            afficher_plan(f"PMID {h['pmid']} — {h['reference']} — plan attendu : {h['attendu']}", h["detail"], h["bilan"])
    print("\n===== PUBLICATIONS RÉELLES DE 2026-S45 : PLAN D'ÉTUDE =====")
    for f in fiches:
        afficher_plan(f"PMID {f['pmid']}, {f['pmcid']}, licence {f['licence']}, {f['type']} — {f['titre'][:110]}",
                      f["plan_etude"], f["bilan_plan"])
    return 0


# --- Programme --------------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sortie", default="resultats-banc")
    p.add_argument("--budget", type=float, default=1.5, help="plafond en dollars, vérifié avant tout appel")
    p.add_argument("--s45", type=int, default=0, help="publications de 2026-S45 à apprécier sur texte intégral")
    p.add_argument("--classement", type=int, default=0, help="publications de 2026-S45 à classer en plus, sur résumé")
    p.add_argument("--limite", type=int, default=0, help="articles au plus par outil (0 : tous)")
    p.add_argument("--sans-ia", action="store_true", help="lit les textes et estime le coût, sans aucun appel à l'IA")
    p.add_argument("--niveaux", choices=NIVEAUX_DEMANDES, default="integral",
                   help="« integral » (défaut) : pas d'appréciation sur résumé seul ; « tout » : aussi sur résumé")
    p.add_argument("--plan-seul", action="store_true",
                   help="mesure l'étape « plan d'étude » seule : aucune appréciation, aucune catégorie")
    p.add_argument("--plan-externe", action="store_true",
                   help="ajoute au plan d'étude les études diagnostiques du corpus de chiffres relevés (hors du "
                        "corpus « qualité »), dont le plan attendu est « étude diagnostique »")
    p.add_argument("--outils", default="",
                   help="grilles du corpus à mesurer, séparées par des virgules (par défaut : toutes), ex. robins_i")
    p.add_argument("--s45-pmids", default="",
                   help="limite 2026-S45 aux publications nommées (PMID séparés par des virgules)")
    p.add_argument("--sans-declarations", action="store_true",
                   help="lit le texte intégral sans les déclarations placées hors du corps (lecture d'avant le 13/11/2026)")
    args = p.parse_args(argv)
    declarations = not args.sans_declarations
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    journal = lambda m: print(m, flush=True)   # noqa: E731

    cfg = charger_config()
    prix = cfg["ia"]["prix_usd_par_million"]
    modele = cfg["ia"]["modele_redaction"]
    consignes = {"appreciation": charger_consigne("appreciation"), "classement": charger_consigne("classement"),
                 "plan_etude": charger_consigne("plan_etude"),
                 "appreciation_robins_i": charger_consigne("appreciation_robins_i")}

    # 1. Cas du corpus, limités par outil si demandé : ceux qui ont un texte lisible d'abord
    cas = charger_cas()
    outils = {o.strip() for o in args.outils.split(",") if o.strip()}
    if outils:
        cas = [c for c in cas if c["outil"] in outils]
    lisibles = {c["pmid"] for nom in ("qualite_lisible.json", "robins_i.json") if (CORPUS / nom).exists()
                for g in json.loads((CORPUS / nom).read_text(encoding="utf-8"))["groupes"] for c in g["cas"]}
    cas.sort(key=lambda c: (c["outil"], c["pmid"] not in lisibles, c["pmid"]))
    if args.limite:
        garde = collections.Counter()
        cas = [c for c in cas if not (garde.update([c["outil"]]) or garde[c["outil"]] > args.limite)]
    refs = {r["pmid"]: r for r in chaine.recuperer_pubmed(sorted({c["pmid"] for c in cas}), cfg)}
    absents = sorted(c["pmid"] for c in cas if c["pmid"] not in refs)
    cas = [c for c in cas if c["pmid"] in refs]
    journal(f"Corpus « qualité » : {len(cas)} articles lus dans PubMed, absents : {absents} — "
            + ", ".join(f"{o} {n}" for o, n in sorted(collections.Counter(c["outil"] for c in cas).items())))

    # 2. Textes intégraux sous licence ouverte
    infos, echecs = acces.decrire_europe_pmc([c["pmid"] for c in cas], journal)
    lus = extraction_banc.lire_textes([refs[c["pmid"]] for c in cas], infos, declarations=declarations)
    for c in cas:
        c["id"] = refs[c["pmid"]]["id"]
        c["doc"] = lus[c["id"]]["doc"]
        journal("  " + extraction_banc.structure(f"{c['id']} ({c['outil']})", lus[c["id"]])
                + (f" | {c['doc'].get('declarations', 0)} déclarations hors du corps" if c["doc"] and declarations else ""))
    journal(f"Texte intégral lu pour {sum(1 for c in cas if c['doc'])} articles sur {len(cas)} "
            f"(paquets Europe PMC en échec : {echecs})")
    if declarations:
        journal(f"Déclarations placées hors du corps de l'article : lues pour "
                f"{sum(1 for c in cas if c['doc'] and c['doc'].get('declarations'))} articles sur "
                f"{sum(1 for c in cas if c['doc'])}")

    # 2 bis. Contrôle hors corpus : études diagnostiques du corpus de chiffres relevés (plan attendu : diagnostique)
    externes = []
    if args.plan_externe:
        deja = {c["pmid"] for c in cas}
        candidats = [c for c in chiffres_banc.cas_du_corpus(chiffres_banc.charger())
                     if c["type_etude"] == "etude_diagnostique" and c["pmid"] not in deja]
        refs_ext = {r["pmid"]: r for r in chaine.recuperer_pubmed(sorted(c["pmid"] for c in candidats), cfg)}
        infos_ext, _ = acces.decrire_europe_pmc([c["pmid"] for c in candidats], journal)
        lus_ext = extraction_banc.lire_textes([refs_ext[c["pmid"]] for c in candidats if c["pmid"] in refs_ext],
                                              infos_ext, declarations=declarations)
        for c in candidats:
            ref = refs_ext.get(c["pmid"])
            if ref and lus_ext[ref["id"]]["doc"]:
                externes.append({"pmid": c["pmid"], "reference": c["reference"], "ref": ref, "doc": lus_ext[ref["id"]]["doc"]})
        journal(f"Hors corpus « qualité » : {len(externes)} études diagnostiques lues en entier sur {len(candidats)}")

    # 3. Publications réelles de 2026-S45
    s45, a_classer = [], []
    if args.s45 or args.classement:
        donnees = json.loads((RACINE / "site" / "data" / "semaines" / "2026-S45.json").read_text(encoding="utf-8"))
        kine = [f for f in donnees["fiches"] if f.get("source") == "pubmed"
                and any(d.startswith("kine/") for d in f.get("domaines", []))]
        licences, _ = acces.decrire_europe_pmc([f["pmid"] for f in kine], journal)
        voulus = {x.strip() for x in args.s45_pmids.split(",") if x.strip()}
        choisies = [f for f in kine if f["pmid"] in voulus] if voulus else kine
        candidates = extraction_banc.choisir_s45(choisies, licences, args.s45) if args.s45 else []
        autres = choisir_classement(kine, {f["pmid"] for f in candidates[:args.s45]}, args.classement)
        refs_s45 = {r["pmid"]: r for r in chaine.recuperer_pubmed(
            sorted({f["pmid"] for f in candidates + autres}), cfg)}
        for f in candidates:
            if len(s45) >= args.s45 or f["pmid"] not in refs_s45:
                continue
            ref = refs_s45[f["pmid"]]
            lu = extraction_banc.lire_textes([ref], licences, declarations=declarations)[ref["id"]]
            if lu["doc"]:
                s45.append({"ref": ref, "fiche": f, **lu})
        # Les catégories d'importance ne sont mesurées que sur demande (« --classement ») : pas de coût en plus.
        a_classer = ([{"ref": x["ref"], "fiche": x["fiche"]} for x in s45] + [
            {"ref": refs_s45[f["pmid"]], "fiche": f} for f in autres if f["pmid"] in refs_s45]) if args.classement else []
        journal(f"2026-S45 : {len(kine)} fiches de kinésithérapie ; {len(s45)} à apprécier sur texte intégral, "
                f"{len(a_classer)} à classer")
        for x in s45:
            journal("  " + extraction_banc.structure(f"{x['ref']['id']} ({x['fiche']['type']})", x))

    # 4. Étape « plan d'étude » : une requête par article lu en entier, puis garde-fou budgétaire
    def demande(ref, doc, type_etude, etape, outil=None, critere=None):
        consigne = consignes["appreciation_robins_i" if outil == "robins_i" else "appreciation"]
        return appreciation.requete_appreciation(ref, doc, consigne, type_etude, etape, outil, critere)

    demande_plan = lambda ref, doc, tri, etape: plan_etude.requete_plan(ref, doc, consignes["plan_etude"], tri, etape)  # noqa: E731
    reqs = {
        "plan": [demande_plan(refs[c["pmid"]], c["doc"], c["type_etude"], "plan-corpus") for c in cas if c["doc"]]
                + [demande_plan(x["ref"], x["doc"], x["fiche"]["type"], "plan-s45") for x in s45]
                + [demande_plan(x["ref"], x["doc"], "etude_diagnostique", "plan-externe") for x in externes],
        "resume": [demande(refs[c["pmid"]], texte.document_resume(refs[c["pmid"]]), c["type_etude"],
                           "appreciation-resume", c["outil"]) for c in cas] if args.niveaux == "tout" else [],
        "integral": [demande(refs[c["pmid"]], c["doc"], c["type_etude"], "appreciation-integral", c["outil"],
                             c.get("critere")) for c in cas if c["doc"]],
        "s45": [],     # construit après l'étape « plan d'étude » : la grille dépend du plan
        "classement": [classement.requete_classement(x["ref"], consignes["classement"], x["fiche"]["type"])
                       for x in a_classer],
    }
    reqs = {k: [r for r in v if r] for k, v in reqs.items()}
    if args.plan_seul:
        reqs.update({"resume": [], "integral": [], "classement": []})
        a_classer = []
    # Borne haute avant tout appel : chaque publication de 2026-S45 serait appréciée avec la grille du tri.
    s45_borne = [] if args.plan_seul else [
        r for r in (demande(x["ref"], x["doc"], x["fiche"]["type"], "appreciation-s45") for x in s45) if r]

    def estimer(plan, resume, integral, classements):
        return (ia.estimer_cout(plan, modele, prix, SORTIE_ESTIMEE["plan"], "direct")
                + ia.estimer_cout(resume, modele, prix, SORTIE_ESTIMEE["resume"], "direct")
                + ia.estimer_cout(integral, modele, prix, SORTIE_ESTIMEE["integral"], "direct")
                + ia.estimer_cout(classements, modele, prix, SORTIE_ESTIMEE["classement"], "direct"))

    estime = estimer(reqs["plan"], reqs["resume"], reqs["integral"] + s45_borne, reqs["classement"])
    journal(f"Coût estimé : {estime:.2f} $ (plafond {args.budget:.2f} $) — {len(reqs['plan'])} plans d'étude "
            f"(dont {len(externes)} hors corpus « qualité »), "
            f"{len(reqs['resume'])} appréciations sur résumé, {len(reqs['integral'])} sur texte intégral, "
            f"jusqu'à {len(s45_borne)} sur 2026-S45, {len(reqs['classement'])} classements")
    if estime > args.budget * MARGE_ESTIMATION:
        journal("ARRÊT : estimation supérieure au plafond, aucun appel n'est fait.")
        return 2
    if estime > args.budget:
        journal(f"Estimation prudente au-dessus du plafond, sous {MARGE_ESTIMATION} fois le plafond : "
                f"le coût réel est vérifié avant chaque groupe de requêtes.")
    if args.sans_ia:
        journal("Lancement sans IA : arrêt ici, aucun appel n'est fait, aucun coût.")
        return 0

    fournisseur = ia.fournisseur(cfg)
    usages = collections.defaultdict(list)

    def lancer(nom):
        debut = time.monotonic()
        res = extraction_banc.appeler(fournisseur, reqs[nom], modele) if reqs[nom] else {}
        journal(f"{nom} : {len(res)} réponses en {int(time.monotonic() - debut)} s")
        return res

    def lire(res, etape, ref, doc, type_etude, ouvert, outil=None):
        reponse, usage = res.get(f"{etape}:{ref['id']}", (None, {}))
        usages[etape.split("-")[-1]].append(usage)
        app, bilan = appreciation.lire_appreciation(reponse, doc, type_etude, publier_passages=ouvert, outil=outil)
        if usage.get("erreur") or usage.get("fin") == "length":
            bilan["refus"].append({"domaine": "réponse", "motif": "réponse illisible : " +
                                   (usage.get("erreur") or "réponse coupée, plafond de sortie atteint")})
        return app, bilan

    def lire_le_plan(res, etape, ref, doc, tri):
        reponse, usage = res.get(f"{etape}:{ref['id']}", (None, {}))
        usages["plan"].append(usage)
        plan, bilan = plan_etude.lire_plan(reponse, doc, tri, publier_passage=True)
        if usage.get("erreur") or usage.get("fin") == "length":
            bilan["ecarts"].append("réponse illisible : " + (usage.get("erreur") or "réponse coupée"))
        return plan, bilan

    # 5. Plan d'étude : corpus (grille comparée à celle du corrigé) et 2026-S45 (grille choisie d'après le plan)
    res = {"plan": lancer("plan")}
    plans = {c["id"]: lire_le_plan(res["plan"], "plan-corpus", refs[c["pmid"]], c["doc"], c["type_etude"])
             for c in cas if c["doc"]}
    plans_s45 = {x["ref"]["id"]: lire_le_plan(res["plan"], "plan-s45", x["ref"], x["doc"], x["fiche"]["type"]) for x in s45}
    plans_ext = {x["ref"]["id"]: lire_le_plan(res["plan"], "plan-externe", x["ref"], x["doc"], "etude_diagnostique")
                 for x in externes}
    if args.plan_seul:
        return resultats_plan_seul(args, sortie, cas, plans, s45, plans_s45, externes, plans_ext, usages, cfg,
                                   modele, prix, consignes, absents)
    routes = {}
    for x in s45:
        plan = plans_s45[x["ref"]["id"]][0]
        routes[x["ref"]["id"]] = plan_etude.choisir_grille(plan["plan"] if plan else plan_etude.NON_DETERMINE)
    reqs["s45"] = [r for r in (demande(x["ref"], x["doc"], x["fiche"]["type"], "appreciation-s45", routes[x["ref"]["id"]][0])
                               for x in s45 if routes[x["ref"]["id"]][0]) if r]
    deja = ia.cout_reel([u for u in usages["plan"] if u], modele, prix, "direct")
    restant = estimer([], reqs["resume"], reqs["integral"] + reqs["s45"], reqs["classement"])
    journal(f"Plans d'étude lus ({deja:.3f} $) ; {len(reqs['s45'])} publications de 2026-S45 sur {len(s45)} ont une grille ; "
            f"reste à dépenser au plus {restant:.2f} $")
    if deja >= args.budget:
        journal("ARRÊT : le plafond serait dépassé, aucune appréciation n'est lancée.")
        return 2
    groupes = {"resume": "resume", "integral": "integral", "s45": "integral", "classement": "classement"}
    for nom, nature in groupes.items():
        depense = ia.cout_reel([u for us in usages.values() for u in us if u], modele, prix, "direct")
        prochain = ia.estimer_cout(reqs[nom], modele, prix, SORTIE_ESTIMEE[nature], "direct")
        if reqs[nom] and depense + prochain > args.budget:
            journal(f"{nom} non lancé : {depense:.3f} $ déjà dépensés et {prochain:.2f} $ estimés dépasseraient le "
                    f"plafond de {args.budget:.2f} $")
            res[nom] = {}
            continue
        res[nom] = lancer(nom)

    # 6. Appréciations du corpus, à la grille du corrigé ; 2026-S45, à la grille du plan
    lignes = []
    for c in cas:
        ref = refs[c["pmid"]]
        attendu = corrige_global(c["outil"], c["corrige"])
        ligne = {"pmid": c["pmid"], "outil": c["outil"], "reference": c["reference"], "attendu": attendu,
                 "texte_integral": bool(c["doc"]), "corrige_conteste": c.get("conteste", False)}
        if c["doc"]:
            plan, bilan_plan = plans[c["id"]]
            grille = plan_etude.choisir_grille(plan["plan"])[0] if plan else None
            ligne["plan_etude"] = {"plan": plan["plan"] if plan else None, "grille_du_plan": grille,
                                   "grille_du_corrige_retrouvee": grille == c["outil"],
                                   "ecart_avec_le_tri": plan["ecart_avec_le_tri"] if plan else None,
                                   "detail": plan, "bilan": bilan_plan}
        for niveau, doc in (("resume", texte.document_resume(ref)), ("integral", c["doc"])):
            if doc is None or (niveau == "resume" and args.niveaux != "tout"):
                continue
            app, bilan = lire(res[niveau], f"appreciation-{niveau}", ref, doc, c["type_etude"], niveau == "integral", c["outil"])
            f = (app or {}).get("fourchette")
            # Lecture stricte sur texte intégral : un domaine non évalué compte comme le pire jugement possible.
            obtenu = f["pire"] if (f and niveau == "integral") else (app["jugement_outil"] if app else None)
            ligne[niveau] = {"obtenu": obtenu, "jugement_outil": app["jugement_outil"] if app else None, "fourchette": f,
                             **comparer(c["outil"], obtenu, attendu),
                             **(comparer_fourchette(c["outil"], f, attendu) if niveau == "integral" else {}),
                             "domaines": accord_domaines(c["outil"], app, c["corrige"]),
                             "appreciation": app, "bilan": bilan}
        lignes.append(ligne)

    # 7. Dix publications de 2026-S45 et classements
    fiches_s45 = []
    for x in s45:
        plan, bilan_plan = plans_s45[x["ref"]["id"]]
        outil, manquante, motif = routes[x["ref"]["id"]]
        if outil:
            app, bilan = lire(res["s45"], "appreciation-s45", x["ref"], x["doc"], x["fiche"]["type"], True, outil)
        else:
            app = appreciation.sans_grille(plan, motif, manquante)
            bilan = {"lisible": True, "outil": appreciation.AUCUN, "proposes": 0, "gardes": 0, "refus": [], "ecarts": [],
                     "alerte_ia": None}
        fiches_s45.append({"pmid": x["ref"]["pmid"], "titre": x["ref"]["titre"], "type": x["fiche"]["type"],
                           "pmcid": x["pmcid"], "licence": x["licence"], "plan_etude": plan, "bilan_plan": bilan_plan,
                           "grille": outil, "grille_manquante": manquante, "appreciation": app, "bilan": bilan})
    classes = []
    for x in a_classer:
        reponse, usage = res["classement"].get(f"classement:{x['ref']['id']}", (None, {}))
        usages["classement"].append(usage)
        c, bilan = classement.lire_classement(reponse, x["ref"])
        classes.append({"pmid": x["ref"]["pmid"], "titre": x["ref"]["titre"], "type": x["fiche"]["type"],
                        "verdict_actuel": x["fiche"].get("verdict"), "etiquette_actuelle": x["fiche"].get("etiquette"),
                        "classement": c, "bilan": bilan})

    # 8. Résumé
    cout = {k: round(ia.cout_reel([u for u in us if u], modele, prix, "direct"), 4) for k, us in usages.items()}
    integral = [x["integral"] for x in lignes if "integral" in x]
    sur_resume = [x["resume"] for x in lignes if "resume" in x]
    par_outil = {}
    for outil in sorted({x["outil"] for x in lignes}):
        du = [x["integral"] for x in lignes if x["outil"] == outil and "integral" in x]
        par_outil[outil] = {"articles_avec_texte_integral": len(du), "etats": repartition(d["etat"] for d in du),
                            "domaines_identiques": f"{sum(d['domaines']['identiques'] for d in du)} sur "
                                                   f"{sum(d['domaines']['compares'] for d in du)}"}
    domaines_resume = [d for x in sur_resume for d in (x["appreciation"] or {}).get("domaines", [])]
    plans_corpus = [x["plan_etude"] for x in lignes if "plan_etude" in x]
    avec_fourchette = [x for x in lignes if "integral" in x and x["integral"].get("contenu") is not None]
    bien_notes = [x for x in avec_fourchette if appreciation.ECHELLES[x["outil"]].index(x["attendu"]) >= 2]

    def stats_fourchette(xs):
        n = len(xs)
        return {"articles": n, "corrige_dans_la_fourchette": sum(1 for x in xs if x["integral"]["contenu"]),
                "fourchette_etroite": sum(1 for x in xs if x["integral"]["etroit"]),
                "dans_la_fourchette_et_etroite": sum(1 for x in xs if x["integral"]["contenu"] and x["integral"]["etroit"]),
                "largeur_moyenne": round(sum(x["integral"]["largeur"] for x in xs) / n, 2) if n else None}

    resume = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "lecture": {"niveaux": args.niveaux, "declarations_hors_du_corps": declarations},
        "chaine": {"modele": modele, "effort": cfg["ia"].get("effort_raisonnement"), "mode": "direct",
                   "consigne_plan_etude": version_consigne(consignes["plan_etude"]),
                   "consigne_appreciation": version_consigne(consignes["appreciation"]),
                   "consigne_appreciation_robins_i": version_consigne(consignes["appreciation_robins_i"]),
                   "consigne_classement": version_consigne(consignes["classement"])},
        "cout_usd": {"total": round(sum(cout.values()), 4), **cout,
                     "par_article": {k: round(cout[k] / len(us), 4) for k, us in usages.items() if us}},
        "corpus": {"articles": len(lignes), "avec_texte_integral": len(integral), "absents_de_pubmed": absents},
        "plan_etude": {
            "corpus": {"articles": len(plans_corpus),
                       "grille_du_corrige_retrouvee": sum(1 for p in plans_corpus if p["grille_du_corrige_retrouvee"]),
                       "plan_non_determine": sum(1 for p in plans_corpus if p["plan"] in (None, plan_etude.NON_DETERMINE)),
                       "ecarts_avec_le_tri": sum(1 for p in plans_corpus if p["ecart_avec_le_tri"]),
                       "repartition": repartition(p["plan"] for p in plans_corpus)},
            "s45": {"articles": len(fiches_s45), "plans": repartition((f["plan_etude"] or {}).get("plan") for f in fiches_s45),
                    "grilles": repartition(f["grille"] or "aucune" for f in fiches_s45),
                    "ecarts_avec_le_tri": sum(1 for f in fiches_s45 if (f["plan_etude"] or {}).get("ecart_avec_le_tri"))}},
        "texte_integral": {"etats": repartition(d["etat"] for d in integral),
                           "jugements_obtenus": repartition(d["obtenu"] for d in integral), "par_outil": par_outil,
                           "lecture_stricte": "un domaine non évalué ou non rapporté compte comme le pire jugement possible",
                           "jugements_de_l_outil": repartition(d["jugement_outil"] for d in integral)},
        "fourchettes": {**stats_fourchette(avec_fourchette), "articles_bien_notes": stats_fourchette(bien_notes),
                        "seuil": seuil_fourchette(avec_fourchette)},
        "resume_seul": {"etats": repartition(d["etat"] for d in sur_resume),
                        "domaines_non_evaluables": f"{sum(1 for d in domaines_resume if d['jugement'] == appreciation.NON_EVALUABLE)} "
                                                   f"sur {len(domaines_resume)}"},
        "seuils": seuils([x["integral"] for x in lignes if "integral" in x and x["outil"] != "robins_i"]),
        "seuils_robins_i": seuils_robins([x["integral"] for x in lignes if "integral" in x and x["outil"] == "robins_i"],
                                         [x["attendu"] for x in lignes if "integral" in x and x["outil"] == "robins_i"]),
        # Second score, comme pour VS-D29 : sans les corrigés marqués contestés avant la mesure.
        "seuils_robins_i_sans_corriges_contestes": seuils_robins(
            [x["integral"] for x in lignes if "integral" in x and x["outil"] == "robins_i" and not x["corrige_conteste"]],
            [x["attendu"] for x in lignes if "integral" in x and x["outil"] == "robins_i" and not x["corrige_conteste"]]),
        "etiquettes_candidates": {
            "corpus_texte_integral": repartition((d["appreciation"] or {}).get("etiquette") for d in integral),
            "corpus_resume_seul": repartition((d["appreciation"] or {}).get("etiquette") for d in sur_resume),
            "s45_texte_integral": repartition((f["appreciation"] or {}).get("etiquette") for f in fiches_s45)},
        "categories_s45": {"classees": len(classes),
                           "repartition": repartition((c["classement"] or {}).get("categorie") for c in classes),
                           "sens_pratique": repartition((c["classement"] or {}).get("sens_pratique") for c in classes),
                           "verdicts_actuels": repartition(c["verdict_actuel"] for c in classes),
                           "ecarts_du_controle": sum(len(c["bilan"]["ecarts"]) for c in classes)},
    }
    (sortie / "resultats-appreciation.json").write_text(json.dumps(
        {"resume": resume, "corpus": lignes, "s45": fiches_s45, "classements": classes}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print("\n===== RÉSUMÉ =====")
    print(json.dumps(resume, ensure_ascii=False, indent=1))
    print("\n===== PLAN D'ÉTUDE : CORPUS, GRILLE DU PLAN CONTRE GRILLE DU CORRIGÉ =====")
    for x in lignes:
        p = x.get("plan_etude")
        if p:
            print(f"  PMID {x['pmid']} | grille du corrigé : {x['outil']} | plan : {p['plan']} | grille du plan : "
                  f"{p['grille_du_plan'] or 'aucune'} | {'retrouvée' if p['grille_du_corrige_retrouvee'] else 'DIFFÉRENTE'} | "
                  f"écart avec le tri : {p['ecart_avec_le_tri']}")
    print("\n===== PLAN D'ÉTUDE : CORPUS, DÉTAIL DES PLANS DIFFÉRENTS =====")
    for x in lignes:
        p = x.get("plan_etude")
        if p and not p["grille_du_corrige_retrouvee"]:
            afficher_plan(f"PMID {x['pmid']} — {x['reference']} — grille du corrigé : {x['outil']}", p["detail"], p["bilan"])
    print("\n===== CORPUS : JUGEMENT GLOBAL, OBTENU CONTRE CORRIGÉ =====")
    for x in lignes:
        morceaux = [f"{niveau} : {x[niveau]['obtenu']} → {x[niveau]['etat']}" for niveau in NIVEAUX if niveau in x]
        dom = x.get("integral", x.get("resume", {})).get("domaines", {})
        f = x.get("integral", {}).get("fourchette")
        print(f"  PMID {x['pmid']} | {x['outil']} | corrigé : {x['attendu']}"
              + (" (contesté)" if x.get("corrige_conteste") else "") + " | " + " | ".join(morceaux)
              + (f" | fourchette : {f['pire']} à {f['meilleur']} | corrigé dans la fourchette : "
                 f"{x['integral']['contenu']} | largeur : {x['integral']['largeur']}" if f else "")
              + (f" | domaines identiques : {dom['identiques']} sur {dom['compares']}"
                 f" dont non rapportés : {dom['non_rapportes']}" if dom.get("compares") else ""))
    print("\n===== CORPUS : DOMAINES EN DÉSACCORD, TEXTE INTÉGRAL =====")
    for x in lignes:
        for d in x.get("integral", {}).get("domaines", {}).get("detail", []):
            if d["attendu"] != d["obtenu"]:
                print(f"  PMID {x['pmid']} | {d['domaine']} | corrigé : {d['attendu']} | obtenu : {d['obtenu']}")
    print("\n===== CORPUS : APPRÉCIATIONS SUR TEXTE INTÉGRAL (licence CC BY ou CC0, passages cités avec leur source) =====")
    for x in lignes:
        if "integral" in x:
            afficher_appreciation(f"PMID {x['pmid']} — {x['reference']} — corrigé : {x['attendu']}",
                                  x["integral"]["appreciation"], x["integral"]["bilan"])
    print("\n===== PUBLICATIONS RÉELLES DE 2026-S45 : PLAN D'ÉTUDE =====")
    for f in fiches_s45:
        afficher_plan(f"PMID {f['pmid']}, {f['pmcid']}, licence {f['licence']}, {f['type']} — {f['titre'][:110]}",
                      f["plan_etude"], f["bilan_plan"])
    print("\n===== PUBLICATIONS RÉELLES DE 2026-S45 : APPRÉCIATION SUR TEXTE INTÉGRAL =====")
    for f in fiches_s45:
        afficher_appreciation(f"PMID {f['pmid']}, {f['pmcid']}, licence {f['licence']}, {f['type']} — {f['titre'][:110]}",
                              f["appreciation"], f["bilan"])
    if classes:
        print("\n===== PUBLICATIONS RÉELLES DE 2026-S45 : CATÉGORIE D'IMPORTANCE (résumé seul) =====")
        for c in classes:
            k = c["classement"]
            if k is None:
                print(f"  PMID {c['pmid']} | illisible : {c['bilan']['ecarts']}")
                continue
            print(f"  PMID {c['pmid']} | {c['type']} | catégorie {k['categorie']} ({k['libelle']}) | sens : {k['sens_pratique']} | "
                  f"verdict actuel : {c['verdict_actuel']} | {c['titre'][:90]}\n      {k['justification_categorie']}"
                  + (f"\n      mise en avant : {json.dumps(k['mise_en_avant'], ensure_ascii=False)}" if k["mise_en_avant"] else "")
                  + (f"\n      écarts : {c['bilan']['ecarts']}" if c["bilan"]["ecarts"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
