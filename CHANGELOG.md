# Journal des changements

Évolutions notables de Veille Santé, de la plus récente à la plus ancienne.
Les versions sont numérotées MAJEUR.MINEUR.CORRECTIF et étiquetées dans Git.

## Non publié

### Corrigé
- Registre : le retour sur les dix fiches venait d'une IA (ChatGPT), pas d'un comité d'experts. Correction tracée dans VS-D46 et en tête des deux comptes rendus, sans rien effacer (VS-D52).

### Modifié
- Lecture d'un texte intégral (`pipeline/texte.py`) : sur demande, les déclarations placées hors
  du corps de l'article (financement, liens d'intérêts, remerciements, notes de fin) sont lues
  aussi. Le banc d'essai de l'appréciation le demande ; l'extraction ne le demande pas, et reçoit
  le même texte qu'avant. Défaut trouvé à la première mesure de l'appréciation : pour 9 revues sur
  16, l'IA répondait que ces déclarations manquaient, alors qu'elle ne les avait pas reçues
  (VS-D40).
- Définitions du plan d'étude : « modèle de prédiction » ne couvre plus que le développement ou
  l'ajustement d'un modèle sur les données de l'étude ; évaluer un test, un score ou un algorithme
  déjà défini contre une référence relève de l'étude diagnostique. « Revue d'interventions » ne
  couvre plus les « expositions » : une revue de groupes ou de lieux est descriptive (VS-D48).
  Mesuré au second cycle (0,16 $) : grille du plan identique à celle des auteurs pour 23 articles
  sur 25 du corpus, avis du comité retrouvé pour 10 fiches sur 10, mais 4 études diagnostiques sur
  7 seulement hors corpus : le cas mixte (développer un modèle et évaluer un outil déjà défini)
  n'est pas résolu. Règle du cas mixte ajoutée (VS-D51) : 24 articles sur 25 du corpus et 7 études
  hors corpus sur 7, ces 7 n'étant plus indépendantes de la règle. Coût 0,16 $.
- Étude des protocoles et des suppléments (sans IA) : 11 revues sur 16 déclarent du matériel
  supplémentaire, surtout Word et PDF ; 9 sur 16 citent un numéro PROSPERO ; 1 sur 16 cite une
  liste des études exclues.
- Banc d'essai : le plan d'étude peut se mesurer seul (« plan_seul »), avec les études diagnostiques
  du corpus de chiffres relevés comme contrôle hors corpus (« plan_externe »). Le seuil de la
  fourchette du jugement global est fixé (VS-D50). Nouvelle étude sans IA des protocoles et des
  suppléments (`banc/supplements.py`, VS-D49).
- Contrôle du coût du banc d'appréciation : l'estimation, prudente, ne refuse plus un lancement
  qu'au-delà de 1,5 fois le plafond ; le coût réel déjà dépensé est vérifié avant chaque groupe de
  requêtes. L'estimation de la sortie est recalée sur les coûts réels.
- Banc d'essai de l'appréciation : il peut ne mesurer que le texte intégral (« niveaux ») et
  rejouer l'ancienne lecture (« sans_declarations »).
- `docs/FICHE_V2.md`, bloc « appreciation » : trois précisions, déclarées au dépôt de
  coordination avant d'être inscrites (CHG-2026-0009). Un champ de plus, `jugement_outil` ; la
  forme de `domaines` ; la liste fermée des domaines de chaque outil. Aucun champ retiré.
- Banc d'essai de l'extraction : il peut ne mesurer qu'une partie du corpus (« parties » : tout,
  cas mesurés depuis la séance 5, ou chiffres relevés). Son plafond fixe passe de 2 $ à 3 $ par
  lancement, parce que le corpus grossit (VS-D33).
- `CLAUDE.md` renvoie aux fiches de méthode de `.claude/skills/` (VS-D35). Les huit règles
  impératives et le format des messages n'y changent pas ; le détail du questionnaire de décision
  est désormais dans la fiche `questionnaire-decision`.
