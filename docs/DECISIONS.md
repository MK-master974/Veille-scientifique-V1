# Registre des décisions

Ce registre garde la trace des décisions qui façonnent Veille Santé, avec leur raison. Une
décision validée n'est pas modifiée sans que le changement et ses conséquences soient présentés
au porteur du projet. Les décisions propres à Veille Santé portent le préfixe `VS-` ; celles de
la coordination entre applications portent le préfixe `POR-`.

Statuts : **validée** (prise par le porteur du projet), **réalisée** (mise en œuvre),
**en révision** (remise en cause par le cahier des charges de novembre 2026, à trancher),
**à arbitrer**.

Voir aussi [ARCHITECTURE.md](ARCHITECTURE.md) et [../CHANGELOG.md](../CHANGELOG.md).

## 1. Décisions fondatrices (1er novembre 2026)

| Sujet | Décision | Statut |
| --- | --- | --- |
| Public | Professionnels de santé francophones, toutes professions ; application gratuite | Validée |
| Support | Application web installable, pour téléphone, tablette et ordinateur | Validée, réalisée |
| Accès | Sans compte : le profil reste sur l'appareil | Validée, réalisée |
| Production | Entièrement automatique. L'IA est appelée par une interface payée à l'usage par le porteur du projet | Validée, réalisée |
| Coût | Indépendant du nombre de lecteurs : une seule veille produite, distribuée filtrée à chacun | Validée, réalisée |
| Rythme | Hebdomadaire | Validée, réalisée. En révision : collecte quotidienne à l'étude |
| Contenus | Recommandations, revues systématiques et méta-analyses, essais randomisés, études diagnostiques | Validée, réalisée |
| Validation | Contrôle automatique, sans relecture humaine avant publication | Validée, réalisée |
| Personnalisation | Par domaine : trois niveaux d'intérêt et trois niveaux de détail | Validée, réalisée. Les trois niveaux de détail sont remplacés, à la bascule vers la fiche v2, par une fiche unique progressive (VS-D12) |
| Niveau de preuve | Étiquette simple (solide, modéré, préliminaire), détail à déplier | Validée, réalisée. À la bascule vers la fiche v2, l'étiquette prend une quatrième valeur, « non évaluable » (VS-D14) |
| Fonctions | Archive et recherche, favoris, export pour Zotero, partage d'une fiche | Validée, réalisée |

## 2. Contenu et méthode

### Sources

- **Retenues** : PubMed (source principale), recommandations indexées dans PubMed, flux RSS de la
  HAS, Crossref pour le contrôle. Seules des sources ouvertes, interrogeables légalement.
- **Écartées** : Embase, Scopus, Web of Science, CINAHL, PsycINFO, SPORTDiscus (abonnement) ;
  Google Scholar (pas d'interface, collecte automatisée interdite) ; PEDro (pas d'interface
  publique) ; prépublications (non relues par les pairs) ; sites de vulgarisation.
- **Reportée** : Europe PMC, en complément dédoublonné.
- **En révision** : le cahier de novembre 2026 demande d'étudier la couverture de ces sources,
  une par une, sans promettre d'exhaustivité.

### Règles de collecte et de tri

- **Fenêtre** : sept jours, selon la date d'entrée dans PubMed, du lundi au dimanche.
- **Exclus dès la collecte** : protocoles, commentaires, lettres, éditoriaux, articles rétractés,
  errata, articles sans résumé, articles ni en anglais ni en français, études sur l'animal seul.
- **Exclus au tri** : études pilotes et de faisabilité, essais de moins de 30 participants, études
  sans groupe contrôle (sauf recommandations et études diagnostiques), études sans conséquence
  clinique plausible. **En révision** : le cahier de novembre 2026 demande de ne plus exclure sur
  un seul critère et de présenter ces études dans une veille complémentaire.
- **Principe** : l'IA ne cherche jamais elle-même. Elle ne travaille que sur les références
  récupérées par le code ; les liens viennent des métadonnées.

### Étiquette de preuve

L'étiquette part de règles fixes ; l'IA peut l'abaisser, jamais la remonter.

| Type d'étude | Solide | Modéré | Préliminaire |
| --- | --- | --- | --- |
| Recommandation | Fondée sur des preuves gradées | Accord d'experts | — |
| Revue systématique ou méta-analyse | GRADE élevé ou modéré rapporté | GRADE faible, ou essais randomisés majoritaires | GRADE très faible, ou études non randomisées majoritaires |
| Essai randomisé | Jamais pour un essai isolé | Au moins 100 participants | De 30 à 99 participants, ou biais majeur |
| Étude diagnostique | — | Cohorte prospective avec référence standard | Rétrospective ou cas-témoins |

Quand l'information manque dans le résumé, la valeur la plus prudente est retenue.

### Verdict pratique

Quatre niveaux : change la pratique, remet en question, confirme, à surveiller. « Change la
pratique » est réservé aux recommandations et aux revues ou méta-analyses d'étiquette « solide ».

Décision validée le 1er novembre 2026, en vigueur jusqu'à la bascule vers la fiche v2. Elle est
alors remplacée par la catégorie d'importance (VS-D13).

### Mentions et cadre

- Chaque fiche porte un avertissement sur sa production par IA.
- Aucun résumé ni article n'est reproduit : seulement des synthèses originales, des références et
  des liens. Seule exception, décidée le 12 novembre 2026 (VS-D15) : un court passage exact d'un
  article sous licence CC BY ou CC0, cité avec sa source.
- Aucune donnée personnelle n'est collectée. Seul l'abonnement aux notifications passerait par un
  service tiers, avec consentement.
- Le cadre légal reste à faire valider par un juriste avant une ouverture large.

## 3. Choix techniques

| Choix | Raison | Statut |
| --- | --- | --- |
| Séparer la collecte (code) de l'analyse (IA) | Les références et les liens sont réels par construction | Réalisée |
| Traitement différé des requêtes d'IA | Moitié prix, résultats sous 24 heures | Réalisée |
| Fichiers statiques sur GitHub Pages | Hébergement gratuit, site utilisable même si le moteur est en panne | Réalisée |
| Moteur planifié sur GitHub Actions | Gratuit pour un dépôt public, relance toutes les heures | Réalisée |
| État de la semaine dans le cache d'Actions | Pas de base de données à administrer | Réalisée. Limite : 7 jours, d'où l'artefact de 90 jours |
| Clés d'IA dans les secrets du dépôt | Jamais dans le code ni dans l'application | Réalisée |
| Recherche par index JSON annuel | Pas de dépendance ; chargé à la première recherche | Réalisée. Limite : grossit chaque semaine |
| Polices du système, aucune bibliothèque | Aucun appel à un tiers | Réalisée |
| Budget hebdomadaire plafonné | Maîtrise du coût d'IA | Réalisée |
| Échec du lancement si plus de 30 % des réponses d'IA manquent | Ne jamais publier une semaine presque vide | Réalisée |
| Contrôle des chiffres contre le résumé | Écarter les chiffres inventés | Réalisée |
| Copies des workflows dans `installation/` | Dépôt initial fait à la main, sans Git | Réalisée. À retirer quand toutes les modifications passeront par Git |

## 4. Constat de la première veille et correctif provisoire

