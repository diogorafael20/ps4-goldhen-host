/* One screen for every host: a percentage, a bar, and one sentence.
 *
 * The chains behind these pages do not report a percentage -- they report
 * stages. So the bar is driven by named checkpoints (see the adapters in each
 * page) and never claims more than the chain has actually done: it holds at
 * 99 until the payload is running, and only then goes to 100.
 *
 * ES5 only: the 5.05 and 6.72 consoles run a WebKit that chokes on arrow
 * functions, and this file is loaded by every folder.
 */
(function () {
    if (window.HostUI) return;

    var PKEY = "hostui.p";
    var st = { mounted: false, done: false, pct: 0, logEl: null };

    var CSS = [
        '.hu{position:fixed;top:0;left:0;right:0;bottom:0;z-index:2147483645;',
        'background:#0b0e12;color:#e8edf3;font:16px/1.5 Arial,Helvetica,sans-serif;',
        '-webkit-font-smoothing:antialiased;display:-webkit-box;display:-webkit-flex;',
        'display:flex;-webkit-box-align:center;-webkit-align-items:center;align-items:center;',
        '-webkit-box-pack:center;-webkit-justify-content:center;justify-content:center;overflow:auto}',
        '.hu *{box-sizing:border-box}',
        '.hu .box{width:100%;max-width:400px;padding:32px 24px;text-align:center}',
        '.hu .fw{color:#5f6b7a;font-size:12px;letter-spacing:.16em;text-transform:uppercase;',
        'margin:0 0 22px;display:-webkit-box;display:flex;-webkit-box-align:center;',
        'align-items:center;-webkit-box-pack:center;justify-content:center}',
        '.hu .fw svg{width:15px;height:15px;margin-right:8px;display:block;opacity:.85}',
        '.hu .pct{font-size:64px;font-weight:bold;line-height:1;letter-spacing:-.03em;',
        'color:#e8edf3;margin:0 0 20px}',
        '.hu .pct i{font-style:normal;font-size:26px;font-weight:normal;color:#5f6b7a;',
        'vertical-align:super;margin-left:2px}',
        '.hu .bar{height:6px;border-radius:3px;background:#1b222c;overflow:hidden;margin:0 0 20px}',
        '.hu .fill{height:100%;width:0;border-radius:3px;',
        'background:#7cc4ff;-webkit-transition:width .45s ease;transition:width .45s ease}',
        '.hu .msg{color:#93a1b1;font-size:15px;line-height:1.45;margin:0;min-height:44px}',
        '.hu.ok .pct{color:#7fe0a6}',
        '.hu.ok .fill{background:#7fe0a6}',
        '.hu.ok .msg{color:#7fe0a6}',
        '.hu.bad .pct{color:#ff9d9d}',
        '.hu.bad .fill{background:#ff9d9d}',
        '.hu.bad .msg{color:#cf9a9a}',
        '.hu button{display:none;width:100%;margin:24px 0 0;padding:17px 14px;border:0;',
        'border-radius:6px;background:#7cc4ff;color:#0b0e12;',
        'font:bold 18px/1.2 Arial,Helvetica,sans-serif;cursor:pointer}',
        '.hu button.show{display:block}',
        '.hu .det{margin:26px 0 0;font-size:12px}',
        '.hu .det a{color:#4d5867;text-decoration:none}',
        '.hu .log{display:none;margin:14px 0 0;padding:10px 12px;text-align:left;',
        'background:#11161d;border:1px solid #1b222c;border-radius:6px;color:#78869a;',
        'font:11px/1.5 Consolas,monospace;white-space:pre-wrap;max-height:38vh;overflow-y:auto}',
        '.hu .log.show{display:block}'
    ].join("");

    function store(v) {
        try { sessionStorage.setItem(PKEY, String(v)); } catch (e) {}
    }

    function mounted() {
        try { return parseInt(sessionStorage.getItem(PKEY) || "0", 10) || 0; }
        catch (e) { return 0; }
    }

    function node(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text) e.appendChild(document.createTextNode(text));
        return e;
    }

    function paint() {
        var pct = st.pct;
        var pctEl = document.getElementById("huPct");
        var fill = document.getElementById("huFill");
        if (pctEl) {
            while (pctEl.firstChild) pctEl.removeChild(pctEl.firstChild);
            pctEl.appendChild(document.createTextNode(String(pct)));
            pctEl.appendChild(node("i", "", "%"));
        }
        if (fill) fill.style.width = pct + "%";
    }

    /* The four face buttons, drawn rather than fetched: the console's browser
       caches images aggressively and an inline SVG is one less file that can
       go missing from the app cache. */
    var GLYPH = '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
        '<polygon points="16,2.8 20.4,10.4 11.6,10.4" fill="none" stroke="#5fd6c8" ' +
        'stroke-width="2" stroke-linejoin="round"/>' +
        '<circle cx="25.2" cy="16" r="4.2" fill="none" stroke="#ff8080" stroke-width="2"/>' +
        '<path d="M3.9 12.4 L10.9 19.6 M10.9 12.4 L3.9 19.6" fill="none" stroke="#8fb6f0" ' +
        'stroke-width="2" stroke-linecap="round"/>' +
        '<rect x="12.3" y="21.6" width="7.4" height="7.4" fill="none" stroke="#f0a3d0" ' +
        'stroke-width="2" stroke-linejoin="round"/></svg>';

    function say(text) {
        var m = document.getElementById("huMsg");
        if (m && text) m.textContent = text;
    }

    var api = {
        /* opts: { fw: "13.00", logEl: <element with the chain's own log>,
                   start: 0..100 } */
        mount: function (opts) {
            opts = opts || {};
            if (st.mounted) return api;
            st.mounted = true;

            var style = node("style");
            style.type = "text/css";
            style.appendChild(document.createTextNode(CSS));
            (document.head || document.documentElement).appendChild(style);

            var box = node("div", "hu");
            box.id = "hostui";
            var inner = node("div", "box");

            /* The label is set through innerHTML because it carries the glyph;
               nothing in it ever comes from the page or the chain. */
            var fwLabel = node("div", "fw");
            fwLabel.innerHTML = GLYPH + "<span>" +
                (opts.fw ? "PS4 \u00b7 " + opts.fw : "PS4") + "</span>";
            inner.appendChild(fwLabel);

            var pct = node("div", "pct");
            pct.id = "huPct";
            pct.appendChild(document.createTextNode("0"));
            pct.appendChild(node("i", "", "%"));
            inner.appendChild(pct);

            var bar = node("div", "bar");
            var fill = node("div", "fill");
            fill.id = "huFill";
            bar.appendChild(fill);
            inner.appendChild(bar);

            var msg = node("div", "msg", opts.msg || "Preparing\u2026");
            msg.id = "huMsg";
            inner.appendChild(msg);

            var again = node("button", "", "Try again");
            again.id = "huAgain";
            again.type = "button";
            again.onclick = function () { location.href = api.home || "../index.html"; };
            inner.appendChild(again);

            var det = node("div", "det");
            var link = node("a", "", "details");
            link.href = "#";
            det.appendChild(link);
            inner.appendChild(det);

            var log = node("div", "log");
            log.id = "huLog";
            inner.appendChild(log);
            st.logEl = opts.logEl || null;

            /* Read the chain's log only when asked: it grows to thousands of
               lines, and re-reading it during a kernel race is work that race
               must not have. */
            link.onclick = function (ev) {
                ev.preventDefault();
                var open = log.className === "log show";
                if (!open && st.logEl) {
                    var txt = st.logEl.textContent || "";
                    log.textContent = txt.length > 6000 ? txt.slice(-6000) : txt;
                }
                log.className = open ? "log" : "log show";
                link.textContent = open ? "details" : "hide";
            };

            box.appendChild(inner);
            (document.body || document.documentElement).appendChild(box);

            /* Always start from zero. The bar used to resume from a value left
               in sessionStorage by an earlier run, so a second unlock began at
               whatever the last one ended on -- which reads as progress that
               never happened. A run starts at 0 and earns each step. */
            st.pct = 0;
            paint();
            return api;
        },

        /* Set progress. Never 100 from here: only a confirmed payload does
           that, and it says so in words as well. */
        set: function (pct, text) {
            if (st.done) return;
            pct = Math.round(pct);
            if (pct > 99) pct = 99;
            if (pct < 0) pct = 0;
            if (pct < st.pct) return;
            st.pct = pct;
            store(pct);
            paint();
            say(text);
        },

        done: function (text, advice) {
            if (st.done) return;
            st.done = true;
            st.pct = 100;
            store(0);
            paint();
            var box = document.getElementById("hostui");
            if (box) box.className = "hu ok";
            say(text || "Unlock complete");
            if (advice) {
                var m = document.getElementById("huMsg");
                if (m) m.textContent = (text || "Unlock complete") + " \u2014 " + advice;
            }
            var again = document.getElementById("huAgain");
            if (again) again.className = "show";
        },

        fail: function (text, advice) {
            if (st.done) return;
            st.done = true;
            store(0);
            var box = document.getElementById("hostui");
            if (box) box.className = "hu bad";
            say(advice ? text + " \u2014 " + advice : text);
            var again = document.getElementById("huAgain");
            if (again) again.className = "show";
        },

        isDone: function () { return st.done; },
        pct: function () { return st.pct; },

        /* Some pages sit inside the host's folder and want to go back up. */
        home: "../index.html"
    };

    window.HostUI = api;
}());
