// Erzeugt PNG-Dateien mit transparentem Hintergrund aus allen SVGs in logo/svg/ und egiz/svg/.
// Aufruf (im Wurzelordner von a-sit-ci):
//   npm ci && npx playwright install chromium   (einmalig)
//   node werkzeuge/png-export.mjs
// Ergebnis: logo/png/<name>-<höhe>.png für die Höhen in HOEHEN (transparent)
//           logo/vorschau/<name>.png mit passendem Hintergrund (für das README)
//           dasselbe für EGIZ unter egiz/png/ und egiz/vorschau/, dazu egiz/symbol/egiz-symbol-<größe>.png
//           logo/teilen/og-standard.png (1200 × 630) als Vorschaubild für geteilte Links

import { readdirSync, readFileSync, mkdirSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SVG = join(ROOT, "logo/svg");
// Jede Marke hat einen Ordner mit svg/, png/ und vorschau/
const MARKEN = ["logo", "egiz"];
const HOEHEN = [64, 128, 256, 512];
// Hintergrund der Vorschaubilder: dunkel für die Fassungen Dunkel, Negativ und Weiß
const hintergrund = (name) => (/-(dunkel|negativ|weiss)$/.test(name) ? "#0B111B" : "#FFFFFF");

const browser = await chromium.launch();
const page = await browser.newPage();
let n = 0;
for (const marke of MARKEN) {
const QUELLE = join(ROOT, marke, "svg");
const PNG = join(ROOT, marke, "png");
const VORSCHAU = join(ROOT, marke, "vorschau");
mkdirSync(PNG, { recursive: true });
mkdirSync(VORSCHAU, { recursive: true });
for (const datei of readdirSync(QUELLE).filter((f) => f.endsWith(".svg")).sort()) {
  const svg = readFileSync(join(QUELLE, datei), "utf8");
  const [, , vbW, vbH] = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  for (const h of HOEHEN) {
    const w = Math.ceil((h * vbW) / vbH);
    await page.setViewportSize({ width: w, height: h });
    await page.setContent(
      `<!doctype html><html><body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${w}" height="${h}" style="display:block" `)}</body></html>`,
    );
    await page.screenshot({ path: join(PNG, `${basename(datei, ".svg")}-${h}.png`), omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
    n++;
  }
  // Vorschau: Logo 80 px hoch, 40 px Rand, feste Breite für eine ruhige Tabelle
  const name = basename(datei, ".svg");
  const vh = 80, vw = Math.ceil((vh * vbW) / vbH), pad = 40;
  await page.setViewportSize({ width: vw + 2 * pad, height: vh + 2 * pad });
  await page.setContent(
    `<!doctype html><html><body style="margin:0;padding:${pad}px;background:${hintergrund(name)}">${svg.replace("<svg ", `<svg width="${vw}" height="${vh}" style="display:block" `)}</body></html>`,
  );
  await page.screenshot({ path: join(VORSCHAU, `${name}.png`) });
  n++;
}
}

// EGIZ-Symbol: quadratische Kachel mit runden Ecken, transparenter Hintergrund
const symbol = readFileSync(join(ROOT, "egiz/symbol/egiz-symbol.svg"), "utf8");
for (const g of HOEHEN) {
  await page.setViewportSize({ width: g, height: g });
  await page.setContent(`<!doctype html><html><body style="margin:0;background:transparent">${symbol.replace("<svg ", `<svg width="${g}" height="${g}" style="display:block" `)}</body></html>`);
  await page.screenshot({ path: join(ROOT, `egiz/symbol/egiz-symbol-${g}.png`), omitBackground: true });
  n++;
}

// Vorschaubild für geteilte Links (Open Graph). Die Website nutzt es für Seiten ohne eigenes Titelbild.
const TEILEN = join(ROOT, "logo/teilen");
mkdirSync(TEILEN, { recursive: true });
const B = 1200, H = 630;
await page.setViewportSize({ width: B, height: H });
await page.setContent(`<!doctype html><html><body style="margin:0;width:${B}px;height:${H}px;background:#FFFFFF;display:flex;align-items:center;justify-content:center">
      <div style="width:640px">${readFileSync(join(SVG, "a-sit-logo.svg"), "utf8").replace("<svg ", '<svg width="100%" ')}</div></body></html>`);
await page.screenshot({ path: join(TEILEN, "og-standard.png") });
n++;

await browser.close();
console.log(`${n} PNG-Dateien geschrieben.`);
