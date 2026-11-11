"""Assemble les cas « sens de l'effet » du corpus de référence.

Le corpus de référence sert à mesurer la chaîne d'analyse : on compare ce que l'IA produit à des
corrigés établis par des humains. Ces cas-ci viennent du jeu de données Evidence Inference
(Lehman et al., 2019 ; DeYoung et al., 2020), publié sous licence MIT :
https://github.com/jayded/evidence-inference

Pour un essai randomisé et une question « intervention contre comparateur, sur tel critère », des
médecins ont noté si le critère a augmenté, diminué ou n'a pas changé de façon significative, et
cité le passage qui le montre.

Ce script ne garde que des identifiants, les questions, les corrigés et de courts passages, pour
des articles sous licence CC BY ou CC0. Il ne copie jamais le texte d'un article.

Usage :
    python banc/assembler_essais.py --nombre 8 --sortie corpus-essais.json
    python banc/assembler_essais.py --dossier chemin/local   (fichiers CSV déjà téléchargés)

Le téléchargement demande un accès au réseau. Aucune IA n'est appelée : aucun coût.
"""
import argparse
import collections
import csv
import io
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/jayded/evidence-inference/master/annotations/"
FICHIER_QUESTIONS = "prompts_merged.csv"
FICHIER_CORRIGES = "annotations_merged.csv"
LICENCES_ADMISES = ("CC BY", "CC0")
LIBELLES = {"1": "augmentation significative", "-1": "diminution significative", "0": "pas de différence significative"}

# Rééducation et réadaptation, au sens large : le cahier des charges demande une attention
# particulière à ces domaines.
MOTS_CLES = (
    "physiotherap", "physical therap", "rehabilitat", "exercise", "training", "strength",
    "stretch", "balance", "gait", "walking", "mobili", "manual therap", "massage", "taping",
    "electrical stimulation", "tens", "pelvic floor", "pulmonary rehab", "aerobic", "resistance",
)
PASSAGE_MAX = 600


def _cle(nom):
    return re.sub(r"[^a-z]", "", (nom or "").lower())


def lire_csv(texte):
    """Lit un CSV en normalisant les noms de colonnes (minuscules, sans espaces)."""
    csv.field_size_limit(sys.maxsize)
    lignes = csv.DictReader(io.StringIO(texte))
    return [{_cle(k): (v or "").strip() for k, v in ligne.items() if k} for ligne in lignes]


def _valeur(ligne, *noms):
    for nom in noms:
        if nom in ligne:
            return ligne[nom]
    return ""


def pertinent(question):
    texte = " ".join((question.get("intervention", ""), question.get("comparator", ""),
                      question.get("outcome", ""))).lower()
    return any(re.search(rf"\b{re.escape(mot)}", texte) for mot in MOTS_CLES)


def candidats(questions, corriges):
    """Regroupe par article les questions pertinentes dont le corrigé est valide et sans désaccord."""
    par_question = collections.defaultdict(list)
    for c in corriges:
        if _valeur(c, "validlabel") not in ("1", "1.0", "True", "true"):
            continue
        if "validreasoning" in c and c["validreasoning"] not in ("1", "1.0", "True", "true"):
            continue
        code = _valeur(c, "labelcode")
        code = {"1.0": "1", "-1.0": "-1", "0.0": "0"}.get(code, code)
        if code not in LIBELLES:
            continue
        par_question[c.get("promptid", "")].append({**c, "labelcode": code})

    par_article = collections.defaultdict(list)
    for q in questions:
        lignes = par_question.get(q.get("promptid", ""))
        if not lignes or not pertinent(q):
            continue
        codes = {ligne["labelcode"] for ligne in lignes}
        if len(codes) != 1:            # désaccord entre annotateurs : la question est écartée
            continue
        passages = []
        for ligne in lignes:
            passage = _valeur(ligne, "annotations").strip()
            if len(passage) >= 40 and passage[:PASSAGE_MAX] not in passages:
                passages.append(passage[:PASSAGE_MAX])
        if not passages:
            continue
        code = codes.pop()
        par_article[q.get("pmcid", "")].append({
            "id": q.get("promptid", ""),
            "intervention": q.get("intervention", ""),
            "comparateur": q.get("comparator", ""),
            "critere": q.get("outcome", ""),
            "corrige": {"code": int(code), "libelle": LIBELLES[code]},
            "passages": passages[:2],
            "annotateurs": len({_valeur(ligne, "userid") for ligne in lignes}),
            "dans_le_resume": all(_valeur(ligne, "inabstract") in ("1", "1.0", "True", "true") for ligne in lignes),
        })
    return {pmcid: qs for pmcid, qs in par_article.items() if pmcid and len(qs) >= 2}


