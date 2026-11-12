"""Mesure des niveaux d'accès documentaire sur une semaine déjà publiée.

Pour chaque fiche de la semaine, cherche si le texte intégral de l'article est accessible
légalement (PubMed Central, par Europe PMC), sous quelle licence, et si ce texte est complet.
Compte ensuite la part des fiches qui pourraient atteindre le niveau 1 (« texte intégral lu »)
selon trois périmètres de licences.

Aucune IA n'est appelée : aucun coût. Rien n'est publié. Le texte des articles n'est jamais
gardé : seules des mesures de leur structure le sont.

Usage :
  python banc/mesure_acces.py --semaine 2026-S45 --sortie resultats
  python banc/mesure_acces.py --ref origin/main --sortie resultats   (semaine du fichier de demande)
"""
import argparse
import collections
import json
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from pipeline import acces  # noqa: E402
from pipeline.config import charger_config  # noqa: E402

DEMANDES = RACINE / "banc" / "mesures_acces.json"
NOMS_ETATS = {"ok": "texte reçu", "absent": "texte non diffusé", "echec": "panne",
              "illisible": "texte illisible", "non_demande": "non demandé",
              "non_mesure": "non mesuré, faute de temps"}
NOMS_PERIMETRES = {
    "strict": "A. CC BY et CC0 seulement",
    "intermediaire": "B. A, plus les licences « pas d'usage commercial » et « partage à l'identique »",
    "large": "C. B, plus les licences « pas de modification »",
}


# --- Lecture des données publiées -------------------------------------------------------------

def lire_fichier(chemin, ref=None):
    """Lit un fichier du dépôt, dans le dossier de travail ou à une référence Git donnée."""
    if ref:
        return subprocess.run(["git", "show", f"{ref}:{chemin}"], cwd=RACINE, check=True,
                              capture_output=True, text=True).stdout
    return (RACINE / chemin).read_text(encoding="utf-8")


def choisir_semaine(demandee, ref=None):
    """Semaine à mesurer : celle demandée, sinon la dernière du fichier de demandes."""
    semaine = (demandee or "").strip()
    if not semaine and DEMANDES.exists():
        mesures = json.loads(DEMANDES.read_text(encoding="utf-8")).get("mesures") or []
        semaine = mesures[-1]["semaine"] if mesures else ""
    if not semaine:
        semaine = json.loads(lire_fichier("site/data/index.json", ref))["derniere"]
    if not re.fullmatch(r"\d{4}-S\d{2}", semaine):
        raise SystemExit(f"Semaine invalide : {semaine!r} (attendu : AAAA-Sxx)")
    return semaine


# --- Mesure -----------------------------------------------------------------------------------

