import cv2, numpy as np, math
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
N = 2000
yy, xx = np.mgrid[:N, :N].astype(np.float32)
ph = cv2.imread(f'{SP}/photo/warped.png')
def smooth(mask, s=6):
    return cv2.GaussianBlur(mask.astype(np.float32), (0, 0), s) > 0.5
def dots(P, rad):
    u = (xx + yy) / math.sqrt(2); v = (xx - yy) / math.sqrt(2)
    du = (u % P) - P / 2; dv = (v % P) - P / 2
    return np.sqrt(du * du + dv * dv) < rad
# ================= character pass =================
out = cv2.imread(f'{SP}/photo/char2_base.png', 0)
# face region: clear clutter, keep one soft shadow shape
face = np.array([(1015,700),(1100,640),(1220,655),(1265,740),(1280,880),(1235,1000),(1140,1075),(1000,1085),(958,1000),(968,900),(985,820),(1012,770)], np.int32)
fm = np.zeros((N, N), np.uint8); cv2.fillPoly(fm, [face], 1)
fm = cv2.GaussianBlur(fm.astype(np.float32), (0, 0), 6) > 0.5
fm = cv2.erode(fm.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
Ls = cv2.GaussianBlur(cv2.cvtColor(ph, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 14)
shadow = smooth(Ls < 100, 10) & fm
base_black = (out == 0).astype(np.uint8)
n_, lab_, st_, _ = cv2.connectedComponentsWithStats(base_black)
isdot = np.zeros(n_, bool); isdot[1:] = st_[1:, cv2.CC_STAT_AREA] < 70
out[isdot[lab_] & fm] = 255
out[shadow & dots(12.0, 4.0)] = 0

def stroke(pts, w0, w1=None, w2=None):
    """tapered brush stroke through points (Catmull-Rom smoothed)."""
    pts = np.array(pts, np.float32)
    P = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
        for t in np.linspace(0, 1, 20, endpoint=False):
            t2, t3 = t * t, t * t * t
            P.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    P.append(pts[-1]); P = np.array(P)
    n = len(P)
    w1 = w0 if w1 is None else w1; w2 = w0 if w2 is None else w2
    w0, w1, w2 = w0 * 1.5, w1 * 1.5, w2 * 1.5
    for i in range(n):
        t = i / (n - 1)
        w = (w0 * (1 - 2 * t) + w1 * 2 * t) if t < .5 else (w1 * (2 - 2 * t) + w2 * (2 * t - 1))
        cv2.circle(out, tuple(np.round(P[i]).astype(int)), max(1, int(round(w / 2))), 0, -1, cv2.LINE_AA)

# eyebrows (bold, determined)
stroke([(1098, 676), (1130, 662), (1170, 656), (1205, 660)], 6, 16, 8)
stroke([(1022, 728), (1045, 716), (1062, 712)], 4, 9, 5)
# near eye: narrowed, looking up — upper lid heavy, lower lid light
stroke([(1138, 735), (1155, 724), (1178, 721), (1200, 728)], 5, 13, 6)
stroke([(1150, 742), (1172, 744), (1194, 738)], 2, 4, 2)
cv2.ellipse(out, (1170, 731), (9, 6), 0, 0, 360, 0, -1, cv2.LINE_AA)     # pupil glint area
cv2.circle(out, (1166, 728), 3, 255, -1, cv2.LINE_AA)
# far eye
stroke([(1028, 778), (1043, 770), (1060, 768)], 3, 8, 3)
# nose: bridge shadow + nostril + underside
# mouth: firm line with corner
stroke([(978, 935), (1010, 940), (1045, 944), (1068, 948)], 3, 8, 4)
stroke([(1000, 958), (1030, 962)], 2, 4, 2)
# cheek / jaw accent lines

cv2.imwrite(f'{SP}/photo/char_logo.png', out)
cv2.imwrite(f'{SP}/photo/char_face.png', out[550:1200, 880:1400])
cv2.imwrite(f'{SP}/photo/char_view.png', cv2.resize(out, (1000, 1000), interpolation=cv2.INTER_AREA))
