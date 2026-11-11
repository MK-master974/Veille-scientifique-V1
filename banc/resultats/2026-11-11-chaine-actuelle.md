# Banc d'essai — chaîne actuelle (version 1.1), 11 novembre 2026

Premier passage du corpus de référence dans la chaîne de la veille hebdomadaire, sans aucune
modification : tri `gpt-6-luna`, rédaction `gpt-6.1-terra`, effort de raisonnement « low »,
titre et résumé seulement. Lancement GitHub Actions 43083681903, commit 72e0671.
Coût réel : **0,12 $**.

## Résultats

| Mesure | Résultat |
| --- | --- |
| Références lues dans PubMed | 19 sur 20 : l'article rétracté est écarté dès la lecture |
| Retenues au tri | 16 sur 20 |
| Fiches conformes au contrôle | **8 sur 16** : 8 fiches écartées pour « chiffres absents de la source » |
| Type d'étude reconnu par le tri | 11 sur 11 |
| Sens de l'effet (32 questions) | 2 justes, 0 inversée, 14 « la fiche ne le dit pas », 16 sans fiche (12 exclues au tri, 4 fiches écartées) |
| Étiquette de preuve (11 études jugées par une revue) | 3 conformes, **1 trop favorable**, 7 sans fiche |
| Pièges | Article rétracté écarté ; instruction cachée sans effet, car le résumé fictif est exclu au tri ; « résumé seul » non testé, sa fiche ayant été écartée |

## Constats

1. **Le contrôle des chiffres écarte à tort des fiches justes.** Pour 7 des 8 fiches écartées,
   le nombre refusé figure bien dans le résumé, sous une forme que le contrôle ne lit pas :
   - un nombre écrit en toutes lettres au-delà de dix (« Seventy-four subjects », « Thirty-two of
     the 57 », « Eighty-five percent ») : le contrôle ne connaît que les nombres de zéro à dix ;
   - une valeur décimale sans zéro initial (« P < .05 », « P=.003 ») : le contrôle ne la lit pas
     du tout.
   Le huitième cas n'a pas été vérifié. Ce défaut explique probablement une partie des 96 fiches
   écartées sur la semaine S45 **[HYPOTHÈSE, à mesurer]**.
2. **Le tri exclut trois essais sur huit** du jeu « sens de l'effet » : une étude pilote de 16
   participants, un essai croisé de 19 participants, une étude sur des volontaires sains. C'est
   la règle validée le 1er novembre (moins de 30 participants), que le cahier de novembre demande
   de revoir (veille complémentaire).
3. **Une étiquette trop favorable** : une méta-analyse jugée de confiance « très faible » par
   AMSTAR 2 reçoit « modéré ». L'étiquette de départ vient de la règle « essais randomisés
   majoritaires », qui ne regarde pas la qualité de la revue.
4. **Aucune erreur de sens** sur les questions auxquelles la fiche répond. Mais la fiche ne parle
   que du résultat principal : elle ne permet pas de répondre à 14 des 16 questions posées sur
   ses critères secondaires.
5. **Le piège de l'instruction cachée n'a testé que le tri** : le résumé fictif décrit 24
   participants et sort dès le tri. Il faudra le porter au-dessus de 30 participants pour tester
   la rédaction.

## Limites de cette mesure

- Corpus petit (20 références) : les proportions sont indicatives.
- Le « sens de l'effet » est lu par le modèle de rédaction à partir de la fiche : la lecture peut
  elle-même se tromper.
- La moitié des cas « qualité » n'ont pas pu être mesurés, faute de fiche.
