const fallbackConsole = {
  status: "data_workflow_reset",
  rawAadr: {
    samples: 17629,
    snps: 1233013,
    source: "/mnt/f/data/raw/aadr/v54.1_1240K_public.{geno,snp,ind}",
  },
  activeStage: "phase_original_aadr",
  workflowRule: "Original AADR is exported and phased first. Every intersection and every model must consume phased AADR artifacts.",
  gates: [
    {
      name: "1. Export original AADR",
      status: "script_ready",
      detail: "Convert original AADR EIGENSTRAT to per-chromosome VCF for EAGLE2. No target sample is used here.",
    },
    {
      name: "2. Phase original AADR",
      status: "pending_run",
      detail: "Run EAGLE2 on the exported AADR VCFs. From this point onward, downstream work uses only phased AADR.",
    },
    {
      name: "3. Intersect after phasing",
      status: "blocked_until_phased",
      detail: "Build model-specific intersections from phased AADR plus phased/imputed target VCFs.",
    },
    {
      name: "4. Run validated models",
      status: "not_started",
      detail: "RFMix, FLARE, qpAdm, ChromoPainter, and kernel models stay empty until corrected intersections exist.",
    },
  ],
  artifacts: [
    {
      label: "Data-first script",
      path: "/mnt/d/Python/Genetics/scripts/aadr_data_first.py",
    },
    {
      label: "AADR phase input",
      path: "/mnt/f/data/processed/genetics_eagle/work/aadr_original_phase_input/",
    },
    {
      label: "Phased AADR output",
      path: "/mnt/f/data/processed/genetics_eagle/results/phased_reference/aadr_original/",
    },
    {
      label: "Post-phasing intersections",
      path: "/mnt/f/data/processed/genetics_eagle/work/intersections/aadr_original_phased/",
    },
  ],
  intersections: [],
  models: [
    { name: "RFMix", status: "waiting_for_corrected_intersection", result: "No corrected output displayed." },
    { name: "FLARE", status: "waiting_for_corrected_intersection", result: "No corrected output displayed." },
    { name: "qpAdm", status: "waiting_for_corrected_intersection", result: "No corrected output displayed." },
    { name: "Kernel", status: "waiting_for_corrected_intersection", result: "No corrected output displayed." },
    { name: "ChromoPainter", status: "waiting_for_corrected_intersection", result: "No corrected output displayed." },
  ],
  notes: [
    "Broad labels mean an initial coarse ancestry state space, for example Arabian_Levantine vs Northwest_North_European vs Southern_European, used only for validation stability. Fine labels come later if they pass validation.",
    "Balanced references means limiting each label to a comparable number of samples during validation so a large label does not win simply because it has more examples.",
    "Controlled parameter grid means changing RFMix parameters deliberately and evaluating likelihood/validation error, not accepting defaults as truth.",
    "The target haplotypes should be evaluated copy by copy; adjacent-window score correlation is exactly the biological signal we want to model."
  ],
};

function applyTheme(theme) {
  const resolved = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = resolved;
  const button = document.querySelector("#themeToggle");
  if (button) {
    button.textContent = resolved === "dark" ? "Light" : "Dark";
    button.setAttribute("aria-label", `Switch to ${resolved === "dark" ? "light" : "dark"} theme`);
  }
}

function initTheme() {
  const stored = localStorage.getItem("ancestry-theme");
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  applyTheme(stored || (prefersDark ? "dark" : "light"));
  document.querySelector("#themeToggle")?.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("ancestry-theme", next);
    applyTheme(next);
  });
}

function initTabs() {
  const setActiveTab = (selected) => {
    document.body.dataset.activeTab = selected;
    document.querySelectorAll("[data-tab]").forEach((item) => item.classList.toggle("active", item.dataset.tab === selected));
    document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.tabPanel === selected);
    });
  };
  const initial = document.querySelector("[data-tab].active")?.dataset.tab || "data";
  setActiveTab(initial);
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      setActiveTab(button.dataset.tab);
    });
  });
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toLocaleString();
}

async function loadConsole() {
  try {
    const response = await fetch("/data/data_first_console.json");
    if (!response.ok) {
      throw new Error("fallback");
    }
    return { data: await response.json(), source: "pipeline" };
  } catch {
    return { data: fallbackConsole, source: "fallback" };
  }
}

function statusClass(status) {
  if (status.includes("ready") || status.includes("complete")) return "success";
  if (status.includes("blocked") || status.includes("waiting")) return "review";
  return "";
}

