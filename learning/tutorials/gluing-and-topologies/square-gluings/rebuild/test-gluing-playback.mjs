// Exercise the self-contained pages and their original final meshes.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {runInNewContext} from 'node:vm';

for (const name of ['sphere-revised','opposite-torus','adjacent-klein','opposite-klein']) {
  test(name + ': playback joins both edge pairs and preserves the endpoint', () => {
    const sphere = name === 'sphere-revised';
    const file = sphere ? 'rotate-sphere.html' : 'rotate.html';
    const html = readFileSync(new URL('../'+name+'/'+file,import.meta.url),'utf8');
    const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
    const element = {addEventListener() {}, getContext() {}};
    const context = {document: {
      querySelector:()=>element, createElement:()=>element, getElementById:()=>element,
    }, ResizeObserver:class {observe() {}}, requestAnimationFrame() {}};
    const result = runInNewContext(script + `
      (() => {
        const first = playbackStage(firstJoin + .01);
        const last = playbackStage(secondJoin);
        const checkGaps = stage => {
          const p = stagePoints(stage);
          return seams.map(([ids],pair) => {
            const partner = sphere || construction.id==='klein-adjacent' ? ids : seams[1-pair][0];
            const reverse = construction.id==='klein-adjacent' || (construction.id==='klein-opposite' && pair===1);
            return Math.max(...ids.map((i,j) => {
              const other=partner[reverse ? ids.length-1-j : j]+mesh.square.length/2;
              return Math.hypot(...p[i].map((v,k)=>v-p[other][k]));
            }));
          });
        };
        const near = stagePoints(playbackStage(secondJoin-.000001));
        const error = Math.max(...near.map((p,i)=>Math.hypot(...p.map((v,k)=>v-mesh.points[i][k]))));
        return {first:checkGaps(first),last:checkGaps(last),error,tips:mesh.tips.length,
          open:stageSeams(playbackStage(0)).length, closed:stageSeams(last).length};
      })()
    `,context);
    assert.equal(result.open,4);
    assert.equal(result.closed,2);
    assert.ok(result.first[0]<1e-6 && result.first[1]>.01,JSON.stringify(result));
    assert.ok(result.last.every(gap=>gap<1e-6));
    assert.ok(result.error<.00002,JSON.stringify(result));
    assert.equal(result.tips,sphere?3:1);
  });
}
