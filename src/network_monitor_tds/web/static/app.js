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

  function closeDrawer() {
    document.getElementById("drawer").innerHTML = "";
    document.body.style.overflow = "";
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
    if (event.target.closest("[data-close]")) closeDrawer();
    const arrow = event.target.closest("[data-scroll]");
    if (arrow) {
      const shelf = arrow.closest(".shelf-sec").querySelector(".shelf");
      shelf.scrollBy({ left: Number(arrow.dataset.scroll) * shelf.clientWidth * 0.85, behavior: "smooth" });
    }
  });

  document.addEventListener("change", (event) => {
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
    if (event.key === "Escape" && document.querySelector("#drawer .drawer")) closeDrawer();
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

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id !== "drawer") return;
    if (!event.detail.target.querySelector(".drawer")) {
      closeDrawer();
      return;
    }
    document.body.style.overflow = "hidden";
    event.detail.target.querySelector("[data-close].icon-btn")?.focus();
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

  window.addEventListener("load", () => setTimeout(() => document.body.classList.remove("intro"), 1200));
})();
