import '@fontsource-variable/manrope';
import '@fontsource/ibm-plex-mono/400.css';
import './styles.css';
import { WeaponThumbnails, WeaponViewer } from './viewer.js';

const paths = {
  grid: '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="3" y="15" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/>',
  primary: '<path d="m3 9 3-3h12v4h3v3h-9l-2 6H7l1-6H3zM12 6V3m4 3V3"/>',
  backup: '<path d="M3 6h17v6H10l-2 8H4l2-10H3zM14 6V4m3 8v3h-6"/>',
  melee: '<path d="m18 3 3 3-11 11-3-3zM5 13l6 6m-7 1 4-4m-5 5 1-1"/>',
  special: '<path d="m13 2-9 12h7l-1 8 10-13h-7z"/>',
  sniper: '<circle cx="12" cy="12" r="7"/><path d="M12 1v6m0 10v6M1 12h6m10 0h6"/><circle cx="12" cy="12" r="1"/>',
  premium: '<path d="m12 3 8 5v8l-8 5-8-5V8zM4 8l8 5 8-5m-8 5v8m-5-15 8 5"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  rotate: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 7a7 7 0 0 1 11-2l3 3M4 16l3 3a7 7 0 0 0 11-2"/>',
  reset: '<path d="M3 4v6h6M3 10a9 9 0 1 1 1 8"/>',
  wireframe: '<path d="m12 2 9 5v10l-9 5-9-5V7zM3 7l9 5 9-5m-9 5v10M3 17l9-5 9 5M12 2v10"/>',
  expand: '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>',
  mouse: '<rect x="6" y="2" width="12" height="20" rx="6"/><path d="M12 2v6"/>',
  volume: '<path d="m11 5-6 4H2v6h3l6 4zM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  damage: '<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3z"/>',
  ammo: '<path d="M6 21V8l3-5 3 5v13zM15 21V8l3-5 3 5v13zM6 16h6m3 0h6"/>',
  rate: '<path d="M12 8v5l3 2M9 2h6m-3 0v3m7 1 2-2"/><circle cx="12" cy="13" r="8"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
};
const icon = (name, className = '') => `<svg class="icon ${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.premium}</svg>`;
const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
const asset = (path) => `${import.meta.env.BASE_URL}${path}`;
const categoryNames = { primary: 'Principal', backup: 'Reserva', melee: 'Cuerpo a cuerpo', special: 'Especial', sniper: 'Francotirador', premium: 'Premium' };
const rarityNames = { Common: 'Común', Uncommon: 'Poco común', Rare: 'Rara', Epic: 'Épica', Legendary: 'Legendaria', Mythic: 'Mítica' };
const featured = ['ak-48', 'hellraiser', 'prototype', 'anti-hero-rifle', 'alien-blaster', 'crystal-laser-cannon', 'dragon-breath', 'laser-minigun', 'pixel-gun'];
const pageSize = 12;
const audio = new Audio();
let weapons = [];
let selected = null;
let category = 'all';
let query = '';
let sort = 'featured';
let page = 0;
let viewer;
let thumbnails;
let selectionVersion = 0;
let toastTimeout;

