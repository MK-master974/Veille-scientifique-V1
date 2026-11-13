# Appréciation par outil et catégories d'importance — 13 novembre 2026

Séance 6 de la phase 1 (VS-D37) : appréciation méthodologique d'une publication par l'outil adapté
à son type d'étude, et catégorie d'importance de 1 à 4. Rien n'est publié et la veille
hebdomadaire n'est pas concernée : les deux modules ne sont pas appelés par elle. Modèle : celui de
la rédaction de la veille, tel que réglé dans `config.json`, avec le même effort ; mode direct, au
prix plein. Consignes : `appreciation.txt` (empreinte 74839e05) et `classement.txt` (73c247ae).

## En bref

- **Deux mesures, un résultat au niveau du seuil** (VS-D39, au moins 70 % des jugements globaux à
  un cran au plus du corrigé) : 18 sur 25 à la première (72 %, atteint), 17 sur 25 à la seconde
  (68 %, non atteint). Aucun jugement plus favorable que le corrigé de deux crans, dans les deux
  mesures.
- **Ce résultat ne prouve pas que le moteur distingue une bonne étude d'une mauvaise.** Répondre
  toujours « le plus mauvais niveau » aurait donné 18 sur 25. Le moteur donne le plus mauvais
  niveau à 21 articles sur 25, puis à 22.
- **L'IA ne répond pas deux fois la même chose** : sur les 10 articles dont le texte était
  identique d'une mesure à l'autre, 11 jugements par domaine sur 122 changent (9 %), et un article
  change de jugement global.
- **Le défaut de lecture des déclarations est corrigé** (VS-D40) : 7 des 9 revues concernées
  obtiennent maintenant « oui » à la question 16. Le score global n'en profite pas.
- **Le moteur ne se trompe pas dans le sens dangereux** : aucun jugement global plus favorable
  que le corrigé de deux crans, et deux plus favorables d'un cran.
- **Le contrôle du code tient** : 2 refus pour 315 domaines jugés, puis 3, aucune réponse
  illisible.
- **L'étiquette candidate (VS-D14) n'est pas utilisable telle quelle** : elle donnerait
  « préliminaire » à 9 des 10 publications réelles appréciées, et ne dirait rien de la dixième.
- **Coût : 1,38 $** sur l'enveloppe de 2,43 $ (VS-D38).

## Ce qui est mesuré

| Corpus | Cas | Texte intégral lisible |
| --- | --- | --- |
| `banc/corpus/qualite_lisible.json`, assemblé pour cette séance | 25 : 16 revues (AMSTAR 2), 7 études diagnostiques (QUADAS-2), 2 essais (RoB 2) | 25, sous licence CC BY |
| `banc/corpus/qualite.json`, assemblé le 11 novembre 2026 | 10 cas utilisés : 3 revues, 3 études diagnostiques, 4 essais | aucun : résumé seul |

Le corrigé de chaque article est le jugement déjà porté par les auteurs d'une revue en accès
libre. Personne n'a rempli de corrigé à la main (VS-D32). Chaque article est apprécié à partir de
son résumé, puis de son texte intégral quand il se lit. L'IA juge chaque domaine de l'outil et cite
le passage qui fonde son jugement ; le code vérifie le passage mot pour mot, refuse un jugement
favorable sans passage, et calcule lui-même le jugement global. L'écart avec le corrigé se compte
en crans sur l'échelle de l'outil.

| Lancement | Objet | Coût réel |
| --- | --- | --- |
| 43363536857 | Lecture des textes, sans IA : 25 textes intégraux lus, 10 publications de 2026-S45 retenues, estimation 1,78 $ | 0 $ |
| 43364297944 | Essai court : un article par outil, deux classements | 0,07 $ |
| 43364759666 | Première mesure, complète | 0,88 $ |
| 43370197937 | Vérification de la nouvelle lecture, sans IA | 0 $ |
| 43370405955 | Seconde mesure, texte intégral seul | 0,43 $ |

