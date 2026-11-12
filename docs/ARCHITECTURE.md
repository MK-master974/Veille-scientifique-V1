# Architecture technique

Description de Veille Santé telle qu'elle existe dans ce dépôt, version 1.1. Ce document suit le
code : toute modification de l'architecture doit y être reportée dans le même changement.

Voir aussi [DECISIONS.md](DECISIONS.md) pour les décisions et leurs raisons, et
[../CHANGELOG.md](../CHANGELOG.md) pour l'historique des versions.

## Vue d'ensemble

```
GitHub Actions — workflow « Veille hebdomadaire », toutes les heures le lundi et le mardi (UTC)
  python -m pipeline.run avancer          (l'état de la semaine est gardé dans le cache d'Actions)
    1. collecte      PubMed (API E-utilities) + flux RSS de la HAS
    2. tri           IA, une requête par référence (traitement différé)
       règles fixes  étiquette de départ, exclusions        (pipeline/regles.py)
    3. rédaction     IA, une requête par étude retenue (traitement différé)
    4. contrôle      structure, chiffres contre la source, Crossref (DOI, rétractations)
    5. synthèses     IA par sous-champ, avec version de secours sans IA
    6. publication   site/data/*.json → commit « Veille AAAA-Sxx » → déploiement GitHub Pages
                     puis résumé chiffré dans le journal et données de travail en artefact
    7. notification  OneSignal, au lancement suivant, entre 7 h 30 et 21 h (heure de Paris)

Navigateur → application web statique (site/), qui lit site/data/*.json
             profil et favoris dans le stockage local, aucun appel à l'IA
```

L'application ne contacte jamais l'IA. Le coût dépend donc du nombre de publications traitées,
pas du nombre de lecteurs.

## Arborescence

| Chemin | Rôle |
| --- | --- |
| `config.json` | Réglages : modèles, prix, budget, collecte, seuils, publication, mentions, fiches retirées |
| `requirements.txt` | Dépendance unique : `requests` |
| `pipeline/run.py` | Point d'entrée, machine à états `Veille`, commandes |
| `pipeline/collecte.py` | PubMed (esearch, efetch, lecture du XML) et HAS (flux RSS et page) |
| `pipeline/etapes.py` | Construction des requêtes d'IA et lecture des réponses, étape par étape |
| `pipeline/ia.py` | Fournisseurs OpenAI (différé et direct), Mistral (direct), démonstration ; estimation des coûts |
| `pipeline/regles.py` | Étiquettes, verdicts autorisés, ordre d'affichage, priorité de sélection |
| `pipeline/controle.py` | Contrôle de structure, contrôle des chiffres, Crossref |
| `pipeline/publication.py` | Écriture de `site/data/` : semaine, index, recherche, catalogue, réglages publics |
| `pipeline/notifications.py` | Messages OneSignal par profession, récapitulatif mensuel |
| `pipeline/semaines.py` | Semaines ISO, du lundi au dimanche, heure de Paris |
| `pipeline/reseau.py` | Requêtes HTTP avec nouvelles tentatives sur les erreurs passagères |
| `pipeline/config.py` | Chargement de la configuration, du catalogue et des consignes |
| `pipeline/acces.py` | Recherche du texte intégral légal, licence et niveau d'accès. Pas encore appelé par la veille |
| `pipeline/texte.py` | Lecture d'une publication en blocs repérés (résumé, sections, tableaux, figures) et recherche d'un passage mot pour mot. Pas encore appelé par la veille |
| `pipeline/extraction.py` | Extraction des données d'une publication et contrôle de chaque donnée par le code. Pas encore appelé par la veille |
| `pipeline/catalogue.json` | Professions et sous-champs |
| `pipeline/prompts/` | Consignes de l'IA : `tri.txt`, `redaction.txt`, `synthese.txt` ; `extraction.txt` pour la future fiche v2 |
| `site/index.html`, `app.js`, `styles.css` | Application web, sans dépendance |
| `site/sw.js` | Service worker : lecture hors ligne et mises à jour |
| `site/manifest.webmanifest`, icônes | Installation sur l'écran d'accueil |
| `site/push/onesignal/` | Service worker de OneSignal, dans un dossier séparé |
| `site/data/` | Données publiées, alimentées par le moteur |
| `.github/workflows/veille.yml` | Veille hebdomadaire et déploiement après publication |
| `.github/workflows/site.yml` | Mise en ligne du site, sur modification ou à la demande |
| `.github/workflows/tests.yml` | Tests automatiques à chaque modification |
| `installation/` | Copies de `veille.yml` et `site.yml`, tenues identiques aux originaux |
| `scripts/demo.py` | Site de démonstration : vrai moteur, IA simulée |
| `scripts/resume_travail.py` | Résumé chiffré d'un dossier de travail |
| `demo/` | Quatre publications réelles et les réponses d'IA simulées |
| `tests/` | Tests du moteur, de la chaîne complète, de l'extraction, des bancs d'essai et de l'assemblage du corpus, sans réseau |
| `banc/` | Corpus de référence et bancs d'essai : chaîne actuelle (`banc.py`), extraction (`banc_extraction.py`), lanceur (`lancer.py`) ; résultats dans `banc/resultats/` |
| `.github/workflows/corpus.yml` | Assemblage du corpus de référence, à la demande |
| `.github/workflows/banc.yml` | Banc d'essai demandé par `banc/lancement.json` : appelle l'IA, a un coût, ne se lance que sur demande |
| `.github/workflows/banc-lecture.yml` | Lecture du détail d'un résultat du banc, sans IA |
| `.github/workflows/acces.yml` | Mesure des niveaux d'accès sur une semaine publiée, sans IA |
| `CLAUDE.md` | Consignes de travail pour les sessions de développement |