- Workflow « Banc d'essai » : il lance le banc demandé par la dernière ligne de
  `banc/lancement.json` (chaîne actuelle ou extraction), avec un plafond de coût fixe pour chaque
  banc. Une demande « sans IA » lit les textes et estime le coût sans rien dépenser.
- `CLAUDE.md`, règle 7 : un court passage exact d'un article sous licence CC BY ou CC0 peut être
  cité avec sa source (VS-D15). Tout autre texte d'article reste interdit dans le dépôt et les
  données publiques.
- Documentation remise à jour : `banc/README.md` indique que le banc d'essai est écrit et a
  tourné deux fois ; `docs/ARCHITECTURE.md` décrit ses deux workflows.

### Corrigé
- Contrôle des chiffres de la veille : il lit désormais les nombres écrits en toutes lettres
  au-delà de dix (« Seventy-four », « trente-deux ») et les décimales sans zéro initial
  (« P < .05 »). Ces formes faisaient écarter à tort des fiches justes : 8 sur 16 au banc d'essai
  du 11 novembre 2026. Un nombre absent de la source reste refusé.
- Contrôle des chiffres, suite (relecture du portail) : deux nombres séparés par une virgule sans
  espace (« 1.2,3.4 ») sont de nouveau lus tous les deux, et « between twenty and thirty » ne
  donne plus 50.

### Ajouté
- Grille ROBINS-I (VS-D54) pour les essais quasi randomisés et les études interventionnelles non
  randomisées, sur le modèle des autres grilles : sept domaines, tout jugement appuyé sur un passage
  vérifié par le code, « pas d'information » lu « non rapporté », jugement global et fourchette
  calculés par le code. Consigne à part (`appreciation_robins_i.txt`). Le plan d'étude envoie ces deux
  plans vers ROBINS-I au lieu de « aucune grille applicable ». Format de la fiche v2 précisé après
  déclaration au dépôt de coordination (CHG-2026-0011). Pas encore appelé par la veille.
- Corpus de référence ROBINS-I (`banc/corpus/robins_i.json`) : 21 études sous licence CC BY, avec
  le jugement ROBINS-I déjà publié dans un tableau par 10 revues sous licence CC BY, repérées sans IA
  parmi 477 revues candidates ; licences, recopie et texte intégral vérifiés par le code (21 sur 21).
  11 corrigés marqués contestés avant la mesure (études sans comparateur jugées « faible » ou
  « modéré » pour la confusion). Nouveaux modes de `banc/assembler_chiffres.py` : repérage des
  tableaux ROBINS-I et vérification du corpus.
- Mesure de ROBINS-I (`banc/resultats/2026-11-14-robins-i.md`, 0,58 $) : seuil de VS-D56 non
  atteint (1 jugement global identique sur 21, 0 sur 10 sans les corrigés contestés ; aucun jugement
  trop favorable). Le moteur juge la confusion « sérieux » pour les 21 études et ne trouve rien sur
  les écarts aux interventions pour 20 : en lecture stricte, « critique » partout. La grille est
  stable (67 jugements par domaine sur 70 identiques d'un lancement à l'autre). Le plan d'étude classe
  9 études du corpus « observationnel » : les revues appliquent ROBINS-I à des cohortes de patients
  traités. Non branché sur la veille.
- Phase 1, séance 7 (VS-D44) : le plan d'étude est établi avant le choix de la grille
  (`pipeline/plan_etude.py`, consigne `plan_etude.txt`) : liste fermée, passage vérifié par le
  code, grille déduite par une table. Quand aucune grille ne s'applique (essai quasi randomisé,
  modèle de prédiction, revue descriptive…), la réponse est « aucune grille applicable », avec le
  nom de la grille qui conviendrait. Pour AMSTAR 2, « non » exige un passage, un silence donne
  « non rapporté », et le jugement global s'accompagne d'une fourchette. Un champ « nature du
  jugement » dit ce que mesure l'axe qualité. Déclaré au dépôt de coordination (CHG-2026-0010).
  Plus d'appréciation sur résumé seul. Pas encore appelé par la veille.