const app = document.querySelector('#app');
app.innerHTML = `
  <a class="skip-link" href="#collection">Ir a la colección</a>
  <div class="sidebar-shade" id="sidebar-shade"></div>
  <aside class="sidebar" id="sidebar" aria-label="Navegación del arsenal">
    <a class="brand" href="${import.meta.env.BASE_URL}" aria-label="Arsenal, inicio">
      <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>
      <span>ARSENAL<span class="brand-subtitle">PIXEL GUN 3D</span></span>
    </a>
    <div class="sidebar-section-label">EXPLORA EL ARCHIVO</div>
    <nav class="category-nav" id="category-nav" aria-label="Categorías de armas"></nav>
    <div class="sidebar-note"><span class="note-cross">+</span><p>Un clásico.<br>Otra perspectiva.</p><span>Las armas que conoces,<br>como nunca las habías visto.</span><div class="pixel-decoration" aria-hidden="true">▦</div></div>
    <div class="sidebar-footer"><span class="status-dot"></span><div>ARCHIVO LOCAL<span>Pixel Gun 3D · 11.3.1</span></div>${icon('premium')}</div>
  </aside>
  <div class="workspace">
    <header class="topbar">
      <div class="breadcrumb"><button class="icon-button mobile-menu" id="menu-toggle" aria-label="Abrir categorías" aria-controls="sidebar" aria-expanded="false">${icon('menu')}</button><span>Pixel Gun 3D</span>${icon('chevron')}<strong>Showroom</strong></div>
      <div class="topbar-right"><span class="archive-version">ARCHIVO / 11.3.1</span><span class="local-badge"><span class="status-dot"></span>100% original</span></div>
    </header>
    <main>
      <section class="page-heading" aria-labelledby="page-title">
        <div><p class="eyebrow"><span></span> EL SHOWROOM DEL ARSENAL CLÁSICO</p><h1 id="page-title">Píxeles. Potencia. <span>Historia.</span></h1><p class="page-intro">Redescubre cada arma. Explora cada detalle.</p></div>
        <div class="collection-count"><strong id="total-count">—</strong><span>ARMAS PARA<br>EXPLORAR ${icon('arrow')}</span></div>
      </section>
      <div class="section-heading"><h2><span class="section-number">01</span> Mesa de inspección</h2><span class="live-status" id="model-status" role="status">Preparando el archivo…</span></div>
      <section class="inspection" aria-label="Inspección del arma seleccionada">
        <div class="stage" id="stage" data-state="loading">
          <span class="stage-word" id="stage-word" aria-hidden="true">ARSENAL</span>
          <div class="stage-grid" aria-hidden="true"></div>
          <div class="viewport" id="viewport"></div>
          <div class="stage-top"><div><span class="weapon-category" id="weapon-category">CARGANDO ARCHIVO</span><h2 id="weapon-name">Tu próxima leyenda.</h2><span class="model-id" id="model-id">MODELOS ORIGINALES · GLB</span></div><span class="interactive-badge">${icon('wireframe')} VISTA 3D</span></div>
          <div class="viewer-message" id="viewer-message" role="status"><span class="spinner"></span><span>Cargando modelo 3D…</span></div>
          <div class="stage-bottom"><div class="viewer-toolbar" aria-label="Controles de la vista 3D"><button id="rotate" class="tool-button" aria-label="Rotación automática" aria-pressed="false" title="Rotación automática">${icon('rotate')}</button><button id="reset-view" class="tool-button" aria-label="Restablecer cámara" title="Restablecer cámara">${icon('reset')}</button><span class="tool-divider"></span><button id="wireframe" class="tool-button" aria-label="Ver malla" aria-pressed="false" title="Ver malla">${icon('wireframe')}</button><button id="fullscreen" class="tool-button" aria-label="Pantalla completa" title="Pantalla completa">${icon('expand')}</button></div><span class="drag-hint">${icon('mouse')} Arrastra para explorar <span>·</span> Scroll para zoom</span></div>
          <span class="stage-coordinate" aria-hidden="true">X / Y / Z <span>+</span></span>
        </div>
        <aside class="weapon-details" aria-label="Ficha del arma"><div class="details-title">${icon('damage')} FICHA DEL ARMA <span id="weapon-number">—</span></div><div class="rarity-row"><span class="rarity-badge" id="rarity">—</span><span id="tier" class="tier-label">—</span></div><div id="weapon-stats" class="weapon-stats"></div><div class="details-meta"><span>Formato<strong>GLB + PNG</strong></span><span>Origen<strong>Pixel Gun 3D</strong></span></div><div class="weapon-actions"><button id="play-audio" class="button button-accent" disabled>${icon('volume')}<span>Escuchar disparo</span></button><div class="download-files" aria-label="Descargar modelo y su textura"><a id="download" class="button button-secondary" download>${icon('download')}Modelo GLB</a><a id="download-texture" class="button button-secondary" download>Textura PNG</a></div></div><p class="original-note">${icon('check')} Datos extraídos del archivo original</p></aside>
      </section>
      <div class="inspection-caption"><span>MALLAS ORIGINALES. TEXTURAS PÍXEL A PÍXEL.</span><div class="weapon-navigation"><button id="previous-weapon" class="icon-button" aria-label="Arma anterior">${icon('chevron', 'flip')}</button><span id="weapon-position">— / —</span><button id="next-weapon" class="icon-button" aria-label="Arma siguiente">${icon('chevron')}</button></div></div>
      <section id="collection" class="collection" aria-labelledby="collection-title">
        <div class="collection-heading"><h2 id="collection-title"><span class="section-number">02</span> La colección <span id="result-count" class="count-badge">—</span></h2><span class="collection-subtitle" id="active-category">Todas las categorías. Todas las leyendas.</span></div>
        <div class="collection-tools"><div class="search-field">${icon('search')}<input id="search" type="search" placeholder="Buscar un arma, un nombre, una leyenda…" aria-label="Buscar armas" autocomplete="off" /><button id="clear-search" class="icon-button" aria-label="Limpiar búsqueda" hidden>${icon('close')}</button><kbd>/</kbd></div><div class="sort-field"><label for="sort">ORDENAR</label><select id="sort"><option value="featured">Destacadas</option><option value="name">Nombre: A–Z</option><option value="damage">Mayor daño</option><option value="tier">Mayor nivel</option></select></div></div>
        <div class="weapon-grid" id="weapon-grid" aria-live="polite"><div class="catalog-loading"><span class="spinner"></span> Abriendo el arsenal…</div></div>
        <div class="pagination"><span id="page-range">Cargando colección…</span><div><button id="previous-page" class="page-button" aria-label="Página anterior">${icon('chevron', 'flip')}</button><span id="page-label">—</span><button id="next-page" class="page-button" aria-label="Página siguiente">${icon('chevron')}</button></div></div>
      </section>
      <footer class="page-footer"><span>HECHO DE PÍXELES. LLENO DE HISTORIA.</span><span>PIXEL GUN 3D <b>©</b> ARCHIVO 11.3.1</span></footer>
    </main>
  </div>
  <div id="toast" class="toast" role="status" hidden></div>
`;

