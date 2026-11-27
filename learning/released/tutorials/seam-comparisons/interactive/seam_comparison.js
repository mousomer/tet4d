"use strict";

const commands = [
  { name: "Left", delta: [-1, 0] },
  { name: "Left", delta: [-1, 0] },
  { name: "Left", delta: [-1, 0] },
  { name: "Up", delta: [0, 1] },
  { name: "Up", delta: [0, 1] },
];
const home = { cell: [0, 2], red: [1, 0], blue: [0, 1] };

function makeTimeline(sign) {
  const timeline = [home];
  for (const command of [...commands, ...commands]) {
    const { cell: [x, y], red, blue } = timeline.at(-1);
    const [dx, dy] = command.delta;
    if (x + dx < 0) {
      // Outward left becomes inward up. The tangent follows the seam sign.
      const transport = ([vx, vy]) => [sign * vy, -vx];
      timeline.push({
        cell: [sign === 1 ? y : 4 - y, 0],
        red: transport(red),
        blue: transport(blue),
        crossing: true,
      });
    } else {
      timeline.push({ cell: [x + dx, y + dy], red, blue, crossing: false });
    }
  }
  return timeline;
}

const boards = [
  { id: "a", timeline: makeTimeline(1) },
  { id: "b", timeline: makeTimeline(-1) },
].map(board => ({
  ...board,
  context: document.querySelector(`#board-${board.id}`).getContext("2d"),
  frame: document.querySelector(`#frame-${board.id}`),
}));
const previous = document.querySelector("#previous");
const next = document.querySelector("#next");
const reset = document.querySelector("#reset");
const progress = document.querySelector("#progress");
const observation = document.querySelector("#observation");
const commandLabels = [...document.querySelectorAll("[data-command]")];
const motion = matchMedia("(prefers-reduced-motion: reduce)");
const finalStep = 2 * commands.length;
const cellSize = 60;
const boardStart = 35;
const boardEnd = boardStart + 5 * cellSize;
const redColor = "#ff8c86";
const blueColor = "#89bbff";
let step = 0;
let animation = 0;

function screen([x, y], size = 5) {
  const spacing = (boardEnd - boardStart) / size;
  return [boardStart + (x + .5) * spacing, boardEnd - (y + .5) * spacing];
}

function line(ctx, from, to, color, width) {
  ctx.beginPath();
  ctx.moveTo(...from);
  ctx.lineTo(...to);
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.stroke();
}

function arrow(ctx, [x, y], [vx, vy], color, length) {
  const end = [x + vx * length, y - vy * length];
  const head = [end[0] - vx * 8, end[1] + vy * 8];
  line(ctx, [x, y], end, color, 4);
  line(ctx, end, [head[0] + vy * 4, head[1] + vx * 4], color, 4);
  line(ctx, end, [head[0] - vy * 4, head[1] - vx * 4], color, 4);
}

function drawFrame(ctx, frame, cell, ghost = false) {
  const center = screen(cell);
  ctx.save();
  ctx.globalAlpha = ghost ? .35 : 1;
  if (ghost) ctx.setLineDash([3, 4]);
  const length = ghost ? 32 : 26;
  arrow(ctx, center, frame.red, redColor, length);
  arrow(ctx, center, frame.blue, blueColor, length);
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.arc(...center, 4, 0, 2 * Math.PI);
  ctx.fillStyle = "#eff3fc";
  ctx.fill();
  ctx.restore();
}

function mix(from, to, t) {
  return from.map((value, axis) => value + (to[axis] - value) * t);
}

function drawGrid(ctx, size = 5) {
  ctx.setTransform(2, 0, 0, 2, 0, 0);
  ctx.clearRect(0, 0, 370, 370);
  ctx.lineCap = "round";
  ctx.fillStyle = "#172236";
  const extent = boardEnd - boardStart;
  ctx.fillRect(boardStart, boardStart, extent, extent);
  for (let i = 0; i <= size; i++) {
    const coordinate = boardStart + i * extent / size;
    line(ctx, [coordinate, boardStart], [coordinate, boardEnd], "#3a4b66", 1);
    line(ctx, [boardStart, coordinate], [boardEnd, coordinate], "#3a4b66", 1);
  }
  ctx.fillStyle = "#b3bed4";
  ctx.font = "20px system-ui";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (let i = 0; i < size; i++) {
    const [x, y] = screen([i, i], size);
    ctx.fillText(i, x, 352);
    ctx.fillText(i, 17, y);
  }

}

