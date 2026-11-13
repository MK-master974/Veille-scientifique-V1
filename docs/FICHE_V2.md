# Fiche v2 — format d'une fiche de veille

Format cible d'une fiche, décidé par le porteur du projet le 12 novembre 2026 (décisions VS-D12 à
VS-D16, VS-D19 et VS-D30 de [DECISIONS.md](DECISIONS.md)).

**Ce format n'est pas encore produit.** Le moteur et l'application publient des fiches au format
actuel (« v1 », décrit dans [ARCHITECTURE.md](ARCHITECTURE.md)) jusqu'à la bascule, dernière
séance de la phase 1. Ce document sert de référence aux séances 4 à 10 et aux autres
applications de l'écosystème.

## Principes

1. **Une publication, une fiche.** L'identifiant est stable ; une publication classée dans
   plusieurs domaines garde une seule fiche.
2. **Fiche unique progressive** (VS-D12). Un en-tête toujours visible, puis des sections que le
   lecteur ouvre. Les niveaux Flash, Standard et Complet ne sont plus trois formats.
3. **Extraire, puis rédiger.** La synthèse est écrite à partir des données extraites, pas de
   l'article. Toutes les sections utilisent les mêmes données.
4. **La fiche dit ce qui a été lu et ce qui a été contrôlé.** Une section qui n'a pas pu être
   analysée reste vide et le dit : elle n'affiche pas une analyse qui n'a pas eu lieu.
5. **Les données bibliographiques viennent du code**, jamais de l'IA.
6. **Rien n'est remplacé en silence.** Toute modification crée une version et une ligne
   d'historique.

## Deux profondeurs, trois niveaux d'accès

Ces deux indications sont distinctes et affichées séparément.

| Profondeur | Traitement | Publications |
| --- | --- | --- |
| `reperage` | Tri et fiche courte, à partir du résumé | Toutes les publications retenues |
| `analyse` | Extraction complète, appréciation méthodologique, vérification indépendante, sur le texte intégral quand il est accessible légalement | Catégories 1 et 2, et domaines prioritaires |

| Niveau d'accès | Sens |
| --- | --- |
| 1 | Texte intégral lu |
| 2 | Texte partiel : des parties essentielles manquent |
| 3 | Résumé uniquement |

## Structure

« R » : présent dans une fiche de repérage. « A » : présent dans une fiche d'analyse.

### Identité (code)

| Champ | Contenu | R | A |
| --- | --- | --- | --- |
| `format` | `2` | oui | oui |
| `id` | Identifiant de la fiche, inchangé par rapport à la v1 : `pm<PMID>` ou `has<identifiant>` | oui | oui |
| `version` | Entier, à partir de 1 ; augmente à chaque modification | oui | oui |
| `statut` | `publiee`, `corrigee`, `suspendue` ou `retiree` | oui | oui |
| `dates` | `analyse`, `publication` (première mise en ligne), `mise_a_jour`, `semaine` | oui | oui |

### `publication` (code)

Source, PMID, DOI, lien, titre original, revue, année, volume, numéro, pages, auteurs, types de
publication déclarés par PubMed, langue, et `signalement` (`null`, `correction`, `reserve` ou
`retractation`). Aucun de ces champs n'est écrit par l'IA.

`annee` et `mois` restent la date du numéro de la revue, comme aujourd'hui. `date_en_ligne`
(VS-D19) porte la date de mise en ligne de l'article quand PubMed la donne, `null` sinon : les
deux peuvent tomber sur des années différentes, ce qui fausse une citation.

### `acces` (code)

| Champ | Contenu |
| --- | --- |
| `niveau` | 1, 2 ou 3 |
| `origine_texte` | D'où vient le texte lu : `null` pour le résumé seul, sinon l'archive ou la revue |
| `url_texte` | Lien vers le texte intégral légal, s'il existe |
| `licence` | Licence du texte lu, telle que la source la déclare ; `null` si elle est inconnue. Le texte intégral n'est lu que sous licence CC BY ou CC0 (VS-D21) |
| `consulte_le` | Date de consultation |
| `parties_lues`, `parties_non_lues` | Listes : résumé, méthode, résultats, tableaux, annexes… |