## Le moteur (`pipeline/`)

### Commandes

```bash
python -m pipeline.run semaine [AAAA-Sxx]       # affiche « semaine=AAAA-Sxx » (par défaut, la semaine précédente)
python -m pipeline.run avancer [--semaine AAAA-Sxx] [--sans-echeance] [--sans-attente]
python -m pipeline.run initialiser              # écrit catalogue, réglages publics et index vide dans site/data/
python scripts/resume_travail.py travail/AAAA-Sxx   # résumé chiffré d'une semaine
```

- `--sans-echeance` : utilisé par les lancements manuels.
- `--sans-attente` : en traitement différé, attend sur place la fin des lots. Utile en local.

### Machine à états

La classe `Veille` de `run.py` suit les étapes
`collecte → tri → redaction → controle → synthese → publication → notification → termine`.
Chaque lancement enchaîne les étapes jusqu'à ce qu'il faille attendre (un lot en cours, l'heure
de notification), puis s'arrête. Le lancement suivant reprend où le précédent s'est arrêté.

Les fichiers de travail sont dans `travail/<semaine>/` :

| Fichier | Contenu |
| --- | --- |
| `etat.json` | Étape, lots, coûts, statistiques, journal, sélection |
| `references.json` | Références collectées, avec leur résumé |
| `tri.json` | Décision du tri pour chaque référence, caractéristiques relevées, étiquette de départ |
| `redaction.json` | Réponses brutes de l'IA de rédaction |
| `fiches.json` | Fiches conformes |
| `rejets.json` | Fiches écartées au contrôle, avec leurs motifs |
| `syntheses.json` | Synthèses par sous-champ |

Ce dossier n'est pas dans le dépôt. Il est sauvé et restauré par `actions/cache`, avec la clé
`travail-<semaine>-<run_id>-<attempt>` et une restauration par le préfixe `travail-<semaine>-`.
GitHub supprime un cache après 7 jours sans usage : c'est pourquoi, une fois la veille publiée,
le dossier est aussi gardé 90 jours en artefact (voir « Workflows »).

### Calendrier

- **Semaine traitée** : la semaine ISO précédente, du lundi au dimanche, heure de Paris.
- **Collecte** : pas avant le lundi 05:00 UTC. PubMed date ses entrées à l'heure de la côte est des
  États-Unis ; il faut que le dimanche y soit terminé.
- **Semaine déjà publiée** : une semaine présente dans `site/data/index.json` n'est pas retraitée.
- **Notification** : au lancement qui suit la publication, entre `notifier_a_partir_de` (7 h 30)
  et 21 h, heure de Paris.
- **Récapitulatif mensuel** : le premier lundi du mois, pour les abonnés « mensuel ».
- **Échéance** : mardi 23 h, heure de Paris. Au-delà, le lancement échoue et GitHub envoie un
  e-mail d'alerte. Les lancements manuels n'ont pas d'échéance.

### Collecte (`collecte.py`)

