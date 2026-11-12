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
     dans la ligne du tableau source) et sa présence dans l'article lui-même.
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
- **Un chiffre absent de l'article est écarté du score avant la mesure**, et compté à part
  (VS-D34) : une revue arrondit, recalcule ou se trompe parfois en recopiant. C'est le code qui le
  constate, sur le texte de l'article, sans regarder ce que l'IA a extrait.
- **Mesure** : le banc de l'extraction cherche chaque chiffre dans la zone attendue des données
  extraites (le champ « effectif », ou les résultats). Aucune IA lectrice : le score ne varie pas
  d'un lancement à l'autre. Seuil : 80 % des chiffres retrouvés à partir du texte intégral.

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
- Le corpus ne contient que des essais randomisés pour le « sens de l'effet » : il ne mesure pas
  l'extraction sur une revue ou une étude diagnostique.
- Ces cas mesurent l'extraction et l'interprétation statistique, pas l'intérêt clinique d'un
  résultat pour un professionnel.
- Un corrigé peut lui-même contenir une erreur : un écart est un signal à examiner, pas une
  preuve.

## Sources écartées

Les revues Cochrane et les scores PEDro ne sont pas utilisés comme corrigés : leurs conditions
d'usage restreignent la fouille de textes et l'usage commercial.