Les sections qui suivent décrivent la première mesure. La seconde a sa section plus bas.

## Résultat sur texte intégral

| Jugement global, 25 articles | Tous | AMSTAR 2 | QUADAS-2 | RoB 2 |
| --- | --- | --- | --- | --- |
| Articles | 25 | 16 | 7 | 2 |
| Identique au corrigé | 11 | 8 | 2 | 1 |
| À un cran du corrigé | 7 | 4 | 2 | 1 |
| Plus sévère de deux crans ou plus | 6 | 3 | 3 | 0 |
| Plus favorable de deux crans ou plus | **0** | 0 | 0 | 0 |
| Non évaluable | 1 | 1 | 0 | 0 |
| **À un cran au plus** | **18 sur 25 (72 %)** | 12 sur 16 | 4 sur 7 | 2 sur 2 |

Parmi les 7 jugements à un cran, 5 sont plus sévères que le corrigé et 2 plus favorables : une
étude diagnostique jugée « incertain » et un essai jugé « quelques réserves », quand le corrigé dit
« risque élevé » (PMID 39080893 et 29796857).

**Seuils fixés par le porteur du projet (VS-D39) : au moins 70 % à un cran au plus, atteint ;
aucun jugement plus favorable de deux crans, atteint.**

## Ce que le seuil ne montre pas

Le moteur donne presque toujours le plus mauvais niveau de l'échelle.

| Outil | Jugements du corrigé | Jugements du moteur |
| --- | --- | --- |
| AMSTAR 2, 16 revues | 8 « très faible », 4 « faible », 4 « modérée » | 14 « très faible », 1 « faible », 1 non évaluable |
| QUADAS-2, 7 études | 3 « élevé », 1 « incertain », 3 « faible » | 6 « élevé », 1 « incertain » |
| RoB 2, 2 essais | 2 « élevé » | 1 « élevé », 1 « quelques réserves » |

Une réponse constante, « le plus mauvais niveau » pour tous les articles, aurait obtenu 18 sur 25
elle aussi : le corpus contient surtout des articles mal notés par leur revue. Le score global ne
départage donc pas le moteur d'une réponse aveugle.

La mesure qui départage est celle des articles bien notés :

| Corrigé | Articles | À un cran au plus | Plus sévère de deux crans | Non évaluable |
| --- | --- | --- | --- | --- |
| Dans les deux crans du bas de l'échelle | 18 | 17 | 0 | 1 |
| À deux crans ou plus au-dessus du plus mauvais niveau | 7 | **1** | **6** | 0 |

Sur les 7 articles que leur revue juge bons ou assez bons (4 revues « modérée », 3 études
diagnostiques à risque de biais faible), le moteur n'en reconnaît qu'un, à un cran près. Les 6
autres sont les PMID 30961569, 35847669 et 41296768 (AMSTAR 2) et 31569689, 33145440 et 35271382
(QUADAS-2).

## Accord domaine par domaine

Le corrigé par domaine existe pour 8 revues, les 7 études diagnostiques et les 2 essais.

| Outil | Domaines comparés | Identiques | Ce que montre le détail |
| --- | --- | --- | --- |
| AMSTAR 2 | 128 | 84 (66 %) | Le moteur n'est pas plus sévère question par question : il répond « non » 58 fois, le corrigé 54 fois. En ne gardant que « oui » ou « non », 94 réponses sur 124 sont d'accord ; répondre toujours « oui » aurait donné 72 |
| QUADAS-2, risque de biais | 23 | 4 | Le moteur est plus sévère 16 fois, plus favorable 3 fois |
| QUADAS-2, applicabilité | 21 | 9 | Plus sévère 7 fois, plus favorable 5 fois |
| RoB 2 | 10 | 5 | Plus sévère 3 fois, plus favorable 2 fois. Deux essais : rien à conclure |

### AMSTAR 2 : la règle de l'outil pèse plus que les réponses

