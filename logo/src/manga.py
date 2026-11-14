import cv2, numpy as np, math
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
S = 4
src = cv2.imread(f'{SP}/clean_nobg.png', 0)
H, W = src.shape
up = cv2.resize(src, (W*S, H*S), interpolation=cv2.INTER_CUBIC).astype(np.float32)
sm = cv2.bilateralFilter(up, 9, 40, 6)

# --- background mask (same silhouette as nobg.py), at 4x ---
pts = [(240,56),(213,76),(201,100),(199,130),(203,155),(218,171),(234,181),(239,195),(238,210),(236,225),(235,245),(236,262),(244,282),(256,298),(258,320),(248,350),(238,380),(235,410),(237,446)]
cx, cy, R = 250.8, 245.9, 215
a0 = math.atan2(pts[-1][1]-cy, pts[-1][0]-cx); a1 = math.atan2(pts[0][1]-cy, pts[0][0]-cx)
A = np.linspace(a0, a1 + 2*math.pi if a1 < a0 else a1, 60)
poly = np.array(pts + [(cx+R*math.cos(a), cy+R*math.sin(a)) for a in A], np.float32)
bg = np.zeros((H*S, W*S), np.uint8)
cv2.fillPoly(bg, [np.round(poly*S).astype(np.int32)], 255)
bg = cv2.erode(bg, np.ones((9, 9), np.uint8)) > 0

# --- 3-tone manga: solid black / screentone / white ---
out = np.full_like(sm, 255)
black = sm < 85
tone = (sm >= 85) & (sm < 205)
# 45-degree dot screen; dot radius grows with darkness
yy, xx = np.mgrid[:H*S, :W*S].astype(np.float32)
P = 9.0
u = (xx + yy) / math.sqrt(2); v = (xx - yy) / math.sqrt(2)
du = (u % P) - P/2; dv = (v % P) - P/2
d = np.sqrt(du*du + dv*dv)
dark = np.clip((205 - sm) / 120, 0, 1)           # 0..1 within tone band
rad = 0.9 + dark * (P * 0.42)
out[tone & (d < rad)] = 0
out[black] = 0

# --- ink lines: adaptive threshold on detail, thickened slightly ---
lines = cv2.adaptiveThreshold(cv2.GaussianBlur(up, (0, 0), 1.2).astype(np.uint8), 255,
                              cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 14) == 0
lines = cv2.dilate(lines.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
out[lines & ~bg] = 0
out[bg] = 255

# --- focus lines (集中線) in the background, aimed at the face ---
fx, fy = 262*S, 200*S
rng = np.random.default_rng(7)
fl = np.zeros_like(out, np.uint8)
n = 150
for i in range(n):
    ang = (i + rng.uniform(-.35, .35)) * 2*math.pi / n
    r0 = rng.uniform(150, 260) * S / 4 * 4 / 4 * 1.0 + 70*S
    r1 = 420*S
    w = rng.uniform(2.0, 7.0)
    p0 = (fx + r0*math.cos(ang), fy + r0*math.sin(ang))
    p1 = (fx + r1*math.cos(ang), fy + r1*math.sin(ang))
    # tapered wedge: thin at the inner end, wider outside
    nx, ny = -math.sin(ang), math.cos(ang)
    quad = np.array([(p0[0], p0[1]),
                     (p1[0] + nx*w*S, p1[1] + ny*w*S),
                     (p1[0] - nx*w*S, p1[1] - ny*w*S)], np.int32)
    cv2.fillPoly(fl, [quad], 255)
out[(fl > 0) & bg] = 0

cv2.imwrite(f'{SP}/manga.png', out.clip(0, 255).astype(np.uint8))
cv2.imwrite(f'{SP}/manga_view.png', cv2.resize(out.astype(np.uint8), (1000, int(1000*H/W)), interpolation=cv2.INTER_AREA))
