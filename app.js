const fallbackReport = {
  sampleName: "MY_SAMPLE",
  uiDirection: {
    primary: "Option 5 consumer-friendly ancestry report",
    secondary: "Option 2 explore map",
  },
  extraction: {
    usable23andmeRsidCalls: null,
    build: "37",
  },
  datasets: [
    {
      id: "hgdp",
      displayName: "HGDP",
      referenceSampleCount: 0,
      referenceLabelCount: 0,
      compatibleSnpCount: 0,
      compatibleRatePct: null,
      coordinateMatchRatePct: null,
      eagleResultFileCount: 0,
      status: "prepared_for_eagle",
    },
    {
      id: "1000genomes",
      displayName: "1000 Genomes",
      referenceSampleCount: 0,
      referenceLabelCount: 0,
      compatibleSnpCount: 0,
      compatibleRatePct: null,
      coordinateMatchRatePct: null,
      eagleResultFileCount: 0,
      status: "prepared_for_eagle",
    },
  ],
};

const fallbackQuality = {
  datasets: {
    hgdp: { totals: {} },
    "1000genomes": { totals: {} },
  },
};

const fallbackPhasing = {
  datasets: {},
};

const fallbackSegments = {
  chromosomes: {},
};

const fallbackValidation = {
  accuracy: null,
  sampleCount: 0,
};

const fallbackTournament = {
  winner: null,
  models: [],
};

const fallbackValidationDashboard = {
  holdout: {},
  tournament: {},
};

const fallbackSampleModelOutputs = {
  models: [],
  metaModel: {},
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
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const selected = button.dataset.tab;
      document.querySelectorAll("[data-tab]").forEach((item) => item.classList.toggle("active", item.dataset.tab === selected));
      document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
        panel.classList.toggle("active", panel.dataset.tabPanel === selected);
      });
    });
  });
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Pending";
  }
  return Number(value).toLocaleString();
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Pending";
  }
  return `${Number(value).toFixed(1)}%`;
}

async function loadJson(path, fallback) {
  try {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return { data: await response.json(), source: "pipeline" };
  } catch {
    return { data: fallback, source: "fallback" };
  }
}

function renderMetrics(report) {
  document.querySelector("#sampleName").textContent = report.sampleName || "MY_SAMPLE";
  document.querySelector("#usableCalls").textContent = formatNumber(report.extraction?.usable23andmeRsidCalls);
  document.querySelector("#datasetCount").textContent = formatNumber(report.datasets?.length ?? 0);
  document.querySelector("#uiDirection").textContent = "Option 5";
}

function renderDatasets(report) {
  const list = document.querySelector("#datasetList");
  list.innerHTML = "";

  for (const dataset of report.datasets || []) {
    const rate = dataset.compatibleRatePct ?? 0;
    const row = document.createElement("div");
    row.className = "dataset-row";
    row.innerHTML = `
      <div>
        <div class="dataset-title">${dataset.displayName}</div>
        <div class="dataset-meta">${formatNumber(dataset.referenceSampleCount)} reference samples · ${formatNumber(dataset.referenceLabelCount)} labels</div>
      </div>
      <div>
        <div class="bar" aria-label="Compatible SNP rate"><i style="width: ${Math.max(4, Math.min(rate, 100))}%"></i></div>
        <div class="dataset-meta">${formatPercent(dataset.compatibleRatePct)} compatible SNP rate</div>
      </div>
      <span class="pill">${dataset.status?.replaceAll("_", " ") || "pending"}</span>
    `;
    list.append(row);
  }
}

function datasetLabel(dataset) {
  return dataset === "1000genomes" ? "1000 Genomes" : dataset.toUpperCase();
}

