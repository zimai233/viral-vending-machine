// 抖音博主主页：统计视频链接数（含正确转义）
(function () {
  try {
    return JSON.stringify({
      links: document.querySelectorAll('a[href*="/video/"]').length
    });
  } catch (e) {
    return JSON.stringify({ error: e.message });
  }
})();