- Première mesure de la séance 7 (`banc/resultats/2026-11-13-seance-7.md`) : le plan d'étude
  retrouve l'avis du comité pour 8 fiches sur 10 de 2026-S45, dont les deux essais quasi
  randomisés, et la grille des auteurs d'une revue pour 20 articles sur 25 du corpus. Défaut
  trouvé et non corrigé : la définition de « modèle de prédiction » est trop large et retire leur
  grille à 5 études diagnostiques sur 7. Sur 54 « non » des revues sources, 31 deviennent « non
  rapporté ». Coût 0,63 $.
- Phase 1, séance 6 : appréciation méthodologique d'une publication par l'outil adapté à son type
  d'étude (RoB 2, QUADAS-2, AMSTAR 2, AGREE II). `pipeline/appreciation.py` et la consigne
  `appreciation.txt` jugent chaque domaine ; le code exige un passage vérifié pour tout jugement
  favorable et calcule lui-même le jugement global. `pipeline/classement.py` et la consigne
  `classement.txt` proposent une catégorie d'importance de 1 à 4, bornée par des règles. La veille
  hebdomadaire n'utilise pas encore ces modules.
- `banc/corpus/qualite_lisible.json` : 25 articles sous licence CC BY dont le texte intégral se
  lit, avec le jugement de qualité déjà porté par une revue (16 revues, 7 études diagnostiques,
  2 essais).
- Banc d'essai de l'appréciation (`banc/banc_appreciation.py`) : écart en crans avec le corrigé,
  accord par domaine, abstention sur résumé seul, catégories sur des publications de 2026-S45.
  Seuils fixés avant la mesure (VS-D39).
- Première mesure de l'appréciation (`banc/resultats/2026-11-13-appreciation.md`) : les deux
  seuils sont atteints (18 jugements sur 25 à un cran au plus du corrigé, aucun plus favorable de
  deux crans), mais le moteur donne presque toujours le plus mauvais niveau et une réponse
  constante aurait obtenu le même score. Le jugement global et l'étiquette candidate ne sont pas
  branchés sur la veille. Dix publications de 2026-S45 appréciées et trente classées sont gardées
  dans `banc/resultats/2026-11-13-appreciation-s45.json`, sans passage d'article.
- Seconde mesure de l'appréciation, après correction de la lecture des déclarations (VS-D40) :
  7 des 9 revues concernées obtiennent maintenant la bonne lecture de leurs déclarations, mais le
  score global passe de 18 à 17 jugements sur 25, sous le seuil de 70 %. L'écart tient à un
  article au texte inchangé : 9 % des jugements par domaine changent d'un lancement à l'autre.
- Corpus de référence renforcé (VS-D32) : `banc/corpus/chiffres_releves.json` réunit 9 études
  diagnostiques, 10 méta-analyses et 1 revue systématique sous licence CC BY, avec 161 chiffres
  déjà relevés par les auteurs de 9 revues en accès libre. Personne n'a rempli de corrigé à la
  main. `banc/chiffres.py` fixe les règles de comparaison avant toute mesure ;
  `banc/assembler_chiffres.py` et le workflow « Corpus, chiffres relevés » lisent les tableaux
  des revues et vérifient chaque chiffre, sans IA.
- Banc d'essai de l'extraction : mesure des chiffres relevés, faite par le code et sans IA
  lectrice. Seuil fixé avant la mesure : 80 % des chiffres retrouvés à partir du texte intégral
  (VS-D34).
