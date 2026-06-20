/* DPDP Chatbot — embeddable website widget.
 *
 * Drop into any site:
 *   <script src="https://YOUR_HOST/widget.js" data-api="https://YOUR_HOST"></script>
 *
 * Creates a floating launcher + chat panel inside a Shadow DOM so the host page's
 * CSS cannot interfere with it (and vice-versa). Talks to POST {api}/api/chat.
 */
(function () {
  var script = document.currentScript;
  var API = (script && script.getAttribute("data-api")) || window.location.origin;

  // --- host element + shadow root (style isolation) ---
  var host = document.createElement("div");
  host.id = "dpdp-widget-host";
  document.body.appendChild(host);
  var root = host.attachShadow({ mode: "open" });

  root.innerHTML = `
  <style>
    :host { all: initial; }
    * { box-sizing: border-box; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
    .launcher {
      position: fixed; bottom: 22px; right: 22px; z-index: 2147483000;
      width: 60px; height: 60px; border-radius: 50%; border: 0; cursor: pointer;
      background: #1f6feb; color: #fff; font-size: 26px; box-shadow: 0 6px 22px rgba(0,0,0,.25);
    }
    .launcher:hover { background: #1a5fd0; }
    .panel {
      position: fixed; bottom: 94px; right: 22px; z-index: 2147483000;
      width: 370px; max-width: calc(100vw - 32px); height: 540px; max-height: calc(100vh - 130px);
      background: #fff; border-radius: 16px; box-shadow: 0 14px 50px rgba(0,0,0,.28);
      display: none; flex-direction: column; overflow: hidden; border: 1px solid #e6e8eb;
    }
    .panel.open { display: flex; }
    .head { background: #11243d; color: #fff; padding: 14px 16px; }
    .head h3 { margin: 0; font-size: 15px; font-weight: 600; }
    .head p { margin: 2px 0 0; font-size: 11.5px; opacity: .75; }
    .head .x { position: absolute; top: 12px; right: 14px; background: none; border: 0; color: #fff;
               font-size: 20px; cursor: pointer; opacity: .8; }
    .body { flex: 1; overflow-y: auto; padding: 14px; background: #f6f7f9; }
    .m { margin-bottom: 12px; display: flex; }
    .m.u { justify-content: flex-end; }
    .b { padding: 9px 13px; border-radius: 13px; max-width: 86%; font-size: 14px; line-height: 1.5; white-space: pre-wrap; }
    .u .b { background: #1f6feb; color: #fff; border-bottom-right-radius: 4px; }
    .a .b { background: #fff; color: #1c2430; border: 1px solid #e6e8eb; border-bottom-left-radius: 4px; }
    .src { margin-top: 6px; font-size: 11px; color: #6b7280; }
    .src b { color: #11243d; font-weight: 600; }
    .warn { font-size: 11px; color: #9a6b00; margin-top: 4px; }
    .foot { display: flex; gap: 8px; padding: 10px; border-top: 1px solid #eceef1; background: #fff; }
    .foot input { flex: 1; border: 1px solid #d7dbe0; border-radius: 10px; padding: 10px 12px; font-size: 14px; }
    .foot input:focus { outline: none; border-color: #1f6feb; }
    .foot button { border: 0; background: #1f6feb; color: #fff; border-radius: 10px; padding: 0 16px; cursor: pointer; font-weight: 600; }
    .foot button:disabled { opacity: .5; cursor: default; }
    .dis { font-size: 10.5px; color: #9aa1ab; text-align: center; padding: 0 10px 8px; background: #fff; }
    .dots span { display:inline-block; width:6px; height:6px; border-radius:50%; background:#9aa1ab; margin-right:3px; animation: bl 1s infinite; }
    .dots span:nth-child(2){animation-delay:.15s} .dots span:nth-child(3){animation-delay:.3s}
    @keyframes bl { 0%,80%,100%{opacity:.25} 40%{opacity:1} }
  </style>

  <button class="launcher" id="launch" aria-label="Open DPDP assistant">💬</button>
  <div class="panel" id="panel">
    <div class="head" style="position:relative">
      <h3>DPDP Assistant</h3>
      <p>Ask about India's Digital Personal Data Protection Act</p>
      <button class="x" id="close" aria-label="Close">×</button>
    </div>
    <div class="body" id="body"></div>
    <div class="foot">
      <input id="inp" placeholder="Ask a DPDP question…" autocomplete="off">
      <button id="send">Send</button>
    </div>
    <div class="dis">Answers come from the DPDP document · general info, not legal advice</div>
  </div>`;

  var $ = function (id) { return root.getElementById(id); };
  var body = $("body"), inp = $("inp"), send = $("send"), panel = $("panel");

  function esc(s) { return s.replace(/[&<>]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]; }); }

  function bubble(text, who, extra) {
    var m = document.createElement("div"); m.className = "m " + who;
    m.innerHTML = '<div class="b">' + esc(text) + (extra || "") + "</div>";
    body.appendChild(m); body.scrollTop = body.scrollHeight; return m;
  }

  function typing() {
    var m = document.createElement("div"); m.className = "m a"; m.id = "typing";
    m.innerHTML = '<div class="b"><span class="dots"><span></span><span></span><span></span></span></div>';
    body.appendChild(m); body.scrollTop = body.scrollHeight;
  }

  async function ask() {
    var q = inp.value.trim(); if (!q) return;
    inp.value = ""; send.disabled = true;
    bubble(q, "u"); typing();
    try {
      var r = await fetch(API + "/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q }),
      });
      var d = await r.json();
      var t = root.getElementById("typing"); if (t) t.remove();
      var extra = "";
      if (d.sources && d.sources.length) {
        var pages = [...new Set(d.sources.map(function (s) { return s.page; }))].join(", ");
        extra = '<div class="src"><b>Source:</b> DPDP document, page ' + esc(String(pages)) + "</div>";
      }
      if (d.ollama_ok === false) extra += '<div class="warn">⚠ Local model offline — showing retrieval only.</div>';
      bubble(d.answer, "a", extra);
    } catch (e) {
      var t2 = root.getElementById("typing"); if (t2) t2.remove();
      bubble("Could not reach the assistant. Please try again.", "a");
    }
    send.disabled = false; inp.focus();
  }

  $("launch").onclick = function () {
    panel.classList.add("open");
    if (!body.childElementCount)
      bubble("Hi! I answer questions about India's DPDP Act — consent, your rights, breach rules, penalties, children's data, and more. What would you like to know?", "a");
    inp.focus();
  };
  $("close").onclick = function () { panel.classList.remove("open"); };
  send.onclick = ask;
  inp.addEventListener("keydown", function (e) { if (e.key === "Enter") ask(); });
})();
