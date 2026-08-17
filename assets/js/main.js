/* 婚礼请柬 H5 — 交互
 * 无依赖。所有内容写在 index.html 里，这里只管行为。
 */
(function () {
  "use strict";

  var deck = document.querySelector(".deck");
  var scenes = Array.prototype.slice.call(document.querySelectorAll(".scene"));

  /* ── 启幕：等封面图加载完（最多等 2.5 秒）───────────── */

  var curtain = document.getElementById("curtain");
  var hero = document.querySelector(".cover .bg img");

  function raiseCurtain() {
    if (!curtain || curtain.classList.contains("done")) return;
    curtain.classList.add("done");
    var first = scenes[0];
    if (first) first.classList.add("in");
  }

  if (hero && !hero.complete) {
    hero.addEventListener("load", raiseCurtain);
    hero.addEventListener("error", raiseCurtain);
  }
  setTimeout(raiseCurtain, 2500);
  if (hero && hero.complete) setTimeout(raiseCurtain, 300);

  /* ── 场景入场 + 进度点 ──────────────────────────────── */

  var dots = document.getElementById("dots");
  var dotList = [];

  if (dots) {
    scenes.forEach(function (_, i) {
      var d = document.createElement("i");
      if (i === 0) d.className = "on";
      dots.appendChild(d);
      dotList.push(d);
    });
  }

  function setActive(i) {
    dotList.forEach(function (d, j) {
      d.classList.toggle("on", j === i);
    });
    if (dots) dots.classList.toggle("dark", scenes[i].classList.contains("paper"));
  }

  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          e.target.classList.add("in");
          var i = scenes.indexOf(e.target);
          if (i > -1) setActive(i);
        });
      },
      { threshold: 0.55 }
    );
    scenes.forEach(function (s) {
      io.observe(s);
    });
  } else {
    scenes.forEach(function (s) {
      s.classList.add("in");
    });
  }

  /* ── 背景音乐 ───────────────────────────────────────
   * 微信内置浏览器可以借 WeixinJSBridgeReady 绕过自动播放限制；
   * 其它环境退化为「首次触屏时播放」。音频文件缺失则隐藏按钮。
   */

  var audio = document.getElementById("bgm");
  var btn = document.getElementById("music");

  if (audio && btn) {
    var wanted = true; // 用户是否希望播放

    audio.addEventListener("error", function () {
      btn.style.display = "none";
    });

    function paint() {
      btn.classList.toggle("playing", !audio.paused);
      btn.classList.toggle("muted", audio.paused);
      btn.setAttribute("aria-label", audio.paused ? "播放音乐" : "暂停音乐");
    }

    function play() {
      if (!wanted) return;
      var p = audio.play();
      if (p && p.catch) p.catch(function () {});
    }

    audio.addEventListener("play", paint);
    audio.addEventListener("pause", paint);

    btn.addEventListener("click", function () {
      wanted = audio.paused;
      if (audio.paused) play();
      else audio.pause();
      paint();
    });

    // 微信
    if (window.WeixinJSBridge) {
      play();
    } else {
      document.addEventListener("WeixinJSBridgeReady", play, false);
    }
    // 其它浏览器：首次交互
    ["touchstart", "click"].forEach(function (evt) {
      document.addEventListener(evt, function once() {
        play();
        document.removeEventListener(evt, once);
      });
    });

    paint();
  }

  /* ── 灯箱 ───────────────────────────────────────────── */

  var lb = document.getElementById("lightbox");
  var track = document.getElementById("lb-track");
  var count = document.getElementById("lb-count");
  var closeBtn = document.getElementById("lb-close");
  var shots = [];

  document.querySelectorAll(".strip").forEach(function (strip) {
    var group = Array.prototype.slice.call(strip.querySelectorAll("button"));
    group.forEach(function (b, i) {
      b.addEventListener("click", function () {
        open(group, i);
      });
    });
  });

  function open(group, index) {
    if (!lb || !track) return;
    shots = group;
    track.innerHTML = "";
    group.forEach(function (b) {
      var fig = document.createElement("figure");
      var img = document.createElement("img");
      img.src = b.dataset.full;
      img.alt = b.dataset.alt || "";
      fig.appendChild(img);
      track.appendChild(fig);
    });
    lb.classList.add("open");
    // 必须等 display 生效后再定位
    requestAnimationFrame(function () {
      track.scrollLeft = index * track.clientWidth;
      tally();
    });
  }

  function tally() {
    if (!count || !track.clientWidth) return;
    var i = Math.round(track.scrollLeft / track.clientWidth);
    count.textContent = i + 1 + " / " + shots.length;
  }

  if (track) track.addEventListener("scroll", tally, { passive: true });

  function close() {
    if (lb) lb.classList.remove("open");
  }

  if (closeBtn) closeBtn.addEventListener("click", close);
  if (track) {
    track.addEventListener("click", function (e) {
      if (e.target.tagName !== "IMG") close();
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") close();
  });

  /* ── 复制地址 ───────────────────────────────────────── */

  document.querySelectorAll("[data-copy]").forEach(function (el) {
    el.addEventListener("click", function () {
      var text = el.dataset.copy;
      var done = function () {
        var old = el.textContent;
        el.textContent = "已复制";
        setTimeout(function () {
          el.textContent = old;
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand("copy");
          done();
        } catch (err) {
          /* 复制失败就算了，地址本身在页面上可见 */
        }
        document.body.removeChild(ta);
      }
    });
  });

  /* ── 下滑提示：滚动后隐藏 ───────────────────────────── */

  var hint = document.querySelector(".hint");
  if (hint && deck) {
    deck.addEventListener(
      "scroll",
      function () {
        hint.style.opacity = deck.scrollTop > 40 ? "0" : "";
      },
      { passive: true }
    );
  }
})();
