"""Rastrea los contornos dibujados en el fotograma de referencia del Suzuki."""
import argparse
import os
import shutil
import cv2
import json
import numpy as np
from pathlib import Path
import subprocess

here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("video", type=Path, help="Clip vertical de tres pistas")
parser.add_argument("salida", type=Path, help="Nuevo JSON de encuadres")
args=parser.parse_args()
source=args.video.resolve(strict=True)
ff=os.environ.get("KONDUCE_FFMPEG") or shutil.which("ffmpeg") or here.parents[2]/".local/ffmpeg.exe"
# Coordenadas trazadas sobre una reproducción de 300 x 534.
items=[
 (20.80,19.93,21.83,[18,129,261,252],"M 278 130 Q 259 159 209 211 Q 151 271 105 294 Q 69 310 39 319 Q 30 344 19 380 Q 125 372 190 348 Q 234 334 246 303 Q 267 213 278 130 Z"),
 (13.70,12.47,14.37,[45,176,200,228],"M 68 178 Q 158 179 231 187 Q 245 188 244 204 L 229 384 Q 226 404 209 398 L 48 344 Q 43 342 46 330 L 62 191 Q 63 180 68 178 Z"),
 (17.10,15.90,17.80,[145,248,91,80],"M 148 304 Q 148 318 153 325 Q 166 316 175 281 Q 182 260 197 256 Q 216 249 235 257")
]

def gray(at):
    out=subprocess.check_output([str(ff),"-v","error","-threads","2","-ss",str(at),"-i",str(source),"-frames:v","1","-an","-vf","scale=300:534,format=gray","-f","rawvideo","-"])
    return np.frombuffer(out,"uint8").reshape((534,300))

details=[]
for ref,start,end,box,path in items:
    frame=gray(ref)
    x,y,w,h=box
    mask=np.zeros(frame.shape,"uint8")
    pad=22
    mask[max(0,y-pad):min(534,y+h+pad),max(0,x-pad):min(300,x+w+pad)]=255
    corners=cv2.goodFeaturesToTrack(frame,maxCorners=160,qualityLevel=.009,minDistance=3,mask=mask)
    positions=[]
    for t in np.linspace(start,end-1/30,5):
        target=gray(float(t))
        shifted,status,_=cv2.calcOpticalFlowPyrLK(frame,target,corners,None,winSize=(31,31),maxLevel=3)
        valid=status.ravel()==1
        affine,_=cv2.estimateAffinePartial2D(corners.reshape(-1,2)[valid],shifted.reshape(-1,2)[valid],method=cv2.RANSAC,ransacReprojThreshold=1.5)
        cx,cy=affine@np.array([x+w/2,y+h/2,1])
        scale=np.hypot(affine[0,0],affine[1,0])
        positions.append([round(cx*1080/300,1),round(cy*1920/534,1),round(w*scale*1080/300,1),round(h*scale*1920/534,1)])
    details.append(dict(sourceBox=box,path=path,positions=positions,reference=ref))
with args.salida.open("x", encoding="utf-8") as out:
    json.dump(details, out, indent=2)
print("Rutas medidas en cinco posiciones por plano.")