function chromosomeRow(chrom, stats) {
  const hets = Number(stats?.heterozygousVariants ?? 0);
  const phased = Number(stats?.phasedHeterozygousVariants ?? 0);
  const unphased = Number(stats?.unphasedHeterozygousVariants ?? 0);
  const rate = Number(stats?.phasedHetRatePct ?? 0);
  const hap1 = Number(stats?.hap1AltAlleles ?? 0);
  const hap2 = Number(stats?.hap2AltAlleles ?? 0);
  const hapTotal = Math.max(hap1 + hap2, 1);
  const hap1Pct = (hap1 / hapTotal) * 100;
  const hap2Pct = (hap2 / hapTotal) * 100;
  const success = hets > 0 && phased === hets && unphased === 0;
  const status = success ? "success" : "review";
  const statusText = success ? "phased" : "review";

  return `
    <div class="chromosome">
      <span>${chrom}</span>
      <div class="chromosome-body">
        <div class="copy-pair" aria-label="Chromosome ${chrom} copy phasing status">
          <div class="copy-row">
            <span class="copy-label">copy 1</span>
            <div class="copy-track"><i class="hap-one" style="width: ${Math.max(4, hap1Pct)}%"></i></div>
            <span class="copy-status ${status}">${statusText}</span>
          </div>
          <div class="copy-row">
            <span class="copy-label">copy 2</span>
            <div class="copy-track"><i class="hap-two" style="width: ${Math.max(4, hap2Pct)}%"></i></div>
            <span class="copy-status ${status}">${statusText}</span>
          </div>
        </div>
        <div class="chromosome-meta">
          <span>${formatNumber(phased)} / ${formatNumber(hets)} heterozygous sites split into two haplotypes</span>
          <strong>${formatPercent(rate)}</strong>
        </div>
      </div>
    </div>
  `;
}

function renderChromosomes(phasing) {
  const stack = document.querySelector("#chromosomeStack");
  stack.innerHTML = "";

  const datasets = ["hgdp", "1000genomes"].filter((dataset) => phasing.datasets?.[dataset]);
  if (!datasets.length) {
    stack.innerHTML = '<p class="empty-state">Phasing QC has not been exported yet.</p>';
    return;
  }

  for (const dataset of datasets) {
    const group = document.createElement("section");
    group.className = "chromosome-group";
    const rows = [];
    for (let chrom = 1; chrom <= 22; chrom += 1) {
      const stats = phasing.datasets?.[dataset]?.[String(chrom)];
      if (stats) {
        rows.push(chromosomeRow(chrom, stats));
      }
    }
    const totalHets = rows.length
      ? Object.values(phasing.datasets?.[dataset] || {}).reduce((sum, row) => sum + Number(row.heterozygousVariants || 0), 0)
      : 0;
    group.innerHTML = `
      <div class="chromosome-group-heading">
        <div>
          <strong>${datasetLabel(dataset)}</strong>
          <span>${formatNumber(totalHets)} heterozygous sites</span>
        </div>
        <span class="pill">phased haplotypes</span>
      </div>
      ${rows.join("")}
    `;
    stack.append(group);
  }
}

function labelClass(label) {
  const colors = ["teal", "coral", "amber", "green", "slate"];
  let hash = 0;
  for (const char of label) {
    hash = (hash + char.charCodeAt(0)) % colors.length;
  }
  return colors[hash];
}

function renderLocalAncestry(segments) {
  const list = document.querySelector("#ancestryBreakdown");
  const available = Object.values(segments.chromosomes || {}).flat();
  if (!available.length) {
    list.innerHTML = '<p class="empty-state">Local ancestry segments will appear after FLARE runs.</p>';
    return;
  }

  const totals = new Map();
  for (const segment of available) {
    const label = segment.label || "Unassigned";
    const length = Math.max(0, Number(segment.end || 0) - Number(segment.start || 0) + 1);
    totals.set(label, (totals.get(label) || 0) + length);
  }

  const totalLength = [...totals.values()].reduce((sum, value) => sum + value, 0) || 1;
  const rows = [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([label, length]) => {
      const pct = (length / totalLength) * 100;
      return `
        <div class="ancestry-row">
          <span><i class="swatch ${labelClass(label)}"></i>${label.replaceAll("_", " ")}</span>
          <div class="bar"><i style="width: ${Math.max(3, pct)}%"></i></div>
          <strong>${formatPercent(pct)}</strong>
        </div>
      `;
    });

  const chromCount = Object.keys(segments.chromosomes || {}).length;
  const profile = segments.smoothingProfile?.replaceAll("_", " ") || "raw/no HMM";
  list.innerHTML = `
    <div class="ancestry-note">${formatNumber(chromCount)} chromosome${chromCount === 1 ? "" : "s"} with FLARE segments · ${profile}</div>
    ${rows.join("")}
  `;
}

