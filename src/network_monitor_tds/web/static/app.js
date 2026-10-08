(() => {
  const toastBox = () => document.getElementById("toast");
  let toastTimer;

  function toast(message) {
    const box = toastBox();
    box.textContent = message;
    box.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { box.hidden = true; }, 3200);
  }

  function closeDialog() {
    const root = document.getElementById("dialog");
    const flipped = root.querySelector(".dialog.flipped");
    if (flipped) {
      flipDialog(flipped, false);
      if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
        afterFlip(flipped, closeDialog);
        return;
      }
    }
    const mac = root.querySelector(".dialog")?.dataset.mac;
    const close = () => {
      root.innerHTML = "";
      markHero(document.querySelector(`.poster[data-mac="${mac}"]`));
    };
    if (!mac || !document.startViewTransition) {
      close();
      return;
    }
    document.documentElement.classList.add("closing");
    document.startViewTransition(close).finished.finally(() => {
      document.documentElement.classList.remove("closing");
      markHero(null);
    });
  }

  // The marked poster shares its view-transition names with the dialog, so the browser morphs
  // one into the other when the dialog opens or closes.
  function markHero(poster) {
    document.querySelectorAll(".poster.is-hero").forEach((other) => other.classList.remove("is-hero"));
    poster?.classList.add("is-hero");
  }

  function flipDialog(dialog, flipped) {
    dialog.classList.toggle("flipped", flipped);
    dialog.querySelector(".face.front").inert = flipped;
    dialog.querySelector(".face.back").inert = !flipped;
    dialog.querySelector(flipped ? "[data-drawing-search]" : "[data-flip]").focus({ preventScroll: true });
  }

  function afterFlip(dialog, callback) {
    const flipper = dialog.querySelector(".flipper");
    flipper.addEventListener("transitionend", function done(event) {
      if (event.target !== flipper) return;
      flipper.removeEventListener("transitionend", done);
      callback();
    });
  }

  function previewDrawing(dialog, tile) {
    const source = tile.querySelector("svg");
    const thumb = dialog.querySelector(".d-art .thumb");
    const footprint = source.querySelector(".ground").getAttribute("rx");
    thumb.querySelector("use").setAttribute("href", source.querySelector("use").getAttribute("href"));
    thumb.querySelector(".ground").setAttribute("rx", footprint);
    dialog.querySelector("[data-flip]").style.setProperty("--fp", footprint);
  }

  function selectTab(tab) {
    tab.closest('[role="tablist"]').querySelectorAll('[role="tab"]').forEach((other) => {
      const selected = other === tab;
      other.setAttribute("aria-selected", String(selected));
      other.tabIndex = selected ? 0 : -1;
      document.getElementById(other.getAttribute("aria-controls")).hidden = !selected;
    });
    tab.focus();
  }

  // Drawings for the chosen category are recommended, never enforced: every drawing stays
  // selectable, and a search ranks them all by how well their label matches.
  function arrangeDrawings(picker) {
    const query = picker.querySelector("[data-drawing-search]").value.trim().toLowerCase();
    const dialog = picker.closest(".dialog");
    const option = dialog.querySelector('select[name="category"]').selectedOptions[0];
    if (!picker.querySelector('input[name="icon"]:checked')) {
      previewDrawing(dialog, picker.querySelector(`.tile[data-name="${option.dataset.drawing}"]`));
    }
    const ranked = [...picker.querySelectorAll(".tile")]
      .map((tile) => ({ tile, score: drawingScore(tile, query) }))
      .sort((a, b) => b.score - a.score || a.tile.dataset.order - b.tile.dataset.order);
    for (const { tile, score } of ranked) {
      tile.hidden = score < 0;
      const recommended = tile.dataset.category === option.dataset.category;
      picker.querySelector(recommended ? "[data-recommended]" : "[data-others]").append(tile);
    }
    picker.querySelectorAll(".dgroup").forEach((group) => {
      group.hidden = !group.querySelector(".tile:not([hidden])");
    });
    picker.querySelector("[data-no-match]").hidden = ranked.some(({ score }) => score >= 0);
  }

  function drawingScore(tile, query) {
    if (!query) return 0;
    const label = tile.dataset.label;
    if (label.startsWith(query)) return 3;
    if (label.split(/[\s,]+/).some((word) => word.startsWith(query))) return 2;
    return tile.dataset.terms.includes(query) ? 1 : -1;
  }

  function setLive(state, label) {
    const live = document.getElementById("live");
    live.classList.remove("connected", "lost");
    if (state) live.classList.add(state);
    live.querySelector(".live-label").textContent = label;
  }

  function showChartPoint(wrap, clientX) {
    const series = wrap.dataset.series.split(",").map(Number);
    const hit = wrap.querySelector(".hit").getBoundingClientRect();
    const index = Math.max(0, Math.min(series.length - 1, Math.round(((clientX - hit.left) / hit.width) * (series.length - 1))));
    const left = `${(index / (series.length - 1)) * 100}%`;
    const cross = wrap.querySelector(".cross");
    const tip = wrap.querySelector(".tip");
    cross.style.left = left;
    cross.hidden = false;
    tip.style.left = `clamp(48px, ${left}, calc(100% - 48px))`;
    tip.textContent = `${index === series.length - 1 ? "Now" : hoursAgo(series.length - 1 - index)} · ${series[index]} devices`;
    tip.hidden = false;
  }

  function hoursAgo(hours) {
    return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-close]")) closeDialog();
    if (event.target.closest("[data-flip]")) flipDialog(event.target.closest(".dialog"), true);
    if (event.target.closest("[data-unflip]")) flipDialog(event.target.closest(".dialog"), false);
    const tab = event.target.closest('[role="tab"]');
    if (tab) selectTab(tab);
    const arrow = event.target.closest("[data-scroll]");
    if (arrow) {
      const shelf = arrow.closest(".shelf-sec").querySelector(".shelf");
      shelf.scrollBy({ left: Number(arrow.dataset.scroll) * shelf.clientWidth * 0.85, behavior: "smooth" });
    }
  });

  document.addEventListener("input", (event) => {
    if (event.target.matches("[data-drawing-search]")) arrangeDrawings(event.target.closest("[data-drawings]"));
  });

  document.addEventListener("change", (event) => {
    if (event.target.matches('.dialog select[name="category"]')) {
      arrangeDrawings(event.target.closest(".dialog").querySelector("[data-drawings]"));
    }
    if (event.target.matches('.dialog input[name="icon"]')) {
      previewDrawing(event.target.closest(".dialog"), event.target.closest(".tile"));
    }
    const picker = event.target.closest?.("[data-cookie]");
    if (!picker) return;
    const { cookie, attribute } = picker.dataset;
    const value = event.target.value;
    document.cookie = `${cookie}=${value}; path=/; max-age=31536000; SameSite=Lax`;
    if (attribute && value === picker.dataset.default) delete document.documentElement.dataset[attribute];
    else if (attribute) document.documentElement.dataset[attribute] = value;
    const choice = event.target.selectedOptions?.[0] ?? event.target.closest("label");
    toast(`${picker.getAttribute("aria-label")}: ${choice.textContent.trim()}`);
  });

  document.addEventListener("keydown", (event) => {
    const flipped = document.querySelector("#dialog .dialog.flipped");
    if (event.key === "Escape" && flipped) flipDialog(flipped, false);
    else if (event.key === "Escape" && document.querySelector("#dialog .dialog")) closeDialog();
    if (event.key === "Enter" && event.target.matches("[data-drawing-search]")) event.preventDefault();
    const tab = event.target.closest?.('[role="tab"]');
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (tab && step) {
      const tabs = [...tab.parentElement.children];
      selectTab(tabs[(tabs.indexOf(tab) + step + tabs.length) % tabs.length]);
    }
  });

  document.addEventListener("pointermove", (event) => {
    const wrap = event.target.closest?.(".chart-wrap");
    if (wrap) showChartPoint(wrap, event.clientX);
  });

  document.addEventListener("pointerout", (event) => {
    const wrap = event.target.closest?.(".chart-wrap");
    if (wrap && !wrap.contains(event.relatedTarget)) {
      wrap.querySelector(".cross").hidden = true;
      wrap.querySelector(".tip").hidden = true;
    }
  });

  document.body.addEventListener("htmx:beforeTransition", (event) => markHero(event.target.closest(".poster")));

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id !== "dialog") return;
    event.detail.target.querySelector('[role="tab"][aria-selected="true"]')?.focus();
  });

  document.body.addEventListener("toast", (event) => toast(event.detail.value));

  document.body.addEventListener("htmx:sseOpen", () => setLive("connected", "Live"));
  document.body.addEventListener("htmx:sseError", () => setLive("lost", "Reconnecting"));
  document.body.addEventListener("htmx:sseMessage", (event) => {
    if (event.detail.type !== "device") return;
    const change = JSON.parse(event.detail.data);
    const messages = {
      device_discovered: `New device: ${change.name}`,
      device_online: `${change.name} came online`,
      device_offline: `${change.name} went offline`,
    };
    if (messages[change.kind]) toast(messages[change.kind]);
  });

  const toolbar = document.getElementById("filters");
  if (toolbar) {
    window.addEventListener("scroll", () => toolbar.classList.toggle("stuck", window.scrollY > 90), { passive: true });
  }

  // Chromium keeps left pages in the back/forward cache with their streams open; a few of
  // those exhaust its six connections per host and the next page waits until one times out.
  const streams = new Set();
  const createEventSource = htmx.createEventSource;
  htmx.createEventSource = (url) => {
    const stream = createEventSource(url);
    streams.add(stream);
    return stream;
  };
  window.addEventListener("pagehide", () => streams.forEach((stream) => stream.close()));
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) location.reload();
  });

  window.addEventListener("load", () => setTimeout(() => document.body.classList.remove("intro"), 1200));
})();
