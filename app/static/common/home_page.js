// Purified home_page.js
(function(){
  function safe(val, fallback='—'){
    return (val !== undefined && val !== null && val !== '') ? val : fallback;
  }

  function getSentimentItemsCount(sentiment, gs){
    if (sentiment?.today?.articles != null) {
      return sentiment.today.articles;
    }
    if (gs?.cards?.sentiment_items != null) {
      return gs.cards.sentiment_items;
    }
    return '—';
  }

  async function init(){
    const res = await fetch('/analysis/global_status_latest.json');
    const gs = await res.json();

    const sentiment = gs?.sentiment || {};

    const el = document.getElementById('sentiment-count');
    if (el){
      el.textContent = safe(getSentimentItemsCount(sentiment, gs));
    }
  }

  init();
})();
