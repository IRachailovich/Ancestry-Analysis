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

function renderChromosomes() {
  const stack = document.querySelector("#chromosomeStack");
  stack.innerHTML = "";
  for (let chrom = 1; chrom <= 8; chrom += 1) {
    const row = document.createElement("div");
    row.className = "chromosome";
    row.innerHTML = `
      <span>${chrom}</span>
      <div class="chromosome-track" aria-label="Chromosome ${chrom} preview">
        <i></i><i></i><i></i>
      </div>
    `;
    stack.append(row);
  }
}

function renderQuality(report, quality) {
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
}

async function main() {
  const [reportResult, qualityResult] = await Promise.all([
    loadJson("/data/report_summary.json", fallbackReport),
    loadJson("/data/shared_snp_quality.json", fallbackQuality),
  ]);

  const report = reportResult.data;
  const quality = qualityResult.data;
  const live = reportResult.source === "pipeline";
  document.querySelector("#dataStatus").textContent = live
    ? "Using exported pipeline JSON"
    : "Using deploy preview shell";

  renderMetrics(report);
  renderDatasets(report);
  renderChromosomes();
  renderQuality(report, quality);
}

main();