def mesurer(fiches, cfg, journal=print, pause=0.3, duree_max=None):
    """Une ligne de mesure par fiche. N'appelle que des sources ouvertes.

    Au-delà de duree_max secondes, les textes restants ne sont plus demandés : ils sont notés
    « non mesuré », pour que la mesure rende toujours un résultat.
    """
    debut = time.monotonic()
    pmids = [f["pmid"] for f in fiches if f.get("pmid")]
    journal(f"Europe PMC : description de {len(pmids)} publications…")
    europe, echecs_europe = acces.decrire_europe_pmc(pmids, journal)
    journal(f"PubMed : identifiants PMC de {len(pmids)} publications…")
    pubmed, echecs_pubmed = acces.pmcids_pubmed(pmids, cfg, journal)

    lignes = []
    a_lire = [f for f in fiches if europe.get(f.get("pmid", ""), {}).get("pmcid")]
    journal(f"Europe PMC : texte intégral demandé pour {len(a_lire)} publications…")
    textes = {}
    for n, f in enumerate(a_lire, 1):
        if duree_max and time.monotonic() - debut > duree_max:
            journal(f"  durée maximale atteinte : {len(a_lire) - n + 1} textes non mesurés")
            for reste in a_lire[n - 1:]:
                textes[reste["pmid"]] = (None, "non_mesure")
            break
        pmcid = europe[f["pmid"]]["pmcid"]
        xml, etat = acces.texte_integral_xml(pmcid)
        textes[f["pmid"]] = (acces.decrire_texte(xml) if xml else None, etat)
        if n % 25 == 0:
            compte = collections.Counter(e for _, e in textes.values())
            journal(f"  {n} sur {len(a_lire)} : {dict(compte)}, {int(time.monotonic() - debut)} s")
        time.sleep(pause)

    for f in fiches:
        pmid = f.get("pmid", "")
        e = europe.get(pmid, {})
        texte, etat = textes.get(pmid, (None, "non_demande"))
        if etat == "ok" and texte is None:
            etat = "illisible"
        lignes.append({
            "id": f["id"], "pmid": pmid, "type": f.get("type", ""),
            "kine": any(d.startswith("kine/") for d in f.get("domaines", [])),
            "decrit_europe": pmid in europe,
            "pmcid_europe": e.get("pmcid", ""), "pmcid_pubmed": pubmed.get(pmid, ""),
            "licence": e.get("licence", "inconnue"), "acces_ouvert": e.get("acces_ouvert"),
            "etat_texte": etat, "texte": texte,
        })
    champs = sorted({c for e in europe.values() for c in e.get("champs", [])})
    return lignes, {"echecs_europe": echecs_europe, "echecs_pubmed": echecs_pubmed, "champs_europe": champs}


# --- Résumé -----------------------------------------------------------------------------------

def _niveaux(lignes, perimetre):
    compte = collections.Counter()
    for l in lignes:
        niveau, _ = acces.niveau_acces(l["pmcid_europe"], l["licence"], l["texte"], perimetre)
        compte[niveau] += 1
    return {str(n): compte.get(n, 0) for n in (1, 2, 3)}


