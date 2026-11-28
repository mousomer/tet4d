// The first fold develops the square into a cone or a Möbius band. The
// second closure interpolates to the Python renderer's actual tipped mesh.
const firstJoin=8, secondStart=10, secondJoin=16;
function onClosure() { section.checked=false; }
PLAYBACK_TRANSPORT
GLUING_GUIDES
const adjacent = mesh.adjacent;
const smooth = x => {
  const u = Math.max(0, Math.min(1, x));
  return u * u * (3 - 2 * u);
};

function foldedPoint([x, y], fold) {
  if (adjacent) {
    const dx = x + .5, dy = .5 - y;
    const beta = Math.PI / 2 - fold * Math.acos(.25);
    const radial = Math.hypot(dx, dy), sine = Math.sin(beta);
    const angle = (Math.PI / 4 - Math.atan2(dy, dx)) / sine;
    const along = radial * sine * Math.cos(angle), across = radial * sine * Math.sin(angle);
    const px = (along + across) / Math.SQRT2, pz = radial * Math.cos(beta);
    const tilt = 1.37 * fold;
    return [-.5 - .15 * fold + Math.cos(tilt) * px + Math.sin(tilt) * pz,
            .5 - .38 * fold + (across - along) / Math.SQRT2,
            -Math.sin(tilt) * px + Math.cos(tilt) * pz];
  }
  if (fold === 0) return [x, y, 0];
  const k = 2 * Math.PI * fold, angle = k * y;
  const radius = (1 - fold) / k + .65 * fold, across = x * Math.cos(angle / 2);
  return [across * Math.cos(angle) + radius * (fold * fold - 2 * Math.sin(angle / 2) ** 2),
          (radius + across) * Math.sin(angle), x * Math.sin(angle / 2)];
}
const closedFold = mesh.square.map(p => foldedPoint(p, 1));
function surfaceAt(fold, closure, separation) {
  return mesh.square.map((p, i) => {
    if (fold < 1) return foldedPoint(p, fold);
    const target = mesh.points[i];
    const z = target[2] + (target[3] || 0) * separation;
    return [target[0], target[1], z].map((v, k) => closedFold[i][k] * (1 - closure) + closure * v);
  });
}
const separation=document.getElementById("separate");
separation?.addEventListener("input",requestDraw);

