/* Mermaid pan/zoom for MkDocs Material - attaches to all mermaid diagrams */
(function () {
  function visibleBox(svg) {
    try {
      var r = svg.getBoundingClientRect();
      return r && r.width > 0 && r.height > 0 && !!svg.ownerDocument.body.contains(svg);
    } catch (e) {
      return false;
    }
  }

  function looksMermaidSvg(svg) {
    if (!svg || svg.tagName !== "svg") return false;
    if (svg.id && svg.id.indexOf("mermaid-") === 0) return true;
    if (svg.closest && svg.closest(".mermaid")) return true;
    var g = svg.querySelector('g[class*="mermaid"]');
    return !!g;
  }

  function isErrorSvg(svg) {
    return !!(svg && svg.getAttribute("aria-roledescription") === "error");
  }

  function ensureViewBox(svg) {
    if (!svg) return;
    try {
      var vb = svg.viewBox && svg.viewBox.baseVal;
      if (!vb) return;
      if ((vb.width && vb.height) && vb.width > 0 && vb.height > 0) return;
      var box = svg.getBBox();
      if (box && box.width > 0 && box.height > 0) {
        svg.setAttribute("viewBox", [box.x, box.y, box.width, box.height].join(" "));
      }
    } catch (err) {
      // ignore if getBBox fails
    }
  }

  function ensureDimensions(svg) {
    if (!svg) return;
    var width = parseFloat(svg.getAttribute("width"));
    var height = parseFloat(svg.getAttribute("height"));

    function safeBox(cb) {
      try {
        var val = cb();
        if (val && isFinite(val) && val > 0) return val;
      } catch (err) {
        // ignore
      }
      return null;
    }

    if (!isFinite(width) || width <= 0) {
      width = safeBox(function () { return svg.getBBox().width; });
      if (!width) width = safeBox(function () { return svg.getBoundingClientRect().width; });
      if (!width) width = 1;
    }

    if (!isFinite(height) || height <= 0) {
      height = safeBox(function () { return svg.getBBox().height; });
      if (!height) height = safeBox(function () { return svg.getBoundingClientRect().height; });
      if (!height) height = 1;
    }

    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
  }

  function alignTopLeft(instance) {
    if (!instance || typeof instance.getPan !== "function") return;
    try {
      var pan = instance.getPan();
      var target = { x: pan.x, y: pan.y };
      if (target.x > 0) target.x = 0;
      if (target.y !== 0) target.y = 0;
      instance.pan(target);
    } catch (err) {
      // ignore alignment target issues
    }
  }

  function markSkip(svg, flag) {
    try {
      svg.setAttribute("data-panzoom-applied", flag);
    } catch (e) {
      /* noop */
    }
  }

  function findMermaidSvgs(root) {
    var out = [];
    var all = (root || document).querySelectorAll("svg");
    for (var i = 0; i < all.length; i++) {
      if (looksMermaidSvg(all[i])) out.push(all[i]);
    }
    return out;
  }

  function attachWhenReady(svg, tries) {
    tries = tries || 0;
    var state = svg.getAttribute("data-panzoom-applied");
    if (state === "1" || state === "error" || state === "failed") return;
    if (!visibleBox(svg)) {
      if (tries > 80) {
        markSkip(svg, "failed");
        return;
      }
      return setTimeout(function () { attachWhenReady(svg, tries + 1); }, 100);
    }
    ensureViewBox(svg);
    ensureDimensions(svg);
    if (isErrorSvg(svg)) {
      markSkip(svg, "error");
      console.warn("[mermaid-panzoom] skip error diagram", svg.id || svg);
      return;
    }
    attach(svg);
  }

  function attach(svg) {
    if (!window.svgPanZoom) {
      console.error("[mermaid-panzoom] svgPanZoom missing.");
      markSkip(svg, "failed");
      return;
    }

    var instance;
    try {
      instance = window.svgPanZoom(svg, {
        panEnabled: true,
        zoomEnabled: true,
        controlIconsEnabled: false,
        dblClickZoomEnabled: false,
        mouseWheelZoomEnabled: false,
        fit: true,
        center: true,
        minZoom: 0.4,
        maxZoom: 8,
        beforePan: null,
        beforeZoom: null
      });
    } catch (err) {
      markSkip(svg, "failed");
      console.error("[mermaid-panzoom] failed to initialise", err);
      return;
    }

    if (instance && typeof instance.enablePan === "function") instance.enablePan();

    if (svg && svg.style) {
      svg.style.userSelect = "none";
      svg.style.webkitUserSelect = "none";
      svg.style.msUserSelect = "none";
      svg.style.touchAction = "none";
      svg.style.cursor = "grab";
    }

    svg.__mermaidPanzoom = instance;
    svg.__pz = instance;

    alignTopLeft(instance);

    var container = svg.parentElement || svg;
    container.addEventListener("wheel", function (e) {
      if (!(e.ctrlKey || e.metaKey)) return;
      e.preventDefault();
      var delta = e.deltaY < 0 ? 1.1 : 0.9;
      try {
        var pt = svg.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;
        var ctm = svg.getScreenCTM();
        if (!ctm || typeof ctm.inverse !== "function") return;
        var cursor = pt.matrixTransform(ctm.inverse());
        instance.zoomAtPointBy(delta, cursor);
      } catch (err) {
        console.warn("[mermaid-panzoom] wheel zoom skipped", err);
      }
    }, { passive: false });

    var wrap = svg.closest && svg.closest(".mermaid");
    if (wrap && !wrap.querySelector(".zoom-controls")) {
      var ui = document.createElement("div");
      ui.className = "zoom-controls";
      ui.innerHTML =
        '<button data-act="fit" title="Fit">Fit</button>' +
        '<button data-act="reset" title="Reset">Reset</button>' +
        '<span class="hint">Ctrl/Cmd + scroll to zoom, drag to pan</span>';
      wrap.appendChild(ui);

      ui.addEventListener("click", function (ev) {
        var act = ev.target.getAttribute("data-act");
        if (act === "fit") { instance.resize(); instance.fit(); alignTopLeft(instance); }
        if (act === "reset") { instance.resize(); instance.resetZoom(); alignTopLeft(instance); }
      });

      var det = wrap.closest("details");
      if (det) det.addEventListener("toggle", function () {
        if (det.open) {
          instance.resize();
          instance.fit();
          alignTopLeft(instance);
        }
      });
    }

    markSkip(svg, "1");
    console.info("[mermaid-panzoom] attached", svg.id || svg);
  }

  function boot() {
    var ticks = 0;
    var poll = setInterval(function () {
      findMermaidSvgs(document).forEach(attachWhenReady);
      if (++ticks > 50) clearInterval(poll);
    }, 100);
  }

  window.MermaidPanZoom = {
    attachAll: function () {
      findMermaidSvgs(document).forEach(attachWhenReady);
    }
  };

  if (window.document$) {
    window.document$.subscribe(boot);
  } else {
    document.addEventListener("DOMContentLoaded", boot);
  }

  var mo = new MutationObserver(function (muts) {
    for (var i = 0; i < muts.length; i++) {
      var n = muts[i].target || document;
      findMermaidSvgs(n).forEach(attachWhenReady);
    }
  });
  mo.observe(document.documentElement, { childList: true, subtree: true });
})();
