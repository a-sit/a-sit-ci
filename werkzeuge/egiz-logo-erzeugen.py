"""Erzeugt das EGIZ-Logo (E-Government Innovationszentrum) in allen Fassungen.

Aufruf (im Wurzelordner von a-sit-ci):
  python werkzeuge/egiz-logo-erzeugen.py <BricolageGrotesque[opsz,wdth,wght].ttf>

Benötigt fonttools. Schrift und Verlauf sind dieselben wie beim A-SIT-Logo (werkzeuge/logo-erzeugen.py).

Aufbau: Das E besteht aus drei Balken. Der obere und der untere tragen den Verlauf der Flagge.
Der mittlere ist kürzer und hat die Farbe der Schrift. Danach folgt „GIZ“.

Erzeugt in egiz/svg/:
  egiz-logo.svg, -dunkel, -negativ, -schwarz, -weiss               Logo
  egiz-logo-unterzeile.svg, -dunkel, -negativ, -schwarz, -weiss    Logo mit ausgeschriebenem Namen
und in egiz/symbol/:
  egiz-symbol.svg                                                  das E auf einer weißen Kachel
und in hugo/layouts/_partials/:
  logo-egiz.html                                                   Logo für den Header der Website (Farben aus den Tokens)
Danach die PNGs neu erzeugen: node werkzeuge/png-export.mjs
"""

import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "egiz"

AXES = {"wght": 800, "opsz": 96, "wdth": 100}  # Wortmarke, wie A-SIT
AXES_UNTERZEILE = {"wght": 500, "opsz": 24, "wdth": 100}
LETTER_SPACING = -0.02  # em, nach jedem Zeichen
NAME = "E-Government Innovationszentrum"

SLOPE = 1 / 3  # Schräge der linken Kante, wie die Flagge im A-SIT-Logo
E_BREITE = 560  # Breite des E (Einheiten der Schrift, 1000 pro Geviert)
MITTE_KUERZER = 1.5  # der mittlere Balken ist um so viele Balkendicken kürzer
ABSTAND_G = 70  # Lücke zwischen E und G
ABSTAND_UNTERZEILE = 110  # Lücke zwischen Grundlinie und Oberkante der Unterzeile
RAND = 14  # Luft oben und unten (Überhang des G)

# Farbverlauf von Digital Austria (siehe logo-erzeugen.py)
FLAG_RATIO = 69.679 / 45
DA_ORIGIN, DA_HEIGHT, DA_CENTER, DA_RADIUS = (1.548, 6.0), 45.0, (8.267, 7.787), (77.9056, 77.5691)
DA_STOPS = [(0.046, "#00A3A6"), (0.149, "#1C7FA0"), (0.275, "#3A5999"), (0.342, "#464B96"), (0.522, "#963286"), (0.8, "#FA0041")]

# Fassungen: Endung, Farbe der Schrift, Farbe der Balken (None = Verlauf), Farbe der Unterzeile
FASSUNGEN = [
    ("", "#0369A1", None, "#566176"),
    ("-dunkel", "#6CBDF0", None, "#9AA4B5"),
    ("-negativ", "#FFFFFF", None, "#FFFFFF"),
    ("-schwarz", "#000000", "#000000", "#000000"),
    ("-weiss", "#FFFFFF", "#FFFFFF", "#FFFFFF"),
]

# Symbol: Kachel wie beim A-SIT-Symbol
KACHEL, KACHEL_RAND, KACHEL_RUNDUNG = 64, 15, 12


def zahl(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Schrift:
    def __init__(self, pfad, achsen):
        self.font = instantiateVariableFont(TTFont(pfad), achsen)
        self.gs, self.cmap, self.hmtx = self.font.getGlyphSet(), self.font.getBestCmap(), self.font["hmtx"]
        self.upem = self.font["head"].unitsPerEm
        self.cap = self.grenzen("H")[3]

    def grenzen(self, ch):
        bp = BoundsPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(bp)
        return bp.bounds

    def breite(self, text):
        return sum(self.hmtx[self.cmap[ord(c)]][0] for c in text)

    def setze(self, text, x, grundlinie, k=1.0, ls=0.0):
        """Text als Pfad. x = sichtbare linke Kante. Liefert (Pfad, sichtbare rechte Kante)."""
        pen = SVGPathPen(self.gs, ntos=zahl)
        x -= self.grenzen(text[0])[0] * k
        rechts = x
        for ch in text:
            g = self.cmap[ord(ch)]
            self.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, grundlinie)))
            if self.grenzen(ch):  # Leerzeichen haben keinen Umriss
                rechts = x + self.grenzen(ch)[2] * k
            x += (self.hmtx[g][0] + ls * self.upem) * k
        return pen.getCommands(), rechts


def balken(y, dicke, rechts):
    """Ein Balken mit schräger linker Kante. Die Schräge beginnt bei x = 0 an der Oberkante des E."""
    return f"M{zahl(SLOPE * y)},{zahl(y)}H{zahl(rechts)}V{zahl(y + dicke)}H{zahl(SLOPE * (y + dicke))}Z"


def verlauf_lage(breite):
    """Lage des Verlaufs von Digital Austria, auf die Breite des E gestreckt (Rot am rechten Rand)."""
    k = breite / FLAG_RATIO / DA_HEIGHT
    cx, cy = (DA_CENTER[0] - DA_ORIGIN[0]) * k, (DA_CENTER[1] - DA_ORIGIN[1]) * k
    return (
        'cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
        f'gradientTransform="matrix({DA_RADIUS[0] * k:.1f} 0 0 {DA_RADIUS[1] * k:.1f} {cx:.1f} {cy:.1f})"'
    )


