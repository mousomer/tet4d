// Run with node --test test-rp2-playback.mjs. Exercise the shipped offline pages.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {runInNewContext} from 'node:vm';

for (const name of ['direct-curl', 'opposite-rp2']) {
  test(name + ' keeps each identified edge joined through playback', () => {
    const html = readFileSync(new URL('../' + name + '/rotate.html', import.meta.url), 'utf8');
    const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
    const element = {addEventListener() {}, getContext() {}};
    const context = {
      document: {
        querySelector: () => element, createElement: () => element, getElementById: () => element,
      },
      ResizeObserver: class {observe() {}}, requestAnimationFrame() {},
    };
    const gaps = runInNewContext(script + `
      [0, .25, .75, 1].map(closure => {
        const p = surfaceAt(1, closure, 0), offset = mesh.square.length / 2;
        return seams.map(([ids], pair) => {
          const other = seams[adjacent ? pair : 1 - pair][0];
          return Math.max(...ids.map((id, j) => {
            const k = adjacent && pair === 0 ? j : ids.length - 1 - j;
            return Math.hypot(...p[id].map((v, axis) => v - p[offset + other[k]][axis]));
          }));
        });
      })
    `, context);
    for (const [first] of gaps) assert.ok(first < 1e-6);
    for (const [, second] of gaps.slice(0,-1)) assert.ok(second > .01);
    assert.ok(gaps.at(-1)[1] < 1e-6);
  });
}
