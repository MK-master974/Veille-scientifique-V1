"""Assemble et vérifie les corrigés « chiffres relevés » du corpus de référence (VS-D32).

Pour une étude diagnostique ou une méta-analyse, le corrigé est fait des chiffres que les auteurs
d'une revue en accès libre ont déjà relevés dans un tableau. Ce script lit ces tableaux à la
source, dans Europe PMC. Aucune IA n'est appelée : aucun coût. Aucun texte d'article n'est gardé ;
seules des lignes de tableaux de revues sous licence CC BY ou CC0 sont écrites dans le journal.

Quatre modes, choisis par la dernière demande de banc/candidats_chiffres.json :
- « reperer » : pour chaque revue candidate, sa licence, ses tableaux, les études que chaque
  tableau cite, et la licence de ces études. Sert à choisir les revues sources et les articles.
  Le genre « robins_i » (VS-D54) repère les tableaux de jugements ROBINS-I, qui portent des mots
  (« serious », « moderate ») plutôt que des chiffres.
- « lire » : les lignes d'un tableau d'une revue source qui portent sur les études choisies.
  Sert à écrire le corrigé.
- « verifier » : pour chaque chiffre de banc/corpus/chiffres_releves.json, trois contrôles :
  licences de la revue source et de l'article ; présence du chiffre dans la ligne du tableau
  source (recopie) ; présence du chiffre dans l'article lui-même, à côté des chiffres de son
  groupe (règle de voisinage de banc/chiffres.py). Un chiffre absent de l'article est écarté du
  score avant toute mesure (VS-D34).

- « recalculer » : après une vérification, recalcule le score des chiffres relevés à partir des
  extractions déjà produites par un lancement du banc (son artefact), avec les règles et le corpus
  du moment. Aucun nouvel appel à l'IA. Sert quand une règle de comparaison a été corrigée.

Usage : python banc/assembler_chiffres.py
"""
import collections
import difflib
import importlib.util
import json
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from pipeline import acces, texte  # noqa: E402
from pipeline.reseau import requete  # noqa: E402

_spec = importlib.util.spec_from_file_location("chiffres", RACINE / "banc" / "chiffres.py")
chiffres = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chiffres)

DEMANDES = RACINE / "banc" / "candidats_chiffres.json"
LICENCES_ADMISES = acces.PERIMETRE_RETENU            # CC BY et CC0 (VS-D21)
CELLULE_REPERAGE = 28
CELLULE_LECTURE = 140

# Mots qui signalent un tableau de données, par type de revue source.
MOTS = {
    "diagnostic": ("sensitivity", "specificity", "true positive", "false positive", " tp", " fp", " fn", " tn",
                   "auc", "likelihood", "predictive", "sample size", "reference standard", "index test"),
    "revue": ("smd", " md", "wmd", "95% ci", "95%ci", "95 % ci", "effect size", "pooled", "i2", "i²",
              "odds ratio", "risk ratio", " rr", " or", "hedges", "number of studies", "participants"),
    # Tableaux de jugements ROBINS-I (VS-D54) : noms des domaines et niveaux de risque.
    "robins_i": ("robins", "confounding", "selection of participants", "classification of intervention",
                 "deviation", "missing data", "measurement of outcome", "selection of the reported",
                 "reported result", "serious", "critical", "moderate", "no information"),
}
# Pour retenir un tableau : nombre minimal de mots-clés, puis de nombres. Un tableau de jugements
# ROBINS-I contient des mots, pas des chiffres.
SEUILS_REPERAGE = {"diagnostic": (2, 10), "revue": (2, 10), "robins_i": (4, 0)}


def journal(message=""):
    print(message, flush=True)


def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _propre(t):
    return re.sub(r"\s+", " ", t or "").strip()


# --- Lecture d'une revue source (fonctions pures) ---------------------------------------------

_DOI = re.compile(r"10\.\d{4,9}/[^\s\"<>]+")