**PubMed**

- `esearch` avec `usehistory=y`, puis `efetch` en XML par paquets de 200.
- Paramètres `tool=veille-sante`, `email` si `email_contact` est renseigné, `api_key` si le secret
  `NCBI_API_KEY` existe. Pause de 0,12 s avec clé, 0,4 s sans.
- Requête construite par `requete_pubmed()` :

  ```
  (AAAA/MM/JJ:AAAA/MM/JJ[edat]) AND (systematic review[pt] OR meta-analysis[pt]
   OR randomized controlled trial[pt] OR guideline[pt] OR practice guideline[pt]
   OR Diagnosis/Narrow[filter]) AND hasabstract AND (eng[la] OR fre[la])
   NOT (retracted publication[pt] OR retraction of publication[pt] OR comment[pt] OR letter[pt]
   OR editorial[pt] OR clinical trial protocol[pt] OR preprint[pt] OR published erratum[pt])
   NOT (animals[mh] NOT humans[mh])
  ```

- La lecture du XML écarte aussi les articles signalés rétractés ou sous réserve.
- Champs gardés : PMID, DOI, titre, résumé avec ses sections, revue, date, volume, numéro, pages,
  auteurs, types de publication, langue, mots-clés MeSH.

**HAS**

- Flux RSS `https://www.has-sante.fr/feed/Rss2.jsp?id=p_3081452`, articles de la semaine, avec le
  texte de la page (8 000 caractères au plus).
- Une panne de la HAS ne bloque pas la veille : le journal l'indique et la collecte continue.

**Ensemble**

- Dédoublonnage par DOI, puis tri par priorité : HAS et recommandations, revues et méta-analyses,
  essais, puis le reste. Si le budget coupe la liste, c'est la fin qui saute.
- Plafond : `max_references` (6 000).

### IA (`ia.py`, `etapes.py`, `prompts/`)

- **Requêtes** : la consigne est le message système, la référence est le message utilisateur.
  Réponse demandée en JSON ; elle est lue même entourée de texte ou de balises de code.
- **Traitement différé (par défaut, OpenAI)** : un fichier de requêtes par étape, résultats sous
  24 heures, à moitié prix. Un lot en échec est resoumis une fois ; au second échec, le lancement
  échoue. Les réponses manquantes d'un lot terminé sont reprises en mode direct.
- **Mode direct** : 8 requêtes en parallèle. Utilisé par les lancements manuels « Tout traiter en
  une fois » et par Mistral.
- **Garde-fous** :
  - coût estimé à 1 jeton pour 3 caractères, avec les prix de `prix_usd_par_million` ;
  - budget hebdomadaire `budget_max_usd_semaine` : la moitié au plus pour le tri, 85 % du reste
    pour la rédaction, réduction par pas de 10 % ;
  - échec du lancement si plus de 30 % des réponses manquent au tri ou à la rédaction. Les
    synthèses en sont exemptées : elles ont une version de secours sans IA.

**Consignes**

| Consigne | Entrée | Sortie |
| --- | --- | --- |
| `tri.txt` | Une référence et le catalogue | Inclusion, motif d'exclusion, type d'étude, pertinence (1 à 3), domaines (1 à 4), effectif, GRADE, majorité d'essais randomisés, accord d'experts, plan diagnostique |
| `redaction.txt` | La référence et le classement du tri | Titre français, étiquette et sa justification, verdict, résumé flash, résultats, impact clinique, limites, méthode, version vulgarisée, chiffres cités, incertitudes |
| `synthese.txt` | 40 fiches au plus d'un sous-champ | Trois listes de phrases : ce qui change la pratique, à surveiller, remis en question |

### Règles (`regles.py`) et contrôle (`controle.py`)

- **Étiquette de départ** : fixée par le code selon le type d'étude et les caractéristiques
  relevées au tri (tableau dans [DECISIONS.md](DECISIONS.md)). Quand l'information manque, la
  valeur la plus prudente est retenue.
- **Abaissement** : l'IA de rédaction peut abaisser l'étiquette, jamais la remonter
  (`plafonner_etiquette`).
- **Verdict** : « change la pratique » n'est accepté que pour une recommandation, ou une revue ou
  méta-analyse d'étiquette « solide » ; sinon il devient « à surveiller » (`verdict_autorise`).
