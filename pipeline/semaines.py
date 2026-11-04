"""Calcul des semaines de veille (lundi au dimanche, heure de Paris)."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Semaine:
    id: str          # ex. "2026-S44"
    lundi: date
    dimanche: date

    def contient(self, jour: date) -> bool:
        return self.lundi <= jour <= self.dimanche


def depuis_lundi(lundi: date) -> Semaine:
    annee, numero, _ = lundi.isocalendar()
    return Semaine(f"{annee}-S{numero:02d}", lundi, lundi + timedelta(days=6))


def depuis_id(identifiant: str) -> Semaine:
    annee, numero = identifiant.split("-S")
    return depuis_lundi(date.fromisocalendar(int(annee), int(numero), 1))


def semaine_precedente(maintenant: datetime | None = None, fuseau: str = "Europe/Paris") -> Semaine:
    tz = ZoneInfo(fuseau)
    maintenant = (maintenant or datetime.now(tz)).astimezone(tz)
    lundi_courant = maintenant.date() - timedelta(days=maintenant.weekday())
    return depuis_lundi(lundi_courant - timedelta(days=7))
