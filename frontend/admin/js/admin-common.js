// admin-common.js
const AdminAPI = {
  base: '',
  async fetchJSON(path, opts = {}) {
    const url = this.base + path;
    const res = await fetch(url, Object.assign({credentials:'same-origin'}, opts));
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch(e){ data = text; }
    if (!res.ok) {
      console.error('API error', url, res.status, data);
      throw new Error(typeof data === 'string' ? data : (data.detail || res.statusText));
    }
    return data;
  },
  // try multiple endpoints in order, return first that succeeds (for order-related uncertainty)
  async tryEndpoints(paths, opts) {
    let lastErr = null;
    for (const p of paths) {
      try {
        return await this.fetchJSON(p, opts);
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr || new Error('No endpoints available');
  }
};

// Minimal toast
function toast(msg, time=3000){
  let el = document.createElement('div');
  el.textContent = msg;
  Object.assign(el.style,{position:'fixed',right:'18px',bottom:'18px',background:'#111',padding:'10px 14px',border:'1px solid #333',color:'#eee',zIndex:9999});
  document.body.appendChild(el);
  setTimeout(()=>el.remove(), time);
}

export { AdminAPI, toast };
