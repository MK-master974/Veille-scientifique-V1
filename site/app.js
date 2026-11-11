/* Veille Santé — web app de lecture. Aucune donnée personnelle ne quitte l'appareil :
   profil, favoris et réglages restent dans le stockage local du navigateur. */
(() => {
  'use strict';

  // --- libellés ---------------------------------------------------------------------------------
  const LIB = {
    type: {
      recommandation: 'Recommandation', revue_systematique: 'Revue systématique', meta_analyse: 'Méta-analyse',
      essai_randomise: 'Essai randomisé', etude_diagnostique: 'Étude diagnostique',
    },
    etiquette: { preliminaire: 'Préliminaire', modere: 'Modéré', solide: 'Solide' },
    niveauPreuve: { preliminaire: 1, modere: 2, solide: 3 },
    verdict: {
      change_la_pratique: 'Change la pratique', remet_en_question: 'Remet en question',
      confirme: 'Confirme', a_surveiller: 'À surveiller',
    },
    verdictGroupe: {
      change_la_pratique: 'Ce qui change la pratique', remet_en_question: 'Remis en question',
      confirme: 'Ce qui se confirme', a_surveiller: 'À surveiller',
    },
    interet: { culture: 'Culture générale', praticien: 'Praticien concerné', expert: 'Expert' },
    detail: { flash: 'Flash', standard: 'Standard', complet: 'Complet' },
    freq: { hebdo: 'Chaque semaine', mensuel: 'Récapitulatif mensuel', aucune: 'Aucune' },
  };
  const ORDRE_VERDICTS = ['change_la_pratique', 'remet_en_question', 'confirme', 'a_surveiller'];
  const RANG_INTERET = { culture: 0, praticien: 1, expert: 2 };
  const RANG_DETAIL = { flash: 0, standard: 1, complet: 2 };
  // Version de l'app, affichée en bas de chaque page : à faire suivre à chaque mise en ligne (CHANGELOG.md).
  const VERSION_APP = '1.1.0';
  // Avertissement court, affiché sous chaque fiche, et texte complet (page À propos, fiche seule).
  const MENTION = 'Fiche produite et contrôlée par IA, sans relecture humaine avant publication. Consultez la publication originale avant toute décision clinique.';
  const MENTION_COMPLETE = 'Cette fiche a été produite et analysée par intelligence artificielle. Elle ne fait pas l’objet d’une validation humaine individuelle avant publication. Malgré plusieurs contrôles automatisés, des erreurs d’extraction, d’interprétation ou de synthèse peuvent subsister. Le niveau d’analyse dépend notamment de l’accessibilité du texte intégral. Consultez systématiquement la publication originale avant d’utiliser ces informations dans une décision clinique.';
  // Niveau d'accès documentaire. Tant que le moteur ne lit que le titre et le résumé, toutes les
  // fiches sont au niveau « résumé » ; le champ `acces` d'une fiche prendra le relais ensuite.
  const ACCES = {
    integral: 'Analyse du texte intégral',
    partiel: 'Analyse d’un texte partiel',
    resume: 'Analyse à partir du résumé uniquement',
  };

  // --- état ---------------------------------------------------------------------------------------
  const E = {
    config: { nom_app: 'Veille Santé', email_contact: '', onesignal_app_id: '' },
    catalogue: null, libelles: {}, courts: {}, index: null,
    semaines: new Map(), recherche: new Map(),
    toutesFiches: false, filtre: 'tout', installation: null,
  };
  const vue = document.getElementById('vue');

  // --- stockage local (peut être indisponible : navigation privée, données bloquées) --------------
  const stock = {
    lire(cle, defaut) {
      try { const v = localStorage.getItem(cle); return v ? JSON.parse(v) : defaut; } catch { return defaut; }
    },
    ecrire(cle, valeur) { try { localStorage.setItem(cle, JSON.stringify(valeur)); } catch { /* sans effet */ } },
    effacer(cle) { try { localStorage.removeItem(cle); } catch { /* sans effet */ } },
  };
  const profil = () => stock.lire('vs.profil', null);
  const enregistrerProfil = (p) => { stock.ecrire('vs.profil', p); synchroniserNotifications(); };
  const favoris = () => stock.lire('vs.favoris', []);
  const enregistrerFavoris = (f) => stock.ecrire('vs.favoris', f);

  // --- utilitaires --------------------------------------------------------------------------------
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const urlSure = (u) => (/^https:\/\//i.test(u || '') ? u : '');
  const sansAccents = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const pluriel = (n, un, plusieurs) => `${n} ${n > 1 ? plusieurs : un}`;

  const fmtJour = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' });
  const fmtJourAn = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
  const jour = (iso, avecAn) => {
    const d = new Date(`${iso}T12:00:00`);
    let t = (avecAn ? fmtJourAn : fmtJour).format(d);
    if (d.getDate() === 1) t = t.replace(/^1 /, '1er ');
    return t;
  };
  const numeroSemaine = (id) => Number(String(id).split('-S')[1]);
  const retiree = (id) => (E.config.fiches_retirees || []).includes(id);
  const periode = (s) => `du ${jour(s.lundi)} au ${jour(s.dimanche, true)}`;

  async function json(chemin) {
    const rep = await fetch(chemin, { cache: 'no-cache' });
    if (!rep.ok) throw new Error(`${rep.status} ${chemin}`);
    return rep.json();
  }
  async function chargerSemaine(id) {
    if (!E.semaines.has(id)) E.semaines.set(id, await json(`data/semaines/${id}.json`));
    return E.semaines.get(id);
  }
  async function chargerRecherche(annee) {
    if (!E.recherche.has(annee)) {
      try { E.recherche.set(annee, await json(`data/recherche/${annee}.json`)); } catch { E.recherche.set(annee, []); }
    }
    return E.recherche.get(annee);
  }

  function toast(message) {
    const t = document.getElementById('toast');
    t.textContent = message;
    t.hidden = false;
    clearTimeout(toast.minuterie);
    toast.minuterie = setTimeout(() => { t.hidden = true; }, 2600);
  }

  async function copier(texte) {
    try { await navigator.clipboard.writeText(texte); return true; } catch { return false; }
  }

  // --- icônes -------------------------------------------------------------------------------------
  const ICONES = {
    favori: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>',
    partager: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 13v7h14v-7"/></svg>',
    zotero: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
    signaler: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 21V4h12l-2 4 2 4H5"/></svg>',
  };

  // --- profil : visibilité d'une fiche ------------------------------------------------------------
  function reglageVisible(fiche, p) {
    let meilleur = null;
    for (const d of fiche.domaines) {
      const r = p?.domaines?.[d];
      if (!r) continue;
      const visible = r.i === 'expert' || (r.i === 'praticien' && fiche.pertinence >= 2) || (r.i === 'culture' && fiche.pertinence === 3);
      if (!visible) continue;
      if (!meilleur || RANG_INTERET[r.i] > RANG_INTERET[meilleur.i]
          || (r.i === meilleur.i && RANG_DETAIL[r.d] > RANG_DETAIL[meilleur.d])) meilleur = { ...r, domaine: d };
    }
    return meilleur;
  }

  function libelleCourt(domaine) { return E.courts[domaine] || domaine; }

  // --- rendu d'une fiche --------------------------------------------------------------------------
  function champ(etiq, valeur, classe = '') {
    if (!valeur || (Array.isArray(valeur) && !valeur.length)) return '';
    const contenu = Array.isArray(valeur) ? `<ul>${valeur.map((v) => `<li>${esc(v)}</li>`).join('')}</ul>` : esc(valeur);
    return `<div class="champ ${classe}"><span class="etiq">${esc(etiq)}</span><div>${contenu}</div></div>`;
  }

  function liens(f) {
    const l = [];
    if (f.pmid) l.push(`<a href="https://pubmed.ncbi.nlm.nih.gov/${esc(f.pmid)}/" target="_blank" rel="noopener">PMID ${esc(f.pmid)}</a>`);
    if (f.doi) l.push(`<a href="https://doi.org/${esc(f.doi)}" target="_blank" rel="noopener">DOI</a>`);
    if (f.source === 'has' && urlSure(f.url)) l.push(`<a href="${esc(f.url)}" target="_blank" rel="noopener">Page HAS</a>`);
    return l.join(' · ');
  }

  function ficheHTML(f, semaineId, opts = {}) {
    const detail = opts.detail || 'standard';
    const vulgarise = Boolean(opts.vulgarise && f.vulgarise);
    const estFavori = favoris().some((x) => x.id === f.id);
    const ouvertResultats = RANG_DETAIL[detail] >= 1 ? ' open' : '';
    const ouvertMethode = RANG_DETAIL[detail] >= 2 ? ' open' : '';
    const n = LIB.niveauPreuve[f.etiquette] || 1;
    const c = f.complet || {};
    const s = f.standard || {};
    const meta = [
      f.revue_abrege || f.revue ? `<span class="revue">${esc(f.revue_abrege || f.revue)}</span>` : '',
      f.annee ? `<span>${esc(f.annee)}</span>` : '',
      ...f.domaines.map((d) => `<span class="domaine">${esc(libelleCourt(d))}</span>`),
    ].filter(Boolean).join('');
    const technique = `<p class="flash">${esc(f.flash)}</p>`;
    const simple = vulgarise ? `<p class="flash">${esc(f.vulgarise.flash)}</p>` : '';
    const email = E.config.email_contact;
    const lienSignal = email
      ? `<a class="action" href="mailto:${esc(email)}?subject=${encodeURIComponent(`Erreur fiche ${f.id} (${semaineId})`)}&body=${encodeURIComponent(`Fiche : ${adresseFiche(semaineId, f.id)}\n\nCe qui est inexact :\n`)}">${ICONES.signaler}<span>Signaler</span></a>`
      : '';

    return `<article class="fiche v-${esc(f.verdict)}" id="f-${esc(f.id)}" data-id="${esc(f.id)}" data-semaine="${esc(semaineId)}">
  <div class="fiche-tete">
    <span class="verdict">${esc(LIB.verdict[f.verdict])}</span>
    <span class="type-etude">${esc(LIB.type[f.type] || f.type)}</span>
    <span class="preuve" title="Niveau de preuve estimé à partir du résumé"><span class="jauge n${n}" aria-hidden="true"><i></i><i></i><i></i></span>${esc(LIB.etiquette[f.etiquette])}<span class="visuel-cache"> (niveau de preuve)</span></span>
  </div>
  <h3 class="fiche-titre"><a href="#fiche-${esc(semaineId)}-${esc(f.id)}">${esc(f.titre_fr)}</a></h3>
  ${RANG_DETAIL[detail] >= 2 || opts.autonome ? `<p class="titre-original" lang="en">${esc(f.titre)}</p>` : ''}
  <p class="fiche-meta">${meta}</p>
  ${vulgarise ? `<div class="vers-simple">${simple}</div><div class="vers-technique" hidden>${technique}</div>
  <p class="registre">Version simplifiée · <button class="lien-fiche" data-action="registre">Voir la version technique</button></p>` : technique}
  <details class="depli"${ouvertResultats}><summary>Résultats et impact</summary>
    <div class="depli-corps">
      ${vulgarise && f.vulgarise.standard ? `<div class="vers-simple">${champ('En pratique', f.vulgarise.standard)}</div>` : ''}
      <div class="${vulgarise ? 'vers-technique' : ''}"${vulgarise ? ' hidden' : ''}>${champ('Résultats', s.resultats)}</div>
      ${champ('Impact clinique', s.impact_clinique, 'impact')}
      ${champ('Limites principales', s.limites)}
    </div>
  </details>
  <details class="depli"${ouvertMethode}><summary>Méthode, population, limites</summary>
    <div class="depli-corps">
      ${champ('Type d’étude', c.type)}
      ${champ('Population', c.population)}
      ${champ(f.type === 'etude_diagnostique' ? 'Test évalué et référence' : 'Intervention et comparateur', c.intervention_comparateur)}
      ${champ('Critères de jugement', c.criteres_jugement)}
      ${champ('Méthode', c.methode)}
      ${champ('GRADE rapporté', c.grade)}
      ${champ('Toutes les limites', c.limites)}
      ${champ('Niveau de preuve', `${LIB.etiquette[f.etiquette]} — ${f.justification_etiquette || ''}`)}
      ${champ('Incertitudes signalées', f.incertitudes)}
      ${champ('Référence', referenceTexte(f))}
    </div>
  </details>
  <div class="fiche-pied">
    <span class="ident">${liens(f)}</span>
    <span class="actions">
      <button class="action" data-action="favori" aria-pressed="${estFavori}" title="${estFavori ? 'Retirer des favoris' : 'Ajouter aux favoris'}">${ICONES.favori}<span>Favori</span></button>
      <button class="action" data-action="partager">${ICONES.partager}<span>Partager</span></button>
      <button class="action" data-action="zotero" title="Exporter la référence (RIS, pour Zotero, Mendeley, EndNote)">${ICONES.zotero}<span>Zotero</span></button>
      ${lienSignal}
    </span>
  </div>
  <p class="mention"><b class="acces">${esc(ACCES[f.acces] || ACCES.resume)}.</b> ${opts.autonome ? MENTION_COMPLETE : MENTION} <a href="#apropos">Limites de l’analyse</a></p>
</article>`;
  }

  function referenceTexte(f) {
    const auteurs = f.auteurs || [];
    const a = auteurs.length > 3 ? `${auteurs.slice(0, 3).join(', ')} et al.` : auteurs.join(', ');
    const vol = [f.volume && `${f.volume}`, f.numero && `(${f.numero})`].filter(Boolean).join('');
    return [a, f.titre, [f.revue, f.annee].filter(Boolean).join(', '), vol && `${vol}${f.pages ? `:${f.pages}` : ''}`,
      f.doi && `doi:${f.doi}`].filter(Boolean).join('. ');
  }

  // --- export RIS (Zotero, Mendeley, EndNote) -----------------------------------------------------
  function ris(f) {
    const l = [`TY  - ${f.source === 'has' ? 'RPRT' : 'JOUR'}`, `TI  - ${f.titre}`];
    for (const a of f.auteurs || []) {
      const m = a.match(/^(.*\S)\s+([A-Z]{1,4})$/);
      l.push(`AU  - ${m ? `${m[1]}, ${m[2]}` : a}`);
    }
    if (f.revue) l.push(`T2  - ${f.revue}`);
    if (f.revue_abrege) l.push(`J2  - ${f.revue_abrege}`);
    if (f.annee) l.push(`PY  - ${f.annee}`);
    if (f.volume) l.push(`VL  - ${f.volume}`);
    if (f.numero) l.push(`IS  - ${f.numero}`);
    if (f.pages) {
      const [sp, ep] = f.pages.split('-');
      l.push(`SP  - ${sp}`);
      if (ep) l.push(`EP  - ${ep}`);
    }
    if (f.doi) l.push(`DO  - ${f.doi}`);
    if (f.pmid) l.push(`AN  - PMID:${f.pmid}`);
    if (urlSure(f.url)) l.push(`UR  - ${f.url}`);
    l.push(`N1  - Veille Santé : ${f.titre_fr}`);
    l.push('ER  - ');
    return l.join('\r\n');
  }

  function telecharger(nom, texte) {
    const blob = new Blob([texte], { type: 'application/x-research-info-systems' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = nom;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }

  // --- adresse des vues ---------------------------------------------------------------------------
  function adresseFiche(semaineId, id) {
    const base = location.href.split('#')[0];
    return `${base}#fiche-${semaineId}-${id}`;
  }

  // --- vues ---------------------------------------------------------------------------------------
  function rendre(html, titre) {
    vue.innerHTML = html;
    document.title = titre ? `${titre} · ${E.config.nom_app}` : E.config.nom_app;
  }

  function marquerOnglet(nom) {
    for (const a of document.querySelectorAll('[data-onglet]')) {
      if (a.dataset.onglet === nom) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    }
  }

  // Bienvenue ------------------------------------------------------------------------------------
  function vueBienvenue() {
    marquerOnglet('');
    const profs = E.catalogue.professions.filter((p) => !p.transversal);
    rendre(`<section class="accueil">
  <p class="surtitre">Veille scientifique hebdomadaire</p>
  <h1>Les études qui comptent pour votre pratique, chaque lundi.</h1>
  <p class="chapo">Recommandations, revues systématiques, essais randomisés et études diagnostiques de la semaine, résumés en français et filtrés selon vos domaines.</p>
  <div class="section">
    <h2>Quelle est votre profession ?</h2>
    <div class="choix-profession">
      ${profs.map((p) => `<button data-profession="${esc(p.id)}">${esc(p.nom)}</button>`).join('')}
    </div>
    <p class="rangee"><button class="bouton discret" data-action="profil-vide">Je règle mes domaines moi-même</button></p>
  </div>
  <div class="principes">
    <p class="principe"><b>Sans compte</b>Vos réglages et favoris restent sur cet appareil.</p>
    <p class="principe"><b>Sources vérifiables</b>Chaque fiche renvoie vers PubMed, le DOI ou la HAS.</p>
    <p class="principe"><b>Lecture à votre rythme</b>L’essentiel en une phrase, la méthode à déplier.</p>
  </div>
</section>`, 'Bienvenue');
  }

  function profilDepuisProfession(idProf) {
    const p = { v: 1, domaines: {}, notif: { freq: 'hebdo' }, cree: new Date().toISOString() };
    const prof = E.catalogue.professions.find((x) => x.id === idProf);
    if (prof) for (const sc of prof.sous_champs) p.domaines[`${prof.id}/${sc.id}`] = { i: 'praticien', d: 'standard' };
    p.domaines['transversal/grandes-nouveautes'] = { i: 'culture', d: 'flash' };
    return p;
  }

  // Semaine --------------------------------------------------------------------------------------
  async function vueSemaine(id) {
    marquerOnglet('semaine');
    const p = profil();
    if (!E.index || !E.index.semaines?.length) {
      rendre(`<div class="entete"><p class="surtitre">Veille de la semaine</p><h1>Première veille en préparation</h1></div>
<p class="vide"><strong>Aucune veille publiée pour l’instant.</strong>La première sera en ligne lundi. Réglez vos domaines dans votre profil pour la recevoir filtrée.</p>`, 'Semaine');
      return;
    }
    const semId = id || E.index.derniere;
    const infos = E.index.semaines.find((s) => s.id === semId);
    let s;
    try { s = await chargerSemaine(semId); } catch {
      rendre(`<p class="vide"><strong>Semaine introuvable.</strong>Elle n’est pas disponible, ou vous êtes hors ligne. <a href="#archive">Voir l’archive</a></p>`, 'Semaine');
      return;
    }
    const estDerniere = semId === E.index.derniere;
    const toutes = E.toutesFiches || !p;
    const visibles = [];
    for (const f of s.fiches.filter((x) => !retiree(x.id))) {
      const r = toutes ? { i: 'expert', d: 'standard' } : reglageVisible(f, p);
      if (r) visibles.push({ f, r });
    }
    // Filtres par profession suivie (ou présente, en mode « toutes »).
    const profsPresentes = new Map();
    for (const { f } of visibles) {
      for (const idp of new Set(f.domaines.map((d) => d.split('/')[0]))) {
        if (!toutes && !Object.keys(p.domaines).some((k) => k.startsWith(`${idp}/`))) continue;
        profsPresentes.set(idp, (profsPresentes.get(idp) || 0) + 1);
      }
    }
    if (E.filtre !== 'tout' && !profsPresentes.has(E.filtre)) E.filtre = 'tout';
    const filtrees = E.filtre === 'tout' ? visibles : visibles.filter(({ f }) => f.domaines.some((d) => d.startsWith(`${E.filtre}/`)));
    const nomProf = (idp) => E.catalogue.professions.find((x) => x.id === idp)?.court || idp;

    const groupes = ORDRE_VERDICTS.map((v) => ({ v, items: filtrees.filter(({ f }) => f.verdict === v) })).filter((g) => g.items.length);
    const total = s.stats?.candidates;

    rendre(`<div class="entete">
  <p class="surtitre">${estDerniere ? 'Veille de la semaine' : 'Archive'} · ${esc(semId)}</p>
  <h1>Semaine ${numeroSemaine(semId)}</h1>
  <p class="chapo">${esc(periode(infos || s))} · ${toutes ? pluriel(visibles.length, 'fiche', 'fiches') : `${pluriel(visibles.length, 'étude', 'études')} pour vous`}${total ? ` sur ${total} publications examinées` : ''}</p>
</div>
${E.config.demonstration ? `<div class="bandeau"><p><b>Démonstration.</b> Ces fiches ont été rédigées à partir de quatre publications réelles de 2026, regroupées ici pour montrer le format : la vraie veille ne contiendra que les publications de la semaine. Vérifiez les chiffres via les liens avant tout usage.</p></div>` : ''}
${!p ? `<div class="bandeau"><p>Vous voyez toute la veille. Choisissez vos domaines pour ne garder que ce qui vous concerne.</p><a class="bouton principal" href="#bienvenue">Choisir mes domaines</a></div>` : ''}
${p && !toutes ? syntheseHTML(s, p, new Set(visibles.map(({ f }) => f.id))) : ''}
<div class="section">
  <div class="section-tete">
    <h2>${toutes ? 'Toutes les fiches' : 'Vos fiches'}</h2>
    ${p ? `<button class="bouton discret" data-action="basculer-toutes">${toutes ? 'Revenir à mon profil' : 'Voir toutes les fiches'}</button>` : ''}
  </div>
  ${profsPresentes.size > 1 ? `<div class="filtres" role="group" aria-label="Filtrer par profession">
    <button class="filtre" data-filtre="tout" aria-pressed="${E.filtre === 'tout'}">Tout · ${visibles.length}</button>
    ${[...profsPresentes].map(([idp, nb]) => `<button class="filtre" data-filtre="${esc(idp)}" aria-pressed="${E.filtre === idp}">${esc(nomProf(idp))} · ${nb}</button>`).join('')}
  </div>` : ''}
  ${groupes.length ? groupes.map((g) => `<section class="groupe v-${g.v}">
    <h2><span class="pastille" aria-hidden="true"></span>${esc(LIB.verdictGroupe[g.v])} <span class="compte">${g.items.length}</span></h2>
    <div class="liste-fiches">${g.items.map(({ f, r }) => ficheHTML(f, semId, { detail: r.d, vulgarise: r.i === 'culture' })).join('')}</div>
  </section>`).join('') : `<p class="vide"><strong>Aucune étude retenue pour vos domaines cette semaine.</strong>Aucune mise à jour cliniquement pertinente cette semaine. Vous pouvez <button class="lien-fiche" data-action="basculer-toutes">voir toutes les fiches</button> ou élargir vos domaines dans votre profil.</p>`}
</div>`, `Semaine ${numeroSemaine(semId)}`);
  }

  function syntheseHTML(s, p, idsVisibles) {
    const suivis = Object.keys(p.domaines);
    const blocs = [];
    const sansNouveaute = [];
    for (const d of suivis) {
      const syn = s.syntheses?.[d];
      if (!syn) continue;
      const filtrer = (liste) => (liste || []).filter((x) => idsVisibles.has(x.id));
      const change = filtrer(syn.ce_qui_change_la_pratique);
      const remet = filtrer(syn.remis_en_question);
      const surveiller = filtrer(syn.a_surveiller);
      if (!change.length && !remet.length && !surveiller.length) { sansNouveaute.push(libelleCourt(d)); continue; }
      const liste = (items) => `<ul>${items.map((x) => `<li><button class="lien-fiche" data-aller="${esc(x.id)}">${esc(x.phrase)}</button></li>`).join('')}</ul>`;
      blocs.push({ d, n: change.length + remet.length + surveiller.length, html: `
        ${change.length ? `<div class="bloc-synthese change"><h3>Ce qui change la pratique</h3>${liste(change)}</div>` : ''}
        ${remet.length ? `<div class="bloc-synthese remet"><h3>Remis en question</h3>${liste(remet)}</div>` : ''}
        ${surveiller.length ? `<div class="bloc-synthese surveiller"><h3>À surveiller</h3>${liste(surveiller)}</div>` : ''}` });
    }
    if (!blocs.length && !sansNouveaute.length) return '';
    blocs.sort((a, b) => b.n - a.n);
    return `<div class="section">
  <div class="section-tete"><h2>En bref</h2><span class="compte">${pluriel(blocs.length, 'domaine', 'domaines')}</span></div>
  <div class="syntheses">
    ${blocs.map((b, i) => `<details class="synthese"${i === 0 ? ' open' : ''}><summary>${esc(E.libelles[b.d] || b.d)}<span class="compte">${b.n}</span></summary><div class="synthese-corps">${b.html}</div></details>`).join('')}
    ${sansNouveaute.length ? `<p class="sans-nouveaute">Aucune mise à jour cliniquement pertinente cette semaine : ${esc(sansNouveaute.join(', '))}.</p>` : ''}
  </div>
</div>`;
  }

  // Fiche seule (lien partagé) ---------------------------------------------------------------------
  async function vueFiche(semId, id) {
    marquerOnglet('');
    let s;
    try { s = await chargerSemaine(semId); } catch { s = null; }
    const f = retiree(id) ? null : (s?.fiches.find((x) => x.id === id) || favoris().find((x) => x.id === id));
    if (!f) {
      rendre(`<p class="vide"><strong>Fiche introuvable.</strong>Le lien est peut-être incomplet, ou vous êtes hors ligne. <a href="#semaine">Voir la veille de la semaine</a></p>`, 'Fiche');
      return;
    }
    rendre(`<div class="entete"><p class="surtitre">Fiche · Semaine ${numeroSemaine(semId)} · ${esc(semId)}</p></div>
${ficheHTML(f, semId, { detail: 'complet', autonome: true })}
<p class="rangee"><a class="bouton" href="#semaine-${esc(semId)}">Ouvrir la veille de cette semaine</a></p>`, f.titre_fr);
  }

  // Archive --------------------------------------------------------------------------------------
  function vueArchive() {
    marquerOnglet('archive');
    const semaines = E.index?.semaines || [];
    const annees = E.index?.annees_recherche || [];
    const profs = E.catalogue.professions;
    const opt = (obj) => Object.entries(obj).map(([k, v]) => `<option value="${esc(k)}">${esc(v)}</option>`).join('');
    const memo = stock.lire('vs.recherche', {});
    rendre(`<div class="entete"><p class="surtitre">Archive</p><h1>Toutes les veilles</h1>
  <p class="chapo">Recherchez dans les titres des fiches de toutes les semaines publiées.</p></div>
<form class="recherche" id="form-recherche" role="search">
  <div class="recherche-champ">
    <label class="visuel-cache" for="q">Mots-clés</label>
    <input id="q" type="search" placeholder="Ex. lombalgie, AVC, gonarthrose" value="${esc(memo.q || '')}" autocomplete="off">
    <button class="bouton principal" type="submit">Rechercher</button>
  </div>
  <div class="recherche-filtres">
    <label for="f-prof">Profession<select id="f-prof"><option value="">Toutes</option>${profs.map((p) => `<option value="${esc(p.id)}">${esc(p.nom)}</option>`).join('')}</select></label>
    <label for="f-type">Type<select id="f-type"><option value="">Tous</option>${opt(LIB.type)}</select></label>
    <label for="f-etiq">Preuve<select id="f-etiq"><option value="">Toutes</option>${opt(LIB.etiquette)}</select></label>
    <label for="f-verdict">Verdict<select id="f-verdict"><option value="">Tous</option>${opt(LIB.verdict)}</select></label>
    <label for="f-annee">Année<select id="f-annee"><option value="">Toutes</option>${annees.map((a) => `<option value="${a}">${a}</option>`).join('')}</select></label>
  </div>
</form>
<div id="resultats" class="section" hidden></div>
<div class="section">
  <div class="section-tete"><h2>Semaines publiées</h2><span class="compte">${semaines.length}</span></div>
  ${semaines.length ? `<ul class="semaines">${semaines.map((s) => `<li><a href="#semaine-${esc(s.id)}"><span class="num">S${numeroSemaine(s.id)} · ${esc(s.id.slice(0, 4))}</span><span>${esc(periode(s))}</span><span class="nb">${pluriel(s.nb_fiches, 'fiche', 'fiches')}</span></a></li>`).join('')}</ul>`
    : '<p class="vide"><strong>Aucune semaine publiée pour l’instant.</strong>La première veille sera en ligne lundi.</p>'}
</div>`, 'Archive');
    for (const [cle, id] of [['prof', 'f-prof'], ['type', 'f-type'], ['etiq', 'f-etiq'], ['verdict', 'f-verdict'], ['annee', 'f-annee']]) {
      if (memo[cle]) document.getElementById(id).value = memo[cle];
    }
    document.getElementById('form-recherche').addEventListener('submit', (e) => { e.preventDefault(); lancerRecherche(); });
    for (const sel of document.querySelectorAll('.recherche select')) sel.addEventListener('change', lancerRecherche);
    if (memo.q || memo.prof || memo.type || memo.etiq || memo.verdict) lancerRecherche();
  }

  async function lancerRecherche(limite = 60) {
    const val = (id) => document.getElementById(id)?.value || '';
    const crit = { q: val('q').trim(), prof: val('f-prof'), type: val('f-type'), etiq: val('f-etiq'), verdict: val('f-verdict'), annee: val('f-annee') };
    stock.ecrire('vs.recherche', crit);
    const zone = document.getElementById('resultats');
    if (!crit.q && !crit.prof && !crit.type && !crit.etiq && !crit.verdict) { zone.hidden = true; return; }
    zone.hidden = false;
    zone.innerHTML = '<p class="chargement">Recherche…</p>';
    const annees = crit.annee ? [Number(crit.annee)] : (E.index?.annees_recherche || []);
    const lots = await Promise.all(annees.map(chargerRecherche));
    const mots = sansAccents(crit.q).split(/\s+/).filter(Boolean);
    const trouves = lots.flat().filter((e) => {
      if (retiree(e.i)) return false;
      if (crit.prof && !e.d.some((d) => d.startsWith(`${crit.prof}/`))) return false;
      if (crit.type && e.y !== crit.type) return false;
      if (crit.etiq && e.e !== crit.etiq) return false;
      if (crit.verdict && e.v !== crit.verdict) return false;
      if (!mots.length) return true;
      const texte = sansAccents(`${e.t} ${e.o} ${e.r}`);
      return mots.every((m) => texte.includes(m));
    }).sort((a, b) => (a.s < b.s ? 1 : a.s > b.s ? -1 : ORDRE_VERDICTS.indexOf(a.v) - ORDRE_VERDICTS.indexOf(b.v)));
    zone.innerHTML = `<div class="section-tete"><h2>Résultats</h2><span class="compte">${trouves.length}</span></div>
${trouves.length ? `<div class="resultats">${trouves.slice(0, limite).map((e) => `<a class="resultat v-${esc(e.v)}" href="#fiche-${esc(e.s)}-${esc(e.i)}">
  <span class="resultat-titre">${esc(e.t)}</span>
  <span class="resultat-meta"><span class="puce-v">${esc(LIB.verdict[e.v])}</span><span>${esc(LIB.type[e.y])}</span><span>${esc(LIB.etiquette[e.e])}</span><span>S${numeroSemaine(e.s)} · ${esc(e.s.slice(0, 4))}</span>${e.r ? `<span class="revue">${esc(e.r)}</span>` : ''}</span>
</a>`).join('')}</div>${trouves.length > limite ? `<p><button class="bouton" data-action="plus" data-limite="${limite + 60}">Afficher plus de résultats</button></p>` : ''}`
    : '<p class="vide"><strong>Aucune fiche ne correspond.</strong>Essayez un autre mot-clé ou retirez un filtre.</p>'}`;
  }

  // Favoris --------------------------------------------------------------------------------------
  function vueFavoris() {
    marquerOnglet('favoris');
    const liste = favoris();
    rendre(`<div class="entete"><p class="surtitre">Favoris</p><h1>Études mises de côté</h1>
  <p class="chapo">Enregistrées sur cet appareil et lisibles hors ligne.</p></div>
${liste.length ? `<div class="rangee"><button class="bouton" data-action="zotero-tout">Exporter tous les favoris (RIS)</button><button class="bouton discret" data-action="copier-ris">Copier les références RIS</button></div>
<div class="liste-fiches">${liste.map((f) => ficheHTML(f, f._semaine, { detail: 'standard' })).join('')}</div>`
    : '<p class="vide"><strong>Aucun favori pour l’instant.</strong>Touchez « Favori » sous une fiche pour la retrouver ici, même sans connexion.</p>'}`, 'Favoris');
  }

  // Profil ---------------------------------------------------------------------------------------
  function vueProfil() {
    marquerOnglet('profil');
    const p = profil() || { v: 1, domaines: {}, notif: { freq: 'hebdo' } };
    const optInteret = (sel) => `<option value="">Non suivi</option>${Object.entries(LIB.interet).map(([k, v]) => `<option value="${k}"${sel === k ? ' selected' : ''}>${v}</option>`).join('')}`;
    const optDetail = (sel) => Object.entries(LIB.detail).map(([k, v]) => `<option value="${k}"${sel === k ? ' selected' : ''}>${v}</option>`).join('');
    const notifPossible = Boolean(E.config.onesignal_app_id);
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const autonome = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;

    const professions = E.catalogue.professions.map((prof) => {
      const suivis = prof.sous_champs.filter((sc) => p.domaines[`${prof.id}/${sc.id}`]).length;
      const lignes = prof.sous_champs.map((sc) => {
        const d = `${prof.id}/${sc.id}`;
        const r = p.domaines[d] || {};
        return `<div class="reglage"><span class="reglage-nom" id="n-${esc(d)}">${esc(sc.nom)}</span>
  <span class="reglage-choix">
    <select data-domaine="${esc(d)}" data-champ="i" aria-labelledby="n-${esc(d)}" aria-label="Niveau d’intérêt">${optInteret(r.i)}</select>
    <select data-domaine="${esc(d)}" data-champ="d" aria-label="Niveau de détail"${r.i ? '' : ' disabled'}>${optDetail(r.d || 'standard')}</select>
  </span></div>`;
      }).join('');
      const tous = prof.sous_champs.length > 1 ? `<div class="reglage tous"><span class="reglage-nom">Toute la profession</span>
  <span class="reglage-choix">
    <select data-profession="${esc(prof.id)}" data-champ="i" aria-label="Niveau d’intérêt pour toute la profession"><option value="-">Choisir…</option>${optInteret('-')}</select>
    <select data-profession="${esc(prof.id)}" data-champ="d" aria-label="Niveau de détail pour toute la profession"><option value="-">Choisir…</option>${optDetail('-')}</select>
  </span></div>` : '';
      return `<details class="profession" data-prof="${esc(prof.id)}"${suivis ? ' open' : ''}><summary><strong>${esc(prof.nom)}</strong><span class="compte">${suivis}/${prof.sous_champs.length}</span></summary>
  <div class="profession-corps">${tous}${lignes}</div></details>`;
    }).join('');

    rendre(`<div class="entete"><p class="surtitre">Profil</p><h1>Vos domaines</h1>
  <p class="chapo">Pour chaque domaine, choisissez votre niveau d’intérêt et le détail affiché par défaut. Tout reste dépliable.</p></div>
<div class="carte legende">
  <span><b>Expert</b> : toutes les études retenues, en langage technique.</span>
  <span><b>Praticien concerné</b> : les études à impact moyen ou fort.</span>
  <span><b>Culture générale</b> : seulement les études à fort impact, en version simplifiée.</span>
  <span><b>Flash</b> : une ou deux phrases · <b>Standard</b> : résultats, impact et limites ouverts · <b>Complet</b> : méthode et population ouvertes aussi.</span>
</div>
<div class="section" id="reglages">${professions}</div>
<div class="carte" id="carte-notif">
  <h2>Notifications</h2>
  <p>Un message le lundi, uniquement pour les professions que vous suivez.</p>
  <label for="freq" class="rangee"><span>Fréquence</span>
    <select id="freq">${Object.entries(LIB.freq).map(([k, v]) => `<option value="${k}"${(p.notif?.freq || 'hebdo') === k ? ' selected' : ''}>${v}</option>`).join('')}</select></label>
  ${notifPossible
    ? (ios && !autonome
      ? '<p>Sur iPhone et iPad, ajoutez d’abord l’app à l’écran d’accueil (bouton Partager, puis « Sur l’écran d’accueil »), puis ouvrez-la depuis l’icône.</p>'
      : `<div class="rangee"><button class="bouton principal" data-action="activer-notif">${p.notif?.abonne ? 'Notifications activées' : 'Activer sur cet appareil'}</button></div>`)
    : '<p>Les notifications ne sont pas encore disponibles sur ce site.</p>'}
</div>
<div class="carte" id="carte-installer" ${E.installation ? '' : 'hidden'}>
  <h2>Installer l’app</h2>
  <p>Ajoute Veille Santé à votre écran d’accueil, comme une application.</p>
  <div class="rangee"><button class="bouton" data-action="installer">Installer</button></div>
</div>
<div class="carte">
  <h2>Changer d’appareil</h2>
  <p>Sans compte, votre profil et vos favoris restent ici. Copiez ce code et collez-le sur l’autre appareil.</p>
  <div class="rangee"><button class="bouton" data-action="exporter-profil">Copier mon code</button></div>
  <label for="code-import" class="visuel-cache">Code de profil à importer</label>
  <textarea id="code-import" placeholder="Collez ici un code venant d’un autre appareil"></textarea>
  <div class="rangee"><button class="bouton" data-action="importer-profil">Importer ce code</button></div>
</div>
<div class="carte">
  <h2>Réinitialiser</h2>
  <p>Efface vos domaines et vos favoris sur cet appareil.</p>
  <div class="rangee" id="zone-reinit"><button class="bouton danger" data-action="reinit">Tout effacer</button></div>
</div>`, 'Profil');

    vue.querySelector('#reglages').addEventListener('change', (e) => {
      const sel = e.target;
      const p2 = profil() || { v: 1, domaines: {}, notif: { freq: 'hebdo' } };
      if (sel.dataset.domaine) {
        const d = sel.dataset.domaine;
        if (sel.dataset.champ === 'i') {
          if (!sel.value) delete p2.domaines[d];
          else p2.domaines[d] = { i: sel.value, d: p2.domaines[d]?.d || 'standard' };
          const det = vue.querySelector(`select[data-domaine="${CSS.escape(d)}"][data-champ="d"]`);
          det.disabled = !sel.value;
        } else if (p2.domaines[d]) {
          p2.domaines[d].d = sel.value;
        }
      } else if (sel.dataset.profession && sel.value !== '-') {
        const prof = E.catalogue.professions.find((x) => x.id === sel.dataset.profession);
        for (const sc of prof.sous_champs) {
          const d = `${prof.id}/${sc.id}`;
          if (sel.dataset.champ === 'i') {
            if (!sel.value) delete p2.domaines[d];
            else p2.domaines[d] = { i: sel.value, d: p2.domaines[d]?.d || 'standard' };
          } else if (p2.domaines[d]) {
            p2.domaines[d].d = sel.value;
          }
        }
        enregistrerProfil(p2);
        vueProfil();
        vue.querySelector(`details[data-prof="${CSS.escape(prof.id)}"]`).open = true;
        toast('Réglage appliqué à toute la profession');
        return;
      }
      enregistrerProfil(p2);
      const det = sel.closest('details.profession');
      const prof = E.catalogue.professions.find((x) => x.id === det.dataset.prof);
      det.querySelector('summary .compte').textContent = `${prof.sous_champs.filter((sc) => p2.domaines[`${prof.id}/${sc.id}`]).length}/${prof.sous_champs.length}`;
      toast('Profil enregistré');
    });
    vue.querySelector('#freq').addEventListener('change', (e) => {
      const p2 = profil() || { v: 1, domaines: {}, notif: {} };
      p2.notif = { ...(p2.notif || {}), freq: e.target.value };
      enregistrerProfil(p2);
      toast('Fréquence enregistrée');
    });
  }

  // À propos -------------------------------------------------------------------------------------
  function vueAPropos() {
    marquerOnglet('');
    const c = E.config;
    rendre(`<div class="entete"><p class="surtitre">À propos</p><h1>Comment la veille est produite</h1></div>
<div class="texte">
  <p>Chaque lundi, un programme automatique rassemble les publications de la semaine précédente, les fait trier et résumer par une intelligence artificielle, contrôle les résultats, puis publie les fiches. Aucune relecture humaine n’a lieu avant publication.</p>
  <h2>Ce que vous devez savoir sur l’IA</h2>
  <p>${MENTION_COMPLETE}</p>
  <ul>
    <li>L’analyse est entièrement automatisée : aucune fiche n’est relue par un humain avant sa publication.</li>
    <li>Aujourd’hui, toutes les fiches reposent sur le titre et le résumé de l’article. Le texte intégral n’est pas lu, et chaque fiche l’indique.</li>
    <li>Une donnée peut être mal extraite ou mal interprétée. Les contrôles automatiques réduisent ce risque sans le supprimer.</li>
    <li>Une fiche ne remplace pas la lecture de la publication originale et ne constitue pas, à elle seule, une recommandation clinique.</li>
  </ul>
  <h2>Sources</h2>
  <ul>
    <li>PubMed : recommandations, revues systématiques, méta-analyses, essais randomisés et études diagnostiques avec résumé, en anglais ou en français, entrés dans PubMed du lundi au dimanche.</li>
    <li>Haute Autorité de santé : recommandations et guides mis en ligne dans la semaine.</li>
    <li>Crossref : vérification des DOI et des rétractations.</li>
  </ul>
  <h2>Ce que l’IA a le droit de faire</h2>
  <ul>
    <li>Elle ne cherche aucune source elle-même : elle ne lit que les références récupérées.</li>
    <li>Elle travaille à partir du titre et du résumé, jamais du texte intégral.</li>
    <li>Chaque chiffre d’une fiche doit figurer dans le résumé source, sinon la fiche est écartée.</li>
    <li>Elle peut abaisser le niveau de preuve fixé par les règles ci-dessous si le résumé montre un défaut, jamais le remonter. Une information absente du résumé ne suffit pas à l’abaisser.</li>
  </ul>
</div>
<div class="section"><h2>Niveau de preuve de départ</h2>
<div class="tableau"><table>
  <thead><tr><th>Type d’étude</th><th>Solide</th><th>Modéré</th><th>Préliminaire</th></tr></thead>
  <tbody>
    <tr><td>Recommandation</td><td>Fondée sur des preuves gradées</td><td>Accord d’experts</td><td>—</td></tr>
    <tr><td>Revue systématique ou méta-analyse</td><td>GRADE élevé ou modéré rapporté</td><td>GRADE faible, ou essais randomisés majoritaires</td><td>GRADE très faible, ou études non randomisées majoritaires</td></tr>
    <tr><td>Essai randomisé</td><td>Jamais pour un essai isolé</td><td>Au moins 100 participants</td><td>De 30 à 99 participants, ou biais majeur</td></tr>
    <tr><td>Étude diagnostique</td><td>—</td><td>Cohorte prospective avec référence standard</td><td>Rétrospective ou cas-témoins</td></tr>
  </tbody>
</table></div></div>
<div class="texte">
  <h2>Verdicts</h2>
  <ul>
    <li><b>Change la pratique</b> : réservé aux recommandations et aux revues ou méta-analyses de niveau solide.</li>
    <li><b>Remet en question</b> : contredit une pratique courante, ou ne retrouve pas le bénéfice attendu d’une intervention couramment utilisée.</li>
    <li><b>Confirme</b> : va dans le sens d’une pratique déjà courante ou déjà recommandée.</li>
    <li><b>À surveiller</b> : pratique pas encore courante, ou résultat trop incertain pour conforter ou contredire une pratique.</li>
  </ul>
  <h2>Limites</h2>
  <ul>
    <li>Les bases sous abonnement (Embase, Scopus, CINAHL…) ne sont pas couvertes.</li>
    <li>Un résumé peut présenter les résultats sous un jour plus favorable que l’article.</li>
    <li>Le niveau de preuve est une estimation faite à partir du résumé.</li>
    <li>Une erreur d’interprétation peut passer jusqu’à son signalement.</li>
  </ul>
  <p><b>Avertissement.</b> Ce service s’adresse aux professionnels de santé. Les fiches ne remplacent ni la lecture de l’article ni le jugement clinique.</p>
  ${c.email_contact ? `<p>Une erreur dans une fiche ? Utilisez le bouton « Signaler » sous la fiche, ou écrivez à <b>${esc(c.email_contact)}</b>.</p>` : ''}
  <h2>Confidentialité</h2>
  <p>L’app ne demande aucun compte et ne dépose aucun traceur publicitaire. Vos domaines et favoris sont stockés uniquement sur votre appareil. Si vous activez les notifications, votre navigateur s’abonne auprès du service OneSignal, qui reçoit la liste des professions suivies pour cibler les messages.</p>
  <h2>Mentions légales</h2>
  <p>Éditeur : ${esc(c.editeur || 'à compléter')}. Hébergement : ${esc(c.hebergeur || 'GitHub Pages, GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis')}.</p>
</div>`, 'À propos');
  }

  // --- actions ------------------------------------------------------------------------------------
  function ficheDepuisElement(el) {
    const art = el.closest('.fiche');
    if (!art) return null;
    const { id, semaine } = art.dataset;
    const s = E.semaines.get(semaine);
    return { art, semaine, f: s?.fiches.find((x) => x.id === id) || favoris().find((x) => x.id === id) };
  }

  document.addEventListener('click', async (e) => {
    const cible = e.target.closest('[data-action], [data-profession], [data-filtre], [data-aller]');
    if (!cible) return;

    if (cible.dataset.aller) {
      const art = document.getElementById(`f-${cible.dataset.aller}`);
      if (art) {
        art.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
        art.classList.add('eclaire');
        setTimeout(() => art.classList.remove('eclaire'), 1800);
      }
      return;
    }
    if (cible.dataset.filtre) { E.filtre = cible.dataset.filtre; route(); return; }
    if (cible.matches('button[data-profession]') && !cible.closest('#reglages')) {
      enregistrerProfil(profilDepuisProfession(cible.dataset.profession));
      location.hash = '#semaine';
      toast('Profil créé. Affinez vos domaines dans Profil.');
      return;
    }

    const action = cible.dataset.action;
    const ctx = ficheDepuisElement(cible);
    switch (action) {
      case 'profil-vide':
        enregistrerProfil({ v: 1, domaines: {}, notif: { freq: 'hebdo' } });
        location.hash = '#profil';
        break;
      case 'basculer-toutes':
        E.toutesFiches = !E.toutesFiches; E.filtre = 'tout'; route();
        break;
      case 'registre': {
        const art = cible.closest('.fiche');
        const simple = art.querySelector('.vers-simple:not([hidden])');
        for (const el of art.querySelectorAll('.vers-simple, .vers-technique')) el.hidden = !el.hidden;
        cible.textContent = simple ? 'Voir la version simplifiée' : 'Voir la version technique';
        cible.parentElement.firstChild.textContent = simple ? 'Version technique · ' : 'Version simplifiée · ';
        break;
      }
      case 'favori': {
        if (!ctx?.f) return;
        let liste = favoris();
        const deja = liste.some((x) => x.id === ctx.f.id);
        liste = deja ? liste.filter((x) => x.id !== ctx.f.id) : [{ ...ctx.f, _semaine: ctx.semaine }, ...liste];
        enregistrerFavoris(liste);
        cible.setAttribute('aria-pressed', String(!deja));
        cible.title = deja ? 'Ajouter aux favoris' : 'Retirer des favoris';
        toast(deja ? 'Retiré des favoris' : 'Ajouté aux favoris');
        if (deja && location.hash === '#favoris') vueFavoris();
        break;
      }
      case 'partager': {
        if (!ctx?.f) return;
        const url = adresseFiche(ctx.semaine, ctx.f.id);
        if (navigator.share) {
          try { await navigator.share({ title: ctx.f.titre_fr, text: ctx.f.flash, url }); return; } catch (err) { if (err?.name === 'AbortError') return; }
        }
        toast(await copier(url) ? 'Lien de la fiche copié' : url);
        break;
      }
      case 'zotero':
        if (!ctx?.f) return;
        telecharger(`${ctx.f.id}.ris`, ris(ctx.f));
        toast('Référence exportée au format RIS');
        break;
      case 'zotero-tout':
        telecharger('veille-sante-favoris.ris', favoris().map(ris).join('\r\n\r\n'));
        toast(`${pluriel(favoris().length, 'référence exportée', 'références exportées')}`);
        break;
      case 'copier-ris':
        toast(await copier(favoris().map(ris).join('\r\n\r\n')) ? 'Références RIS copiées' : 'Copie impossible sur ce navigateur');
        break;
      case 'plus':
        lancerRecherche(Number(cible.dataset.limite));
        break;
      case 'exporter-profil': {
        const code = btoa(unescape(encodeURIComponent(JSON.stringify({ profil: profil(), favoris: favoris().map((f) => ({ id: f.id, s: f._semaine })) }))));
        const zone = document.getElementById('code-import');
        if (await copier(code)) toast('Code copié. Collez-le sur l’autre appareil.');
        else { zone.value = code; zone.select(); toast('Copiez le code affiché'); }
        break;
      }
      case 'importer-profil': {
        try {
          const donnees = JSON.parse(decodeURIComponent(escape(atob(document.getElementById('code-import').value.trim()))));
          if (!donnees.profil?.domaines) throw new Error('code');
          enregistrerProfil(donnees.profil);
          const recuperes = [];
          for (const { id, s } of donnees.favoris || []) {
            try { const sem = await chargerSemaine(s); const f = sem.fiches.find((x) => x.id === id); if (f) recuperes.push({ ...f, _semaine: s }); } catch { /* semaine indisponible */ }
          }
          if (recuperes.length) enregistrerFavoris(recuperes);
          toast('Profil importé');
          vueProfil();
        } catch { toast('Ce code n’est pas valide. Copiez-le à nouveau depuis l’autre appareil.'); }
        break;
      }
      case 'reinit':
        document.getElementById('zone-reinit').innerHTML = '<span>Effacer domaines et favoris ?</span><button class="bouton danger" data-action="reinit-ok">Oui, tout effacer</button><button class="bouton discret" data-action="reinit-non">Annuler</button>';
        break;
      case 'reinit-ok':
        stock.effacer('vs.profil'); stock.effacer('vs.favoris'); stock.effacer('vs.recherche');
        location.hash = '#bienvenue';
        break;
      case 'reinit-non':
        vueProfil();
        break;
      case 'installer':
        if (E.installation) { E.installation.prompt(); E.installation = null; }
        break;
      case 'activer-notif':
        activerNotifications(cible);
        break;
      default:
    }
  });

  // --- notifications (OneSignal, chargé seulement si l'utilisateur les active) --------------------
  function cheminBase() { return location.pathname.replace(/[^/]*$/, ''); }

  function chargerOneSignal() {
    if (chargerOneSignal.promesse) return chargerOneSignal.promesse;
    chargerOneSignal.promesse = new Promise((resoudre, rejeter) => {
      window.OneSignalDeferred = window.OneSignalDeferred || [];
      const sc = document.createElement('script');
      sc.src = 'https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js';
      sc.defer = true;
      sc.onerror = () => rejeter(new Error('OneSignal indisponible'));
      document.head.append(sc);
      window.OneSignalDeferred.push(async (OneSignal) => {
        try {
          const base = cheminBase();
          await OneSignal.init({
            appId: E.config.onesignal_app_id,
            serviceWorkerPath: `${base.slice(1)}push/onesignal/OneSignalSDKWorker.js`,
            serviceWorkerParam: { scope: `${base}push/onesignal/` },
          });
          resoudre(OneSignal);
        } catch (err) { rejeter(err); }
      });
    });
    return chargerOneSignal.promesse;
  }

  function etiquettesNotif(p) {
    const tags = {};
    for (const prof of E.catalogue.professions) {
      tags[`prof_${prof.id}`] = Object.keys(p.domaines).some((d) => d.startsWith(`${prof.id}/`)) ? '1' : '';
    }
    tags.freq = p.notif?.freq === 'aucune' ? '' : (p.notif?.freq || 'hebdo');
    return tags;
  }

  async function activerNotifications(bouton) {
    const p = profil();
    if (!p) { toast('Choisissez d’abord vos domaines'); return; }
    bouton.disabled = true;
    try {
      const OneSignal = await chargerOneSignal();
      await OneSignal.Notifications.requestPermission();
      if (!OneSignal.Notifications.permission) { toast('Notifications refusées dans les réglages du navigateur'); bouton.disabled = false; return; }
      const tags = etiquettesNotif(p);
      await OneSignal.User.addTags(Object.fromEntries(Object.entries(tags).filter(([, v]) => v)));
      const aRetirer = Object.entries(tags).filter(([, v]) => !v).map(([k]) => k);
      if (aRetirer.length) await OneSignal.User.removeTags(aRetirer);
      p.notif = { ...(p.notif || {}), abonne: true };
      stock.ecrire('vs.profil', p);
      bouton.textContent = 'Notifications activées';
      toast('Notifications activées sur cet appareil');
    } catch {
      toast('Activation impossible pour le moment. Réessayez plus tard.');
    }
    bouton.disabled = false;
  }

  async function synchroniserNotifications() {
    const p = profil();
    if (!p?.notif?.abonne || !E.config.onesignal_app_id) return;
    try {
      const OneSignal = await chargerOneSignal();
      const tags = etiquettesNotif(p);
      await OneSignal.User.addTags(Object.fromEntries(Object.entries(tags).filter(([, v]) => v)));
      const aRetirer = Object.entries(tags).filter(([, v]) => !v).map(([k]) => k);
      if (aRetirer.length) await OneSignal.User.removeTags(aRetirer);
    } catch { /* nouvel essai à la prochaine modification */ }
  }

  // --- routage (#semaine, #semaine-2026-S44, #fiche-2026-S44-pm123, #archive…) ---------------------
  async function route() {
    const h = decodeURIComponent(location.hash.slice(1));
    const p = profil();
    let m;
    if ((m = h.match(/^fiche-(\d{4}-S\d{2})-([A-Za-z0-9]+)$/))) return vueFiche(m[1], m[2]);
    if ((m = h.match(/^semaine-(\d{4}-S\d{2})$/))) return vueSemaine(m[1]);
    if (h === 'archive') return vueArchive();
    if (h === 'favoris') return vueFavoris();
    if (h === 'profil') return vueProfil();
    if (h === 'apropos') return vueAPropos();
    if (h === 'bienvenue' || (!p && h !== 'semaine')) return vueBienvenue();
    return vueSemaine();
  }

  window.addEventListener('hashchange', () => {
    if (!/^#semaine/.test(location.hash)) E.toutesFiches = false;
    route().then(() => { window.scrollTo(0, 0); vue.focus({ preventScroll: true }); });
  });
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    E.installation = e;
    const carte = document.getElementById('carte-installer');
    if (carte) carte.hidden = false;
  });

  // --- démarrage ----------------------------------------------------------------------------------
  async function demarrer() {
    const [config, catalogue, index] = await Promise.all([
      json('data/config.json').catch(() => null),
      json('data/catalogue.json'),
      json('data/index.json').catch(() => ({ semaines: [] })),
    ]);
    if (config) Object.assign(E.config, config);
    E.catalogue = catalogue;
    E.index = index;
    for (const prof of catalogue.professions) {
      for (const sc of prof.sous_champs) {
        const d = `${prof.id}/${sc.id}`;
        E.libelles[d] = prof.transversal ? sc.nom : `${prof.court} · ${sc.nom}`;
        E.courts[d] = prof.transversal ? sc.nom : `${prof.court} · ${sc.nom}`;
      }
    }
    const pied = document.createElement('p');
    pied.className = 'mention';
    pied.style.cssText = 'max-width:calc(var(--largeur) + 2rem);margin:0 auto 1.5rem;padding:0 max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px))';
    pied.innerHTML = `<a href="#apropos">À propos, sources et limites</a> · Version ${VERSION_APP}`;
    vue.after(pied);
    await route();
    if ('serviceWorker' in navigator && location.protocol === 'https:') {
      navigator.serviceWorker.register('sw.js').catch(() => { /* lecture hors ligne indisponible */ });
    }
  }

  demarrer().catch(() => {
    vue.innerHTML = '<p class="vide"><strong>La veille n’a pas pu être chargée.</strong>Vérifiez votre connexion puis rechargez la page.</p>';
  });
})();
