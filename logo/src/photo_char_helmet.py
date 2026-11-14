import cv2, numpy as np
SP = '/tmp/claude-0/-home-user--/67da5411-496e-5744-8c63-efbe275d2058/scratchpad'
ch = cv2.imread(f'{SP}/photo/char_logo.png', 0)      # character version
v1 = cv2.imread(f'{SP}/photo/manga_logo.png', 0)     # fine-tone version (helmet look the user likes)
helmet = np.array([(780, 300), (1000, 270), (1450, 300), (1720, 470), (1880, 700), (1920, 950), (1860, 1110),
                   (1720, 1190), (1560, 1185), (1440, 1120), (1330, 1020), (1320, 900), (1310, 760),
                   (1250, 650), (1120, 625), (1000, 640), (930, 690), (860, 660), (800, 520)], np.int32)
hm = np.zeros(ch.shape, np.uint8); cv2.fillPoly(hm, [helmet], 255)
A = np.load(f'{SP}/photo/old_to_photo.npy'); OC = np.array([250.8, 245.9])
Q = np.array([[0.25, 0, OC[0] - 250], [0, 0.25, OC[1] - 250], [0, 0, 1]]); M = (A @ Q)[:2]
fg = cv2.imread(f'{SP}/photo/fg.png', 0)
m = cv2.warpAffine(fg, M, (2000, 2000), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP) > 127
inner = cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))) > 0
out = np.where((hm > 0) & inner, v1, ch)
cv2.imwrite(f'{SP}/photo/char_helmet_logo.png', out)
cv2.imwrite(f'{SP}/photo/char_helmet_view.png', cv2.resize(out, (1000, 1000), interpolation=cv2.INTER_AREA))
