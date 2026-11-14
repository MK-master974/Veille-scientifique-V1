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
| Banc d'essai de l'extraction (fiche v2) | Écrit le 12 novembre 2026 : `banc_extraction.py`. Quatre mesures faites : `resultats/2026-11-12-extraction.md` |
| Cas « chiffres relevés » : 9 études diagnostiques, 10 méta-analyses, 1 revue systématique, 161 chiffres | Assemblés et vérifiés le 12 novembre 2026 : `corpus/chiffres_releves.json`. Mesure : `resultats/2026-11-12-chiffres-releves.md` |
| Cas « qualité, articles lisibles en entier » : 16 revues (AMSTAR 2), 7 études diagnostiques (QUADAS-2), 2 essais (RoB 2) | Assemblés le 13 novembre 2026 : `corpus/qualite_lisible.json` |
| Banc d'essai de l'appréciation et des catégories d'importance | Écrit le 13 novembre 2026 : `banc_appreciation.py`. Deux mesures faites : `resultats/2026-11-13-appreciation.md`. Séance 7, plan d'étude : deux cycles, plus l'étude des suppléments, `resultats/2026-11-13-seance-7.md` |
| Cas « ROBINS-I » : 38 études non randomisées sous licence CC BY, en trois lots (21, puis 7 et 10 articles neufs, VS-D59 et VS-D65), jugement ROBINS-I d'une revue sous licence CC BY | Assemblés et vérifiés le 14 novembre 2026 : `corpus/robins_i.json`. Mesures et stabilité : `resultats/2026-11-14-robins-i.md` |

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

## Les cas « chiffres relevés »

Pour une étude diagnostique ou une méta-analyse, le corrigé est fait des **chiffres que les
auteurs d'une revue en accès libre ont déjà relevés** dans un tableau (VS-D32) : effectif,
sensibilité et spécificité pour une étude diagnostique ; nombre d'études, effet groupé et bornes de
son intervalle de confiance pour une méta-analyse. Personne ne remplit de corrigé à la main.

- **Sources** : une revue de précision diagnostique pour les études diagnostiques, une revue de
  revues pour les méta-analyses. La revue source et l'article sont sous licence CC BY ou CC0.
- **Assemblage** (`assembler_chiffres.py`, workflow « Corpus, chiffres relevés », sans IA) :
  1. « repérer » : pour chaque revue candidate, ses tableaux, les études que chaque tableau cite
     et la licence de ces études ;
  2. « lire » : les lignes du tableau qui portent sur les études choisies ;
  3. « vérifier » : pour chaque chiffre du corpus, les licences, la recopie (le chiffre est bien
     dans la ligne du tableau source) et sa présence dans l'article lui-même ;
  4. « recalculer » : après une correction des règles, le score est recalculé sur les extractions
     d'un lancement déjà fait, sans nouvel appel à l'IA.
- **Ce qui est gardé** (`corpus/chiffres_releves.json`) : des identifiants, des licences et des
  chiffres. Aucun texte d'article.
- **Règles de comparaison**, fixées avant toute mesure (`chiffres.py`) : le signe est ignoré ;
  l'arrondi est toléré (« 29,56 » correspond à « 29,6 ») ; pour une proportion, une fraction et un
  pourcentage se valent (« 0,94 » et « 94 % »). Rien d'autre n'est toléré.
- **Règle de voisinage.** Un petit nombre se retrouve presque toujours quelque part dans un long
  texte. Les chiffres qui vont ensemble forment donc un groupe : un effet et les bornes de son
  intervalle ; la sensibilité, la spécificité et l'aire sous la courbe d'un même test. Dans
  l'article, un chiffre d'un groupe n'est confirmé qu'à moins de 300 caractères d'un autre chiffre
  de son groupe. Dans l'extraction, une borne d'intervalle n'est retrouvée que dans un résultat qui
  porte aussi son effet.
- **Quatre corrections faites après la première mesure**, publiées avec les deux scores : un zéro
  final n'est pas un arrondi ; un nombre d'études écrit en toutes lettres est lu ; le « 95 » de
  « IC à 95 % » n'est pas une donnée ; une valeur ponctuelle se cherche dans le champ « valeur »
  d'un résultat.
- **Un chiffre absent de l'article est écarté du score avant la mesure**, et compté à part
  (VS-D34) : une revue arrondit, recalcule ou se trompe parfois en recopiant. C'est le code qui le
  constate, sur le texte de l'article, sans regarder ce que l'IA a extrait.
- **Mesure** : le banc de l'extraction cherche chaque chiffre dans la zone attendue des données
  extraites (le champ « effectif », ou les résultats). Aucune IA lectrice : le score ne varie pas
  d'un lancement à l'autre. Seuil : 80 % des chiffres retrouvés à partir du texte intégral.

