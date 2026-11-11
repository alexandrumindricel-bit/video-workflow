import cv2, numpy as np, sys
D=sys.argv[1]; LOGO=sys.argv[2]; rng=np.random.default_rng(5)
im=cv2.imread(f'{D}/hero-mr.jpg'); H,W=im.shape[:2]
f=im.astype(np.int32); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
roi=np.zeros((H,W),np.uint8); roi[1450:1650,340:530]=1
m=(((hsv[...,2]>50)|((f[...,0]-f[...,2]>12)&(hsv[...,2]>30)))&(roi>0)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(m)
keep=np.zeros_like(m)
for k in range(1,n):
    if st[k,4]>150: keep[l==k]=1
pts=np.argwhere(keep>0)[:,::-1].astype(np.int32)
hull=cv2.convexHull(pts); flag=np.zeros_like(m); cv2.fillPoly(flag,[hull],1)
flag=cv2.dilate(flag,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))
(cx,cy),(w,h),ang=cv2.minAreaRect(pts.astype(np.float32)); print('flag',cx,cy,w,h,ang)
# 1) remove flag
clean=cv2.inpaint(im,flag*255,25,cv2.INPAINT_TELEA).astype(np.float32)
sm=cv2.GaussianBlur(clean,(0,0),5); fm=cv2.GaussianBlur(flag.astype(np.float32),(0,0),3)[...,None]
clean=clean*(1-fm)+(sm+rng.normal(0,2.4,(H,W,1)).astype(np.float32))*fm
# 2) logo: key out black, crop
lg=cv2.imread(LOGO).astype(np.float32)
la=np.clip((lg.max(2)-40)/60,0,1)
ys,xs=np.where(la>0.05); lg=lg[ys.min():ys.max()+1,xs.min():xs.max()+1]; la=la[ys.min():ys.max()+1,xs.min():xs.max()+1]
# size: same width as the flag; rotation: follow the back's slope (same as the flag, ~ -8 deg visually)
tw=int(sys.argv[4]) if len(sys.argv)>4 else 150; s=tw/lg.shape[1]
lg=cv2.resize(lg,None,fx=s,fy=s,interpolation=cv2.INTER_AREA); la=cv2.resize(la,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
lh,lw=la.shape; rot=float(sys.argv[3]) if len(sys.argv)>3 else -8
M=cv2.getRotationMatrix2D((lw/2,lh/2),-rot,1.0); M[0,2]+=cx-lw/2; M[1,2]+=cy-lh/2
L=cv2.warpAffine(lg,M,(W,H),flags=cv2.INTER_LINEAR); A=cv2.warpAffine(la,M,(W,H),flags=cv2.INTER_LINEAR)
# printed-on-fabric look: muted like the old flag/text print (brightest ~120), fabric folds through, slight wear
gray=cv2.cvtColor(np.clip(clean,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
fold=((gray-cv2.GaussianBlur(gray,(0,0),20))/25.0)[...,None]
ink=L*0.5+np.array([8,8,10],np.float32)       # dim + slight cool cast from the overcast light
ink=ink*(1+0.35*fold)+rng.normal(0,3.5,(H,W,1)).astype(np.float32)
cr=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),1.3); cr/=cr.std()
A=cv2.GaussianBlur(A,(0,0),0.8)*np.clip(1-0.5*np.clip(cr-1.4,0,None),0,1)
A=(A*0.95)[...,None]
out=clean*(1-A)+ink*A
cv2.imwrite(f'{D}/hero-mr2.jpg',np.clip(out,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,94])
cv2.imwrite(f'{D}/crop.jpg',np.clip(out,0,255).astype(np.uint8)[1400:1750,250:700])