const $ = (selector) => document.querySelector(selector);
function toast(message) {
  clearTimeout(toastTimeout);
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  toastTimeout = setTimeout(() => { $('#toast').hidden = true; }, 4500);
}

function filteredWeapons() {
  const term = query.trim().toLocaleLowerCase('es');
  const list = weapons.filter((weapon) => (category === 'all' || weapon.category === category) && (!term || [weapon.name, weapon.id, weapon.slug, ...weapon.aliases].some((value) => value.toLocaleLowerCase('es').includes(term))));
  return list.sort((a, b) => {
    if (sort === 'name') return a.name.localeCompare(b.name, 'es', { numeric: true });
    if (sort === 'damage') return (b.stats.damage ?? -1) - (a.stats.damage ?? -1) || a.number - b.number;
    if (sort === 'tier') return b.tier - a.tier || a.number - b.number;
    const rank = (weapon) => { const index = featured.indexOf(weapon.slug); return index < 0 ? featured.length : index; };
    return rank(a) - rank(b) || a.number - b.number;
  });
}

function renderNav() {
  $('#category-nav').innerHTML = [['all', 'Todas las armas'], ...Object.entries(categoryNames)].map(([key, name]) => `<button class="category-button ${category === key ? 'active' : ''}" data-category="${key}" aria-pressed="${category === key}">${icon(key === 'all' ? 'grid' : key)}<span>${name}</span><small>${key === 'all' ? weapons.length : weapons.filter((weapon) => weapon.category === key).length}</small></button>`).join('');
}

// Shop icon from the game when there is one; otherwise a render of the textured GLB.
function preview(weapon) {
  if (weapon.icon) return `<img src="${asset(weapon.icon)}" alt="" loading="lazy" decoding="async" />`;
  const rendered = thumbnails?.cached(asset(weapon.model));
  if (rendered) return `<img src="${rendered}" alt="" />`;
  return `<span class="no-preview" data-thumbnail="${escape(weapon.id)}">${icon('wireframe')}<small>EXPLORAR EN 3D</small></span>`;
}

