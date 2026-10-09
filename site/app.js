"use strict";

// Every page shares this script. Attach behaviour only when its page is present.
// All article sections share one archive widget. Section pages are discovered
// from their _section.md; adding a new section does not require JS changes.
function readReturnState(key) {
  try {
    const value = JSON.parse(sessionStorage.getItem(key) || "null");
    return value?.pending && typeof value.scrollY === "number" ? value : null;
  } catch (_) { return null; }
}
function saveReturnState(key, details) {
  try {
    sessionStorage.setItem(key, JSON.stringify({ ...details, scrollY: scrollY, pending: true }));
  } catch (_) { /* sessionStorage might be disabled */ }
}
function restoreReturnPosition(key, value) {
  if (!value) return;
  requestAnimationFrame(() => requestAnimationFrame(() => {
    window.scrollTo({ top: value.scrollY, behavior: "instant" });
    try { sessionStorage.removeItem(key); } catch (_) {}
  }));
}

const archive = document.querySelector("[data-archive]");
if (archive) {
  const archiveList = archive.querySelector(".archive-list");
  const archiveCount = archive.querySelector(".archive-count");
  const searchInput = archive.querySelector(".archive-search-input");
  const categoryButtons = Array.from(archive.querySelectorAll(".filter"));
  const key = "dii.archive." + archive.dataset.archive + ".v2";
  const saved = readReturnState(key);
  let articles = [];
  let category = saved?.category || "全部";
  if (saved?.query) searchInput.value = saved.query;

  function makeRow(article) {
    const link = document.createElement("a");
    link.className = "archive-row";
    link.href = article.url;
    link.setAttribute("aria-label", "阅读：" + article.title);
    const date = document.createElement("span");
    date.className = "archive-date";
    date.textContent = article.date.slice(0, 4);
    const type = document.createElement("span");
    type.className = "archive-category";
    type.textContent = article.category;
    const title = document.createElement("span");
    title.className = "archive-title";
    title.textContent = article.title;
    if (article.author) {
      const author = document.createElement("small");
      author.className = "archive-author";
      author.textContent = "作者：" + article.author;
      title.appendChild(author);
    }
    const arrow = document.createElement("span");
    arrow.className = "archive-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "↗";
    link.append(date, type, title, arrow);
    return link;
  }

  function updateTabs() {
    categoryButtons.forEach((button) => {
      const active = button.dataset.filter === category;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }
  function render() {
    const query = searchInput.value.trim().toLocaleLowerCase("zh-CN");
    const items = articles.filter((post) => {
      if (category !== "全部" && post.category !== category) return false;
      return !query || [post.title, post.category, post.author, ...(post.tags || [])]
        .join(" ").toLocaleLowerCase("zh-CN").includes(query);
    });
    archiveList.replaceChildren(...items.map(makeRow));
    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "暂时没有找到对应的文章。";
      archiveList.append(empty);
    }
    archiveCount.textContent = "共 " + items.length + " 篇文章";
  }
  updateTabs();
  categoryButtons.forEach((button) => button.addEventListener("click", () => {
    category = button.dataset.filter;
    updateTabs();
    render();
  }));
  searchInput.addEventListener("input", render);
  archiveList.addEventListener("click", (event) => {
    if (event.target.closest("a.archive-row")) {
      saveReturnState(key, { category, query: searchInput.value });
    }
  });
  fetch(archive.dataset.index)
    .then((response) => {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    })
    .then((entries) => {
      articles = entries;
      render();
      restoreReturnPosition(key, saved);
    })
    .catch(() => {
      archiveCount.textContent = "文章索引读取失败";
      archiveList.textContent = "请通过本地 HTTP 服务预览页面，或检查栏目数据。";
    });
}

// Sections that opt for a simple server-rendered title list reuse the same
// independent per-section scroll restoration as the searchable archive.
const simpleSection = document.querySelector("[data-static-section]");
if (simpleSection) {
  const key = "dii.archive." + simpleSection.dataset.staticSection + ".v2";
  simpleSection.addEventListener("click", (event) => {
    if (event.target.closest("a.study-article")) saveReturnState(key, {});
  });
  const saved = readReturnState(key);
  if (saved) {
    if (document.readyState === "complete") restoreReturnPosition(key, saved);
    else window.addEventListener("load", () => restoreReturnPosition(key, saved), { once: true });
  }
}

const dialog = document.getElementById("album-dialog");
if (dialog) {
  const open = () => { if (!dialog.open) dialog.showModal(); };
  const opener = document.getElementById("open-album");
  const secondary = document.getElementById("open-album-secondary");
  const close = document.getElementById("close-album");
  opener?.addEventListener("click", open);
  secondary?.addEventListener("click", open);
  close?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
}

/*
 * Homepage name reveal:
 * Department for Intensive Instruction of Fundamental Sciences -> DII 的博客,
 * while the compact full name becomes "A place for dreams and dreaming".
 * The animation plays once. The original static title is always the fallback.
 */
(function animateHeroName() {
  const story = document.querySelector("[data-hero-story]");
  if (!story || !Element.prototype.animate ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const expansion = story.querySelector(".hero-expansion");
  const sourceLetters = [...story.querySelectorAll(".expansion-initial")];
  const targetLetters = [...story.querySelectorAll(".hero-char")];
  const blogSuffix = story.querySelector(".hero-heading-rest");
  const subtitle = story.querySelector(".hero-slogan");
  if (!expansion || sourceLetters.length !== 3 || targetLetters.length !== 3 ||
      !blogSuffix || !subtitle) return;

  story.classList.add("is-animating");
  let lettersInFlight = [];
  const delay = (milliseconds) =>
    new Promise((resolve) => window.setTimeout(resolve, milliseconds));
  const play = (element, keyframes, options) => element.animate(keyframes, options);
  const heroPanel = story.closest(".hero-panel");

  // Measure everything in the hero's local coordinates, never in a
  // separately scrolling viewport coordinate space.
  function localRect(element) {
    const panelRect = heroPanel.getBoundingClientRect();
    const rect = element.getBoundingClientRect();
    return {
      left: rect.left - panelRect.left - heroPanel.clientLeft,
      top: rect.top - panelRect.top - heroPanel.clientTop,
      width: rect.width,
      height: rect.height,
      centerX: rect.left - panelRect.left - heroPanel.clientLeft + rect.width / 2,
      centerY: rect.top - panelRect.top - heroPanel.clientTop + rect.height / 2,
    };
  }

  function floatingInitial(from, to) {
    const start = localRect(from);
    const end = localRect(to);
    const computed = getComputedStyle(from);
    const floating = document.createElement("span");
    floating.className = "flying-initial";
    floating.textContent = from.textContent;
    Object.assign(floating.style, {
      position: "absolute",
      left: start.left + "px",
      top: start.top + "px",
      fontFamily: computed.fontFamily,
      fontWeight: computed.fontWeight,
      fontSize: computed.fontSize,
      lineHeight: computed.lineHeight,
      letterSpacing: computed.letterSpacing,
      color: computed.color,
      whiteSpace: "nowrap",
      pointerEvents: "none",
      transformOrigin: "top left",
      zIndex: "30",
    });
    heroPanel.appendChild(floating);
    lettersInFlight.push(floating);
    const dx = end.left - start.left;
    const dy = end.top - start.top;
    const sx = end.width / Math.max(start.width, 1);
    const sy = end.height / Math.max(start.height, 1);
    return play(floating, [
      { transform: "translate(0px,0px) scale(1,1)" },
      { transform: "translate(" + dx + "px," + dy + "px) scale(" + sx + "," + sy + ")" }
    ], {
      duration: 980,
      easing: "cubic-bezier(.22,.72,.2,1)",
      fill: "forwards",
    });
  }

  async function run() {
    await play(expansion, [
      { opacity: 0, transform: "translate(-50%,calc(-50% + 9px))" },
      { opacity: 1, transform: "translate(-50%,-50%)" }
    ], {
      duration: 730, easing: "ease-out", fill: "forwards"
    }).finished;
    await delay(880);

    const source = localRect(expansion);
    const destination = localRect(subtitle);
    const dx = destination.centerX - source.centerX;
    const dy = destination.centerY - source.centerY;
    const compactScale = window.innerWidth <= 700 ? 0.56 : 0.55;
    const initials = sourceLetters.map((from, index) =>
      floatingInitial(from, targetLetters[index]));
    // These three initials are now represented by the flying copies.
    // Concealing the originals prevents a second D/I/I from drifting down
    // with the shrinking full-name sentence during the same animation.
    sourceLetters.forEach((letter) => { letter.style.visibility = "hidden"; });

    await Promise.all([
      play(expansion, [
        { transform: "translate(-50%,-50%) scale(1)" },
        { transform: "translate(calc(-50% + " + dx +
          "px),calc(-50% + " + dy + "px)) scale(" + compactScale + ")" }
      ], {
        duration: 980,
        easing: "cubic-bezier(.2,.65,.2,1)",
        fill: "forwards"
      }).finished,
      ...initials.map((animation) => animation.finished)
    ]);

    await Promise.all([
      ...targetLetters.map((letter) => play(letter, [
        { opacity: 0 }, { opacity: 1 }
      ], { duration: 140, fill: "forwards" }).finished),
      ...lettersInFlight.map((floating) => play(floating, [
        { opacity: 1 }, { opacity: 0 }
      ], { duration: 160, fill: "forwards" }).finished)
    ]);
    lettersInFlight.forEach((letter) => letter.remove());
    lettersInFlight = [];

    await play(blogSuffix, [
      { opacity: 0, transform: "translateY(5px)" },
      { opacity: 1, transform: "translateY(0px)" }
    ], {
      duration: 440,
      easing: "ease-out",
      fill: "forwards"
    }).finished;
    await delay(320);

    await Promise.all([
      play(expansion, [
        { opacity: 1 }, { opacity: 0 }
      ], { duration: 560, easing: "ease-in-out", fill: "forwards" }).finished,
      play(subtitle, [
        { opacity: 0, transform: "translateY(4px)" },
        { opacity: 1, transform: "translateY(0px)" }
      ], { duration: 620, easing: "ease-out", fill: "forwards" }).finished
    ]);
  }

  run()
    .catch(() => {})
    .finally(() => {
      story.classList.remove("is-animating");
      expansion.style.display = "none";
      lettersInFlight.forEach((letter) => letter.remove());
      story.dataset.animationComplete = "true";
    });
})();
