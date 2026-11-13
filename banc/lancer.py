"""Lance le banc d'essai demandé par la dernière ligne de banc/lancement.json.

Chaque lancement appelle l'IA et a un coût : il n'a lieu que sur demande écrite dans ce fichier,
avec l'accord du porteur du projet. Une demande précise :
- "banc" : "chaine" (chaîne actuelle de la veille, valeur par défaut), "extraction" ou
  "appreciation" (appréciation méthodologique et catégorie d'importance, séance 6) ;
- "budget_usd" : plafond du lancement, vérifié avant tout appel. Il ne peut pas dépasser le
  plafond fixé ici pour chaque banc, même si la demande en écrit un plus grand ;
- pour le banc « extraction » : "s45" (nombre de publications réelles de 2026-S45 à extraire en
  plus), "effort" (effort de raisonnement, à la place de celui de config.json), "parties"
  (« tout », « historique » : les cas mesurés depuis la séance 5, ou « chiffres » : les articles
  dont le corrigé est fait de chiffres relevés) et "sans_ia" (lecture des textes et estimation du
  coût seulement : aucun appel à l'IA, aucun coût).

- pour le banc « appreciation » : "s45" (publications de 2026-S45 à apprécier sur texte
  intégral), "classement" (publications de 2026-S45 à classer en plus, sur résumé), "limite"
  (articles au plus par outil, pour un essai court), "niveaux" (« integral » par défaut : pas
  d'appréciation sur résumé seul ; « tout » : aussi sur résumé), "sans_declarations" (lecture du
  texte intégral sans les déclarations placées hors du corps de l'article) et "sans_ia". Le banc
  établit d'abord le plan d'étude de chaque article lu en entier (séance 7, VS-D44).

Plafonds fixes : 1 $ pour la chaîne actuelle ; 3 $ pour l'extraction, porté de 2 $ à 3 $ le
12 novembre 2026 parce que le corpus grossit (VS-D33) ; 2,43 $ pour l'appréciation, soit toute
l'enveloppe de la séance 6 (VS-D38).

Usage : python banc/lancer.py --sortie resultats-banc
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DEMANDES = RACINE / "banc" / "lancement.json"
BANCS = {"chaine": ("banc.py", 1.0), "extraction": ("banc_extraction.py", 3.0),
         "appreciation": ("banc_appreciation.py", 2.43)}
EFFORTS = ("minimal", "low", "medium", "high")
PARTIES = ("tout", "historique", "chiffres")
NIVEAUX = ("tout", "integral")


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
        if demande.get("parties"):
            if demande["parties"] not in PARTIES:
                raise SystemExit(f"Parties inconnues : {demande['parties']!r} (attendu : {', '.join(PARTIES)})")
            arguments += ["--parties", demande["parties"]]
        if demande.get("sans_ia") is True:
            arguments.append("--sans-ia")
    if banc == "appreciation":
        for cle, maximum in (("s45", 12), ("classement", 40), ("limite", 50)):
            if int(demande.get(cle, 0)) > 0:
                arguments += [f"--{cle}", str(min(int(demande[cle]), maximum))]
        if demande.get("niveaux"):
            if demande["niveaux"] not in NIVEAUX:
                raise SystemExit(f"Niveaux inconnus : {demande['niveaux']!r} (attendu : {', '.join(NIVEAUX)})")
            arguments += ["--niveaux", demande["niveaux"]]
        if demande.get("sans_declarations") is True:
            arguments.append("--sans-declarations")
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
