// --- Version depuis le footer (incrustée côté serveur) ---
const APP_VERSION = document.getElementById("versionInfo").textContent.split(": ")[1];

// Utilitaire: normalise "2025/2026" -> "2025-2026"
function normalizeSeason(s) {
  return (s || "").replace("/", "-");
}

// --- Week-end courant (Samedi/Dimanche) ---
function getWeekendDates() {
  const now = new Date();
  const day = now.getDay(); // 0=Dim, 1=Lun, ..., 6=Sam
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((day + 6) % 7));
  const saturday = new Date(monday);
  saturday.setDate(monday.getDate() + 5);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const fmt = d => d.toISOString().slice(0, 10);
  return { saturday: fmt(saturday), sunday: fmt(sunday) };
}

// --- Chargement des catégories ---
async function loadCategoriesForSeason() {
  const saisonRaw = document.getElementById("saison")?.value || "";
  const saison = normalizeSeason(saisonRaw);
  const sel = document.getElementById("categories");

  // État "chargement"
  sel.innerHTML = "";
  const loadingOpt = document.createElement("option");
  loadingOpt.text = "Chargement des catégories…";
  loadingOpt.disabled = true;
  loadingOpt.selected = true;
  sel.add(loadingOpt);

  try {
    const resp = await fetch("/categories?saison=" + encodeURIComponent(saison));
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();

    sel.innerHTML = "";
    Object.entries(data).forEach(([code, info]) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.text = `${info.type || ""} - ${info.genre || ""} - ${info.label} - ${info.nom || ""}`;
      sel.add(opt);
    });

    // Optionnel: sélectionne tout par défaut si rien n'est coché
    if (sel.options.length && !Array.from(sel.options).some(o => o.selected)) {
      Array.from(sel.options).forEach(o => (o.selected = true));
    }
  } catch (e) {
    console.error("Erreur catégories:", e);
    sel.innerHTML = "";
    const errOpt = document.createElement("option");
    errOpt.text = "Erreur de chargement des catégories";
    errOpt.disabled = true;
    sel.add(errOpt);
  }
}

// --- Soumission du formulaire ---
async function submitForm(e) {
  e.preventDefault();
  document.getElementById("loading").style.display = "inline";
  document.getElementById("resultImg").style.display = "none";

  const saisonRaw = document.getElementById("saison").value;
  const saison = normalizeSeason(saisonRaw);
  const title = document.getElementById("title").value;
  const format = document.querySelector('input[name="format"]:checked').value;
  const cats = Array.from(document.getElementById("categories").selectedOptions).map(opt => opt.value);
  const date_start = document.getElementById("date_start").value;
  const date_end = document.getElementById("date_end").value;
  const mode = document.getElementById("mode").value;

  let url = "/image?mode=" + encodeURIComponent(mode);
  if (cats.length) url += "&" + cats.map(c => "categories=" + encodeURIComponent(c)).join("&");
  if (saison) url += "&saison=" + encodeURIComponent(saison);
  if (title) url += "&title=" + encodeURIComponent(title);
  if (format) url += "&format=" + encodeURIComponent(format);
  if (date_start) url += "&date_start=" + encodeURIComponent(date_start);
  if (date_end) url += "&date_end=" + encodeURIComponent(date_end);

  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const blob = await r.blob();
    const imgUrl = URL.createObjectURL(blob);
    const img = document.getElementById("resultImg");
    img.src = imgUrl;
    img.style.display = "block";
  } catch (err) {
    console.error("Erreur génération image:", err);
    alert("Erreur lors de la génération de l'image.");
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}

// --- Modal / Lightbox ---
function setupLightbox() {
  const img = document.getElementById("resultImg");
  const modal = document.getElementById("imgModal");
  const modalImg = document.getElementById("imgModalContent");
  const closeBtn = document.getElementById("imgModalClose");

  img.onclick = function () {
    if (this.src && this.style.display !== "none") {
      modalImg.src = this.src;
      modal.style.display = "flex";
    }
  };
  closeBtn.onclick = function () {
    modal.style.display = "none";
  };
  modal.onclick = function (e) {
    if (e.target === modal) modal.style.display = "none";
  };
}

// --- Boot ---
document.addEventListener("DOMContentLoaded", async function () {
  // Dates par défaut = week-end courant
  const weekend = getWeekendDates();
  document.getElementById("date_start").value = weekend.saturday;
  document.getElementById("date_end").value = weekend.sunday;

  // Catégories dynamiques au démarrage et sur changement de saison
  await loadCategoriesForSeason();
  document.getElementById("saison")?.addEventListener("change", loadCategoriesForSeason);

  // Form submit
  document.getElementById("filterForm").addEventListener("submit", submitForm);

  // Version dans le footer
  document.getElementById("versionInfo").textContent = "Version : " + APP_VERSION;

  // Lightbox
  setupLightbox();
});
