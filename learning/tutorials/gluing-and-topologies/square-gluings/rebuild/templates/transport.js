const timeline = document.getElementById('timeline');
const play = document.getElementById('play');
const phase = document.getElementById('phase');
const duration = Number(timeline.max);
let seconds = duration;
let started = null;
function seek(value) {
  const wasOpen = seconds < secondJoin;
  seconds = Math.min(duration, Math.max(0, value));
  timeline.value = seconds;
  phase.textContent = seconds < firstJoin ? 'Orange edges approaching' : seconds < secondStart ? 'Orange seam joined'
    : seconds < secondJoin ? 'Cyan edges approaching' : 'Both seams joined';
  if (seconds >= secondJoin && (wasOpen || seconds === duration)) {
    onClosure();
    trace.checked = true;
  }
  if (seconds === duration) {
    started = null;
    play.textContent = 'Replay';
  }
  requestDraw();
}
function pause() {
  started = null;
  play.textContent = 'Play';
}
function togglePlayback() {
  if (started !== null) { pause(); return; }
  if (seconds === duration) seek(0);
  started = performance.now() - seconds * 1000;
  play.textContent = 'Pause';
  requestDraw();
}
play.addEventListener('click', togglePlayback);
timeline.addEventListener('input', () => { pause(); seek(Number(timeline.value)); });
canvas.addEventListener('keydown', e => {
  if (e.code === 'Space') { e.preventDefault(); togglePlayback(); }
});
