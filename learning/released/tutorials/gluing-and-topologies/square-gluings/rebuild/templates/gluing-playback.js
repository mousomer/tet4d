const sphere = construction.id === 'sphere';
const firstJoin = sphere ? 4.35 : 8;
const secondStart = sphere ? 5.25 : 10;
const secondJoin = sphere ? 6.9 : 16;
function onClosure() {
  const separationControl = document.getElementById('separate');
  if (separationControl) separationControl.value = 0;
}
PLAYBACK_TRANSPORT

function smooth(x) {
  x = Math.max(0, Math.min(1, x));
  return x*x*(3-2*x);
}
function playbackStage(time) {
  const params = sphere ? construction.params(time) : {
    fold: smooth((time-2)/6), puff: smooth((time-secondStart)/6), gap: 0
  };
  const view = smooth(time / secondJoin);
  const reveal = view * (1-smooth((time-secondJoin)/(sphere ? 2.6 : 5)));
  return {params, view, reveal, closed: time >= secondJoin, firstClosed: time >= firstJoin};
}

function stagePoints(stage) {
  const displacement = Number(document.getElementById('separate')?.value || 0) * .006;
  if (stage.closed) {
    return mesh.points.map(([x,y,z,w]) => [x,y,z+(w||0)*displacement]);
  }
  // The adjacent Klein endpoint in this viewer is rotated about z by 0.57.
  const roll = construction.id === 'klein-adjacent' ? .57*stage.view :
    sphere ? -Math.PI/4*(1-stage.view) : 0;
  const c = Math.cos(roll), s = Math.sin(roll);
  return mesh.square.map(([u,v]) => {
    const [x,y,z] = construction.point(u,v,stage.params,1);
    const cy = sphere ? y+.5*(1-stage.params.fold) : y;
    return [c*x-s*cy,s*x+c*cy,z];
  });
}

function stageSeams(stage) {
  if (stage.closed) return seams;
  const adjacent = sphere || construction.id === 'klein-adjacent';
  const offset = mesh.square.length/2;
  return seams.concat(seams.flatMap(([ids,color],pair) => {
    if (pair===0 && stage.firstClosed) return [];
    const partner = adjacent ? ids : seams[1-pair][0];
    return [[partner.map(id => id+offset),color]];
  }));
}

function faceNormal(a,b,c,sign) {
  const ux=b[0]-a[0], uy=b[1]-a[1], uz=b[2]-a[2];
  const vx=c[0]-a[0], vy=c[1]-a[1], vz=c[2]-a[2];
  const x=uy*vz-uz*vy, y=uz*vx-ux*vz, z=ux*vy-uy*vx;
  const scale=sign/(Math.hypot(x,y,z)||1);
  return [scale*x,scale*y,scale*z];
}
