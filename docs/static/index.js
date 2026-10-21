(function () {
    var DIFFICULTY = { e: "Easy", m: "Medium", h: "Hard" };
    var MAX_RESULTS = 40;

    var tags = JSON.parse(document.getElementById("tags").textContent);
    var form = document.getElementById("filters");
    var map = document.getElementById("map");
    var count = document.getElementById("count");
    var results = document.getElementById("results");
    var clear = document.getElementById("clear");
    var tip = document.getElementById("tip");
    var blocks = Array.prototype.slice.call(map.querySelectorAll(".block"));

    var problems = Array.prototype.map.call(map.querySelectorAll("a.c"), function (el) {
        var label = el.getAttribute("aria-label");
        var dot = label.indexOf(". ");
        return {
            el: el,
            id: label.slice(0, dot),
            title: label.slice(dot + 2),
            lower: label.toLowerCase(),
            difficulty: el.classList[1],
            solved: el.classList.contains("s"),
            paid: el.classList.contains("p"),
            tags: el.dataset.g ? el.dataset.g.split(" ") : [],
        };
    });
    var byEl = new Map(problems.map(function (p) { return [p.el, p]; }));

    function state() {
        return {
            q: form.q.value.trim().toLowerCase(),
            d: form.d.value,
            s: form.s.value,
            t: form.t.value,
        };
    }

    function matches(p, f) {
        if (f.d && p.difficulty !== f.d) return false;
        if (f.s === "s" && !p.solved) return false;
        if (f.s === "u" && p.solved) return false;
        if (f.t && p.tags.indexOf(f.t) < 0) return false;
        if (f.q) return /^\d+$/.test(f.q) ? p.id === f.q || p.id.indexOf(f.q) === 0 : p.lower.indexOf(f.q) >= 0;
        return true;
    }

    function cell(p) {
        var i = document.createElement("i");
        i.className = p.el.className;
        return i;
    }

    function renderResults(hits) {
        results.textContent = "";
        hits.slice(0, MAX_RESULTS).forEach(function (p) {
            var li = document.createElement("li");
            var a = document.createElement("a");
            a.href = p.el.href;
            a.target = "_blank";
            a.rel = "noopener";
            var n = document.createElement("span");
            n.className = "n";
            n.textContent = p.id;
            var t = document.createElement("span");
            t.className = "t";
            t.textContent = p.title;
            a.append(cell(p), n, t);
            li.append(a);
            results.append(li);
        });
        if (hits.length > MAX_RESULTS) {
            var more = document.createElement("li");
            more.className = "more";
            more.textContent = "+ " + (hits.length - MAX_RESULTS) + " more highlighted on the map";
            results.append(more);
        }
    }

    function apply() {
        var f = state();
        var active = !!(f.q || f.d || f.s || f.t);
        var hits = [];
        problems.forEach(function (p) {
            var hit = active && matches(p, f);
            p.el.classList.toggle("hit", hit);
            if (hit) hits.push(p);
        });
        blocks.forEach(function (b) {
            b.classList.toggle("none", active && !b.querySelector(".hit"));
        });
        map.classList.toggle("filtering", active);
        count.textContent = active ? hits.length.toLocaleString() + " match" + (hits.length === 1 ? "" : "es") : "";
        clear.hidden = !active;
        results.hidden = !f.q || !hits.length;
        if (f.q) renderResults(hits);

        var params = new URLSearchParams();
        ["q", "d", "s", "t"].forEach(function (k) { if (form[k].value.trim()) params.set(k, form[k].value.trim()); });
        var qs = params.toString();
        history.replaceState(null, "", qs ? "?" + qs : location.pathname);
    }

    function restore() {
        var params = new URLSearchParams(location.search);
        form.q.value = params.get("q") || "";
        form.t.value = params.get("t") || "";
        ["d", "s"].forEach(function (k) {
            var input = form.querySelector('input[name="' + k + '"][value="' + (params.get(k) || "") + '"]');
            if (input) input.checked = true;
        });
    }

    form.addEventListener("input", apply);
    form.addEventListener("change", apply);
    clear.addEventListener("click", function () {
        form.reset();
        apply();
        form.q.focus();
    });
    document.addEventListener("keydown", function (e) {
        if (e.key === "/" && document.activeElement !== form.q) {
            e.preventDefault();
            form.q.focus();
        } else if (e.key === "Escape" && document.activeElement === form.q) {
            form.q.value = "";
            apply();
        }
    });

    function showTip(el) {
        var p = byEl.get(el);
        if (!p) return;
        var meta = [DIFFICULTY[p.difficulty], p.solved ? "Solved" : "Unsolved"];
        if (p.paid) meta.push("Premium");
        tip.innerHTML = "";
        var title = document.createElement("b");
        title.textContent = "#" + p.id + " " + p.title;
        var line = document.createElement("div");
        line.className = "meta";
        line.textContent = meta.join(" · ");
        tip.append(title, line);
        if (p.tags.length) {
            var tagLine = document.createElement("div");
            tagLine.className = "meta";
            tagLine.textContent = p.tags.map(function (t) { return tags[t]; }).join(", ");
            tip.append(tagLine);
        }
        tip.hidden = false;
        var r = el.getBoundingClientRect();
        var w = tip.offsetWidth;
        var h = tip.offsetHeight;
        var left = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), window.innerWidth - w - 8);
        var top = r.top - h - 8 < 8 ? r.bottom + 8 : r.top - h - 8;
        tip.style.left = left + "px";
        tip.style.top = top + "px";
    }

    function hideTip() { tip.hidden = true; }

    map.addEventListener("mouseover", function (e) { if (e.target.matches("a.c")) showTip(e.target); });
    map.addEventListener("mouseout", function (e) { if (e.target.matches("a.c")) hideTip(); });
    map.addEventListener("focusin", function (e) { if (e.target.matches("a.c")) showTip(e.target); });
    map.addEventListener("focusout", hideTip);
    window.addEventListener("scroll", hideTip, { passive: true });

    restore();
    apply();
})();
