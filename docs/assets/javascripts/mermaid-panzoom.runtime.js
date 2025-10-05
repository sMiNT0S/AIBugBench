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
      // getBBox can throw if the element isn't in the document yet; swallow.
    }
  }

  function alignTopLeft(instance) {
    if (!instance || typeof instance.getPan !== "function") return;
    try {
      var pan = instance.getPan();
      var x = pan.x;
      var y = pan.y;
      if (x > 0) x = 0;
      if (y > 0) y = 0;
      if (x !== pan.x || y !== pan.y) {
        instance.pan({ x: x, y: y });
      }
    } catch (err) {
      // ignore alignment failures
    }
  }

  function syncContainer(instance, wrap) {
    if (!instance || !wrap || typeof instance.getSizes !== "function") return;
    try {
      var sizes = instance.getSizes();
      if (!sizes || !sizes.height) return;
      var frame = Math.ceil(sizes.height + 70);
      wrap.style.setProperty("--mermaid-auto-height", frame + "px");
    } catch (err) {
      // ignore sizing issues
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
      return setTimeout(function () {
        attachWhenReady(svg, tries + 1);
      }, 100);
    }
    if (isErrorSvg(svg)) {
      markSkip(svg, "error");
      console.warn("[mermaid-panzoom] skip error diagram", svg.id || svg);
      return;
    }
    ensureViewBox(svg);
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
        preventMouseEventsDefault: true,
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

    if (instance && typeof instance.enablePan === "function") {
      instance.enablePan();
    }

    if (svg && svg.style) {
      svg.style.userSelect = "none";
      svg.style.webkitUserSelect = "none";
      svg.style.msUserSelect = "none";
      svg.style.touchAction = "none";
      svg.style.cursor = "grab";
    }

    svg.__mermaidPanzoom = instance;
    svg.__pz = instance;

    var wrap = svg.closest && svg.closest(".mermaid");
    alignTopLeft(instance);
    if (wrap) syncContainer(instance, wrap);

    var container = svg.parentElement || svg;
    container.addEventListener(
      "wheel",
      function (e) {
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
      },
      { passive: false }
    );

    wrap = wrap || (svg.closest && svg.closest(".mermaid"));
    if (wrap && !wrap.querySelector(".zoom-controls")) {
      var ui = document.createElement("div");
      ui.className = "zoom-controls";
      ui.style.position = "absolute";
      ui.style.top = "0.75rem";
      ui.style.left = "1rem";
      ui.innerHTML =
        '<button data-act="fit" title="Fit">Fit</button>' +
        '<button data-act="reset" title="Reset">Reset</button>' +
        '<span class="hint">Ctrl/Cmd + scroll to zoom, drag to pan</span>';
      wrap.appendChild(ui);

      ui.addEventListener("click", function (ev) {
        var act = ev.target.getAttribute("data-act");
        if (act === "fit") {
          instance.resize();
          instance.fit();
          alignTopLeft(instance);
          syncContainer(instance, wrap);
        }
        if (act === "reset") {
          instance.resize();
          instance.resetZoom();
          alignTopLeft(instance);
          syncContainer(instance, wrap);
        }
      });

      var det = wrap.closest("details");
      if (det)
        det.addEventListener("toggle", function () {
          if (det.open) {
            instance.resize();
            instance.fit();
            alignTopLeft(instance);
            syncContainer(instance, wrap);
          }
        });
    }

    markSkip(svg, "1");
    console.info("[mermaid-panzoom] attached to", svg.id || svg);
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
