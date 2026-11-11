"""Résumé chiffré d'un dossier de travail du moteur (travail/<semaine>/).

Outil de diagnostic, en lecture seule. Il n'affiche que des comptages et des motifs,
jamais le résumé d'un article. Il sert à comprendre ce que le tri et la rédaction ont
réellement décidé pour une semaine : étiquettes de départ, abaissements par l'IA,
verdicts ramenés par les règles, motifs d'exclusion et de rejet.

Usage : python scripts/resume_travail.py travail/2026-S45
"""
import collections
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from pipeline import regles  # noqa: E402
from pipeline.config import charger_config  # noqa: E402
from pipeline.ia import lire_json  # noqa: E402


def lire(dossier, nom, defaut):
    chemin = dossier / nom
    if not chemin.exists():
        print(f"  (fichier absent : {nom})")
        return defaut
    return json.loads(chemin.read_text(encoding="utf-8"))


def titre(texte):
    print(f"\n=== {texte} ===")


def tableau(compteur, limite=None):
    """Affiche un compteur {clé: nombre}, du plus fréquent au moins fréquent."""
    lignes = sorted(compteur.items(), key=lambda kv: (-kv[1], str(kv[0])))
    for cle, nb in lignes[:limite]:
        cle = " | ".join(str(c) for c in cle) if isinstance(cle, tuple) else str(cle)
        print(f"  {nb:5d}  {cle}")
    if limite and len(lignes) > limite:
        print(f"  ... {len(lignes) - limite} autres lignes")


CATEGORIES_EXCLUSION = (
    ("étude pilote ou de faisabilité", r"pilote|faisabilit|pilot|feasib"),
    ("protocole", r"protocol"),
    ("sans groupe contrôle", r"sans groupe|groupe contr[oô]le|non contr[oô]l|pas de (groupe )?compar"),
    ("effectif insuffisant", r"effectif|moins de 30|< ?30|participants"),
    ("recherche fondamentale ou animale", r"fondamental|animal|in vitro|pr[ée]clinique|cellul"),
    ("organisationnel ou économique", r"organisationnel|[ée]conomi|co[uû]t"),
    ("sans conséquence clinique", r"cons[ée]quence|implication|pertinen|pratique clinique|clinique"),
    ("type d'étude non retenu", r"type d.[ée]tude|non retenu|observationnel|cohorte|transversal|cas-t[ée]moins|narrativ"),
    ("aucun domaine du catalogue", r"aucun domaine|catalogue"),
    ("réponse illisible", r"illisible"),
)


def categorie_exclusion(motif):
    m = (motif or "").lower()
    for nom, motif_re in CATEGORIES_EXCLUSION:
        if re.search(motif_re, m):
            return nom
    return "autre"


def tranche_effectif(valeur):
    n = regles._entier(valeur)
    if n is None:
        return "inconnu"
    if n < 30:
        return "< 30"
    return "30 à 99" if n < 100 else ">= 100"