function renderQuality(report, quality, validation) {
  const grid = document.querySelector("#qualityGrid");
  grid.innerHTML = "";

  for (const dataset of report.datasets || []) {
    const totals = quality.datasets?.[dataset.id]?.totals || {};
    const article = document.createElement("article");
    article.innerHTML = `
      <span>${dataset.displayName}</span>
      <strong>${formatNumber(totals.compatibleBiallelicSnpCount ?? dataset.compatibleSnpCount)}</strong>
      <span>${formatPercent(totals.coordinateMatchRatePct ?? dataset.coordinateMatchRatePct)} coordinate match</span>
    `;
    grid.append(article);
  }

  const extraction = document.createElement("article");
  extraction.innerHTML = `
    <span>Raw build</span>
    <strong>${report.extraction?.build || "Pending"}</strong>
    <span>Detected from extraction log</span>
  `;
  grid.append(extraction);

  const validator = document.createElement("article");
  validator.innerHTML = `
    <span>HGDP holdout validation</span>
    <strong>${validation.accuracy === null || validation.accuracy === undefined ? "Pending" : formatPercent(Number(validation.accuracy) * 100)}</strong>
    <span>${formatNumber(validation.sampleCount || 0)} known samples, chr22</span>
  `;
  grid.append(validator);
}

function renderTournament(tournament) {
  const list = document.querySelector("#modelTournament");
  if (!list) {
    return;
  }
  const models = tournament.models || [];
  if (!models.length) {
    list.innerHTML = '<p class="empty-state">Model tournament results will appear after validation runs.</p>';
    return;
  }
  list.innerHTML = models.slice(0, 5).map((model, index) => `
    <div class="model-row">
      <span>${index + 1}</span>
      <div>
        <strong>${model.modelName.replaceAll("_", " ")}</strong>
        <small>${formatPercent(Number(model.accuracy || 0) * 100)} · ${formatNumber(model.trackedBridgeErrors || 0)} tracked bridge errors</small>
      </div>
      <span class="pill">${model.modelName === tournament.winner ? "winner" : "tested"}</span>
    </div>
  `).join("");
}

