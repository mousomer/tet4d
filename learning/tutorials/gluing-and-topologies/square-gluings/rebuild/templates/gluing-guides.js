// Intersect the material grid with the mesh in square coordinates once.
const guideGrid = [];
const gridStep = (Math.max(...mesh.square.map(p => p[0])) * 2) / 8;
for (const face of faces) {
  const ids = face.slice(0,3);
  for (let axis=0; axis<2; axis++) {
    const coordinates = ids.map(id=>mesh.square[id][axis]);
    for (let line=-3; line<=3; line++) {
      const level=line*gridStep;
      if (level<Math.min(...coordinates) || level>=Math.max(...coordinates)) continue;
      const ends=[];
      for (let i=0; i<3; i++) {
        const j=(i+1)%3, a=coordinates[i], b=coordinates[j];
        if ((a<=level)===(b<=level)) continue;
        ends.push([ids[i],ids[j],(level-a)/(b-a)]);
      }
      if (ends.length===2) guideGrid.push(ends);
    }
  }
}
const guideOffset=mesh.square.length/2;
const guideAdjacent=['sphere-revised','adjacent-klein','direct-curl'].includes(mesh.kind);
const guideReversed={
  'sphere-revised':[false,false], 'adjacent-klein':[true,true],
  'direct-curl':[false,true], 'opposite-torus':[false,false],
  'opposite-klein':[false,true], 'opposite-rp2':[true,true],
}[mesh.kind];
const guideEdges=seams.map(([edge,color],pair)=>{
  const lower=seams[guideAdjacent?pair:1-pair][0].map(id=>id+guideOffset);
  if (guideReversed[pair]) lower.reverse();
  return {edge,lower,color};
});
const guideCorners=[seams[0][0][0],seams[0][0].at(-1),seams[1][0].at(-1),
  seams[0][0].at(-1)+guideOffset];
function guideLabels(firstClosed,closed) {
  const groups=guideCorners.map((id,i)=>[[id],String.fromCharCode(65+i)]);
  function merge(a,b) {
    // The diagonal AC is represented by a vertex in each triangular patch.
    const normalize=id=> {
      if (id===guideCorners[0]+guideOffset || id===guideCorners[2]+guideOffset) return id-guideOffset;
      return id;
    };
    const i=groups.findIndex(([ids])=>ids.includes(normalize(a)));
    const j=groups.findIndex(([ids])=>ids.includes(normalize(b)));
    if (i===j) return;
    const lo=Math.min(i,j), hi=Math.max(i,j);
    groups[lo][0].push(...groups[hi][0]);
    groups[lo][1]+=groups[hi][1];
    groups.splice(hi,1);
  }
  for (const {edge,lower} of guideEdges.slice(0,closed?2:firstClosed?1:0)) {
    merge(edge[0],lower[0]);
    merge(edge.at(-1),lower.at(-1));
  }
  return groups.map(([ids,name])=>[ids[0],[...name].sort().join(' + ')]);
}
function drawGuides(screen,firstClosed,closed) {
  const opacity=1-Math.min(1,Math.max(0,(seconds-secondJoin)/1.25));
  if (!opacity) return;
  ctx.save();
  ctx.globalAlpha=opacity*.46;
  ctx.strokeStyle='#dbe9fb';
  ctx.lineWidth=.65;
  ctx.beginPath();
  for (const ends of guideGrid) {
    const [p,q]=ends.map(([a,b,t])=>screen[a].slice(0,2).map((v,i)=>v+(screen[b][i]-v)*t));
    ctx.moveTo(...p);
    ctx.lineTo(...q);
  }
  ctx.stroke();
  ctx.globalAlpha=opacity;
  for (const [{edge,lower,color},joined] of guideEdges.map((edge,i)=>[edge,i?closed:firstClosed])) {
    for (const ids of joined?[edge]:[edge,lower]) {
      const mid=Math.floor(ids.length/2);
      const [x,y]=screen[ids[mid]], a=screen[ids[mid-2]], b=screen[ids[mid+2]];
      const length=Math.hypot(b[0]-a[0],b[1]-a[1]);
      if (length<1) continue;
      const u=(b[0]-a[0])/length, v=(b[1]-a[1])/length;
      ctx.beginPath();
      ctx.moveTo(x+10*u,y+10*v);
      ctx.lineTo(x-6*u-5*v,y-6*v+5*u);
      ctx.lineTo(x-6*u+5*v,y-6*v-5*u);
      ctx.closePath();
      ctx.fillStyle=color;
      ctx.strokeStyle='#152032';
      ctx.lineWidth=2.5;
      ctx.stroke();
      ctx.fill();
    }
  }
  ctx.font='14px system-ui';
  ctx.textAlign='center';
  ctx.textBaseline='middle';
  for (const [id,name] of guideLabels(firstClosed,closed)) {
    const [x,y]=screen[id];
    const w=ctx.measureText(name).width+12;
    const lx=Math.min(canvas.clientWidth-w/2,Math.max(w/2,x));
    const ly=Math.max(12,y-16);
    ctx.fillStyle='#172335';
    ctx.fillRect(lx-w/2,ly-10,w,20);
    ctx.fillStyle='#fff3da';
    ctx.fillText(name,lx,ly);
  }
  ctx.restore();
}
