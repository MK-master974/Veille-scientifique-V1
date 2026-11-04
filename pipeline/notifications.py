"""Notifications web push via OneSignal.

L'app enregistre sur chaque appareil abonné des étiquettes :
  prof_<profession> = "1"   pour chaque profession suivie
  freq = "hebdo" | "mensuel"
Le moteur envoie un message par profession, uniquement aux abonnés concernés.
"""
import os

from .reseau import requete

URL = "https://api.onesignal.com/notifications"


def messages_semaine(fiches, catalogue, semaine_id):
    """Un message par profession ayant au moins une nouveauté."""
    messages = []
    for prof in catalogue["professions"]:
        concernees = [f for f in fiches if any(d.startswith(prof["id"] + "/") for d in f["domaines"])]
        if not concernees:
            continue
        change = sum(f["verdict"] == "change_la_pratique" for f in concernees)
        remet = sum(f["verdict"] == "remet_en_question" for f in concernees)
        morceaux = []
        if change:
            morceaux.append(f"{change} étude{'s' if change > 1 else ''} qui change{'nt' if change > 1 else ''} la pratique")
        if remet:
            morceaux.append(f"{remet} remise{'s' if remet > 1 else ''} en question")
        morceaux.append(f"{len(concernees)} nouveauté{'s' if len(concernees) > 1 else ''}")
        messages.append({
            "profession": prof["id"],
            "titre": f"{prof['court']} : la veille de la semaine est en ligne",
            "texte": " · ".join(morceaux),
        })
    return messages


def message_mensuel():
    return {"titre": "Votre récapitulatif du mois", "texte": "Les veilles des dernières semaines vous attendent."}


def envoyer(cfg, titre, texte, filtres, url, journal=print):
    app_id = cfg.get("notifications", {}).get("onesignal_app_id")
    cle = os.environ.get("ONESIGNAL_REST_API_KEY")
    if not app_id or not cle:
        journal("Notifications : OneSignal non configuré, envoi ignoré")
        return False
    requete("POST", URL, headers={"Authorization": f"Key {cle}"}, json={
        "app_id": app_id,
        "target_channel": "push",
        "headings": {"en": titre, "fr": titre},
        "contents": {"en": texte, "fr": texte},
        "filters": filtres,
        "url": url,
    })
    return True


def notifier_semaine(semaine_id, fiches, catalogue, cfg, premier_lundi_du_mois, journal=print):
    base = (cfg.get("url_site") or "").rstrip("/")
    envoyes = 0
    for m in messages_semaine(fiches, catalogue, semaine_id):
        filtres = [
            {"field": "tag", "key": f"prof_{m['profession']}", "relation": "=", "value": "1"},
            {"field": "tag", "key": "freq", "relation": "=", "value": "hebdo"},
        ]
        if envoyer(cfg, m["titre"], m["texte"], filtres, f"{base}/#semaine-{semaine_id}", journal):
            envoyes += 1
    if premier_lundi_du_mois:
        m = message_mensuel()
        if envoyer(cfg, m["titre"], m["texte"],
                   [{"field": "tag", "key": "freq", "relation": "=", "value": "mensuel"}],
                   f"{base}/#archive", journal):
            envoyes += 1
    journal(f"Notifications : {envoyes} message(s) envoyé(s)")
    return envoyes