def dominante(questions):
    return collections.Counter(q["corrige"]["code"] for q in questions).most_common(1)[0][0]


def choisir(par_article, nombre, licence_de):
    """Choix déterministe : les articles les plus riches d'abord, en variant le sens des corrigés."""
    plafond = math.ceil(nombre / 2)
    compte = collections.Counter()
    retenus = []
    ordre = sorted(par_article.items(), key=lambda kv: (-len(kv[1]), int(re.sub(r"\D", "", kv[0]) or 0)))
    for pmcid, questions in ordre:
        if len(retenus) >= nombre:
            break
        d = dominante(questions)
        if compte[d] >= plafond:
            continue
        infos = licence_de(pmcid)
        if not infos or infos.get("licence") not in LICENCES_ADMISES or infos.get("retracte"):
            continue
        compte[d] += 1
        retenus.append({"pmcid": f"PMC{re.sub(r'[^0-9]', '', pmcid)}", **infos, "questions": questions[:4]})
    return retenus


# --- Réseau -----------------------------------------------------------------------------------

def telecharger(url):
    import requests
    for essai in range(4):
        try:
            rep = requests.get(url, timeout=120, headers={"User-Agent": "veille-sante-banc/1.0"})
            if rep.status_code == 200:
                return rep.text
        except requests.RequestException:
            pass
        time.sleep(2 * (essai + 1))
    raise RuntimeError(f"Téléchargement impossible : {url}")


def licence_pmc(pmcid):
    """Licence, référence et PMID d'un article de PubMed Central (service « OA » du NCBI)."""
    numero = re.sub(r"[^0-9]", "", pmcid)
    try:
        xml = telecharger(f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC{numero}")
    except RuntimeError:
        return None
    m = re.search(r"<record\b([^>]*)>", xml)
    if not m:
        return None
    attributs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
    infos = {"licence": attributs.get("license", ""), "reference": attributs.get("citation", ""),
             "retracte": attributs.get("retracted", "no") == "yes", "pmid": ""}
    try:
        conv = json.loads(telecharger(
            f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=PMC{numero}&format=json&tool=veille-sante"))
        infos["pmid"] = str((conv.get("records") or [{}])[0].get("pmid", ""))
    except (RuntimeError, ValueError):
        pass
    time.sleep(0.4)
    return infos


# --- Programme --------------------------------------------------------------------------------

def assembler(questions_csv, corriges_csv, nombre, licence_de):
    questions, corriges = lire_csv(questions_csv), lire_csv(corriges_csv)
    par_article = candidats(questions, corriges)
    cas = choisir(par_article, nombre, licence_de)
    return {
        "nom": "Corpus de référence — essais randomisés, sens de l'effet",
        "source": "Evidence Inference (Lehman et al., 2019 ; DeYoung et al., 2020), licence MIT",
        "source_url": "https://github.com/jayded/evidence-inference",
        "assemble_le": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "regles": "Questions pertinentes pour la rééducation, corrigé validé et sans désaccord, "
                  "au moins deux questions par article, article sous licence CC BY ou CC0.",
        "comptes": {"questions": len(questions), "corriges": len(corriges),
                    "articles_candidats": len(par_article), "articles_retenus": len(cas)},
        "cas": cas,
    }, par_article


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--nombre", type=int, default=8)
    p.add_argument("--sortie", default="corpus-essais.json")
    p.add_argument("--dossier", help="dossier local contenant les deux fichiers CSV (sans réseau)")
    args = p.parse_args(argv)

    if args.dossier:
        lire = lambda nom: (Path(args.dossier) / nom).read_text(encoding="utf-8")
    else:
        lire = lambda nom: telecharger(SOURCE + nom)
    corpus, par_article = assembler(lire(FICHIER_QUESTIONS), lire(FICHIER_CORRIGES), args.nombre, licence_pmc)

    print("Comptes :", json.dumps(corpus["comptes"], ensure_ascii=False))
    print("Articles candidats les plus riches :")
    for pmcid, qs in sorted(par_article.items(), key=lambda kv: -len(kv[1]))[:25]:
        sens = collections.Counter(q["corrige"]["libelle"] for q in qs)
        print(f"  PMC{pmcid} | {len(qs)} questions | {dict(sens)} | {qs[0]['intervention'][:70]}")
    print("Articles retenus :")
    for c in corpus["cas"]:
        print(f"  {c['pmcid']} | PMID {c['pmid']} | {c['licence']} | {len(c['questions'])} questions | {c['reference'][:80]}")

    Path(args.sortie).write_text(json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8")
    print("=====DEBUT_CORPUS=====")
    print(json.dumps(corpus, ensure_ascii=False))
    print("=====FIN_CORPUS=====")
    return 0 if corpus["cas"] else 1


if __name__ == "__main__":
    sys.exit(main())
