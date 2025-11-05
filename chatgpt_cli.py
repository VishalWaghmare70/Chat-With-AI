import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ Please set your OpenAI API key in a .env file as OPENAI_API_KEY=your_key")
    exit()

client = OpenAI(api_key=api_key)

app = Flask(__name__)

SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful and intelligent AI assistant."}

HTML_PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Chat — Single Exchange</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    :root{--bg:#f5f7fa;--panel:#ffffff;--user:#0a66c2;--assistant:#0a9d58;--muted:#6b7280}
    body{background:var(--bg);font-family:Inter,Segoe UI,Roboto,Arial,sans-serif;margin:0;height:100vh;display:flex;align-items:center;justify-content:center}
    .container{width:100%;max-width:760px;height:90vh;background:linear-gradient(180deg,rgba(255,255,255,.6),rgba(255,255,255,.9));box-shadow:0 10px 30px rgba(2,6,23,.08);border-radius:12px;display:flex;flex-direction:column;overflow:hidden}
    header{padding:18px 22px;border-bottom:1px solid rgba(15,23,42,.04);display:flex;align-items:center;gap:12px}
    header h1{font-size:16px;margin:0}
    .chat{flex:1;padding:18px;overflow:auto;display:flex;flex-direction:column;gap:12px;background:transparent}
    .bubble{max-width:78%;padding:12px 14px;border-radius:14px;box-shadow:0 1px 0 rgba(15,23,42,.02);line-height:1.35}
    .user{align-self:flex-end;background:linear-gradient(90deg,var(--user),#084a9a);color:#fff;border-bottom-right-radius:6px}
    .assistant{align-self:flex-start;background:var(--panel);color:#0b2f18;border-bottom-left-radius:6px;border:1px solid rgba(10,10,10,.03)}
    .meta{font-size:12px;color:var(--muted);margin-top:6px}
    .composer{padding:12px;border-top:1px solid rgba(15,23,42,.04);display:flex;gap:8px;background:rgba(255,255,255,.9)}
    .input{flex:1;display:flex;gap:8px}
    textarea{width:100%;resize:none;border-radius:10px;padding:10px 12px;border:1px solid rgba(15,23,42,.06);font-size:14px;min-height:48px;max-height:140px}
    button{background:var(--user);color:#fff;padding:10px 14px;border-radius:10px;border:none;cursor:pointer;font-weight:600}
    button:disabled{opacity:.5;cursor:default}
    footer{padding:10px 14px;text-align:center;font-size:12px;color:var(--muted);border-top:1px solid rgba(15,23,42,.02)}
    @media (max-width:520px){.container{height:96vh;border-radius:8px}}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Simple Chat — Single Exchange (no history saved)</h1>
    </header>

    <div id="chat" class="chat" aria-live="polite"></div>

    <div class="composer">
      <div class="input">
        <textarea id="msg" placeholder="Ask anything — response will be shown below."></textarea>
      </div>
      <div>
        <button id="send">Send</button>
      </div>
    </div>

    <footer>Note: Conversation is not stored on the server. Each send creates a single request/response.</footer>
  </div>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('msg');
const sendBtn = document.getElementById('send');

function appendBubble(text, who){
  const d = document.createElement('div');
  d.className = 'bubble ' + (who === 'user' ? 'user' : 'assistant');
  d.innerText = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}

function setLoading(enabled){
  sendBtn.disabled = enabled;
  input.disabled = enabled;
  sendBtn.innerText = enabled ? 'Thinking…' : 'Send';
}

sendBtn.addEventListener('click', async () => {
  const txt = input.value.trim();
  if(!txt) return;
  appendBubble(txt, 'user');
  input.value = '';
  setLoading(true);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: txt})
    });
    const data = await res.json();
    if(res.ok && data.reply){
      appendBubble(data.reply, 'assistant');
    } else {
      appendBubble('[Error] ' + (data.error || JSON.stringify(data)), 'assistant');
    }
  } catch(err){
    appendBubble('[Network error] ' + err.message, 'assistant');
  } finally{
    setLoading(false);
  }
});

input.addEventListener('keydown', (e)=>{
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault();
    sendBtn.click();
  }
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "empty message"}), 400

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[SYSTEM_PROMPT, {"role": "user", "content": user_msg}],
            temperature=0.7,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        reply = f"[Error from API: {e}]"
    return jsonify({"reply": reply})

if __name__ == "__main__":
    print("Starting web UI at http://127.0.0.1:5000")
    app.run(debug=True)