Le code applique la règle de l'outil à la lettre : plus d'une faiblesse critique donne « très
faible ». Avec sept questions critiques, deux « non » suffisent. Deux constats, vérifiés sur le
corpus :

- Appliquée aux 16 réponses du corrigé lui-même, cette règle donne un niveau plus bas que celui
  que les auteurs de la revue ont publié, pour 2 des 8 articles (PMID 29980200 : « faible »
  publié, « très faible » par la règle ; PMID 30961569 : « modérée » publié, « faible » par la
  règle). Les auteurs des revues sources sont plus indulgents que la règle stricte.
- Les questions le plus souvent en désaccord sont la déclaration des conflits d'intérêts
  (6 articles sur 8), la prise en compte du biais dans l'interprétation (5) et la description des
  études (4).

### Un défaut de lecture, trouvé à cette occasion

`pipeline/texte.py` ne lit que le corps de l'article, ses tableaux et ses figures. Les
déclarations de financement et de conflits d'intérêts placées dans les parties annexes du fichier
ne sont pas transmises à l'IA. Vérifié dans le code. Conséquence observée : pour 9 revues sur 16,
le moteur répond « non » à la question 16 en écrivant que ces déclarations ne figurent pas « dans
le texte fourni ». Pour les 4 revues de 2026-S45, où ces déclarations sont dans le corps de
l'article, il répond « oui » les 4 fois. Non vérifié article par article : l'endroit exact de ces
déclarations dans les 9 fichiers.

De même, les fichiers annexes d'un article (liste des études exclues, équation de recherche
complète) ne sont pas lus. C'est une hypothèse pour une partie des « non » aux questions 4 et 7,
non vérifiée.

### QUADAS-2 : le moteur relève des défauts que le corrigé ne retient pas

Le désaccord est massif sur la sélection des patients : 7 études sur 7 pour le risque de biais,
7 sur 7 pour l'applicabilité. Dans les deux études relues par la session de développement
(PMID 31569689 et 33145440), le jugement du moteur s'appuie sur un passage exact de l'article :
des résidents de maison de retraite exclus, des seuils choisis d'après les données de l'étude, un
échantillon enrichi en fractures. Ce sont des questions que l'outil pose réellement. Le corrigé,
lui, note « risque faible ».

Un exemple du même ordre pour AMSTAR 2. Pour la revue de Charlesworth et collaborateurs
(BMC Musculoskelet Disord 2019, [PMID 30961569](https://pubmed.ncbi.nlm.nih.gov/30961569/),
licence CC BY), le corrigé répond « oui » à la sélection des études en double. Le moteur répond
« non » et cite l'article : « However, by the standards of a systemic review, another author
should have screened the articles and this is a limitation to the search strategy. »

**Ce qui est vérifié** : le moteur est plus sévère que les corrigés, et ses jugements sévères
citent un passage exact. **Ce qui ne l'est pas** : qui a raison, du moteur ou des auteurs des
revues. Aucun humain n'a tranché. C'est l'objet de la relecture des dix fiches par le porteur du
projet.

## Sur résumé seul

| Mesure, 35 articles | Résultat |
| --- | --- |
| Jugement global non évaluable | 33 |
| Jugement global rendu | 2, tous deux « risque élevé » (QUADAS-2), plus sévères de deux crans que le corrigé |
| Domaines notés « non évaluable » | 341 sur 404 (84 %) |

Sur un résumé, le moteur s'abstient presque toujours : une absence dans un résumé ne prouve rien.
Les deux jugements rendus (PMID 31569689 et 34298491) le sont parce qu'un seul domaine à risque
élevé suffit à fixer le plus mauvais niveau.

## Contrôles du code

| Mesure | Corpus, texte intégral | 2026-S45, texte intégral |
| --- | --- | --- |
| Appréciations lisibles | 25 sur 25 | 10 sur 10 |
| Domaines jugés | 315 | 100 |
| Refus du contrôle | 2 : un jugement favorable dont le passage est introuvable, une certitude GRADE sans passage qui la nomme | 0 |
| Alertes de l'IA | 0 | 0 |

## Seconde mesure, après correction de la lecture (VS-D40)

Décision du porteur du projet au point d'arrêt : corriger la lecture des déclarations placées hors
du corps de l'article, puis remesurer sur texte intégral. Son avis, noté tel quel : « garde en
tête que je trouve tes avis parfois trop sévère ». La consigne de l'IA n'a pas été modifiée
(empreinte 74839e05), pour mesurer l'effet de cette seule correction.

**La correction.** `texte.document_jats` lit maintenant, sur demande, les déclarations de
financement et de liens d'intérêts, les remerciements et les notes placés en tête ou en fin de
fichier. Les références, les annexes et les adresses de correspondance ne sont pas lues.
L'extraction ne demande pas cette lecture. Vérification sans IA (lancement 43370197937) : ces
déclarations existent pour 15 des 25 articles du corpus.

**Ce que la correction change, là où elle porte.** Question 16 d'AMSTAR 2, déclaration des
conflits d'intérêts et du financement :

| 16 revues | Première mesure | Seconde mesure |
| --- | --- | --- |
| Réponse « oui » | 4 | 12 |
| Réponse « non » | 12 | 4 |
| dont « ni financement ni conflits d'intérêts dans le texte fourni » | 9 | 0 |

Sur les 9 revues où l'IA n'avait pas reçu ces déclarations, 7 obtiennent « oui » et citent la
déclaration. Les 4 « non » qui restent disent qu'une seule des deux déclarations manque. L'accord
avec le corrigé sur cette question ne s'améliore presque pas (2 sur 8, puis
3 sur 8) : trois corrigés répondent « non » là où le moteur lit une déclaration.