### `classement` (IA, bornée par des règles)

| Champ | Contenu |
| --- | --- |
| `type` | Type d'étude, compatible avec celui déclaré par PubMed. Valeurs : voir ci-dessous |
| `domaines` | Sous-champs du catalogue |
| `themes` | `pathologie`, `population`, `intervention`, `critere` : listes de termes libres, pour la recherche. `region` : liste de régions anatomiques, à vocabulaire fermé (VS-D16), voir ci-dessous |
| `categorie` | Catégorie d'importance, de 1 à 4 (VS-D13) |
| `justification_categorie` | Obligatoire. Pourquoi cette catégorie |
| `mise_en_avant` | Obligatoire en catégorie 1 : ce que la publication apporte de nouveau, ce qu'elle remet en question, si elle peut modifier les pratiques, le degré de certitude de cette lecture, les confirmations nécessaires |
| `sens_pratique` | `confirme`, `remet_en_question` ou `null` : précision gardée de l'ancien verdict |
| `pertinence` | 1 à 3, gardée telle quelle jusqu'à la refonte de la page de veille : le profil du lecteur s'en sert |

Types d'étude : `recommandation`, `revue_systematique`, `meta_analyse`, `essai_randomise`,
`etude_diagnostique`. Ce sont les cinq valeurs du moteur actuel (`TYPES` dans `pipeline/regles.py`).
La liste pourra s'élargir quand les règles d'inclusion seront revues ; ce n'est pas décidé.

Régions : `themes.region` ne prend que des valeurs de la liste commune aux applications de
l'écosystème, validée par le porteur du projet le 12 novembre 2026 (décision de coordination
POR-D22) : `genou`, `rachis-lombaire`, `epaule`, `cheville-pied`, `rachis-cervical`, `hanche`,
`rachis-thoracique`, `coude`, `poignet-main`, et `transversal` pour une publication qui concerne
tout le corps. Une fiche peut porter plusieurs régions ; la liste reste vide quand la publication
n'en concerne aucune. La liste est tenue dans le dépôt de coordination : une nouvelle région y
passe par une demande de fusion. Le domaine `kine/msk-membre-inf` couvre la hanche, le genou et
la cheville : il ne suffit pas à rapprocher une fiche d'une région d'Évalys. Le code `transversal`
d'une région n'a pas de rapport avec le domaine `transversal/grandes-nouveautes`.

Catégories : 1 « évolution potentielle des pratiques », 2 « apport scientifique important »,
3 « actualisation des connaissances », 4 « veille complémentaire ». La catégorie est indépendante
du niveau de preuve ; une publication n'est jamais mise en avant pour sa seule nouveauté.

### `extraction` (IA, vérifiée par le code)

Chaque donnée est « sourcée » : elle porte sa valeur et l'endroit où elle se trouve.

```json
{ "valeur": "…", "source": { "emplacement": "résumé | section : … | tableau 2 | figure 1", "passage": null } }
```

`emplacement` (précisé le 12 novembre 2026, VS-D30) est écrit par le code, à l'endroit où le
passage a été retrouvé dans le texte lu. Il prend l'une de ces quatre formes : « résumé » ;
« section : » suivi des titres de la section, du plus général au plus précis
(« section : Methods > Participants ») ; « tableau » et son numéro ; « figure » et son numéro.

| Champ | Contenu | R | A |
| --- | --- | --- | --- |
| `question` | Question étudiée | oui | oui |
| `population`, `effectif` | Population et effectifs | oui | oui |
| `intervention`, `comparateur` | Ou test évalué et test de référence pour une étude diagnostique | oui | oui |
| `resultats` | Liste, un élément par critère de jugement (voir ci-dessous) | principal | tous |
| `evenements_indesirables` | Rapportés ou non, et ce qui en est dit (forme ci-dessous) | si rapportés | oui |