def resumer(dossier):
    dossier = Path(dossier)
    cfg_preuve = charger_config().get("preuve")
    c = collections.Counter

    titre(f"ÉTAT DU MOTEUR — {dossier.name}")
    etat = lire(dossier, "etat.json", {})
    print("  étape :", etat.get("etape"), "| mise à jour :", etat.get("maj"))
    print("  statistiques :", json.dumps(etat.get("stats", {}), ensure_ascii=False))
    print("  coûts ($) :", json.dumps(etat.get("couts", {}), ensure_ascii=False))
    for nom, lot in (etat.get("lots") or {}).items():
        court = {k: v for k, v in lot.items() if not isinstance(v, (list, dict))}
        print(f"  lot {nom} :", json.dumps(court, ensure_ascii=False))
    print("  journal :")
    for ligne in etat.get("journal", []):
        print("   ", ligne)

    titre("RÉFÉRENCES COLLECTÉES (métadonnées seulement)")
    refs = lire(dossier, "references.json", [])
    print("  total :", len(refs))
    tableau(c(r.get("source") for r in refs))
    print("  types de publication déclarés par la source :")
    tableau(c(t for r in refs for t in r.get("types_publication", [])), 15)
    print("  références sans DOI :", sum(1 for r in refs if not r.get("doi")))

    titre("TRI")
    tris = lire(dossier, "tri.json", {})
    inclus = [t for t in tris.values() if t.get("inclure")]
    exclus = [t for t in tris.values() if not t.get("inclure")]
    print(f"  triées : {len(tris)} | retenues : {len(inclus)} | exclues : {len(exclus)}")
    print("  motifs d'exclusion, par famille (repérage par mots-clés) :")
    tableau(c(categorie_exclusion(t.get("motif_exclusion")) for t in exclus))
    print("  exemples de motifs classés « autre » :")
    for t in [t for t in exclus if categorie_exclusion(t.get("motif_exclusion")) == "autre"][:25]:
        print("    -", (t.get("motif_exclusion") or "")[:150])

    titre("ÉTIQUETTE DE DÉPART (règles fixes), par type d'étude")
    tableau(c((t.get("type_etude"), t.get("etiquette_depart")) for t in inclus))
    print("  pertinence, par type :")
    tableau(c((t.get("type_etude"), f"pertinence {t.get('pertinence')}") for t in inclus))

    titre("CE QUE LE TRI A RELEVÉ DANS LES RÉSUMÉS")
    revues = [t for t in inclus if t.get("type_etude") in ("revue_systematique", "meta_analyse")]
    print(f"  revues et méta-analyses ({len(revues)}) : GRADE relevé | majorité d'essais randomisés")
    tableau(c((f"GRADE {t.get('grade')}", f"majorité ECR {t.get('majorite_essais_randomises')}") for t in revues))
    recos = [t for t in inclus if t.get("type_etude") == "recommandation"]
    print(f"  recommandations ({len(recos)}) : accord d'experts")
    tableau(c(f"accord d'experts {t.get('accord_experts')}" for t in recos))
    essais = [t for t in inclus if t.get("type_etude") == "essai_randomise"]
    print(f"  essais randomisés ({len(essais)}) : effectif relevé")
    tableau(c(tranche_effectif(t.get("effectif")) for t in essais))
    diags = [t for t in inclus if t.get("type_etude") == "etude_diagnostique"]
    print(f"  études diagnostiques ({len(diags)}) : plan relevé | effectif")
    tableau(c((f"plan {t.get('design_diagnostique')}", tranche_effectif(t.get("effectif"))) for t in diags))
    print("  exclusions faites par la règle d'effectif (après réponse du tri) :",
          sum(1 for t in exclus if "effectif inférieur" in (t.get("motif_exclusion") or "")))

    titre("RÉDACTION : CE QUE L'IA A PROPOSÉ, AVANT LES RÈGLES")
    brutes = lire(dossier, "redaction.json", {})
    print("  réponses de rédaction :", len(brutes))
    illisibles = 0
    etiq, abaisse, verdicts, change = c(), c(), c(), c()
    for ident, texte in brutes.items():
        tri = tris.get(ident, {})
        try:
            brut = lire_json(texte)
        except Exception:
            illisibles += 1
            continue
        depart = tri.get("etiquette_depart")
        proposee = brut.get("etiquette")
        if depart not in regles.ETIQUETTES:
            continue
        finale = regles.plafonner_etiquette(proposee, depart)
        etiq[(f"départ {depart}", f"IA {proposee}", f"finale {finale}")] += 1
        if regles.ETIQUETTES.index(finale) < regles.ETIQUETTES.index(depart):
            abaisse[tri.get("type_etude")] += 1
        v_ia = brut.get("verdict")
        v_final = regles.verdict_autorise(v_ia, tri.get("type_etude"), finale)
        verdicts[(f"IA {v_ia}", f"final {v_final}")] += 1
        if v_ia == "change_la_pratique":
            change[(tri.get("type_etude"), f"étiquette finale {finale}", f"verdict final {v_final}")] += 1
    print("  réponses illisibles :", illisibles)
    print("  étiquette : départ | proposée par l'IA | finale")
    tableau(etiq)
    print("  fiches dont l'IA a abaissé l'étiquette, par type :", sum(abaisse.values()))
    tableau(abaisse)
    print("  verdict : proposé par l'IA | après les règles")
    tableau(verdicts)
    print("  détail des « change la pratique » proposés par l'IA :")
    tableau(change)

    titre("CONTRÔLE : FICHES ÉCARTÉES")
    rejets = lire(dossier, "rejets.json", [])
    print("  fiches écartées :", len(rejets))
    print("  par famille de motif :")
    tableau(c(re.split(r"\s*[:(]", m, maxsplit=1)[0].strip()[:70] for r in rejets for m in r.get("motifs", [])))
    print("  par type d'étude :")
    tableau(c(tris.get(r.get("id"), {}).get("type_etude") for r in rejets))
    print("  exemples de motifs :")
    for r in rejets[:40]:
        print("    -", r.get("id"), ":", " ; ".join(r.get("motifs", []))[:200])

    titre("FICHES CONFORMES")
    fiches = lire(dossier, "fiches.json", [])
    print("  total :", len(fiches))
    tableau(c((f.get("type"), f.get("etiquette"), f.get("verdict")) for f in fiches))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    resumer(sys.argv[1])
