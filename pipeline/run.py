"""Point d'entrée du moteur : fait avancer la veille de la semaine d'une ou plusieurs étapes.

Lancé toutes les heures par GitHub Actions du dimanche soir au mardi.
Chaque lancement reprend où le précédent s'est arrêté (état dans travail/<semaine>/).

Usage :
  python -m pipeline.run semaine [2026-S44]     -> affiche « semaine=2026-S44 »
  python -m pipeline.run avancer [--semaine 2026-S44] [--sans-attente]
"""
import argparse
import json
import os
import sys
from datetime import datetime, time as heure, timedelta
from zoneinfo import ZoneInfo

from . import collecte, controle, etapes, ia, notifications, publication
from .config import (DOSSIER_TRAVAIL, charger_catalogue, charger_config, charger_consigne,
                     domaines_du_catalogue)
from .semaines import depuis_id, semaine_precedente

ORDRE = ("collecte", "tri", "redaction", "controle", "synthese", "publication", "notification", "termine")


class Echec(RuntimeError):
    """Erreur qui doit faire échouer le lancement (GitHub envoie alors un e-mail d'alerte)."""


class Veille:
    def __init__(self, semaine, cfg=None, catalogue=None, dossier_site=None, maintenant=None, echeance=True):
        self.semaine = semaine
        self.cfg = cfg or charger_config()
        self.catalogue = catalogue or charger_catalogue()
        self.libelles = domaines_du_catalogue(self.catalogue)
        self.dossier = DOSSIER_TRAVAIL / semaine.id
        self.dossier.mkdir(parents=True, exist_ok=True)
        self.dossier_site = dossier_site
        self.tz = ZoneInfo(self.cfg.get("publication", {}).get("fuseau", "Europe/Paris"))
        self._maintenant = maintenant
        self.etat = self._lire("etat.json", None) or {
            "semaine": semaine.id, "etape": "collecte", "lots": {}, "couts": {},
            "stats": {}, "journal": [],
        }
        self.publie_ce_lancement = False
        self.echeance = echeance
        self._fournisseur = None

    # --- utilitaires ---------------------------------------------------------------------
    def maintenant(self):
        return self._maintenant or datetime.now(self.tz)

    def journal(self, message):
        ligne = f"{self.maintenant().strftime('%Y-%m-%d %H:%M')} {message}"
        print(ligne, flush=True)
        self.etat["journal"].append(ligne)

    def _lire(self, nom, defaut):
        try:
            return json.loads((self.dossier / nom).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return defaut

    def _ecrire(self, nom, donnees):
        chemin = self.dossier / nom
        tmp = chemin.with_suffix(".tmp")
        tmp.write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(chemin)

    def sauver(self):
        self.etat["maj"] = self.maintenant().isoformat(timespec="seconds")
        self._ecrire("etat.json", self.etat)

    @property
    def fournisseur(self):
        if self._fournisseur is None:
            self._fournisseur = ia.fournisseur(self.cfg)
        return self._fournisseur

    def mode(self):
        voulu = os.environ.get("VEILLE_MODE") or self.cfg["ia"].get("mode", "lot")
        return "lot" if voulu == "lot" and self.fournisseur.lot_possible else "direct"

    def passer(self, etape):
        self.etat["etape"] = etape
        self.sauver()

    # --- appels d'IA, en lot ou en direct --------------------------------------------------
    def appeler_ia(self, nom, requetes, modele, sortie_moyenne, tolerant=False):
        """Renvoie {id: (texte, usage)} quand les résultats sont prêts, None s'il faut attendre.

        tolerant : les réponses manquantes ne font pas échouer le lancement (synthèses,
        qui ont une version de secours sans IA)."""
        if not requetes:
            return {}
        prix = self.cfg["ia"]["prix_usd_par_million"]
        mode = self.mode()
        lots = self.etat["lots"]
        if mode == "direct":
            res = self.fournisseur.direct(requetes, modele, self.cfg["ia"].get("requetes_simultanees", 8))
            manquants = [r for r in requetes if res.get(r["id"], (None,))[0] is None]
            if manquants:
                self.journal(f"{nom} : {len(manquants)} réponse(s) manquante(s), nouvel essai")
                res.update(self.fournisseur.direct(manquants, modele, 4))
            self._compter(nom, res, modele, mode)
            if not tolerant:
                self._verifier_taux(nom, requetes, res)
            return res

        info = lots.get(nom)
        if info is None:
            estime = ia.estimer_cout(requetes, modele, prix, sortie_moyenne, mode)
            lot_id = self.fournisseur.soumettre_lot(requetes, modele, f"veille {self.semaine.id} {nom}")
            lots[nom] = {"id": lot_id, "soumis_le": self.maintenant().isoformat(timespec="seconds"),
                         "tentatives": 1, "nb": len(requetes), "cout_estime": round(estime, 3)}
            self.journal(f"{nom} : lot de {len(requetes)} requêtes soumis ({lot_id}), "
                         f"coût estimé {estime:.2f} $")
            self.sauver()
            return None
        statut, details = self.fournisseur.etat_lot(info["id"])
        if statut == "en_cours":
            compte = details.get("request_counts") or {}
            self.journal(f"{nom} : lot en cours ({compte.get('completed', '?')}/{compte.get('total', '?')})")
            return None
        if statut == "echec":
            if info["tentatives"] >= 2:
                raise Echec(f"{nom} : le lot a échoué deux fois ({details.get('status')}, "
                            f"{details.get('errors')})")
            self.journal(f"{nom} : lot en échec ({details.get('status')}), nouvelle soumission")
            info["id"] = self.fournisseur.soumettre_lot(requetes, modele, f"veille {self.semaine.id} {nom}")
            info["tentatives"] += 1
            self.sauver()
            return None
        res = self.fournisseur.resultats_lot(details)
        manquants = [r for r in requetes if res.get(r["id"], (None,))[0] is None]
        if manquants:
            self.journal(f"{nom} : {len(manquants)} réponse(s) manquante(s) dans le lot, reprise en direct")
            res.update(self.fournisseur.direct(manquants, modele, 4))
        self._compter(nom, res, modele, mode)
        if not tolerant:
            self._verifier_taux(nom, requetes, res)
        return res

    def _verifier_taux(self, nom, requetes, res):
        """Une panne d'IA ne doit pas publier une semaine vide : au-delà de 30 % de réponses
        absentes, le lancement échoue et GitHub envoie une alerte."""
        absentes = [r["id"] for r in requetes if res.get(r["id"], (None,))[0] is None]
        if len(requetes) >= 5 and len(absentes) / len(requetes) > 0.3:
            exemple = next((u.get("erreur") for t, u in res.values() if t is None and isinstance(u, dict)
                            and u.get("erreur")), "réponses vides")
            raise Echec(f"{nom} : {len(absentes)} réponses manquantes sur {len(requetes)} ({exemple})")

    def _compter(self, nom, res, modele, mode):
        usages = [u for _, u in res.values() if isinstance(u, dict)]
        cout = ia.cout_reel(usages, modele, self.cfg["ia"]["prix_usd_par_million"], mode)
        self.etat["couts"][nom] = round(self.etat["couts"].get(nom, 0) + cout, 4)

    def budget_restant(self):
        return float(self.cfg["ia"].get("budget_max_usd_semaine", 8)) - sum(self.etat["couts"].values()) \
            - sum(l.get("cout_estime", 0) for k, l in self.etat["lots"].items() if k not in self.etat["couts"])

    # --- étapes -----------------------------------------------------------------------------
    def etape_collecte(self):
        refs = collecte.collecter(self.semaine, self.cfg, self.journal)
        self._ecrire("references.json", refs)
        self.etat["stats"]["candidates"] = len(refs)
        self.journal(f"Collecte : {len(refs)} références candidates")
        self.passer("tri")
        return True

    def etape_tri(self):
        refs = self._lire("references.json", [])
        consigne = charger_consigne("tri", self.catalogue)
        modele = self.cfg["ia"]["modele_tri"]
        prix = self.cfg["ia"]["prix_usd_par_million"]
        if "tri" not in self.etat["lots"]:
            # Garde-fou budgétaire : la moitié du budget au plus pour le tri.
            plafond = self.budget_restant() / 2
            reqs = etapes.requetes_tri(refs, consigne)
            while reqs and ia.estimer_cout(reqs, modele, prix, 200, self.mode()) > plafond:
                reqs = reqs[: int(len(reqs) * 0.9)]
            if len(reqs) < len(refs):
                self.journal(f"Tri : budget atteint, {len(refs) - len(reqs)} références non triées")
                self.etat["stats"]["non_triees_budget"] = len(refs) - len(reqs)
                refs = refs[: len(reqs)]
                self._ecrire("references.json", refs)
        reqs = etapes.requetes_tri(refs, consigne)
        res = self.appeler_ia("tri", reqs, modele, 200)
        if res is None:
            return False
        valides = set(self.libelles)
        tris = {}
        for ref in refs:
            texte, _ = res.get(f"tri:{ref['id']}", (None, {}))
            tris[ref["id"]] = etapes.lire_tri(texte, ref, valides, self.cfg.get("preuve"))
        self._ecrire("tri.json", tris)
        inclus = sum(t.get("inclure", False) for t in tris.values())
        self.etat["stats"]["retenues_tri"] = inclus
        self.journal(f"Tri : {inclus} références retenues sur {len(refs)}")
        self.passer("redaction")
        return True

    def etape_redaction(self):
        refs = {r["id"]: r for r in self._lire("references.json", [])}
        tris = self._lire("tri.json", {})
        modele = self.cfg["ia"]["modele_redaction"]
        prix = self.cfg["ia"]["prix_usd_par_million"]
        consigne = charger_consigne("redaction")
        maximum = int(self.cfg.get("selection", {}).get("max_fiches", 1200))
        selection, ecartes = etapes.selectionner(tris, maximum)
        reqs = etapes.requetes_redaction(selection, refs, self.libelles, consigne)
        if "redaction" not in self.etat["lots"]:
            plafond = self.budget_restant() * 0.85
            while reqs and ia.estimer_cout(reqs, modele, prix, 900, self.mode()) > plafond:
                reqs = reqs[: int(len(reqs) * 0.9)]
            if len(reqs) < len(selection):
                self.journal(f"Rédaction : budget atteint, {len(selection) - len(reqs)} études les moins "
                             f"prioritaires non rédigées")
            if ecartes:
                self.journal(f"Rédaction : plafond de {maximum} fiches, {len(ecartes)} études écartées")
            self.etat["selection"] = [r["id"].split(":", 1)[1] for r in reqs]
            self.sauver()
        ids = self.etat.get("selection", [])
        selection = [tris[i] for i in ids]
        reqs = etapes.requetes_redaction(selection, refs, self.libelles, consigne)
        res = self.appeler_ia("redaction", reqs, modele, 900)
        if res is None:
            return False
        self._ecrire("redaction.json", {k.split(":", 1)[1]: v[0] for k, v in res.items()})
        self.journal(f"Rédaction : {len(res)} réponses reçues")
        self.passer("controle")
        return True

    def etape_controle(self):
        refs = {r["id"]: r for r in self._lire("references.json", [])}
        tris = self._lire("tri.json", {})
        brutes = self._lire("redaction.json", {})
        fiches, rejets = [], []
        for ident, texte in brutes.items():
            fiche, erreurs = etapes.lire_redaction(texte, refs[ident], tris[ident], self.cfg.get("preuve"))
            if fiche:
                fiches.append(fiche)
            else:
                rejets.append({"id": ident, "url": refs[ident]["url"], "motifs": erreurs})
        if os.environ.get("VEILLE_SANS_RESEAU") != "1" and self.cfg.get("controle", {}).get("crossref", True):
            fiches, exclues = controle.verifier_externe(fiches, self.cfg.get("email_contact", ""), self.journal)
            rejets += [{"id": e["id"], "url": refs[e["id"]]["url"], "motifs": [e["motif"]]} for e in exclues]
        self._ecrire("fiches.json", fiches)
        self._ecrire("rejets.json", rejets)
        self.etat["stats"].update({"fiches": len(fiches), "rejetees_controle": len(rejets)})
        self.journal(f"Contrôle : {len(fiches)} fiches conformes, {len(rejets)} écartées")
        self.passer("synthese")
        return True

    def etape_synthese(self):
        fiches = self._lire("fiches.json", [])
        groupes = etapes.fiches_par_domaine(fiches)
        consigne = charger_consigne("synthese")
        modele = self.cfg["ia"]["modele_synthese"]
        reqs = etapes.requetes_synthese(groupes, self.libelles, consigne)
        res = self.appeler_ia("synthese", reqs, modele, 600, tolerant=True)
        if res is None:
            return False
        syntheses, replis = {}, 0
        for domaine, fiches_dom in groupes.items():
            texte, _ = res.get(f"synthese:{domaine}", (None, {}))
            syntheses[domaine], repli = etapes.lire_synthese(texte, fiches_dom)
            replis += repli
        self._ecrire("syntheses.json", syntheses)
        self.journal(f"Synthèses : {len(syntheses)} sous-champs ({replis} complétée(s) sans IA)")
        self.passer("publication")
        return True

    def etape_publication(self):
        fiches = self._lire("fiches.json", [])
        syntheses = self._lire("syntheses.json", {})
        stats = {**self.etat["stats"], "cout_usd": round(sum(self.etat["couts"].values()), 2)}
        kw = {"dossier": self.dossier_site} if self.dossier_site else {}
        publication.publier_semaine(self.semaine, fiches, syntheses, stats, self.cfg, self.catalogue, **kw)
        self.publie_ce_lancement = True
        self.journal(f"Publication : {len(fiches)} fiches en ligne, coût IA {stats['cout_usd']} $")
        self.passer("notification")
        return False  # on laisse le site se déployer avant de notifier (lancement suivant)

    def etape_notification(self):
        debut = heure.fromisoformat(self.cfg.get("publication", {}).get("notifier_a_partir_de", "07:30"))
        maintenant = self.maintenant()
        if not (debut <= maintenant.time() <= heure(21, 0)):
            self.journal("Notification : en attente de l'heure d'envoi")
            return False
        fiches = self._lire("fiches.json", [])
        premier_lundi = maintenant.weekday() == 0 and maintenant.day <= 7
        notifications.notifier_semaine(self.semaine.id, fiches, self.catalogue, self.cfg,
                                       premier_lundi, self.journal)
        self.passer("termine")
        return False

    # --- boucle -----------------------------------------------------------------------------
    def avancer(self):
        if self.etat["etape"] == "termine":
            print(f"{self.semaine.id} : veille déjà terminée")
            return
        kw = {"dossier": self.dossier_site} if self.dossier_site else {}
        if self.etat["etape"] == "collecte" and publication.semaine_publiee(self.semaine.id, **kw):
            print(f"{self.semaine.id} : déjà publiée, rien à faire")
            return
        if self.etat["etape"] == "collecte":
            # PubMed date ses entrées à l'heure de la côte est des États-Unis : on attend que
            # le dimanche y soit terminé (lundi 5 h UTC) pour ne manquer aucune entrée.
            debut = datetime.combine(self.semaine.dimanche + timedelta(days=1), heure(5, 0), ZoneInfo("UTC"))
            if self.maintenant() < debut:
                print(f"{self.semaine.id} : collecte prévue à partir du lundi 5 h UTC")
                return
        self.verifier_echeance()
        while self.etat["etape"] != "termine":
            continuer = getattr(self, f"etape_{self.etat['etape']}")()
            self.sauver()
            if not continuer:
                break

    def verifier_echeance(self):
        """La veille doit être publiée au plus tard le mardi 23 h (heure de Paris)."""
        limite = datetime.combine(self.semaine.dimanche + timedelta(days=2), heure(23, 0), self.tz)
        if self.echeance and self.maintenant() > limite and ORDRE.index(self.etat["etape"]) < ORDRE.index("notification"):
            raise Echec(f"{self.semaine.id} : veille non publiée à l'échéance (étape {self.etat['etape']})")


def _sortie_github(cle, valeur):
    chemin = os.environ.get("GITHUB_OUTPUT")
    if chemin:
        with open(chemin, "a", encoding="utf-8") as f:
            f.write(f"{cle}={valeur}\n")


def main(argv=None):
    p = argparse.ArgumentParser(prog="pipeline.run")
    sous = p.add_subparsers(dest="commande", required=True)
    s = sous.add_parser("semaine")
    s.add_argument("id", nargs="?", default="")
    a = sous.add_parser("avancer")
    a.add_argument("--semaine", default="")
    a.add_argument("--sans-echeance", action="store_true",
                   help="lancement manuel : ne pas exiger une publication avant mardi 23 h")
    a.add_argument("--sans-attente", action="store_true",
                   help="en mode lot, attend sur place la fin des lots (utile en local)")
    sous.add_parser("initialiser", help="écrit catalogue, réglages publics et index vide du site")
    args = p.parse_args(argv)

    cfg = charger_config()
    if args.commande == "initialiser":
        publication.initialiser_site(cfg, charger_catalogue())
        print("site/data prêt")
        return 0
    fuseau = cfg.get("publication", {}).get("fuseau", "Europe/Paris")
    demandee = (args.id if args.commande == "semaine" else args.semaine).strip()
    semaine = depuis_id(demandee) if demandee else semaine_precedente(fuseau=fuseau)

    if args.commande == "semaine":
        print(f"semaine={semaine.id}")
        return 0

    veille = Veille(semaine, cfg, echeance=not args.sans_echeance)
    try:
        veille.avancer()
        while args.sans_attente and veille.etat["etape"] not in ("termine", "notification"):
            ia.attendre(120)
            veille.avancer()
    except Echec as e:
        veille.journal(f"ÉCHEC : {e}")
        veille.sauver()
        print(f"::error::{e}", file=sys.stderr)
        return 1
    except ia.ErreurIA as e:
        veille.journal(f"ÉCHEC IA : {e}")
        veille.sauver()
        print(f"::error::{e}", file=sys.stderr)
        return 1
    finally:
        _sortie_github("publie", "true" if veille.publie_ce_lancement else "false")
        _sortie_github("etape", veille.etat["etape"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
