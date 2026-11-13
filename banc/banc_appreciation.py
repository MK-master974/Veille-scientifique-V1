"""Banc d'essai de l'appréciation méthodologique et de la catégorie d'importance.

Phase 1, séance 6. Rien n'est publié et la veille hebdomadaire n'est pas concernée.

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

Aucun texte d'article n'est écrit dans le journal ni dans les résultats, hors courts passages
exacts d'articles sous licence CC BY ou CC0, cités avec leur identifiant (VS-D15).

Usage : python banc/banc_appreciation.py --sortie resultats [--budget 1.5] [--s45 10]
                                         [--classement 30] [--limite 0] [--sans-ia]
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

from pipeline import acces, appreciation, classement, ia, texte  # noqa: E402
from pipeline.config import charger_config, charger_consigne  # noqa: E402
from pipeline.extraction import version_consigne  # noqa: E402

_spec = importlib.util.spec_from_file_location("banc_extraction", RACINE / "banc" / "banc_extraction.py")
extraction_banc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(extraction_banc)
chaine = extraction_banc.chaine

CORPUS = RACINE / "banc" / "corpus"
# Seuils fixés par le porteur du projet le 12 novembre 2026 (VS-D39), sur le texte intégral.
SEUIL_UN_CRAN = 0.70
NIVEAUX = ("resume", "integral")
OUTILS_DU_CORPUS = {"RoB 2": "rob2", "QUADAS-2": "quadas2", "AMSTAR 2": "amstar2", "AGREE II": "agree2"}
SORTIE_ESTIMEE = {"resume": 1500, "integral": 4500, "classement": 700}


# --- Fonctions pures, testées sans réseau -----------------------------------------------------

def cle(valeur):
    """« quelques réserves », « très faible » → « quelques_reserves », « tres_faible »."""
    sans = "".join(c for c in unicodedata.normalize("NFD", str(valeur or "")) if unicodedata.category(c) != "Mn")
    return sans.lower().strip().replace(" ", "_")


def charger_cas():
    """Les cas des deux corpus « qualité », à plat. Un article présent deux fois n'est gardé qu'une fois :
    la version « lisible », plus récente, l'emporte."""
    cas = {}
    for nom in ("qualite.json", "qualite_lisible.json"):
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
                                      "source": g["source"]["pmid"]}
    return list(cas.values())


def corrige_global(outil, corrige):
    """Jugement global du corrigé, dans les mots de l'outil. None si le corrigé n'en permet pas."""
    if outil == "amstar2":
        return cle(corrige.get("confiance_globale")) or None
    if outil == "rob2":
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


