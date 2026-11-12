# Corpus renforcé et mesure de l'extraction sur des chiffres relevés — 12 novembre 2026

Suite décidée au point d'arrêt de la séance 5 (VS-D28) : renforcer le corpus de référence avec des
études diagnostiques, des méta-analyses et des revues qui ont déjà un corrigé, puis remesurer
l'extraction. Rien n'est publié et la veille hebdomadaire n'est pas concernée. Modèle : celui de
la rédaction de la veille, tel que réglé dans `config.json`, avec le même effort ; mode direct, au
prix plein. Consigne d'extraction inchangée depuis la clôture de la séance 5.

## Pourquoi

En 2026-S45, 620 fiches publiées sur 710 sont des études diagnostiques (305), des méta-analyses
(176) ou des revues systématiques (131). L'extraction n'était mesurée que sur 8 essais randomisés.

## Le corpus ajouté

`banc/corpus/chiffres_releves.json` : **20 articles sous licence CC BY** (9 études diagnostiques,
10 méta-analyses, 1 revue systématique sans méta-analyse) et **161 chiffres** que les auteurs de
9 revues en accès libre avaient déjà relevés dans leurs tableaux (VS-D32). Personne n'a rempli de
corrigé à la main. Le détail des revues sources et du choix des articles est dans
[`banc/README.md`](../README.md).

| Étape, sans IA | Lancement | Résultat |
| --- | --- | --- |
| Repérage de 82 revues candidates trouvées dans PubMed | 43276480183 | 62 sous licence CC BY avec un texte lisible ; 13 ont un tableau de chiffres qui cite des études sous licence CC BY |
| Lecture des lignes de tableaux | 43278548445, 43279523961 | 9 revues sources gardées, 20 articles |
| Vérification du corpus | 43284046225 | Licences conformes : 20 sur 20. Recopie conforme : 161 chiffres sur 161. Confirmés dans leur article : 159 sur 161 |

