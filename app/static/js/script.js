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

// --- Sync date_end sur le lendemain de date_start ---
function syncEndToNextDay(opts = { force: false }) {
  const start = document.getElementById("date_start");
  const end   = document.getElementById("date_end");
  if (!start || !end || !start.value) return;

  // Empêche une fin avant le début
  end.min = start.value;

  // Calcule le lendemain (robuste fuseau)
  let next;
  if (start.valueAsDate) {
    next = new Date(start.valueAsDate.getTime());
    next.setDate(next.getDate() + 1);
    // Si on force, ou si end est avant start, on met le lendemain
    if (opts.force || !end.value || end.value < start.value) {
      end.valueAsDate = next;
    }
  } else {
    const [y, m, d] = start.value.split("-").map(Number);
    next = new Date(y, m - 1, d);
    next.setDate(next.getDate() + 1);
    const iso = new Date(next.getTime() - next.getTimezoneOffset() * 60000)
      .toISOString().slice(0, 10);
    if (opts.force || !end.value || end.value < start.value) {
      end.value = iso;
    }
  }
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
      opt.text = `${info.titre || ""}`;
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

  // Mettre la contrainte min et sync initiale
  syncEndToNextDay({ force: false });

  // Quand la date de début change -> forcer le lendemain et min
  document.getElementById("date_start").addEventListener("change", () => {
    syncEndToNextDay({ force: true });
  });

  // S'il met une date de fin avant le début, on recale
  document.getElementById("date_end").addEventListener("change", () => {
    const start = document.getElementById("date_start").value;
    const end = document.getElementById("date_end").value;
    if (start && end && end < start) syncEndToNextDay({ force: true });
  });

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

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("imgModal");
  const modalImg = document.getElementById("imgModalContent");
  const closeBtn = document.getElementById("imgModalClose");

  let zoomed = false;
  let dragging = false;
  let startX = 0, startY = 0;
  let baseX = 0, baseY = 0; // offset courant

  function resetView() {
    zoomed = false;
    dragging = false;
    baseX = baseY = 0;
    modalImg.classList.remove("zoomed");
    modalImg.style.transform = "translate(0, 0)";
    modalImg.style.maxWidth = "90%";
    modalImg.style.maxHeight = "90%";
  }

  // Toggle zoom au clic
  modalImg.addEventListener("click", (e) => {
    if (dragging) return; // éviter déclenchement si on a déplacé
    zoomed = !zoomed;
    if (zoomed) {
      modalImg.classList.add("zoomed");
      modalImg.style.maxWidth = "50%";
      modalImg.style.maxHeight = "50%";
      baseX = baseY = 0;
      modalImg.style.transform = "translate(0, 0)";
    } else {
      resetView();
    }
  });

  // Début drag
  modalImg.addEventListener("mousedown", (e) => {
    if (!zoomed) return;
    dragging = true;
    startX = e.clientX - baseX;
    startY = e.clientY - baseY;
  });

  // Fin drag
  window.addEventListener("mouseup", () => {
    dragging = false;
  });

  // Déplacement
  window.addEventListener("mousemove", (e) => {
    if (!dragging || !zoomed) return;

    let newX = e.clientX - startX;
    let newY = e.clientY - startY;

    // On pourrait ici ajouter des limites (clamp) si besoin
    baseX = newX;
    baseY = newY;
    modalImg.style.transform = `translate(${baseX}px, ${baseY}px)`;
  });

  // Fermeture → reset
  closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
    resetView();
  });
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
      resetView();
    }
  });
});

  const resultImg = document.getElementById("resultImg");
  const dlIcon = document.getElementById("downloadIcon");
  const shareIcon = document.getElementById("shareIcon");

  // Masquer les icônes avant génération
  document.getElementById("filterForm").addEventListener("submit", () => {
    dlIcon.style.display = "none";
    shareIcon.style.display = "none";
  });

  // Afficher les icônes après génération
  resultImg.addEventListener("load", () => {
    if (resultImg.src) {
      dlIcon.style.display = "inline-flex";
      shareIcon.style.display = "inline-flex";
    }
  });

  // Téléchargement direct
  dlIcon.addEventListener("click", () => {
    if (!resultImg.src) return;
    const a = document.createElement("a");
    a.href = resultImg.src;
    a.download = "image-veec.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
  });

  // Partage avec fallback
  shareIcon.addEventListener("click", async () => {
    if (!resultImg.src) return;

    try {
      const resp = await fetch(resultImg.src, { cache: "no-store" });
      const blob = await resp.blob();
      const file = new File([blob], "image-veec.png", { type: blob.type || "image/png" });

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          title: "Comm' VEEC",
          text: "Voici l'image générée 🚀",
          files: [file]
        });
        return;
      }

      if (navigator.share) {
        await navigator.share({
          title: "Comm' VEEC",
          text: "Voici l'image générée 🚀",
          url: resultImg.src
        });
        return;
      }

      // Fallback: téléchargement
      const a = document.createElement("a");
      a.href = resultImg.src;
      a.download = "image-veec.png";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      console.warn("Partage indisponible, fallback download.", e);
    }
  });

const refreshIcon   = document.getElementById("refreshConfigIcon");
const statusEl      = document.getElementById("configStatus");

function setRefreshBusy(busy) {
  if (busy) {
    refreshIcon.dataset.busy = "1";
    refreshIcon.classList.remove("fa-rotate-right");
    refreshIcon.classList.add("fa-spinner", "fa-spin", "is-busy");
    refreshIcon.title = "Mise à jour en cours…";
    refreshIcon.style.cursor = "wait";
  } else {
    refreshIcon.dataset.busy = "0";
    refreshIcon.classList.remove("fa-spinner", "fa-spin", "is-busy");
    refreshIcon.classList.add("fa-rotate-right");
    refreshIcon.title = "Mettre à jour la configuration";
    refreshIcon.style.cursor = "pointer";
  }
}

function showStatus(msg, type = "info", autohideMs = 3000) {
  statusEl.className = "";           // reset classes
  statusEl.classList.add(type);      // info | ok | error
  statusEl.textContent = msg;
  statusEl.style.display = "inline";

  // auto‑masquage (sauf en cas d’erreur, on laisse visible)
  if (type !== "error" && autohideMs > 0) {
    clearTimeout(statusEl._t);
    statusEl._t = setTimeout(() => {
      statusEl.style.display = "none";
    }, autohideMs);
  }
}

refreshIcon?.addEventListener("click", async () => {
  if (refreshIcon.dataset.busy === "1") return;

  try {
    setRefreshBusy(true);
    showStatus("Mise à jour…", "info", 0);

    const resp  = await fetch("/update-config", { method: "POST" });
    const data  = await resp.json();

    // Succès
    showStatus(data.message || "Configuration mise à jour.", "ok", 2500);
  } catch (err) {
    // Erreur (on ne masque pas automatiquement)
    showStatus("Échec de la mise à jour : " + err, "error", 0);
  } finally {
    setRefreshBusy(false);
  }
});
