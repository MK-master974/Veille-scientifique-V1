---
name: debogage-methodique
description: Méthode pour chercher la cause d'un défaut signalé (par Marvin, un test ou une autre session) avant de corriger. À utiliser dès qu'un comportement est faux, qu'un test échoue sans raison claire ou qu'une première correction n'a pas marché.
---
# Déboguer méthodiquement

1. **Reproduire** le défaut : mêmes étapes, même appareil si possible. Sans reproduction, demander à Marvin une capture ou les étapes exactes.
2. **Écrire le comportement attendu** en une phrase.
3. **Chercher la cause** avant de corriger :
   - lire le code concerné ;
   - chercher le texte affiché ou l'identifiant dans tout le dépôt ;
   - formuler une hypothèse et la tester par la plus petite expérience possible.
4. **Écrire d'abord un test** qui échoue à cause du défaut, puis corriger jusqu'à ce qu'il passe.
5. **Une seule correction à la fois.** Si deux corrections de suite échouent, s'arrêter : revoir l'hypothèse plutôt qu'empiler des rustines.
6. **Vérifier qu'on n'a rien cassé ailleurs** (skill `verifier-avant-terminer`), puis noter la cause au journal du projet.
