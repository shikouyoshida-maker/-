import cv2, numpy as np, math
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
photo = cv2.imread(f'{SP}/photo/src.png')
fg = cv2.imread(f'{SP}/photo/fg.png', 0)

# --- clean leftover green foliage from the mask (below the visor only) ---
b, g, r = [photo[:, :, i].astype(int) for i in range(3)]
green = (g > r + 12) & (g > b + 5)
yy = np.mgrid[:fg.shape[0], :fg.shape[1]][0]
fg[(green) & (yy > 900)] = 0
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); fg = (lab == big).astype(np.uint8) * 255
inv = cv2.bitwise_not(fg); n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < 20000: fg[lab == i] = 255
fg = cv2.GaussianBlur(fg, (0, 0), 1.5)

# --- warp photo into logo space: 2000x2000 px = 1000x1000 logo units ---
A = np.load(f'{SP}/photo/old_to_photo.npy')            # old-sketch px -> photo px
OC = np.array([250.8, 245.9])
# out px q -> old = (q - 1000)/4 + OC
Q = np.array([[0.25, 0, OC[0] - 250], [0, 0.25, OC[1] - 250], [0, 0, 1]])
out_to_photo = (A @ Q)[:2]
N = 2000
ph = cv2.warpAffine(photo, out_to_photo, (N, N), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderValue=(255, 255, 255))
m = cv2.warpAffine(fg, out_to_photo, (N, N), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP).astype(np.float32) / 255

# --- flatten colours (cel look), then luminance ---
flat = cv2.pyrMeanShiftFiltering(ph, 6, 18)
flat = cv2.bilateralFilter(flat, 9, 30, 5)
L = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY).astype(np.float32)
G0 = cv2.cvtColor(ph, cv2.COLOR_BGR2GRAY).astype(np.float32)

# --- ink lines: XDoG on lightly smoothed gray ---
gs = cv2.bilateralFilter(G0.astype(np.uint8), 7, 25, 5).astype(np.float32) / 255
s1, kk, tau = 1.4, 1.6, 0.985
D = cv2.GaussianBlur(gs, (0, 0), s1) - tau * cv2.GaussianBlur(gs, (0, 0), s1 * kk)
ink = D < -0.008
ink = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
# drop tiny specks
n, lab, st, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8))
keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 25
ink = keep[lab]

# --- tones ---
out = np.full((N, N), 255, np.float32)
yy, xx = np.mgrid[:N, :N].astype(np.float32)
def dots(P, rad):
    u = (xx + yy) / math.sqrt(2); v = (xx - yy) / math.sqrt(2)
    du = (u % P) - P / 2; dv = (v % P) - P / 2
    return np.sqrt(du * du + dv * dv) < rad
black = L < 50
tone_d = (L >= 50) & (L < 82)
tone_l = (L >= 82) & (L < 106)
out[tone_l & dots(8.0, 1.7)] = 0
out[tone_d & dots(8.0, 3.0)] = 0
out[black] = 0
out[ink] = 0
# silhouette outline (pen line around the figure)
mb = (m > 0.5).astype(np.uint8)
edge = cv2.dilate(mb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) - cv2.erode(mb, np.ones((3, 3), np.uint8))
out[edge > 0] = 0

# --- background: white with focus lines toward the face ---
bgm = m < 0.5
out = out * m + 255 * (1 - m)
out[edge > 0] = 0
fx, fy = 1000 + 4 * (262 - OC[0]), 1000 + 4 * (200 - OC[1])
rng = np.random.default_rng(7)
fl = np.zeros((N, N), np.uint8)
n = 170
for i in range(n):
    ang = (i + rng.uniform(-.35, .35)) * 2 * math.pi / n
    r0 = rng.uniform(330, 520); r1 = 1500
    w = rng.uniform(3, 10)
    p0 = (fx + r0 * math.cos(ang), fy + r0 * math.sin(ang))
    p1 = (fx + r1 * math.cos(ang), fy + r1 * math.sin(ang))
    nx, ny = -math.sin(ang), math.cos(ang)
    tri = np.array([p0, (p1[0] + nx * w, p1[1] + ny * w), (p1[0] - nx * w, p1[1] - ny * w)], np.int32)
    cv2.fillPoly(fl, [tri], 255)
bg_hard = cv2.erode(bgm.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
out[(fl > 0) & bg_hard] = 0

cv2.imwrite(f'{SP}/photo/manga_logo.png', out.clip(0, 255).astype(np.uint8))
cv2.imwrite(f'{SP}/photo/manga_view.png', cv2.resize(out.clip(0, 255).astype(np.uint8), (1000, 1000), interpolation=cv2.INTER_AREA))
