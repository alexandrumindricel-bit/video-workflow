import cv2, numpy as np, sys
D=sys.argv[1]; rng=np.random.default_rng(4)
im=cv2.imread('/root/.claude/uploads/ebc6ba86-1f1e-5f93-b5f5-71bbfcbb7910/14c53957-image.jpg'); H,W=im.shape[:2]
f=im.astype(np.float32)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(np.float32); Hh,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
subj=np.load(f'{D}/subj.npy').astype(np.float32)
green=((Hh>28)&(Hh<95)&(S>45)).astype(np.float32)
green=cv2.GaussianBlur(green,(0,0),2)
subj=np.clip(subj-green*(subj<0.999),0,1)
# ground caught inside the subject mask (beside/under the wheels): give it back to the snow
zone=np.zeros((H,W),np.uint8)
for poly in [[(380,1480),(520,1480),(470,1700),(420,2000),(380,2000)],[(640,1960),(1060,1960),(1060,2120),(640,2120)],
             [(1650,1760),(1932,1700),(1932,2100),(1600,2100)],[(480,1480),(640,1480),(600,1560),(470,1600)]]:
    cv2.fillPoly(zone,[np.array(poly,np.int32)],1)
ground_like=~(((S>110)&((Hh<22)|(Hh>165)))|(V<55)|((S<30)&(V>200)))
subj=np.where((zone>0)&ground_like,0,subj)
hz=np.zeros((H,W),bool); hz[1080:1240,740:868]=True
skin=(Hh<25)&(S>40)&(V>110)
subj=np.where(hz&~skin,0,subj)
subj=cv2.morphologyEx(subj,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
subj=cv2.GaussianBlur(subj,(0,0),1.2)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
L=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
# --- regions ---
skyc=((Hh>95)&(Hh<130)&(V>120)) | ((S<40)&(V>185))
skyc=skyc.astype(np.uint8); skyc[yy>1300]=0
pad=np.pad(skyc,((1,0),(0,0)),constant_values=1); _,lab=cv2.connectedComponents(pad,connectivity=4)
sky=(lab[1:,:]==lab[0,0]).astype(np.float32)
sky=cv2.GaussianBlur(cv2.morphologyEx(sky,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)),(0,0),1.5)
# ground: below the field edge line (fence base ~y 1420 on the left, ~1400 on the right)
gl=1415+0*xx
ground=np.clip((yy-gl)/25,0,1)
trees=np.clip(1-sky-ground,0,1)
bgw=(1-subj)
# --- sky: overcast winter grey, keep cloud texture ---
Ls=cv2.GaussianBlur(L,(0,0),1.0)
skyv=np.clip(150+0.42*Ls,0,255)
gy=np.clip(yy/1300,0,1)[...,None]
skycol=np.dstack([skyv*1.03,skyv*1.0,skyv*0.97])*(1-0.10*gy)
# --- trees: dark wintry foliage + snow on lit tops ---
Lb=cv2.GaussianBlur(L,(0,0),6)
hi=np.clip((cv2.GaussianBlur(L,(0,0),1.5)-Lb)/16,0,1)
lum=np.clip((L-40)/150,0,1)
snowamt=np.clip(0.10+1.25*hi*(0.4+lum)+0.55*lum**1.6,0,1)
snowamt=cv2.GaussianBlur(snowamt,(0,0),1.6)
dark=np.dstack([L*0.42+22,L*0.50+26,L*0.40+16])   # dark evergreen
haze=np.clip((1450-yy)/650,0,1)[...,None]*0.28     # distant hills lighter
snowc=np.array([238,236,232],np.float32)
treecol=dark*(1-snowamt[...,None])+snowc*snowamt[...,None]*(0.88+0.12*lum[...,None])
treecol=treecol*(1-haze)+np.array([214,212,208],np.float32)*haze
# --- ground: snow blanket, stones/grass poking through slightly, keep shadows ---
Lg=cv2.GaussianBlur(L,(0,0),30); shade=np.clip(Lg/np.percentile(Lg[1500:,:],70),0.35,1.15)
tex=(L-cv2.GaussianBlur(L,(0,0),3))/40
n=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),6); n/=n.std()
poke=np.clip((Lb-L)/35-0.35+0.25*n,0,1)*0.22         # darkest bits (stones, grass) show through a bit
base=np.array([244,240,236],np.float32)
n2=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),40); n2/=n2.std()
gcol=base*(0.94+0.025*n[...,None]+0.035*n2[...,None]+0.025*tex[...,None])
# blue-ish shadow: lower B less
sh=shade[...,None]
gcol=gcol*np.dstack([sh**0.85,sh**0.95,sh**1.05])
gcol=gcol*(1-poke[...,None])+f*0.75*poke[...,None]
# perspective: far ground smoother
# --- compose background ---
bg=skycol*sky[...,None]+treecol*trees[...,None]+gcol*ground[...,None]
# contact shadow under the ATV/rider on the snow
cs=cv2.GaussianBlur((subj>0.5).astype(np.float32),(0,0),25); cs=np.roll(cs,30,axis=0)
bg=bg*(1-0.32*cs[...,None]*ground[...,None])
# snow touching the tyre bottoms
out=f*subj[...,None]+bg*bgw[...,None]
# --- grade subjects to winter light: cooler, slightly less warm saturation ---
gs=np.dstack([out[...,0]*1.05+4,out[...,1]*1.0,out[...,2]*0.95])
out=out*(1-subj[...,None])+gs*subj[...,None]
# global: soft contrast, cool, film grain
out=out*0.96+8
out+=rng.normal(0,2.2,(H,W,1)).astype(np.float32)
cv2.imwrite(f'{D}/hero-winter.jpg',np.clip(out,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,93])
cv2.imwrite(f'{D}/crop.jpg',cv2.resize(np.clip(out,0,255).astype(np.uint8),None,fx=.35,fy=.35))