La première veille (semaine 2026-S45, publiée le 9 novembre 2026) a produit 710 fiches, dont
92 % « préliminaire », aucune « solide », et 707 « à surveiller ».

Les données de travail ont montré trois causes, sur les 806 études retenues au tri :

1. 594 partent « préliminaire » par règle, faute d'information dans le résumé ;
2. l'IA de rédaction abaisse 158 étiquettes, dont les 9 « solide » ;
3. l'IA propose elle-même « à surveiller » 802 fois.

| Décision | Contenu | Statut |
| --- | --- | --- |
| VS-D6 | Correctif provisoire de la consigne de rédaction : l'étiquette n'est plus abaissée pour une information absente du résumé ; « confirme » et « remet en question » sont mieux définis | Validée et réalisée le 11 novembre 2026. À mesurer sur la semaine suivante |
| Refonte du niveau de preuve | Remplacer le tableau par une appréciation selon l'outil adapté au type d'étude, distinguer « preuve faible » et « non évaluable » | Format arrêté le 12 novembre 2026 (VS-D14, [FICHE_V2.md](FICHE_V2.md)). La règle d'attribution reste à régler et à mesurer au banc d'essai, en séance 6 |

## 5. Décisions du 11 novembre 2026

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D1 | Sauvegarder les données de travail de la semaine 2026-S45 avant leur expiration | Réalisée |
| VS-D2 | Phase 0 limitée aux travaux critiques et aux réglages publics | Validée |
| VS-D3 | Donner à l'application une adresse propre. Nom et forme à choisir avant la bêta | Validée sur le principe |
| VS-D4 | Le dépôt reste public | Validée |
| VS-D5 | Documentation technique dans le dépôt : architecture, décisions, journal des changements | Validée, réalisée |
| VS-D7 | Coordination entre applications par un dépôt dédié et des messages entre environnements de développement, pas par un journal dans un espace documentaire | Validée |
| Corpus de référence | Assemblé à partir de corrigés qui existent déjà (jeux de données de recherche, registres d'essais, revues Cochrane, scores PEDro consultés à la main, PubMed) plutôt que rempli à la main | Validée |
| Phase 1 | Fiabilisation scientifique en dix séances, chacune terminée par un point d'arrêt. Démarre après la phase 0, sur accord explicite | Validée |
| Mise en ligne | Toute modification passe par la branche de travail, les tests automatiques, puis une demande de fusion validée par le porteur du projet | Pratique en vigueur |

Décisions prises au fil des séances 2 et 3 de la phase 1 :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D8 | Corriger le contrôle des chiffres avant la veille du 16 novembre : lire les nombres en toutes lettres au-delà de dix et les décimales sans zéro initial, sans accepter de nombre absent de la source. Constat du banc d'essai : 8 fiches sur 16 écartées à tort | Validée le 11 novembre 2026 (questionnaire), réalisée |
| VS-D9 | Relancer le banc d'essai après la correction pour mesurer le gain (environ 0,12 $) | Validée le 11 novembre 2026 (questionnaire) |
| VS-D10 | Faire la séance 3 de la phase 1 dans une conversation neuve | Validée le 11 novembre 2026 (questionnaire, d'après le plan, section 22), réalisée |
| VS-D11 | Modèle d'IA de la session de développement de la séance 3 : choisi par le porteur du projet. Son nom n'est pas inscrit dans le dépôt | Validée le 11 novembre 2026 (questionnaire, d'après le plan, section 22), réalisée |

Décisions de coordination entre applications, relayées les 11 et 12 novembre 2026 :

| Référence | Décision |
| --- | --- |
| POR-D17 | Un préfixe par projet pour les décisions : `VS-` pour Veille Santé |
| POR-D18 | Dix codes communs pour le circuit des connaissances vers Évalys : `NON_SELECTIONNEE`, `A_EXAMINER`, `EN_EVALUATION`, `VALIDEE_TRANSMISSION`, `TRANSMISE`, `RECUE`, `INTEGREE`, `REFUSEE`, `DIFFEREE`, `A_ACTUALISER` |
| POR-D9 | Pilote du circuit vers Évalys sur le genou, cinq propositions au plus, sans modification clinique. Attend la fiche v2 de Veille Santé |
| POR-D12 | Veille Santé garde sa propre interface de gestion ; le portail n'en affiche qu'une synthèse. Interface reportée à la phase 4 |
| POR-D19 | Essai de format du circuit vers Évalys : seul du contenu déjà public dans ce dépôt, avec la mention « résumé uniquement, non destinée à l'intégration clinique ». Pas avant la fin de la phase 0 |
| POR-D21 | Un avis réglementaire commun aux applications, demandé après la bascule de la fiabilisation |
| POR-D22 | Liste fermée de dix régions du corps, commune à Veille Santé et à Évalys. Régions validées par le porteur du projet le 12 novembre 2026 ; le second champ de cinq thèmes proposé par Évalys attend le pilote « genou » |

## 6. Décisions du 12 novembre 2026 : format « fiche v2 »

Séance 3 de la phase 1. Les décisions VS-D12 à VS-D15 ont été prises par questionnaire, après
relecture du brouillon ; le format a été figé le même jour par la fusion de la demande n° 8. Le format est décrit dans [FICHE_V2.md](FICHE_V2.md). Rien ne change dans la veille
publiée avant la bascule, dernière séance de la phase 1.

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D12 | Fiche unique progressive : un en-tête toujours visible (question, résultat principal, impact clinique, limite principale), puis des sections à déplier. Remplace, à la bascule, les trois niveaux de détail du 1er novembre. Le réglage « niveau de détail » du profil sera revu en phase 3 | Validée |
| VS-D13 | La catégorie d'importance, de 1 à 4 et justifiée, remplace le verdict. « Confirme » et « remet en question » restent comme précision ; « change la pratique » correspond à la catégorie 1 ; « à surveiller » disparaît. Remplace, à la bascule, le verdict à quatre niveaux du 1er novembre. Constat : 707 fiches sur 710 portaient « à surveiller » en S45 | Validée |
| VS-D14 | L'étiquette de preuve prend quatre valeurs : solide, modéré, préliminaire, non évaluable. Remplace, à la bascule, l'étiquette à trois valeurs du 1er novembre. La règle d'attribution est réglée et mesurée au banc d'essai en séance 6 | Validée |
| VS-D15 | Un court passage exact d'un article n'est publié que si l'article est sous licence CC BY ou CC0, avec sa source. Pour tous les autres, seul l'emplacement est publié. La règle « ni résumé ni texte d'article » est complétée dans ce sens | Validée |
| VS-D16 | La fiche v2 porte une région anatomique, `classement.themes.region`, à vocabulaire fermé. La liste est commune aux applications de l'écosystème et tenue dans le dépôt de coordination : dix régions, validées le même jour (POR-D22). Complément au format, demandé par le portail dans son analyse de CHG-2026-0004 | Validée (questionnaire de fin de séance 3) |
| VS-D17 | Proposer au contrat `vs-evalys-connaissance` la règle suivante, par une demande de fusion dans le dépôt de coordination : une fiche corrigée, suspendue ou retirée, ou une publication signalée, fait repasser la proposition liée à « à actualiser » | Validée (questionnaire de fin de séance 3) |
| VS-D18 | Séance 4 de la phase 1 (texte intégral en accès ouvert, niveaux d'accès) : accord donné, dans la même conversation de développement | Validée (questionnaire de fin de séance 3) |
| VS-D19 | La fiche v2 porte la date de mise en ligne de l'article (`publication.date_en_ligne`), en plus de la date du numéro de la revue. Remplie par le code à partir de PubMed. Demande d'Évalys, qui déclare des écarts de citation venus de cette confusion | Validée (questionnaire de fin de séance 3) |
| VS-D20 | Plan de la séance 4 : un module qui cherche le texte intégral légal et sa licence, et une mesure à la demande des niveaux d'accès sur une semaine publiée, sans IA et hors de la veille hebdomadaire. Mesure sur S45, puis sur S46 le jour de sa publication. Le périmètre des licences admises sera décidé au point d'arrêt, avec les chiffres | Validée le 12 novembre 2026 (questionnaire), réalisée pour S45 |
| VS-D21 | Une fiche n'est analysée sur le texte intégral (niveau d'accès 1) que si l'article est sous licence CC BY ou CC0. Mesure sur S45 : 34 % des fiches, 53 % en kinésithérapie. Les licences « pas d'usage commercial » et « pas de modification » (187 fiches en S45) sont soumises à l'avis juridique commun (POR-D21) | Validée le 12 novembre 2026 (questionnaire, point d'arrêt de la séance 4) |
| VS-D22 | Mesurer les niveaux d'accès de S46 le jour de sa publication, lundi 16 novembre 2026, par un rappel programmé dans la conversation de développement | Validée le 12 novembre 2026 (questionnaire) |
| VS-D23 | Séance 5 de la phase 1 (extraction des données) : accord donné, dans une conversation neuve | Validée le 12 novembre 2026 (questionnaire) |

Décisions de la séance 5 de la phase 1 (extraction des données), prises par questionnaire :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D24 | Plan de la séance 5, réalisé : lecture du texte intégral en blocs repérés, consigne d'extraction, contrôles par le code et banc d'essai « extraction ». Chaque essai du corpus sous licence CC BY est extrait deux fois, sur le résumé seul puis sur le texte intégral, pour mesurer ce que le texte intégral apporte. La veille hebdomadaire et l'application ne sont pas touchées | Validée le 12 novembre 2026 (questionnaire) |
| VS-D25 | Seuils de réussite de l'extraction au banc d'essai, sur le texte intégral : au moins 26 réponses justes sur 32, aucune erreur de sens, aucun passage ni chiffre gardé qui ne soit pas dans l'article, 3 pièges sur 3. Si un seuil n'est pas atteint, les écarts sont présentés avant d'aller plus loin. Le plan prévoyait de fixer des seuils en séance 2 ; aucun ne l'avait été. La session proposait 22 sur 32 ; le porteur du projet a retenu 26 | Validée le 12 novembre 2026 (questionnaire) |
| VS-D26 | La relecture de dix extractions par le porteur du projet, prévue au plan (section 18), n'a pas lieu en séance 5 : la session de développement la fait elle-même et en rend compte. Conséquence : aucun humain ne relit les extractions à cette séance | Validée le 12 novembre 2026 (questionnaire : « fait sans moi ») |
| VS-D27 | Budget d'IA de la séance 5 : enveloppe de 5 $. Le coût estimé est annoncé avant chaque lancement du banc, le coût réel après ; la session s'arrête et redemande si l'enveloppe ne suffit pas | Validée le 12 novembre 2026 (questionnaire) |

Décisions du point d'arrêt de la séance 5, prises par questionnaire le 12 novembre 2026 après la
mesure (résultats : [../banc/resultats/2026-11-12-extraction.md](../banc/resultats/2026-11-12-extraction.md)) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D28 | Suite de la phase 1 : renforcer d'abord le corpus de référence (revues et études diagnostiques avec corrigé), puis faire la séance 6, dans une conversation neuve. Constat : le seuil de 26 réponses justes n'est pas atteint (24), et les défauts trouvés sur dix publications réelles n'apparaissaient pas dans un corpus fait seulement d'essais | Validée le 12 novembre 2026 (questionnaire ; le porteur du projet a retenu ensemble « séance 6, conversation neuve » et « renforcer d'abord le corpus ») |
| VS-D29 | Les dix questions du corpus dont le corrigé est contesté sont marquées dans `banc/corpus/corriges_contestes.json`, avec leur preuve, sans être supprimées. Le banc donne deux scores : sur les 32 questions, et sur les 22 non contestées. La liste est établie par la session de développement ; elle n'est pas relue par un humain | Validée le 12 novembre 2026 (questionnaire), réalisée |
| VS-D30 | Quatre précisions du bloc `extraction` de la fiche v2 : forme de `evenements_indesirables`, forme de `emplacement`, valeur `sans_objet` de `sens_mesure`, champ `comparaison` d'un résultat. Déclarées au dépôt de coordination avant d'être inscrites (CHG-2026-0007). Complète le format figé le 12 novembre (VS-D12 à VS-D19) sans rien en retirer | Validée le 12 novembre 2026 (questionnaire), réalisée |
| VS-D31 | Ouvrir la demande de fusion du lot de la séance 5 sans attendre la veille du 16 novembre : aucun fichier de la veille hebdomadaire ni de l'application n'est modifié | Validée le 12 novembre 2026 (questionnaire) |

Décisions du renforcement du corpus de référence, prises par questionnaire le 12 novembre 2026, au
début de la conversation de développement qui suit la séance 5 :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D32 | Les corrigés des nouveaux articles du corpus (études diagnostiques, méta-analyses, revues) sont les chiffres déjà relevés par les auteurs d'une revue en accès libre : revue de précision diagnostique pour une étude diagnostique, revue de revues pour une méta-analyse. La revue source et l'article sont sous licence CC BY ou CC0. La comparaison est faite par le code, sans IA lectrice. Constat : en 2026-S45, 620 fiches sur 710 sont de ces types, et l'extraction n'était mesurée que sur 8 essais. Options écartées : le jeu de données PubMedQA, en complément ou seul | Validée le 12 novembre 2026 (questionnaire), réalisée : 20 articles, 9 revues sources, 161 chiffres (`banc/corpus/chiffres_releves.json`) |
| VS-D33 | Budget d'IA du renforcement du corpus et de sa mesure : enveloppe de 5 $. Le coût estimé est annoncé avant chaque lancement, le coût réel après. Une nouvelle enveloppe est demandée avant la séance 6. Le plafond fixe d'un lancement du banc « extraction » passe de 2 $ à 3 $, parce que le corpus grossit | Validée le 12 novembre 2026 (questionnaire). Dépensé : 2,57 $ en deux lancements |
| VS-D34 | Seuil de réussite pour les nouveaux articles, fixé avant la mesure : l'extraction retrouve, à partir du texte intégral, au moins 80 % des chiffres du corrigé. Un chiffre de corrigé que le code ne retrouve pas dans l'article est écarté du score avant la mesure, et compté à part. En dessous du seuil, les écarts sont présentés avant d'aller plus loin | Validée le 12 novembre 2026 (questionnaire). Seuil atteint : 148 à 149 chiffres retrouvés sur 159, soit 93 %. Deux chiffres écartés avant la mesure finale. Quatre règles de comparaison ont été corrigées après la première mesure ; les deux scores sont publiés ([résultats](../banc/resultats/2026-11-12-chiffres-releves.md)) |
| VS-D35 | Consigne du portail CONS-2026-11-12-01 (décision de coordination POR-D24) appliquée en version prudente : les sept fiches de méthode communes sont copiées dans `.claude/skills/` ; les huit règles impératives et le format des messages restent dans `CLAUDE.md` ; seul le détail du questionnaire y devient un renvoi. `CLAUDE.md` fait foi en cas d'écart | Validée le 12 novembre 2026 (questionnaire), réalisée |

Décisions du point d'arrêt du renforcement du corpus, prises par questionnaire le 12 novembre 2026
après la mesure (résultats : [../banc/resultats/2026-11-12-chiffres-releves.md](../banc/resultats/2026-11-12-chiffres-releves.md)) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D36 | Ouvrir sans attendre la demande de fusion du lot « corpus renforcé », séparée de la séance 6 : aucun fichier de la veille hebdomadaire ni de l'application n'est modifié | Validée le 12 novembre 2026 (questionnaire) |
| VS-D37 | Séance 6 de la phase 1 (appréciation par outil selon le type d'étude, catégories d'importance) : accord donné, dans la même conversation de développement. Plan : corrigés de qualité lus dans les revues sources déjà utilisées, module d'appréciation dont chaque jugement porte un passage vérifié par le code, banc d'essai, dix fiches à relire par le porteur du projet, point d'arrêt | Validée le 12 novembre 2026 (questionnaire) |
| VS-D38 | Budget d'IA de la séance 6 : le reste de l'enveloppe du corpus, soit 2,43 $, sans argent nouveau. Le coût estimé est annoncé avant chaque lancement ; la session s'arrête et redemande si cela ne suffit pas. Conséquence annoncée : un lancement complet, probablement pas de seconde mesure après correction | Validée le 12 novembre 2026 (questionnaire) |
| VS-D39 | Seuil de réussite de l'appréciation au banc d'essai, fixé avant la mesure : au moins 70 % des jugements globaux à un cran au plus du jugement des auteurs d'une revue, et aucun jugement plus favorable que ce corrigé de deux crans. En dessous, les écarts sont présentés avant d'aller plus loin | Validée le 12 novembre 2026 (questionnaire). Mesuré le 13 novembre 2026 : 18 jugements sur 25 à un cran au plus (72 %), puis 17 sur 25 (68 %) à la seconde mesure ; aucun jugement plus favorable de deux crans. Résultat au niveau du seuil, et une réponse constante obtient 18 sur 25 ([résultats](../banc/resultats/2026-11-13-appreciation.md)). **Remplacée par VS-D75 le 14 novembre 2026** (seuil des quatre premières grilles) |

Décisions du point d'arrêt de la séance 6, prises par questionnaire le 13 novembre 2026 après la
première mesure de l'appréciation (résultats :
[../banc/resultats/2026-11-13-appreciation.md](../banc/resultats/2026-11-13-appreciation.md)) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D40 | Suite de la séance 6 : corriger la lecture des déclarations placées hors du corps de l'article (financement, liens d'intérêts), puis remesurer l'appréciation sur texte intégral, sur le reste de l'enveloppe (1,48 $), sans argent nouveau. Avis du porteur du projet, noté tel quel : « garde en tête que je trouve tes avis parfois trop sévère ». La consigne d'appréciation n'est pas modifiée pour cette seconde mesure : la sévérité se règle après la relecture des dix fiches, pour ne pas ajuster la consigne sur les articles qui servent à la mesurer (interprétation de la session de développement) | Validée le 13 novembre 2026 (questionnaire), réalisée. Dépensé pour la séance 6 : 1,38 $ sur 2,43 $ |
| VS-D41 | Règle d'attribution de l'étiquette (VS-D14) : décision reportée. La règle écrite dans `pipeline/appreciation.py` reste candidate et n'est pas branchée sur la veille. Elle sera tranchée quand la mesure montrera que le moteur reconnaît une bonne étude | Validée le 13 novembre 2026 (questionnaire) |
| VS-D42 | Demande de fusion de la séance 6 : ouverte après la fusion du lot 12, pour ne montrer que les fichiers de la séance 6 | Validée le 13 novembre 2026 (questionnaire) |
| VS-D43 | Accord pour écrire dans le dépôt de coordination : accusé de lecture de la consigne CONS-2026-11-12-01, compte rendu de la séance 6, déclaration des précisions du bloc « appreciation » de la fiche v2 | Validée le 13 novembre 2026 (questionnaire), réalisée : commit `05757ba` du dépôt de coordination (déclaration CHG-2026-0009, compte rendu du 13 novembre, accusé de lecture) |

Décisions prises par questionnaire le 13 novembre 2026, après le retour du comité d'experts sur les
dix fiches (recoupement : [../banc/resultats/2026-11-13-appreciation.md](../banc/resultats/2026-11-13-appreciation.md)) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D44 | Séance 7 : le socle d'abord. Quatre corrections sans nouvel outil d'appréciation : (1) une étape « plan d'étude » avant le choix de la grille, avec « aucune grille applicable » quand rien ne convient ; (2) « non rapporté » distinct de « non », et une fourchette du jugement global au lieu de « non évaluable » ; (3) un champ « nature du jugement » pour que l'axe qualité ne soit plus lu comme une certitude, déclaré au dépôt de coordination avant d'être inscrit dans `docs/FICHE_V2.md` ; (4) plus d'appréciation sur résumé seul. ROBINS-I, PROBAST, ROBIS et les grilles JBI viennent après, chacun avec son corpus de référence | Validée le 13 novembre 2026 (questionnaire), réalisée et mesurée une fois ([résultats](../banc/resultats/2026-11-13-seance-7.md)) : plan retrouvé pour 8 fiches sur 10 de 2026-S45 et 20 articles sur 25 du corpus. Défaut trouvé : la définition de « modèle de prédiction » est trop large, non corrigé en attendant l'accord pour un second cycle |
| VS-D45 | Budget d'IA de la séance 7 : le reste de l'enveloppe de la séance 6, soit 1,05 $, sans argent nouveau. Un seul cycle de mesure ; si un second est nécessaire, la session s'arrête et redemande | Validée le 13 novembre 2026 (questionnaire). Dépensé : 0,63 $ en un cycle ; total de la séance 6 et de la séance 7 : 2,02 $ sur 2,43 $, reste 0,41 $ |
| VS-D46 | Le retour du comité d'experts tient lieu de relecture des dix fiches. Il est inscrit comme avis déclaré, recoupé par la session sur 9 fiches avec les jugements du moteur et sur 6 avec PubMed. Ce n'est pas un corrigé : il ne rejoint le corpus de référence qu'après confirmation par un second lecteur humain | Validée le 13 novembre 2026 (questionnaire) ; **corrigée le 13 novembre 2026** : le porteur du projet précise que ce retour venait d'une IA (ChatGPT), pas d'un comité d'experts. Il reste un second avis utile, jamais une validation, et il n'est pas indépendant du moteur, qui utilise le même fournisseur d'IA (voir VS-D52) |
| VS-D47 | La page de relecture est refaite pour capter des désaccords précis (domaine contesté, jugement proposé, passage de l'article, nature de l'erreur, grille et plan d'étude proposés). Les avis sont des annotations avec l'identité du relecteur, séparées du corpus de référence. Aucun coût d'IA, aucun fichier du dépôt. Le partage de la page avec les membres du comité est fait par le porteur du projet | Validée le 13 novembre 2026 (questionnaire) |

Décisions prises par questionnaire le 13 novembre 2026, après la première mesure de la séance 7
(résultats : [../banc/resultats/2026-11-13-seance-7.md](../banc/resultats/2026-11-13-seance-7.md)) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D48 | Second cycle de la séance 7, plan d'étude seul : corriger les définitions de « modèle de prédiction » et de « revue d'interventions », puis mesurer l'étape « plan d'étude » sans appréciation. Critère à écrire : développer ou ajuster un modèle sur les données de l'étude relève de PROBAST ; évaluer un test, un score ou un algorithme déjà défini contre une référence relève de QUADAS-2 ; une revue de groupes ou d'expositions sans intervention est descriptive. Mesure sur les 25 articles du corpus « qualité », les 10 publications de 2026-S45 et les études diagnostiques du corpus de chiffres relevés (7 de plus : 2 des 9 figurent déjà au corpus « qualité »), qui servent de contrôle hors du corpus où le défaut a été trouvé. Plafond de dépense : 0,25 $ sur les 0,41 $ restants | Validée le 13 novembre 2026 (questionnaire), réalisée : 0,16 $. Grille du plan identique à celle des auteurs pour 23 articles sur 25 du corpus (20 avant), conforme à l'avis du comité pour 10 fiches sur 10, mais seulement 4 études diagnostiques sur 7 hors corpus : le cas mixte (développer un modèle et évaluer un outil défini) reste à traiter. Total des séances 6 et 7 : 2,17 $ sur 2,43 $ ([résultats](../banc/resultats/2026-11-13-seance-7.md)) |
| VS-D49 | Étude, sans IA et sans coût, de la récupération des protocoles et des suppléments pour les revues sous licence CC BY : nombre d'articles avec fichiers supplémentaires, numéros de protocole ou de registre cités dans le texte. Aucun changement du moteur ; la session dit ensuite si le développement en vaut la peine | Validée le 13 novembre 2026 (questionnaire), réalisée : 11 revues sur 16 déclarent du matériel supplémentaire (surtout Word et PDF), 9 sur 16 citent un numéro PROSPERO, 1 sur 16 cite une liste des études exclues ; le paquet d'Europe PMC n'est pas un signal fiable. Gain non mesuré, développement non décidé |
| VS-D50 | Seuil de réussite de la fourchette du jugement global au banc d'essai, fixé avant la mesure : au moins 70 % des articles dont le corrigé est dans la fourchette, la fourchette couvrant deux niveaux au plus. Mesure de la séance 7, premier cycle : 9 articles sur 25 (36 %), seuil non atteint ; non remesuré au second cycle | Validée le 13 novembre 2026 (questionnaire) |

Décision du 14 novembre 2026, par questionnaire, au choix de la prochaine étape :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D51 | Cas mixte du plan d'étude : une étude qui développe un modèle et évalue aussi un outil, un score ou des seuils déjà définis est classée « étude diagnostique » (grille QUADAS-2 pour cette évaluation). Mesure du plan seul, plafond 0,25 $ sur les 0,26 $ restants, sans nouvelle enveloppe | Validée (questionnaire), réalisée : 0,16 $ ; 24 articles sur 25 du corpus, 7 études hors corpus sur 7 (plus indépendantes de la règle), 10 fiches sur 10. Total des séances 6 et 7 : 2,33 $ sur 2,43 $ |

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D52 | Relecture des fiches : le porteur du projet relit lui-même 3 ou 4 fiches de son domaine sur la page de relecture, seul avis humain disponible. Un avis d'IA (ChatGPT ou autre) peut servir de second regard, inscrit comme tel, jamais comme une validation | Remplacée par VS-D53 le 13 novembre 2026 |
| VS-D53 | Le porteur du projet ne relit pas les appréciations : il dit ne pas avoir les compétences pour en juger et se fie à deux avis d'IA, celui de ChatGPT et celui de la session de développement (Claude). Conséquences, dites au porteur du projet : aucune appréciation n'est validée par un humain ; la relecture par la session est un peu indépendante du moteur (autre fournisseur d'IA), celle de ChatGPT ne l'est pas ; une appréciation publiée devra porter la mention « appréciation automatique, non relue par un professionnel » | Validée le 13 novembre 2026 (message du porteur du projet) |

Décisions du 14 novembre 2026, par questionnaire, au début de la conversation de développement
consacrée à ROBINS-I (dépôt de coordination lu au commit `f0f7c1d`, paquet de contexte `0eb5e90`) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D54 | Grille ROBINS-I pour les études interventionnelles non randomisées et les essais quasi randomisés, en trois étapes : (1) corpus de référence sans IA, fait des jugements ROBINS-I déjà publiés dans un tableau par une revue sous licence CC BY, sur des articles eux-mêmes sous licence CC BY (méthode VS-D32) ; arrêt et nouvelle demande si moins de 10 articles ; (2) grille écrite sur le modèle de `pipeline/appreciation.py` (passage vérifié par le code, « non rapporté » distinct d'un défaut, fourchette du jugement global), précédée d'une déclaration au dépôt de coordination pour tout changement de `docs/FICHE_V2.md` ; (3) mesure au banc d'essai. La veille hebdomadaire et l'application ne sont pas touchées. Choix de la session, non contesté : ROBINS-I version 1 (2016), parce que les jugements publiés dans les revues sont presque tous en version 1 | Validée le 14 novembre 2026 (questionnaire), réalisée : corpus de 21 études vérifié sans IA (`banc/corpus/robins_i.json`, 11 corrigés marqués contestés avant la mesure), grille écrite, déclaration CHG-2026-0011 (dépôt de coordination, commit `443b872`), mesure faite ([résultats](../banc/resultats/2026-11-14-robins-i.md)) |
| VS-D55 | Budget d'IA de la mesure de ROBINS-I : une enveloppe nouvelle de 1 $, qui s'ajoute aux 0,10 $ restants, pour deux lancements (mesure, puis stabilité). Plafond de 0,45 $ par lancement ; le coût estimé est annoncé avant chaque lancement, le coût réel après | Validée le 14 novembre 2026 (questionnaire). Plafond par lancement modifié par VS-D57 ; l'enveloppe ne change pas. Dépensé : 0,58 $ pour la mesure et la stabilité, puis 0,18 $ pour VS-D59, soit 0,76 $ sur 1,10 $ ; reste 0,34 $. Puis 0,19 $ pour VS-D66 (lancement 43559966228) : 0,945 $ sur 1,10 $ ; reste 0,155 $ |
| VS-D56 | Seuil de réussite de ROBINS-I au banc d'essai, fixé avant la mesure, en lecture stricte (un domaine non rapporté ou non évalué compte comme le pire jugement) : au moins 50 % des jugements globaux identiques à celui des auteurs de la revue, et plus qu'une réponse fixe au niveau le plus fréquent du corpus ; aucun jugement plus favorable que le corrigé de deux crans. Le seuil de VS-D39 (à un cran au plus) n'est pas repris : ROBINS-I a quatre niveaux et une réponse fixe « sérieux » serait à un cran de presque tous les corrigés. Le seuil de la fourchette (VS-D50) s'applique tel quel | Validée le 14 novembre 2026 (questionnaire). Mesuré : **non atteint**, 1 jugement global identique sur 21 (0 sur 10 sans les corrigés contestés) contre 12 (6) pour une réponse fixe « modéré » ; aucun jugement plus favorable de deux crans. Le moteur donne « critique » aux 21 études en lecture stricte : confusion « sérieux » 21 fois, écarts aux interventions « non rapporté » 20 fois ([résultats](../banc/resultats/2026-11-14-robins-i.md)) |
| VS-D57 | Plafond des lancements de la mesure de ROBINS-I, dans l'enveloppe de VS-D55 (1,10 $) : le premier lancement mesure tout le corpus (21 études et les deux essais quasi randomisés de 2026-S45) avec un plafond de 0,70 $ ; le second mesure la stabilité sur les 10 études dont le corrigé n'est pas contesté, avec pour plafond le reste de l'enveloppe. Constat qui l'a motivée : l'estimation prudente du banc (0,75 $, sans dépense, lancement 43547277468) dépassait 1,5 fois le plafond de 0,45 $, et le contrôle avant chaque groupe de requêtes aurait bloqué l'appréciation ; la dépense réelle attendue est d'environ 0,47 $ pour le premier lancement et 0,20 $ pour le second | Validée le 14 novembre 2026 (questionnaire), réalisée : 0,40 $ (lancement 43547764658) puis 0,18 $ (43548169119). Stabilité : 67 jugements par domaine sur 70 identiques |

Décisions du 14 novembre 2026, par questionnaire, après la mesure de ROBINS-I ([résultats](../banc/resultats/2026-11-14-robins-i.md)) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D58 | Ouvrir sans attendre la demande de fusion du travail ROBINS-I : la grille n'est appelée que par le banc d'essai, aucun fichier de la veille, de l'application ni des workflows ne change, les tests passent | Validée le 14 novembre 2026 (questionnaire) |
| VS-D59 | Suite de ROBINS-I : corriger le seul domaine « écarts aux interventions prévues ». Quand l'article décrit l'intervention réalisée et que rien n'indique d'écart dû au contexte de l'étude ni de co-intervention déséquilibrée, la consigne permet « faible », avec le passage qui décrit l'intervention réalisée, au lieu de « non rapporté ». C'est une exception à VS-D44 (« un silence n'est pas un défaut ») pour ce seul domaine de ROBINS-I, où l'effet jugé est celui de l'attribution ; ailleurs, la règle de VS-D44 tient. La règle de la confusion ne change pas (plus sévère que les revues, mais conforme à l'outil d'après la relecture de la session). Nouvelle mesure sur des articles neufs, qui n'ont pas servi à trouver le défaut, dans les 0,52 $ restants (environ 0,30 $ attendus). Conséquence annoncée : les jugements devraient passer surtout de « critique » à « sérieux » ; le seuil de VS-D56 restera sans doute non atteint | Validée le 14 novembre 2026 (questionnaire), réalisée : 0,18 $ (lancement 43550182278) sur 7 articles neufs. Écarts aux interventions « faible » 4 fois sur 7 (avant : « non rapporté » 20 fois sur 21) ; seuil non atteint (1 sur 7) ; d'autres domaines « non rapporté » donnent encore « critique » à 5 études. La relecture de la session trouve un défaut de la consigne non corrigé : un classement « établi à partir de dossiers » est jugé « sérieux » à tort. Total dépensé : 0,76 $ sur 1,10 $ ; reste 0,34 $ |
| VS-D60 | Cohortes de patients traités (9 études du corpus ROBINS-I sur 21 classées « observationnel » par le plan d'étude, que les revues jugent avec ROBINS-I) : décision reportée à la suite de ROBINS-I. La table de VS-D44 ne change pas | Validée le 14 novembre 2026 (questionnaire). Tranchée par VS-D69 |
| VS-D61 | Défaut de la consigne ROBINS-I trouvé à la relecture de la session : un classement des interventions « établi après coup, à partir de dossiers » est jugé « sérieux », alors qu'un traitement clairement enregistré (médicament prescrit, technique opératoire) ne risque guère d'être mal classé (5 études neuves sur 7 ; les revues : « faible » 6 fois sur 6). Corriger et mesurer à la prochaine séance consacrée à ROBINS-I, sur des articles neufs. La consigne du dépôt reste celle qui a été mesurée (lancement 43550182278) ; la grille n'est pas branchée sur la veille. Reste de l'enveloppe de VS-D55 : 0,34 $, non dépensés | Validée le 14 novembre 2026 (questionnaire), réalisée par VS-D63 à VS-D66 : consigne corrigée (VS-D64), mesurée sur 10 articles neufs ; le classement des interventions est identique au corrigé 7 fois sur 10 (lot 2 : 1 sur 6) ([résultats](../banc/resultats/2026-11-14-robins-i.md)) |
| VS-D62 | La session surveille la demande de fusion n° 16 (tests automatiques et commentaires) jusqu'à sa fusion par le porteur du projet ; elle ne la fusionne jamais elle-même | Validée le 14 novembre 2026 (questionnaire) |

Décisions du 14 novembre 2026, au début de la conversation consacrée à la correction du classement des
interventions (VS-D61), après la fusion de la demande n° 16 (dépôt de coordination lu au commit `2ec46e7`,
paquet de contexte `991c143`) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D63 | Finir ROBINS-I maintenant, dans une conversation de développement neuve : corriger le défaut de VS-D61 et le mesurer sur des articles neufs (ni lot 1 ni lot 2 du corpus), trouvés et vérifiés sans IA (méthode VS-D32), dans les 0,34 $ restants de l'enveloppe de VS-D55, avec les seuils de VS-D56 inchangés | Validée le 14 novembre 2026 (questionnaire de la conversation précédente), réalisée le même jour |
| VS-D64 | Correction de la consigne ROBINS-I pour le seul domaine « classement des interventions », d'après le guide détaillé de l'outil (version 1, 2016) : « faible » quand les groupes sont définis clairement et que l'appartenance vient d'une information enregistrée au moment de l'intervention (inscription au programme, médicament prescrit ou administré, technique opératoire réalisée), même relue après coup dans des dossiers ; « modéré » quand une partie de l'appartenance est reconstituée après coup ; « sérieux » seulement si les groupes sont mal définis ou si l'appartenance a pu dépendre de la connaissance du résultat ; « critique » exceptionnel ; « non rapporté » quand ni la définition des groupes ni la source de l'information ne sont décrites. La consigne est corrigée et enregistrée avant le choix des articles neufs. Ce qui sera compté pour ce domaine, fixé avant la mesure : jugements identiques au corrigé, plus sévères, plus favorables, et aucun plus favorable de deux crans | Validée le 14 novembre 2026 (questionnaire), réalisée : consigne enregistrée au commit `9fbecbf` (empreinte 4ec71ef0), avant le choix des articles. Mesuré sur le lot 3 : classement identique au corrigé 7 fois sur 10, plus sévère 2 fois (sur des faits précis, pas sur le caractère rétrospectif), plus favorable 1 fois, jamais de deux crans |
| VS-D65 | Articles neufs : un quatrième lot de revues candidates, les 250 revues les plus récentes de PubMed (ROBINS-I dans le titre ou le résumé, revue systématique ou méta-analyse, accès libre, depuis 2019) qui n'ont pas déjà été examinées, sans filtre de sujet. Repérage, lecture des lignes et vérification par le code, sans IA. Règle de choix fixée avant : les études admissibles (intervention, pas d'essai randomisé, ROBINS-I version 1 avec jugement global, licence CC BY ou CC0, texte dans PubMed Central), dans l'ordre du repérage, 3 au plus par revue, 10 au plus ; corrigés contestés marqués avant la mesure selon le critère de VS-D54. Constat qui l'a motivée : les 477 revues déjà examinées ne laissent que 24 études jamais utilisées, dont 22 relèvent d'un motif d'écart déjà appliqué | Validée le 14 novembre 2026 (questionnaire), réalisée : 250 revues repérées (lancements 43557433512 et 43557452808), lignes de 8 revues lues (43558447652) ; 10 études gardées dans 6 revues, 9 écartées avec leur motif (une en partie randomisée ; groupes définis par une exposition ou une caractéristique des patients ; facteurs pronostiques), aucun corrigé contesté ; corpus vérifié, 38 études sur 38 (43558883716). Précision de la session, appliquée avant la lecture des lignes : un tableau qui ne donne que le jugement global n'est pas retenu, parce qu'il ne permet pas de mesurer le domaine corrigé |
| VS-D66 | Un seul lancement du banc, sur 10 articles neufs au plus, sans les deux fiches de 2026-S45, avec un plafond de 0,34 $ ; dépense réelle attendue d'environ 0,20 $. Le contrôle du coût avant chaque groupe de requêtes limite un lancement à une dizaine d'articles avec ce plafond | Validée le 14 novembre 2026 (questionnaire), réalisée : estimation sans IA de 0,34 $ (lancement 43559641076), coût réel **0,19 $** (lancement 43559966228). Seuils de VS-D56 **non atteints** : 4 jugements globaux identiques sur 10, contre 6 pour une réponse fixe « sérieux » ; aucun plus favorable de deux crans. Seuil de la fourchette (VS-D50) atteint : 8 sur 10. Reste de l'enveloppe de VS-D55 : 0,155 $ |
| VS-D67 | Ouvrir la demande de fusion sans attendre à la fin du travail (la grille n'est toujours appelée que par le banc d'essai ; aucun fichier de la veille, de l'application ni des workflows ne change). La session la surveille et ne la fusionne jamais elle-même (comme VS-D62) | Validée le 14 novembre 2026 (questionnaire), réalisée : demande de fusion n° 17, surveillée par la session |

Décision du 14 novembre 2026, par questionnaire, après la mesure du lot 3 :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D68 | ROBINS-I en pause : la grille reste hors de la veille. Deux pistes sont inscrites sans être traitées : (1) la règle « sélection des participants » paraît trop sévère (« sérieux » 6 fois sur 10 au lot 3, surtout quand l'inclusion exige un suivi ou la survie après l'intervention) ; hypothèse non vérifiée sur le guide de l'outil ; (2) les domaines « non rapporté », surtout les données manquantes (4 fois sur 10), donnent encore « critique » en lecture stricte. La suite sera décidée avec les cohortes de patients traités (VS-D60). Reste de l'enveloppe de VS-D55 : 0,155 $, non dépensés. Options écartées : une séance sur la sélection des participants maintenant (environ 0,25 $) ; revoir tout de suite la lecture stricte de VS-D56 | Validée le 14 novembre 2026 (questionnaire) |

Décisions du 14 novembre 2026, par questionnaire, sur les cohortes de patients traités (VS-D60) ; dépôt de coordination lu au commit `2ec46e7` (paquet de contexte `991c143`) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D69 | Nouveau plan d'étude « étude observationnelle d'une intervention » (`observationnel_intervention`), envoyé vers ROBINS-I : les groupes comparés, ou le suivi avant-après, sont définis par un traitement, une technique ou un programme reçu en soins courants ou choisi par le patient, sans affectation pour l'étude (cohorte prospective ou rétrospective, base de données de soins, avant-après, série de patients traités). « Observationnel » reste pour les études d'exposition, de facteurs pronostiques ou descriptives (grille JBI à écrire) ; « interventionnel non randomisé » pour une intervention affectée dans le cadre de l'étude. Fondement vérifié : ROBINS-I couvre les cohortes où les groupes sont formés « during the course of usual treatment decisions » (Sterne et al., BMJ 2016) et les cohortes rétrospectives (manuel Cochrane, chapitre 25) ; ROBINS-E vise les expositions. Constat qui l'a motivée : 23 des 38 études du corpus ROBINS-I classées « observationnel », donc sans grille. La valeur nouvelle de la liste fermée de `docs/FICHE_V2.md` est déclarée au dépôt de coordination avant d'être écrite. Options écartées : élargir « interventionnel non randomisé » (étiquette trompeuse pour une cohorte de soins courants) ; ne rien changer | Validée le 14 novembre 2026 (questionnaire), réalisée : déclarée au dépôt de coordination (CHG-2026-0012, commit `36d4c9b`), écrite au commit `dd20036` avant la mesure ([résultats](../banc/resultats/2026-11-14-cohortes.md)) |
| VS-D70 | Budget d'IA de la mesure du plan d'étude seul : une enveloppe nouvelle de 0,35 $, qui s'ajoute aux 0,155 $ restants de VS-D55, soit 0,505 $ ; un lancement, plafond de 0,50 $. Mesure sur 86 articles : les 38 études du corpus ROBINS-I, 6 témoins d'exposition ou de facteurs pronostiques écartés du lot 3, les 25 articles du corpus « qualité », 10 fiches de 2026-S45 et 7 études diagnostiques hors corpus. Dépense réelle attendue : environ 0,33 $. Limite annoncée : toutes ces études ont déjà été vues par la session | Validée le 14 novembre 2026 (questionnaire), réalisée : estimation sans IA de 0,66 $ (lancement 43561977924), coût réel **0,345 $** (lancement 43562590400) ; reste 0,16 $ |
| VS-D71 | Seuil de réussite, fixé avant la mesure : ROBINS-I choisie pour au moins 34 études sur 38 du corpus ROBINS-I (90 %) ; au plus 1 témoin d'exposition sur 6 envoyé vers ROBINS-I ; sur les autres corpus, pas plus d'un article de moins qu'à la mesure de VS-D51 (24 sur 25 du corpus « qualité », 7 sur 7 hors corpus, 10 fiches sur 10) | Validée le 14 novembre 2026 (questionnaire). Mesuré : **atteint** ; ROBINS-I pour 36 études sur 38 (avant : 14), 0 témoin sur 6 envoyé vers ROBINS-I, corpus « qualité » 23 sur 25 (à la limite ; deux revues AMSTAR 2 sans lien avec le changement), 7 sur 7 hors corpus, 10 fiches sur 10 |
| VS-D72 | Ouvrir la demande de fusion sans attendre à la fin du travail (le plan d'étude n'est toujours pas branché sur la veille ; aucun fichier de la veille, de l'application ni des workflows ne change). La session la surveille et ne la fusionne jamais elle-même | Validée le 14 novembre 2026 (questionnaire), réalisée : demande de fusion n° 18, surveillée par la session |

Décision du 14 novembre 2026, par questionnaire, après la fusion de la demande n° 18 :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D73 | Suite du juge de fiabilité : diagnostic des quatre premières grilles (RoB 2, QUADAS-2, AMSTAR 2, AGREE II), sans IA et sans coût. Il porte sur leurs désaccords avec les revues, domaine par domaine, d'après les journaux des mesures déjà faites (dernière mesure complète : lancement 43378868507, consigne 4ce7fb70). La session revient avec les causes et un plan chiffré avant toute dépense. Constat qui l'a motivé : 20 jugements sur 25 à un cran au plus, quand une réponse fixe en obtient 18 ; fourchette trop large (9 articles sur 25). Options écartées pour l'instant : confirmer la règle des cohortes sur des études neuves ; les pistes ROBINS-I de VS-D68 ; une pause | Validée le 14 novembre 2026 (questionnaire), réalisée : le moteur donne le jugement global exact pour 13 articles sur 25, autant qu'une réponse fixe au niveau le plus sévère ([diagnostic](../banc/resultats/2026-11-14-diagnostic-quatre-grilles.md)) |

Décisions du 14 novembre 2026, par questionnaire, après le diagnostic (VS-D73) :

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D74 | Une mesure qui tranche, avant toute correction des quatre premières grilles : ajouter au corpus « qualité », sans IA (méthode VS-D32), 20 articles neufs que les revues jugent favorablement, puis mesurer le moteur actuel (consigne 4ce7fb70, inchangée). Règle de choix fixée avant : articles sous licence CC BY ou CC0 avec texte dans PubMed Central, jugés dans un tableau étude par étude par une revue sous licence CC BY ; jugement global favorable (AMSTAR 2 « élevée » ou « modérée » ; RoB 2 « faible » ; QUADAS-2 « faible » pour les quatre domaines de risque de biais) ; dans l'ordre du repérage, 3 au plus par revue source ; environ 8 revues AMSTAR 2, 6 essais RoB 2 et 6 études QUADAS-2, l'une complétant l'autre si elle en manque ; aucun article déjà présent dans un corpus | Validée le 14 novembre 2026 (questionnaire), réalisée avec un écart : **17 articles au lieu de 20** (11 revues AMSTAR 2, 3 essais RoB 2, 3 études QUADAS-2). Le repérage a parcouru 120 revues AMSTAR 2, 240 revues RoB 2 et 240 revues QUADAS-2 : les tableaux lisibles étude par étude sont rares pour RoB 2 et QUADAS-2 (souvent des figures). Vérifiés sans IA, 17 sur 17 conformes (lancement 43580024170). Mesure : le moteur retrouve le jugement de la revue pour 1 article sur 17 ([résultats](../banc/resultats/2026-11-14-quatre-grilles-lot-2.md)) |
| VS-D75 | Seuil de réussite des quatre premières grilles, qui remplace celui de VS-D39, sur le modèle de VS-D56, en lecture stricte : au moins 50 % des jugements globaux identiques au corrigé ; plus de jugements identiques qu'une réponse fixe donnant, pour chaque grille, le niveau le plus fréquent de ses corrigés ; aucun jugement plus favorable que le corrigé de deux crans. Il s'apprécie sur l'ensemble des articles mesurés avec la même consigne : les 25 articles du lancement 43378868507 et les 20 articles neufs. Le seuil de la fourchette (VS-D50) reste inchangé. Constat qui l'a motivé : une réponse fixe obtient 18 sur 25 avec le seuil de VS-D39 | Validée le 14 novembre 2026 (questionnaire). Mesuré le 14 novembre 2026 sur 42 articles (les 25 et 17 neufs) : **non atteint**. 14 jugements identiques sur 42 (33 %), contre 20 pour la réponse fixe ; aucun trop favorable de deux crans ; fourchette : 10 sur 42 ([résultats](../banc/resultats/2026-11-14-quatre-grilles-lot-2.md)) |
| VS-D76 | Budget d'IA de la mesure des quatre grilles : une enveloppe nouvelle de 0,60 $, qui s'ajoute aux 0,16 $ restants de VS-D70, soit 0,76 $ ; un lancement, plafond de 0,75 $ ; dépense réelle attendue : environ 0,40 $ pour 20 articles neufs. Le coût estimé est annoncé avant le lancement, le coût réel après | Validée le 14 novembre 2026 (questionnaire), réalisée : estimation sans IA de 0,64 $ (lancement 43580529821), coût réel **0,405 $** (lancement 43580986912) ; reste 0,355 $ |

**Numérotation.** Ce registre fait foi : les décisions y sont numérotées dans l'ordre où elles
sont prises. Le plan de Veille Santé (section 15) avait numéroté à l'avance des décisions
attendues, de D8 à D18 ; ces numéros ne correspondent pas à ceux du registre.

| Décision attendue dans le plan | Dans ce registre |
| --- | --- |
| D11, première partie : remplacer le tableau des étiquettes | VS-D14 pour le format ; la règle reste à arbitrer |
| D12 : anciens verdicts et quatre catégories | VS-D13 |
| D13 : avis juridique sur les textes intégraux | VS-D15 pour les passages publiés ; l'avis reste à demander |
| D14 : plateforme du service. Le plan l'appelle « VS-D14 » | Pas encore prise, pas encore numérotée ici |
| D16 : forme de la fiche | VS-D12. Le VS-D16 de ce registre porte sur la région anatomique |

## 7. Règles permanentes

- La publication hebdomadaire reste automatique et ne dépend d'aucun autre outil ni d'aucune
  autre application.
- Le transfert de connaissances vers Évalys suit un circuit distinct, sélectif, validé par un
  humain. Aucune fiche n'y part automatiquement.
- Aucune donnée de patient n'entre dans Veille Santé.
- Aucune fiche n'est modifiée ou retirée sans trace.
- `installation/*.yml` reste identique à `.github/workflows/*.yml` tant que ce dossier existe.
- Aucun secret dans le code ni dans `config.json`. L'historique Git n'est jamais réécrit, et
  aucune semaine publiée n'est supprimée de `site/data/`.

## 8. Options écartées

| Option | Raison |
| --- | --- |
| Utiliser un abonnement personnel à un assistant d'IA pour tous les lecteurs | Impossible techniquement et contractuellement |
| Application native distribuée par les magasins | Plus lourde ; l'application web installable suffit à ce stade |
| Comptes obligatoires | Accès sans compte retenu |
| Relecture humaine de chaque fiche avant publication | Incompatible avec une production automatique sans équipe |
| Question libre à l'IA depuis l'application | Chaque question serait facturée : le coût dépendrait du nombre de lecteurs |
