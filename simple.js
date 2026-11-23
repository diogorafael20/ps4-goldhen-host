/* Adapter for the older hosts (5.05 / 6.72 / 7.00 / 9.00).
 *
 * Those folders carry a vendor page whose layout is a wall of payload
 * buttons and a raw status line. Nothing here replaces that logic: the same
 * global functions the buttons call are the ones called below, so the exploit
 * runs exactly as it did -- only what is on screen changes, and it now uses
 * the same percentage screen as every other host.
 *
 * Loaded after the host's own scripts, with window.SIMPLE_AUTO naming the
 * function to call once the host is ready (or "" when it starts by itself).
 */
(function () {
    if (window.__SIMPLE_UI) return;
    window.__SIMPLE_UI = true;

    var AUTO = window.SIMPLE_AUTO;
    var UI = window.HostUI;

    function $(id) { return document.getElementById(id); }

    function fwFromUa() {
        var m = (navigator.userAgent || "").match(/PlayStation\s+4[\/ ](\d+)\.(\d+)/);
        if (!m) return "";
        var minor = parseInt(m[2], 16);
        var hex = minor.toString(16);
        if (hex.length < 2) hex = "0" + hex;
        return m[1] + "." + hex;
    }

    /* Every one of these hosts reports through one of three lines: #msgs2 and
     * #msgs carry the plain status, #log carries the PSFree loader's notices,
     * and #console the raw stage output. Only the last is used for the bar. */
    function readStatus() {
        var a = $("msgs2"), b = $("msgs"), c = $("log"), t = "";
        if (a) t += a.textContent || "";
        if (b && b !== a) t += " " + (b.textContent || "");
        if (c) t += " " + (c.textContent || "");
        return t;
    }

    function readStages() {
        var c = $("console");
        return c ? (c.textContent || "") : "";
    }

    function judge(t) {
        if (!t || UI.isDone()) return;

        /* Order matters: "already loaded" and the failure lines must be read
         * before the generic success test, or both come out as success. */
        if (/already/i.test(t)) {
            UI.done("Unlock complete", "it was already unlocked");
            return;
        }
        if (/Unsupported|not supported/i.test(t)) {
            UI.fail("Firmware not supported", "this unlock does not apply to this console");
            return;
        }
        if (/Failed to Load|Restart your Console|[Cc]ache failed|Load failed|Cannot [Ll]oad|error in loadPayload|network error/i.test(t)) {
            UI.fail("Failed", "close and reopen the browser, then try again");
            return;
        }
        if (/Loading GoldHEN|Please Wait/i.test(t)) {
            UI.set(88, "Loading GoldHEN\u2026");
            return;
        }
        if (/Loaded|Success|succeeded/i.test(t)) {
            UI.done("Unlock complete", "GoldHEN is running");
            return;
        }
        if (/Installing Offline Cache/i.test(t)) {
            var m = t.match(/(\d+)%/);
            UI.set(4, "Saving the files\u2026 " + (m ? m[1] + "%" : ""));
            return;
        }
        if (/caching|Checking offline cache/i.test(t)) {
            UI.set(3, "Checking the files\u2026");
            return;
        }
        if (/Jailbreak|Exploit|Starting/i.test(t)) {
            UI.set(20, "Exploiting the flaw\u2026");
        }
    }

    /* The PSFree hosts print their stages into #console; those lines are the
     * only honest progress signal for the middle of the run. */
    function judgeStages(s) {
        if (!s || UI.isDone()) return;
        if (/load GoldHen succeeded/i.test(s)) { UI.set(97, "Loading GoldHEN\u2026"); return; }
        if (/STAGE: [Pp]atch kernel/i.test(s)) { UI.set(84, "Applying the patches\u2026"); return; }
        if (/STAGE: Get arbitrary kernel read\/write|make_kernel_arw/i.test(s)) { UI.set(66, "Opening a path into the kernel\u2026"); return; }
        if (/STAGE: Get string relative read|make_rdr/i.test(s)) { UI.set(48, "Reading system memory\u2026"); return; }
        if (/STAGE: UAF SSV|prepare_uaf/i.test(s)) { UI.set(30, "Exploiting the flaw\u2026"); return; }
        if (/STAGE:|Exploiting/i.test(s)) { UI.set(16, "Preparing the exploit\u2026"); return; }
    }

    function watch(el, fn) {
        if (!el || !window.MutationObserver) return;
        new MutationObserver(fn).observe(el, { childList: true, characterData: true, subtree: true });
    }

    function callAuto() {
        if (!AUTO) return;
        var fn = window[AUTO];
        if (typeof fn === "function") {
            try { fn(); } catch (e) {}
        }
    }

    function boot() {
        /* Hide the vendor page; the exploit keeps running behind the overlay. */
        var app = document.querySelector(".app");
        if (app) app.style.display = "none";
        var sup = document.querySelector(".pspulse-support");
        if (sup) sup.style.display = "none";

        UI.mount({ fw: fwFromUa(), msg: "Preparing\u2026", logEl: $("console") || $("log") });

        var statusFn = function () { judge(readStatus()); };
        var stageFn = function () { judgeStages(readStages()); };

        watch($("msgs2"), statusFn);
        watch($("msgs"), statusFn);
        watch($("log"), statusFn);
        watch($("console"), stageFn);

        judge(readStatus());
        judgeStages(readStages());

        /* 5.05 only shows its payload menu once the kernel stage has finished,
         * so the GoldHEN call waits for that rather than for a clock. */
        var controls = $("controls");
        if (AUTO && controls && controls.style.display === "none") {
            watch(controls, function () {
                if (controls.style.display !== "none") callAuto();
            });
        } else if (AUTO) {
            setTimeout(callAuto, 600);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot, false);
    } else {
        boot();
    }
}());