Un résultat porte : `critere`, `comparaison` (`entre_groupes`, `avant_apres`, `descriptif`,
`non_precise`), `rang` (`principal`, `secondaire`, `non_precise`), `sens_mesure` (`augmente`,
`diminue`, `pas_de_difference`, `sans_objet`, `non_rapporte`), `en_faveur_de` (`intervention`,
`comparateur`, `aucun`, `indetermine`), `valeur`, `intervalle`, `p`, et sa `source`.

Trois précisions du 12 novembre 2026 (VS-D30), nées de la première mesure de l'extraction :

- **`comparaison`** dit ce que le résultat compare : deux groupes ou deux conditions
  (`entre_groupes`), un seul groupe suivi dans le temps (`avant_apres`), ou rien
  (`descriptif` : sensibilité d'un test, prévalence, recommandation, constat d'une revue). Un
  résultat `avant_apres` ou `descriptif` n'est jamais « en faveur de » l'intervention ni du
  comparateur : sans autre groupe, rien ne dit que l'évolution vient de l'intervention.
- **`sens_mesure` vaut `sans_objet`** pour un résultat descriptif. `non_rapporte` veut seulement
  dire : une comparaison est faite, mais le texte lu ne dit pas dans quel sens.
- **`evenements_indesirables`** est un objet : `rapportes` (`true`, `false`, ou `null` quand le
  texte dit qu'ils sont rapportés sans passage vérifiable), `valeur` (ce qui en est dit, ou
  `null`) et `source` (ou `null`).

`sens_mesure` et `en_faveur_de` sont deux champs séparés : une durée d'incapacité qui diminue est
un résultat favorable. Le banc d'essai du 11 novembre 2026 a montré que les confondre fait
compter comme inversé un résultat juste.

**Passage exact** (VS-D15). `emplacement` est toujours rempli. `passage` ne contient un court
extrait exact que si `acces.licence` est CC BY ou CC0 ; il reste `null` dans tous les autres cas,
y compris pour un résumé. Les passages des autres articles restent dans les données de travail,
qui ne sont pas publiées.

### `appreciation` (IA, bornée par des règles)

