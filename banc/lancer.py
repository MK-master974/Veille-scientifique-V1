"""Lance le banc d'essai demandé par la dernière ligne de banc/lancement.json.

Chaque lancement appelle l'IA et a un coût : il n'a lieu que sur demande écrite dans ce fichier,
avec l'accord du porteur du projet. Une demande précise :
- "banc" : "chaine" (chaîne actuelle de la veille, valeur par défaut) ou "extraction" ;
- "budget_usd" : plafond du lancement, vérifié avant tout appel. Il ne peut pas dépasser le
  plafond fixé ici pour chaque banc, même si la demande en écrit un plus grand ;
- pour le banc « extraction » : "s45" (nombre de publications réelles de 2026-S45 à extraire en
  plus), "effort" (effort de raisonnement, à la place de celui de config.json) et "sans_ia"
  (lecture des textes et estimation du coût seulement : aucun appel à l'IA, aucun coût).

Usage : python banc/lancer.py --sortie resultats-banc
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DEMANDES = RACINE / "banc" / "lancement.json"
BANCS = {"chaine": ("banc.py", 1.0), "extraction": ("banc_extraction.py", 2.0)}
EFFORTS = ("minimal", "low", "medium", "high")


def commande(demande, sortie):
    """Script et arguments d'une demande de lancement. Fonction pure, testée sans réseau."""
    banc = demande.get("banc", "chaine")
    if banc not in BANCS:
        raise SystemExit(f"Banc inconnu : {banc!r} (attendu : {', '.join(BANCS)})")
    script, plafond = BANCS[banc]
    budget = min(float(demande.get("budget_usd", plafond)), plafond)
    arguments = ["--sortie", sortie, "--budget", str(budget)]
    if banc == "extraction":
        if int(demande.get("s45", 0)) > 0:
            arguments += ["--s45", str(min(int(demande["s45"]), 12))]
        if demande.get("effort"):
            if demande["effort"] not in EFFORTS:
                raise SystemExit(f"Effort inconnu : {demande['effort']!r}")
            arguments += ["--effort", demande["effort"]]
        if demande.get("sans_ia") is True:
            arguments.append("--sans-ia")
    return script, arguments


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sortie", default="resultats-banc")
    args = p.parse_args(argv)
    demande = json.loads(DEMANDES.read_text(encoding="utf-8"))["lancements"][-1]
    script, arguments = commande(demande, args.sortie)
    print(f"Demande du {demande.get('date')} : {demande.get('raison')}\nAccord : {demande.get('accord')}\n"
          f"Lancement : {script} {' '.join(arguments)}\n", flush=True)
    spec = importlib.util.spec_from_file_location(script[:-3], RACINE / "banc" / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main(arguments)


if __name__ == "__main__":
    sys.exit(main())
