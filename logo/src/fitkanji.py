import math, numpy as np, json
# silhouette (old 500px coords) -> logo units
pts=[(240,56),(213,76),(201,100),(199,130),(203,155),(218,171),(234,181),(239,195),(238,210),(236,225),(235,245),(236,262),(244,282),(256,298),(258,320),(248,350),(238,380),(235,410),(237,446)]
P=[((x-250.8)*2+500,(y-245.9)*2+500) for x,y in pts]
ys=np.array([p[1] for p in P]); xs=np.array([p[0] for p in P])
def silx(y): return np.interp(y, ys, xs, left=xs[0], right=xs[-1])
OVERLAP=24
def ok_box(cx,cy,h):
    # corners & edge samples
    pts=[]
    for t in np.linspace(0,2*math.pi,48,endpoint=False):
        c,s_=math.cos(t),math.sin(t); m=max(abs(c),abs(s_))
        # rounded square (corners pulled in ~12%)
        k=(abs(c)**4+abs(s_)**4)**(-0.25)/1.0
        k=min(k,1/m)*0.98 if abs(abs(c)-abs(s_))>0.3 else 0.88*1.41
        pts.append((cx+h*c*min(k,1/m), cy+h*s_*min(k,1/m)))
    for (x,y) in pts:
            r=math.hypot(x-500,y-500); a=math.degrees(math.atan2(500-y,x-500))%360
            if 169<=a<=198:
                if r>462: return False
            elif r>412: return False
    for y in np.linspace(cy-h,cy+h,15):
        if cx+h > silx(y)+OVERLAP: return False
    return True
def half(fs): return 0.46*fs + (fs*0.065+26)/2
def fit(rel, slants):
    best=None
    for sl in slants:
        for S in range(460,120,-2):
            fs=S*0.86; h=half(fs)
            found=None
            for cx in range(150,420,3):
                for cy in range(380,640,3):
                    ok=True
                    for (k,j,sc) in rel:
                        x=cx+(j*sl)*S*1.02; y=cy+j*S*1.02
                        if not ok_box(x,y,half(fs*sc)): ok=False;break
                    if ok: found=(cx,cy);break
                if found: break
            if found:
                if best is None or S>best[0]: best=(S,sl,found)
                break
    return best
res={}
two=[(0,-0.5,1),(1,0.5,1)]
three=[(0,-1,1),(1,0,1),(2,1,1)]
one=[(0,0,1)]
for k,rel,sl in [('two',two,[0,0.1,0.2]),('three',three,[0,0.08,0.15]),('one',one,[0])]:
    res[k]=fit(rel,sl); print(k,res[k])
json.dump(res,open('fit.json','w'))

# 8の字極めます: two columns, scale about its own centre and translate
def column(n_sc, xc, yc, S, gap=1.04):
    hs=[k*S*gap for k in n_sc]; y=yc-sum(hs)/2; out=[]
    for k,h in zip(n_sc,hs): out.append((xc,y+h/2,S*k)); y+=h
    return out
best=None
for S in range(124,260,2):
    found=None
    for xr in range(300,420,3):
        for gapx in (1.02,1.06,1.10):
            xl=xr-S*gapx
            for yr in range(380,600,4):
                for dy in (20,36,52):
                    g=column([.9,.8,1],xr,yr,S)+column([1,.8,.8,.8],xl,yr+dy,S)
                    if all(ok_box(x,y,half(fs)) for x,y,fs in g): found=(S,xr,yr,round(xl),yr+dy);break
                if found:break
            if found:break
        if found:break
    if found: best=found
    else: break
print('hachi',best)
