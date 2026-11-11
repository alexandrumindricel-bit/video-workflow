import cv2, numpy as np, sys
im=cv2.imread(sys.argv[1]); H,W=im.shape[:2]; out_path=sys.argv[2]
s=900/max(H,W); sm=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_AREA); h,w=sm.shape[:2]
hsv=cv2.cvtColor(sm,cv2.COLOR_BGR2HSV)
gc=np.full((h,w),cv2.GC_PR_BGD,np.uint8)
red=(hsv[...,1]>120)&(hsv[...,2]>90)
blk=cv2.morphologyEx((hsv[...,2]<45).astype(np.uint8),cv2.MORPH_OPEN,np.ones((9,9),np.uint8))>0
g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY).astype(np.float32)
tex=cv2.GaussianBlur(np.abs(cv2.Laplacian(g,cv2.CV_32F,ksize=3)),(0,0),3)
fg=red|blk
gc[cv2.dilate(fg.astype(np.uint8),np.ones((5,5),np.uint8))>0]=cv2.GC_PR_FGD
gc[cv2.erode(fg.astype(np.uint8),np.ones((7,7),np.uint8))>0]=cv2.GC_FGD
gc[(hsv[...,1]<40)&(hsv[...,2]>60)&(hsv[...,2]<200)&(tex>=9)]=cv2.GC_BGD
b=8; gc[:b]=gc[-b:]=cv2.GC_BGD; gc[:,:b]=gc[:,-b:]=cv2.GC_BGD
cv2.grabCut(sm,gc,None,np.zeros((1,65)),np.zeros((1,65)),6,cv2.GC_INIT_WITH_MASK)
m=((gc==1)|(gc==3)).astype(np.uint8)
m=cv2.resize(m,(W,H),interpolation=cv2.INTER_NEAREST)
def biggest(m):
    n,l,st,_=cv2.connectedComponentsWithStats(m); k=1+np.argmax(st[1:,4]); return (l==k).astype(np.uint8)
def fillholes(m):
    ff=np.pad(1-m,1,constant_values=1); _,lab=cv2.connectedComponents(ff); return (m|(lab[1:-1,1:-1]!=lab[0,0])).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))  # grout lines
m=fillholes(biggest(m))
# white FOX letters on the glove (touch the edge, so not a hole)
HSV=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); V=HSV[...,2].astype(int); S=HSV[...,1].astype(int)
ys,xs=np.where(m>0); x0,y0=xs.min(),ys.min(); bw,bh=xs.max()-x0,ys.max()-y0
zone=np.zeros_like(m); zone[y0+int(bh*.38):y0+int(bh*.62), x0+int(bw*.5):]=1
wh=cv2.morphologyEx(((V>170)&(S<80)&(zone>0)).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(wh)
for k in range(1,n):
    if st[k,4]>1500 and st[k,0]+st[k,2] < x0+bw-10: m[l==k]=1
# granite visible through the tag hook only (small box under the hook)
G=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
T=cv2.GaussianBlur(np.abs(cv2.Laplacian(G,cv2.CV_32F,ksize=3)),(0,0),3)
hook=np.zeros_like(m); hook[y0+int(bh*.07):y0+int(bh*.19), x0+int(bw*.48):x0+int(bw*.66)]=1
gr=((S<45)&(V>70)&(V<200)&(T>12)&(hook>0)).astype(np.uint8)
gr=cv2.morphologyEx(gr,cv2.MORPH_OPEN,np.ones((5,5),np.uint8)); gr=cv2.morphologyEx(gr,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
m[gr>0]=0
m=biggest(m)
a=cv2.GaussianBlur(m.astype(np.float32)*255,(0,0),1.2)
out=np.dstack([im,a.astype(np.uint8)])
ys,xs=np.where(out[...,3]>20); out=out[ys.min():ys.max()+1,xs.min():xs.max()+1]
cv2.imwrite(out_path,out)