| Champ | Contenu |
| --- | --- |
| `plan_etude` | Plan réel de l'étude, établi avant le choix de l'outil : `plan` (liste fermée : `essai_randomise`, `essai_quasi_randomise`, `interventionnel_non_randomise`, `observationnel`, `etude_diagnostique`, `modele_de_prediction`, `revue_interventions`, `revue_descriptive`, `recommandation`, `autre`, ou `non_determine`), `source` (`emplacement`, `passage` vérifié par le code), `type_tri` et `ecart_avec_le_tri` |
| `outil` | `rob2`, `robins_i`, `amstar2`, `quadas2`, `agree2`, `autre` ou `aucun`. `aucun` quand aucune grille ne s'applique, avec `grille_manquante` (`robins_i`, `probast`, `robis`, `jbi` ou `null`) et `motif` ; le jugement est alors `non_evaluable`, sans note forcée |
| `jugement` | Qualité méthodologique : `elevee`, `moyenne`, `faible` ou `non_evaluable`. Déduite de `jugement_outil` |
| `nature_du_jugement` | Ce que mesure l'axe `jugement` : `risque_de_biais` (RoB 2, QUADAS-2) ou `fiabilite_de_la_methode` (AMSTAR 2, AGREE II). Jamais une certitude des preuves : celle-ci reste `grade_rapporte` |
| `fourchette` | `pire` et `meilleur`, dans les mots de l'outil : le jugement global si chaque domaine non évalué ou non rapporté valait le pire, puis le meilleur jugement possible. Calculée par le code. Si les deux sont égaux, `jugement_outil` les reprend ; sinon `jugement_outil` vaut `non_evaluable` |
| `jugement_outil` | Jugement global dans les mots de l'outil, calculé par le code. RoB 2 : `faible`, `quelques_reserves`, `eleve`. QUADAS-2 : `faible`, `incertain`, `eleve`. AMSTAR 2 : `elevee`, `moderee`, `faible`, `tres_faible`. AGREE II : `elevee`, `moyenne`, `faible`. Ou `non_evaluable` |
| `domaines` | Liste. Pour chaque domaine de l'outil : `domaine` (clé prise dans la liste fermée de l'outil), `jugement` (valeurs de l'outil, `non_evaluable`, ou `sans_objet` pour les trois questions d'AMSTAR 2 réservées aux méta-analyses ; pour AMSTAR 2 aussi `non_rapporte` : le texte intégral ne dit rien, ce qui n'est pas un défaut. `non` exige un passage qui montre que le critère n'est pas rempli), `justification`, `source` (`emplacement`, `passage`) |
| `precision_statistique` | Intervalles de confiance et taille d'effet, seulement s'ils figurent dans l'article ; aucun calcul inventé |
| `grade_rapporte` | Certitude GRADE telle que les auteurs la donnent ; `null` sinon. Jamais calculée pour une étude isolée |
| `etiquette` | Étiquette de façade : `solide`, `modere`, `preliminaire` ou `non_evaluable` (VS-D14) |
| `justification_etiquette` | Une phrase |

`non_evaluable` signifie « ce qui a été lu ne permet pas de juger ». Ce n'est pas une preuve
faible.

Aucune appréciation n'est faite sur résumé seul : le niveau d'accès « résumé uniquement » donne
`outil: aucun` et `motif: texte_integral_inaccessible` (mesure du 13 novembre 2026 : 33 articles sur
35 « non évaluable », et les 2 jugements rendus étaient trop sévères).