- **Contrôle de chaque fiche** :
  - structure : champs obligatoires, valeurs valides, résumé flash de 60 mots au plus ;
  - chiffres : tout nombre des champs rédigés doit figurer dans la source (titre, résumé, revue,
    mots-clés, année, PMID). La virgule décimale, les séparateurs de milliers et les décimales
    sans zéro initial (« .05 ») sont tolérés, ainsi que les nombres écrits en toutes lettres dans
    la source, en anglais ou en français, et les ordinaux anglais (« first ») ;
  - grande nouveauté : le domaine transversal est ajouté si la pertinence vaut 3 et que le verdict
    est « change la pratique » ou « remet en question ».
- **Crossref** : le DOI est retiré si le titre déclaré diffère trop (similarité inférieure à 0,6)
  ou s'il est introuvable ; l'étude est exclue si un avis de rétractation existe. Une panne de
  Crossref ne pénalise pas la fiche.
- **Synthèses** : chaque phrase est validée (fiche connue, verdict cohérent, 45 mots au plus,
  chiffres présents dans la fiche). Un bloc vide est complété sans IA.

### Accès au texte intégral (`acces.py`)

Module de la phase 1, séance 4. **La veille hebdomadaire ne l'appelle pas** : il sert à la mesure
des niveaux d'accès et servira à la future chaîne d'analyse (bloc `acces` de la fiche v2).

- **Sources** : Europe PMC pour l'identifiant PubMed Central, la licence déclarée et le texte
  intégral en XML des articles en accès ouvert ; PubMed pour recouper l'identifiant.
- **Licence** : ramenée à une classe fixe (CC0, CC BY, CC BY-NC…, « autre », « inconnue »). Une
  licence inconnue ou propriétaire ne donne jamais mieux que « résumé uniquement ».
- **Niveau d'accès** : 1 si le texte a un corps d'au moins 5 000 caractères et deux parties, 2 s'il
  est partiel, 3 sinon. Seules les licences CC BY et CC0 ouvrent le niveau 1 (VS-D21).
- **Aucun texte d'article n'est gardé** : seules des mesures de sa structure le sont.

### Lecture d'une publication et extraction (`texte.py`, `extraction.py`)

Modules de la phase 1, séance 5. **La veille hebdomadaire ne les appelle pas** : ils produisent le
bloc `extraction` de la fiche v2 ([FICHE_V2.md](FICHE_V2.md)) et sont mesurés par
`banc/banc_extraction.py`.

