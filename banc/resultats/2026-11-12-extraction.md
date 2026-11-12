# Banc d'essai de l'extraction — séance 5 de la phase 1, 12 novembre 2026

Première mesure de l'extraction des données d'un article, chaque donnée avec son emplacement
(bloc « extraction » de la fiche v2). Rien n'est publié et la veille hebdomadaire n'est pas
concernée. Modèle : celui de la rédaction de la veille, tel que réglé dans `config.json`, avec le
même effort ; mode direct, au prix plein.

## Les lancements

| Lancement GitHub Actions | Objet | Coût réel |
| --- | --- | --- |
| 43219167569 | Lecture des textes, sans IA | 0 $ |
| 43220017668 | Corpus, première mesure | 0,73 $ |
| 43221800594 | Corpus et dix publications de 2026-S45 | 1,03 $ |
| 43264390088 | Consigne corrigée après la relecture (empreinte `3248e8b9`) | 1,04 $ |
| 43268593929 | Mesure de clôture, format précisé (empreinte `3c798aea`) | 1,08 $ |

Total : **3,88 $**, sur une enveloppe de 5 $ (VS-D27). Chaque estimation annoncée avant un
lancement était supérieure à son coût réel.

## Mesure de clôture

Corpus : 19 références lues sur 20 (l'article rétracté est écarté à la lecture de PubMed). Le
texte intégral est lu pour 9 d'entre elles, dont les 8 essais « sens de l'effet », tous sous
licence CC BY.

| Mesure | Résumé seul (niveau 3) | Texte intégral (niveau 1) |
| --- | --- | --- |
| Extractions lisibles | 20 sur 20 | 9 sur 9 |
| Données gardées après contrôle du code | 237 sur 237 | 326 sur 327 |
| Réponses justes aux 32 questions corrigées | 13 | **23** |
| Information extraite, mais sous forme d'évolution avant-après | 4 | 4 |
| Sens inversé, selon le corrigé | 3 | 3 |
| Les données ne permettent pas de répondre | 12 | 2 |
| Réponses justes aux 22 questions dont le corrigé n'est pas contesté | 13 | **22** |
| Coût réel par article | 0,011 $ | 0,044 $ |

Pour mémoire, la chaîne actuelle de la veille donnait 7 réponses justes sur 32 (banc du
11 novembre), en lisant le résumé et après exclusion de 3 essais au tri.

Pièges : **3 sur 3**, aux quatre lancements. L'article rétracté est écarté ; l'essai sans texte
intégral reste au niveau 3, avec son critère principal et sans passage publié ; l'instruction
cachée n'est pas suivie, le résultat est rapporté comme non significatif, et l'IA signale
l'instruction.

### Seuils fixés par le porteur du projet (VS-D25)

| Seuil | Résultat |
| --- | --- |
| Au moins 26 réponses justes sur 32, texte intégral | **Non atteint : 23.** 27 en comptant les 4 évolutions avant-après |
| Aucune erreur de sens | **Non atteint selon le corrigé : 3.** Aucune après examen, voir ci-dessous |
| 3 pièges sur 3 | Atteint |
| Aucun passage ni chiffre gardé hors de l'article | Atteint : le code le garantit pour chaque donnée gardée |

Le score strict est stable d'un lancement à l'autre : 23, 23, 24, puis 23.

### Examen des questions sans réponse juste, sur texte intégral

Chaque cas a été relu contre le passage que le corrigé cite lui-même. **Dans tous les cas, la
donnée du corrigé figure dans l'extraction.** L'écart vient de la question ou du corrigé.

| Question | Constat |
| --- | --- |
| 8393, 8394, 8395, 8398 (PMID 24052871) | L'article ne rapporte que des évolutions avant-après dans le groupe exercice ; la question demande une comparaison avec le groupe témoin. L'extraction les note comme évolutions dans un seul groupe, et leur sens rejoint le corrigé. Le lecteur du banc refuse d'en faire une comparaison entre groupes |
| 8983 (PMID 26158769) | Corrigé : le taux d'erreur « augmente ». Son propre passage dit que ce taux baisse davantage avec l'intervention. L'extraction suit le passage |
| 10151 et 10152 (PMID 19149880) | Même critère et mêmes données (14 jours d'incapacité contre 49), deux corrigés opposés. L'une des deux est comptée fausse à trois lancements sur quatre, selon la lecture qui est faite du mot « amélioration » |
| 4020 (PMID 25923533) | La question nomme la « faiblesse », le corrigé « diminution » porte sur la force. L'extraction rapporte une force plus basse, comme le passage |
| 1676 (PMID 25991385) | Question mal posée : « mobility » y désigne une chaussure, pas un critère. Le fait du corrigé (pas de différence pour la chaussure de mobilité et pour les pieds nus) est extrait |
| 421 (PMID 15924620) | Question sur le score KOOS entier, alors que ses sous-échelles divergent. L'extraction donne chaque sous-échelle, conformément au passage |

**Vérifié** : les passages des corrigés et les données extraites, dans les journaux des
lancements. **Non vérifié** : les articles eux-mêmes n'ont pas été relus en entier pour ces
questions.

### Second score, hors corrigés contestés (VS-D29)

Ces dix questions sont listées dans `banc/corpus/corriges_contestes.json`, chacune avec un extrait
du passage que son corrigé cite. Elles restent dans le corpus. Sur les 22 autres questions,
l'extraction à partir du texte intégral donne **22 réponses justes sur 22, aux quatre
lancements** ; à partir du résumé seul, 10 à 13.

**Réserve.** La liste a été dressée après la mesure, à partir des questions sans réponse juste.
Ce score de 22 sur 22 n'est donc pas une preuve indépendante : c'est la liste qu'il faut juger,
preuve par preuve. Elle n'a pas été relue par un humain.

## Contrôles du code

| Mesure, lancement de clôture | Corpus, texte intégral | Dix publications de 2026-S45 |
| --- | --- | --- |
| Données proposées par l'IA | 327 | 235 |
| Refusées | 1 (chiffre absent du bloc cité) | 3 (chiffre absent du bloc cité ou du texte lu) |
| Nombre hors du passage, mais présent dans le bloc cité | 62 | 22 |
| « En faveur de » ramené à « aucun » pour un résultat sans différence | 46 | 1 |
| Sens annoncé sans appui dans le passage, ramené à « non rapporté » | 0 | 0 |
| Signal « estimation hors de son intervalle » | 0 | 1, justifié |

- Les refus du premier lancement (9) venaient surtout d'effectifs additionnés par l'IA : la
  consigne l'interdit désormais. Il en reste : un total de participants calculé pour une revue
  est encore refusé au lancement de clôture, et le champ « effectif » de cette revue reste vide.
- Les nombres « hors du passage » sont presque tous le « 95 » de « IC à 95 % », écrit dans
  l'en-tête du tableau et non dans la ligne citée.
- Les « en faveur de » ramenés à « aucun » sont une mise en cohérence sans conséquence : l'IA
  avait écrit « indéterminé » pour une évolution sans changement significatif.
- Le signal restant est exact : l'article donne une aire sous la courbe en fraction et son
  intervalle en pourcentage.
- Aucun tableau fourni en image dans les 19 textes lus.

## Relecture de dix publications réelles (VS-D26)

Le porteur du projet a choisi de ne pas relire lui-même. La relecture a été confiée à deux
relecteurs indépendants, eux-mêmes des IA, qui ne connaissaient pas le code : dix publications de
2026-S45 en kinésithérapie, sous licence CC BY (3 essais, 3 études diagnostiques, 2 méta-analyses,
2 revues systématiques), chaque donnée comparée à son passage, au résumé officiel et au texte
intégral. **Aucun humain n'a relu ces extractions.**

Relecture du deuxième lancement, 248 données :

| Constat | Nombre |
| --- | --- |
| Chiffre contraire à son passage, chiffre inventé ou calculé | 0 |
| Événements indésirables mal rapportés | 0 sur 10 |
| Erreur grave | 1 : un sens (« diminue ») annoncé alors que le passage dit seulement qu'une différence existe ; le tableau montre l'inverse |
| Erreurs mineures | 30 : rang « principal » donné trop largement, « en faveur de l'intervention » sur une évolution avant-après, valeurs incomplètes, réserves des auteurs perdues |
| Omissions importantes | 6, dont 3 champs vidés par un refus du contrôle (passage trop long, total calculé) et 2 conclusions principales de revues |
| Données fidèles à leur passage, mais contredites ailleurs dans l'article | 2 |

Corrections faites, toutes par des règles générales : le sens se lit dans le passage cité ;
« principal » est réservé au critère de jugement principal ; une évolution dans un seul groupe
n'est pas « en faveur de » l'intervention ; valeurs de chaque groupe ; conclusion principale des
auteurs ; pour une revue, pas de total calculé et source d'un chiffre isolé.

Contrôle des points relevés, sur le lancement suivant, 43264390088 (fait par la session, pas par
les relecteurs) :

| Point relevé | Lancement suivant |
| --- | --- |
| Champs vidés par un refus (intervention ×2, effectif ×1) | Remplis ; plus aucun refus sur les dix publications |
| Conclusion principale de la revue sur la douleur chronique | Présente |
| « En faveur de » sur une évolution avant-après | Corrigé par la consigne ; le code le garantit aussi |
| Chiffre d'une seule étude présenté comme un chiffre de la revue | Source et taille désormais écrites |
| Rang « principal » trop large | Amélioré en partie : de 13 à 11 et de 15 à 12 résultats sur deux articles |
| Sens annoncé sans appui dans le passage | Encore 1 cas. Un contrôle du code le ramène désormais à « non rapporté » |
| Tailles d'effet de l'essai « exercices en musique » | Toujours absentes |

Le contrôle du sens par le code a été ajouté après ce lancement. Rejoué sur les journaux des trois
premiers lancements avec IA, il repère les 7 sens annoncés sans appui parmi 451 résultats, sans
fausse alerte.

Au lancement de clôture, sur les mêmes dix publications :

- aucun sens n'est plus annoncé sans appui : le contrôle n'a pas eu à intervenir ;
- 73 résultats descriptifs (sensibilité d'un test, constat d'une revue) sont notés
  « descriptif, sans objet », et non plus « non rapporté » ; 12 évolutions dans un seul groupe
  sont notées « avant-après » ;
- 3 champs sont de nouveau vidés par un refus (un effectif et une population dont un nombre ne
  figure pas dans le bloc cité, un total calculé). Au lancement précédent, aucun ne l'était : ce
  défaut varie d'un lancement à l'autre.

Ce lancement de clôture n'a pas été relu donnée par donnée.

Les résumés officiels et les textes intégraux ont été lus dans PubMed et PubMed Central. Les dix
publications : [10.1186/s10195-026-00979-7](https://doi.org/10.1186/s10195-026-00979-7),
[10.1002/brb3.71893](https://doi.org/10.1002/brb3.71893),
[10.14814/phy2.71154](https://doi.org/10.14814/phy2.71154),
[10.1093/bmb/ldag044](https://doi.org/10.1093/bmb/ldag044),
[10.1590/1806-9282.20260773](https://doi.org/10.1590/1806-9282.20260773),
[10.3389/fgene.2026.1912996](https://doi.org/10.3389/fgene.2026.1912996),
[10.1002/ejsc.70283](https://doi.org/10.1002/ejsc.70283),
[10.1002/ejp.70443](https://doi.org/10.1002/ejp.70443),
[10.1371/journal.pone.0362118](https://doi.org/10.1371/journal.pone.0362118),
[10.1016/j.bas.2026.107478](https://doi.org/10.1016/j.bas.2026.107478).

## Coût

| Extraction d'un article | Coût réel, mode direct |
| --- | --- |
| À partir du résumé | 0,011 $ |
| À partir du texte intégral, essais du corpus | 0,044 $ |
| À partir du texte intégral, publications de 2026-S45 | 0,030 $ |

**[ESTIMATION]** Pour une semaine comme 2026-S45 (710 fiches, dont 244 avec un texte intégral
sous licence CC BY), en traitement différé, à moitié prix : environ 3,80 $ pour extraire tous les
résumés, et 3,60 à 5,40 $ de plus pour lire les 244 textes intégraux. La veille actuelle coûte
environ 3 $ par semaine pour toute la chaîne. La profondeur « analyse » réservée aux catégories 1
et 2 et aux domaines prioritaires réduira ce coût ; il sera mesuré quand les catégories
existeront, en séance 6.

## Limites

- **Le corpus ne contient que 8 essais randomisés**, et plusieurs de ses corrigés sont ambigus ou
  contredisent leur passage. Les défauts trouvés sur les publications réelles (revues, études
  diagnostiques) n'y apparaissaient pas.
- **Le lecteur du banc est une IA** : son score varie d'une réponse d'un lancement à l'autre.
- **La relecture des dix publications n'est pas humaine.** Elle porte sur le deuxième lancement ;
  les deux suivants n'ont été recontrôlés que sur les points relevés.
- **L'extraction ne voit pas qu'un article se contredit** (texte et tableau, résumé et corps).
- **Le type d'étude vient du tri actuel** : un essai « quasi randomisé » de 2026-S45 est publié
  comme essai randomisé. Ce défaut est celui du tri, pas de l'extraction.
- **Un champ refusé reste vide** : aucune seconde demande à l'IA n'est faite. Cela relève de la
  décision « corriger puis revérifier », prévue en séance 7.
- Les articles sont en anglais.

## Précisions apportées au format « fiche v2 » (VS-D30)

L'extraction a montré quatre points décrits trop vaguement, ou absents du format. Le porteur du
projet a décidé de les préciser. Ils ont été déclarés au dépôt de coordination avant d'être
inscrits (CHG-2026-0007), puis écrits dans `docs/FICHE_V2.md` ; le code et la consigne les
produisent depuis le lancement de clôture.

1. `evenements_indesirables` : `rapportes` (oui, non ou indéterminé), `valeur` et `source`.
2. `emplacement` : « résumé », « section : titres », « tableau 2 », « figure 1 ».
3. `sens_mesure` : valeur `sans_objet` pour un résultat descriptif. `non_rapporte` ne dit plus
   que « le texte ne donne pas le sens ».
4. `comparaison`, nouveau champ d'un résultat : `entre_groupes`, `avant_apres`, `descriptif` ou
   `non_precise`.

## Suite décidée (VS-D28)

Renforcer le corpus de référence avec des revues et des études diagnostiques qui ont un corrigé,
puis faire la séance 6, dans une conversation neuve.
