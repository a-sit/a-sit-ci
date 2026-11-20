// Erzeugt PNG-Dateien mit transparentem Hintergrund aus allen SVGs in logo/svg/.
// Aufruf (im Wurzelordner von a-sit-ci):
//   npm ci && npx playwright install chromium   (einmalig)
//   node werkzeuge/png-export.mjs
// Ergebnis: logo/png/<name>-<höhe>.png für die Höhen in HOEHEN.

import { readdirSync, readFileSync, mkdirSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SVG = join(ROOT, "logo/svg");
const PNG = join(ROOT, "logo/png");
const HOEHEN = [64, 128, 256, 512];

mkdirSync(PNG, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage();
let n = 0;
for (const datei of readdirSync(SVG).filter((f) => f.endsWith(".svg")).sort()) {
  const svg = readFileSync(join(SVG, datei), "utf8");
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
}
await browser.close();
console.log(`${n} PNG-Dateien geschrieben.`);
