import cv2, numpy as np, sys
D=sys.argv[1]; rng=np.random.default_rng(3)
im=cv2.imread(f'{D}/hero.jpg'); H,W=im.shape[:2]
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
roi=np.zeros((H,W),np.uint8)
cv2.fillPoly(roi,[np.array([[165,2014],[165,1890],[540,1615],[722,1618],[728,1716],[430,2016]],np.int32)],255)
old=((g>45)&(roi>0)).astype(np.uint8)*255
old=cv2.morphologyEx(old,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
old=cv2.dilate(old,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)))
# shading of the old print (lit lower-left, darker toward the shoulder): fit a plane to its brightness
ys,xs=np.where((g>95)&(roi>0))
A=np.c_[xs,ys,np.ones_like(xs)]; coef,*_=np.linalg.lstsq(A,g[ys,xs],rcond=None)
print('old print L plane',coef, 'mean',g[ys,xs].mean())
col=np.median(im[(g>95)&(roi>0)].astype(np.float32),axis=0); print('print colour',col)
# 1) remove old print: inpaint, then restore fabric grain
clean=cv2.inpaint(im,old,21,cv2.INPAINT_TELEA).astype(np.float32)
sm=cv2.GaussianBlur(clean,(0,0),6)
grain=rng.normal(0,2.6,(H,W,1)).astype(np.float32)
om=cv2.GaussianBlur((old>0).astype(np.float32),(0,0),3)[...,None]
clean=clean*(1-om)+(sm+grain)*om
# 2) new print
t=cv2.imread(f'{D}/txtnew.png',cv2.IMREAD_UNCHANGED)[...,3].astype(np.float32)/255
t=cv2.GaussianBlur(t,(0,0),0.9)
yy,xx=np.mgrid[0:H,0:W]
L=coef[0]*xx+coef[1]*yy+coef[2]
shade=(L/np.median(g[ys,xs]))[...,None]
# fabric folds show through the print: high-pass of the cleaned fabric luminance
cl=cv2.cvtColor(np.clip(clean,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
fold=(cl-cv2.GaussianBlur(cl,(0,0),25))/30.0
# worn / cracked print like the original
crack=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),1.4); crack/=crack.std()
wear=np.clip(1-0.55*np.clip(crack-1.3,0,None),0,1)
ta=(t*wear)[...,None]
pc=col*1.1*shade*(1+0.35*fold[...,None]) + rng.normal(0,4,(H,W,1)).astype(np.float32)
out=clean*(1-ta*0.97)+pc*ta*0.97
cv2.imwrite(f'{D}/hero-mr.jpg',np.clip(out,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,94])
cv2.imwrite(f'{D}/txtcrop.jpg',np.clip(out,0,255).astype(np.uint8)[1450:2016,0:900])
