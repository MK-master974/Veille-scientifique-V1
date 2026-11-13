"""Étude, sans IA et sans coût, des protocoles et des suppléments des articles du corpus (VS-D49).

Phase 1, séance 7. Rien n'est publié et la veille hebdomadaire n'est pas concernée.

Question : pour les revues sous licence CC BY du corpus « qualité », les critères d'AMSTAR 2 qui
pèsent le plus (protocole, liste des études exclues, recherche complète) se jugent-ils hors du corps
de l'article, et que faudrait-il aller chercher ? Pour chaque article lu en entier, ce banc mesure :
- le nombre d'éléments « matériel supplémentaire » déclarés dans le fichier de l'article, et leurs
  extensions de fichier ;
- les familles de numéros de protocole ou de registre cités dans le texte (PROSPERO, ClinicalTrials.gov,
  ISRCTN, DRKS, ChiCTR, ANZCTR, CTRI, OSF, INPLASY) ;
- le nombre de mentions de fichiers supplémentaires, de listes d'études exclues et de protocole ;
- l'existence d'un paquet de fichiers supplémentaires chez Europe PMC, et sa taille annoncée.

Aucun texte d'article n'est gardé ni écrit : seules des mesures le sont, et aucun numéro de
registre n'est recopié. Aucun accès payant, aucune authentification n'est contourné.

Usage : python banc/supplements.py --sortie resultats
"""
import argparse
import collections
import importlib.util
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from pipeline import acces  # noqa: E402
from pipeline.reseau import requete  # noqa: E402

_spec = importlib.util.spec_from_file_location("banc_appreciation", RACINE / "banc" / "banc_appreciation.py")
banc_appreciation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(banc_appreciation)

XLINK = "{http://www.w3.org/1999/xlink}href"
REGISTRES = {
    "PROSPERO": r"CRD\d{8,14}", "ClinicalTrials.gov": r"NCT\d{8}", "ISRCTN": r"ISRCTN\d{8}", "DRKS": r"DRKS\d{8}",
    "ChiCTR": r"ChiCTR[-A-Za-z0-9]+", "ANZCTR": r"ACTRN\d{14}", "CTRI": r"CTRI/\d{4}/\d{2,3}/\d+",
    "OSF": r"osf\.io/[a-z0-9]{4,6}", "INPLASY": r"INPLASY\d+"}
MENTIONS = {
    "fichier_supplementaire": r"additional files?|supplementary (?:material|files?|data|tables?|figures?|information)|"
                              r"supporting information|appendix|appendices|\bS\d+ (?:file|table|fig)",
    "liste_des_exclus": r"excluded studies|list of excluded|studies excluded|reasons? for exclusion|full-text exclusions?",
    "protocole": r"protocol"}


def analyser(xml_txt):
    """Mesures d'un texte intégral au format JATS. Renvoie None si le XML est illisible."""
    try:
        racine = ET.fromstring(xml_txt)
    except (ET.ParseError, TypeError, ValueError):
        return None
    elements = [e for e in racine.iter() if e.tag.rsplit("}", 1)[-1] == "supplementary-material"]
    extensions = collections.Counter()
    for e in elements:
        liens = [e.get(XLINK)] + [f.get(XLINK) for f in e.iter() if f is not e]
        for lien in (x for x in liens if x):
            extensions[lien.rsplit(".", 1)[-1].lower()[:6] if "." in lien else "sans"] += 1
    texte = " ".join(racine.itertext())
    return {"elements_supplementaires": len(elements), "extensions": dict(extensions),
            "registres": {nom: len(set(re.findall(motif, texte))) for nom, motif in REGISTRES.items()
                          if re.search(motif, texte)},
            "mentions": {nom: len(re.findall(motif, texte, re.I)) for nom, motif in MENTIONS.items()}}


def paquet_europe_pmc(pmcid):
    """Existence et taille annoncée du paquet de fichiers supplémentaires chez Europe PMC, sans le télécharger."""
    try:
        rep = requete("GET", f"{acces.EUROPE_PMC}/{pmcid}/supplementaryFiles", tentatives=2, timeout=30, stream=True)
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else None
        return {"present": False, "code": code}
    except (requests.RequestException, RuntimeError):
        return {"present": None, "code": None}
    try:
        taille = rep.headers.get("Content-Length")
        return {"present": rep.status_code == 200, "code": rep.status_code,
                "octets": int(taille) if taille and taille.isdigit() else None}
    finally:
        rep.close()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sortie", default="resultats-banc")
    p.add_argument("--budget", type=float, default=0.0, help="ignoré : cette étude n'appelle pas l'IA")
    args = p.parse_args(argv)
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    journal = lambda m: print(m, flush=True)   # noqa: E731

    cas = banc_appreciation.charger_cas()
    infos, echecs = acces.decrire_europe_pmc([c["pmid"] for c in cas], journal)
    journal(f"{len(cas)} articles du corpus « qualité » ; paquets Europe PMC en échec : {echecs}")
    lignes = []
    for c in sorted(cas, key=lambda c: (c["outil"], c["pmid"])):
        info = infos.get(c["pmid"], {})
        pmcid, licence = info.get("pmcid", ""), info.get("licence", "inconnue")
        ligne = {"pmid": c["pmid"], "outil": c["outil"], "pmcid": pmcid or None, "licence": licence, "lu": False}
        if pmcid and licence in acces.PERIMETRE_RETENU:
            xml, etat = acces.texte_integral_xml(pmcid)
            mesures = analyser(xml) if xml else None
            if mesures:
                ligne.update({"lu": True, **mesures, "paquet_europe_pmc": paquet_europe_pmc(pmcid)})
            time.sleep(0.3)
        lignes.append(ligne)
        journal("  " + f"PMID {c['pmid']} ({c['outil']}) | {pmcid or 'pas de version PMC'} | licence {licence}"
                + (f" | éléments supplémentaires : {ligne['elements_supplementaires']} | registres : "
                   f"{', '.join(ligne['registres']) or 'aucun'} | paquet Europe PMC : "
                   f"{ligne['paquet_europe_pmc']['present']} | liste des exclus citée : "
                   f"{ligne['mentions']['liste_des_exclus']} fois" if ligne["lu"] else ""))

    def stats(xs):
        lus = [x for x in xs if x["lu"]]
        return {"articles": len(xs), "lus_en_entier": len(lus),
                "avec_element_supplementaire": sum(1 for x in lus if x["elements_supplementaires"]),
                "avec_paquet_europe_pmc": sum(1 for x in lus if x["paquet_europe_pmc"]["present"]),
                "avec_numero_de_registre_ou_de_protocole": sum(1 for x in lus if x["registres"]),
                "citent_une_liste_des_exclus": sum(1 for x in lus if x["mentions"]["liste_des_exclus"]),
                "citent_un_fichier_supplementaire": sum(1 for x in lus if x["mentions"]["fichier_supplementaire"]),
                "extensions": dict(collections.Counter(e for x in lus for e in x["extensions"])),
                "familles_de_registre": dict(collections.Counter(f for x in lus for f in x["registres"]))}

    resume = {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "cout_usd": 0,
              "par_outil": {o: stats([x for x in lignes if x["outil"] == o]) for o in sorted({x["outil"] for x in lignes})}}
    (sortie / "resultats-supplements.json").write_text(
        json.dumps({"resume": resume, "articles": lignes}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n===== RÉSUMÉ =====")
    print(json.dumps(resume, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
