"""Erzeugt die Wortmarke „A=SIT" (Bricolage Grotesque als Pfade) in allen Varianten.

Aufruf (im Wurzelordner von a-sit-ci):
  python werkzeuge/logo-erzeugen.py <BricolageGrotesque[opsz,wdth,wght].ttf>
  python werkzeuge/logo-erzeugen.py <schrift.ttf> <skala> <datei.svg>   (nur Entwurf, z. B. 0.85)

Benötigt fonttools. Die Schrift gibt es unter
https://github.com/google/fonts/tree/main/ofl/bricolagegrotesque (SIL OFL 1.1).

Erzeugt:
  logo/svg/a-sit-logo.svg            Farbe, für helle Flächen
  logo/svg/a-sit-logo-dunkel.svg     helles Blau, für dunkle Flächen
  logo/svg/a-sit-logo-negativ.svg    Weiß mit Verlauf, für dunkle oder farbige Flächen
  logo/svg/a-sit-logo-schwarz.svg    einfarbig Schwarz
  logo/svg/a-sit-logo-weiss.svg      einfarbig Weiß
  hugo/layouts/_partials/logo.html   Logo für den Website-Header, Farben aus den Tokens der Site
Danach die PNGs neu erzeugen: node werkzeuge/png-export.mjs
"""

import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]

AXES = {"wght": 800, "opsz": 96, "wdth": 100}
LETTER_SPACING = -0.02  # em, nach jedem Zeichen
# Abstände: Die Lücke zum A (senkrecht zur Schräge gemessen) und die Lücke zum S
# sind so breit wie ein Balken – genau wie der weiße Streifen zwischen den Balken.
# Flagge nach der Vorlage von Digital Austria: Höhe 45, Breite 69,679.
# Die linken Kanten beider Balken liegen in einer Flucht. Rechts enden beide bündig.
# Die Schräge läuft parallel zur rechten Kante des A (Steigung wird aus der Schrift gelesen).
FLAG_RATIO = 69.679 / 45  # Breite : Höhe

# Farbverlauf genau wie bei Digital Austria: radial, Mittelpunkt links oben.
# Flagge dort ab (1,548 | 6), Höhe 45.
DA_ORIGIN = (1.548, 6.0)
DA_HEIGHT = 45.0
DA_CENTER = (8.267, 7.787)
DA_RADIUS = (77.9056, 77.5691)
DA_STOPS = [  # (Position, Farbe)
    (0.046, "#00A3A6"),
    (0.149, "#1C7FA0"),
    (0.275, "#3A5999"),
    (0.342, "#464B96"),
    (0.522, "#963286"),
    (0.8, "#FA0041"),
]

# Varianten: Dateiname, Farbe der Schrift, Farbe der Flagge (None = Verlauf)
VARIANTEN = [
    ("a-sit-logo.svg", "#0369A1", None),
    ("a-sit-logo-dunkel.svg", "#6CBDF0", None),
    ("a-sit-logo-negativ.svg", "#FFFFFF", None),
    ("a-sit-logo-schwarz.svg", "#000000", "#000000"),
    ("a-sit-logo-weiss.svg", "#FFFFFF", "#FFFFFF"),
]