def resumer(lignes, prix_entree_par_million=None):
    """Compte les niveaux d'accès par périmètre de licences. Fonction pure, testée sans réseau."""
    kine = [l for l in lignes if l["kine"]]
    avec_pmc = [l for l in lignes if l["pmcid_europe"]]
    resume = {
        "fiches": len(lignes),
        "fiches_kine": len(kine),
        "decrites_europe": sum(1 for l in lignes if l["decrit_europe"]),
        "pmc_europe": len(avec_pmc),
        "pmc_pubmed": sum(1 for l in lignes if l["pmcid_pubmed"]),
        "pmc_pubmed_seul": sum(1 for l in lignes if l["pmcid_pubmed"] and not l["pmcid_europe"]),
        "pmc_europe_seul": sum(1 for l in lignes if l["pmcid_europe"] and not l["pmcid_pubmed"]),
        "licences": dict(collections.Counter(l["licence"] for l in avec_pmc).most_common()),
        "etats_texte": dict(collections.Counter(l["etat_texte"] for l in avec_pmc).most_common()),
        "perimetres": {}, "par_type": {},
    }
    for nom, licences in acces.PERIMETRES.items():
        resume["perimetres"][nom] = {"toutes": _niveaux(lignes, licences), "kine": _niveaux(kine, licences)}
    for t in sorted({l["type"] for l in lignes}):
        du_type = [l for l in lignes if l["type"] == t]
        resume["par_type"][t] = {"fiches": len(du_type),
                                 "strict": _niveaux(du_type, acces.PERIMETRES["strict"])["1"],
                                 "large": _niveaux(du_type, acces.PERIMETRES["large"])["1"]}
    lisibles = [l for l in lignes
                if acces.niveau_acces(l["pmcid_europe"], l["licence"], l["texte"], acces.PERIMETRES["large"])[0] == 1]
    tailles = sorted(l["texte"]["caracteres"] for l in lisibles)
    if tailles:
        jetons = sum(max(1, t // 3) for t in tailles)  # même règle que pipeline/ia.py
        resume["textes"] = {
            "nombre": len(tailles), "mediane": int(statistics.median(tailles)),
            "neuvieme_decile": tailles[min(len(tailles) - 1, int(len(tailles) * 0.9))],
            "maximum": tailles[-1], "total": sum(tailles), "jetons_estimes": jetons,
            "avec_methode_et_resultats": sum(1 for l in lisibles if l["texte"]["methode"] and l["texte"]["resultats"]),
            "avec_tableaux": sum(1 for l in lisibles if l["texte"]["tableaux"]),
        }
        if prix_entree_par_million:
            resume["textes"]["cout_entree_usd"] = round(jetons / 1e6 * prix_entree_par_million, 2)
    return resume


# --- Rapport ----------------------------------------------------------------------------------

def _part(n, total):
    return f"{n} ({round(100 * n / total)} %)" if total else "0"


def _nb(n):
    return f"{n:,}".replace(",", " ")


def rapport(resume, contexte):
    """Rapport en Markdown, lisible par un non-développeur."""
    r, n, nk = resume, resume["fiches"], resume["fiches_kine"]
    lignes = [
        f"# Niveaux d'accès — semaine {contexte['semaine']}",
        "",
        f"Mesure du {contexte['mesure_le']}, sur les {n} fiches publiées de la semaine "
        f"{contexte['semaine']}" + (f", {contexte['delai_jours']} jours après leur publication." if
                                     contexte.get("delai_jours") is not None else "."),
        "Aucune IA n'est appelée : coût nul. Le texte des articles n'est pas gardé.",
        "",
        "## Texte intégral disponible",
        "",
        "| Mesure | Résultat |",
        "| --- | --- |",
        f"| Fiches retrouvées dans Europe PMC | {_part(r['decrites_europe'], n)} |",
        f"| Fiches avec une version dans PubMed Central, selon Europe PMC | {_part(r['pmc_europe'], n)} |",
        f"| Fiches avec une version dans PubMed Central, selon PubMed | {_part(r['pmc_pubmed'], n)} |",
        f"| Version connue de PubMed mais pas encore d'Europe PMC | {r['pmc_pubmed_seul']} |",
        f"| Version connue d'Europe PMC mais pas de PubMed | {r['pmc_europe_seul']} |",
        "",
        "## Licences des versions trouvées",
        "",
        "| Licence déclarée | Fiches |",
        "| --- | --- |",
    ]
    lignes += [f"| {lic} | {_part(nb, r['pmc_europe'])} |" for lic, nb in r["licences"].items()]
    lignes += ["", "Demande du texte intégral à Europe PMC : " +
               ", ".join(f"{NOMS_ETATS.get(etat, etat)} {nb}" for etat, nb in r["etats_texte"].items()) + ".", "",
               "## Part des fiches par niveau d'accès, selon le périmètre de licences", "",
               "Niveau 1 : texte intégral lisible. Niveau 2 : texte partiel. Niveau 3 : résumé uniquement.", "",
               "| Périmètre | Niveau 1 | Niveau 2 | Niveau 3 | Niveau 1, fiches de kinésithérapie |",
               "| --- | --- | --- | --- | --- |"]
    for nom, libelle in NOMS_PERIMETRES.items():
        t, k = r["perimetres"][nom]["toutes"], r["perimetres"][nom]["kine"]
        lignes.append(f"| {libelle} | {_part(t['1'], n)} | {_part(t['2'], n)} | {_part(t['3'], n)} | "
                      f"{_part(k['1'], nk)} sur {nk} |")
    lignes += ["", "## Niveau 1 par type d'étude", "",
               "| Type | Fiches | Niveau 1, périmètre A | Niveau 1, périmètre C |", "| --- | --- | --- | --- |"]
    lignes += [f"| {t} | {v['fiches']} | {_part(v['strict'], v['fiches'])} | {_part(v['large'], v['fiches'])} |"
               for t, v in r["par_type"].items()]
    if r.get("textes"):
        x = r["textes"]
        lignes += ["", "## Taille des textes lisibles (périmètre C)", "",
                   "| Mesure | Résultat |", "| --- | --- |",
                   f"| Textes lisibles | {x['nombre']} |",
                   f"| Avec une partie « méthode » et une partie « résultats » repérées | {x['avec_methode_et_resultats']} |",
                   f"| Avec au moins un tableau | {x['avec_tableaux']} |",
                   f"| Taille médiane | {_nb(x['mediane'])} caractères |",
                   f"| Neuf textes sur dix font moins de | {_nb(x['neuvieme_decile'])} caractères |",
                   f"| Texte le plus long | {_nb(x['maximum'])} caractères |",
                   f"| Volume total, estimé en jetons | {_nb(x['jetons_estimes'])} |"]
        if "cout_entree_usd" in x:
            lignes.append(f"| Coût d'une seule lecture de tous ces textes par le modèle de rédaction actuel, "
                          f"au prix plein, hors réponse | environ {str(x['cout_entree_usd']).replace('.', ',')} $ (estimation) |")
    lignes += ["", "## Limites", "",
               "- La licence est celle que déclare Europe PMC. Elle n'a pas été relue dans chaque article.",
               "- Seul PubMed Central est interrogé. Un texte en accès ouvert ailleurs n'est pas compté.",
               "- Un texte est compté « lisible » s'il a un corps d'au moins "
               f"{_nb(acces.SEUIL_CARACTERES)} caractères et {acces.SEUIL_SECTIONS} parties. Ce seuil est un "
               "point de départ.",
               "- La mesure est faite après la publication de la semaine. Le lundi de la veille, moins "
               "de textes sont déjà déposés."]
    if contexte.get("echecs"):
        lignes.append(f"- Paquets en échec pendant la mesure : {contexte['echecs']}. Les fiches "
                      "concernées sont comptées sans texte intégral.")
    if contexte.get("champs_europe") is not None:
        ok = "isOpenAccess" in contexte["champs_europe"]
        lignes.append("- Champ « accès ouvert » d'Europe PMC : " + ("lu." if ok else "absent des réponses."))
    return "\n".join(lignes) + "\n"


# --- Programme --------------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--semaine", default="", help="semaine publiée à mesurer (AAAA-Sxx)")
    p.add_argument("--ref", default=None, help="référence Git où lire les données publiées (ex. origin/main)")
    p.add_argument("--sortie", default="resultats-acces", help="dossier des résultats")
    p.add_argument("--limite", type=int, default=0, help="ne mesurer que les N premières fiches (essai)")
    p.add_argument("--minutes", type=int, default=45, help="durée maximale de la lecture des textes")
    args = p.parse_args(argv)

    semaine = choisir_semaine(args.semaine, args.ref)
    donnees = json.loads(lire_fichier(f"site/data/semaines/{semaine}.json", args.ref))
    fiches = [f for f in donnees["fiches"] if f.get("source") == "pubmed"]
    if args.limite:
        fiches = fiches[:args.limite]
    cfg = charger_config()
    journal = lambda m: print(m, flush=True)  # noqa: E731

    maintenant = datetime.now(timezone.utc)
    lignes, infos = mesurer(fiches, cfg, journal, duree_max=60 * args.minutes)
    modele = cfg["ia"]["modele_redaction"]
    prix = cfg["ia"]["prix_usd_par_million"].get(modele, [None])[0]
    resume = resumer(lignes, prix)
    delai = None
    if donnees.get("publie_le"):
        delai = (maintenant - datetime.fromisoformat(donnees["publie_le"])).days
    contexte = {"semaine": semaine, "mesure_le": maintenant.strftime("%d/%m/%Y à %H h %M UTC"),
                "delai_jours": delai, "echecs": infos["echecs_europe"] + infos["echecs_pubmed"],
                "champs_europe": infos["champs_europe"]}
    texte = rapport(resume, contexte)

    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / f"mesure-acces-{semaine}.md").write_text(texte, encoding="utf-8")
    (sortie / f"mesure-acces-{semaine}.json").write_text(json.dumps(
        {"contexte": contexte, "resume": resume, "lignes": lignes}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n" + texte, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
