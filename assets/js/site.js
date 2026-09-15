/* ADHDme — site.js
   Three jobs, nothing else: mark the page as scripted so arrivals can run,
   let the floating nav arrive once the hero has left the viewport, and
   reveal the consult steps as they enter. Reduced motion skips all three. */
(function () {
  var root = document.documentElement;
  root.classList.remove("no-js");
  root.classList.add("js");

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var floating = document.querySelector("[data-floating]");
  var hero = document.querySelector("[data-hero]");
  var reveals = document.querySelectorAll("[data-reveal]");

  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
    if (floating) { floating.hidden = false; floating.classList.add("is-on"); }
    return;
  }

  // Floating nav: absent over the hero, arrives when less than 8% of it remains.
  if (floating && hero) {
    floating.hidden = false;
    new IntersectionObserver(function (entries) {
      var heroVisible = entries[0].isIntersecting;
      floating.classList.toggle("is-on", !heroVisible);
    }, { threshold: 0.08 }).observe(hero);
  }

  // Reveals: once, when a quarter of the element is in view.
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
    });
  }, { threshold: 0.25, rootMargin: "0px 0px -8% 0px" });
  reveals.forEach(function (el) { io.observe(el); });
})();
