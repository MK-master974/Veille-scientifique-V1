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
| Cas « qualité méthodologique » : études déjà évaluées dans des revues en accès libre (RoB 2, AMSTAR 2, QUADAS-2, AGREE II) | À assembler |
| Pièges : article rétracté, résumé seul, instruction cachée dans le texte | À construire |
| Banc d'essai : rejouer la chaîne sur le corpus et compter les écarts | À écrire |

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

## Limites connues

- Les articles sont en anglais et datent de 2005 à 2015.
- Une partie des questions n'a qu'un seul annotateur.
- Ces cas mesurent l'extraction et l'interprétation statistique, pas l'intérêt clinique d'un
  résultat pour un professionnel.
- Un corrigé peut lui-même contenir une erreur : un écart est un signal à examiner, pas une
  preuve.

## Sources écartées

Les revues Cochrane et les scores PEDro ne sont pas utilisés comme corrigés : leurs conditions
d'usage restreignent la fouille de textes et l'usage commercial.