**Revues sources** (toutes sous licence CC BY), et articles retenus :

| Revue source | Tableaux | Articles du corpus |
| --- | --- | --- |
| PMID 37444127, Int J Environ Res Public Health 2023 : dépistage de la fragilité aux urgences | 3 et 4 | 2 études diagnostiques |
| PMID 35150292, Knee Surg Sports Traumatol Arthrosc 2022 : tests cliniques du ligament croisé antérieur | 2 | 2 études diagnostiques |
| PMID 39014328, BMC Geriatr 2024 : test d'Ishii pour la sarcopénie | 1 et 2 | 3 études diagnostiques |
| PMID 36151550, BMC Musculoskelet Disord 2022 : règle d'Ottawa pour la cheville | 1 et 2 | 2 études diagnostiques |
| PMID 39026375, Syst Rev 2024 : exercices traditionnels chinois et arthrose du genou | 1 et 7 | 4 méta-analyses |
| PMID 42643227, Front Nutr 2026 : glucosamine et arthrose du genou | 1, 4 et 5 | 2 méta-analyses |
| PMID 42947838, Front Psychol 2026 : exercice et équilibre dans la maladie de Parkinson | 2 | 2 méta-analyses |
| PMID 40943700, J Clin Med 2025 : exercice et lombalgie | 1 | 2 méta-analyses |
| PMID 38786366, Healthcare 2024 : exercice et interleukine 6 | 3 | 1 revue systématique sans méta-analyse |

**Choix des articles.** 82 revues candidates ont été trouvées dans PubMed, puis lues sans IA : 62
sont sous licence CC BY avec un texte lisible, et 13 ont un tableau de chiffres qui cite des études
elles-mêmes sous licence CC BY. Neuf ont été gardées : celles dont le tableau donne des chiffres
par étude (et non seulement un décompte), en variant les sujets. Ce choix est fait par la session
de développement, avant toute mesure ; il n'est pas tiré au sort.

**Vérification** (lancement 43284046225, sans IA) : licences conformes pour les 20 articles et les
9 revues ; 161 chiffres sur 161 bien recopiés ; 159 sur 161 confirmés dans leur article. Les deux
autres sont des valeurs calculées par la revue source : ils restent dans le corpus, marqués, et ne
comptent pas dans le score.

**Mesure** (`resultats/2026-11-12-chiffres-releves.md`) : à partir du texte intégral, l'extraction
retrouve 148 à 149 chiffres sur 159, soit 93 % ; à partir du résumé seul, 113. Le seuil de 80 %
est atteint.

