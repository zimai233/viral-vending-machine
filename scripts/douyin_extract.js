// 抖音博主主页：提取所有视频卡片
// DOM 结构: li.innerText = "点赞数\n\n标题/正文..."
(function () {
  try {
    const out = [];
    const anchors = document.querySelectorAll('a[href*="/video/"]');
    const seen = {};
    for (const a of anchors) {
      const m = (a.getAttribute('href') || '').match(/\/video\/(\d+)/);
      if (!m) continue;
      const id = m[1];
      if (seen[id]) continue;
      seen[id] = true;
      let container = a.closest('li') || a.parentElement || a;
      const txt = (container.innerText || '').trim();
      // 首行是点赞数（可能带万），剩余是标题/正文
      const lines = txt.split('\n').map(s => s.trim()).filter(Boolean);
      let likesRaw = '';
      let title = '';
      if (lines.length > 0) {
        const first = lines[0];
        const lm = first.match(/^([\d.]+)\s*万?$/);
        if (lm) {
          likesRaw = lm[1];
          if (first.includes('万')) likesRaw += '万';
          title = lines.slice(1).join('\n');
        } else {
          title = txt;
        }
      }
      out.push({ id: id, title: title, likesRaw: likesRaw, txt: txt });
    }
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ error: e.message });
  }
})();