**Le résultat global ne s'améliore pas** (lancement 43370405955) :

| Jugement global, 25 articles | Première mesure | Seconde mesure |
| --- | --- | --- |
| Identique au corrigé | 11 | 11 |
| À un cran du corrigé | 7 | 6 |
| Plus sévère de deux crans ou plus | 6 | 7 |
| Plus favorable de deux crans ou plus | 0 | **0** |
| Non évaluable | 1 | 1 |
| **À un cran au plus** | 18 sur 25 (72 %) | **17 sur 25 (68 %)** |
| Plus mauvais niveau de l'échelle donné à | 21 articles | 22 articles |
| Articles bien notés par leur revue, reconnus à un cran près | 1 sur 7 | 0 sur 7 |
| Domaines identiques au corrigé, AMSTAR 2 | 84 sur 128 | 80 sur 128 |
| Domaines identiques au corrigé, QUADAS-2 | 13 sur 44 | 14 sur 44 |
| Domaines identiques au corrigé, RoB 2 | 5 sur 10 | 6 sur 10 |
| Refus du contrôle | 2 | 3 |

**Seuils (VS-D39) : au moins 70 % à un cran au plus, non atteint à la seconde mesure ; aucun
jugement plus favorable de deux crans, atteint.** Une réponse constante, « le plus mauvais
niveau », obtient toujours 18 sur 25.

**L'écart entre les deux mesures tient à un seul article, et au hasard de l'IA.** La revue
PMID 36316416, notée « modérée » par le corrigé, passe de « faible » à « très faible ». Son texte
était le même aux deux mesures : aucune déclaration n'y a été ajoutée. L'IA a répondu autrement à
trois questions, dont deux critiques.

**Stabilité, mesurée pour la première fois.** Dix articles avaient exactement le même texte et la
même consigne aux deux mesures :

| Outil | Articles au texte identique | Jugements par domaine qui changent |
| --- | --- | --- |
| AMSTAR 2 | 6 | 9 sur 96 |
| QUADAS-2 | 3 | 1 sur 21 |
| RoB 2 | 1 | 1 sur 5 |
| Ensemble | 10 | **11 sur 122 (9 %)** |