**Deux pièges du travail sur des tableaux**, que le code traite : dans une revue source, les
renvois numérotés du tableau ne désignaient pas les études nommées sur la ligne (le nom et l'année
écrits l'emportent ; une ligne dont rien ne concorde est écartée) ; dans une autre, chaque étude
occupait un bloc de lignes.

## Les cas « qualité », sur des textes lisibles

`corpus/qualite_lisible.json` complète `corpus/qualite.json`, dont presque aucun article n'a de
texte intégral ouvert. Il réunit 25 articles sous licence CC BY, avec le jugement déjà porté par
les auteurs d'une revue elle-même sous licence CC BY :

| Outil | Revue source | Articles | Corrigé |
| --- | --- | --- | --- |
| QUADAS-2 | PMID 37444127, dépistage de la fragilité aux urgences (variante QUADAS-C) | 2 études diagnostiques | 4 domaines de risque de biais, 3 d'applicabilité |
| QUADAS-2 | PMID 39367147, logiciels de détection de fractures | 5 études diagnostiques | 3 domaines de risque de biais sur 4, 3 d'applicabilité |
| RoB 2 | PMID 34006560, rééducation après ligamentoplastie | 2 essais | 5 domaines et jugement global, pour un critère de proprioception |
| AMSTAR 2 | PMID 39026375, exercices traditionnels chinois et arthrose du genou | 6 revues | 16 questions et confiance globale |
| AMSTAR 2 | PMID 42643227, glucosamine et arthrose du genou | 2 revues | 16 questions et confiance globale |
| AMSTAR 2 | PMID 42947838, exercice et maladie de Parkinson | 4 revues | Confiance globale |
| AMSTAR 2 | PMID 40943700, exercice et lombalgie | 4 revues | Confiance globale |

Répartition des 16 revues : 8 « très faible », 4 « faible », 4 « modérée », aucune « élevée ».
Les lignes ont été lues sans IA par le workflow « Corpus, chiffres relevés ». Le corrigé n'est pas
relu par un humain.

## Le banc de l'appréciation

`banc_appreciation.py` mesure l'appréciation méthodologique (bloc « appreciation » de la fiche v2)
et la catégorie d'importance.

- **Texte intégral seul par défaut** (depuis la séance 7) : un article n'est apprécié que si son
  texte intégral est sous licence CC BY ou CC0. `"niveaux": "tout"` rejoue aussi l'appréciation
  sur résumé seul.
- **Plan d'étude** (séance 7) : une requête par article lu en entier. Pour le corpus, la grille du
  plan est comparée à celle des auteurs de la revue. Pour 2026-S45, la grille est choisie d'après
  le plan ; sans grille applicable, aucune appréciation n'est demandée.
- **Étude des protocoles et des suppléments** (VS-D49) : `supplements.py`, sans IA et sans coût,
  lancé par `"banc": "supplements"`. Pour chaque article du corpus « qualité » sous licence CC BY :
  éléments de matériel supplémentaire déclarés, familles de numéros de protocole ou de registre
  cités, mentions de fichiers supplémentaires et de listes d'exclus, paquet de fichiers chez Europe
  PMC. Aucun texte d'article et aucun numéro de registre n'est gardé.
- **ROBINS-I** (VS-D54) : `"outils": ["robins_i"]` ne mesure que cette grille, sur
  `corpus/robins_i.json` ; `"lot"` ne mesure qu'un lot de ce corpus (2 ou 3 : articles neufs) ;
  `"plan_temoins"`, avec `"plan_seul"`, ajoute les 6 témoins d'exposition de ce corpus, pour lesquels
  aucune grille ROBINS-I n'est attendue (VS-D70) ;
  `"s45_pmids"` limite 2026-S45 aux publications nommées (les deux essais
  quasi randomisés de la séance 7). Le critère jugé par la revue source est donné à l'IA. Seuils
  fixés avant la mesure (VS-D56), en lecture stricte : au moins 50 % des jugements globaux
  identiques au corrigé, plus qu'une réponse fixe au niveau le plus fréquent du corpus, et aucun
  jugement plus favorable de deux crans. Le seuil « à un cran au plus » de VS-D39 n'est pas repris :
  sur quatre niveaux, une réponse fixe « sérieux » serait à un cran de presque tout.
- **Plan d'étude seul** (VS-D48) : `"plan_seul": true` mesure l'étape sans aucune appréciation ;
  `"plan_externe": true` y ajoute les études diagnostiques du corpus de chiffres relevés, hors du
  corpus « qualité », pour contrôler les définitions sur des articles qui ne les ont pas inspirées.
- **Contrôle du coût** : l'estimation du banc est prudente (entrée comptée au plus haut). Un
  lancement est refusé d'emblée si elle dépasse 1,5 fois le plafond ; ensuite, le coût réel déjà
  dépensé est vérifié avant chaque groupe de requêtes, et un groupe qui dépasserait le plafond
  n'est pas lancé. Deux lancements de la séance 7 se sont arrêtés au contrôle d'estimation sans
  rien dépenser avant ce réglage.
- **Fourchette du jugement global** (séance 7) : le corrigé est-il dans la fourchette, et la
  fourchette est-elle étroite ? Mesure descriptive, sans seuil : un seuil reste à fixer par le
  porteur du projet. Les seuils de VS-D39 portent sur la lecture stricte (un domaine non évalué ou
  non rapporté compte comme le pire jugement possible).
- **Déclarations hors du corps de l'article** (financement, liens d'intérêts) : lues depuis le
  13 novembre 2026. `"sans_declarations": true` rejoue la lecture d'avant.
- **Écart en crans** : le jugement global, calculé par le code, est comparé à celui du corrigé sur
  l'échelle de l'outil (trois crans pour RoB 2 et QUADAS-2, quatre pour AMSTAR 2).
- **Seuils** fixés par le porteur du projet (VS-D39), sur le texte intégral : au moins 70 % des
  jugements à un cran au plus du corrigé, et aucun jugement plus favorable de deux crans.
- **Abstention** : sur résumé seul, la part des domaines notés « non évaluable ».
- **Accord par domaine**, quand le corrigé le donne.
- **Catégories d'importance** : répartition sur des publications réelles de 2026-S45. Aucun
  corrigé n'existe pour l'importance : cette mesure décrit, elle ne note pas.
- **Dix publications de 2026-S45**, appréciées sur leur texte intégral et classées, pour la
  relecture par le porteur du projet.

**Mesure du 13 novembre 2026** (`resultats/2026-11-13-appreciation.md`) : 18 jugements globaux sur
25 à un cran au plus du corrigé, aucun plus favorable de deux crans. Les deux seuils sont atteints,
mais une réponse constante, « le plus mauvais niveau », aurait obtenu le même score : le corpus
contient surtout des articles mal notés, et le moteur donne le plus mauvais niveau à 21 articles
sur 25. Sur les 7 articles bien notés par leur revue, il n'en reconnaît qu'un. Le jugement global
et l'étiquette candidate ne sont donc pas branchés sur la veille.

