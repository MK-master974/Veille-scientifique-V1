"""Affiche le détail utile d'un résultat du banc d'essai : pièges et réponses non conformes.

Usage : python banc/lire_resultats.py chemin/resultats.json
Aucune IA n'est appelée : aucun coût.
"""
import json
import sys


def court(texte, n=700):
    texte = " ".join(str(texte or "").split())
    return texte if len(texte) <= n else texte[:n] + "…"


def afficher_fiche(fiche):
    s = fiche.get("standard") or {}
    print(f"    étiquette : {fiche.get('etiquette')} | verdict : {fiche.get('verdict')}")
    print(f"    justification : {court(fiche.get('justification_etiquette'), 300)}")
    print(f"    flash : {court(fiche.get('flash'), 400)}")
    print(f"    résultats : {court(s.get('resultats'))}")
    print(f"    impact : {court(s.get('impact_clinique'), 400)}")
    print(f"    limites : {court(' | '.join(s.get('limites') or []), 500)}")


def main(chemin):
    d = json.load(open(chemin, encoding="utf-8"))
    fiches = d.get("fiches", {})
    print("===== PIÈGES =====")
    for p in d.get("pieges", []):
        print(f"  {p['id']} | réussi : {p['reussi']} | {p['constat']}")
    if "fictif-instruction" in fiches:
        print("  Fiche produite pour le résumé fictif :")
        afficher_fiche(fiches["fictif-instruction"])
    print("\n===== RÉPONSES NON CONFORMES (sens de l'effet) =====")
    for e in d.get("effet", []):
        if e["resultat"] in ("sens_inverse", "incorrect", "illisible"):
            print(f"  PMID {e['pmid']} question {e['question']} | corrigé : {e['corrige']} | lu : {e.get('reponse')} | {e['resultat']}")
            print(f"    passage cité par le lecteur : {court(e.get('passage'), 300)}")
            f = fiches.get(f"pm{e['pmid']}")
            if f:
                afficher_fiche(f)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