Avec AMSTAR 2, où deux « non » critiques suffisent pour « très faible », une réponse sur dix qui
change suffit à faire changer le niveau d'un article. Un écart d'un article entre deux mesures ne
veut donc rien dire : le résultat est au niveau du seuil, ni franchement au-dessus, ni franchement
en dessous.

Pour les 15 articles dont le texte a été complété, 24 jugements changent sur 193, dont 8 à la
question 16. La part due à la nouvelle lecture et la part due au hasard ne sont pas séparées.

## Dix publications réelles de 2026-S45

Dix publications de kinésithérapie sous licence CC BY, appréciées sur leur texte intégral et
classées. Le détail, domaine par domaine, est dans
[`2026-11-13-appreciation-s45.json`](2026-11-13-appreciation-s45.json), sans les passages des
articles. Le porteur du projet les relit sur une page privée, hors du dépôt.

| PMID | Type | Outil | Jugement de l'outil | Étiquette candidate | Étiquette publiée | Catégorie |
| --- | --- | --- | --- | --- | --- | --- |
| [42980682](https://pubmed.ncbi.nlm.nih.gov/42980682/) | Essai randomisé | RoB 2 | risque élevé | préliminaire | préliminaire | 2 |
| [42987112](https://pubmed.ncbi.nlm.nih.gov/42987112/) | Essai randomisé | RoB 2 | risque élevé | préliminaire | préliminaire | 3 |
| [42993769](https://pubmed.ncbi.nlm.nih.gov/42993769/) | Essai randomisé | RoB 2 | risque élevé | préliminaire | préliminaire | 3 |
| [42975150](https://pubmed.ncbi.nlm.nih.gov/42975150/) | Étude diagnostique | QUADAS-2 | risque élevé | préliminaire | préliminaire | 3 |
| [42979604](https://pubmed.ncbi.nlm.nih.gov/42979604/) | Étude diagnostique | QUADAS-2 | risque élevé | préliminaire | préliminaire | 3 |
| [42999635](https://pubmed.ncbi.nlm.nih.gov/42999635/) | Étude diagnostique | QUADAS-2 | risque élevé | préliminaire | préliminaire | 3 |
| [42968433](https://pubmed.ncbi.nlm.nih.gov/42968433/) | Méta-analyse | AMSTAR 2 | confiance très faible | préliminaire | préliminaire | 4 |
| [42969067](https://pubmed.ncbi.nlm.nih.gov/42969067/) | Méta-analyse | AMSTAR 2 | non évaluable | non évaluable | préliminaire | 3 |
| [42969580](https://pubmed.ncbi.nlm.nih.gov/42969580/) | Revue systématique | AMSTAR 2 | confiance très faible | préliminaire | préliminaire | 3 |
| [42969584](https://pubmed.ncbi.nlm.nih.gov/42969584/) | Revue systématique | AMSTAR 2 | confiance faible | préliminaire | préliminaire | 2 |

## Retour du comité d'experts sur les dix fiches (13 novembre 2026)

Avis déclaré, reçu du porteur du projet après une relecture des dix fiches (VS-D46). Ce n'est pas
un corrigé. La session l'a recoupé avec les jugements du moteur pour 9 fiches, et avec les résumés
PubMed pour 6 (fiches 1, 2, 4, 6, 7 et 9). Le texte intégral n'a pas pu être relu : Europe PMC est
injoignable depuis l'environnement de développement. La fiche 8 n'a pas été recoupée (seul son
titre est connu).

| Observation du comité | Recoupement |
| --- | --- |
| La grille ne convient pas au plan réel (fiches 1, 4, 6, 8, 9) | **Confirmé pour 1, 4, 6, 9.** Fiche 1 : le titre dit « quasi-randomised » et PubMed l'étiquette « Randomized Controlled Trial » ; ce cas avait été signalé le 12 novembre, sans correction. Fiche 9 : le moteur a lui-même relevé une affectation alternée, puis appliqué RoB 2. Fiche 4 : revue descriptive jugée « non » parce que la question ne précise pas de comparateur. Fiche 6 : le résumé dit que des modèles diagnostiques sont construits. Fiche 8 : non recoupée |
| Un critère non rapporté est pris pour un défaut | **Confirmé.** Fiche 3 : « non » parce que les méthodes « ne précisent pas » la gestion des mesures répétées. Corpus : 9 revues sur 16 avaient reçu « non » à la question 16 faute de déclarations dans le texte fourni. Cause : la consigne d'appréciation fait écrire « non » quand le texte intégral se tait |
| Risque de biais, qualité, certitude et importance sont confondus | **Confirmé pour les trois premiers** : un seul axe « qualité » alimente l'étiquette et met sur la même échelle le risque de biais d'une étude et la fiabilité de la méthode d'une revue. L'importance est déjà indépendante : la catégorie est proposée sans voir la qualité |
| Fiche 2 : comparaison entre volontaires sains simulant une faiblesse et patients | **À corriger.** D'après le résumé PubMed, l'étude ne compte aucun patient : 42 volontaires sains. La limite est plus grave que décrite. Le moteur a jugé l'applicabilité « sans réserve » : erreur du moteur |
| Fiche 5 : l'absence d'insu ne doit pas donner « risque élevé » aux écarts aux interventions | **Non constaté.** Le moteur a mis « quelques réserves » sur ce domaine ; le « élevé » porte sur la mesure du critère |
| Conclusions trop affirmatives | **Non constaté dans le texte publié** : les synthèses publiées des fiches 1, 5 et 9 sont prudentes. Le défaut est dans l'appréciation |
| Fiche 7 : « non évaluable » non conforme à AMSTAR 2, suppléments à récupérer | **Confirmé.** Le moteur écrit que les suppléments manquent ; la règle du code rend le jugement global « non évaluable ». Une fourchette répond mieux |
| Fiche 10 : analyse convaincante, biais de vérification partielle bien identifié | **Confirmé** : le moteur classe le domaine « flux et délais » à risque élevé pour cette raison |
| Traçabilité | **Déjà en place** : jugement, justification, passage, emplacement. **Manquent** : un niveau de confiance et la liste des informations manquantes. Non relevé par le comité : l'IA n'est pas stable (voir la seconde mesure) |

La sévérité n'est pas expliquée par la seule inadéquation des grilles : sur des études diagnostiques
bien classées du corpus, le moteur reste plus sévère que le corrigé des revues (16 domaines de
biais sur 23, première mesure).

## L'étiquette candidate (VS-D14)

La règle candidate part de la qualité méthodologique : élevée donne « solide », moyenne
« modéré », faible « préliminaire », avec les plafonds déjà validés (un essai isolé ou une étude
diagnostique n'est jamais « solide »).

| Articles | « solide » | « modéré » | « préliminaire » | Non évaluable |
| --- | --- | --- | --- | --- |
| Corpus, texte intégral (25) | 0 | 2 | 22 | 1 |
| 2026-S45, texte intégral (10) | 0 | 0 | 9 | 1 |
| Pour comparaison : étiquettes publiées en 2026-S45 (710 fiches, moteur actuel) | 0 | 58 | 652 | sans objet |

Tant que le jugement global est presque toujours au plus bas, cette règle n'apporte rien de plus
que l'étiquette actuelle. Elle n'est pas branchée sur la veille et reste à arbitrer.

## Catégories d'importance

Trente publications de 2026-S45 classées à partir du titre et du résumé. Aucun corrigé n'existe
pour l'importance : cette mesure décrit, elle ne note pas.

| Catégorie | Publications |
| --- | --- |
| 1, évolution potentielle des pratiques | 3 |
| 2, apport scientifique important | 7 |
| 3, actualisation des connaissances | 17 |
| 4, veille complémentaire | 3 |

- Les 30 publications portent aujourd'hui le verdict « à surveiller » : la catégorie les
  départage, ce que le verdict actuel ne fait pas.
- Aucun écart relevé par le contrôle : aucune catégorie ramenée à une valeur prudente, aucun
  chiffre absent du titre et du résumé.
- Le sens pour la pratique (« confirme » ou « remet en question ») n'est rempli que 2 fois sur 30.
- **La catégorie ne tient pas compte de la qualité.** Les trois publications classées en
  catégorie 1 sont deux essais isolés (PMID 42968156, 42972476) et une méta-analyse de
  phytothérapie (PMID 42973526). Leur qualité n'a pas été appréciée. Les définitions des quatre
  catégories écrites dans `classement.txt` sont une proposition de la session de développement,
  à valider par le porteur du projet.

## Coût

| Lancement | Coût réel |
| --- | --- |
| 43363536857, sans IA | 0 $ |
| 43364297944, essai court | 0,07 $ |
| 43364759666, mesure complète | 0,88 $ : résumé seul 0,25 $, texte intégral 0,43 $, dix publications de 2026-S45 0,15 $, trente classements 0,06 $ |

| 43370197937, vérification sans IA | 0 $ |
| 43370405955, seconde mesure | 0,43 $ : 25 articles sur texte intégral |

Total : **1,38 $** sur l'enveloppe de 2,43 $ (VS-D38). Reste 1,05 $. Les estimations annoncées
avant les deux mesures étaient de 1,78 $ et de 0,90 $ ; les coûts réels, de 0,88 $ et de 0,43 $.

Coût par article : 0,007 $ sur résumé, 0,017 $ sur texte intégral, 0,002 $ pour un classement.

## Limites

- **Le corpus contient surtout des articles mal notés.** Aucune revue notée « élevée », aucun
  essai à risque faible, seulement 7 articles notés deux crans au-dessus du plus bas. C'est ce
  qui rend le score global peu parlant.
- **Deux essais randomisés seulement** sur texte intégral : RoB 2 n'est pas mesuré. **AGREE II
  n'est pas mesuré du tout** : aucune recommandation dans le corpus.
- **Le corrigé est un avis, pas une vérité.** Il vient des auteurs d'une revue, parfois plus
  indulgents que la règle de l'outil. Les corrigés QUADAS-2 viennent de deux revues seulement.
- **Aucun humain n'a relu** ni les corrigés, ni les appréciations.
- **Le choix des articles n'est pas un tirage au sort** : il dépend des revues sources qui citent
  des études sous licence CC BY.
- **Deux mesures seulement, et une IA instable** : 9 % des jugements par domaine changent quand
  rien d'autre ne change. Les dix publications de 2026-S45 n'ont été appréciées qu'une fois, avec
  l'ancienne lecture.
- **Les annexes et les fichiers joints d'un article ne sont toujours pas lus** : une liste d'études
  exclues ou une équation de recherche placée là reste invisible.
- Les précisions du bloc « appreciation » (clés des domaines, valeurs, jugement de l'outil) ont
  été déclarées au dépôt de coordination (CHG-2026-0009), puis inscrites dans `docs/FICHE_V2.md`.
  La déclaration est à l'état « proposé » : le portail et Évalys n'ont pas encore répondu.

## Suite proposée

À décider par le porteur du projet.

1. **Ne brancher sur la veille ni le jugement global, ni l'étiquette candidate**, dans leur état
   actuel.
2. **Relire les dix fiches** : dire si le moteur est trop sévère, ou si les corrigés sont trop
   indulgents.
3. **Corriger le défaut de lecture** des déclarations de fin d'article, puis remesurer sur texte
   intégral : fait le 13 novembre 2026 (VS-D40), voir la section « Seconde mesure ».
4. **Compléter le corpus avec des articles bien notés** avant de conclure sur la capacité du
   moteur à reconnaître une bonne étude.
5. **Régler la sévérité seulement après la relecture** : régler la consigne sur les articles du
   corpus, puis remesurer sur ces mêmes articles, flatterait le score.
6. **Réduire l'effet du hasard** avant toute bascule : par exemple apprécier chaque article deux
   fois et ne garder un jugement que s'il est stable. Coût doublé ; non décidé.
