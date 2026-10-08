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
    const form = root.querySelector("#labels-form[data-dirty]");
    if (form) saveLabels(form);
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

  // Labels save as they change, without re-rendering the dialog, so the picker stays open.
  function saveLabels(form) {
    delete form.dataset.dirty;
    fetch(form.dataset.save, { method: "POST", body: new URLSearchParams(new FormData(form)) })
      .then((response) => {
        if (!response.ok) throw new Error(response.statusText);
        document.body.dispatchEvent(new Event("devices-changed"));
        toast("Saved");
      })
      .catch(() => toast("Could not save"));
  }

  function chooseCategory(dialog, option) {
    dialog.style.setProperty("--cat", `var(--cat-${option.dataset.color})`);
    const picker = dialog.querySelector("[data-drawings]");
    arrangeDrawings(picker);
    const [first] = [...picker.querySelectorAll(`.tile[data-category="${option.dataset.category}"]`)]
      .sort((a, b) => a.dataset.order - b.dataset.order);
    first.querySelector("input").checked = true;
    previewDrawing(dialog, first);
    saveLabels(dialog.querySelector("#labels-form"));
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

  // Each sort starts in its natural direction; the order button reverses it.
  function setSortOrder(order) {
    const label = document.getElementById("sort").selectedOptions[0].dataset[order];
    const button = document.querySelector("[data-sort-order]");
    document.getElementById("order").value = order;
    button.dataset.order = order;
    button.title = label;
    button.setAttribute("aria-label", `Order: ${label}`);
    button.querySelector(".label").textContent = label;
  }

  function togglePanel(button) {
    const open = button.getAttribute("aria-expanded") !== "true";
    closePanels();
    button.setAttribute("aria-expanded", String(open));
    document.getElementById(button.getAttribute("aria-controls")).hidden = !open;
  }

  function closePanels() {
    document.querySelectorAll("[data-panel]").forEach((button) => {
      button.setAttribute("aria-expanded", "false");
      document.getElementById(button.getAttribute("aria-controls")).hidden = true;
    });
  }

  function removeFilter(chip) {
    const { unset, value } = chip.dataset;
    const input = document.querySelector(
      unset === "status" ? '#filters input[name="status"][value="all"]' : `#filters input[name="${unset}"][value="${value}"]`,
    );
    input.checked = unset === "status";
    input.dispatchEvent(new Event("change", { bubbles: true }));
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
    const panelButton = event.target.closest("[data-panel]");
    if (panelButton) togglePanel(panelButton);
    else if (!event.target.closest(".panel")) closePanels();
    const filterChip = event.target.closest("[data-unset]");
    if (filterChip) removeFilter(filterChip);
    if (event.target.closest("[data-sort-order]")) {
      const order = document.getElementById("order");
      setSortOrder(order.value === "asc" ? "desc" : "asc");
      order.dispatchEvent(new Event("change", { bubbles: true }));
    }
    const arrow = event.target.closest("[data-scroll]");
    if (arrow) {
      const shelf = arrow.closest(".shelf-sec").querySelector(".shelf");
      shelf.scrollBy({ left: Number(arrow.dataset.scroll) * shelf.clientWidth * 0.85, behavior: "smooth" });
    }
  });

  document.addEventListener("input", (event) => {
    if (event.target.matches("[data-drawing-search]")) arrangeDrawings(event.target.closest("[data-drawings]"));
    if (event.target.matches('#labels-form input[name="name"]')) event.target.form.dataset.dirty = "";
  });

  document.addEventListener("submit", (event) => {
    if (event.target.id !== "labels-form") return;
    event.preventDefault();
    saveLabels(event.target);
  });

  document.addEventListener("change", (event) => {
    if (event.target.matches('#labels-form select[name="category"]')) {
      chooseCategory(event.target.closest(".dialog"), event.target.selectedOptions[0]);
    }
    if (event.target.matches('.dialog input[name="icon"]')) {
      previewDrawing(event.target.closest(".dialog"), event.target.closest(".tile"));
      saveLabels(event.target.form);
    }
    if (event.target.matches('#labels-form input[name="name"]')) saveLabels(event.target.form);
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

  // Captured so the order is reset before htmx sends the form on the same change.
  document.addEventListener("change", (event) => {
    if (event.target.id === "sort") setSortOrder(event.target.selectedOptions[0].dataset.order);
  }, true);

  document.addEventListener("keydown", (event) => {
    const flipped = document.querySelector("#dialog .dialog.flipped");
    if (event.key === "Escape" && flipped) flipDialog(flipped, false);
    else if (event.key === "Escape" && document.querySelector("#dialog .dialog")) closeDialog();
    else if (event.key === "Escape") closePanels();
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