def domaines_du_corrige(outil, corrige):
    """Corrigé par domaine, avec les clés du module d'appréciation : {clé: valeur}."""
    if outil == "rob2":
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
            "non_evaluables": sum(1 for x in lignes if x["obtenu"] == appreciation.NON_EVALUABLE), "detail": lignes}


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
    print(f"  outil {app['outil']} | jugement de l'outil : {app['jugement_outil']} | qualité : {app['jugement']} | "
          f"étiquette candidate : {app['etiquette']}"
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


# --- Programme --------------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sortie", default="resultats-banc")
    p.add_argument("--budget", type=float, default=1.5, help="plafond en dollars, vérifié avant tout appel")
    p.add_argument("--s45", type=int, default=0, help="publications de 2026-S45 à apprécier sur texte intégral")
    p.add_argument("--classement", type=int, default=0, help="publications de 2026-S45 à classer en plus, sur résumé")
    p.add_argument("--limite", type=int, default=0, help="articles au plus par outil (0 : tous)")
    p.add_argument("--sans-ia", action="store_true", help="lit les textes et estime le coût, sans aucun appel à l'IA")
    args = p.parse_args(argv)
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    journal = lambda m: print(m, flush=True)   # noqa: E731

    cfg = charger_config()
    prix = cfg["ia"]["prix_usd_par_million"]
    modele = cfg["ia"]["modele_redaction"]
    consignes = {"appreciation": charger_consigne("appreciation"), "classement": charger_consigne("classement")}

    # 1. Cas du corpus, limités par outil si demandé : ceux qui ont un texte lisible d'abord
    cas = charger_cas()
    lisibles = {c["pmid"] for g in json.loads((CORPUS / "qualite_lisible.json").read_text(encoding="utf-8"))["groupes"]
                for c in g["cas"]} if (CORPUS / "qualite_lisible.json").exists() else set()
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
    lus = extraction_banc.lire_textes([refs[c["pmid"]] for c in cas], infos)
    for c in cas:
        c["id"] = refs[c["pmid"]]["id"]
        c["doc"] = lus[c["id"]]["doc"]
        journal("  " + extraction_banc.structure(f"{c['id']} ({c['outil']})", lus[c["id"]]))
    journal(f"Texte intégral lu pour {sum(1 for c in cas if c['doc'])} articles sur {len(cas)} "
            f"(paquets Europe PMC en échec : {echecs})")

    # 3. Publications réelles de 2026-S45
    s45, a_classer = [], []
    if args.s45 or args.classement:
        donnees = json.loads((RACINE / "site" / "data" / "semaines" / "2026-S45.json").read_text(encoding="utf-8"))
        kine = [f for f in donnees["fiches"] if f.get("source") == "pubmed"
                and any(d.startswith("kine/") for d in f.get("domaines", []))]
        licences, _ = acces.decrire_europe_pmc([f["pmid"] for f in kine], journal)
        candidates = extraction_banc.choisir_s45(kine, licences, args.s45) if args.s45 else []
        autres = choisir_classement(kine, {f["pmid"] for f in candidates[:args.s45]}, args.classement)
        refs_s45 = {r["pmid"]: r for r in chaine.recuperer_pubmed(
            sorted({f["pmid"] for f in candidates + autres}), cfg)}
        for f in candidates:
            if len(s45) >= args.s45 or f["pmid"] not in refs_s45:
                continue
            ref = refs_s45[f["pmid"]]
            lu = extraction_banc.lire_textes([ref], licences)[ref["id"]]
            if lu["doc"]:
                s45.append({"ref": ref, "fiche": f, **lu})
        a_classer = [{"ref": x["ref"], "fiche": x["fiche"]} for x in s45] + [
            {"ref": refs_s45[f["pmid"]], "fiche": f} for f in autres if f["pmid"] in refs_s45]
        journal(f"2026-S45 : {len(kine)} fiches de kinésithérapie ; {len(s45)} à apprécier sur texte intégral, "
                f"{len(a_classer)} à classer")
        for x in s45:
            journal("  " + extraction_banc.structure(f"{x['ref']['id']} ({x['fiche']['type']})", x))

    # 4. Requêtes et garde-fou budgétaire
    demande = lambda ref, doc, type_etude, etape: appreciation.requete_appreciation(   # noqa: E731
        ref, doc, consignes["appreciation"], type_etude, etape)
    reqs = {
        "resume": [demande(refs[c["pmid"]], texte.document_resume(refs[c["pmid"]]), c["type_etude"], "appreciation-resume")
                   for c in cas],
        "integral": [demande(refs[c["pmid"]], c["doc"], c["type_etude"], "appreciation-integral") for c in cas if c["doc"]],
        "s45": [demande(x["ref"], x["doc"], x["fiche"]["type"], "appreciation-s45") for x in s45],
        "classement": [classement.requete_classement(x["ref"], consignes["classement"], x["fiche"]["type"])
                       for x in a_classer],
    }
    reqs = {k: [r for r in v if r] for k, v in reqs.items()}
    estime = (ia.estimer_cout(reqs["resume"], modele, prix, SORTIE_ESTIMEE["resume"], "direct")
              + ia.estimer_cout(reqs["integral"] + reqs["s45"], modele, prix, SORTIE_ESTIMEE["integral"], "direct")
              + ia.estimer_cout(reqs["classement"], modele, prix, SORTIE_ESTIMEE["classement"], "direct"))
    journal(f"Coût estimé : {estime:.2f} $ (plafond {args.budget:.2f} $) — {len(reqs['resume'])} appréciations sur résumé, "
            f"{len(reqs['integral'])} sur texte intégral, {len(reqs['s45'])} sur 2026-S45, {len(reqs['classement'])} classements")
    if estime > args.budget:
        journal("ARRÊT : estimation supérieure au plafond, aucun appel n'est fait.")
        return 2
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

    def lire(res, etape, ref, doc, type_etude, ouvert):
        reponse, usage = res.get(f"{etape}:{ref['id']}", (None, {}))
        usages[etape.split("-")[-1]].append(usage)
        app, bilan = appreciation.lire_appreciation(reponse, doc, type_etude, publier_passages=ouvert)
        if usage.get("erreur") or usage.get("fin") == "length":
            bilan["refus"].append({"domaine": "réponse", "motif": "réponse illisible : " +
                                   (usage.get("erreur") or "réponse coupée, plafond de sortie atteint")})
        return app, bilan

    # 5. Appréciations du corpus, aux deux niveaux d'accès
    res = {nom: lancer(nom) for nom in ("resume", "integral", "s45", "classement")}
    lignes = []
    for c in cas:
        ref = refs[c["pmid"]]
        attendu = corrige_global(c["outil"], c["corrige"])
        ligne = {"pmid": c["pmid"], "outil": c["outil"], "reference": c["reference"], "attendu": attendu,
                 "texte_integral": bool(c["doc"])}
        for niveau, doc in (("resume", texte.document_resume(ref)), ("integral", c["doc"])):
            if doc is None:
                continue
            app, bilan = lire(res[niveau], f"appreciation-{niveau}", ref, doc, c["type_etude"], niveau == "integral")
            obtenu = app["jugement_outil"] if app else None
            ligne[niveau] = {"obtenu": obtenu, **comparer(c["outil"], obtenu, attendu),
                             "domaines": accord_domaines(c["outil"], app, c["corrige"]),
                             "appreciation": app, "bilan": bilan}
        lignes.append(ligne)

    # 6. Dix publications de 2026-S45 et classements
    fiches_s45 = []
    for x in s45:
        app, bilan = lire(res["s45"], "appreciation-s45", x["ref"], x["doc"], x["fiche"]["type"], True)
        fiches_s45.append({"pmid": x["ref"]["pmid"], "titre": x["ref"]["titre"], "type": x["fiche"]["type"],
                           "pmcid": x["pmcid"], "licence": x["licence"], "appreciation": app, "bilan": bilan})
    classes = []
    for x in a_classer:
        reponse, usage = res["classement"].get(f"classement:{x['ref']['id']}", (None, {}))
        usages["classement"].append(usage)
        c, bilan = classement.lire_classement(reponse, x["ref"])
        classes.append({"pmid": x["ref"]["pmid"], "titre": x["ref"]["titre"], "type": x["fiche"]["type"],
                        "verdict_actuel": x["fiche"].get("verdict"), "etiquette_actuelle": x["fiche"].get("etiquette"),
                        "classement": c, "bilan": bilan})

    # 7. Résumé
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
    resume = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "chaine": {"modele": modele, "effort": cfg["ia"].get("effort_raisonnement"), "mode": "direct",
                   "consigne_appreciation": version_consigne(consignes["appreciation"]),
                   "consigne_classement": version_consigne(consignes["classement"])},
        "cout_usd": {"total": round(sum(cout.values()), 4), **cout,
                     "par_article": {k: round(cout[k] / len(us), 4) for k, us in usages.items() if us}},
        "corpus": {"articles": len(lignes), "avec_texte_integral": len(integral), "absents_de_pubmed": absents},
        "texte_integral": {"etats": repartition(d["etat"] for d in integral),
                           "jugements_obtenus": repartition(d["obtenu"] for d in integral), "par_outil": par_outil},
        "resume_seul": {"etats": repartition(d["etat"] for d in sur_resume),
                        "domaines_non_evaluables": f"{sum(1 for d in domaines_resume if d['jugement'] == appreciation.NON_EVALUABLE)} "
                                                   f"sur {len(domaines_resume)}"},
        "seuils": seuils(integral),
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
    print("\n===== CORPUS : JUGEMENT GLOBAL, OBTENU CONTRE CORRIGÉ =====")
    for x in lignes:
        morceaux = [f"{niveau} : {x[niveau]['obtenu']} → {x[niveau]['etat']}" for niveau in NIVEAUX if niveau in x]
        dom = x.get("integral", x.get("resume", {})).get("domaines", {})
        print(f"  PMID {x['pmid']} | {x['outil']} | corrigé : {x['attendu']} | " + " | ".join(morceaux)
              + (f" | domaines identiques : {dom['identiques']} sur {dom['compares']}" if dom.get("compares") else ""))
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
    print("\n===== PUBLICATIONS RÉELLES DE 2026-S45 : APPRÉCIATION SUR TEXTE INTÉGRAL =====")
    for f in fiches_s45:
        afficher_appreciation(f"PMID {f['pmid']}, {f['pmcid']}, licence {f['licence']}, {f['type']} — {f['titre'][:110]}",
                              f["appreciation"], f["bilan"])
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
