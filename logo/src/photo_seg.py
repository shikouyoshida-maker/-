import cv2, numpy as np
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
im = cv2.imread(f'{SP}/photo/src.png')
H, W = im.shape[:2]
# rough person outline in photo pixels (traced from the grid)
person = np.array([
    (815, 330), (1000, 315), (1380, 300), (1500, 370), (1700, 500), (1800, 650), (1830, 800),
    (1815, 1000), (1770, 1130), (1840, 1190), (1880, 1290), (1880, 1500), (1760, 1750),
    (1500, 1930), (790, 1930), (800, 1600), (900, 1480), (1060, 1330), (1100, 1250),
    (1000, 1210), (955, 1120), (950, 1040), (962, 940), (972, 840), (960, 790), (995, 720),
    (930, 690), (850, 610), (815, 470)], np.int32)
mask = np.full((H, W), cv2.GC_BGD, np.uint8)
circ = np.zeros((H, W), np.uint8); cv2.circle(circ, (1024, 1024), 896, 255, -1)
poly = np.zeros((H, W), np.uint8); cv2.fillPoly(poly, [person], 255)
grow = cv2.dilate(poly, np.ones((61, 61), np.uint8))
shrink = cv2.erode(poly, np.ones((61, 61), np.uint8))
mask[(grow > 0) & (circ > 0)] = cv2.GC_PR_BGD
mask[(poly > 0) & (circ > 0)] = cv2.GC_PR_FGD
mask[(shrink > 0) & (circ > 0)] = cv2.GC_FGD
# work at half resolution for speed
s = 0.5
sm = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
mk = cv2.resize(mask, (sm.shape[1], sm.shape[0]), interpolation=cv2.INTER_NEAREST)
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(sm, mk, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = ((mk == cv2.GC_FGD) | (mk == cv2.GC_PR_FGD)).astype(np.uint8) * 255
fg = cv2.resize(fg, (W, H), interpolation=cv2.INTER_LINEAR)
fg = (cv2.GaussianBlur(fg, (0, 0), 2) > 127).astype(np.uint8) * 255
# keep largest component, fill holes
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); fg = (lab == big).astype(np.uint8) * 255
inv = cv2.bitwise_not(fg); n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] < 20000: fg[lab == i] = 255
cv2.imwrite(f'{SP}/photo/fg.png', fg)
view = im.copy(); view[fg == 0] = (view[fg == 0] * 0.25 + np.array([0, 0, 180]) * 0.75).astype(np.uint8)
cv2.polylines(view, [person], True, (255, 0, 0), 3)
cv2.imwrite(f'{SP}/photo/seg_view.png', cv2.resize(view, (900, 900)))