def verlauf(gid, breite):
    """Verlauf mit festen Farben, für die eigenständigen SVG-Dateien."""
    stopps = "".join(f'<stop offset="{o:g}" stop-color="{c}"/>' for o, c in DA_STOPS)
    return f'<radialGradient id="{gid}" {verlauf_lage(breite)}>{stopps}</radialGradient>'


def hugo_partial(viewbox, d_aussen, d_schrift):
    """Hugo-Partial für den Header: Farben kommen über CSS aus den Tokens der Site."""
    stopps = "\n".join(f'      <stop class="logo__stop-{i}" offset="{o:g}"></stop>' for i, (o, _) in enumerate(DA_STOPS, 1))
    return f"""{{{{- /* Logo EGIZ (E aus drei Balken, GIZ in Bricolage Grotesque als Pfade).
     Erzeugt von werkzeuge/egiz-logo-erzeugen.py im Repository a-sit-ci. Nicht von Hand ändern.
     Gleiche Höhe und Grundlinie wie die Wortmarke A-SIT (logo.html).
     Farben: --color-brand und --color-brand-flag-1..6 in der Token-Datei der Site. */ -}}}}
<svg class="logo logo--egiz" viewBox="{viewbox}" role="img" aria-label="EGIZ" focusable="false">
  <defs>
    <radialGradient id="logo-egiz-flagge" {verlauf_lage(E_BREITE)}>
{stopps}
    </radialGradient>
  </defs>
  <path class="logo__flag" fill="url(#logo-egiz-flagge)" d="{d_aussen}"></path>
  <path class="logo__text" d="{d_schrift}"></path>
</svg>
"""


def main(font_path: str) -> None:
    fett = Schrift(font_path, AXES)
    leicht = Schrift(font_path, AXES_UNTERZEILE)
    cap = fett.cap
    b = cap / 5  # Balkendicke: die Arme des E sind in der Schrift ein Fünftel der Versalhöhe dick

    d_aussen = balken(0, b, E_BREITE) + balken(4 * b, b, E_BREITE)
    d_mitte = balken(2 * b, b, E_BREITE - MITTE_KUERZER * b)
    d_giz, rechts = fett.setze("GIZ", E_BREITE + ABSTAND_G, cap, ls=LETTER_SPACING)

    # Unterzeile: läuft über die volle Breite des Logos
    k = rechts / (leicht.breite(NAME) - leicht.grenzen(NAME[0])[0])
    grundlinie = cap + ABSTAND_UNTERZEILE + leicht.cap * k
    d_name, _ = leicht.setze(NAME, 0, grundlinie, k)

    def svg(schrift, balkenfarbe, unterzeile):
        defs = "" if balkenfarbe else f'<defs>{verlauf("egiz-flagge", E_BREITE)}</defs>\n'
        unten = (grundlinie if unterzeile else cap) + RAND
        label = f"EGIZ – {NAME}" if unterzeile else "EGIZ"
        name = f'\n<path fill="{unterzeile}" d="{d_name}"/>' if unterzeile else ""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-RAND} {rechts:.0f} {unten + RAND:.0f}" role="img" aria-label="{label}">
<title>{label}</title>
{defs}<path fill="{balkenfarbe or 'url(#egiz-flagge)'}" d="{d_aussen}"/>
<path fill="{schrift}" d="{d_mitte}{d_giz}"/>{name}
</svg>
"""

    (ZIEL / "svg").mkdir(parents=True, exist_ok=True)
    for endung, schrift, balkenfarbe, unterzeile in FASSUNGEN:
        (ZIEL / "svg" / f"egiz-logo{endung}.svg").write_text(svg(schrift, balkenfarbe, None))
        (ZIEL / "svg" / f"egiz-logo-unterzeile{endung}.svg").write_text(svg(schrift, balkenfarbe, unterzeile))

    # Hugo-Partial: Logo ohne Unterzeile, gleicher Ausschnitt wie egiz-logo.svg
    (ROOT / "hugo/layouts/_partials/logo-egiz.html").write_text(
        hugo_partial(f"0 {-RAND} {rechts:.0f} {cap + 2 * RAND:.0f}", d_aussen, d_mitte + d_giz)
    )

    # Symbol: das E mittig auf einer weißen Kachel
    s = (KACHEL - 2 * KACHEL_RAND) / cap
    ox = (KACHEL - E_BREITE * s) / 2
    (ZIEL / "symbol").mkdir(parents=True, exist_ok=True)
    (ZIEL / "symbol" / "egiz-symbol.svg").write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {KACHEL} {KACHEL}" role="img" aria-label="EGIZ">
<title>EGIZ</title>
<defs>{verlauf("egiz-flagge", E_BREITE)}</defs>
<rect width="{KACHEL}" height="{KACHEL}" rx="{KACHEL_RUNDUNG}" fill="#FFFFFF"/>
<g transform="translate({ox:.2f} {KACHEL_RAND}) scale({s:.5f})"><path fill="url(#egiz-flagge)" d="{d_aussen}"/><path fill="{FASSUNGEN[0][1]}" d="{d_mitte}"/></g>
</svg>
""")
    print(f"cap={cap} balken={b} breite={rechts:.0f} unterzeile k={k:.4f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
