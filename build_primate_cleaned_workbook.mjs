import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const baseDir = "C:/Users/16976/Desktop/smile_FFV";
const dataDir = path.join(baseDir, "output", "cleaned_data");
const outXlsx = path.join(dataDir, "primate_data_cleaned.xlsx");

const headerFormat = {
  fill: "#0F766E",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
};

function colLetter(n) {
  let s = "";
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function csvMatrix(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];
    if (ch === '"') {
      if (inQuotes && next === '"') {
        cell += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      row.push(cell);
      cell = "";
    } else if ((ch === "\n" || ch === "\r") && !inQuotes) {
      if (ch === "\r" && next === "\n") i += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += ch;
    }
  }
  if (cell.length > 0 || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }
  return rows.filter((r) => !(r.length === 1 && r[0] === ""));
}

async function addCsvSheet(workbook, csvPath, sheetName) {
  const csvText = await fs.readFile(csvPath, "utf8");
  await workbook.fromCSV(csvText, { sheetName });
  return workbook.worksheets.getItem(sheetName);
}

async function csvColumnCount(csvPath) {
  const csvText = await fs.readFile(csvPath, "utf8");
  const rows = csvMatrix(csvText);
  return rows[0]?.length ?? 1;
}

async function main() {
  const workbook = Workbook.create();

  const summary = JSON.parse(
    await fs.readFile(path.join(dataDir, "summary.json"), "utf8"),
  );

  const overview = workbook.worksheets.add("Overview");
  overview.showGridLines = false;
  overview.getRange("A1:H1").merge();
  overview.getRange("A1").values = [["PIMs Cleaned Dataset Overview"]];
  overview.getRange("A1").format = {
    fill: "#0F766E",
    font: { bold: true, color: "#FFFFFF", size: 16 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };

  overview.getRange("A3:B11").values = [
    ["Metric", "Value"],
    ["Rows in cleaned dataset", summary.n_rows_clean],
    ["FFV pilot rows", summary.n_ffv_pilot],
    ["CO2 main rows", summary.n_co2_main],
    ["CO2/CH4 paired rows", summary.n_co2_ch4_pair],
    ["CO2/N2 paired rows", summary.n_co2_n2_pair],
    ["Primary source workbook", "primate_data.xlsx"],
    ["Cleaning strategy", "Flattened headers + tidy rows"],
    ["Original workbook edited?", "No"],
  ];
  overview.getRange("A3:B3").format = headerFormat;
  overview.getRange("A3:B11").format.wrapText = true;
  overview.getRange("A:B").format?.autofitColumns?.();
  overview.getRange("A:A").format.columnWidthPx = 220;
  overview.getRange("B:B").format.columnWidthPx = 220;

  overview.getRange("D3:E8").values = [
    ["Subset", "Rows"],
    ["FFV pilot", summary.n_ffv_pilot],
    ["CO2 main", summary.n_co2_main],
    ["CO2/CH4 pair", summary.n_co2_ch4_pair],
    ["CO2/N2 pair", summary.n_co2_n2_pair],
    ["All cleaned rows", summary.n_rows_clean],
  ];
  overview.getRange("D3:E3").format = headerFormat;

  const chart = overview.charts.add("bar", overview.getRange("D3:E8"));
  chart.title = "Subset Sizes";
  chart.hasLegend = false;
  chart.setPosition("G3", "N18");
  chart.xAxis = { axisType: "textAxis" };
  chart.yAxis = { numberFormatCode: "0" };

  overview.getRange("A14:H18").merge();
  overview.getRange("A14").values = [[
    "This workbook is a cleaned copy for machine-learning preparation. The original primate_data.xlsx was not modified. Use tidy_data as the master sheet, co2_main_subset for the CO2 task, and ffv_pilot_subset for the exploratory FFV model.",
  ]];
  overview.getRange("A14").format.wrapText = true;
  overview.getRange("A14").format.verticalAlignment = "top";
  overview.getRange("A14").format.fill = "#ECFDF5";
  overview.getRange("A14").format.rowHeightPx = 96;

  await addCsvSheet(workbook, path.join(dataDir, "tidy_data.csv"), "tidy_data");
  await addCsvSheet(workbook, path.join(dataDir, "co2_main_subset.csv"), "co2_main_subset");
  await addCsvSheet(workbook, path.join(dataDir, "ffv_pilot_subset.csv"), "ffv_pilot_subset");
  await addCsvSheet(workbook, path.join(dataDir, "co2_ch4_subset.csv"), "co2_ch4_subset");
  await addCsvSheet(workbook, path.join(dataDir, "co2_n2_subset.csv"), "co2_n2_subset");
  await addCsvSheet(workbook, path.join(dataDir, "key_metrics.csv"), "quality_metrics");
  await addCsvSheet(workbook, path.join(dataDir, "missingness.csv"), "missingness");
  await addCsvSheet(workbook, path.join(dataDir, "field_dictionary.csv"), "field_dictionary");
  await addCsvSheet(workbook, path.join(dataDir, "membrane_counts.csv"), "membrane_counts");

  const mainSheetCols = await csvColumnCount(path.join(dataDir, "tidy_data.csv"));

  const sheetSpecs = {
    tidy_data: { cols: mainSheetCols, wideCols: { A: 72, D: 220, E: 260 } },
    co2_main_subset: { cols: mainSheetCols, wideCols: { A: 72, D: 220, E: 260 } },
    ffv_pilot_subset: { cols: mainSheetCols, wideCols: { A: 72, D: 220, E: 260 } },
    co2_ch4_subset: { cols: mainSheetCols, wideCols: { A: 72, D: 220, E: 260 } },
    co2_n2_subset: { cols: mainSheetCols, wideCols: { A: 72, D: 220, E: 260 } },
    quality_metrics: { cols: 2, wideCols: { A: 240, B: 120 } },
    missingness: { cols: 4, wideCols: { A: 240, B: 120, C: 100, D: 120 } },
    field_dictionary: { cols: 2, wideCols: { A: 220, B: 460 } },
    membrane_counts: { cols: 2, wideCols: { A: 220, B: 100 } },
  };

  for (const [sheetName, spec] of Object.entries(sheetSpecs)) {
    const sheet = workbook.worksheets.getItem(sheetName);
    sheet.freezePanes.freezeRows(1);
    sheet.getRange(`A1:${colLetter(spec.cols)}1`).format = headerFormat;
    sheet.getRange(`A1:${colLetter(spec.cols)}200`).format.wrapText = true;
    for (const [col, width] of Object.entries(spec.wideCols)) {
      sheet.getRange(`${col}:${col}`).format.columnWidthPx = width;
    }
  }

  const metrics = csvMatrix(await fs.readFile(path.join(dataDir, "key_metrics.csv"), "utf8"));
  const metricSheet = workbook.worksheets.getItem("quality_metrics");
  metricSheet.getRange("D2:E7").values = metrics.slice(0, 6);
  metricSheet.getRange("D2:E2").format = headerFormat;
  const metricChart = metricSheet.charts.add("bar", metricSheet.getRange("D2:E7"));
  metricChart.title = "Key Dataset Counts";
  metricChart.hasLegend = false;
  metricChart.setPosition("G2", "N18");
  metricChart.xAxis = { axisType: "textAxis" };
  metricChart.yAxis = { numberFormatCode: "0" };

  await fs.mkdir(dataDir, { recursive: true });
  for (const sheetName of [
    "Overview",
    "tidy_data",
    "co2_main_subset",
    "ffv_pilot_subset",
    "quality_metrics",
    "field_dictionary",
  ]) {
    const blob = await workbook.render({
      sheetName,
      autoCrop: "all",
      scale: 1,
      format: "png",
    });
    const bytes = new Uint8Array(await blob.arrayBuffer());
    await fs.writeFile(path.join(dataDir, `${sheetName}.png`), bytes);
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outXlsx);
  console.log(`Saved ${outXlsx}`);
}

await main();
