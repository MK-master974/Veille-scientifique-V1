"""Appels aux modèles d'IA.

Deux modes :
- « lot » (OpenAI uniquement) : traitement différé, facturé moitié prix, résultats sous 24 h.
  Le pipeline soumet un lot, enregistre son identifiant et revient le chercher plus tard.
- « direct » : requêtes immédiates en parallèle (OpenAI ou Mistral), prix plein.

Un fournisseur « demo » rejoue des réponses enregistrées, pour les tests et la démonstration.
"""
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

from .reseau import requete

URL_OPENAI = "https://api.openai.com/v1"
URL_MISTRAL = "https://api.mistral.ai/v1"


class ErreurIA(RuntimeError):
    pass


def lire_json(texte):
    """Extrait l'objet JSON d'une réponse, même entourée de texte ou de balises de code."""
    if texte is None:
        raise ValueError("réponse vide")
    texte = texte.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", texte, re.S)
    if m:
        texte = m.group(1).strip()
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut < 0 or fin < 0:
        raise ValueError("aucun objet JSON")
    return json.loads(texte[debut:fin + 1])


EFFORT = os.environ.get("VEILLE_EFFORT")      # réglé par la configuration au démarrage


def corps_requete(modele, consigne, contenu, max_sortie=2500):
    corps = {
        "model": modele,
        "messages": [
            {"role": "system", "content": consigne},
            {"role": "user", "content": contenu},
        ],
        "response_format": {"type": "json_object"},
        # Plafond large : les modèles qui « réfléchissent » consomment des jetons avant de répondre.
        # Seuls les jetons réellement produits sont facturés.
        "max_completion_tokens": max_sortie,
    }
    if EFFORT:
        corps["reasoning_effort"] = EFFORT
    return corps


