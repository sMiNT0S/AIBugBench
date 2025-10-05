// Mermaid init for MkDocs Material with SPA navigation + markup normalization
(function () {
  var configured = false;

  var MERMAID_KEYWORDS = [
    "graph",
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "journey",
    "gantt",
    "pie",
    "mindmap",
    "gitGraph",
    "quadrantChart"
  ];

  function looksLikeMermaidSource(raw) {
    if (!raw) return false;
    var lines = raw.split(/\r?\n/).map(function (line) { return line.trim(); });
    while (lines.length && lines[0] === "") lines.shift();
    if (!lines.length) return false;

    var first = lines[0];
    if (first.startsWith("%%{")) {
      lines.shift();
      while (lines.length && lines[0] === "") lines.shift();
      if (!lines.length) return false;
      first = lines[0];
    }

    for (var i = 0; i < MERMAID_KEYWORDS.length; i += 1) {
      if (first.startsWith(MERMAID_KEYWORDS[i])) {
        return true;
      }
    }
    return false;
  }

  function collectExtraClasses(node) {
    if (!node || !node.classList) return [];
    var forbidden = { highlight: true };
    var extras = [];
    node.classList.forEach(function (cls) {
      if (!cls || forbidden[cls] || /^language-/.test(cls)) return;
      extras.push(cls);
    });
    return extras;
  }

  function normalizeMermaidSource(raw) {
    if (!raw) return "";
    var lines = raw.split(/\r?\n/);
    var normalized = [];

    for (var i = 0; i < lines.length; i += 1) {
      var line = lines[i].replace(/\u00a0/g, " ");
      var commentIdx = line.indexOf("%%");
      if (commentIdx > -1) {
        var before = line.slice(0, commentIdx);
        var after = line.slice(commentIdx);
        if (before.trim().length) {
          normalized.push(before.replace(/\s+$/, ""));
          line = after;
        }
      }
      if (/^\s*%%/.test(line)) {
        line = line.replace(/^\s+/, "");
      }
      normalized.push(line);
    }

    return normalized.join("\n");
  }

  function promoteHighlightBlocks(root) {
    var scope = root || document;
    var processed = false;
    var highlightBlocks = scope.querySelectorAll("div.highlight, div.highlighter-rouge");

    for (var i = 0; i < highlightBlocks.length; i += 1) {
      var block = highlightBlocks[i];
      if (block.getAttribute("data-mermaid-processed") === "1") continue;
      var pre = block.querySelector("pre");
      if (!pre) continue;

      var textContent = pre.textContent || "";
      if (!looksLikeMermaidSource(textContent)) continue;

      var wrapper = block.parentElement;
      var extras = collectExtraClasses(block)
        .concat(collectExtraClasses(pre))
        .concat(collectExtraClasses(wrapper));
      var div = document.createElement("div");
      div.className = "mermaid" + (extras.length ? " " + extras.join(" ") : "");
      div.textContent = normalizeMermaidSource(textContent);
      block.replaceWith(div);
      block.setAttribute("data-mermaid-processed", "1");
      processed = true;
    }

    return processed;
  }

  function promoteBarePreBlocks(root) {
    var scope = root || document;
    var processed = false;
    var preNodes = scope.querySelectorAll("pre");

    for (var i = 0; i < preNodes.length; i += 1) {
      var pre = preNodes[i];
      if (pre.getAttribute("data-mermaid-processed") === "1") continue;
      var textContent = pre.textContent || "";
      if (!looksLikeMermaidSource(textContent)) continue;

      var wrapper = pre.parentElement;
      var extras = collectExtraClasses(pre).concat(collectExtraClasses(wrapper));
      var div = document.createElement("div");
      div.className = "mermaid" + (extras.length ? " " + extras.join(" ") : "");
      div.textContent = normalizeMermaidSource(textContent);
      if (wrapper && wrapper !== document.body && wrapper.childNodes.length === 1) {
        wrapper.replaceWith(div);
      } else {
        pre.replaceWith(div);
      }
      pre.setAttribute("data-mermaid-processed", "1");
      processed = true;
    }

    return processed;
  }

  function normalizeExistingMermaidBlocks(root) {
    var scope = root || document;
    var nodes = scope.querySelectorAll(".mermaid");
    var mutated = false;

    for (var i = 0; i < nodes.length; i += 1) {
      var node = nodes[i];
      if (node.getAttribute("data-mermaid-ready") === "1") continue;
      if (node.querySelector("svg")) {
        node.setAttribute("data-mermaid-ready", "1");
        continue;
      }
      var raw = node.textContent || "";
      if (!looksLikeMermaidSource(raw)) continue;
      var normalized = normalizeMermaidSource(raw);
      if (normalized !== raw) {
        node.textContent = normalized;
      }
      node.setAttribute("data-mermaid-ready", "1");
      mutated = true;
    }

    return mutated;
  }

  function prepareMermaidBlocks(root) {
    var changed = false;
    if (promoteHighlightBlocks(root)) changed = true;
    if (promoteBarePreBlocks(root)) changed = true;
    if (normalizeExistingMermaidBlocks(root)) changed = true;
    return changed;
  }

  function schedulePanZoomAttach() {
    if (window.MermaidPanZoom && window.MermaidPanZoom.attachAll) {
      setTimeout(function () {
        window.MermaidPanZoom.attachAll();
      }, 0);
    }
  }

  function renderMermaid() {
    if (!window.mermaid) {
      console.warn("[init_mermaid] window.mermaid unavailable; retrying shortly.");
      return;
    }

    prepareMermaidBlocks();

    if (!configured) {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "default"
      });
      configured = true;
    }

    var targets = document.querySelectorAll(".mermaid:not([data-processed='true'])");
    if (!targets.length) {
      schedulePanZoomAttach();
      return;
    }

    try {
      window.mermaid.init(undefined, targets);
    } catch (err) {
      console.warn("[init_mermaid] failed to render diagrams:", err);
    }

    schedulePanZoomAttach();
  }

  function boot() {
    prepareMermaidBlocks();
    renderMermaid();
  }

  var observer = new MutationObserver(function (mutations) {
    var needsRefresh = false;
    for (var i = 0; i < mutations.length; i += 1) {
      if (prepareMermaidBlocks(mutations[i].target)) {
        needsRefresh = true;
      }
    }
    if (needsRefresh) {
      renderMermaid();
    }
  });

  observer.observe(document.documentElement, { childList: true, subtree: true });

  if (window.document$) {
    window.document$.subscribe(function () {
      boot();
    });
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      boot();
    });
  }
})();
