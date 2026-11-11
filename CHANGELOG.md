# Journal des changements

Évolutions notables de Veille Santé, de la plus récente à la plus ancienne.
Les versions sont numérotées MAJEUR.MINEUR.CORRECTIF et étiquetées dans Git.

## 1.1.1 — en préparation

### Ajouté
- Documentation technique dans le dépôt : `docs/ARCHITECTURE.md` (comment l'ensemble est
  construit) et `docs/DECISIONS.md` (registre des décisions et de leurs raisons).

### Modifié
- Le numéro de version est aussi affiché en tête de la page « À propos » : en bas de la page
  « Semaine », il fallait faire défiler toutes les fiches pour l'atteindre.

### Corrigé
- Référence d'une fiche : plus de double point après un titre terminé par un point, ni de point
  après un titre terminé par un point d'interrogation.

## 1.1.0 — 11 novembre 2026 (socle et transparence)

### Ajouté
- Tests automatiques à chaque modification (`.github/workflows/tests.yml`) : tests du moteur,
  démonstration complète avec IA simulée, et vérification que `installation/` reste identique
  aux workflows.
- Mémoire de chaque veille : après la publication, un résumé chiffré est écrit dans le journal
  du lancement et les données de travail sont gardées 90 jours en artefact. Le fichier des
  références, qui contient les résumés des articles, n'est pas copié.
- `scripts/resume_travail.py` : résumé chiffré d'un dossier de travail (étiquettes de départ,
  abaissements par l'IA, verdicts, motifs d'exclusion et de rejet).
- Niveau d'accès documentaire affiché sous chaque fiche : « Analyse à partir du résumé
  uniquement » tant que le moteur ne lit pas le texte intégral.
- `.gitignore` et ce journal des changements.
- Numéro de version affiché en bas de chaque page de l'app.

### Modifié
- Avertissement sur l'IA : texte court sous chaque fiche, texte complet sur la fiche seule et
  sur la page « À propos », qui explique l'absence de relecture humaine et les limites.
- Consigne de rédaction, correctif provisoire : l'étiquette de preuve n'est plus abaissée pour
  une information absente du résumé ; les verdicts « confirme » et « remet en question » sont
  mieux définis. Ce correctif sera remplacé par la refonte du niveau de preuve.
- `config.json` : adresse du site renseignée.
- Mise à jour de l'app : en ligne, la dernière version est chargée dès l'ouverture, et la copie
  gardée sur l'appareil ne sert plus que sans connexion. Auparavant, une mise à jour pouvait ne
  jamais arriver sur un téléphone. Quand une nouvelle version s'installe, l'app se recharge seule.

### Supprimé
- `.github/worklows/site.yml` : doublon mal orthographié de `.github/workflows/site.yml`,
  sans effet.

## 1.0.0 — 9 novembre 2026

Première version en production.

- Veille hebdomadaire automatique : collecte PubMed et HAS, tri et rédaction par IA en
  traitement différé, contrôle des chiffres et des DOI, synthèses par sous-champ, publication.
- Application web installable, sans compte : profil par profession et sous-champ, fiches
  dépliables, archive et recherche, favoris, export RIS, partage.
- Première veille publiée : semaine 2026-S45, 710 fiches.
