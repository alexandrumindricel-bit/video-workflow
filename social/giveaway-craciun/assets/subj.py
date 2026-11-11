import cv2, numpy as np, sys
D=sys.argv[1]
im=cv2.imread('/root/.claude/uploads/ebc6ba86-1f1e-5f93-b5f5-71bbfcbb7910/14c53957-image.jpg'); H,W=im.shape[:2]
poly=np.array([(630,1330),(780,1050),(980,1050),(1060,1230),(1180,1330),(1300,1160),(1440,1120),(1560,1200),(1600,1235),(1932,1225),
 (1932,1740),(1790,1800),(1780,1880),(1700,2010),(1420,2170),(1250,2320),(1060,2260),(990,2080),(700,2060),(520,2075),(395,1880),(400,1720),(430,1540),(560,1490)],np.int32)
s=0.4; sm=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_AREA); h,w=sm.shape[:2]
P=(poly*s).astype(np.int32)
gc=np.full((h,w),cv2.GC_BGD,np.uint8)
cv2.fillPoly(gc,[P],int(cv2.GC_PR_FGD))
# definite foreground cores (scaled coords from orig)
cores=[[(820,1100),(950,1100),(960,1250),(1050,1400),(980,1600),(900,1700),(870,1900),(760,1860),(760,1680),(660,1640),(700,1420)],
       [(1000,1500),(1500,1500),(1700,1700),(1600,1950),(1300,2100),(1100,2100),(1050,1800)],
       [(470,1600),(700,1560),(720,1900),(560,2000),(460,1850)],
       [(1380,1220),(1520,1220),(1560,1480),(1400,1480)],
       [(1650,1260),(1932,1260),(1932,1640),(1700,1640)]]
for c in cores: cv2.fillPoly(gc,[(np.array(c)*s).astype(np.int32)],int(cv2.GC_FGD))
cv2.grabCut(sm,gc,None,np.zeros((1,65)),np.zeros((1,65)),6,cv2.GC_INIT_WITH_MASK)
m=((gc==1)|(gc==3)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(m)
keep=np.zeros_like(m)
for k in range(1,n):
    if st[k,4]>400: keep[l==k]=1
ff=np.pad(1-keep,1,constant_values=1); _,lb=cv2.connectedComponents(ff); holes=(lb[1:-1,1:-1]!=lb[0,0])
nh,lh,sh,_=cv2.connectedComponentsWithStats(holes.astype(np.uint8))
for k in range(1,nh):
    if sh[k,4]<600: keep[lh==k]=1
M=cv2.resize(keep.astype(np.float32),(W,H),interpolation=cv2.INTER_LINEAR)
M=cv2.GaussianBlur(M,(0,0),1.5)
np.save(f'{D}/subj.npy',M.astype(np.float16))
v=im.copy(); sel=M>0.5; v[~sel]=(v[~sel]*0.25+np.array([0,140,0])*0.75).astype(np.uint8)
cv2.imwrite(f'{D}/crop.jpg',cv2.resize(v[1000:2400,300:1932],None,fx=.5,fy=.5))
