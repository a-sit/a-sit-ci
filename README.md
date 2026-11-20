# A-SIT Corporate Identity

Logo, Farben und Werkzeuge der Marke A-SIT. Die Website [technology.a-sit.at](https://technology.a-sit.at) bindet dieses Repository als Git-Submodul ein und nutzt immer den hier freigegebenen Stand.

## Das Logo

Die Wortmarke „A=SIT“ ist in Bricolage Grotesque (ExtraBold) gesetzt und in Pfade umgewandelt. Zwischen A und SIT steht eine Flagge aus zwei Balken. Sie ist an das Logo von Digital Austria angelehnt:

- Die Balken sind so dick wie ein Bindestrich der Schrift.
- Die Flagge sitzt mittig auf Höhe der Großbuchstaben.
- Die linken Kanten beider Balken liegen in einer Flucht. Die Schräge läuft parallel zur rechten Kante des A (Steigung 1 : 3).
- Die Lücke zum A, die Lücke zum S und der Streifen zwischen den Balken sind je so breit wie ein Balken.
- Seitenverhältnis und Farbverlauf der Flagge stammen aus dem Logo von Digital Austria.

## Dateien

| Datei | Einsatz |
|---|---|
| `logo/svg/a-sit-logo.svg` | Standard. Für weiße und helle Flächen. |
| `logo/svg/a-sit-logo-dunkel.svg` | Für dunkle Flächen, Schrift in hellem Blau. |
| `logo/svg/a-sit-logo-negativ.svg` | Für dunkle oder farbige Flächen, Schrift in Weiß. |
| `logo/svg/a-sit-logo-schwarz.svg` | Einfarbig, z. B. für Stempel, Fax und Schwarz-Weiß-Druck. |
| `logo/svg/a-sit-logo-weiss.svg` | Einfarbig weiß, z. B. für Prägung oder Fotos. |
| `logo/png/<name>-<höhe>.png` | Alle Varianten als PNG mit transparentem Hintergrund, 64, 128, 256 und 512 px hoch. |
| `logo/entwuerfe/` | Nicht freigegebene Entwürfe mit kleinerer Flagge (85 % und 75 %). Nur zum Vergleich. |
| `farben/farben.css`, `farben/farben.json` | Farben als CSS-Variablen und als JSON. |
| `hugo/layouts/_partials/logo.html` | Logo für den Website-Header. Die Farben kommen aus den Tokens der Site. |

Verwende nach Möglichkeit SVG. PNG nur dort, wo SVG nicht geht.

## Farben

| Name | Wert | Einsatz | Kontrast |
|---|---|---|---|
| A-SIT-Blau | `#0369A1` | Wortmarke auf hellen Flächen | 5,9 : 1 auf Weiß |
| A-SIT-Blau hell | `#6CBDF0` | Wortmarke auf dunklen Flächen | 9,2 : 1 auf `#0B111B` |
| Flagge 1 | `#00A3A6` | Verlauf, Stopp bei 4,6 % | |
| Flagge 2 | `#1C7FA0` | Verlauf, Stopp bei 14,9 % | |
| Flagge 3 | `#3A5999` | Verlauf, Stopp bei 27,5 % | |
| Flagge 4 | `#464B96` | Verlauf, Stopp bei 34,2 % | |
| Flagge 5 | `#963286` | Verlauf, Stopp bei 52,2 % | |
| Flagge 6 | `#FA0041` | Verlauf, Stopp bei 80 % | |

Der Verlauf ist radial. Sein Mittelpunkt liegt links oben an der Flagge. Die genaue Lage steht in `werkzeuge/logo-erzeugen.py`.

## Regeln für den Einsatz

- Das Logo nicht verzerren, drehen, umfärben oder mit Effekten versehen.
- Schrift und Flagge immer gemeinsam verwenden. Die Abstände nicht ändern.
- Rund um das Logo frei lassen: mindestens die Höhe der Flagge.
- Mindestgröße: 16 px Höhe am Bildschirm. [Platzhalter: Mindestgröße im Druck festlegen]
- Auf hellen Flächen die Standardfassung verwenden, auf dunklen Flächen die dunkle oder die negative Fassung.
- Auf unruhigen Fotos die einfarbige Fassung verwenden.

## Logo neu erzeugen

Alle Dateien entstehen aus dem Generator. Nicht von Hand ändern.

Einmalig:

```bash
python3 -m venv .venv && .venv/bin/pip install fonttools
npm ci && npx playwright install chromium
```

Die Schrift Bricolage Grotesque (variable TTF) gibt es bei [Google Fonts](https://github.com/google/fonts/tree/main/ofl/bricolagegrotesque).

```bash
.venv/bin/python werkzeuge/logo-erzeugen.py <BricolageGrotesque[opsz,wdth,wght].ttf>
node werkzeuge/png-export.mjs
```

Entwurf mit anderer Flaggengröße (z. B. 85 %):

```bash
.venv/bin/python werkzeuge/logo-erzeugen.py <schrift.ttf> 0.85 logo/entwuerfe/a-sit-logo-flagge-85.svg
```

## Einbindung in die Website

`hugo.toml` macht dieses Repository zu einem Hugo-Theme-Baustein. Die Website bindet es als Submodul unter `themes/a-sit-ci` ein und stellt es vor das Basis-Theme: `theme = ["a-sit-ci", "asit-base"]`.

Ein neuer Stand hier erreicht die Website über einen Pull Request von Dependabot in a-sit-web. Dort wird er geprüft und freigegeben.

## Lizenzen

Die Schrift Bricolage Grotesque steht unter der SIL Open Font License 1.1 (`lizenzen/OFL-BricolageGrotesque.txt`). Das Logo selbst ist Eigentum von A-SIT.
