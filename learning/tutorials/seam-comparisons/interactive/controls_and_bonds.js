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

  function renderSequence(index) {
    sequenceStep = index;
    const code = sequence.value;
    const status = [index === 0 ? "Start" : moves[code[index - 1]], `Move ${index} of ${code.length}`];
    for (const { id, seams, ctx, cells, bond } of sequenceBoards) {
      const { a, b, bonded } = tracePose(code, id, index);
      const previouslyBonded = tracePose(code, id, Math.max(0, index - 1)).bonded;
      const label = bonded ? (previouslyBonded ? "Bond intact" : "Bond rejoined") :
        (previouslyBonded ? "Bond broken" : "Bond still broken");
      drawDomino(ctx, a, b, seams, bonded);
      bond.textContent = label;
      bond.dataset.bonded = String(bonded);
      cells.textContent = `1 at (${a.join(", ")}) · 2 at (${b.join(", ")})`;
      status.push(`${id.toUpperCase()} ${label.toLowerCase()}`);
    }
    sequenceProgress.textContent = status.join(" · ");
    sequencePrevious.disabled = index === 0;
    sequenceReset.disabled = index === 0;
    sequenceNext.disabled = index === code.length;
  }

  sequence.addEventListener("change", () => renderSequence(0));
  sequencePrevious.addEventListener("click", () => {
    renderSequence(sequenceStep - 1);
    if (sequencePrevious.disabled) sequenceNext.focus();
  });
  sequenceNext.addEventListener("click", () => {
    renderSequence(sequenceStep + 1);
    if (sequenceNext.disabled) sequencePrevious.focus();
  });
  sequenceReset.addEventListener("click", () => {
    renderSequence(0);
    sequenceNext.focus();
  });

  renderSequence(0);
  renderComparison(0);
  renderDomino(false);
})();