function drawBoard({ context: ctx, timeline }, fraction) {
  drawGrid(ctx);
  const current = timeline[step];
  const completed = fraction === 1 ? step : step - 1;
  for (const frame of timeline.slice(0, completed + 1)) {
    const [x, y] = screen(frame.cell);
    ctx.fillStyle = "#253956";
    ctx.fillRect(x - 25, y - 25, 50, 50);
  }
  if (step === 0 || current.crossing) {
    const [, y] = screen(home.cell);
    const [entryX] = screen(timeline[1].cell);
    const color = current.crossing ? "#a1f3cf" : "#5d9e8a";
    line(ctx, [boardStart, y - 18], [boardStart, y + 18], color, 4);
    line(ctx, [entryX - 18, boardEnd], [entryX + 18, boardEnd], color, 4);
  }
  drawFrame(ctx, home, home.cell, true);

  if (fraction === 1) {
    drawFrame(ctx, current, current.cell);
    return;
  }
  const before = timeline[step - 1];
  if (!current.crossing) {
    drawFrame(ctx, current, mix(before.cell, current.cell, fraction));
  } else if (fraction < .5) {
    const exit = [-.5, before.cell[1]];
    drawFrame(ctx, before, mix(before.cell, exit, fraction * 2));
  } else {
    const entry = [current.cell[0], -.5];
    drawFrame(ctx, current, mix(entry, current.cell, fraction * 2 - 1));
  }
}

function direction([x, y]) {
  if (x !== 0) return x > 0 ? "right" : "left";
  return y > 0 ? "up" : "down";
}

function updateText() {
  const commandIndex = (step - 1) % commands.length;
  const loop = Math.max(1, Math.ceil(step / commands.length));
  const crossing = boards[0].timeline[step].crossing;
  progress.textContent = step === 0 ? "Ready · Both tokens start at (0, 2)" :
    `Loop ${loop} · Step ${commandIndex + 1} of 5 · ${commands[commandIndex].name}${crossing ? " · Left-to-bottom crossing" : ""}`;
  for (const [index, label] of commandLabels.entries()) {
    label.classList.toggle("current", step > 0 && index === commandIndex);
  }
  for (const { frame, timeline } of boards) {
    const { cell, red, blue } = timeline[step];
    frame.textContent = `(${cell.join(", ")}) · Red ${direction(red)}, blue ${direction(blue)}`;
  }
  if (step === 0) {
    observation.textContent = "Predict how the two frames will look after they come home.";
  } else if (step === 5) {
    observation.textContent = "Both tokens are home. Turn from red to blue in each frame. A keeps its handedness and B reverses it.";
  } else if (step === finalStep) {
    observation.textContent = "After two loops, A has turned half a turn. B’s original frame is restored.";
  } else if (crossing) {
    observation.textContent = step === 1
      ? "Both seams send index 2 to index 2. Compare where the blue arrow points on arrival."
      : "The same seam acts on the frame you brought back from the first loop.";
  } else {
    observation.textContent = "Both tokens move along the board axes. Their frames keep the directions they had after the crossing.";
  }
  previous.disabled = step === 0;
  next.disabled = step === finalStep;
  reset.disabled = step === 0;
}

function goTo(target, animate = false) {
  cancelAnimationFrame(animation);
  step = target;
  updateText();
  if (!animate || motion.matches) {
    boards.forEach(board => drawBoard(board, 1));
    return;
  }
  const start = performance.now();
  const duration = boards[0].timeline[step].crossing ? 850 : 240;
  function tick(now) {
    const fraction = motion.matches ? 1 : Math.min(1, (now - start) / duration);
    boards.forEach(board => drawBoard(board, fraction));
    if (fraction < 1) animation = requestAnimationFrame(tick);
  }
  animation = requestAnimationFrame(tick);
}

previous.addEventListener("click", () => goTo(step - 1));
next.addEventListener("click", () => goTo(step + 1, true));
reset.addEventListener("click", () => goTo(0));
goTo(0);
