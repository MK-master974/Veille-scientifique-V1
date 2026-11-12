# Journal des changements

Évolutions notables de Veille Santé, de la plus récente à la plus ancienne.
Les versions sont numérotées MAJEUR.MINEUR.CORRECTIF et étiquetées dans Git.

## Non publié

### Modifié
- `CLAUDE.md`, règle 7 : un court passage exact d'un article sous licence CC BY ou CC0 peut être
  cité avec sa source (VS-D15). Tout autre texte d'article reste interdit dans le dépôt et les
  données publiques.
- Documentation remise à jour : `banc/README.md` indique que le banc d'essai est écrit et a
  tourné deux fois ; `docs/ARCHITECTURE.md` décrit ses deux workflows.

### Corrigé
- Contrôle des chiffres de la veille : il lit désormais les nombres écrits en toutes lettres
  au-delà de dix (« Seventy-four », « trente-deux ») et les décimales sans zéro initial
  (« P < .05 »). Ces formes faisaient écarter à tort des fiches justes : 8 sur 16 au banc d'essai
  du 11 novembre 2026. Un nombre absent de la source reste refusé.
- Contrôle des chiffres, suite (relecture du portail) : deux nombres séparés par une virgule sans
  espace (« 1.2,3.4 ») sont de nouveau lus tous les deux, et « between twenty and thirty » ne
  donne plus 50.

### Ajouté
- Phase 1, séance 4 : `pipeline/acces.py` cherche le texte intégral légal d'une publication, lit
  sa licence et attribue un niveau d'accès ; `banc/mesure_acces.py` et le workflow « Niveaux
  d'accès » mesurent ces niveaux sur une semaine déjà publiée. Aucune IA n'est appelée, aucun
  texte d'article n'est gardé, et la veille hebdomadaire n'utilise pas encore ce module.
- Première mesure des niveaux d'accès, sur 2026-S45 : 61 % des fiches ont un texte intégral
  lisible dans PubMed Central, 34 % sous une licence CC BY. Résultats dans
  `banc/resultats/2026-11-12-niveaux-acces-S45.md`. La mesure a désormais une durée maximale et
  rend toujours un résultat.
- `docs/FICHE_V2.md` : format cible d'une fiche, la « fiche v2 », décidé le 12 novembre 2026
  (VS-D12 à VS-D15). Fiche unique progressive avec l'impact clinique dans l'en-tête, niveau
  d'accès et profondeur d'analyse, données extraites avec leur emplacement, catégorie d'importance
  à la place du verdict, étiquette à quatre valeurs, version et historique. Le moteur et
  l'application ne changent pas : la veille publie le format actuel jusqu'à la bascule.
- `docs/FICHE_V2.md`, compléments demandés par le portail et par Évalys : région anatomique prise
  dans une liste commune de dix régions (`classement.themes.region`, VS-D16, POR-D22), liste des
  cinq types d'étude actuels, date de mise en ligne de l'article (`publication.date_en_ligne`,
  VS-D19).
- Corpus de référence, suite : cas « qualité méthodologique » (`banc/corpus/qualite.json` : RoB 2,
  QUADAS-2, AMSTAR 2, AGREE II, tirés de revues sous licence CC BY) et trois pièges
  (`banc/corpus/pieges.json`). `banc/extraire_tableaux.py` repère les tableaux d'évaluation dans
  ces revues. Aucune IA n'est appelée.
- `CLAUDE.md` : consignes de travail pour les sessions de développement (règles impératives,
  circuit d'une modification, communication, coordination avec les autres applications).
- `banc/assembler_essais.py` et le workflow « Corpus de référence » : assemblage des premiers cas
  du corpus de référence à partir du jeu de données public Evidence Inference (licence MIT).
  Aucune IA n'est appelée.

## 1.1.1 — 11 novembre 2026

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
