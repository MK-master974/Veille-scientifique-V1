# RoB 2, QUADAS-2, AMSTAR 2 : la mesure qui tranche (lot 2) — 14 novembre 2026

Décisions VS-D74 à VS-D76, après le diagnostic de VS-D73
([2026-11-14-diagnostic-quatre-grilles.md](2026-11-14-diagnostic-quatre-grilles.md)). Rien n'est publié et
la veille hebdomadaire n'est pas concernée : l'appréciation n'est appelée que par le banc d'essai.

- **Moteur mesuré :** le moteur actuel, sans correction. La consigne est `appreciation.txt`, empreinte
  4ce7fb70, inchangée depuis la séance 7. Les règles du code pour ces trois grilles n'ont pas changé non
  plus (seuls des ajouts pour ROBINS-I).
- **Modèle :** celui de la rédaction de la veille, réglé dans `config.json`.
- **Lancements :**
  - 43580024170 : vérification du corpus, sans IA, 0 $ ;
  - 43580529821 : estimation, sans IA, 0 $ ;
  - 43580986912 : mesure, 0,405 $.

## En bref

- **Seuil de VS-D75 : non atteint.** Sur les 42 articles mesurés avec cette consigne, le moteur donne le
  jugement global de la revue pour **14 articles**. Le seuil en demandait au moins 21, et une réponse fixe
  en obtient **20**. Aucun jugement n'est trop favorable de deux crans.
- **Sur les 17 articles neufs, que les revues jugent favorablement, le moteur n'en retrouve qu'un.** Pour
  les 16 autres, il est plus sévère que la revue, de deux crans ou plus pour 12. La mesure tranche : le
  moteur ne reproduit pas le jugement des revues. Il ne faisait pas mieux qu'une réponse fixe au niveau le
  plus sévère, et cela ne venait pas seulement d'un corpus dominé par les niveaux sévères.
- **Deux causes distinctes**, vérifiées dans les journaux :
  - **AMSTAR 2.** Le niveau tient le plus souvent à ce que l'article ne dit pas : liste des études
    exclues, souvent en supplément ; effet du risque de biais ; financement des études incluses. La
    fourchette couvre plusieurs niveaux pour 25 revues sur 27. Aucune des deux lectures extrêmes ne colle
    aux revues :
    - lecture stricte (chaque silence compte comme le pire) : 11 exactes sur 27 ;
    - lecture indulgente (chaque silence compte comme favorable) : 5 sur 27, et 7 trop favorables.
  - **RoB 2 et QUADAS-2.** La fourchette est étroite pour les 15 études : le moteur ne manque pas
    d'information, il juge plus sévèrement que les revues. Dans ces 6 articles neufs, les jugements
    sévères s'appuient sur des faits de l'article et suivent la lettre de l'outil (détail plus bas). Les
    revues paraissent plus clémentes. C'était déjà le cas pour QUADAS-2 au lot 1 et pour ROBINS-I.
- **Coût réel : 0,405 $.** Estimation prudente : 0,64 $. Plafond : 0,75 $. Enveloppe de VS-D76 : 0,76 $.
  **Reste : 0,355 $.**

## Le corpus neuf (VS-D74)

17 articles, et non les 20 prévus, ajoutés au corpus « qualité » (`corpus/qualite_lisible.json`,
`"lot": 2`) sans IA, par la méthode de VS-D32. Tous sont sous licence CC BY, avec un texte intégral dans
PubMed Central, et sont jugés dans un tableau étude par étude par une revue elle-même sous licence CC BY.

| Grille | Articles | Corrigé des revues | Revues sources |
| --- | --- | --- | --- |
| AMSTAR 2 | 11 revues | « élevée » 4, « modérée » 7 | 4 revues de revues |
| RoB 2 | 3 essais | « faible », tous les domaines | 3 revues |
| QUADAS-2 | 3 études diagnostiques | « faible », quatre domaines de risque de biais | 1 revue |

**Pourquoi 17 et non 20 :**
- le repérage a parcouru 120 revues de revues AMSTAR 2, 240 revues RoB 2 et 240 revues QUADAS-2 ;
- les tableaux étude par étude, lisibles et sous licence ouverte, sont rares pour RoB 2 et QUADAS-2 : le
  plus souvent le jugement est une figure, et une grande revue emploie des symboles qu'on ne peut pas
  distinguer ;
- cinq candidats ont été écartés, avec leur motif, dans `ecartees_lot_2`.

La règle de VS-D74 laissait AMSTAR 2 compléter les autres grilles.

**Vérification (lancement 43580024170), 17 sur 17 :**
- licences conformes ;
- niveaux recopiés à l'identique depuis la ligne du tableau source ;
- texte intégral lu.

Le corrigé n'est pas relu par un humain.

## Résultats

**Seuil de VS-D75**, fixé avant la mesure, en lecture stricte, sur les 42 articles mesurés avec la même
consigne : les 25 du lancement 43378868507 et les 17 neufs.

| Seuil | Mesuré | Atteint |
| --- | --- | --- |
| Au moins 50 % des jugements globaux identiques au corrigé | 14 sur 42 (33 %) | non |
| Plus de jugements identiques qu'une réponse fixe (le niveau le plus fréquent des corrigés de chaque grille : AMSTAR 2 « modérée », QUADAS-2 « faible », RoB 2 « faible ») | 14 contre 20 | non |
| Aucun jugement plus favorable que le corrigé de deux crans | 0 | oui |
| Fourchette (VS-D50) : corrigé dans la fourchette, qui couvre deux niveaux au plus, pour 70 % des articles | 10 sur 42 | non |

**Par lot :**

