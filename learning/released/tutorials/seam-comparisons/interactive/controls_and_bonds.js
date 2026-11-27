"use strict";

(() => {
  const start = [4, 1];
  const byId = id => document.getElementById(id);

  function token(ctx, cell, color, label = "") {
    const [x, y] = screen(cell);
    ctx.beginPath();
    ctx.arc(x, y, 20, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    if (label) {
      ctx.fillStyle = "#111827";
      ctx.font = "bold 23px system-ui";
      ctx.fillText(label, x, y);
    }
  }

  function edgeMark(ctx, cell, delta) {
    const [x, y] = screen(cell);
    const [dx, dy] = delta;
    const edge = [x + dx * cellSize / 2, y - dy * cellSize / 2];
    line(ctx, [edge[0] - 18 * dy, edge[1] - 18 * dx],
      [edge[0] + 18 * dy, edge[1] + 18 * dx], "#a1f3cf", 5);
  }

  const comparison = boardSeams.map(([id, seams]) => {
    const afterRight = move(start, right, seams);
    return {
      ctx: byId(`compare-${id}`).getContext("2d"),
      output: byId(`position-${id}`),
      cells: [start, afterRight, move(afterRight, left, seams)],
      receivingDirection: seams === opposite ? left : up,
    };
  });

  const compareRight = byId("compare-right");
  const compareLeft = byId("compare-left");
  const compareReset = byId("compare-reset");
  const compareStatus = byId("compare-status");

  function renderComparison(step) {
    compareRight.disabled = step !== 0;
    compareLeft.disabled = step !== 1;
    compareReset.disabled = step === 0;
    compareStatus.textContent = [
      "Ready · All three tokens are at (4, 1).",
      "After Right · A and B enter from the top. C enters from the left. What will Left do?",
      "After Left · C returns home. A and B move along the top row. On A and B, Up would cross straight back from the receiving cell.",
    ][step];

    for (const { ctx, output, cells, receivingDirection } of comparison) {
      const cell = cells[step];
      drawGrid(ctx);
      edgeMark(ctx, start, right);
      edgeMark(ctx, cells[1], receivingDirection);
      if (step > 0 && !sameCell(cell, start)) token(ctx, start, "#40516b");
      token(ctx, cell, "#a1f3cf");
      output.textContent = `(${cell.join(", ")})${step === 2 && sameCell(cell, start) ? " · Home" : ""}`;
    }
  }

  compareRight.addEventListener("click", () => {
    renderComparison(1);
    compareLeft.focus();
  });
  compareLeft.addEventListener("click", () => {
    renderComparison(2);
    compareReset.focus();
  });
  compareReset.addEventListener("click", () => {
    renderComparison(0);
    compareRight.focus();
  });

  const dominoCtx = byId("domino-board").getContext("2d");
  const dominoUp = byId("domino-up");
  const dominoReset = byId("domino-reset");
  const neighbours = [right, left, up, down];
  const original = [start, move(start, right, opposite)];

  function drawDomino(ctx, a, b, seams, bonded) {
    drawGrid(ctx);
    if (bonded) {
      // Each half-edge meets its partner in the chart or at the paired seam.
      for (const [cell, other] of [[a, b], [b, a]]) {
        const [x, y] = screen(cell);
        for (const delta of neighbours) {
          if (sameCell(move(cell, delta, seams), other)) {
            const [dx, dy] = delta;
            line(ctx, [x, y], [x + dx * cellSize / 2, y - dy * cellSize / 2], "#ffd17a", 7);
          }
        }
      }
    }
    token(ctx, a, "#ff8c86", "1");
    token(ctx, b, "#89bbff", "2");
  }

  function renderDomino(moved) {
    const [a, b] = moved ? original.map(cell => move(cell, up, opposite)) : original;
    const bonded = neighbours.some(delta => sameCell(move(a, delta, opposite), b));
    drawDomino(dominoCtx, a, b, opposite, bonded);
    byId("domino-position").textContent = `1 at (${a.join(", ")}) · 2 at (${b.join(", ")})`;
    byId("domino-status").textContent = bonded
      ? "Bond intact · Cell 1 touches cell 2 across the seam."
      : `Bond broken · Both cells moved Up. Across the right seam, cell 1 now touches (${move(a, right, opposite).join(", ")}).`;
    dominoUp.disabled = moved;
    dominoReset.disabled = !moved;
  }

  dominoUp.addEventListener("click", () => {
    renderDomino(true);
    dominoReset.focus();
  });
  dominoReset.addEventListener("click", () => {
    renderDomino(false);
    dominoUp.focus();
  });

  const sequence = byId("domino-sequence");
  const sequencePrevious = byId("sequence-previous");
  const sequenceNext = byId("sequence-next");
  const sequenceReset = byId("sequence-reset");
  const sequenceProgress = byId("sequence-progress");
  const moves = { L: "Left", R: "Right", U: "Up", D: "Down", T: "Clockwise turn" };
  const startingDomino = { a: [0, 1], b: [1, 1], bonded: true };
  // Native trace columns are sphere, opposite projective, adjacent projective.
  const traceBoard = { a: 0, b: 2, c: 1 };
  const trace = new Map(dominoTrace.trim().split("\n").map(row => {
    const [code, board, index, ...values] = row.split(" ");
    const [ax, ay, bx, by, bonded] = values.map(Number);
    return [`${code} ${board} ${index}`, { a: [ax, ay], b: [bx, by], bonded: bonded === 1 }];
  }));
  const sequenceBoards = boardSeams.map(([id, seams]) => ({
    id,
    seams,
    ctx: byId(`sequence-board-${id}`).getContext("2d"),
    cells: byId(`sequence-cells-${id}`),
    bond: byId(`sequence-bond-${id}`),
  }));
  let sequenceStep = 0;

  function tracePose(code, id, index) {
    return index === 0 ? startingDomino : trace.get(`${code} ${traceBoard[id]} ${index}`);
  }

  function displayPose(board, { a, b, bonded }, previouslyBonded) {
    const label = bonded ? (previouslyBonded ? "Bond intact" : "Bond rejoined") :
      (previouslyBonded ? "Bond broken" : "Bond still broken");
    drawDomino(board.ctx, a, b, board.seams, bonded);
    board.bond.textContent = label;
    board.bond.dataset.bonded = String(bonded);
    board.cells.textContent = `1 at (${a.join(", ")}) · 2 at (${b.join(", ")})`;
    return label.toLowerCase();
  }

  function renderSequence(index) {
    sequenceStep = index;
    const code = sequence.value;
    const status = [index === 0 ? "Start" : moves[code[index - 1]], `Move ${index} of ${code.length}`];
    for (const board of sequenceBoards) {
      const pose = tracePose(code, board.id, index);
      const previousPose = tracePose(code, board.id, Math.max(0, index - 1));
      const label = displayPose(board, pose, previousPose.bonded);
      status.push(`${board.id.toUpperCase()} ${label}`);
    }
    sequenceProgress.textContent = status.join(" · ");
    sequencePrevious.disabled = index === 0;
    sequenceReset.disabled = index === 0;
    sequenceNext.disabled = index === code.length;
  }

  const replayControls = byId("domino-replay-controls");
  const freeControls = byId("domino-free-controls");
  const playground = byId("domino-playground");
  const freeButtons = [...freeControls.querySelectorAll("[data-domino-direction]")];
  const freeDirections = { L: left, R: right, U: up, D: down };
  const arrowDirections = { ArrowLeft: "L", ArrowRight: "R", ArrowUp: "U", ArrowDown: "D" };
  let freePoses;

  function resetMode() {
    const free = sequence.value === "free";
    replayControls.hidden = free;
    freeControls.hidden = !free;
    sequenceReset.textContent = free ? "Reset free movement" : "Reset sequence";
    if (free) {
      freePoses = sequenceBoards.map(board => {
        displayPose(board, startingDomino, true);
        return startingDomino;
      });
      sequenceProgress.textContent = "Start · All three boards are bonded.";
      sequenceReset.disabled = true;
    } else {
      renderSequence(0);
    }
  }

  function moveFreely(key) {
    const status = [moves[key]];
    freePoses = sequenceBoards.map((board, index) => {
      const previous = freePoses[index];
      const a = move(previous.a, freeDirections[key], board.seams);
      const b = move(previous.b, freeDirections[key], board.seams);
      const blocked = sameCell(a, b);
      const pose = blocked ? previous : {
        a, b, bonded: neighbours.some(delta => sameCell(move(a, delta, board.seams), b)),
      };
      const label = displayPose(board, pose, previous.bonded);
      status.push(`${board.id.toUpperCase()} ${blocked ? "blocked, " : ""}${label}`);
      return pose;
    });
    sequenceProgress.textContent = status.join(" · ");
    sequenceReset.disabled = false;
  }

  for (const button of freeButtons) {
    button.addEventListener("click", () => moveFreely(button.dataset.dominoDirection));
  }
  playground.addEventListener("keydown", event => {
    const direction = arrowDirections[event.key];
    if (!direction || freeControls.hidden || event.target === sequence ||
        event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    event.preventDefault();
    moveFreely(direction);
  });
  sequence.addEventListener("change", resetMode);
  sequencePrevious.addEventListener("click", () => {
    renderSequence(sequenceStep - 1);
    if (sequencePrevious.disabled) sequenceNext.focus();
  });
  sequenceNext.addEventListener("click", () => {
    renderSequence(sequenceStep + 1);
    if (sequenceNext.disabled) sequencePrevious.focus();
  });
  sequenceReset.addEventListener("click", () => {
    resetMode();
    (freeControls.hidden ? sequenceNext : freeButtons[0]).focus();
  });

  resetMode();
  if (location.hash === "#domino-sequences") playground.focus({ preventScroll: true });
  renderComparison(0);
  renderDomino(false);
})();
