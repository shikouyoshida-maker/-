import cv2, numpy as np, math
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
im = cv2.imread(f'{SP}/clean.png', 0).astype(np.float32)
# 1) whiten everything left of the person's silhouette
pts = [(240,56),(213,76),(201,100),(199,130),(203,155),(218,171),(234,181),(239,195),(238,210),(236,225),(235,245),(236,262),(244,282),(256,298),(258,320),(248,350),(238,380),(235,410),(237,446)]
cx, cy, R = 250.8, 245.9, 215
a0 = math.atan2(pts[-1][1]-cy, pts[-1][0]-cx); a1 = math.atan2(pts[0][1]-cy, pts[0][0]-cx)
A = np.linspace(a0, a1 + 2*math.pi if a1 < a0 else a1, 60)
poly = np.array(pts + [(cx+R*math.cos(a), cy+R*math.sin(a)) for a in A], np.float32)
S = 4
m = np.zeros((im.shape[0]*S, im.shape[1]*S), np.uint8)
cv2.fillPoly(m, [np.round(poly*S).astype(np.int32)], 255)
m = cv2.resize(m, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_AREA).astype(np.float32)/255
line = np.zeros_like(m, np.uint8)
cv2.polylines(line, [np.round(np.array(pts)).astype(np.int32)], False, 255, 10)
m[(line > 0) & (im < 120)] = 0
m = cv2.GaussianBlur(m, (0,0), 1.0)
im = im*(1-m) + 255*m
# 2) above / through the visor: whiten only light-gray blotches, keep lines and their halo
Y, X = np.mgrid[:im.shape[0], :im.shape[1]]
zone = ((X>=198)&(X<=412)&(Y>=48)&(Y<=135)) | ((X>=368)&(X<=415)&(Y>=100)&(Y<=175))
dark = cv2.dilate((im < 160).astype(np.uint8), np.ones((5,5), np.uint8)) > 0
g = zone & (im >= 160) & (im <= 240) & ~dark
g = cv2.morphologyEx(g.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2,2), np.uint8)) > 0
mm = cv2.GaussianBlur(g.astype(np.float32), (0,0), 0.8)
im = im*(1-mm) + 255*mm
cv2.imwrite(f'{SP}/clean_nobg.png', im.clip(0,255).astype(np.uint8))
c = cv2.cvtColor(im.clip(0,255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
cv2.imwrite(f'{SP}/topzoom2.png', cv2.resize(c[45:190,190:450], None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC))