function fillThumbnails() {
  if (!thumbnails) return;
  for (const placeholder of document.querySelectorAll('#weapon-grid [data-thumbnail]')) {
    const weapon = weapons.find((item) => item.id === placeholder.dataset.thumbnail);
    thumbnails.render(asset(weapon.model)).then(() => {
      // The grid may have been re-rendered meanwhile: look the slot up again.
      const slot = document.querySelector(`#weapon-grid [data-thumbnail="${CSS.escape(weapon.id)}"]`);
      if (slot) slot.outerHTML = preview(weapon);
    }, (error) => console.error(`Vista previa de ${weapon.id}:`, error));
  }
}

// The shot when there is one; melee weapons and a few others only have their own sound.
function soundOf(weapon) {
  return weapon?.audio.find((item) => item.role === 'shoot') || weapon?.audio.find((item) => item.role === 'other') || weapon?.audio[0];
}

function audioLabel(weapon) {
  return soundOf(weapon)?.role === 'shoot' ? 'Escuchar disparo' : 'Escuchar sonido';
}

function renderCollection() {
  const list = filteredWeapons();
  const pages = Math.max(1, Math.ceil(list.length / pageSize));
  page = Math.min(page, pages - 1);
  $('#result-count').textContent = list.length;
  $('#active-category').textContent = category === 'all' ? 'Todas las categorías. Todas las leyendas.' : `Colección / ${categoryNames[category]}`;
  $('#clear-search').hidden = !query;
  $('#weapon-grid').innerHTML = list.slice(page * pageSize, (page + 1) * pageSize).map((weapon) => `<button class="weapon-card ${selected?.id === weapon.id ? 'selected' : ''}" data-weapon="${escape(weapon.id)}" aria-pressed="${selected?.id === weapon.id}"><div class="card-top"><span class="card-category">${icon(weapon.category)}${escape(categoryNames[weapon.category])}</span><span class="rarity-dot rarity-${escape(weapon.rarity.toLowerCase())}" title="${rarityNames[weapon.rarity] || escape(weapon.rarity)}"></span></div><div class="card-preview">${preview(weapon)}<span class="card-open">${icon('arrow')}</span></div><div class="card-info"><div><h3>${escape(weapon.name)}</h3><span>${rarityNames[weapon.rarity] || escape(weapon.rarity)} <b>·</b> ${weapon.tier ? `Nivel ${weapon.tier}` : 'Versión base'}</span></div><span class="selected-check">${icon('check')}</span></div></button>`).join('') || `<div class="empty-state">${icon('search')}<h3>Ningún arma en la mira.</h3><p>Prueba otro nombre o explora todas las categorías.</p><button class="button button-secondary" id="reset-filters">Limpiar filtros</button></div>`;
  fillThumbnails();
  $('#page-range').textContent = list.length ? `Mostrando ${page * pageSize + 1}–${Math.min((page + 1) * pageSize, list.length)} de ${list.length} armas` : '0 armas encontradas';
  $('#page-label').textContent = `${page + 1} / ${pages}`;
  $('#previous-page').disabled = page === 0;
  $('#next-page').disabled = page >= pages - 1;
  const index = list.findIndex((weapon) => weapon.id === selected?.id);
  $('#weapon-position').textContent = `${index < 0 ? '—' : String(index + 1).padStart(2, '0')} / ${String(list.length).padStart(2, '0')}`;
  $('#previous-weapon').disabled = $('#next-weapon').disabled = !list.length;
}

function setModelState(state, message) {
  $('#stage').dataset.state = state;
  $('#model-status').textContent = message;
  $('#model-status').classList.toggle('is-ready', state === 'ready');
  $('#viewer-message').innerHTML = state === 'loading' ? '<span class="spinner"></span><span>Cargando modelo 3D…</span>' : `<span>${escape(message)}</span>`;
}

function resetAudio() {
  audio.pause();
  audio.currentTime = 0;
  $('#play-audio span').textContent = audioLabel(selected);
  $('#play-audio').classList.remove('is-playing');
}

