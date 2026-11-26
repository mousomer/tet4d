"use strict";

(() => {
  const script = document.currentScript;
  const domino = script.dataset.view === "domino";
  const page = domino
    ? "tutorials/seam-comparisons/interactive/index.html#domino-sequences"
    : "index.html";
  const frame = document.createElement("iframe");
  frame.src = new URL(page, script.src).href;
  frame.title = domino ? "Tet4D Lesson 03 · Domino tutorial" : "Tet4D Learning";
  frame.height = /^\d{3,4}$/.test(script.dataset.height) ? script.dataset.height : "850";
  frame.style.cssText = "display:block;width:100%;border:0";
  if (document.head.contains(script)) {
    const mount = () => document.body.append(frame);
    if (document.body) mount();
    else document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    script.before(frame);
  }
})();
