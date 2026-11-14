# Diagnostic des quatre premières grilles (RoB 2, QUADAS-2, AMSTAR 2, AGREE II) — 14 novembre 2026

Décision VS-D73 : diagnostic sans IA et sans coût. Source : le journal de la dernière mesure complète de
ces grilles, lancement 43378868507 (séance 7, 13 novembre 2026, consigne `appreciation.txt` 4ce7fb70,
inchangée depuis). Corpus : 25 articles lus en entier (16 jugés avec AMSTAR 2, 7 avec QUADAS-2, 2 avec
RoB 2 ; aucun avec AGREE II). Rien n'a été relancé ni dépensé.

## En bref

- **Le moteur ne fait pas mieux qu'une réponse « toujours le pire niveau ».** Il donne le jugement global
  exact de la revue pour 13 articles sur 25. Une réponse fixe au niveau le plus sévère de chaque grille
  en donne aussi 13. À un cran près : 20 contre 18. La mesure actuelle ne peut donc pas dire si le moteur
  juge bien.
- **Le moteur est presque toujours au niveau le plus sévère** : AMSTAR 2 « très faible » 13 fois sur 16,
  QUADAS-2 « élevé » 6 fois sur 7. Les revues sont plus clémentes, et leur corpus est lui-même dominé par
  les niveaux sévères (AMSTAR 2 « très faible » 8 fois sur 16), ce qui flatte une réponse fixe.
- **Pour AMSTAR 2, le « très faible » de 8 revues sur 16 ne tient qu'à des cases « non rapporté »** :
  l'article lu ne dit rien, et la lecture stricte compte ce silence comme le pire. Si ces cases valaient
  « oui », ces revues pourraient être « élevée ». D'où une fourchette qui couvre les 4 niveaux.
- **Pour QUADAS-2, la sévérité repose sur des faits précis**, vérifiés dans les passages : exclusions de
  patients ou d'examens, échantillon enrichi, biais d'incorporation, référence qui varie selon les
  patients. C'est défendable au regard de l'outil. Comme pour ROBINS-I, les revues paraissent généreuses.

## Jugement global (25 articles)

| Grille | Articles | Exacts (moteur) | Exacts (réponse fixe au pire niveau) | Moteur au pire niveau | Moteur plus sévère de deux crans |
| --- | --- | --- | --- | --- | --- |
| AMSTAR 2 | 16 | 10 | 8 | 13 | 2 |
| QUADAS-2 | 7 | 2 | 3 | 6 | 3 |
| RoB 2 | 2 | 1 | 2 | 1 | 0 |
| **Total** | **25** | **13** | **13** | **20** | **5** |

Corrigés des revues : AMSTAR 2 très faible 8, faible 4, modérée 4 ; QUADAS-2 élevé 3, incertain 1,
faible 3 ; RoB 2 élevé 2.

## Par domaine : où le moteur s'écarte des revues

**AMSTAR 2** (16 revues). Les cases « non rapporté » du moteur se concentrent sur quelques questions :
- financement des études incluses (q10) : 8 fois ;
- choix des plans d'étude (q03) : 6 ;
- effet du risque de biais sur le résultat groupé (q12) : 6 ;
- protocole (q02) : 5 ;
- liste des études exclues (q07) : 5 ;
- biais de publication (q15) : 3 ;
- extraction en double (q06) : 3.

Trois de ces questions sont critiques pour l'outil : q02, q07 et q15. Une seule réponse « non », ou
« non rapporté » en lecture stricte, à deux questions critiques suffit à donner « très faible ».

En dehors de ces silences, les écarts vont dans les deux sens. Le moteur est plus favorable sur
l'interprétation (q13) et sur les conflits d'intérêts (q16), 3 fois chacun ; il est plus sévère sur
l'évaluation du risque de biais (q09), 3 fois.

**QUADAS-2** (7 études). Le moteur est plus sévère sur trois domaines du risque de biais :
- sélection des patients : « élevé » 4 fois où la revue dit « faible » ;
- test évalué : « incertain » 4 fois où la revue dit « faible » ;
- flux et délais : « élevé » 2 fois où la revue dit « faible ».

Les domaines d'applicabilité diffèrent aussi, mais ils ne comptent pas dans le jugement global. Le moteur
les juge par rapport à « la question », qu'il ne connaît pas, alors que la revue les juge par rapport à
sa propre question.

**RoB 2** (2 essais) : trop peu d'articles pour conclure.

## Relecture critique de la session (VS-D53)

Relu : les justifications et les passages des 7 études QUADAS-2. Les jugements sévères s'appuient sur des
faits de l'article, et ils sont cohérents avec les questions de l'outil :
- « les exclusions de patients sont-elles évitées ? » ;
- « tous les patients sont-ils analysés ? » ;
- « la référence est-elle interprétée sans connaître le test ? ».

Non relu : les justifications AMSTAR 2, revue par revue.

## Causes retenues

1. **La mesure ne peut pas trancher.** Le corpus manque d'articles bien notés par les revues (aucune revue
   AMSTAR 2 « élevée », aucun essai RoB 2 à faible risque), et le seuil de VS-D39 (« à un cran au plus »)
   laisse passer une réponse fixe. Toute correction mesurée ainsi resterait invérifiable.
2. **Les silences d'AMSTAR 2.** Une partie de l'information se trouve souvent dans les suppléments, que le
   moteur ne lit pas (VS-D49 : 11 revues sur 16 déclarent du matériel supplémentaire). La lecture stricte
   en fait des « non », ce qui pousse vers « très faible ».
3. **Une sévérité défendable mais plus forte que celle des revues**, comme pour ROBINS-I. Rendre le moteur
   plus clément pour coller aux revues n'est pas forcément le rendre plus juste.
