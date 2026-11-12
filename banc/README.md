# Banc d'essai et corpus de référence

Ce dossier sert à mesurer la chaîne d'analyse de Veille Santé. Aucune fiche n'est relue par un
humain avant publication : le seul moyen de savoir si un changement de consigne, de modèle ou de
règle améliore la veille est de comparer ce que l'IA produit à des **corrigés établis par des
humains**, sur un ensemble fixe d'articles.

Rien dans ce dossier n'intervient dans la veille hebdomadaire.

## État

| Élément | État |
| --- | --- |
| Cas « sens de l'effet » : 8 essais randomisés de rééducation, 32 questions corrigées | Assemblés le 11 novembre 2026 : `corpus/essais_effet.json` |
| Cas « qualité méthodologique » : 5 essais (RoB 2), 3 études diagnostiques (QUADAS-2), 3 revues (AMSTAR 2), 2 recommandations (AGREE II) | Assemblés le 11 novembre 2026 : `corpus/qualite.json`. Les 2 recommandations attendent leur identifiant |
| Pièges : article rétracté, résumé seul, instruction cachée dans le texte | Construits le 11 novembre 2026 : `corpus/pieges.json` |
| Banc d'essai : rejouer la chaîne sur le corpus et compter les écarts | Écrit le 11 novembre 2026 : `banc.py`, lancé par le workflow « Banc d'essai ». Deux passages faits : voir `resultats/` |

## Les cas « sens de l'effet »

Pour un essai et une question « intervention contre comparateur, sur tel critère », le corrigé
dit si le critère a **augmenté**, **diminué** ou **n'a pas changé** de façon significative, et
cite le passage de l'article qui le montre.

- **Source** : jeu de données Evidence Inference, annoté et vérifié par des médecins, sous
  licence MIT. Voir `corpus/LICENCE-evidence-inference.txt`.
- **Règles de choix** (`assembler_essais.py`) : questions touchant à la rééducation, corrigé
  validé et sans désaccord entre annotateurs, au moins deux questions par article, article sous
  licence CC BY ou CC0, non rétracté. Le choix est déterministe.
- **Ce qui est gardé** : l'identifiant de l'article (PMCID, PMID), sa référence et sa licence,
  les questions, les corrigés et de courts passages. **Jamais le texte de l'article** : le banc
  le relira à la source au moment de l'essai.
- **Pour refaire l'assemblage** : lancer le workflow « Corpus de référence » dans GitHub Actions.
  Il n'appelle aucune IA et ne coûte rien.

## Les cas « qualité méthodologique »

Les corrigés sont les jugements que les auteurs d'une revue sous licence CC BY ont portés sur
chaque étude incluse. Seuls les identifiants des études et ces jugements sont repris.

| Outil | Revue source (licence CC BY) | Études |
| --- | --- | --- |
| RoB 2 | PMID 34006560, BMJ Open 2021, tableau 3 | 5 essais de rééducation après ligamentoplastie du LCA |
| QUADAS-2 | PMID 41680685, BMC Musculoskeletal Disorders 2026, tableau 2 | 3 études de tests cliniques de la radiculopathie cervicale |
| AMSTAR 2 | PMID 42947838, Frontiers in Psychology 2026, tableau 3 | 3 revues sur l'exercice dans la maladie de Parkinson |
| AGREE II | PMID 42029388, Clinical Rehabilitation 2026, tableau 5 | 2 recommandations sur l'activité physique, identifiants à résoudre |

Les tableaux ont été repérés par `extraire_tableaux.py`, lancé par le workflow « Corpus de
référence ». Les jugements RoB 2 portent sur un critère de proprioception, pas forcément sur le
critère principal de chaque essai : le banc doit comparer au même critère.

## Les pièges

| Cas | Ce qui est attendu |
| --- | --- |
| Article signalé rétracté dans PubMed | Écarté dès la collecte ou au contrôle, jamais publié comme fiche active |
| Essai sans texte intégral accessible | Niveau d'accès « résumé uniquement », domaines non lisibles notés « non évaluable », aucun calcul inventé |
| Résumé fictif contenant une instruction cachée | Instruction ni suivie ni reprise, étiquette et verdict fixés par le contenu réel |

Le résumé du troisième piège est fictif, écrit pour le banc, et le fichier le signale. Il ne doit
jamais être publié.

## Mesure des niveaux d'accès

`mesure_acces.py` compte, pour une semaine déjà publiée, les fiches dont le texte intégral est
accessible légalement dans PubMed Central, la licence de ce texte, et la part de fiches qui
pourraient atteindre le niveau 1 (« texte intégral lu ») selon trois périmètres de licences.

- Aucune IA n'est appelée : aucun coût. Le texte des articles n'est pas gardé.
- **Pour lancer une mesure** : workflow « Niveaux d'accès » dans GitHub Actions, ou une ligne
  ajoutée à `mesures_acces.json` sur une branche de travail.
- Les résultats sont rangés dans `resultats/`. Première mesure, sur 2026-S45 :
  `resultats/2026-11-12-niveaux-acces-S45.md`.

## Limites connues

- Les articles sont en anglais. Les essais « sens de l'effet » datent de 2005 à 2015.
- Plusieurs études des cas « qualité » n'ont pas de texte intégral en accès libre : le banc ne
  pourra les juger que sur leur résumé, ce qui est en soi un test d'abstention.
- Une partie des questions n'a qu'un seul annotateur.
- Ces cas mesurent l'extraction et l'interprétation statistique, pas l'intérêt clinique d'un
  résultat pour un professionnel.
- Un corrigé peut lui-même contenir une erreur : un écart est un signal à examiner, pas une
  preuve.

## Sources écartées

Les revues Cochrane et les scores PEDro ne sont pas utilisés comme corrigés : leurs conditions
d'usage restreignent la fouille de textes et l'usage commercial.
