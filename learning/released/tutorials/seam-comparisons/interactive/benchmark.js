"use strict";

(() => {
  const size = 8;
  const directions = [left, right, up, down];
  const cells = Array.from({ length: size ** 2 }, (_, id) => [id % size, Math.floor(id / size)]);
  const idOf = ([x, y]) => y * size + x;
  const inside = ([x, y], [dx, dy]) =>
    x + dx >= 0 && x + dx < size && y + dy >= 0 && y + dy < size;
  const crosses = cells.map(cell => directions.map(direction => !inside(cell, direction)));
  const boardNames = ["A · Sphere", "B · Adjacent projective plane", "C · Opposite projective plane"];
  const byId = id => document.getElementById(id);

  function fourCellSets() {
    // Grow ordinary grid-connected shapes and deduplicate sorted cell IDs.
    let shapes = cells.map((_, id) => [id]);
    for (let count = 1; count < 4; count++) {
      const grown = new Map();
      for (const shape of shapes) {
        for (const id of shape) {
          for (const [dx, dy] of directions) {
            if (!inside(cells[id], [dx, dy])) continue;
            const [x, y] = cells[id];
            const neighbour = idOf([x + dx, y + dy]);
            if (shape.includes(neighbour)) continue;
            const expanded = [...shape, neighbour].sort((a, b) => a - b);
            grown.set(expanded.join(","), expanded);
          }
        }
      }
      shapes = [...grown.values()];
    }
    return shapes;
  }

  const shapes = fourCellSets();
  const topology = boardSeams.map(([, seams]) => ({
    seams,
    steps: cells.map(cell => directions.map(direction => idOf(move(cell, direction, seams, size)))),
  }));
  const collides = pose => new Set(pose).size !== pose.length;

  function lostBonds(before, after, steps) {
    const lost = [];
    for (let a = 0; a < before.length; a++) {
      for (let b = a + 1; b < before.length; b++) {
        if (steps[before[a]].includes(before[b]) && !steps[after[a]].includes(after[b])) {
          lost.push([a, b]);
        }
      }
    }
    return lost;
  }

  function tally({ steps }) {
    let crossings = 0;
    let misses = 0;
    let firstTrials = 0;
    let firstBlocks = 0;
    let secondTrials = 0;
    let secondBlocks = 0;
    let secondLosses = 0;

    for (const [id, targets] of steps.entries()) {
      for (const [command, target] of targets.entries()) {
        if (crosses[id][command]) {
          crossings++;
          if (steps[target][command ^ 1] !== id) misses++; // Directions are ordered in opposite pairs.
        }
      }
    }
    for (const start of shapes) {
      for (const [command] of directions.entries()) {
        if (!start.some(id => crosses[id][command])) continue;
        firstTrials++;
        const afterFirst = start.map(id => steps[id][command]);
        if (collides(afterFirst)) {
          firstBlocks++;
          continue;
        }
        for (const [next] of directions.entries()) {
          secondTrials++;
          const afterSecond = afterFirst.map(id => steps[id][next]);
          if (collides(afterSecond)) secondBlocks++;
          else if (lostBonds(afterFirst, afterSecond, steps).length) secondLosses++;
        }
      }
    }
    return [[misses, crossings], [firstBlocks, firstTrials],
      [secondBlocks, secondTrials], [secondLosses, secondTrials]];
  }

  const counts = topology.map(tally);
  const metric = byId("benchmark-metric");
  const countTable = byId("benchmark-counts");
  const sample = byId("benchmark-sample");
  const integer = new Intl.NumberFormat("en");
  const percent = new Intl.NumberFormat("en", { style: "percent", maximumFractionDigits: 1 });

  function renderCounts() {
    const selected = metric.selectedIndex;
    sample.textContent = [
      "Sample · Every single-cell command that crosses a seam. The opposite command is checked for return to the starting cell.",
      "Sample · Every ordinary grid-connected four-cell placement and command that attempts a seam crossing.",
      "Sample · Four second commands after every successful first command.",
      "Sample · The same second-command trials, including blocked moves. Only a successful move that loses at least one existing bond counts.",
    ][selected];
    countTable.replaceChildren(...counts.map((row, index) => {
      const [events, trials] = row[selected];
      const tr = document.createElement("tr");
      const label = document.createElement("th");
      label.scope = "row";
      label.textContent = boardNames[index];
      const count = document.createElement("td");
      count.textContent = `${integer.format(events)}/${integer.format(trials)}`;
      const rate = document.createElement("td");
      rate.textContent = percent.format(events / trials);
      const bar = document.createElement("meter");
      bar.max = trials;
      bar.value = events;
      bar.setAttribute("aria-label", `${boardNames[index]} rate`);
      rate.append(bar);
      tr.append(label, count, rate);
      return tr;
    }));
  }

  const example = byId("benchmark-example");
  const previous = byId("benchmark-previous");
  const next = byId("benchmark-next");
  const reset = byId("benchmark-reset");
  const source = byId("benchmark-source").getContext("2d");
  const target = byId("benchmark-target").getContext("2d");
  const labels = ["1", "2", "3", "4"];
  let stage = 0;

  const blockStart = [[0, 1], [1, 0], [1, 1], [2, 0]].map(idOf);
  const blockedArrival = blockStart.map(id => topology[0].steps[id][0]);
  const lossStart = [[0, 1], [0, 2], [0, 3], [1, 1]].map(idOf);
  const afterLeft = lossStart.map(id => topology[2].steps[id][0]);
  const afterUp = afterLeft.map(id => topology[2].steps[id][2]);
  const lost = lostBonds(afterLeft, afterUp, topology[2].steps);
  const examples = {
    block: [
      { before: blockStart, after: blockStart, title: "Starting board", message: "A · The four labelled cells are ready to move Left." },
      { before: blockStart, after: blockedArrival, title: "Proposed arrivals", message: "Left sends labels 1 and 4 to (1, 0). The striped cell marks the collision." },
      { before: blockStart, after: blockStart, title: "After rejection", message: "Blocked · The collision rejects the entire command. All four labels stay in their original cells." },
    ],
    loss: [
      { before: lossStart, after: lossStart, title: "Starting board", message: "C · Start with four connected cells. Left sends three of them across the reversed seam." },
      { before: lossStart, after: afterLeft, title: "After Left", message: "Left succeeds. Labels 1 and 4 share a seam bond, shown in gold at the left and right edges.", bond: lost, bondAfter: true },
      { before: afterLeft, after: afterUp, title: "After Up", message: "Up succeeds. All four destinations are distinct, but labels 1 and 4 no longer share an edge.", bond: lost, bondAfter: false },
    ],
  };

  function drawBond(ctx, pose, pairs) {
    for (const [first, second] of pairs) {
      for (const [a, b] of [[first, second], [second, first]]) {
        const [x, y] = screen(cells[pose[a]], size);
        const [dx, dy] = directions[topology[2].steps[pose[a]].indexOf(pose[b])];
        const radius = (boardEnd - boardStart) / size / 2;
        line(ctx, [x, y], [x + dx * radius, y - dy * radius], "#ffd17a", 6);
      }
    }
  }

  function drawPose(ctx, pose, bonds, markCollision) {
    drawGrid(ctx, size);
    drawBond(ctx, pose, bonds);
    for (const id of new Set(pose)) {
      const [x, y] = screen(cells[id], size);
      const occupants = labels.filter((_, index) => pose[index] === id);
      const collision = markCollision && occupants.length > 1;
      ctx.fillStyle = collision ? "#9b393e" : "#365273";
      const half = collision ? 16 : 12;
      ctx.fillRect(x - half, y - half, half * 2, half * 2);
      if (collision) {
        line(ctx, [x - 14, y + 11], [x + 11, y - 14], "#cf6469", 3);
        line(ctx, [x - 9, y + 14], [x + 14, y - 9], "#cf6469", 3);
      }
      ctx.fillStyle = "#eff3fc";
      ctx.font = "bold 17px system-ui";
      ctx.fillText(occupants.join("+"), x, y);
    }
  }

  function describePose(pose) {
    return pose.map((id, index) => `${labels[index]} at (${cells[id].join(", ")})`).join(" · ");
  }

  function renderExample(index) {
    stage = index;
    const timeline = examples[example.value];
    const { before, after, title, message, bond = [], bondAfter } = timeline[stage];
    drawPose(source, before, bondAfter === false ? bond : [], false);
    drawPose(target, after, bondAfter ? bond : [], collides(after));
    byId("benchmark-source-title").textContent = stage === 0 ? "Starting pose" : "Before the command";
    byId("benchmark-target-title").textContent = title;
    byId("benchmark-source-cells").textContent = describePose(before);
    byId("benchmark-target-cells").textContent = describePose(after);
    byId("benchmark-status").textContent = `Stage ${stage + 1} of ${timeline.length} · ${message}`;
    previous.disabled = stage === 0;
    reset.disabled = stage === 0;
    next.disabled = stage === timeline.length - 1;
  }

  metric.addEventListener("change", renderCounts);
  example.addEventListener("change", () => renderExample(0));
  previous.addEventListener("click", () => {
    renderExample(stage - 1);
    if (previous.disabled) next.focus();
  });
  next.addEventListener("click", () => {
    renderExample(stage + 1);
    if (next.disabled) previous.focus();
  });
  reset.addEventListener("click", () => {
    renderExample(0);
    next.focus();
  });
  renderCounts();
  renderExample(0);
})();