def references(racine):
    """Identifiant XML d'une référence → {"pmid", "doi", "auteur", "annee", "titre"} de l'étude citée."""
    refs = {}
    for ref in racine.iter():
        if _local(ref.tag) != "ref" or not ref.get("id"):
            continue
        infos = {"pmid": "", "doi": "", "auteur": "", "annee": "", "titre": ""}
        liens = []
        for el in ref.iter():
            nom, contenu = _local(el.tag), (el.text or "").strip()
            liens += [v for v in el.attrib.values() if "10." in v]
            if nom == "pub-id" and contenu and el.get("pub-id-type") in ("pmid", "doi") \
                    and not infos[el.get("pub-id-type")]:
                infos[el.get("pub-id-type")] = contenu.lower() if el.get("pub-id-type") == "doi" else contenu
            elif nom == "surname" and contenu and not infos["auteur"]:
                infos["auteur"] = contenu
            elif nom == "year" and contenu and not infos["annee"]:
                infos["annee"] = contenu[:4]
            elif nom == "article-title" and not infos["titre"]:
                infos["titre"] = _propre("".join(el.itertext()))
        if not infos["doi"]:                         # DOI écrit en clair, ou dans un lien
            m = _DOI.search(" ".join(liens) + " " + " ".join(ref.itertext()))
            if m:
                infos["doi"] = m.group(0).rstrip(".,;)").lower()
        refs[ref.get("id")] = infos
    return refs


def _cellule(element, cites):
    """Texte d'une cellule ; chaque renvoi bibliographique y est noté et ajouté à « cites »."""
    morceaux = [element.text or ""]
    for enfant in element:
        if _local(enfant.tag) == "xref" and enfant.get("ref-type") == "bibr":
            cites.extend((enfant.get("rid") or "").split())
            morceaux.append("".join(enfant.itertext()))
        else:
            morceaux.append(_cellule(enfant, cites))
        morceaux.append(enfant.tail or "")
    return _propre("".join(morceaux))


def _sans_accents(t):
    t = unicodedata.normalize("NFKD", (t or "").replace("ı", "i").replace("ø", "o").replace("ł", "l"))
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _nomme(ligne, ref):
    """Vrai si le début de la ligne écrit le nom du premier auteur de la référence."""
    return len(ref["auteur"]) > 1 and re.search(
        rf"\b{re.escape(_sans_accents(ref['auteur']))}\b", _sans_accents(" ".join(ligne[:2]))) is not None


def _cites_par_nom(ligne, refs):
    """Études citées par « Auteur année » dans les premières cellules, quand il n'y a pas de renvoi."""
    debut = " ".join(ligne[:2])
    trouves = []
    for ident, r in refs.items():
        if r["auteur"] and r["annee"] and len(r["auteur"]) > 2 and re.search(
                rf"\b{re.escape(r['auteur'])}\b[^|]{{0,40}}{r['annee']}", debut, re.I):
            trouves.append(ident)
    if trouves or not ligne:
        return trouves
    # Sans année dans la ligne : le nom seul, s'il ne désigne qu'une référence de l'article.
    auteurs = collections.Counter(r["auteur"].lower() for r in refs.values() if r["auteur"])
    for ident, r in refs.items():
        if len(r["auteur"]) > 2 and auteurs[r["auteur"].lower()] == 1 and re.match(
                rf"\W*{re.escape(r['auteur'])}\b", ligne[0], re.I):
            trouves.append(ident)
    return trouves


