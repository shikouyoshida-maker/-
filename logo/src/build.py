import base64, math, sys, json
import cv2

SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'

# --- illustration: upscale cleaned raster, centre on inner ring centre ---
import os
STYLE = os.environ.get('STYLE', 'sketch')
src = cv2.imread(f'{SP}/clean_nobg.png', 0)
S = 4
if STYLE == 'manga':
    up = cv2.imread(f'{SP}/manga.png', 0)
else:
    up = cv2.resize(src, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
cv2.imwrite(f'{SP}/clean_up.png', up)
b64 = base64.b64encode(open(f'{SP}/clean_up.png', 'rb').read()).decode()

C = 500.0                    # new centre
OC = (250.8, 245.9)          # inner-ring centre in original
K = 2.0                      # original px -> new units
def P(x, y): return ((x - OC[0]) * K + C, (y - OC[1]) * K + C)

R_IMG = 381          # illustration clip (inner edge of inner ring)
R_RING_IN, R_RING_OUT = 381, 406
R_OUT_IN, R_OUT_OUT = 466, 495
BAND_MID = (R_RING_OUT + R_OUT_IN) / 2   # 436
LS = 22
CAP = 43                                   # cap height of ring text

def arc(r, a0, a1, sweep):
    # angles in degrees, math convention (0 = right, CCW positive, y up)
    x0, y0 = C + r * math.cos(math.radians(a0)), C - r * math.sin(math.radians(a0))
    x1, y1 = C + r * math.cos(math.radians(a1)), C - r * math.sin(math.radians(a1))
    large = 1 if abs(a1 - a0) > 180 else 0
    return f'M{x0:.2f},{y0:.2f} A{r},{r} 0 {large},{sweep} {x1:.2f},{y1:.2f}'

TOP_SPAN = 200   # degrees
BOT_SPAN = 200
r_top = BAND_MID - CAP / 2          # baseline of top text (letters point outward)
r_bot = BAND_MID + CAP / 2          # baseline of bottom text (letters point inward)
top_path = arc(r_top, 90 + TOP_SPAN / 2, 90 - TOP_SPAN / 2, 1)      # clockwise over top
bot_path = arc(r_bot, 270 - BOT_SPAN / 2, 270 + BOT_SPAN / 2, 0)    # counter-clockwise under bottom
top_len = math.radians(TOP_SPAN) * r_top
bot_len = math.radians(BOT_SPAN) * r_bot

# --- kanji layouts: list of (char, x, y, size) in new coords ---
def line(chars, a, b, size):
    n = len(chars)
    out = []
    for i, ch in enumerate(chars):
        t = 0.5 if n == 1 else i / (n - 1)
        out.append((ch, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, round(size * 0.86)))
    return out

k1 = P(138, 198); k2 = P(170, 342)   # original 究 / 極 centres
OVER = {'yoshidajuku', 'hachinoji'}
def column(chars, xc, yc, S, scales=None, gap=1.04):
    scales = scales or [1] * len(chars)
    hs = [k * S * gap for k in scales]
    y = yc - sum(hs) / 2
    out = []
    for ch, k, h in zip(chars, scales, hs):
        out.append((ch, xc, y + h / 2, round(S * k)))
        y += h
    return out
VARIANTS = {
    'kyukyoku': line('究極', (272, 390), (334, 690), 282),
    'anzen':    line('安全', (272, 390), (334, 690), 282),
    'takumi':   line('匠', (300, 495), (300, 495), 395),
    'yoshidajuku': column('吉田', 336, 468, 176) + column('塾', 128, 534, 194),
    'monka':    line('門下', (272, 390), (334, 690), 282),
    'kaiden':   line('皆伝', (272, 390), (334, 690), 282),
    'hachinoji': column('8の字', 354, 478, 124, [.9, .8, 1]) + column('極めます', 208, 514, 124, [1, .8, .8, .8]),
}
LABEL = {
    'kyukyoku': '究極', 'anzen': '安全', 'takumi': '匠', 'yoshidajuku': '吉田塾',
    'monka': '門下', 'kaiden': '皆伝', 'hachinoji': '8の字極めます',
}

def svg(key):
    V = VARIANTS[key]
    def layer(cls, extra, w, dx=0, dy=0):
        return ''.join(
            f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" font-size="{s}" class="kj {cls}" stroke-width="{s*0.065+w(s):.1f}"{extra}>{ch}</text>'
            for ch, x, y, s in V)
    glow = layer('kjg', '', lambda s: min(s*0.42, 80))
    shadow = layer('kjs', '', lambda s: 26, 8, 8)
    edge = layer('kje', '', lambda s: 26)
    kanji_o = layer('kjo', '', lambda s: 16)
    kanji = layer('', '', lambda s: -s*0.065)
    stack = f'<g opacity="0.55">{shadow}</g>{edge}{kanji_o}'
    under, over = ('', stack) if key in OVER else (f'<g clip-path="url(#clipo-{key})">{stack}</g>', '')
    return f'''<svg id="{key}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1000 1000" width="1000" height="1000">
<defs>
  <filter id="blur-{key}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="22"/></filter>
  <clipPath id="clipo-{key}"><circle cx="{C}" cy="{C}" r="{R_RING_OUT-2}"/></clipPath>
  <clipPath id="clip-{key}"><circle cx="{C}" cy="{C}" r="{R_IMG}"/></clipPath>
  <path id="tp-{key}" d="{top_path}"/>
  <path id="bp-{key}" d="{bot_path}"/>
</defs>
<circle cx="{C}" cy="{C}" r="{R_OUT_OUT}" fill="#fff"/>
<image href="data:image/png;base64,{b64}" x="{P(0,0)[0]:.2f}" y="{P(0,0)[1]:.2f}" width="{src.shape[1]*K}" height="{src.shape[0]*K}" clip-path="url(#clip-{key})" preserveAspectRatio="none"/>
<g clip-path="url(#clip-{key})" filter="url(#blur-{key})" opacity="0.9">{glow}</g>
{under}
<g fill="none" stroke="#000">
  <circle cx="{C}" cy="{C}" r="{(R_RING_IN+R_RING_OUT)/2}" stroke-width="{R_RING_OUT-R_RING_IN}"/>
  <circle cx="{C}" cy="{C}" r="{(R_OUT_IN+R_OUT_OUT)/2}" stroke-width="{R_OUT_OUT-R_OUT_IN}"/>
</g>
<text class="ring"><textPath href="#tp-{key}" startOffset="50%" text-anchor="middle">KYUKYOKUNO</textPath></text>
<text class="ring"><textPath href="#bp-{key}" startOffset="50%" text-anchor="middle">SAFETY&#160;RIDING</textPath></text>
{over}{kanji}
</svg>'''

html = f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,900&family=Noto+Serif+JP:wght@900&display=block" rel="stylesheet">
<style>
body{{margin:0;background:transparent}}
svg{{display:block}}
.ring{{font-family:'Archivo';font-stretch:125%;font-weight:900;font-size:{CAP/0.70:.1f}px;letter-spacing:{LS}px;fill:#000;stroke:#fff;stroke-width:5;paint-order:stroke;stroke-linejoin:round}}
.kj{{font-family:'Noto Serif JP';font-weight:900;fill:#000;stroke:#000;stroke-linejoin:round;text-anchor:middle;dominant-baseline:central}}
.kjo{{stroke:#fff;fill:#fff}}
.kjg{{stroke:#fff;fill:#fff}}
.kjs,.kje{{stroke:#000;fill:#000}}
</style></head><body>
{''.join(svg(k) for k in VARIANTS)}
</body></html>'''
open(f'{SP}/logos.html' if STYLE == 'sketch' else f'{SP}/logos_{STYLE}.html', 'w').write(html)
json.dump(LABEL, open(f'{SP}/labels.json', 'w'), ensure_ascii=False)
print('ok', top_len, bot_len)