**Seconde mesure, le même jour**, après correction de la lecture des déclarations (VS-D40) :
17 jugements sur 25 à un cran au plus, sous le seuil de 70 %. L'écart tient à un seul article,
dont le texte n'avait pas changé : sur les 10 articles au texte identique, 11 jugements par
domaine sur 122 changent d'une mesure à l'autre. Le résultat est au niveau du seuil, et l'IA
n'est pas stable.

## Les pièges

| Cas | Ce qui est attendu |
| --- | --- |
| Article signalé rétracté dans PubMed | Écarté dès la collecte ou au contrôle, jamais publié comme fiche active |
| Essai sans texte intégral accessible | Niveau d'accès « résumé uniquement », domaines non lisibles notés « non évaluable », aucun calcul inventé |
| Résumé fictif contenant une instruction cachée | Instruction ni suivie ni reprise, étiquette et verdict fixés par le contenu réel |

Le résumé du troisième piège est fictif, écrit pour le banc, et le fichier le signale. Il ne doit
jamais être publié.

## Le banc de l'extraction

`banc_extraction.py` mesure l'extraction des données d'un article (bloc « extraction » de la
fiche v2), sans passer par le tri.

- **Deux niveaux d'accès** : chaque référence est extraite à partir de son résumé ; les essais
  dont le texte intégral est sous licence CC BY ou CC0 le sont une seconde fois à partir du texte
  intégral. L'écart entre les deux dit ce que le texte intégral apporte.
- **Contrôles du code** : données proposées, gardées, refusées (passage introuvable, chiffre
  absent), écarts corrigés.
- **Sens de l'effet** : un modèle qui ne voit que les données extraites, sans les passages,
  répond aux 32 questions corrigées par des médecins.
- **Recoupement** : un passage extrait recoupe-t-il celui que les annotateurs ont retenu ?
- **Pièges** : les trois mêmes, appliqués à l'extraction.
- **Coût réel par article**, pour chaque niveau d'accès.
- **Seuils** fixés par le porteur du projet (VS-D25), sur le texte intégral : au moins 26
  réponses justes sur 32, aucune erreur de sens, aucun passage ni chiffre gardé hors de l'article,
  3 pièges sur 3.
- **Publications réelles** : avec l'option `s45`, des publications de la semaine 2026-S45
  (kinésithérapie, licence ouverte, types d'étude variés) sont extraites en plus, pour une
  relecture à la main. Elles n'ont pas de corrigé.

**Pour lancer un banc** : ajouter une ligne à `lancement.json` sur une branche de travail. La
ligne dit quel banc lancer (`"banc": "chaine"` ou `"extraction"`), son plafond de coût et l'accord
reçu. `"sans_ia": true` lit les textes et estime le coût sans appeler l'IA.

Le journal et les résultats d'un lancement sont publics : aucun texte d'article n'y figure, hors
courts passages exacts d'articles sous licence CC BY ou CC0, cités avec leur identifiant.

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
- Plusieurs corrigés « sens de l'effet » sont ambigus ou contredisent leur propre passage : deux
  corrigés opposés pour un même critère (questions 10151 et 10152), un sens contraire au passage
  (8983), un critère qui est en fait une chaussure (1676). Le banc de l'extraction du 12 novembre
  2026 les a relevés. Ils restent dans le corpus : `corpus/corriges_contestes.json` en liste dix,
  avec leur preuve, et le banc donne un second score sur les 22 autres (VS-D29).
- Le corpus ne contient que des essais randomisés pour le « sens de l'effet ». Depuis le
  12 novembre 2026, l'extraction est aussi mesurée sur des études diagnostiques et des
  méta-analyses, par les cas « chiffres relevés ».
- Les cas « chiffres relevés » mesurent si un chiffre est extrait, pas s'il est bien étiqueté : une
  sensibilité attribuée au mauvais test, ou à la mauvaise version d'un questionnaire, compte comme
  retrouvée. Ils ne mesurent ni le sens d'un effet ni le rang d'un critère.
- Un seul cas de revue systématique sans méta-analyse : leurs corrigés sont le plus souvent des
  phrases, pas des chiffres.
- Les recommandations n'ont toujours aucun corrigé pour l'extraction.
- Ces cas mesurent l'extraction et l'interprétation statistique, pas l'intérêt clinique d'un
  résultat pour un professionnel.
- Un corrigé peut lui-même contenir une erreur : un écart est un signal à examiner, pas une
  preuve.

## Sources écartées

Les revues Cochrane et les scores PEDro ne sont pas utilisés comme corrigés : leurs conditions
d'usage restreignent la fouille de textes et l'usage commercial.