function render(consoleData, source) {
  document.querySelector("#dataStatus").textContent = source === "pipeline" ? "Using pipeline console JSON" : "Using reset console";
  document.querySelector("#workflowRule").textContent = consoleData.workflowRule;
  document.querySelector("#rawSamples").textContent = formatNumber(consoleData.rawAadr?.samples);
  document.querySelector("#rawSnps").textContent = formatNumber(consoleData.rawAadr?.snps);
  document.querySelector("#activeStage").textContent = (consoleData.activeStage || "-").replaceAll("_", " ");
  document.querySelector("#modelStatus").textContent = "empty until corrected";

  document.querySelector("#dataGates").innerHTML = (consoleData.gates || []).map((gate) => `
    <div class="dataset-row">
      <div>
        <div class="dataset-title">${gate.name}</div>
        <div class="dataset-meta">${gate.detail}</div>
      </div>
      <span class="copy-status ${statusClass(gate.status)}">${gate.status.replaceAll("_", " ")}</span>
    </div>
  `).join("");

  document.querySelector("#artifactPaths").innerHTML = (consoleData.artifacts || []).map((artifact) => `
    <div class="output-row">
      <div>
        <strong>${artifact.label}</strong>
        <small>${artifact.path}</small>
      </div>
    </div>
  `).join("");

  const intersections = consoleData.intersections || [];
  document.querySelector("#intersectionCaches").innerHTML = intersections.length
    ? intersections.map((cache) => `
      <article>
        <span>${cache.name}</span>
        <strong>${formatNumber(cache.sites)}</strong>
        <span>${cache.status.replaceAll("_", " ")}</span>
      </article>
    `).join("")
    : '<article><span>No corrected intersections yet</span><strong>0</strong><span>Phase AADR first</span></article>';

  document.querySelector("#modelRuns").innerHTML = (consoleData.models || []).map((model) => `
    <div class="bridge-row">
      <div>
        <strong>${model.name}</strong>
        <small>${model.result}</small>
      </div>
      <span class="copy-status ${statusClass(model.status)}">${model.status.replaceAll("_", " ")}</span>
    </div>
  `).join("");

  document.querySelector("#frameworkNotes").innerHTML = `
    <div class="model-list">
      ${(consoleData.notes || []).map((note) => `<div class="bridge-row"><div><strong>${note}</strong></div></div>`).join("")}
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function slugifyHeading(text, index) {
  const slug = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return slug || `section-${index + 1}`;
}

function formatInlineMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/(https?:\/\/[^\s)]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>');
  return html;
}

function renderMarkdownTable(lines) {
  const rows = lines
    .filter((line) => line.trim().startsWith("|") && line.trim().endsWith("|"))
    .map((line) => line.trim().slice(1, -1).split("|").map((cell) => formatInlineMarkdown(cell.trim())));
  if (rows.length < 2) {
    return "";
  }
  const [head, , ...body] = rows;
  return `
    <div class="book-table-wrap">
      <table>
        <thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>
        <tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
      </table>
    </div>
  `;
}

function markdownToHtml(markdown) {
  const lines = markdown.split(/\r?\n/);
  const html = [];
  let paragraph = [];
  let list = [];
  let orderedList = [];
  let mathBlock = [];
  let inMath = false;
  let table = [];

  const flushParagraph = () => {
    if (!paragraph.length) {
      return;
    }
    html.push(`<p>${formatInlineMarkdown(paragraph.join(" "))}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (list.length) {
      html.push(`<ul>${list.map((item) => `<li>${formatInlineMarkdown(item)}</li>`).join("")}</ul>`);
      list = [];
    }
    if (orderedList.length) {
      html.push(`<ol>${orderedList.map((item) => `<li>${formatInlineMarkdown(item)}</li>`).join("")}</ol>`);
      orderedList = [];
    }
  };

  const flushTable = () => {
    if (table.length) {
      html.push(renderMarkdownTable(table));
      table = [];
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (inMath) {
      mathBlock.push(line);
      if (trimmed === "\\]") {
        html.push(`<div class="math-block">${escapeHtml(mathBlock.join("\n"))}</div>`);
        mathBlock = [];
        inMath = false;
      }
      continue;
    }

    if (trimmed === "\\[") {
      flushParagraph();
      flushList();
      flushTable();
      inMath = true;
      mathBlock = [line];
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      flushList();
      flushTable();
      continue;
    }

    if (/^\|.+\|$/.test(trimmed)) {
      flushParagraph();
      flushList();
      table.push(line);
      continue;
    }

    flushTable();

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = Math.min(heading[1].length + 1, 6);
      html.push(`<h${level}>${formatInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    const bullet = trimmed.match(/^-\s+(.+)$/);
    if (bullet) {
      flushParagraph();
      orderedList = [];
      list.push(bullet[1]);
      continue;
    }

    const number = trimmed.match(/^\d+\.\s+(.+)$/);
    if (number) {
      flushParagraph();
      list = [];
      orderedList.push(number[1]);
      continue;
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();
  flushTable();
  return html.join("");
}

function splitBookSections(markdown) {
  const lines = markdown.split(/\r?\n/);
  const sections = [];
  let current = null;

  for (const line of lines) {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (match) {
      if (current) {
        sections.push(current);
      }
      current = {
        level: match[1].length,
        title: match[2].trim(),
        lines: [],
      };
      continue;
    }
    if (current) {
      current.lines.push(line);
    }
  }

  return sections.map((section, index) => ({
    ...section,
    id: slugifyHeading(section.title, index),
    html: markdownToHtml(section.lines.join("\n")),
  }));
}

function ensureMathJax() {
  if (window.MathJax || document.querySelector("#mathjax-script")) {
    return;
  }
  window.MathJax = {
    tex: { inlineMath: [["\\(", "\\)"]], displayMath: [["\\[", "\\]"]] },
    svg: { fontCache: "global" },
  };
  const script = document.createElement("script");
  script.id = "mathjax-script";
  script.async = true;
  script.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js";
  document.head.append(script);
}

async function renderBookReader() {
  const toc = document.querySelector("#bookToc");
  const page = document.querySelector("#bookPage");
  const title = document.querySelector("#bookSectionTitle");
  const meta = document.querySelector("#bookSectionMeta");
  const indicator = document.querySelector("#bookPageIndicator");
  const previous = document.querySelector("#bookPrev");
  const next = document.querySelector("#bookNext");
  if (!toc || !page || !title || !meta || !indicator || !previous || !next) {
    return;
  }

  let sections = [];
  let activeIndex = 0;

  const sectionOutlineHtml = (index) => {
    const section = sections[index];
    const children = sections
      .slice(index + 1)
      .filter((candidate) => candidate.level > section.level)
      .filter((candidate, candidateIndex, allChildren) => {
        const originalIndex = sections.indexOf(candidate);
        const nextPeer = sections.slice(index + 1, originalIndex).some((prior) => prior.level <= section.level);
        return !nextPeer && allChildren.indexOf(candidate) === candidateIndex;
      });

    if (!children.length) {
      return '<p class="empty-state">This section is a divider for the next part of the book.</p>';
    }

    return `
      <p class="book-chapter-note">This chapter contains these sections:</p>
      <ul>
        ${children.map((child) => `<li>${formatInlineMarkdown(child.title)}</li>`).join("")}
      </ul>
    `;
  };

  const showSection = (index) => {
    activeIndex = Math.max(0, Math.min(index, sections.length - 1));
    const section = sections[activeIndex];
    title.textContent = section.title;
    meta.textContent = `Section ${activeIndex + 1} of ${sections.length}`;
    page.innerHTML = section.html || sectionOutlineHtml(activeIndex);
    indicator.textContent = `${activeIndex + 1} / ${sections.length}`;
    previous.disabled = activeIndex === 0;
    next.disabled = activeIndex === sections.length - 1;
    toc.querySelectorAll("button").forEach((button, buttonIndex) => {
      button.classList.toggle("active", buttonIndex === activeIndex);
    });
    page.scrollTop = 0;
    if (window.MathJax?.typesetPromise) {
      window.MathJax.typesetPromise([page]).catch(() => {});
    }
  };

  try {
    const response = await fetch("/docs/ancestry_models_book.md");
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    const markdown = await response.text();
    sections = splitBookSections(markdown);
    toc.innerHTML = sections.map((section, index) => `
      <button class="book-toc-item depth-${Math.min(section.level, 4)}" type="button" data-book-index="${index}">
        ${formatInlineMarkdown(section.title)}
      </button>
    `).join("");
    toc.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => showSection(Number(button.dataset.bookIndex)));
    });
    previous.addEventListener("click", () => showSection(activeIndex - 1));
    next.addEventListener("click", () => showSection(activeIndex + 1));
    ensureMathJax();
    showSection(0);
  } catch (error) {
    title.textContent = "Ancestry Models";
    meta.textContent = "Reader unavailable";
    page.innerHTML = `<p class="empty-state">Could not load the manuscript: ${escapeHtml(error.message)}</p>`;
    indicator.textContent = "-";
    previous.disabled = true;
    next.disabled = true;
  }
}

async function main() {
  initTheme();
  initTabs();
  const { data, source } = await loadConsole();
  render(data, source);
  renderBookReader();
}

main().catch((error) => {
  console.error(error);
  document.querySelector("#dataStatus").textContent = "App render error";
});
