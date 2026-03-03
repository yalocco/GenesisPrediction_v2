
(function(){
  const NAV_HTML = `
  <div class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <div class="brand-dot"></div>
        <div class="brand-title">GenesisPrediction v2</div>
      </div>
      <div class="topnav">
        <a href="/static/index.html?v=20260303v2" class="pill" data-page="index">Home</a>
        <a href="/static/overlay.html?v=20260303v2" class="pill" data-page="overlay">Overlay</a>
        <a href="/static/sentiment.html?v=20260303v2" class="pill" data-page="sentiment">Sentiment</a>
        <a href="/static/digest.html?v=20260303v2" class="pill" data-page="digest">Digest</a>
        <span class="pill good"><span class="dot"></span>Ready</span>
        <span class="pill mono">Health: --</span>
        <span class="pill mono">as_of: --</span>
      </div>
    </div>
  </div>`;

  document.addEventListener("DOMContentLoaded", function(){
    document.body.insertAdjacentHTML("afterbegin", NAV_HTML);

    // auto active detection
    const path = window.location.pathname;
    let page = "index";
    if (path.includes("overlay")) page = "overlay";
    if (path.includes("sentiment")) page = "sentiment";
    if (path.includes("digest")) page = "digest";

    document.querySelectorAll(".pill[data-page]").forEach(el=>{
      if (el.dataset.page === page){
        el.classList.add("active");
      }
    });
  });
})();
