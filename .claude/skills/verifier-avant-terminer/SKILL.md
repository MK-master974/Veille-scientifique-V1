---
name: verifier-avant-terminer
description: Vérifications à faire avant d'annoncer qu'une tâche, une correction ou une version est terminée. À utiliser avant tout message qui dit « fait », « corrigé », « terminé » ou « prêt ».
---
# Vérifier avant d'annoncer « terminé »

1. **Lancer la vérification complète du projet** (voir « Dans ce projet ») et lire son résultat jusqu'au bout.
2. **Relire le changement** : le diff correspond à la demande, rien de plus. Pas de fichier de travail oublié.
3. **Tester le cas demandé lui-même**, pas seulement la suite : reproduire le scénario de Marvin.
4. **Dire exactement ce qui est vérifié et ce qui ne l'est pas.** Une fonction non testée sur appareil réel n'est pas « terminée » ; c'est « prêt à tester sur le téléphone ».
5. Si un test échoue : le dire, avec la sortie. Ne jamais l'annoncer comme réussi, ne jamais désactiver un test pour passer.

## Dans ce projet

Veille Santé :

```bash
pip install -r requirements.txt pytest
python -m pytest tests            # sans réseau ni clé
python scripts/demo.py apercu     # vrai moteur, IA simulée
```

- `installation/*.yml` reste identique à `.github/workflows/*.yml` : les tests le vérifient.
- Application (`site/`) : vérifier le rendu au format téléphone ; toute modification visible fait
  avancer `VERSION_APP` dans `site/app.js` et s'inscrit dans `CHANGELOG.md`.
- Service worker (`site/sw.js`) : tester le passage d'une version à la suivante, une première
  installation et le fonctionnement hors connexion.
- Banc d'essai : un lancement réel passe par GitHub Actions et a un coût, à annoncer avant. Un
  résultat du banc n'est « mesuré » que lu dans le journal du lancement terminé.
