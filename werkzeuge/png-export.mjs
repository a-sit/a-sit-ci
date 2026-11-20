// Erzeugt PNG-Dateien mit transparentem Hintergrund aus allen SVGs in logo/svg/.
// Aufruf (im Wurzelordner von a-sit-ci):
//   npm ci && npx playwright install chromium   (einmalig)
//   node werkzeuge/png-export.mjs
// Ergebnis: logo/png/<name>-<höhe>.png für die Höhen in HOEHEN (transparent)
//           logo/vorschau/<name>.png mit passendem Hintergrund (für das README)
//           logo/teilen/og-standard.png (1200 × 630) als Vorschaubild für geteilte Links

import { readdirSync, readFileSync, mkdirSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SVG = join(ROOT, "logo/svg");
const PNG = join(ROOT, "logo/png");
const VORSCHAU = join(ROOT, "logo/vorschau");
const HOEHEN = [64, 128, 256, 512];
// Hintergrund der Vorschaubilder je Fassung
const HINTERGRUND = { "a-sit-logo": "#FFFFFF", "a-sit-logo-dunkel": "#0B111B", "a-sit-logo-negativ": "#0B111B", "a-sit-logo-schwarz": "#FFFFFF", "a-sit-logo-weiss": "#0B111B" };

mkdirSync(PNG, { recursive: true });
mkdirSync(VORSCHAU, { recursive: true });
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
  // Vorschau: Logo 80 px hoch, 40 px Rand, feste Breite für eine ruhige Tabelle
  const name = basename(datei, ".svg");
  const vh = 80, vw = Math.ceil((vh * vbW) / vbH), pad = 40;
  await page.setViewportSize({ width: vw + 2 * pad, height: vh + 2 * pad });
  await page.setContent(
    `<!doctype html><html><body style="margin:0;padding:${pad}px;background:${HINTERGRUND[name] ?? "#FFFFFF"}">${svg.replace("<svg ", `<svg width="${vw}" height="${vh}" style="display:block" `)}</body></html>`,
  );
  await page.screenshot({ path: join(VORSCHAU, `${name}.png`) });
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