def tableaux(racine):
    """Tableaux d'un article : libellé, légende, lignes, et pour chaque ligne les références citées.

    Une ligne sans citation hérite de la précédente quand elle en est la suite : première cellule
    vide, ou moins de cellules que le tableau n'a de colonnes (cellule fusionnée sur plusieurs lignes).
    « cites_bloc » applique un héritage plus large, pour les tableaux où une étude occupe un bloc de
    lignes : toute ligne sans citation appartient à la dernière étude citée.

    Un renvoi numéroté peut être faux dans le fichier source. Quand la ligne écrit un nom d'auteur
    et une année qui désignent une autre référence que le renvoi, c'est le nom écrit qui est suivi.
    Quand ni le renvoi ni le nom ne concordent, la ligne est marquée « douteux ».
    """
    refs = references(racine)
    resultat = []
    for tw in racine.iter():
        if _local(tw.tag) != "table-wrap":
            continue
        label = caption = ""
        for el in tw:
            if _local(el.tag) == "label":
                label = _propre("".join(el.itertext()))
            elif _local(el.tag) == "caption":
                caption = _propre("".join(el.itertext()))
        lignes = []
        for tr in (e for e in tw.iter() if _local(e.tag) == "tr"):
            cites = []
            cellules = [_cellule(c, cites) for c in tr if _local(c.tag) in ("td", "th")]
            if any(cellules):
                lignes.append({"cellules": cellules, "cites": list(dict.fromkeys(cites)), "herite": False})
        colonnes = max((len(l["cellules"]) for l in lignes), default=0)
        courant, bloc = [], []
        for l in lignes:
            l["douteux"] = False
            par_nom = _cites_par_nom(l["cellules"], refs)
            connus = [i for i in l["cites"] if i in refs and refs[i]["auteur"]]
            if not l["cites"]:
                l["cites"] = par_nom
            elif connus and not any(_nomme(l["cellules"], refs[i]) for i in connus):
                if par_nom:
                    l["cites"] = par_nom               # le nom et l'année écrits l'emportent sur le renvoi
                else:
                    l["douteux"] = True
            if l["douteux"]:
                courant, bloc, l["cites_bloc"] = [], [], []    # les lignes suivantes n'en héritent pas
            elif l["cites"]:
                courant = bloc = l["cites"]
                l["cites_bloc"] = l["cites"]
            else:
                l["cites_bloc"] = bloc
                if courant and (not l["cellules"][0] or len(l["cellules"]) < colonnes):
                    l["cites"], l["herite"] = courant, True
                else:
                    courant = []
        notes = " ".join(_propre("".join(e.itertext())) for e in tw.iter() if _local(e.tag) == "table-wrap-foot")
        resultat.append({"label": label or f"Tableau {len(resultat) + 1}", "caption": caption,
                         "lignes": lignes, "colonnes": colonnes, "notes": notes})
    return resultat, refs


def score_donnees(tableau, genre):
    contenu = (tableau["caption"] + " " + " ".join(" ".join(l["cellules"]) for l in tableau["lignes"])).lower()
    return sum(1 for m in MOTS[genre] if m in contenu), len(chiffres.nombres(contenu))


def meme_libelle(a, b):
    """« Table 2 », « TABLE 2. » et « table 2 » désignent le même tableau."""
    forme = lambda x: re.sub(r"[\s.:]+", " ", (x or "").lower()).strip()   # noqa: E731
    return forme(a) == forme(b)


def lignes_d_une_etude(tableau, idents, bloc=False):
    """Lignes d'un tableau qui citent l'une des références « idents » (ou en héritent).

    Une ligne dont l'attribution est douteuse n'est jamais retenue.
    """
    cle = "cites_bloc" if bloc else "cites"
    return [l for l in tableau["lignes"] if set(l[cle]) & set(idents) and not l["douteux"]]


# --- Réseau -----------------------------------------------------------------------------------

def decrire(identifiants):
    """PMID ou DOI → description Europe PMC : pmid, pmcid, licence, revue, année, titre, doi."""
    infos = {}
    identifiants = [i for i in dict.fromkeys(identifiants) if i]
    for i in range(0, len(identifiants), 20):
        lot = identifiants[i:i + 20]
        termes = [f'DOI:"{x}"' if "/" in x else f"EXT_ID:{x}" for x in lot]
        try:
            rep = requete("GET", f"{acces.EUROPE_PMC}/search", params={
                "query": "(" + " OR ".join(termes) + ") AND SRC:MED", "format": "json",
                "resultType": "core", "pageSize": 100}).json()
        except Exception as e:                      # une panne ne doit pas arrêter le repérage
            journal(f"  Europe PMC : échec d'un paquet ({str(e)[:120]})")
            continue
        for r in (rep.get("resultList") or {}).get("result") or []:
            fiche = {"pmid": str(r.get("pmid") or ""), "pmcid": r.get("pmcid") or "",
                     "licence": acces.classe_licence(r.get("license")),
                     "revue": ((r.get("journalInfo") or {}).get("journal") or {}).get("medlineAbbreviation", ""),
                     "annee": str(r.get("pubYear") or ""), "titre": _propre(r.get("title")),
                     "doi": (r.get("doi") or "").lower(),
                     "types": ((r.get("pubTypeList") or {}).get("pubType") or [])}
            if fiche["pmid"]:
                infos[fiche["pmid"]] = fiche
            if fiche["doi"]:
                infos[fiche["doi"]] = fiche
        time.sleep(0.3)
    return infos


