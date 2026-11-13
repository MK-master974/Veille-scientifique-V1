---
name: declaration-portail
description: Déclarer au portail central (dépôt ecosysteme) une évolution qui touche une autre application ou un contrat d'échange, AVANT de la développer. À utiliser dès qu'un changement modifie un format d'échange, une donnée partagée ou une règle commune.
---
# Déclarer une évolution au portail

**Quand :** avant de développer un changement qui touche une autre application, un contrat (`interfaces/` du dépôt `ecosysteme`) ou une règle commune. Exemple : tout changement du format `kinetools-seances`.

1. Lire d'abord le paquet de contexte du dépôt `ecosysteme` (`contexte/`) et noter son commit.
2. Créer `evolutions/CHG-AAAA-nnnn-sujet.md` d'après `evolutions/MODELE.md` : en-tête complet, texte court.
   - `niveau` : 1 indépendant, 2 coordination nécessaire, 3 dépendance bloquante ;
   - `preuves` : commits, demandes de fusion ou versions réels ; ne jamais en inventer.
3. Avant l'envoi : `python3 outils/verifier.py` puis `python3 -m unittest discover -s tests`.
4. Envoyer directement sur `main` (les déclarations y sont permises, POR-D6). Une décision, un contrat ou une règle passent au contraire par une demande de fusion que Marvin accepte.
5. Prévenir la session « portail central » par un message court, au format du skill `message-cons07`.

**Jamais** de donnée de patient, de nom de personne ni de secret dans une déclaration (R1, R8).

## Dans ce projet

Veille Santé :

- paquet de contexte à lire : `contexte/veille-sante.md` du dépôt `ecosysteme` ; citer son commit
  dans la déclaration et dans le compte rendu ;
- tout changement du format « fiche v2 » (`docs/FICHE_V2.md`) est déclaré avant d'être inscrit :
  voir CHG-2026-0004 et CHG-2026-0007 ;
- aucune fiche ne part automatiquement vers une autre application.
