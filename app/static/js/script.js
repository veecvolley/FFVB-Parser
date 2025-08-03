
const APP_VERSION = document.getElementById("versionInfo").textContent.split(": ")[1];

document.addEventListener("DOMContentLoaded", async function () {
    // --- Calcul automatique samedi/dimanche de la semaine courante ---
    function getWeekendDates() {
        const now = new Date();
        const day = now.getDay();
        const monday = new Date(now);
        monday.setDate(now.getDate() - ((day + 6) % 7));
        const saturday = new Date(monday);
        saturday.setDate(monday.getDate() + 5);
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        function fmt(d) { return d.toISOString().slice(0, 10); }
        return { saturday: fmt(saturday), sunday: fmt(sunday) };
    }

    const weekend = getWeekendDates();
    document.getElementById("date_start").value = weekend.saturday;
    document.getElementById("date_end").value = weekend.sunday;

    // --- Chargement des catégories ---
    fetch("/categories")
        .then(r => r.json())
        .then(cats => {
            const sel = document.getElementById("categories");
            Object.entries(cats).forEach(([val, label]) => {
                let opt = document.createElement("option");
                opt.value = val;
                opt.text = label;
                sel.add(opt);
            });
        });

    // --- Soumission du formulaire ---
    document.getElementById("filterForm").onsubmit = async function (e) {
        e.preventDefault();
        document.getElementById("loading").style.display = "inline";
        document.getElementById("resultImg").style.display = "none";

        let title = document.getElementById("custom_title").value;
        let format = document.querySelector('input[name="format"]:checked').value;
        let cats = Array.from(document.getElementById("categories").selectedOptions).map(opt => opt.value);
        let date_start = document.getElementById("date_start").value;
        let date_end = document.getElementById("date_end").value;
        let mode = document.getElementById("mode_select").value;

        let url = "/image?mode=" + encodeURIComponent(mode);
        url += "&" + cats.map(c => "categories=" + encodeURIComponent(c)).join("&");

        if (title) url += "&title=" + encodeURIComponent(title);
        if (format) url += "&format=" + encodeURIComponent(format);
        if (date_start) url += "&date_start=" + encodeURIComponent(date_start);
        if (date_end) url += "&date_end=" + encodeURIComponent(date_end);

        fetch(url)
            .then(r => r.blob())
            .then(blob => {
                let imgUrl = URL.createObjectURL(blob);
                let img = document.getElementById("resultImg");
                img.src = imgUrl;
                img.style.display = "block";
                document.getElementById("loading").style.display = "none";
            });
    };

    // --- Ajout de la version dans le footer ---
    document.getElementById("versionInfo").textContent = "Version : " + APP_VERSION;

    // --- Modal/lightbox pour agrandir l’image ---
    document.getElementById("resultImg").onclick = function () {
        if (this.src && this.style.display !== "none") {
            document.getElementById("imgModalContent").src = this.src;
            document.getElementById("imgModal").style.display = "flex";
        }
    };
    document.getElementById("imgModalClose").onclick = function () {
        document.getElementById("imgModal").style.display = "none";
    };
    document.getElementById("imgModal").onclick = function (e) {
        if (e.target === this) {
            document.getElementById("imgModal").style.display = "none";
        }
    };
});