- **Lecture** (`texte.py`) : une publication devient une suite de blocs repérés. `R` est le
  résumé ; `S1`, `S2`… les sections, avec le chemin de leurs titres ; `T1`… les tableaux, lus
  ligne par ligne ; `F1`… les légendes de figures. La source est le résumé de PubMed (niveau
  d'accès 3) ou le texte intégral au format JATS d'Europe PMC (niveau 1). Les références
  bibliographiques ne sont pas lues. Un tableau fourni en image est signalé comme non lu. Au-delà
  de 120 000 caractères, des sections qui ne sont ni la méthode ni les résultats sont laissées de
  côté, et le document le dit.
- **Protection** : le texte remis à l'IA est placé entre deux marques, que l'article ne peut pas
  imiter, et la consigne dit qu'il s'agit d'une donnée, jamais d'une instruction. Une consigne
  trouvée dans l'article est signalée, pas suivie.
- **Extraction** (`extraction.py`, consigne `extraction.txt`) : l'IA propose la question, la
  population, l'effectif, l'intervention, le comparateur, les résultats et les événements
  indésirables. Chaque donnée vient avec le repère d'un bloc et un passage.
- **Contrôle par le code**, donnée par donnée :
  - le passage doit se retrouver mot pour mot dans le texte lu ; seules la casse, les espaces et
    la typographie (guillemets, tirets) sont ignorées. L'emplacement gardé est celui où le passage
    se trouve réellement, et l'extrait gardé est recopié du texte lu, pas de la proposition ;
  - les nombres de la valeur, de l'intervalle et de p doivent figurer dans le passage, ou au moins
    dans le bloc cité (écart noté). Un nombre absent du bloc ou du texte fait refuser la donnée ;
  - une valeur fermée invalide ou incohérente est ramenée à la plus prudente (`non_precise`,
    `non_rapporte`, `indetermine`) ;
  - une estimation hors de son intervalle, ou un p qui contredit le sens annoncé, lève un signal
    sans refuser la donnée.
- **Une donnée refusée n'est ni corrigée ni gardée** : elle est comptée, avec son motif.
- **Passage publié** seulement quand le texte lu est sous licence CC BY ou CC0 (VS-D15) ; sinon
  seul l'emplacement est gardé.
- **Fiche de repérage** : `reduire_au_reperage` ne garde que le résultat principal, et les
  événements indésirables s'ils sont rapportés.

## Données publiées (`site/data/`)

| Fichier | Contenu |
| --- | --- |
| `index.json` | Semaines publiées, de la plus récente à la plus ancienne, et années de recherche |
| `semaines/AAAA-Sxx.json` | Statistiques, fiches dans l'ordre d'affichage, synthèses par domaine |
| `recherche/AAAA.json` | Index compact par année : identifiant, semaine, titres, domaines, type, étiquette, verdict, pertinence, revue |
| `catalogue.json` | Copie de `pipeline/catalogue.json` |
| `config.json` | Réglages publics : nom, e-mail de contact, éditeur, hébergeur, fiches retirées |

Une fiche porte son identification (`id`, PMID, DOI, lien), sa référence, son classement (type,
pertinence, domaines, étiquette et justification, verdict) et son contenu (résumé flash,
résultats et impact, méthode et limites, version vulgarisée, incertitudes).

Une publication n'a qu'une fiche, même classée dans plusieurs domaines.

**Format cible.** Ce qui précède décrit le format actuel d'une fiche. Le format qui le remplacera
à la fin de la phase 1, la « fiche v2 », est décrit dans [FICHE_V2.md](FICHE_V2.md). Il n'est
produit ni par le moteur ni par l'application pour l'instant.

## L'application web (`site/`)

- **Un seul fichier JavaScript**, sans bibliothèque ni appel à un service tiers. OneSignal n'est
  chargé que si le lecteur active les notifications.
- **Adresses** : `#semaine`, `#semaine-AAAA-Sxx`, `#fiche-AAAA-Sxx-<id>` (lien partagé),
  `#archive`, `#favoris`, `#profil`, `#apropos`, `#bienvenue`.
- **Stockage local** : `vs.profil` (domaines suivis, intérêt et détail par domaine, notifications)
  et `vs.favoris` (copies des fiches, lisibles hors ligne).
- **Filtrage** : une fiche est visible si l'un de ses domaines suivis la montre. « Expert »
  montre tout, « praticien » une pertinence de 2 et plus, « culture générale » une pertinence
  de 3.
- **Avertissement** : sous chaque fiche, le niveau d'accès documentaire (« Analyse à partir du
  résumé uniquement » tant que le moteur ne lit pas le texte intégral) et l'absence de relecture
  humaine. Le texte complet figure sur la fiche seule et sur la page « À propos ».
- **Version** : la constante `VERSION_APP` de `app.js` est affichée en bas de chaque page et en
  tête de la page « À propos ». Elle suit le journal des changements.

### Hors ligne et mises à jour (`sw.js`)

- En ligne, l'application et les données sont prises sur le réseau en priorité. La copie gardée
  sur l'appareil ne sert que sans connexion, ou si le réseau met plus de quatre secondes à
  répondre.
- Quand une nouvelle version du service worker s'installe, les pages ouvertes sont rechargées une
  fois. Seules les copies locales de cette application sont supprimées.
- Les adresses `/push/onesignal/` ne sont pas interceptées.
- Le service worker n'est enregistré qu'en HTTPS.

## Workflows (`.github/workflows/`)

**`veille.yml`**

- Déclencheurs : toutes les heures le lundi et le mardi (UTC), et lancement manuel avec le choix
  de la semaine et du mode direct. GitHub ne garantit pas l'heure exacte des lancements planifiés.