Domaines : 5 pour RoB 2, 7 pour QUADAS-2 (4 de risque de biais, 3 d'applicabilité), 16 pour
AMSTAR 2, 6 pour AGREE II. Leurs clés sont dans `pipeline/appreciation.py`. Ces trois précisions
(`jugement_outil`, forme de `domaines`, listes fermées) ont été déclarées au dépôt de coordination
avant d'être inscrites ici (CHG-2026-0009). Le plan d'étude, `outil: aucun`, `non_rapporte`, la
fourchette et `nature_du_jugement` l'ont été de même (CHG-2026-0010).

La règle qui attribue l'étiquette a été mesurée au banc d'essai en séance 6 : elle reste
candidate, et sa décision est reportée (VS-D41). Le jugement global n'est pas encore assez fiable
pour être publié : voir [les résultats](../banc/resultats/2026-11-13-appreciation.md).

### `synthese` (IA)

| Champ | Contenu |
| --- | --- |
| `titre_fr` | Titre français |
| `entete` | Toujours visible : `question`, `resultat_principal`, `impact_clinique`, `limite_principale` |
| `standard` | Contexte, objectif, population, méthode, intervention et comparateur, critères de jugement, résultats, interprétation, limites, pertinence clinique, conclusion prudente |
| `complet` | Analyse méthodologique et statistique, risque de biais, cohérence entre résultats et conclusion, applicabilité, certitude, points de vigilance |
| `vulgarise` | Version sans jargon, gardée pour le profil « culture générale » ; `null` sinon |
| `incertitudes` | Ce qui n'est pas rapporté ou reste incertain |

`impact_clinique` est obligatoire dans l'en-tête, pour les deux profondeurs : demande du porteur
du projet du 11 novembre 2026. Le « message essentiel » du cahier des charges est porté par le
couple résultat principal et impact clinique. Un champ de `complet` qui n'a pas pu être analysé
vaut `null`.

### `controles` et `provenance` (code)

- `controles` : liste des contrôles passés, chacun avec son `nom` et son `resultat` (`conforme`,
  `ecart_corrige`, `non_applicable`). La vérification indépendante y figure quand elle a eu lieu.
- `provenance` : version du moteur, nom des modèles d'IA par étape, version de chaque consigne.

### `historique` (code)

Une ligne par version : `version`, `date`, `nature` (`creation`, `correction`, `suspension`,
`retablissement`, `retrait`), `motif`, `elements_modifies`.

## Règles attachées au format

Le code les vérifie avant toute publication.

1. `id` ne change jamais ; `version` augmente de 1 à chaque modification, avec une ligne
   d'historique.
2. `passage` non vide exige une licence CC BY ou CC0 (VS-D15).
3. Tout nombre d'un champ rédigé figure dans une donnée extraite ou dans la source lue : c'est
   l'extension du contrôle des chiffres actuel.
4. Tout passage cité se retrouve mot pour mot dans le texte lu.
5. `justification_categorie` n'est jamais vide ; `mise_en_avant` est rempli en catégorie 1.
6. `grade_rapporte` n'est rempli que si la certitude figure dans le texte lu.
7. Aucun résumé ni texte d'article, hors les passages de la règle 2.

## De la v1 à la v2

| Fiche v1 | Fiche v2 |
| --- | --- |
| `id` | Inchangé : liens partagés et favoris continuent de fonctionner |
| `flash` | Remplacé par `synthese.entete` |
| `standard.impact_clinique` | `synthese.entete.impact_clinique` |
| `standard`, `complet` | `synthese.standard`, `synthese.complet`, écrits à partir de `extraction` |
| `etiquette`, `justification_etiquette` | `appreciation.etiquette`, quatre valeurs |
| `verdict` | Remplacé par `classement.categorie` ; `confirme` et `remet_en_question` passent dans `sens_pratique` ; `change_la_pratique` correspond à la catégorie 1 ; `a_surveiller` disparaît |
| `pertinence`, `domaines`, `type` | `classement` |
| `vulgarise`, `incertitudes` | `synthese` |
| Champs bibliographiques à la racine | `publication` |

Les fiches v1 déjà publiées restent en ligne, marquées « résumé uniquement ». Aucune n'est
supprimée ni réécrite.

## Ce que la fiche ne contient pas

- Le texte ou le résumé de l'article.
- Le statut du circuit vers Évalys, la cible dans Évalys et la justification d'une sélection :
  ils sont tenus dans le dépôt de coordination, par un humain.
- Toute donnée sur un lecteur ou sur un patient.

## Correspondance avec le contrat `vs-evalys-connaissance`

| Champ d'une proposition | Dans la fiche v2 |
| --- | --- |
| Source | `publication` |
| Origine | `id` et `version` |
| Impact clinique | `synthese.entete.impact_clinique` |
| Contenu | `synthese`, `extraction`, `appreciation`, `dates.analyse` |
| Cible dans Évalys, justification | Hors de la fiche. `classement.themes.region` aide à trouver la région concernée |

Aucune fiche ne part automatiquement vers une autre application. La publication hebdomadaire ne
dépend d'aucune d'elles.

## Points ouverts

| Sujet | Où il se règle |
| --- | --- |
| Second champ de thèmes proposé par Évalys (sécurité et tri, douleur, post-opératoire, questionnaire, médicament) | Après le pilote « genou » |
| Liste des types d'étude au-delà des cinq actuels | Avec la révision des règles d'inclusion |
| Règle de l'étiquette et de la catégorie, mesurée au banc d'essai | Séance 6 |
| Longueur maximale des champs de l'en-tête | Séance 7, au banc d'essai |
| Variante de vérification indépendante | Séance 8 |
| Rangement des fichiers publiés (par fiche ou par semaine) | Avec le choix de la plateforme |
| Présentation dans l'application | Phase 3 |

## Exemple

Fiche de repérage, assemblée à la main à partir de la fiche `pm42984544` publiée en semaine
2026-S45. Les textes viennent de cette fiche. `question` est rédigée à la main ; `categorie` vaut
`null` parce que la nouvelle chaîne n'a encore rien produit. Seuls les blocs utiles à la lecture
sont montrés.

```json
{
  "format": 2,
  "id": "pm42984544",
  "version": 1,
  "statut": "publiee",
  "acces": { "niveau": 3, "origine_texte": null, "licence": null,
             "parties_lues": ["titre", "résumé"],
             "parties_non_lues": ["méthode détaillée", "tableaux", "analyses complémentaires"] },
  "profondeur": "reperage",
  "classement": { "type": "meta_analyse",
                  "domaines": ["kine/msk-membre-inf", "medecine/rhumatologie", "medecine/mpr"],
                  "themes": { "region": [] },
                  "categorie": null, "sens_pratique": null, "pertinence": 2 },
  "extraction": {
    "resultats": [
      { "critere": "KOOS, symptômes", "comparaison": "entre_groupes", "rang": "non_precise",
        "sens_mesure": "augmente", "en_faveur_de": "intervention",
        "valeur": "4,44", "intervalle": "1,62 à 7,26",
        "source": { "emplacement": "résumé", "passage": null } },
      { "critere": "KOOS, douleur", "comparaison": "entre_groupes", "rang": "non_precise",
        "sens_mesure": "pas_de_difference", "en_faveur_de": "aucun",
        "valeur": "1,95", "intervalle": "−0,27 à 4,17",
        "source": { "emplacement": "résumé", "passage": null } }
    ]
  },
  "appreciation": { "plan_etude": { "plan": "revue_interventions", "type_tri": "meta_analyse", "ecart_avec_le_tri": false },
                    "outil": "amstar2", "nature_du_jugement": "fiabilite_de_la_methode",
                    "jugement": "non_evaluable", "jugement_outil": "non_evaluable",
                    "fourchette": { "pire": "faible", "meilleur": "elevee" },
                    "grade_rapporte": null, "etiquette": "non_evaluable" },
  "synthese": {
    "titre_fr": "Efficacité de l’entraînement neuromusculaire dans la rééducation de l’arthrose du genou : revue systématique et méta-analyse d’essais randomisés",
    "entete": {
      "question": "L’entraînement neuromusculaire améliore-t-il les symptômes, la fonction et la qualité de vie dans l’arthrose du genou, par rapport à des interventions témoins ?",
      "resultat_principal": "14 essais randomisés, 1 029 participants. Score KOOS de symptômes : différence moyenne 4,44 (IC à 95 % : 1,62 à 7,26). Douleur : 1,95 (−0,27 à 4,17), non significatif.",
      "impact_clinique": "L’entraînement neuromusculaire constitue une option à considérer chez les personnes atteintes d’arthrose du genou, sans que ces résultats suffisent à établir la pertinence clinique des améliorations ou une supériorité sur la douleur.",
      "limite_principale": "La pertinence clinique de l’amplitude des effets reste incertaine."
    }
  },
  "historique": [ { "version": 1, "date": "2026-11-09", "nature": "creation", "motif": null } ]
}
```

## Sources

- Cahier des charges de Veille Santé, chapitres 5.3, 5.4, 5.8, 7.5, 9, 26.1 à 26.3, 26.9 et 29.3.
- Résultats du banc d'essai : [../banc/resultats/](../banc/resultats/).
- Déclarations au dépôt de coordination : CHG-2026-0004 (format), CHG-2026-0007 (précisions du
  bloc `extraction`), CHG-2026-0009 et CHG-2026-0010 (précisions du bloc `appreciation`).
- Contrat `vs-evalys-connaissance` du dépôt de coordination, version 0 (brouillon).