- Mesure de l'extraction sur le corpus renforcé, deux lancements (2,57 $) : à partir du texte
  intégral, 148 à 149 chiffres retrouvés sur 159, soit 93 % (études diagnostiques 58 sur 59,
  méta-analyses 88 à 89 sur 98) ; à partir du résumé seul, 113. Le seuil de 80 % est atteint. Les
  cas de la séance 5 ne changent pas : 24 réponses justes sur 32, seuil de 26 non atteint.
  Résultats, défauts trouvés et limites dans `banc/resultats/2026-11-12-chiffres-releves.md`.
- `.claude/skills/` : les sept fiches de méthode communes aux applications de l'écosystème,
  copiées du dépôt de coordination (consigne CONS-2026-11-12-01, VS-D35). Seule leur partie
  « Dans ce projet » est propre à Veille Santé.
- Phase 1, séance 5 : extraction des données d'une publication, chaque donnée avec son
  emplacement (bloc « extraction » de la fiche v2). `pipeline/texte.py` lit un résumé ou un texte
  intégral en blocs repérés ; `pipeline/extraction.py` et la consigne `extraction.txt` extraient
  les données, et le code contrôle chaque passage mot pour mot et chaque nombre. Une donnée non
  vérifiée est refusée et comptée. La veille hebdomadaire n'utilise pas encore ces modules.
- Banc d'essai de l'extraction (`banc/banc_extraction.py`) : contrôles du code, sens de l'effet
  sur 32 questions corrigées, recoupement avec les passages des annotateurs, pièges, coût réel par
  article. Seuils de réussite fixés (VS-D25).
- Première mesure de l'extraction, sur quatre lancements : 23 réponses justes sur 32 à partir du
  texte intégral, 13 à partir du résumé seul, contre 7 pour la chaîne actuelle ; 3 pièges sur 3 ;
  326 données gardées sur 327. Le seuil de 26 n'est pas atteint. Relecture indépendante de dix
  publications réelles de 2026-S45 : aucun chiffre contraire à son passage, 1 erreur grave de sens.
  Résultats et limites dans `banc/resultats/2026-11-12-extraction.md`.
- `banc/corpus/corriges_contestes.json` : dix questions du corpus dont le corrigé est contesté,
  avec leur preuve. Elles restent dans le corpus ; le banc de l'extraction donne un second score
  sur les 22 autres (VS-D29).
- `docs/FICHE_V2.md`, quatre précisions du bloc « extraction » (VS-D30, déclaration
  CHG-2026-0007) : forme des événements indésirables et de l'emplacement, valeur `sans_objet` du
  sens d'un résultat, champ `comparaison` d'un résultat.
- Phase 1, séance 4 : `pipeline/acces.py` cherche le texte intégral légal d'une publication, lit
  sa licence et attribue un niveau d'accès ; `banc/mesure_acces.py` et le workflow « Niveaux
  d'accès » mesurent ces niveaux sur une semaine déjà publiée. Aucune IA n'est appelée, aucun
  texte d'article n'est gardé, et la veille hebdomadaire n'utilise pas encore ce module.
- Première mesure des niveaux d'accès, sur 2026-S45 : 61 % des fiches ont un texte intégral
  lisible dans PubMed Central, 34 % sous une licence CC BY. Résultats dans
  `banc/resultats/2026-11-12-niveaux-acces-S45.md`. La mesure a désormais une durée maximale et
  rend toujours un résultat.
- Licences admises pour l'analyse du texte intégral : CC BY et CC0 seulement (VS-D21).
- `docs/FICHE_V2.md` : format cible d'une fiche, la « fiche v2 », décidé le 12 novembre 2026
  (VS-D12 à VS-D15). Fiche unique progressive avec l'impact clinique dans l'en-tête, niveau
  d'accès et profondeur d'analyse, données extraites avec leur emplacement, catégorie d'importance
  à la place du verdict, étiquette à quatre valeurs, version et historique. Le moteur et
  l'application ne changent pas : la veille publie le format actuel jusqu'à la bascule.