def estimer_jetons(texte):
    return max(1, len(texte) // 3)


def estimer_cout(requetes, modele, prix, sortie_moyenne, mode):
    entree, sortie = prix.get(modele, (2.0, 10.0))
    jetons_entree = sum(estimer_jetons(r["consigne"] + r["contenu"]) for r in requetes)
    jetons_sortie = sortie_moyenne * len(requetes)
    cout = (jetons_entree * entree + jetons_sortie * sortie) / 1e6
    return cout / 2 if mode == "lot" else cout


def cout_reel(usages, modele, prix, mode):
    entree, sortie = prix.get(modele, (2.0, 10.0))
    total = sum(u.get("prompt_tokens", 0) * entree + u.get("completion_tokens", 0) * sortie for u in usages) / 1e6
    return total / 2 if mode == "lot" else total


# --- Fournisseurs ---------------------------------------------------------------------------

class Fournisseur:
    nom = "?"
    lot_possible = False

    def direct(self, requetes, modele, simultanes=8):
        """requetes : [{"id", "consigne", "contenu", "max_sortie"}] -> {id: (texte, usage)}"""
        raise NotImplementedError


class FournisseurCompatibleOpenAI(Fournisseur):
    def __init__(self, url, cle, nom):
        if not cle:
            raise ErreurIA(f"Clé d'API {nom} absente : ajoute-la dans les secrets du dépôt")
        self.url, self.cle, self.nom = url, cle, nom

    @property
    def entetes(self):
        return {"Authorization": f"Bearer {self.cle}"}

    def _un_appel(self, r, modele):
        corps = corps_requete(modele, r["consigne"], r["contenu"], r.get("max_sortie", 2500))
        if self.nom == "mistral":
            corps["max_tokens"] = corps.pop("max_completion_tokens")
            corps.pop("reasoning_effort", None)
        try:
            rep = requete("POST", f"{self.url}/chat/completions", json=corps,
                          headers=self.entetes, timeout=180).json()
            return r["id"], (rep["choices"][0]["message"]["content"], rep.get("usage", {}))
        except Exception as e:
            if "401" in str(e) or "403" in str(e):
                raise ErreurIA(f"Clé d'API {self.nom} refusée : {e}") from e
            return r["id"], (None, {"erreur": str(e)})

    def direct(self, requetes, modele, simultanes=8):
        with ThreadPoolExecutor(simultanes) as ex:
            return dict(ex.map(lambda r: self._un_appel(r, modele), requetes))


class FournisseurOpenAI(FournisseurCompatibleOpenAI):
    lot_possible = True

    def __init__(self):
        super().__init__(URL_OPENAI, os.environ.get("OPENAI_API_KEY", ""), "openai")

    def soumettre_lot(self, requetes, modele, description=""):
        lignes = [json.dumps({
            "custom_id": r["id"], "method": "POST", "url": "/v1/chat/completions",
            "body": corps_requete(modele, r["consigne"], r["contenu"], r.get("max_sortie", 2500)),
        }, ensure_ascii=False) for r in requetes]
        fichier = requete("POST", f"{self.url}/files", headers=self.entetes,
                          data={"purpose": "batch"},
                          files={"file": ("lot.jsonl", "\n".join(lignes).encode("utf-8"))}).json()
        lot = requete("POST", f"{self.url}/batches", headers=self.entetes, json={
            "input_file_id": fichier["id"], "endpoint": "/v1/chat/completions",
            "completion_window": "24h", "metadata": {"description": description[:500]},
        }).json()
        return lot["id"]

    def etat_lot(self, lot_id):
        """Renvoie ("en_cours" | "termine" | "echec", infos)."""
        lot = requete("GET", f"{self.url}/batches/{lot_id}", headers=self.entetes).json()
        statut = lot.get("status")
        if statut == "completed":
            return "termine", lot
        if statut in ("failed", "expired", "cancelled"):
            return "echec", lot
        return "en_cours", lot

    def resultats_lot(self, lot):
        resultats = {}
        for cle in ("output_file_id", "error_file_id"):
            if not lot.get(cle):
                continue
            texte = requete("GET", f"{self.url}/files/{lot[cle]}/content", headers=self.entetes).text
            for ligne in texte.splitlines():
                if not ligne.strip():
                    continue
                item = json.loads(ligne)
                corps = (item.get("response") or {}).get("body") or {}
                try:
                    contenu = corps["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    contenu = None
                resultats[item["custom_id"]] = (contenu, corps.get("usage", {}))
        return resultats


class FournisseurMistral(FournisseurCompatibleOpenAI):
    def __init__(self):
        super().__init__(URL_MISTRAL, os.environ.get("MISTRAL_API_KEY", ""), "mistral")


class FournisseurDemo(Fournisseur):
    """Rejoue des réponses enregistrées : {"tri": {id: {...}}, "redaction": {...}, "synthese": {...}}."""
    nom = "demo"
    lot_possible = False

    def __init__(self, chemin=None):
        chemin = chemin or os.environ.get("VEILLE_REPONSES_DEMO")
        with open(chemin, encoding="utf-8") as f:
            self.reponses = json.load(f)

    def direct(self, requetes, modele, simultanes=8):
        res = {}
        for r in requetes:
            etape, _, ident = r["id"].partition(":")
            rep = self.reponses.get(etape, {}).get(ident)
            res[r["id"]] = (json.dumps(rep, ensure_ascii=False) if rep is not None else None,
                            {"prompt_tokens": estimer_jetons(r["consigne"] + r["contenu"]),
                             "completion_tokens": 400})
        return res


def fournisseur(cfg):
    global EFFORT
    EFFORT = cfg["ia"].get("effort_raisonnement") or None
    nom = os.environ.get("VEILLE_FOURNISSEUR") or cfg["ia"].get("fournisseur", "openai")
    if nom == "openai":
        return FournisseurOpenAI()
    if nom == "mistral":
        return FournisseurMistral()
    if nom == "demo":
        return FournisseurDemo()
    raise ErreurIA(f"Fournisseur d'IA inconnu : {nom}")


def attendre(secondes):
    time.sleep(secondes)
