(()=>{
'use strict';
const W=720,H=360,S=480;
// The decoded mask is derived from the GSHHG shoreline dataset; see COASTLINE_DATA_LICENSE.md.
const mask64=window.EARTH_S2_GSHHG_MASK_B64;
const packed=atob(mask64), land=new Uint8Array(W*H);let offset=0,bit=packed.charCodeAt(0);
for(let k=1;k<packed.length;k++){const n=packed.charCodeAt(k);land.fill(bit,offset,offset+n);offset+=n;bit^=1;}
if(offset!==W*H)throw new Error('Corrupt coastline mask');
const canvas=document.getElementById('world'),ctx=canvas.getContext('2d',{alpha:false}),image=ctx.createImageData(S,S),pixels=image.data;
const vectors=new Float32Array(S*S*3),tM=2*Math.PI/(2+Math.SQRT2),tC=2*tM,origin=-165*Math.PI/180;
function squarePoint(x,y){
  x=Math.max(0,Math.min(1,x));y=Math.max(0,Math.min(1,y));
  const north=y>=x;
  const wa=north?1-y:1-x,wm=north?y-x:x-y,wc=north?x:y;
  const rr=Math.max(0,Math.min(1,1-3*Math.min(wa,wm,wc)));
  if(rr<1e-8)return [0,0,north?1:-1];
  const a=1/3+(wa-1/3)/rr,m=1/3+(wm-1/3)/rr,c=1/3+(wc-1/3)/rr;
  let theta;if(c<1e-6)theta=tM*m;
  else if(a<1e-6)theta=tM+(tC-tM)*c;
  else theta=tC+(2*Math.PI-tC)*a;
  const lat=(north?1:-1)*(Math.PI/2)*(1-rr),lon=origin+theta;
  return [Math.cos(lat)*Math.cos(lon),Math.cos(lat)*Math.sin(lon),Math.sin(lat)];
}
for(let row=0;row<S;row++)for(let col=0;col<S;col++){
  const p=squarePoint((col+0.5)/S,1-(row+0.5)/S),q=(row*S+col)*3;
  vectors[q]=p[0];vectors[q+1]=p[1];vectors[q+2]=p[2];
}
let q=[1,0,0,0],graticule=true,drag=false,previous=null,scheduled=false;
function multiply(a,b){return [
 a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3],
 a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],
 a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1],
 a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]];}
function unit(a){const n=Math.hypot(...a);return a.map(z=>z/n);}
function rotateBetween(a,b){
 const d=Math.max(-1,Math.min(1,a[0]*b[0]+a[1]*b[1]+a[2]*b[2]));
 if(d>0.999999)return [1,0,0,0];
 if(d< -0.999999){let axis=Math.abs(a[0])<.9?[0,-a[2],a[1]]:[-a[1],a[0],0];axis=unit(axis);return [0,...axis];}
 return unit([1+d,a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]);
}
// Projection coordinates are exposed for independent seam-continuity tests.
window.TET4D_EARTH_S2_DIAGNOSTICS = Object.freeze({ squarePoint });
function pointerSphere(e){const rect=canvas.getBoundingClientRect();return squarePoint((e.clientX-rect.left)/rect.width,1-(e.clientY-rect.top)/rect.height);}
function render(){
 scheduled=false;
 const [w,x,y,z]=q;
 const r00=1-2*(y*y+z*z),r01=2*(x*y-z*w),r02=2*(x*z+y*w);
 const r10=2*(x*y+z*w),r11=1-2*(x*x+z*z),r12=2*(y*z-x*w);
 const r20=2*(x*z-y*w),r21=2*(y*z+x*w),r22=1-2*(x*x+y*y);
 const pi2=Math.PI*2;
 for(let i=0,j=0;i<S*S;i++,j+=3){
   const X=vectors[j],Y=vectors[j+1],Z=vectors[j+2];
   const a=r00*X+r01*Y+r02*Z,b=r10*X+r11*Y+r12*Z,c=r20*X+r21*Y+r22*Z;
   const lon=Math.atan2(b,a),lat=Math.atan2(c,Math.hypot(a,b));
   let px=Math.floor((lon/pi2+.5)*W),py=Math.floor((.5-lat/Math.PI)*H);
   px=((px%W)+W)%W;py=Math.max(0,Math.min(H-1,py));
   const isLand=land[py*W+px];
   const u=(lon/pi2+.5),v=lat/Math.PI;
   let r,g,bb;
   if(isLand){
     const desert=(lat>0.16&&lat<0.60&&lon>-0.35&&lon<1.00)||(lat<-.28&&lat>-.68&&lon>1.93&&lon<2.80);
     const mild=8*Math.sin(u*36+Math.sin(v*24)) +4*Math.cos(v*45);
     r=(desert?204:174)+mild;g=(desert?178:167)+mild;bb=(desert?113:122)+mild*.5;
   }else{
     const wave=4*Math.sin(u*41+v*13)+3*Math.cos(v*37);
     r=20+wave;g=70+wave;bb=104+wave;
   }
   if(isLand && Math.abs(lat)>1.30){r=218;g=228;bb=227;}
   if(graticule){
     const parallel=Math.abs(Math.sin(6*lat))<0.014;
     const meridian=Math.abs(Math.sin(4*lon))<0.014;
     if(parallel||meridian){r=r*.75+242*.25;g=g*.75+245*.25;bb=bb*.75+230*.25;}
   }
   const k=i*4;pixels[k]=r;pixels[k+1]=g;pixels[k+2]=bb;pixels[k+3]=255;
 }
 ctx.putImageData(image,0,0);
 // The two original triangles remain fixed while Earth spins.
 ctx.save();ctx.setLineDash([6,6]);ctx.strokeStyle='rgba(255,244,206,.95)';ctx.lineWidth=1.8;
 ctx.beginPath();ctx.moveTo(0,S);ctx.lineTo(S,0);ctx.stroke();ctx.restore();
}
function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(render);}}
canvas.addEventListener('pointerdown',e=>{if(e.button!==0&&e.pointerType==='mouse')return;drag=true;previous=pointerSphere(e);canvas.setPointerCapture(e.pointerId);canvas.classList.add('dragging');});
canvas.addEventListener('pointermove',e=>{if(!drag)return;const now=pointerSphere(e);q=unit(multiply(q,rotateBetween(now,previous)));previous=now;schedule();});
function stop(e){drag=false;previous=null;canvas.classList.remove('dragging');if(e&&canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);}
canvas.addEventListener('pointerup',stop);canvas.addEventListener('pointercancel',stop);canvas.addEventListener('lostpointercapture',()=>{drag=false;previous=null;canvas.classList.remove('dragging');});
document.getElementById('reset').addEventListener('click',()=>{q=[1,0,0,0];schedule();});
document.getElementById('grid').addEventListener('click',e=>{graticule=!graticule;e.currentTarget.textContent=graticule?'Hide graticule':'Show graticule';e.currentTarget.setAttribute('aria-pressed',String(graticule));schedule();});
render();
})();
