"""Repère, dans des revues en accès libre, les tableaux d'évaluation de la qualité des études.

Le corpus de référence a besoin de corrigés « qualité méthodologique » : des jugements déjà portés
par les auteurs d'une revue sur chaque étude incluse (RoB 2 pour les essais, AMSTAR 2 pour les
revues, QUADAS-2 pour les études diagnostiques, AGREE II pour les recommandations).

Pour chaque revue candidate, ce script :
1. lit sa licence et son identifiant PubMed Central dans Europe PMC, et écarte ce qui n'est pas
   sous licence CC BY ou CC0 ;
2. télécharge son texte intégral au format XML et repère les tableaux qui portent ces jugements ;
3. remplace chaque renvoi bibliographique d'un tableau par l'identifiant PubMed de l'étude citée ;
4. écrit un extrait compact dans le journal, pour choisir les corrigés à la main.

Il n'enregistre aucun texte d'article. Aucune IA n'est appelée : aucun coût.

Usage : python banc/extraire_tableaux.py banc/candidats_qualite.json
"""
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
LICENCES_ADMISES = ("CC BY", "CC0")
MOTS = {
    "rob2": ("some concerns", "low risk", "high risk", "randomi", "deviation", "overall", "missing outcome"),
    "amstar2": ("amstar", "critically low", "confidence", "moderate", "high", "low"),
    "quadas2": ("quadas", "patient selection", "index test", "reference standard", "flow and timing", "applicability"),
    "agree2": ("agree", "scope", "rigour", "rigor", "stakeholder", "applicability", "editorial", "clarity"),
}
LIGNES_MAX = 30
CELLULE_MAX = 45


def telecharger(url, essais=3, delai=60):
    import requests
    for essai in range(essais):
        try:
            rep = requests.get(url, timeout=delai, headers={"User-Agent": "veille-sante-banc/1.0"})
            if rep.status_code == 200:
                return rep.text
            if rep.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * (essai + 1))
    return None


def normaliser_licence(brute):
    l = (brute or "").upper().replace("-", " ").strip()
    if l.startswith("CC0"):
        return "CC0"
    if l in ("CC BY", "CC BY 4.0", "CC BY 3.0"):
        return "CC BY"
    return l or "inconnue"


def decrire(pmids):
    """PMCID, licence et titre de chaque PMID, lus par paquets dans Europe PMC."""
    infos = {}
    for i in range(0, len(pmids), 20):
        lot = pmids[i:i + 20]
        requete = "(" + " OR ".join(f"EXT_ID:{p}" for p in lot) + ") AND SRC:MED"
        texte = telecharger(f"{API}search?format=json&resultType=core&pageSize=100&query={quote(requete)}")
        for r in (json.loads(texte).get("resultList", {}).get("result", []) if texte else []):
            infos[str(r.get("pmid", ""))] = {
                "pmcid": r.get("pmcid", ""),
                "licence": normaliser_licence(r.get("license")),
                "titre": r.get("title", ""),
                "revue": ((r.get("journalInfo") or {}).get("journal") or {}).get("title", ""),
                "annee": r.get("pubYear", ""),
                "doi": r.get("doi", ""),
            }
        time.sleep(0.3)
    return infos


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _texte(element, pmid_de):
    """Texte d'un élément, avec chaque renvoi bibliographique remplacé par [PMID …]."""
    morceaux = [element.text or ""]
    for enfant in element:
        if _local(enfant.tag) == "xref" and enfant.get("ref-type") == "bibr":
            cibles = [pmid_de.get(r, "") for r in (enfant.get("rid") or "").split()]
            cibles = [c for c in cibles if c]
            morceaux.append(f"{''.join(enfant.itertext())}[PMID {','.join(cibles)}]" if cibles
                            else "".join(enfant.itertext()))
        else:
            morceaux.append(_texte(enfant, pmid_de))
        morceaux.append(enfant.tail or "")
    return re.sub(r"\s+", " ", "".join(morceaux)).strip()


