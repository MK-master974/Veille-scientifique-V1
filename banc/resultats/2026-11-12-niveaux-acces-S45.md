# Niveaux d'accès — semaine 2026-S45, mesure du 12 novembre 2026

Première mesure de la séance 4 de la phase 1 : pour chaque fiche publiée en S45, existe-t-il un
texte intégral accessible légalement, et sous quelle licence ? Lancement GitHub Actions
43187296541 (workflow « Niveaux d'accès »), commit 2f7e7e6, le 12 novembre 2026 à 08 h 58 UTC,
soit 2 jours après la publication de la semaine. Aucune IA n'est appelée : **coût nul**. Le texte
des articles n'est pas gardé.

## Résultats

| Mesure | Résultat |
| --- | --- |
| Fiches mesurées | 710, toutes retrouvées dans Europe PMC |
| Avec une version dans PubMed Central, selon Europe PMC | 435 (61 %) |
| Avec une version dans PubMed Central, selon PubMed | 455 (64 %) |
| Version connue de PubMed mais pas encore d'Europe PMC | 20 |
| Texte intégral reçu d'Europe PMC | 431 sur 435 demandés |
| Textes reçus mais partiels (niveau 2) | 0 |

### Licences des 435 versions trouvées

| Licence déclarée | Fiches | Ce qu'elle permet |
| --- | --- | --- |
| CC BY | 244 (56 %) | Réutilisation libre, y compris commerciale, avec mention des auteurs |
| CC BY-NC-ND | 153 (35 %) | Pas d'usage commercial, pas de modification |
| CC BY-NC | 24 (6 %) | Pas d'usage commercial |
| CC BY-NC-SA | 7 (2 %) | Pas d'usage commercial, partage à l'identique |
| CC BY-ND | 3 (1 %) | Pas de modification |
| Inconnue | 4 (1 %) | Rien n'est supposé |

### Part des fiches qui atteindraient le niveau 1, selon le périmètre de licences

| Périmètre | Toutes les fiches (710) | Fiches de kinésithérapie (73) |
| --- | --- | --- |
| A. CC BY et CC0 seulement | 244 (34 %) | 39 (53 %) |
| B. A, plus « pas d'usage commercial » et « partage à l'identique » | 275 (39 %) | 42 (58 %) |
| C. B, plus « pas de modification » | 431 (61 %) | 56 (77 %) |

Les autres fiches restent au niveau 3, « résumé uniquement ».

### Par type d'étude

| Type | Fiches | Niveau 1, périmètre A | Niveau 1, périmètre C |
| --- | --- | --- | --- |
| Essai randomisé | 90 | 20 (22 %) | 53 (59 %) |
| Étude diagnostique | 305 | 74 (24 %) | 161 (53 %) |
| Méta-analyse | 176 | 84 (48 %) | 129 (73 %) |
| Recommandation | 8 | 1 | 2 |
| Revue systématique | 131 | 65 (50 %) | 86 (66 %) |

### Taille des 431 textes reçus

| Mesure | Résultat |
| --- | --- |
| Avec une partie « méthode » et une partie « résultats » repérées | 417 |
| Avec au moins un tableau | 414 |
| Taille médiane | 42 834 caractères |
| Neuf textes sur dix font moins de | 72 192 caractères |
| Texte le plus long | 154 559 caractères |
| Volume total | environ 6,7 millions de jetons (estimation : 1 jeton pour 3 caractères) |

## Lecture

1. **C'est la licence qui décide, pas la disponibilité.** 61 % des fiches ont un texte intégral
   lisible dans PubMed Central, mais seulement 34 % sous une licence qui permet toute
   réutilisation. Les 27 points d'écart tiennent presque tous à la licence CC BY-NC-ND
   (153 fiches).
2. **La kinésithérapie est mieux servie** : 53 % au périmètre A, 77 % au périmètre C. L'effectif
   est petit (73 fiches) : ces parts sont indicatives.
3. **Les revues et méta-analyses sont plus souvent ouvertes** (48 à 50 % au périmètre A) que les
   essais et les études diagnostiques (22 à 24 %).
4. **Aucun texte partiel.** Les 431 textes reçus ont tous un corps complet ; 417 ont une partie
   « méthode » et une partie « résultats » repérables. Le niveau 2 est vide sur cette semaine.
5. **Aucun texte sous licence ouverte n'a été perdu.** Les 4 demandes restées sans texte
   correspondent aux 4 versions sans licence connue : les 431 versions sous licence Creative
   Commons ont toutes été reçues.
6. **Europe PMC a un léger retard sur PubMed** : 20 versions connues de PubMed n'y figuraient pas
   encore.

## Ordre de grandeur du coût de lecture **[ESTIMATION]**

Lire une fois ces 431 textes avec le modèle de rédaction actuel coûterait environ 6,70 $ au prix
plein, ou la moitié en traitement différé, hors réponse du modèle. La future chaîne lira un texte
plusieurs fois (extraction, appréciation, vérification) : le coût réel sera mesuré au banc
d'essai, à partir de la séance 5. Pour comparaison, la veille actuelle coûte environ 3 $ par
semaine. Le coût au seul périmètre A n'a pas été calculé séparément.

## Limites

- **Mesure faite 4 à 10 jours après l'entrée des articles dans PubMed.** Le lundi de la veille,
  moins de textes sont déjà déposés. Une mesure le jour même de la publication de S46 est prévue.
- La licence est celle que déclare Europe PMC. Elle n'a pas été relue dans chaque article.
- Seul PubMed Central est interrogé. Un texte en accès ouvert ailleurs n'est pas compté.
- Un texte est compté « lisible » s'il a un corps d'au moins 5 000 caractères et 2 parties.
- La lecture des 435 textes a pris 28 minutes : un texte intégral pèse lourd.

## Décision

Le porteur du projet a retenu le périmètre A le 12 novembre 2026 (VS-D21) : seules les licences
CC BY et CC0 ouvrent l'analyse du texte intégral.

## Ce qui reste

1. Mesurer S46 le jour de sa publication (VS-D22).
2. Demander, dans l'avis juridique commun, si l'analyse d'un texte sous licence « pas d'usage
   commercial » ou « pas de modification » est permise : 187 fiches de cette semaine en dépendent.
3. Étudier une lecture directe dans PubMed Central, pour ne pas dépendre du retard d'Europe PMC.