function renderValidationDetails(dashboard) {
  const box = document.querySelector("#validationDetails");
  const holdout = dashboard.holdout || {};
  const bridge = holdout.bridgeErrors || {};
  const pairs = bridge.pairs || {};
  const errors = holdout.errors || [];
  const southern = holdout.southernEuropeanAttractorErrors || [];
  const independent = dashboard.independentModels || [];
  const synthetic = dashboard.syntheticValidation?.rfmixDefaultStrict;
  const gridModels = dashboard.parameterGrid?.models || [];
  box.innerHTML = `
    <div class="quality-grid">
      <article><span>Holdout accuracy</span><strong>${formatPercent(Number(holdout.accuracy || 0) * 100)}</strong><span>${formatNumber(holdout.sampleCount || 0)} known samples</span></article>
      <article><span>Total errors</span><strong>${formatNumber(holdout.errorCount || errors.length)}</strong><span>chr22 validation</span></article>
      <article><span>Southern attractor</span><strong>${formatNumber(southern.length)}</strong><span>non-Southern labels called Southern</span></article>
    </div>
    <div class="model-list">
      ${Object.entries(pairs).map(([pair, count]) => `
        <div class="bridge-row"><div><strong>${pair.replaceAll("_", " ")}</strong><small>tracked bridge pair</small></div><strong>${formatNumber(count)}</strong></div>
      `).join("")}
    </div>
    <div class="model-list">
      ${independent.map((model) => `
        <div class="bridge-row">
          <div><strong>${model.displayName}</strong><small>${(model.status || "pending").replaceAll("_", " ")}</small></div>
          <strong>${model.accuracy === null || model.accuracy === undefined ? "Pending" : formatPercent(Number(model.accuracy) * 100)}</strong>
        </div>
      `).join("")}
      ${synthetic ? `
        <div class="bridge-row">
          <div><strong>RFMix synthetic mixtures</strong><small>${synthetic.status.replaceAll("_", " ")}</small></div>
          <strong>${Number(synthetic.meanMixtureAbsError).toFixed(3)}</strong>
        </div>
      ` : ""}
      ${gridModels.map((model) => `
        <div class="bridge-row">
          <div><strong>${model.preset.replaceAll("_", " ")}</strong><small>RFMix parameter check · ${formatNumber(model.trackedBridgeErrors)} bridge errors</small></div>
          <strong>${model.accuracy === null || model.accuracy === undefined ? Number(model.meanMixtureAbsError).toFixed(3) : formatPercent(Number(model.accuracy) * 100)}</strong>
        </div>
      `).join("")}
    </div>
    <div class="model-list">
      ${errors.slice(0, 8).map((row) => `
        <div class="bridge-row">
          <div><strong>${row.trueLabel.replaceAll("_", " ")} -> ${row.predictedLabel.replaceAll("_", " ")}</strong><small>${row.sample}</small></div>
          <strong>${formatPercent(Number(row.topProbability || 0) * 100)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function renderSampleModelOutputs(outputs) {
  const list = document.querySelector("#sampleModelOutputs");
  const copies = document.querySelector("#copyDiagnostics");
  const models = outputs.models || [];
  const meta = outputs.metaModel || {};
  if (!models.length) {
    list.innerHTML = '<p class="empty-state">Sample model outputs will appear after model runs.</p>';
    copies.innerHTML = '<p class="empty-state">Copy-specific diagnostics will appear after model runs.</p>';
    return;
  }
  const metaHtml = `
    <div class="output-row meta-output">
      <div>
        <strong>Meta-model</strong>
        <small>${(meta.status || "provisional").replaceAll("_", " ")}</small>
      </div>
      <div>
        ${(meta.topConsensus || []).slice(0, 5).map((item) => `
          <div class="ancestry-row">
            <span><i class="swatch ${labelClass(item.label)}"></i>${item.label.replaceAll("_", " ")}</span>
            <div class="bar"><i style="width: ${Math.max(3, Number(item.probability || 0))}%"></i></div>
            <strong>${formatPercent(item.probability)}</strong>
          </div>
        `).join("")}
        <div class="ancestry-note">${meta.labelPolicy?.reason || "Final labels require validation."}</div>
      </div>
    </div>
  `;
  list.innerHTML = metaHtml + models.map((model) => `
    <div class="output-row">
      <div><strong>${model.displayName}</strong><small>${model.id.replaceAll("_", " ")}</small></div>
      <div>
        ${(model.globalTop || []).slice(0, 5).map((item) => `
          <div class="ancestry-row">
            <span><i class="swatch ${labelClass(item.label)}"></i>${item.label.replaceAll("_", " ")}</span>
            <div class="bar"><i style="width: ${Math.max(3, Number(item.probability || 0))}%"></i></div>
            <strong>${formatPercent(item.probability)}</strong>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");

  copies.innerHTML = models.map((model) => `
    <div class="output-row">
      <div><strong>${model.displayName}</strong><small>copy-specific chr22 proportions</small></div>
      <div>
        ${Object.entries(model.segments?.perCopy || {}).map(([copy, labels]) => {
          const top = Object.entries(labels).slice(0, 4);
          return `<div class="ancestry-note">copy ${copy}: ${top.map(([label, pct]) => `${label.replaceAll("_", " ")} ${formatPercent(pct)}`).join(" · ")}</div>`;
        }).join("")}
      </div>
    </div>
  `).join("");
}

async function main() {
  initTheme();
  initTabs();
  const [
    reportResult,
    qualityResult,
    phasingResult,
    segmentsResult,
    validationResult,
    tournamentResult,
    validationDashboardResult,
    sampleModelOutputsResult,
  ] = await Promise.all([
    loadJson("/data/report_summary.json", fallbackReport),
    loadJson("/data/shared_snp_quality.json", fallbackQuality),
    loadJson("/data/phasing_qc.json", fallbackPhasing),
    loadJson("/data/chromosome_segments_hgdp.json", fallbackSegments),
    loadJson("/data/validation_hgdp_chr22.json", fallbackValidation),
    loadJson("/data/model_tournament_hgdp_chr22.json", fallbackTournament),
    loadJson("/data/validation_dashboard.json", fallbackValidationDashboard),
    loadJson("/data/sample_model_outputs.json", fallbackSampleModelOutputs),
  ]);

  const report = reportResult.data;
  const quality = qualityResult.data;
  const phasing = phasingResult.data;
  const segments = segmentsResult.data;
  const validation = validationResult.data;
  const tournament = tournamentResult.data;
  const validationDashboard = validationDashboardResult.data;
  const sampleModelOutputs = sampleModelOutputsResult.data;
  const live = reportResult.source === "pipeline";
  document.querySelector("#dataStatus").textContent = live
    ? "Using exported pipeline JSON"
    : "Using deploy preview shell";

  renderMetrics(report);
  renderDatasets(report);
  renderChromosomes(phasing);
  renderLocalAncestry(segments);
  renderQuality(report, quality, validation);
  renderTournament(tournament);
  renderValidationDetails(validationDashboard);
  renderSampleModelOutputs(sampleModelOutputs);
}

main().catch((error) => {
  console.error(error);
  const status = document.querySelector("#dataStatus");
  const chromosomes = document.querySelector("#chromosomeStack");
  if (status) {
    status.textContent = "App render error";
  }
  if (chromosomes) {
    chromosomes.innerHTML = `<p class="empty-state">${error.message}</p>`;
  }
});
