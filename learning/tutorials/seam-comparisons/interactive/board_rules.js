"use strict";

const right = [1, 0];
const left = [-1, 0];
const up = [0, 1];
const down = [0, -1];
const adjacent = {
  R: ["T", 1], T: ["R", 1], L: ["B", 1], B: ["L", 1],
};
const opposite = {
  R: ["L", -1], L: ["R", -1], T: ["B", -1], B: ["T", -1],
};

function move([x, y], [dx, dy], seams, size = 5) {
  const last = size - 1;
  const nextX = x + dx;
  const nextY = y + dy;
  const exit = nextX < 0 ? "L" : nextX > last ? "R" :
    nextY < 0 ? "B" : nextY > last ? "T" : null;
  if (exit === null) return [nextX, nextY];
  const [entry, sign] = seams[exit];
  const index = dx === 0 ? x : y;
  const t = sign === 1 ? index : last - index;
  return {
    L: [0, t], R: [last, t], B: [t, 0], T: [t, last],
  }[entry];
}

function sameCell(a, b) {
  return a[0] === b[0] && a[1] === b[1];
}

const boardSeams = [
  ["a", adjacent],
  ["b", { ...adjacent, L: ["B", -1], B: ["L", -1] }],
  ["c", opposite],
];