def references(racine):
    """Identifiant XML d'une référence → PMID de l'étude citée."""
    pmid_de = {}
    for ref in racine.iter():
        if _local(ref.tag) != "ref" or not ref.get("id"):
            continue
        for pid in ref.iter():
            if _local(pid.tag) == "pub-id" and pid.get("pub-id-type") == "pmid" and (pid.text or "").strip():
                pmid_de[ref.get("id")] = pid.text.strip()
                break
    return pmid_de


def tableaux(racine, outil):
    pmid_de = references(racine)
    trouves = []
    for tw in racine.iter():
        if _local(tw.tag) != "table-wrap":
            continue
        label = caption = ""
        lignes = []
        for el in tw.iter():
            nom = _local(el.tag)
            if nom == "label" and not label:
                label = "".join(el.itertext()).strip()
            elif nom == "caption" and not caption:
                caption = re.sub(r"\s+", " ", "".join(el.itertext())).strip()
            elif nom == "tr":
                cellules = [_texte(c, pmid_de) for c in el if _local(c.tag) in ("td", "th")]
                if any(cellules):
                    lignes.append(cellules)
        contenu = (caption + " " + " ".join(" ".join(l) for l in lignes)).lower()
        score = sum(contenu.count(m) for m in MOTS[outil])
        if score:
            trouves.append({"label": label, "caption": caption[:200], "lignes": lignes, "score": score})
    trouves.sort(key=lambda t: -t["score"])
    figures = []
    for fig in racine.iter():
        if _local(fig.tag) == "fig":
            cap = re.sub(r"\s+", " ", "".join(fig.itertext())).strip()
            if re.search(r"risk of bias|amstar|quadas|agree", cap, re.I):
                figures.append(cap[:160])
    return trouves[:2], figures[:3], len(pmid_de)


def main(chemin):
    groupes = json.load(open(chemin, encoding="utf-8"))
    for outil, pmids in groupes.items():
        if outil not in MOTS:
            continue
        print(f"\n##### {outil.upper()} — {len(pmids)} revues candidates", flush=True)
        infos = decrire([str(p) for p in pmids])
        for pmid in pmids:
            i = infos.get(str(pmid))
            if not i:
                print(f"\n=== PMID {pmid} : introuvable dans Europe PMC", flush=True)
                continue
            entete = f"\n=== PMID {pmid} | {i['pmcid'] or 'sans PMCID'} | {i['licence']} | {i['revue']} {i['annee']}\n    {i['titre'][:150]}"
            if i["licence"] not in LICENCES_ADMISES or not i["pmcid"]:
                print(entete + "\n    écartée : licence ou texte intégral indisponible", flush=True)
                continue
            xml = telecharger(f"{API}{i['pmcid']}/fullTextXML")
            if not xml:
                print(entete + "\n    écartée : texte intégral introuvable", flush=True)
                continue
            try:
                racine = ET.fromstring(xml)
            except ET.ParseError as e:
                print(entete + f"\n    écartée : XML illisible ({e})", flush=True)
                continue
            trouves, figures, nb_refs = tableaux(racine, outil)
            print(entete + f"\n    références avec PMID : {nb_refs}", flush=True)
            for f in figures:
                print(f"    figure : {f}")
            if not trouves:
                print("    aucun tableau d'évaluation repéré")
            for t in trouves:
                print(f"    --- {t['label']} (score {t['score']}) : {t['caption']}")
                for ligne in t["lignes"][:LIGNES_MAX]:
                    print("      | " + " | ".join(c[:CELLULE_MAX] for c in ligne))
                if len(t["lignes"]) > LIGNES_MAX:
                    print(f"      … {len(t['lignes']) - LIGNES_MAX} lignes de plus")
            sys.stdout.flush()
            time.sleep(0.5)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