Les deux chiffres écartés sont la sensibilité et la spécificité de la règle d'Ottawa pour une
étude ([10.7717/peerj.10152](https://doi.org/10.7717/peerj.10152)) : la revue source les a
calculées elle-même (0,95 et 0,16), et le résumé de l'article dans PubMed en rapporte d'autres
(0,59 et 0,37). Ils restent dans le corpus, marqués, et ne comptent pas dans le score (VS-D34).

## Résultat

Première mesure : lancement 43281503491, sur les 20 articles, à partir du résumé seul puis du
texte intégral. La comparaison est faite par le code, sans IA lectrice.

| Chiffres du corrigé retrouvés dans l'extraction | Résumé seul | Texte intégral |
| --- | --- | --- |
| Avec les règles fixées avant la mesure | 115 sur 161 (71 %) | **150 sur 161 (93,2 %)** |
| Avec les règles corrigées après la mesure (recalcul 43284046225, mêmes extractions) | 113 sur 159 (71 %) | **149 sur 159 (93,7 %)** |
| dont études diagnostiques, règles corrigées | 41 sur 59 | 58 sur 59 |
| dont méta-analyses, règles corrigées | 71 sur 98 | 89 sur 98 |
| dont revue systématique, règles corrigées | 1 sur 2 | 2 sur 2 |

**Seuil fixé par le porteur du projet (VS-D34) : au moins 80 % à partir du texte intégral.
Atteint, avec les règles d'origine comme avec les règles corrigées.**

## Quatre défauts de l'instrument, trouvés après la première mesure

Les règles de comparaison avaient été fixées avant la mesure. L'examen des 11 chiffres non
retrouvés a montré que quatre d'entre elles étaient fausses. Elles sont corrigées dans
`banc/chiffres.py` ; les deux scores sont publiés pour que la correction ne puisse pas arranger
le résultat.

| Défaut | Effet sur le score |
| --- | --- |
| Un zéro final pris pour un arrondi : « 0,7 » n'égalait pas « 0,70 » | Pénalisait l'extraction |
| Un nombre d'études écrit en toutes lettres, non lu (« Huit études ») | Pénalisait l'extraction |
| Le « 95 » de « IC à 95 % » lu comme une donnée : toute sensibilité de 0,95 était retrouvée par hasard, dans l'article comme dans l'extraction | Flattait l'extraction, et confirmait à tort deux chiffres dans leur article |
| Une valeur cherchée dans tout un résultat : un effet de 0,06 était « retrouvé » dans la borne 0,06 d'un autre résultat | Flattait l'extraction |

Une première vérification retrouvait les 161 chiffres dans leur article, ce qui ne prouvait rien :
un petit nombre se retrouve presque toujours quelque part dans un long texte. Une **règle de
voisinage** a donc été ajoutée avant la première mesure : un chiffre n'est confirmé qu'à côté des
chiffres de son groupe (un effet et son intervalle ; sensibilité, spécificité et aire sous la
courbe d'un même test).

## Les dix chiffres non retrouvés, texte intégral, règles corrigées

| Article | Chiffre | Constat |
| --- | --- | --- |
| PMID 23620778 | Borne 0,70 de l'intervalle de la douleur | **L'article se contredit.** Son résumé dans PubMed donne −0,70 ([10.1371/journal.pone.0061672](https://doi.org/10.1371/journal.pone.0061672)) ; l'extraction cite le corps du texte, où le passage vérifié par le code donne −0,77 |
| PMID 41296768 | Borne 0,28 de l'intervalle du Timed Up and Go | La revue source écrit −0,28 ; l'extraction cite un passage de l'article qui donne −0,29 |
| PMID 29713967 | 10 essais | Décompte propre à la revue source ; le résumé de l'article dans PubMed en annonce 18 ([10.1007/s10067-018-4106-2](https://doi.org/10.1007/s10067-018-4106-2)), et l'extraction aussi |
| PMID 29713967 | Effet et intervalle du WOMAC total, intervalle du WOMAC fonction (5 chiffres) | **Défaut de l'extraction** : ces deux résultats sont extraits sans leur valeur |
| PMID 37489348 | 8 essais | **Défaut de l'extraction** : le champ « effectif » donne les participants, pas le nombre d'études |
| PMID 37443572 | 215 participants | **Défaut connu** : le contrôle du code a refusé le champ « effectif » (un second nombre, 245, ne figurait pas dans le bloc cité) ; le champ est resté vide, sans seconde demande |

Bilan : 7 chiffres manquent par un défaut de l'extraction ; 3 tiennent à la source (un article qui
se contredit, deux écarts entre la revue source et l'article). Le contrôle fait avant la mesure
n'avait écarté aucun de ces trois-là. **Vérifié** : les résumés de PubMed pour trois articles, et les passages des
extractions, contrôlés mot pour mot par le code. **Non vérifié** : les articles n'ont pas été
relus en entier, et aucun humain n'a relu ces extractions.

## Contrôles du code, première mesure

| Mesure | Résumé seul | Texte intégral |
| --- | --- | --- |
| Extractions lisibles | 20 sur 20 | 20 sur 20 |
| Données gardées après contrôle | 234 sur 234 | 543 sur 550 |
| Refus | 0 | 7 : 6 « chiffre absent du bloc cité », 1 « passage trop long » |
| Coût réel par article | 0,011 $ | 0,034 $ |

- Quatre des refus portent sur des lignes d'un tableau dont l'IA écrit l'intervalle « IC à
  95 % », alors que le « 95 » n'est pas écrit dans ce tableau : quatre résultats d'une étude
  diagnostique sont perdus. Le niveau de confiance n'est pas une donnée : ce contrôle est à
  assouplir (séance 7, « corriger puis revérifier »).
- Trois champs sont vidés par un refus, sur deux articles : un effectif, deux populations.
- Sur 439 résultats extraits des textes intégraux, 41 n'ont pas de valeur, et 37 sont notés
  « principal », dans 7 articles (jusqu'à 10 sur 20 dans une méta-analyse). Non vérifié : si ces
  rangs sont justifiés.
- Trois articles atteignent ou frôlent le maximum de 40 résultats.

## Ce que le texte intégral apporte

À partir du résumé seul, l'extraction retrouve 71 % des chiffres ; à partir du texte intégral,
94 %. L'écart est le plus net pour les études diagnostiques (41 contre 58 sur 59) : les
sensibilités et spécificités par test ou par sous-groupe sont dans les tableaux, pas dans le
résumé.
