---
name: aucune-donnee-patient
description: Contrôle à faire avant tout commit, exemple, test, capture ou message à une autre session - aucune donnée de patient, aucun nom de personne réel, aucun secret, aucun code de secours en clair (règles R1 et R8).
---
# Aucune donnée de patient, aucun secret

Avant un commit, un exemple, un test, une capture d'écran ou un message à une autre session, vérifier que :

1. **Aucune donnée de patient** n'y figure : identité, date de naissance, valeurs de bilan réelles, texte libre clinique. Les exemples et les tests n'utilisent que des personnes **manifestement fictives**.
2. **Aucun nom de personne réel** : cela vaut aussi pour l'espace « Personnes » de Kiné Tools et pour l'option « Joindre le nom ».
3. **Aucun secret** : clé d'API, jeton, mot de passe. Les secrets vivent dans les réglages de GitHub ou de Cloudflare, jamais dans un fichier ni un message.
4. **Évalys :** le code de secours de test n'est jamais écrit en clair, nulle part. Pour un test qui en a besoin, donner à Marvin une commande qui le lit sans l'afficher.
5. **Aucun service extérieur** ne reçoit de données d'Évalys ou de Kiné Tools (POR-D24) : pas de suivi d'erreurs, de mesure d'usage ni de relecture d'écran.

En cas de doute : ne pas écrire, et demander.