| | Lot 1 (25, corrigés surtout sévères) | Lot 2 (17, corrigés favorables) |
| --- | --- | --- |
| Identiques au corrigé | 13 | 1 |
| Réponse fixe du lot | 13 | 13 |
| Plus sévères de deux crans ou plus | 5 | 12 |

**Lot 2, article par article** (lecture stricte ; « meilleur » : chaque silence compté comme favorable) :

| Grille | PMID | Corrigé | Moteur | Meilleur |
| --- | --- | --- | --- | --- |
| AMSTAR 2 | 29973193 | élevée | faible | élevée |
| AMSTAR 2 | 31267483 | élevée | faible | élevée |
| AMSTAR 2 | 32112628 | élevée | très faible | faible |
| AMSTAR 2 | 34770049 | élevée | très faible | élevée |
| AMSTAR 2 | 31552570 | modérée | faible | faible |
| AMSTAR 2 | 32311937 | modérée | faible | élevée |
| AMSTAR 2 | 35147898 | modérée | très faible | faible |
| AMSTAR 2 | 36070150 | modérée | **modérée** | élevée |
| AMSTAR 2 | 36836403 | modérée | très faible | élevée |
| AMSTAR 2 | 37065695 | modérée | très faible | faible |
| AMSTAR 2 | 37199654 | modérée | très faible | très faible |
| RoB 2 | 19068113 | faible | quelques réserves | quelques réserves |
| RoB 2 | 34768404 | faible | quelques réserves | quelques réserves |
| RoB 2 | 40338913 | faible | élevé | élevé |
| QUADAS-2 | 35505425 | faible | élevé | élevé |
| QUADAS-2 | 39598099 | faible | élevé | élevé |
| QUADAS-2 | 40100278 | faible | élevé | élevé |

**Plan d'étude** (mesuré en même temps) : la grille du corrigé est retrouvée pour 16 articles sur 17.
L'essai 19068113 est classé « autre » : l'article dit que les patients ont été « randomly assigned »,
mais ne décrit pas le procédé. Ce défaut n'avait pas été vu. L'appréciation, elle, a été demandée avec la
grille du corrigé.

## Relecture critique (VS-D53)

Relu : les domaines défavorables des 17 articles neufs, avec leur justification et leur passage. Le
passage est vérifié par le code. Ce que je n'ai pas pu vérifier : les suppléments des revues, que ni le
moteur ni moi n'avons lus, et le texte du protocole de chaque revue.

**RoB 2** (3 essais). Les jugements suivent l'algorithme de l'outil :
- **19068113 et 34768404 :** « quelques réserves » parce que l'article ne décrit pas le masquage de
  l'affectation, ou ne dit pas que l'essai a été enregistré avant l'analyse. Le guide de RoB 2 donne
  « some concerns » quand cette information manque.
- **34768404, deux domaines discutables :** « données manquantes » (un seul retrait rapporté) et
  « écarts aux interventions » (essai en double insu) seraient défendables en « faible ».
- **40338913 :** « élevé » pour la mesure du critère. Le critère est un questionnaire rempli par des
  participants qui savent quel groupe ils ont reçu. C'est le cas typique du risque élevé dans RoB 2. La
  revue a jugé « faible ».

**QUADAS-2** (3 études). Chaque « élevé » s'appuie sur un fait de l'article :
- exclusion de patients après coup : images insuffisantes, histologie non concluante, cancer non visible
  à l'IRM ;
- seuil choisi d'après les données de l'étude ;
- référence différente selon les patients (cystectomie ou résection).

Deux réserves :
- pour 39598099, l'exclusion des patients opérés avant l'IRM ressemble davantage à un critère
  d'inclusion qu'à une exclusion après coup ;
- pour 40100278, la « référence imparfaite » s'appuie sur une phrase générale de l'introduction.

**AMSTAR 2** (11 revues). Les jugements « non » appuyés par un passage sont le plus souvent conformes à
l'outil :
- protocole non enregistré avant l'extraction (35147898) ;
- liste des exclus « disponible sur demande » (31552570) ;
- différence de moyennes pour un critère binaire et définition contradictoire du risque de biais
  (37199654).

Deux sont discutables :
- absence de test de biais de publication avec moins de 10 essais (32112628) ;
- retrait d'une étude extrême (37065695).

Mais le niveau tient surtout aux silences. Cinq revues sur onze n'ont aucune faiblesse critique prouvée :
leur niveau sévère ne vient que de cases « non rapporté » ou « non évaluable ». La question q07 (liste des
études exclues) est inconnue pour 7 revues sur 11 ; pour trois, la justification du moteur dit que la
liste est annoncée dans un supplément.

**Une simulation sans IA, écartée :** si une case critique renvoyée à un supplément valait « oui
partiel », 3 revues changeraient de niveau, et aucune ne deviendrait exacte (11 sur 27 avant comme
après).

## Ce que la mesure établit, et ce qu'elle n'établit pas

- **Établi :** le moteur actuel ne reproduit pas le jugement global des revues pour ces trois grilles. Il
  est plus sévère qu'elles, et d'autant plus que la revue est favorable.
- **Non établi :** que le moteur juge mal. Pour RoB 2 et QUADAS-2, sa sévérité est défendable au regard
  des questions de l'outil. Les revues servent de corrigé, mais elles appliquent l'outil avec plus de
  clémence et ne sont pas relues par un humain. Pour AMSTAR 2, une partie de l'information manque au
  moteur (suppléments) : ni la lecture stricte ni la lecture indulgente ne la remplacent.
- **Conséquence :** rendre le moteur plus clément pour coller aux revues pourrait faire passer le seuil
  sans le rendre plus juste. Toute correction écrite d'après ces 42 articles devrait être mesurée sur des
  articles neufs.
