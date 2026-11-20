// Erzeugt das Symbol (Favicon, App-Symbol) aus logo/svg/a-sit-logo.svg:
// das „A“ der Wortmarke und der Anfang der Flagge auf einer weißen Kachel.
// Aufruf (im Wurzelordner von a-sit-ci, nach logo-erzeugen.py):
//   node werkzeuge/symbol-erzeugen.mjs
// Ergebnis: logo/symbol/a-sit-symbol.svg und a-sit-symbol-<größe>.png (Kachel mit runden Ecken)
//           logo/symbol/web/favicon.svg, favicon.ico (16, 32, 48 px), apple-touch-icon.png (180 px, ohne Rundung)
// Die Website bindet logo/symbol/web/ als Wurzel ein (hugo.toml).

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const ZIEL = join(ROOT, "logo/symbol");
const WEB = join(ZIEL, "web");

const KACHEL = 64;          // Seitenlänge der Kachel (viewBox)
const RAND = 6;             // Rand links und rechts
const RUNDUNG = 12;         // Eckenradius der Kachel
const FLAGGE_ENDE = 1010;   // rechtes Ende der gekürzten Flagge (Einheiten des Logos)
const VERLAUF_RADIUS = 440; // kleinerer Radius: der ganze Verlauf passt auf die kurze Flagge
const FLAECHE = "#FFFFFF";
const PNG_GROESSEN = [64, 128, 256, 512];
const ICO_GROESSEN = [16, 32, 48];

// Bausteine aus dem Logo lesen
const logo = readFileSync(join(ROOT, "logo/svg/a-sit-logo.svg"), "utf8");
const [textPfad, flaggePfad] = [...logo.matchAll(/<path fill="([^"]+)" d="([^"]+)"/g)].map((m) => ({ fill: m[1], d: m[2] }));
// Das „A“ sind die ersten zwei Teilpfade der Wortmarke (Umriss und Querbalken).
const a = textPfad.d.split("Z").slice(0, 2).join("Z") + "Z";
const links = Number(a.match(/M(-?[\d.]+)/)[1]); // linke Kante: Startpunkt des Umrisses
// Flagge: zwei Balken „Mx,yHx2Vy2Hx3Z“. Das rechte Ende wird gekürzt.
const balken = flaggePfad.d.split("Z").filter(Boolean).map((t) => t.match(/-?[\d.]+/g).map(Number));
const flagge = balken.map(([x1, y1, , y2, x3]) => `M${x1},${y1}H${FLAGGE_ENDE}V${y2}H${x3}Z`).join("");
const stops = logo.match(/<stop [\s\S]*?(?=<\/radialGradient>)/)[0];
const [, , , , cx, cy] = logo.match(/gradientTransform="matrix\(([^)]+)\)"/)[1].split(/\s+/).map(Number);
const hoehe = Math.max(...textPfad.d.split("Z")[0].match(/-?[\d.]+/g).map(Number).filter((_, i) => i % 2 === 1));

const s = (KACHEL - 2 * RAND) / (FLAGGE_ENDE - links);
const tx = RAND - links * s;
const ty = (KACHEL - hoehe * s) / 2;
const r = (n) => Number(n.toFixed(4));

function symbol(rundung) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${KACHEL} ${KACHEL}">
<defs><radialGradient id="a-sit-symbol-flagge" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(${VERLAUF_RADIUS} 0 0 ${VERLAUF_RADIUS} ${cx} ${cy})">${stops}</radialGradient></defs>
<rect width="${KACHEL}" height="${KACHEL}"${rundung ? ` rx="${rundung}"` : ""} fill="${FLAECHE}"/>
<g transform="translate(${r(tx)} ${r(ty)}) scale(${r(s)})"><path fill="${textPfad.fill}" d="${a}"/><path fill="url(#a-sit-symbol-flagge)" d="${flagge}"/></g>
</svg>
`;
}

mkdirSync(WEB, { recursive: true });
const rund = symbol(RUNDUNG);
writeFileSync(join(ZIEL, "a-sit-symbol.svg"), rund);
writeFileSync(join(WEB, "favicon.svg"), rund);

const browser = await chromium.launch();
const page = await browser.newPage();
async function png(svg, px, transparent) {
  await page.setViewportSize({ width: px, height: px });
  await page.setContent(`<!doctype html><html><body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${px}" height="${px}" style="display:block" `)}</body></html>`);
  return page.screenshot({ omitBackground: transparent, clip: { x: 0, y: 0, width: px, height: px } });
}
for (const px of PNG_GROESSEN) writeFileSync(join(ZIEL, `a-sit-symbol-${px}.png`), await png(rund, px, true));
// iOS rundet die Ecken selbst: volle Fläche ohne Rundung und ohne Transparenz
writeFileSync(join(WEB, "apple-touch-icon.png"), await png(symbol(0), 180, false));

// favicon.ico: Behälter mit PNG-Bildern (von allen aktuellen Browsern unterstützt)
const bilder = [];
for (const px of ICO_GROESSEN) bilder.push({ px, daten: await png(rund, px, true) });
await browser.close();
const kopf = Buffer.alloc(6 + 16 * bilder.length);
kopf.writeUInt16LE(0, 0); kopf.writeUInt16LE(1, 2); kopf.writeUInt16LE(bilder.length, 4);
let versatz = kopf.length;
bilder.forEach(({ px, daten }, i) => {
  const p = 6 + 16 * i;
  kopf.writeUInt8(px, p); kopf.writeUInt8(px, p + 1); kopf.writeUInt8(0, p + 2); kopf.writeUInt8(0, p + 3);
  kopf.writeUInt16LE(1, p + 4); kopf.writeUInt16LE(32, p + 6);
  kopf.writeUInt32LE(daten.length, p + 8); kopf.writeUInt32LE(versatz, p + 12);
  versatz += daten.length;
});
writeFileSync(join(WEB, "favicon.ico"), Buffer.concat([kopf, ...bilder.map((b) => b.daten)]));
console.log(`Symbol geschrieben: SVG, ${PNG_GROESSEN.length} PNG, favicon.ico (${ICO_GROESSEN.join(", ")} px), apple-touch-icon.png.`);