function draw(timestamp) {
  if (started !== null) seek((timestamp - started) / 1000);
  pending = false;
  const {width, height} = canvas.getBoundingClientRect();
  const density = Math.min(devicePixelRatio || 1, 2);
  canvas.width = Math.round(width*density);
  canvas.height = Math.round(height*density);
  ctx.setTransform(density,0,0,density,0,0);
  const fold = smooth((seconds - 2) / 6), closure = smooth((seconds - 10) / 6);
  const turn = smooth((seconds - 16) / 5);
  const approach = smooth((seconds - 8) / 6);
  const azimuth = yaw - home.yaw + home.yaw * approach - .34 * approach * (1 - turn);
  const elevation = pitch - home.pitch + home.pitch * approach + .12 * approach * (1 - turn);
  const ca = Math.cos(azimuth), sa = Math.sin(azimuth);
  const ce = Math.cos(elevation), se = Math.sin(elevation);
  const scale = Math.min(width*.29,height*.39) * (1.55 - .55 * closure);
  const points = surfaceAt(fold, closure, Number(separation?.value || 0) * .006);
  const screen = points.map(([x,y,z]) => {
    const a = ca*x+sa*z, b = -sa*x+ca*z;
    return [width/2+scale*a,height*.51-scale*(ce*y-se*b),se*y+ce*b];
  });
  const sorted = faces.map(([a,b,c]) => {
    const [ax,ay,az]=points[a], [bx,by,bz]=points[b], [cx,cy,cz]=points[c];
    const u=(by-ay)*(cz-az)-(bz-az)*(cy-ay);
    const v=(bz-az)*(cx-ax)-(bx-ax)*(cz-az);
    const w=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax);
    const length=Math.hypot(u,v,w)||1;
    const nx=u/length, ny=v/length, nz=w/length;
    const x = ca*nx+sa*nz, z = -sa*nx+ca*nz;
    const diffuse = Math.max(0,(se*ny+ce*z<0?-1:1)*(Number(light.value)/100*x+.56*(ce*ny-se*z)+.73*(se*ny+ce*z)));
    return [a,b,c,(screen[a][2]+screen[b][2]+screen[c][2])/3,diffuse, (1-Math.min(1,Math.abs(se*ny+ce*z)))**3];
  }).sort((a,b)=>a[3]-b[3]);
  function path(indices, close=false) {
    ctx.beginPath();
    indices.forEach((id,i) => {
      const [x,y] = screen[id];
      if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    if (close) ctx.closePath();
  }
  function seam(ids, color, dashed) {
    ctx.setLineDash(dashed ? [5,5] : []);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    path(ids);
    if (!dashed) {
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#233449';
      ctx.stroke();
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = dashed ? 2 : 1.7;
    ctx.stroke();
    ctx.setLineDash([]);
  }
  const w=Math.round(width), h=Math.round(height);
  const pixels=ctx.createImageData(w,h);
  const heads=new Int32Array(w*h);
  let capacity=w*h+1, count=0;
  let depth=new Float32Array(capacity), next=new Int32Array(capacity), colors=new Uint32Array(capacity);
  function grow(buffer) {
    const result=new buffer.constructor(2*buffer.length);
    result.set(buffer);
    return result;
  }
  const palette=Number(hue.value)*Math.PI/180;
  const rgb=points.map(()=>[0,0,0,0]);
  for(const [a,b,c,,illumination,rim] of sorted) {
    const angle=Math.atan2(mesh.points[a][1]+mesh.points[b][1]+mesh.points[c][1],mesh.points[a][0]+mesh.points[b][0]+mesh.points[c][0])+palette;
    const faceColor=[0,2.1,4.2].map(v=>Math.min(255,(135+118*Math.cos(angle-v))*(.35+.8*illumination)+45*illumination**12+85*rim));
    const relief = Math.max(0,Math.min(1,((screen[a][2]+screen[b][2]+screen[c][2])/3+1.25)/1.6));
    for (let k=0;k<3;k++) faceColor[k]*=.32+.68*relief;
    for(const id of [a,b,c]) {
      for(let k=0;k<3;k++)rgb[id][k]+=faceColor[k];
      rgb[id][3]++;
    }
  }
  for(const color of rgb)for(let k=0;k<3;k++)color[k]/=color[3]||1;
  for(const [a,b,c] of sorted) {
    const [x,y,z]=screen[a], [bx,by,bz]=screen[b], [cx,cy,cz]=screen[c];
    const ux=bx-x,uy=by-y,vx=cx-x,vy=cy-y,det=ux*vy-uy*vx;
    if(Math.abs(det)<1e-9)continue;
    const right=Math.min(w-1,Math.ceil(Math.max(x,bx,cx)));
    const bottom=Math.min(h-1,Math.ceil(Math.max(y,by,cy)));
    for(let j=Math.max(0,Math.floor(Math.min(y,by,cy)));j<=bottom;j++){
      for(let i=Math.max(0,Math.floor(Math.min(x,bx,cx)));i<=right;i++){
        const dx=i+.501-x,dy=j+.503-y;
        const u=(dx*vy-dy*vx)/det,v=(ux*dy-uy*dx)/det,t=1-u-v;
        if(u<0||v<0||t<0)continue;
        const id=++count;
        if(id>=capacity){depth=grow(depth);next=grow(next);colors=grow(colors);capacity=depth.length;}
        depth[id]=t*z+u*bz+v*cz;
        let packed=0;
        for(let k=0;k<3;k++)packed|=Math.round(t*rgb[a][k]+u*rgb[b][k]+v*rgb[c][k])<<(8*k);
        colors[id]=packed;
        const pix=j*w+i;
        let prev=0,cur=heads[pix];
        while(cur && depth[cur]<depth[id]){prev=cur;cur=next[cur];}
        next[id]=cur;
        if(prev)next[prev]=id;else heads[pix]=id;
      }
    }
  }
  const alpha=Number(opacity.value)/100;
  for(let pix=0;pix<heads.length;pix++){
    if(!heads[pix])continue;
    let r=17,g=27,b=42;
    for(let id=heads[pix];id;id=next[id]){
      const col=colors[id];
      r+=alpha*((col&255)-r);g+=alpha*(((col>>>8)&255)-g);b+=alpha*((col>>>16)-b);
    }
    const i=4*pix;
    pixels.data[i]=r;pixels.data[i+1]=g;pixels.data[i+2]=b;pixels.data[i+3]=255;
  }
  buffer.width=w;buffer.height=h;
  buffer.getContext('2d').putImageData(pixels,0,0);
  ctx.drawImage(buffer,0,0,width,height);
  ctx.globalAlpha=1;
  if (trace.checked) {
    ctx.globalAlpha = .72;
    for (const [ids,color] of seams) seam(ids,color,false);
    const offset = mesh.square.length / 2;
    for (const [pair, progress] of [fold, closure].entries()) {
      if (progress === 1) continue;
      const ids = seams[adjacent ? pair : 1 - pair][0];
      const other=ids.map(id=>id+offset);
      seam(other, seams[pair][1], false);
    }
    ctx.globalAlpha = 1;
  }

  drawGuides(screen,fold===1,closure===1);
  const used = [];
  ctx.font = '14px system-ui';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (const [id,name] of (section.checked && seconds>=secondJoin+1.25 ? tips : [])) {
    const [x,y] = screen[id];
    const w = ctx.measureText(name).width+18;
    let lx = Math.max(w/2+5,Math.min(width-w/2-5,x+(x-width/2)*.23));
    let ly = Math.max(16,Math.min(height-16,y+(y>height*.51?34:-34)));
    for(let tries=0;tries<3 && used.some(([px,py,pw])=>Math.abs(py-ly)<28&&Math.abs(px-lx)<(pw+w)/2+4);tries++) {
      ly = ly > height/2 ? ly-30 : ly+30;
    }
    used.push([lx,ly,w]);
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(lx,ly);
    ctx.strokeStyle = '#d2e1ef';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.beginPath();
    ctx.roundRect(lx-w/2,ly-12,w,24,6);
    ctx.fillStyle = '#172335';
    ctx.fill();
    ctx.strokeStyle = '#687e95';
    ctx.stroke();
    ctx.fillStyle = '#fff3da';
    ctx.fillText(name,lx,ly);
  }
  if (started !== null) requestDraw();
}
function requestDraw() {
  if (pending) return;
  pending = true;
  requestAnimationFrame(draw);
}
function rotate(dx,dy) {
  yaw += dx;
  pitch += dy;
  requestDraw();
}
canvas.addEventListener('pointerdown', event => {
  canvas.setPointerCapture(event.pointerId);
  drag = [event.pointerId,event.clientX,event.clientY];
});
canvas.addEventListener('pointermove', event => {
  if (!drag || drag[0] !== event.pointerId) return;
  rotate((event.clientX-drag[1])*.012,(event.clientY-drag[2])*.012);
  drag = [event.pointerId,event.clientX,event.clientY];
});
canvas.addEventListener('lostpointercapture', () => { drag = null; });
canvas.addEventListener('keydown', event => {
  const delta = {ArrowLeft:[-.13,0],ArrowRight:[.13,0],ArrowUp:[0,-.13],ArrowDown:[0,.13]}[event.key];
  if (!delta) return;
  event.preventDefault();
  rotate(...delta);
});
reset.addEventListener('click', () => { pause(); seek(duration); ({yaw,pitch}=home); trace.checked=true; section.checked=false; if (separation) separation.value=0; requestDraw(); });
trace.addEventListener('change', requestDraw);
for (const id of ['section','opacity','light','hue']) document.getElementById(id).addEventListener('input',requestDraw);
new ResizeObserver(requestDraw).observe(canvas);
requestDraw();