- Tâche `veille` : installation, calcul de la semaine, restauration du cache de travail,
  `pipeline.run avancer` avec les secrets, sauvegarde du cache. Si une publication a eu lieu :
  commit de `site/data` par `veille-sante[bot]`, résumé chiffré dans le journal, et dossier de
  travail gardé 90 jours en artefact, sans `references.json` (résumés d'articles, dépôt public).
  Ces deux dernières étapes ne peuvent pas faire échouer la veille.
- Tâche `deployer`, si publication : déploiement de `site/` sur GitHub Pages.

**`site.yml`** : redéploie l'application quand `site/**`, `config.json` ou le catalogue changent
sur `main`, ou à la demande. Un commit fait par le robot ne déclenche pas d'autre workflow :
c'est pourquoi `veille.yml` déploie lui-même.

**`tests.yml`** : à chaque modification, sur toutes les branches. Tests du moteur, démonstration
complète avec IA simulée, et vérification que `installation/` est identique aux workflows.

**`corpus.yml`** : à la demande. Assemble les cas du corpus de référence à partir d'un jeu de
données public, sans IA ni clé. Le résultat est écrit dans le journal et gardé en artefact.

**`banc.yml`** : lance le banc d'essai demandé par la dernière ligne de `banc/lancement.json`
(`banc/lancer.py`) : la chaîne d'analyse actuelle (`banc/banc.py`) ou l'extraction des données
(`banc/banc_extraction.py`). Rien n'est publié. Il appelle l'IA et a un coût : il ne se lance que
sur demande, par le bouton de lancement manuel ou quand `banc/lancement.json` est modifié sur une
branche `claude/**`. Le budget est vérifié avant tout appel, et borné par un plafond fixe pour
chaque banc. Une demande « sans IA » lit les textes et estime le coût, sans aucun appel. Le
journal et les résultats sont publics : aucun texte d'article n'y figure, hors courts passages
exacts d'articles sous licence CC BY ou CC0.

**`banc-lecture.yml`** : affiche dans le journal le détail d'un résultat du banc déjà produit, à
partir de son artefact. Aucune IA n'est appelée.

**`acces.yml`** : mesure, pour une semaine déjà publiée, la part des fiches dont le texte intégral
est accessible légalement, et sous quelle licence (`banc/mesure_acces.py`). Il lit les données
publiées sur `main`, interroge Europe PMC et PubMed, et ne garde aucun texte d'article. Aucune IA
n'est appelée. Il se lance à la demande, ou quand `banc/mesures_acces.json` est modifié sur une
branche de travail.

## Configuration

| Où | Quoi |
| --- | --- |
| `config.json` | Général (`nom_app`, `url_site`, `email_contact`), `ia`, `collecte`, `preuve`, `selection`, `publication`, `notifications`, `mentions`, `fiches_retirees`, `controle` |
| Secrets du dépôt | `OPENAI_API_KEY`, `NCBI_API_KEY` (facultatif), `ONESIGNAL_REST_API_KEY`, `MISTRAL_API_KEY` |
| Variables du dépôt | `URL_SITE`, `EMAIL_CONTACT`, `ONESIGNAL_APP_ID` : facultatives, elles remplacent `config.json` |
| Variables d'environnement du moteur | `VEILLE_CONFIG`, `VEILLE_TRAVAIL`, `VEILLE_FOURNISSEUR`, `VEILLE_MODE`, `VEILLE_EFFORT`, `VEILLE_SANS_RESEAU`, `VEILLE_REPONSES_DEMO` |

Aucun secret ne figure dans le code ni dans `config.json`, qui est public.

## Catalogue

Dix professions et 65 sous-champs, dans `pipeline/catalogue.json` : masso-kinésithérapie (13),
médecine (17), soins infirmiers (8), pédicurie-podologie (5), ergothérapie (5), orthophonie (5),
maïeutique (4), pharmacie (3), diététique (4), et un domaine transversal « grandes nouveautés en
santé ».

## Tests et démonstration

```bash
pip install -r requirements.txt pytest
python -m pytest tests                 # sans réseau ni clé
python scripts/demo.py apercu          # site de démonstration dans apercu/
python -m http.server -d apercu 8000   # à ouvrir sur http://localhost:8000
```

Les dossiers `apercu/`, `travail/` et les caches Python sont ignorés par Git.

## Limites connues de cette version

- **Analyse à partir du résumé seulement** : le texte intégral n'est pas lu. Chaque fiche le dit.
- **Mémoire limitée** : les données de travail d'une semaine sont gardées 90 jours, pas au-delà.
- **Données publiées par semaine entière** : un fichier de plusieurs mégaoctets, chargé d'un bloc.
- **Aucun service côté serveur** : le signalement d'une erreur passe par un e-mail.
- **Notifications** : le code existe, le service n'est pas configuré.
- **Dépendance aux fournisseurs** : les noms de modèles et les prix de `config.json` doivent
  suivre ceux du fournisseur d'IA.