async function selectWeapon(weapon) {
  selected = weapon;
  const version = ++selectionVersion;
  resetAudio();
  $('#weapon-name').textContent = weapon.name;
  $('#stage-word').textContent = weapon.name.replace(/ Up\d+$/, '');
  $('#weapon-category').innerHTML = `${icon(weapon.category)} ${escape(categoryNames[weapon.category])}`;
  $('#model-id').textContent = `MODELO ${String(weapon.number).padStart(5, '0')} / ${weapon.id.toUpperCase()}`;
  $('#weapon-number').textContent = `#${String(weapon.number).padStart(3, '0')}`;
  $('#rarity').textContent = rarityNames[weapon.rarity] || weapon.rarity;
  $('#rarity').className = `rarity-badge rarity-${weapon.rarity.toLowerCase()}`;
  $('#tier').textContent = weapon.tier ? `NIVEL ${weapon.tier}` : 'VERSIÓN BASE';
  const stats = [['damage', 'Daño base', 'damage'], ['rate', 'Cadencia', 'fire_rate_shop'], ['ammo', 'Cargador', 'ammo_in_clip']];
  const peers = weapons.filter((item) => item.category === weapon.category);
  $('#weapon-stats').innerHTML = stats.map(([name, label, key]) => {
    const value = weapon.stats[key];
    const maximum = Math.max(1, ...peers.map((item) => item.stats[key] ?? 0));
    return `<div class="stat"><div class="stat-label">${icon(name)}<span>${label}</span><strong>${value ?? '—'}${key === 'ammo_in_clip' ? `<small> / ${weapon.stats.max_ammo ?? '—'}</small>` : ''}</strong></div><div class="stat-track" title="Escala relativa al máximo de esta categoría"><span style="width:${Math.min(100, Math.max(0, (value ?? 0) / maximum * 100))}%"></span></div></div>`;
  }).join('');
  $('#download').href = asset(weapon.model);
  $('#download').download = `${weapon.slug}.glb`;
  $('#download-texture').href = asset(weapon.textures[0]);
  $('#download-texture').download = weapon.textures[0].split('/').pop();
  $('#play-audio').disabled = !soundOf(weapon);
  renderCollection();
  if (!viewer) return;
  setModelState('loading', 'Cargando modelo…');
  try {
    if (await viewer.load(asset(weapon.model)) && version === selectionVersion) {
      viewer.renderer.domElement.setAttribute('aria-label', `Modelo 3D de ${weapon.name}. Arrastra para girar y usa la rueda para acercar.`);
      $('#stage').dataset.loadedId = weapon.id;
      setModelState('ready', 'Modelo listo para explorar');
    }
  } catch (error) {
    if (version !== selectionVersion) return;
    setModelState('error', 'No se pudo cargar el modelo. Selecciona otra arma o vuelve a intentarlo.');
    console.error('Carga del modelo:', error);
  }
}

function closeMenu() {
  document.body.classList.remove('menu-open');
  $('#menu-toggle').setAttribute('aria-expanded', 'false');
}