def main(font_path: str, scale: float = 1.0, out: str | None = None) -> None:
    font = instantiateVariableFont(TTFont(font_path), AXES)
    upem = font["head"].unitsPerEm
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    def bounds(ch):
        bp = BoundsPen(gs)
        gs[cmap[ord(ch)]].draw(bp)
        return bp.bounds

    cap = bounds("H")[3]

    # Rechte Außenkante des A: oberster und unterster Punkt ganz rechts
    rp = RecordingPen()
    gs[cmap[ord("A")]].draw(rp)
    pts = [pt for _, args in rp.value for pt in args]
    y_top = max(y for _, y in pts)
    y_bot = min(y for _, y in pts)
    a_top_x = max(x for x, y in pts if y == y_top)
    a_bot_x = max(x for x, y in pts if y == y_bot)
    slope = (a_bot_x - a_top_x) / (y_top - y_bot)  # waagrecht pro Einheit Höhe (nach unten)
    _, hy0, _, hy1 = bounds("-")
    t = hy1 - hy0  # Dicke des Bindestrichs = Dicke eines Balkens
    ls = LETTER_SPACING * upem

    text_pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    x = 0.0
    all_bounds = []

    def draw(ch):
        nonlocal x
        g = gs[cmap[ord(ch)]]
        # Spiegeln: SVG zählt y nach unten
        tp = TransformPen(text_pen, (1, 0, 0, -1, x, cap))
        g.draw(tp)
        b = bounds(ch)
        all_bounds.append((x + b[0], cap - b[3], x + b[2], cap - b[1]))
        x += hmtx[cmap[ord(ch)]][0] + ls

    a_x = x
    draw("A")

    # Flagge: zwei Balken, mittig auf Versalhöhe
    tf = t * scale  # Balkendicke; 1.0 = Dicke des Bindestrichs
    h = 3 * tf
    w = FLAG_RATIO * h
    fy = cap / 2 - h / 2  # Unterkante über der Grundlinie
    top = cap - (fy + h)  # in SVG-Koordinaten
    gap_a = tf * (1 + slope**2) ** 0.5  # waagrecht, damit senkrecht zur Schräge genau t bleibt
    fx = a_x + a_top_x + slope * (top - (cap - y_top)) + gap_a
    right = fx + w

    def bar(y):
        # linke Kante folgt der gemeinsamen Schräge ab der Oberkante der Flagge
        x_top = fx + slope * (y - top)
        x_bottom = fx + slope * (y + tf - top)
        return f"M{x_top:.1f},{y:.1f}H{right:.1f}V{y + tf:.1f}H{x_bottom:.1f}Z"

    flag_d = bar(top) + bar(top + 2 * tf)

    # Verlauf auf die Größe der Flagge übertragen
    k = h / DA_HEIGHT
    gcx = fx + (DA_CENTER[0] - DA_ORIGIN[0]) * k
    gcy = top + (DA_CENTER[1] - DA_ORIGIN[1]) * k
    grad_attrs = (
        f'cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
        f'gradientTransform="matrix({DA_RADIUS[0] * k:.1f} 0 0 {DA_RADIUS[1] * k:.1f} {gcx:.1f} {gcy:.1f})"'
    )
    stops_fixed = "".join(f'<stop offset="{o:g}" stop-color="{c}"/>' for o, c in DA_STOPS)
    stops_tokens = "\n".join(
        f'      <stop class="logo__stop-{i}" offset="{o:g}"></stop>' for i, (o, _) in enumerate(DA_STOPS, 1)
    )
    all_bounds.append((fx, top, fx + w, top + h))
    x = right + tf - bounds("S")[0]  # sichtbare Lücke bis zum S = t

    for ch in "SIT":
        draw(ch)

    x0 = min(b[0] for b in all_bounds)
    y0 = min(b[1] for b in all_bounds)
    x1 = max(b[2] for b in all_bounds)
    y1 = max(b[3] for b in all_bounds)
    vb = f"{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}"
    text_d = text_pen.getCommands()

    def svg(text_fill: str, flag_fill: str | None) -> str:
        defs = "" if flag_fill else f'<defs><radialGradient id="a-sit-flagge" {grad_attrs}>{stops_fixed}</radialGradient></defs>\n'
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="A-SIT">
<title>A-SIT</title>
{defs}<path fill="{text_fill}" d="{text_d}"/>
<path fill="{flag_fill or 'url(#a-sit-flagge)'}" d="{flag_d}"/>
</svg>
"""

    if out:  # nur Entwurf: eine Datei in Farbe
        Path(out).write_text(svg(*VARIANTEN[0][1:]))
        print(f"Entwurf geschrieben: {out} (Flagge {scale:.0%})")
        return

    for name, text_fill, flag_fill in VARIANTEN:
        (ROOT / "logo/svg" / name).write_text(svg(text_fill, flag_fill))

    # Hugo-Partial: Farben kommen über CSS aus den Tokens der Site
    partial = f"""{{{{- /* Wortmarke A-SIT (Bricolage Grotesque als Pfade).
     Erzeugt von werkzeuge/logo-erzeugen.py im Repository a-sit-ci. Nicht von Hand ändern.
     Farben: --color-brand und --color-brand-flag-1..6 in der Token-Datei der Site. */ -}}}}
<svg class="logo" viewBox="{vb}" role="img" aria-label="{{{{ site.Params.marke.name }}}}" focusable="false">
  <defs>
    <radialGradient id="logo-flagge" {grad_attrs}>
{stops_tokens}
    </radialGradient>
  </defs>
  <path class="logo__text" d="{text_d}"></path>
  <path class="logo__flag" fill="url(#logo-flagge)" d="{flag_d}"></path>
</svg>
"""
    (ROOT / "hugo/layouts/_partials/logo.html").write_text(partial)
    print(f"upem={upem} cap={cap} t={t} slope={slope:.4f} flag_x={fx:.1f} viewBox={vb}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4):
        sys.exit(__doc__)
    if len(sys.argv) == 4:
        main(sys.argv[1], float(sys.argv[2]), sys.argv[3])
    else:
        main(sys.argv[1])