- `docs/FICHE_V2.md`, compléments demandés par le portail et par Évalys : région anatomique prise
  dans une liste commune de dix régions (`classement.themes.region`, VS-D16, POR-D22), liste des
  cinq types d'étude actuels, date de mise en ligne de l'article (`publication.date_en_ligne`,
  VS-D19).
- Corpus de référence, suite : cas « qualité méthodologique » (`banc/corpus/qualite.json` : RoB 2,
  QUADAS-2, AMSTAR 2, AGREE II, tirés de revues sous licence CC BY) et trois pièges
  (`banc/corpus/pieges.json`). `banc/extraire_tableaux.py` repère les tableaux d'évaluation dans
  ces revues. Aucune IA n'est appelée.
- `CLAUDE.md` : consignes de travail pour les sessions de développement (règles impératives,
  circuit d'une modification, communication, coordination avec les autres applications).
- `banc/assembler_essais.py` et le workflow « Corpus de référence » : assemblage des premiers cas
  du corpus de référence à partir du jeu de données public Evidence Inference (licence MIT).
  Aucune IA n'est appelée.

## 1.1.1 — 11 novembre 2026

### Ajouté
- Documentation technique dans le dépôt : `docs/ARCHITECTURE.md` (comment l'ensemble est
  construit) et `docs/DECISIONS.md` (registre des décisions et de leurs raisons).

### Modifié
- Le numéro de version est aussi affiché en tête de la page « À propos » : en bas de la page
  « Semaine », il fallait faire défiler toutes les fiches pour l'atteindre.

### Corrigé
- Référence d'une fiche : plus de double point après un titre terminé par un point, ni de point
  après un titre terminé par un point d'interrogation.

## 1.1.0 — 11 novembre 2026 (socle et transparence)

### Ajouté
- Tests automatiques à chaque modification (`.github/workflows/tests.yml`) : tests du moteur,
  démonstration complète avec IA simulée, et vérification que `installation/` reste identique
  aux workflows.
- Mémoire de chaque veille : après la publication, un résumé chiffré est écrit dans le journal
  du lancement et les données de travail sont gardées 90 jours en artefact. Le fichier des
  références, qui contient les résumés des articles, n'est pas copié.
- `scripts/resume_travail.py` : résumé chiffré d'un dossier de travail (étiquettes de départ,
  abaissements par l'IA, verdicts, motifs d'exclusion et de rejet).
- Niveau d'accès documentaire affiché sous chaque fiche : « Analyse à partir du résumé
  uniquement » tant que le moteur ne lit pas le texte intégral.
- `.gitignore` et ce journal des changements.
- Numéro de version affiché en bas de chaque page de l'app.

### Modifié
- Avertissement sur l'IA : texte court sous chaque fiche, texte complet sur la fiche seule et
  sur la page « À propos », qui explique l'absence de relecture humaine et les limites.
- Consigne de rédaction, correctif provisoire : l'étiquette de preuve n'est plus abaissée pour
  une information absente du résumé ; les verdicts « confirme » et « remet en question » sont
  mieux définis. Ce correctif sera remplacé par la refonte du niveau de preuve.
- `config.json` : adresse du site renseignée.
- Mise à jour de l'app : en ligne, la dernière version est chargée dès l'ouverture, et la copie
  gardée sur l'appareil ne sert plus que sans connexion. Auparavant, une mise à jour pouvait ne
  jamais arriver sur un téléphone. Quand une nouvelle version s'installe, l'app se recharge seule.

### Supprimé
- `.github/worklows/site.yml` : doublon mal orthographié de `.github/workflows/site.yml`,
  sans effet.

## 1.0.0 — 9 novembre 2026

Première version en production.

- Veille hebdomadaire automatique : collecte PubMed et HAS, tri et rédaction par IA en
  traitement différé, contrôle des chiffres et des DOI, synthèses par sous-champ, publication.
- Application web installable, sans compte : profil par profession et sous-champ, fiches
  dépliables, archive et recherche, favoris, export RIS, partage.
- Première veille publiée : semaine 2026-S45, 710 fiches.