$('#category-nav').addEventListener('click', (event) => {
  const button = event.target.closest('[data-category]');
  if (!button) return;
  category = button.dataset.category;
  page = 0;
  renderNav();
  renderCollection();
  const list = filteredWeapons();
  if (list.length && !list.some((weapon) => weapon.id === selected?.id)) selectWeapon(list[0]);
  closeMenu();
});
$('#weapon-grid').addEventListener('click', (event) => {
  const card = event.target.closest('[data-weapon]');
  if (card) {
    selectWeapon(weapons.find((weapon) => weapon.id === card.dataset.weapon));
    if (window.innerWidth < 760) $('#stage').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  if (event.target.closest('#reset-filters')) {
    category = 'all'; query = ''; page = 0; $('#search').value = ''; renderNav(); renderCollection();
  }
});
$('#search').addEventListener('input', (event) => { query = event.target.value; page = 0; renderCollection(); });
$('#clear-search').addEventListener('click', () => { query = ''; page = 0; $('#search').value = ''; renderCollection(); $('#search').focus(); });
$('#sort').addEventListener('change', (event) => { sort = event.target.value; page = 0; renderCollection(); });
for (const [id, direction] of [['previous-page', -1], ['next-page', 1]]) {
  $( `#${id}`).addEventListener('click', () => { page += direction; renderCollection(); $('#collection').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
}
for (const [id, direction] of [['previous-weapon', -1], ['next-weapon', 1]]) {
  $(`#${id}`).addEventListener('click', () => {
    const list = filteredWeapons();
    if (!list.length) return;
    const current = list.findIndex((weapon) => weapon.id === selected?.id);
    const index = current < 0 ? (direction > 0 ? 0 : list.length - 1) : (current + direction + list.length) % list.length;
    page = Math.floor(index / pageSize);
    selectWeapon(list[index]);
  });
}
$('#rotate').addEventListener('click', () => {
  if (!viewer) return;
  viewer.controls.autoRotate = !viewer.controls.autoRotate;
  $('#rotate').setAttribute('aria-pressed', String(viewer.controls.autoRotate));
});
$('#reset-view').addEventListener('click', () => viewer?.reset());
$('#wireframe').addEventListener('click', () => {
  if (!viewer) return;
  viewer.setWireframe(!viewer.wireframe);
  $('#wireframe').setAttribute('aria-pressed', String(viewer.wireframe));
});
$('#fullscreen').addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await $('#stage').requestFullscreen();
  } catch { toast('El navegador no permite abrir la vista en pantalla completa.'); }
});
$('#play-audio').addEventListener('click', async () => {
  if (!audio.paused) { resetAudio(); return; }
  const clip = soundOf(selected);
  if (!clip) return;
  audio.src = asset(clip.file);
  try {
    await audio.play();
    if (!audio.paused) {
      $('#play-audio span').textContent = 'Reproduciendo…';
      $('#play-audio').classList.add('is-playing');
    }
  } catch (error) {
    // Changing weapon while the clip loads aborts play(): not a failure.
    if (error.name !== 'AbortError') toast('No se pudo reproducir el sonido de esta arma.');
  }
});
audio.addEventListener('ended', resetAudio);
$('#menu-toggle').addEventListener('click', () => {
  const open = document.body.classList.toggle('menu-open');
  $('#menu-toggle').setAttribute('aria-expanded', String(open));
});
$('#sidebar-shade').addEventListener('click', closeMenu);
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeMenu();
  if (event.key === '/' && !event.ctrlKey && !event.metaKey && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { event.preventDefault(); $('#search').focus(); }
});
window.addEventListener('pagehide', (event) => { resetAudio(); if (!event.persisted) viewer?.dispose(); });

try {
  const response = await fetch(asset('catalog.json'));
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const catalog = await response.json();
  weapons = catalog.weapons.filter((weapon) => weapon.status === 'ok');
  $('#total-count').textContent = weapons.length;
  renderNav();
  try {
    viewer = new WeaponViewer($('#viewport'));
    $('#rotate').setAttribute('aria-pressed', String(viewer.controls.autoRotate));
  } catch (error) {
    setModelState('error', 'El visor necesita WebGL. Activa la aceleración gráfica para explorar los modelos.');
    for (const id of ['rotate', 'reset-view', 'wireframe']) $(`#${id}`).disabled = true;
    console.error('Inicialización del visor:', error);
  }
  // Without a second WebGL context the cards keep their placeholder.
  try { thumbnails = new WeaponThumbnails(); } catch (error) { console.error('Vistas previas:', error); }
  const initial = weapons.find((weapon) => weapon.slug === 'ak-48') || weapons[0];
  if (initial) await selectWeapon(initial);
  else setModelState('error', 'No hay armas disponibles en el catálogo.');
} catch (error) {
  setModelState('error', 'No se pudo abrir el catálogo de armas.');
  $('#weapon-grid').innerHTML = '<div class="empty-state"><h3>El archivo no está disponible.</h3><p>Comprueba que exports/weapons/catalog.json existe y recarga la página.</p><button class="button button-secondary" id="reload-catalog">Volver a cargar</button></div>';
  $('#reload-catalog').addEventListener('click', () => location.reload());
  $('#page-range').textContent = 'Catálogo no disponible';
  $('#previous-page').disabled = $('#next-page').disabled = true;
  console.error('Carga del catálogo:', error);
}
