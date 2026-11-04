"""Requêtes HTTP avec nouvelles tentatives sur les erreurs passagères."""
import time

import requests

AGENT = "VeilleSante/1.0 (veille scientifique pour professionnels de sante)"
_session = requests.Session()
_session.headers["User-Agent"] = AGENT


def requete(methode, url, *, tentatives=4, attente=2.0, timeout=60, **kwargs):
    derniere_erreur = None
    for essai in range(tentatives):
        try:
            rep = _session.request(methode, url, timeout=timeout, **kwargs)
            if rep.status_code in (429, 500, 502, 503, 504):
                derniere_erreur = RuntimeError(f"HTTP {rep.status_code} sur {url}")
            else:
                rep.raise_for_status()
                return rep
        except requests.RequestException as e:
            if getattr(e, "response", None) is not None and e.response.status_code < 500 \
                    and e.response.status_code != 429:
                raise
            derniere_erreur = e
        time.sleep(attente * (2 ** essai))
    raise derniere_erreur
