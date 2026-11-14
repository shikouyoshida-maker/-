import base64, math, sys, json
import cv2

SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'

# --- illustration: upscale cleaned raster, centre on inner ring centre ---
src = cv2.imread(f'{SP}/clean.png', 0)
S = 4
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
CAP = 46                                   # cap height of ring text

def arc(r, a0, a1, sweep):
    # angles in degrees, math convention (0 = right, CCW positive, y up)
    x0, y0 = C + r * math.cos(math.radians(a0)), C - r * math.sin(math.radians(a0))
    x1, y1 = C + r * math.cos(math.radians(a1)), C - r * math.sin(math.radians(a1))
    large = 1 if abs(a1 - a0) > 180 else 0
    return f'M{x0:.2f},{y0:.2f} A{r},{r} 0 {large},{sweep} {x1:.2f},{y1:.2f}'

TOP_SPAN = 156   # degrees
BOT_SPAN = 142
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
        out.append((ch, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, size))
    return out

k1 = P(138, 198); k2 = P(170, 342)   # original 究 / 極 centres
VARIANTS = {
    'kyukyoku': line('究極', (260, 385), (330, 690), 290),
    'anzen':    line('安全', (260, 385), (330, 690), 290),
    'takumi':   line('匠', (300, 495), (300, 495), 395),
    'yoshidajuku': line('吉田塾', (290, 290), (345, 712), 210),
    'monkasei':    line('門下生', (290, 290), (345, 712), 210),
    'menkyokaiden': line('免許', (382, 300), (388, 470), 168) + line('皆伝', (222, 445), (228, 615), 168),
    'hachinoji': line('8の字', (372, 255), (386, 545), 168) + line('極めます', (212, 345), (244, 712), 124),
}
LABEL = {
    'kyukyoku': '究極', 'anzen': '安全', 'takumi': '匠', 'yoshidajuku': '吉田塾',
    'monkasei': '門下生', 'menkyokaiden': '免許皆伝', 'hachinoji': '8の字極めます',
}

def svg(key):
    kanji_o = ''.join(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{s}" class="kj kjo" stroke-width="{s*0.065+14:.1f}">{ch}</text>'
        for ch, x, y, s in VARIANTS[key])
    kanji = ''.join(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{s}" class="kj" stroke-width="{s*0.065:.1f}">{ch}</text>'
        for ch, x, y, s in VARIANTS[key])
    return f'''<svg id="{key}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1000 1000" width="1000" height="1000">
<defs>
  <clipPath id="clip-{key}"><circle cx="{C}" cy="{C}" r="{R_IMG}"/></clipPath>
  <path id="tp-{key}" d="{top_path}"/>
  <path id="bp-{key}" d="{bot_path}"/>
</defs>
<circle cx="{C}" cy="{C}" r="{R_OUT_OUT}" fill="#fff"/>
<image href="data:image/png;base64,{b64}" x="{P(0,0)[0]:.2f}" y="{P(0,0)[1]:.2f}" width="{src.shape[1]*K}" height="{src.shape[0]*K}" clip-path="url(#clip-{key})" preserveAspectRatio="none"/>
{kanji_o}
<g fill="none" stroke="#000">
  <circle cx="{C}" cy="{C}" r="{(R_RING_IN+R_RING_OUT)/2}" stroke-width="{R_RING_OUT-R_RING_IN}"/>
  <circle cx="{C}" cy="{C}" r="{(R_OUT_IN+R_OUT_OUT)/2}" stroke-width="{R_OUT_OUT-R_OUT_IN}"/>
</g>
<text class="ring"><textPath href="#tp-{key}" textLength="{top_len:.1f}" lengthAdjust="spacing">KYUKYOKUNO</textPath></text>
<text class="ring"><textPath href="#bp-{key}" textLength="{bot_len:.1f}" lengthAdjust="spacing">SAFETY&#160;&#160;RIDING</textPath></text>
{kanji}
</svg>'''

html = f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,900&family=Yuji+Boku&display=block" rel="stylesheet">
<style>
body{{margin:0;background:transparent}}
svg{{display:block}}
.ring{{font-family:'Archivo';font-stretch:125%;font-weight:900;font-size:{CAP*2.04:.1f}px;fill:#000;stroke:#fff;stroke-width:5;paint-order:stroke;stroke-linejoin:round}}
.kj{{font-family:'Yuji Boku';fill:#000;stroke:#000;stroke-linejoin:round;text-anchor:middle;dominant-baseline:central}}
.kjo{{stroke:#fff;fill:#fff}}
</style></head><body>
{''.join(svg(k) for k in VARIANTS)}
</body></html>'''
open(f'{SP}/logos.html', 'w').write(html)
json.dump(LABEL, open(f'{SP}/labels.json', 'w'), ensure_ascii=False)
print('ok', top_len, bot_len)
