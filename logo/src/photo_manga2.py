"""Stronger manga treatment of the original photo (bold ink, 3 flat values, coarse tone)."""
import cv2, numpy as np, math
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
photo = cv2.imread(f'{SP}/photo/src.png')
fg = cv2.imread(f'{SP}/photo/fg.png', 0)

# --- mask cleanup (same as v1) ---
b, g, r = [photo[:, :, i].astype(int) for i in range(3)]
green = (g > r + 12) & (g > b + 5)
yy0 = np.mgrid[:fg.shape[0], :fg.shape[1]][0]
fg[green & (yy0 > 900)] = 0
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
fg = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8) * 255
inv = cv2.bitwise_not(fg); n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < 20000: fg[lab == i] = 255
fg = cv2.GaussianBlur(fg, (0, 0), 1.5)

# --- warp into logo space ---
A = np.load(f'{SP}/photo/old_to_photo.npy')
OC = np.array([250.8, 245.9])
Q = np.array([[0.25, 0, OC[0] - 250], [0, 0.25, OC[1] - 250], [0, 0, 1]])
SC, AX, AY = 0.89, 620.0, 1000.0          # shrink figure about a point at the bottom of the circle (logo units)
T = np.array([[1/SC, 0, 2*AX*(1 - 1/SC)], [0, 1/SC, 2*AY*(1 - 1/SC)], [0, 0, 1]])
M = (A @ Q @ T)[:2]
N = 2000
ph = cv2.warpAffine(photo, M, (N, N), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderValue=(255, 255, 255))
m = cv2.warpAffine(fg, M, (N, N), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP).astype(np.float32) / 255
mb = (m > 0.5).astype(np.uint8)
yy, xx = np.mgrid[:N, :N].astype(np.float32)

# --- strong flattening ---
flat = cv2.pyrMeanShiftFiltering(ph, 10, 28)
flat = cv2.medianBlur(flat, 7)
L = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY).astype(np.float32)

# --- clean helmet: fill sticker holes inside the white shell ---
white = (L > 140).astype(np.uint8)
closed = cv2.morphologyEx(white, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
stickers = (closed > 0) & (white == 0) & (xx > 2*AX + SC*(1330-2*AX)) & (yy < 2*AY + SC*(1080-2*AY)) & (yy > 2*AY + SC*(560-2*AY))
stickers = cv2.dilate(stickers.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
L[stickers] = 200

# --- three flat values ---
BLACK, TONE = 62, 104
black = L < BLACK
tone = (L >= BLACK) & (L < TONE)
black = cv2.morphologyEx(black.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
tone = cv2.morphologyEx(tone.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)) > 0

def dots(P, rad):
    u = (xx + yy) / math.sqrt(2); v = (xx - yy) / math.sqrt(2)
    du = (u % P) - P / 2; dv = (v % P) - P / 2
    return np.sqrt(du * du + dv * dv) < rad

# visor: bluish tinted plastic -> light tone
B_, G_, R_ = [ph[:, :, i].astype(int) for i in range(3)]
visor = (B_ - R_ > 14) & (mb > 0) & (yy < 2*AY + SC*(740-2*AY)) & (xx < 2*AX + SC*(1380-2*AX)) & (L >= TONE)
visor = cv2.morphologyEx(visor.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)) > 0
out = np.full((N, N), 255, np.float32)
out[visor & dots(11.0, 2.4)] = 0
out[tone & dots(11.0, 3.6)] = 0
out[black] = 0

# --- bold ink: region boundaries of the flat image + XDoG detail ---
gs = cv2.GaussianBlur(L / 255, (0, 0), 1.0)
D = cv2.GaussianBlur(gs, (0, 0), 1.8) - 0.98 * cv2.GaussianBlur(gs, (0, 0), 1.8 * 1.6)
ink = (D < -0.010)
edges = cv2.Canny(flat, 40, 110) > 0
ink = ink | edges
ink[stickers] = False
ink = cv2.dilate(ink.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))) > 0
n, lab, st, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8))
keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 80
ink = keep[lab]
# helmet shell: drop short strokes (shading noise) inside bright white areas
shell = cv2.erode((closed > 0).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
n, lab, st, _ = cv2.connectedComponentsWithStats((ink & shell).astype(np.uint8))
small = np.zeros(n, bool); small[1:] = st[1:, cv2.CC_STAT_AREA] < 1500
ink[small[lab] & shell & (xx > 2*AX + SC*(1250-2*AX))] = False
out[ink] = 0

# --- gloss highlights on black parts (white streaks where the photo is bright inside black areas) ---
G0 = cv2.cvtColor(ph, cv2.COLOR_BGR2GRAY).astype(np.float32)
hl = (G0 > 120) & cv2.erode(black.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
hl = cv2.morphologyEx(hl.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
out[hl] = 255

# --- composite on white + thick silhouette outline ---
out = out * m + 255 * (1 - m)
edge = cv2.dilate(mb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) - cv2.erode(mb, np.ones((3, 3), np.uint8))
out[edge > 0] = 0

# --- bold focus lines ---
fx, fy = 1000 + 4 * (262 - OC[0]), 1000 + 4 * (200 - OC[1])
fx, fy = 2*AX + SC*(fx - 2*AX), 2*AY + SC*(fy - 2*AY)
rng = np.random.default_rng(11)
fl = np.zeros((N, N), np.uint8)
n = 120
for i in range(n):
    ang = (i + rng.uniform(-.4, .4)) * 2 * math.pi / n
    r0 = rng.uniform(300, 470); r1 = 1500
    w = rng.uniform(6, 16)
    p0 = (fx + r0 * math.cos(ang), fy + r0 * math.sin(ang))
    p1 = (fx + r1 * math.cos(ang), fy + r1 * math.sin(ang))
    nx, ny = -math.sin(ang), math.cos(ang)
    tri = np.array([p0, (p1[0] + nx * w, p1[1] + ny * w), (p1[0] - nx * w, p1[1] - ny * w)], np.int32)
    cv2.fillPoly(fl, [tri], 255)
bg_hard = cv2.erode((1 - mb), np.ones((25, 25), np.uint8)) > 0
out[(fl > 0) & bg_hard] = 0

res = out.clip(0, 255).astype(np.uint8)
cv2.imwrite(f'{SP}/photo/manga2_logo.png', res)
cv2.imwrite(f'{SP}/photo/manga2_view.png', cv2.resize(res, (1000, 1000), interpolation=cv2.INTER_AREA))
cv2.imwrite(f'{SP}/photo/face2_zoom.png', res[500:1300, 850:1650])

# --- person-only RGBA (for breaking out over the inner ring) ---
_a = cv2.dilate((m > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) * 255
_o = out.clip(0, 255).astype(np.uint8)
cv2.imwrite(f'{SP}/photo/manga2_person.png', cv2.merge([_o, _o, _o, _a]))
