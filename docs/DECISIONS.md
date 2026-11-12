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

Décisions de coordination entre applications, relayées le 11 novembre 2026 :

| Référence | Décision |
| --- | --- |
| POR-D17 | Un préfixe par projet pour les décisions : `VS-` pour Veille Santé |
| POR-D18 | Dix codes communs pour le circuit des connaissances vers Évalys : `NON_SELECTIONNEE`, `A_EXAMINER`, `EN_EVALUATION`, `VALIDEE_TRANSMISSION`, `TRANSMISE`, `RECUE`, `INTEGREE`, `REFUSEE`, `DIFFEREE`, `A_ACTUALISER` |
| POR-D9 | Pilote du circuit vers Évalys sur le genou, cinq propositions au plus, sans modification clinique. Attend la fiche v2 de Veille Santé |
| POR-D12 | Veille Santé garde sa propre interface de gestion ; le portail n'en affiche qu'une synthèse. Interface reportée à la phase 4 |
| POR-D19 | Essai de format du circuit vers Évalys : seul du contenu déjà public dans ce dépôt, avec la mention « résumé uniquement, non destinée à l'intégration clinique ». Pas avant la fin de la phase 0 |
| POR-D21 | Un avis réglementaire commun aux applications, demandé après la bascule de la fiabilisation |

## 6. Décisions du 12 novembre 2026 : format « fiche v2 »

Séance 3 de la phase 1. Les quatre décisions ont été prises par questionnaire, après relecture du
brouillon. Le format est décrit dans [FICHE_V2.md](FICHE_V2.md). Rien ne change dans la veille
publiée avant la bascule, dernière séance de la phase 1.

| Référence | Décision | Statut |
| --- | --- | --- |
| VS-D12 | Fiche unique progressive : un en-tête toujours visible (question, résultat principal, impact clinique, limite principale), puis des sections à déplier. Remplace, à la bascule, les trois niveaux de détail du 1er novembre. Le réglage « niveau de détail » du profil sera revu en phase 3 | Validée |
| VS-D13 | La catégorie d'importance, de 1 à 4 et justifiée, remplace le verdict. « Confirme » et « remet en question » restent comme précision ; « change la pratique » correspond à la catégorie 1 ; « à surveiller » disparaît. Remplace, à la bascule, le verdict à quatre niveaux du 1er novembre. Constat : 707 fiches sur 710 portaient « à surveiller » en S45 | Validée |
| VS-D14 | L'étiquette de preuve prend quatre valeurs : solide, modéré, préliminaire, non évaluable. Remplace, à la bascule, l'étiquette à trois valeurs du 1er novembre. La règle d'attribution est réglée et mesurée au banc d'essai en séance 6 | Validée |
| VS-D15 | Un court passage exact d'un article n'est publié que si l'article est sous licence CC BY ou CC0, avec sa source. Pour tous les autres, seul l'emplacement est publié. La règle « ni résumé ni texte d'article » est complétée dans ce sens | Validée |

**Numérotation.** Ce registre fait foi : les décisions y sont numérotées dans l'ordre où elles
sont prises. Le plan de Veille Santé (section 15) avait numéroté à l'avance des décisions
attendues, de D8 à D18 ; ces numéros ne correspondent pas à ceux du registre.

| Décision attendue dans le plan | Dans ce registre |
| --- | --- |
| D11, première partie : remplacer le tableau des étiquettes | VS-D14 pour le format ; la règle reste à arbitrer |
| D12 : anciens verdicts et quatre catégories | VS-D13 |
| D13 : avis juridique sur les textes intégraux | VS-D15 pour les passages publiés ; l'avis reste à demander |
| D14 : plateforme du service. Le plan l'appelle « VS-D14 » | Pas encore prise, pas encore numérotée ici |
| D16 : forme de la fiche | VS-D12 |

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
