(function(){
  "use strict";

  async function loadFragment(url, targetId){
    try{
      var res = await fetch(url, { cache: "no-store" });
      if(!res.ok) throw new Error("HTTP " + res.status);

      var html = await res.text();
      var target = document.getElementById(targetId);
      if(!target) return null;

      target.innerHTML = html;
      return target;
    }catch(err){
      console.error("Failed to load fragment:", url, err);
      return null;
    }
  }

  function detectPage(){
    var path = window.location.pathname.toLowerCase();

    if(path.indexOf("prediction_history.html") >= 0) return "prediction_history";
    if(path.indexOf("prediction.html") >= 0) return "prediction";
    if(path.indexOf("overlay.html") >= 0) return "overlay";
    if(path.indexOf("sentiment.html") >= 0) return "sentiment";
    if(path.indexOf("digest.html") >= 0) return "digest";
    return "index";
  }

  function applyHeaderActive(headerRoot){
    if(!headerRoot) return;

    var page = detectPage();
    var links = headerRoot.querySelectorAll(".nav-link");

    links.forEach(function(link){
      if(link.dataset.page === page){
        link.classList.add("active");
        link.setAttribute("aria-current", "page");
      }else{
        link.classList.remove("active");
        link.removeAttribute("aria-current");
      }
    });
  }

  async function initLayout(){
    var headerRoot = await loadFragment("/static/common/header.html", "site-header");
    applyHeaderActive(headerRoot);

    await loadFragment("/static/common/footer.html", "site-footer");
  }

  document.addEventListener("DOMContentLoaded", initLayout);

  window.GPLayout = {
    initLayout: initLayout,
    detectPage: detectPage,
    applyHeaderActive: applyHeaderActive
  };
})();