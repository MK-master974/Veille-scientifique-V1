---
name: publication-version
description: Étapes pour publier une version d'une application (Évalys, Kiné Tools, Veille Santé) - accord de Marvin, vérification, numéro, journal des changements, mise en ligne, étiquette. À utiliser avant toute mise en production.
---
# Publier une version

1. **Accord de Marvin** dans la conversation de l'application :
   - Évalys : « Go Vxx » explicite ; rien n'est construit ni livré sans lui ;
   - autres applications : selon leur `CLAUDE.md`.
2. **Vérification complète au vert** (skill `verifier-avant-terminer`) et revue de sécurité par la commande `/security-review`.
3. **Numéro de version et journal :**
   - Évalys : `Vxx` ;
   - Kiné Tools : `1.0.0-rc.N` jusqu'à la validation sur appareils, puis SemVer ;
   - mettre `CHANGELOG.md` à jour.
4. **Mise en ligne :**
   - travailler sur une branche ;
   - proposer la demande de fusion vers `main` ;
   - Marvin la fusionne.
5. **Étiquette :** l'envoi d'étiquettes est refusé depuis les sessions. Marvin la crée par GitHub, onglet « Releases » : donner le lien direct et les étapes.
6. **Après la mise en ligne :**
   - demander à Marvin de vérifier sur son téléphone ou sa tablette ;
   - noter le résultat ;
   - prévenir le portail si un échange avec une autre application est touché.

## Dans ce projet

Veille Santé :

- numéro `MAJEUR.MINEUR.CORRECTIF` dans `VERSION_APP` (`site/app.js`), repris dans `CHANGELOG.md` ;
- la publication hebdomadaire reste automatique : aucune version ne la fait dépendre d'une
  validation manuelle ;
- une modification du service worker (`site/sw.js`) se teste avant la demande de fusion : passage
  d'une version à la suivante, première installation, hors connexion.