def _titre_plat(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def resoudre(refs, idents):
    """Référence citée → description Europe PMC, par PMID, par DOI, puis par titre exact.

    La recherche par titre ne garde un résultat que si son titre est presque identique à celui de
    la référence : une étude mal identifiée fausserait le corrigé.
    """
    cle = lambda i: refs[i]["pmid"] or refs[i]["doi"]          # noqa: E731
    connus = decrire([cle(i) for i in idents if cle(i)])
    fiches = {i: connus.get(cle(i)) for i in idents if cle(i)}
    for i in idents:
        r = refs[i]
        if fiches.get(i) or len(_titre_plat(r["titre"])) < 25:
            continue
        mots = _titre_plat(r["titre"])
        try:
            rep = requete("GET", f"{acces.EUROPE_PMC}/search", params={
                "query": f'TITLE:"{mots}" AND SRC:MED', "format": "json", "resultType": "core", "pageSize": 5}).json()
        except Exception:
            continue
        for x in (rep.get("resultList") or {}).get("result") or []:
            if difflib.SequenceMatcher(None, mots, _titre_plat(x.get("title"))).ratio() >= 0.92 and x.get("pmid"):
                fiches[i] = decrire([str(x["pmid"])]).get(str(x["pmid"]))
                break
        time.sleep(0.2)
    return fiches


def lire_xml(pmcid):
    xml, etat = acces.texte_integral_xml(pmcid)
    if not xml:
        return None, etat
    try:
        return ET.fromstring(xml), "ok"
    except ET.ParseError:
        return None, "xml illisible"


def utilisable(fiche):
    return bool(fiche) and bool(fiche["pmcid"]) and fiche["licence"] in LICENCES_ADMISES


# --- Mode « reperer » -------------------------------------------------------------------------

def reperer(demande):
    for genre in ("diagnostic", "revue", "robins_i"):
        sources = [str(p) for p in demande.get(genre, [])]
        if demande.get("tranche"):                   # une partie de la liste, pour tenir dans le délai
            debut, fin = demande["tranche"]
            sources = sources[debut:fin]
        if not sources:
            continue
        min_mots, min_nombres = SEUILS_REPERAGE[genre]
        journal(f"\n##### {genre.upper()} — {len(sources)} revues candidates")
        infos = decrire(sources)
        for pmid in sources:
            s = infos.get(pmid)
            if not s:
                journal(f"\n=== PMID {pmid} : introuvable dans Europe PMC")
                continue
            entete = (f"\n=== PMID {pmid} | {s['pmcid'] or 'sans PMC'} | {s['licence']} | {s['revue']} {s['annee']} | "
                      f"{s['doi']}\n    {s['titre'][:120]}")
            if not utilisable(s):
                journal(entete + "\n    écartée : licence hors CC BY et CC0, ou pas de texte dans PMC")
                continue
            racine, etat = lire_xml(s["pmcid"])
            if racine is None:
                journal(entete + f"\n    écartée : texte intégral non lu ({etat})")
                continue
            tabs, refs = tableaux(racine)
            journal(entete + f"\n    {len(tabs)} tableaux ; {len(refs)} références, dont "
                    f"{sum(1 for r in refs.values() if r['pmid'])} avec PMID et "
                    f"{sum(1 for r in refs.values() if r['doi'])} avec DOI")
            if genre == "robins_i":
                # Où sont les jugements ROBINS-I ? Dans une figure (image, que le code ne lit pas), ou dans un
                # tableau dont les lignes ne citent pas assez d'études identifiables.
                figures = sum(1 for f in racine.iter() if _local(f.tag) == "fig"
                              and re.search(r"robins|risk of bias", " ".join(f.itertext()), re.I))
                sans_etudes = [t["label"] for t in tabs if score_donnees(t, genre)[0] >= min_mots
                               and len({i for l in t["lignes"] for i in l["cites"] if i in refs}) < 2]
                journal(f"    ROBINS-I : {figures} figure(s) de risque de biais (image) ; tableau(x) de jugements sans "
                        f"études identifiées : {', '.join(sans_etudes) or 'aucun'}")
            for t in tabs:
                t["lignes"] = [l for l in t["lignes"] if not l["douteux"]]
            retenus = [t for t in tabs if len({i for l in t["lignes"] for i in l["cites"] if i in refs}) >= 2
                       and score_donnees(t, genre)[0] >= min_mots and score_donnees(t, genre)[1] >= min_nombres]
            etudes = resoudre(refs, sorted({i for t in retenus for l in t["lignes"] for i in l["cites"] if i in refs}))
            cle = lambda i: i                                          # noqa: E731
            bons, autres = {}, collections.Counter()
            for t in tabs:
                idents = list(dict.fromkeys(i for l in t["lignes"] for i in l["cites"] if i in refs))
                mots, nb = score_donnees(t, genre)
                if len(idents) < 2 or mots < min_mots or nb < min_nombres:
                    continue
                ok = [i for i in idents if utilisable(etudes.get(cle(i)))]
                entete_t = " | ".join(c[:CELLULE_REPERAGE] for c in t["lignes"][0]["cellules"])
                journal(f"    --- {t['label']} | {len(t['lignes'])} lignes × {t['colonnes']} col | {len(idents)} études, "
                        f"dont {len(ok)} utilisables | mots-clés {mots} | {nb} nombres | {t['caption'][:90]}\n"
                        f"        en-tête : {entete_t[:230]}")
                for i in idents:
                    f = etudes.get(cle(i))
                    if utilisable(f):
                        types = ",".join(x for x in f["types"] if x not in ("research-article", "Journal Article"))[:40]
                        bons[f["pmid"]] = (f"{f['pmid']} {f['pmcid']} {f['licence']} {f['revue']} {f['annee']} "
                                           f"[{refs[i]['auteur']}] {types}")
                    elif not f:
                        autres["non résolue"] += 1
                    elif not f["pmcid"]:
                        autres["sans PMC"] += 1
                    else:
                        autres[f["licence"]] += 1
            journal(f"    études utilisables, sous CC BY ou CC0 avec texte dans PMC : {len(bons)}"
                    + (" — autres citations : " + ", ".join(f"{k} ×{v}" for k, v in sorted(autres.items())) if autres else ""))
            if len(bons) >= int(demande.get("minimum", 2)):
                for ligne in bons.values():
                    journal("      " + ligne)
            time.sleep(0.3)
    return 0


# --- Mode « lire » ----------------------------------------------------------------------------

def lire(demande):
    for d in demande.get("lectures", []):
        pmid = str(d["source"])
        s = decrire([pmid]).get(pmid)
        if not utilisable(s):
            journal(f"\n=== PMID {pmid} : écartée (licence hors CC BY et CC0, ou pas de texte dans PMC)")
            continue
        racine, etat = lire_xml(s["pmcid"])
        if racine is None:
            journal(f"\n=== PMID {pmid} : texte intégral non lu ({etat})")
            continue
        tabs, refs = tableaux(racine)
        tabs = [t for t in tabs if not d.get("tableaux") or any(meme_libelle(t["label"], x) for x in d["tableaux"])]
        fiches = resoudre(refs, sorted({i for t in tabs for l in t["lignes"] for i in l["cites"] if i in refs}))
        voulus = {str(p) for p in d.get("pmids", [])}
        # Par défaut : les études sous licence CC BY ou CC0 dont le texte est dans PubMed Central.
        idents = {i for i, f in fiches.items() if f and (f["pmid"] in voulus if voulus else utilisable(f))}
        journal(f"\n=== PMID {pmid} | {s['pmcid']} | {s['licence']} | {s['revue']} {s['annee']} | {s['doi']}")
        for i in sorted(idents, key=lambda i: fiches[i]["pmid"]):
            f = fiches[i]
            types = ",".join(x for x in f["types"] if x not in ("research-article", "Journal Article"))[:60]
            journal(f"  étude {f['pmid']} | {f['pmcid']} | {f['licence']} | {f['revue']} {f['annee']} | {f['doi']} | "
                    f"[{refs[i]['auteur']} {refs[i]['annee']}] {types} | {f['titre'][:90]}")
        bloc = d.get("heritage") == "bloc"
        for t in tabs:
            lignes = lignes_d_une_etude(t, idents, bloc)
            douteuses = sum(1 for l in t["lignes"] if l["douteux"])
            if not lignes:
                continue
            journal(f"--- {t['label']} — {t['caption'][:200]}" + (f" — {douteuses} ligne(s) à l'attribution douteuse, écartée(s)" if douteuses else ""))
            for l in t["lignes"][:int(d.get("lignes_entete", 2))]:
                if l not in lignes:
                    journal("  en-tête | " + " | ".join(c[:CELLULE_LECTURE] for c in l["cellules"]))
            if t.get("notes"):
                journal(f"  notes | {t['notes'][:600]}")
            for l in lignes:
                cites = l["cites_bloc"] if bloc else l["cites"]
                qui = ",".join(dict.fromkeys(fiches[i]["pmid"] for i in cites if i in idents))
                suite = " ↳" if l["herite"] or not l["cites"] else ""
                journal(f"  [{qui}{suite}] | " + " | ".join(c[:CELLULE_LECTURE] for c in l["cellules"]))
        time.sleep(0.3)
    return 0


# --- Mode « verifier » ------------------------------------------------------------------------

def texte_des_lignes(tableau_ou_liste, idents, bloc=False):
    tabs = tableau_ou_liste if isinstance(tableau_ou_liste, list) else [tableau_ou_liste]
    return " ; ".join(" | ".join(l["cellules"]) for t in tabs for l in lignes_d_une_etude(t, idents, bloc))


def verifier(_demande=None):
    corpus = chiffres.charger()
    defauts = chiffres.verifier_forme(corpus)
    for d in defauts:
        journal(f"DÉFAUT DE FORME : {d}")
    cas = chiffres.cas_du_corpus(corpus)
    if not cas:
        journal("Corpus vide : rien à vérifier.")
        return 1 if defauts else 0
    fiches = decrire([c["pmid"] for c in cas] + [c["source"]["pmid"] for c in cas])
    sources, bilan, etats = {}, collections.Counter(), {}
    for c in cas:
        s, a = c["source"], fiches.get(c["pmid"])
        journal(f"\n=== {c['type_etude']} PMID {c['pmid']} — corrigé : PMID {s['pmid']}, {s['tableau']}")
        fs = fiches.get(s["pmid"])
        licence_ok = utilisable(a) and utilisable(fs)
        journal(f"  licences : article {a['licence'] if a else 'introuvable'} ({a['pmcid'] if a else '-'}), "
                f"revue source {fs['licence'] if fs else 'introuvable'} → {'conformes' if licence_ok else 'NON CONFORMES'}")
        bilan["licences conformes" if licence_ok else "licences non conformes"] += 1
        if not licence_ok:
            continue
        if s["pmid"] not in sources:
            racine, _ = lire_xml(fs["pmcid"])
            sources[s["pmid"]] = tableaux(racine) if racine is not None else ([], {})
            time.sleep(0.3)
        tabs, refs = sources[s["pmid"]]
        voulus = [t for t in tabs if any(meme_libelle(t["label"], x) for x in s["tableau"].split(","))]
        idents = {i for i, r in refs.items() if r["pmid"] == c["pmid"] or (a["doi"] and r["doi"] == a["doi"])
                  or (len(_titre_plat(r["titre"])) >= 25 and difflib.SequenceMatcher(
                      None, _titre_plat(r["titre"]), _titre_plat(a["titre"])).ratio() >= 0.92)}
        ligne_source = texte_des_lignes(voulus, idents, s.get("lignes") == "bloc")
        if not ligne_source:
            journal("  recopie : AUCUNE LIGNE du tableau source ne cite cette étude")
        xml, _ = acces.texte_integral_xml(a["pmcid"])
        doc = texte.document_jats(xml, None) if xml else None
        lu = texte.texte_lu(doc) if doc else ""
        if doc:
            journal(f"  article lu : {sum(len(b['texte']) for b in doc['blocs'])} caractères, "
                    f"{doc['tableaux_en_image']} tableau(x) en image, {len(doc['non_lus'])} bloc(s) laissé(s) de côté")
        else:
            journal("  article : TEXTE INTÉGRAL NON LU")
        time.sleep(0.3)
        confirmes = chiffres.confirmes_dans_un_texte(c["chiffres"], lu) if doc else {}
        for x in c["chiffres"]:
            recopie = chiffres.present(x, ligne_source)
            dans = confirmes.get(x["id"]) if doc else None
            etats[f"{c['pmid']}:{x['id']}"] = dans
            bilan["recopie conforme" if recopie else "recopie à revoir"] += 1
            bilan[{True: "dans l'article", False: "absent de l'article", None: "article non lu"}[dans]] += 1
            ecart = "" if x.get("dans_l_article") == dans else f"  ← le corpus dit {x.get('dans_l_article')}"
            journal(f"  {x['id']} | {x['nature']} | {x.get('libelle', '')[:60]} | {x['valeur']} | recopie "
                    f"{'conforme' if recopie else 'À REVOIR'} | dans l'article : "
                    f"{ {True: 'oui', False: 'NON', None: 'non lu'}[dans] }{ecart}")
    journal("\n===== BILAN =====")
    for k, v in sorted(bilan.items()):
        journal(f"  {k} : {v}")
    journal("\n===== ÉTAT « dans_l_article » DE CHAQUE CHIFFRE =====")
    journal(json.dumps(etats, ensure_ascii=False))
    return etats if _demande and _demande.get("mode") == "recalculer" else 0


# --- Mode « recalculer » ----------------------------------------------------------------------

def recalculer(demande):
    """Vérifie le corpus, puis recalcule le score sur les extractions d'un lancement déjà fait."""
    etats = verifier(demande)
    if not isinstance(etats, dict):
        return 1
    chemin = RACINE / demande.get("resultats", "resultats-banc/resultats-extraction.json")
    if not chemin.exists():
        journal(f"\nARRÊT : résultats introuvables ({chemin.name}). L'artefact du lancement n'a pas été récupéré.")
        return 1
    extractions = json.loads(chemin.read_text(encoding="utf-8"))["extractions"]
    cas = chiffres.cas_du_corpus(chiffres.charger())
    for c in cas:
        for x in c["chiffres"]:
            x["dans_l_article"] = etats.get(f"{c['pmid']}:{x['id']}")
    journal(f"\n===== SCORE RECALCULÉ sur les extractions du lancement {demande.get('lancement')} =====")
    for niveau, nom in (("resume", "résumé seul"), ("integral", "texte intégral")):
        lignes_par_cas = {c["pmid"]: chiffres.mesurer_cas(c, (extractions.get(f"{niveau}:pm{c['pmid']}") or {}).get("extraction"))
                          for c in cas}
        toutes = [x for lignes in lignes_par_cas.values() for x in lignes]
        journal(f"\n--- {nom} : " + json.dumps(chiffres.score(toutes), ensure_ascii=False))
        for t in sorted({c["type_etude"] for c in cas}):
            s = chiffres.score([x for c in cas if c["type_etude"] == t for x in lignes_par_cas[c["pmid"]]])
            journal(f"    {t} : {s['retrouves']} sur {s['confirmes_dans_l_article']} ({s['part']}), "
                    f"{s['ecartes_car_absents_de_l_article']} écarté(s)")
        if niveau == "integral":
            for c in cas:
                for x in lignes_par_cas[c["pmid"]]:
                    if x["etat"] != "retrouve" or x["dans_l_article"] is not True:
                        journal(f"    PMID {c['pmid']} | {x['id']} | {x['nature']} | {x['valeur']} | {x['etat']} | "
                                f"dans l'article : {x['dans_l_article']}")
    return 0


def main():
    demande = json.loads(DEMANDES.read_text(encoding="utf-8"))["demandes"][-1]
    journal(f"Demande du {demande.get('date')} : mode « {demande.get('mode')} » — {demande.get('raison', '')}")
    modes = {"reperer": reperer, "lire": lire, "verifier": verifier, "recalculer": recalculer}
    if demande.get("mode") not in modes:
        raise SystemExit(f"Mode inconnu : {demande.get('mode')!r} (attendu : {', '.join(modes)})")
    resultat = modes[demande["mode"]](demande)
    return resultat if isinstance(resultat, int) else 0


if __name__ == "__main__":
    sys.exit(main())
