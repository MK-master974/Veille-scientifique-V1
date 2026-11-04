"""Écriture des données publiées, lues par la web app (fichiers statiques)."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from . import regles
from .config import DOSSIER_SITE, domaines_du_catalogue


def _ecrire(chemin, donnees):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    tmp.write_text(json.dumps(donnees, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(chemin)


def _lire(chemin, defaut):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return defaut


def config_publique(cfg):
    mentions = cfg.get("mentions", {})
    publique = {
        "nom_app": cfg.get("nom_app", "Veille Santé"),
        "email_contact": cfg.get("email_contact", ""),
        "onesignal_app_id": cfg.get("notifications", {}).get("onesignal_app_id", ""),
        "editeur": mentions.get("editeur", ""),
        "hebergeur": mentions.get("hebergeur", ""),
        "fiches_retirees": [str(x) for x in cfg.get("fiches_retirees", [])],
    }
    if cfg.get("demonstration"):
        publique["demonstration"] = True
    return publique


def publier_semaine(semaine, fiches, syntheses, stats, cfg, catalogue, dossier=None):
    dossier = dossier or DOSSIER_SITE
    data = dossier / "data"
    tz = ZoneInfo(cfg.get("publication", {}).get("fuseau", "Europe/Paris"))
    maintenant = datetime.now(tz).isoformat(timespec="seconds")
    fiches = sorted(fiches, key=regles.cle_tri)

    # Toutes les synthèses du catalogue, y compris les sous-champs sans nouveauté.
    tout_syntheses = {}
    groupes = {}
    for f in fiches:
        for d in f["domaines"]:
            groupes[d] = groupes.get(d, 0) + 1
    for d in domaines_du_catalogue(catalogue):
        s = syntheses.get(d)
        tout_syntheses[d] = {**(s or {"ce_qui_change_la_pratique": [], "a_surveiller": [],
                                      "remis_en_question": []}),
                             "nb_fiches": groupes.get(d, 0)}

    _ecrire(data / "semaines" / f"{semaine.id}.json", {
        "semaine": semaine.id,
        "lundi": semaine.lundi.isoformat(),
        "dimanche": semaine.dimanche.isoformat(),
        "publie_le": maintenant,
        "stats": stats,
        "fiches": fiches,
        "syntheses": tout_syntheses,
    })

    # Index de recherche par année (compact : la fiche complète est chargée à l'ouverture).
    annee = semaine.lundi.isocalendar()[0]
    chemin_recherche = data / "recherche" / f"{annee}.json"
    recherche = [e for e in _lire(chemin_recherche, []) if e["s"] != semaine.id]
    for f in fiches:
        recherche.append({
            "i": f["id"], "s": semaine.id, "t": f["titre_fr"], "o": f["titre"],
            "d": f["domaines"], "y": f["type"], "e": f["etiquette"], "v": f["verdict"],
            "p": f["pertinence"], "r": f.get("revue_abrege") or f.get("revue", ""),
        })
    _ecrire(chemin_recherche, recherche)

    index = _lire(data / "index.json", {"semaines": []})
    semaines = [s for s in index["semaines"] if s["id"] != semaine.id]
    semaines.append({
        "id": semaine.id, "lundi": semaine.lundi.isoformat(), "dimanche": semaine.dimanche.isoformat(),
        "nb_fiches": len(fiches), "publie_le": maintenant,
    })
    semaines.sort(key=lambda s: s["lundi"], reverse=True)
    annees = sorted({int(s["id"][:4]) for s in semaines}, reverse=True)
    _ecrire(data / "index.json", {
        "genere_le": maintenant,
        "derniere": semaines[0]["id"],
        "semaines": semaines,
        "annees_recherche": annees,
    })
    _ecrire(data / "catalogue.json", catalogue)
    _ecrire(data / "config.json", config_publique(cfg))
    return data / "semaines" / f"{semaine.id}.json"


def initialiser_site(cfg, catalogue, dossier=None):
    """Prépare les données minimales du site (avant la première veille, et à chaque déploiement)."""
    data = (dossier or DOSSIER_SITE) / "data"
    _ecrire(data / "catalogue.json", catalogue)
    _ecrire(data / "config.json", config_publique(cfg))
    if not (data / "index.json").exists():
        _ecrire(data / "index.json", {"genere_le": "", "derniere": None, "semaines": [], "annees_recherche": []})


def semaine_publiee(semaine_id, dossier=None):
    dossier = dossier or DOSSIER_SITE
    index = _lire(dossier / "data" / "index.json", {"semaines": []})
    return any(s["id"] == semaine_id for s in index["semaines"])
