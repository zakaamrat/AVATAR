import streamlit as st
import streamlit.components.v1 as components
import base64
import os

st.set_page_config(page_title="Omani AI Tutor", layout="centered")

# --- 1. SECURE KEY ACCESS ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API Key Missing! Add 'GEMINI_API_KEY' to your Streamlit Secrets.")
    st.stop()

# --- 2. VIDEO ENCODING ---
def get_video_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

video_base64 = get_video_base64("omaniavata.mp4")
video_src = f"data:video/mp4;base64,{video_base64}" if video_base64 else ""

# --- 3. THE INTERFACE & LOGIC ---
html_template = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; text-align: center; margin: 0; }
        .container { width: 95%; max-width: 420px; margin: 20px auto; background: #1e293b; padding: 25px; border-radius: 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
        #avatar-box { width: 150px; height: 150px; border-radius: 50%; overflow: hidden; margin: 0 auto 15px; border: 4px solid #38bdf8; background: #000; }
        video { width: 100%; height: 100%; object-fit: cover; }
        #chat { height: 160px; overflow-y: auto; background: #0f172a; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; font-size: 0.9em; border: 1px solid #334155; }
        .controls { display: flex; gap: 10px; justify-content: center; }
        button { padding: 12px 20px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-mic { background: #22c55e; color: white; flex-grow: 2; }
        .btn-pdf { background: #fbbf24; color: #0f172a; flex-grow: 1; display: none; }
        #status { color: #38bdf8; font-size: 0.8em; margin-bottom: 8px; min-height: 1.2em; }
        .user-txt { color: #38bdf8; margin-bottom: 5px; }
        .ai-txt { color: #f1f5f9; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px; }
    </style>
</head>
<body>
    <div style="font-size: 0.7em; color: #64748b; margin-top: 15px;">FUNDED BY SHANNAQ</div>
    <div class="container">
        <div id="avatar-box">
            <video id="v" src="VIDEO_DATA" loop muted playsinline></video>
        </div>
        <div id="status">Click Start to begin</div>
        <div id="chat"></div>
        <div class="controls">
            <button id="mBtn" class="btn-mic" onclick="run()">🚀 Start Session</button>
            <button id="pBtn" class="btn-pdf" onclick="pdf()">📄 Report</button>
        </div>
    </div>

    <script type="module">
        import { GoogleGenerativeAI } from "https://esm.run/@google/generative-ai";

        const genAI = new GoogleGenerativeAI("MY_KEY");
        const model = genAI.getGenerativeModel({ 
            model: "gemini-3.1-flash-lite-preview",
            systemInstruction: "You are an English tutor for Omani students. Use a Case Study approach. Keep replies under 20 words. Correct grammar gently."
        });

        let active = false;
        let history = [];
        const v = document.getElementById('v');
        const s = document.getElementById('status');
        const c = document.getElementById('chat');

        const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new Speech();
        rec.lang = 'en-US';

        window.run = () => {
            if (!active) {
                active = true;
                document.getElementById('mBtn').innerText = "Mic Active...";
                document.getElementById('pBtn').style.display = "block";
                rec.start();
            } else {
                active = false;
                document.getElementById('mBtn').innerText = "🚀 Resume";
                rec.stop();
            }
        };

        rec.onresult = async (e) => {
            const msg = e.results[0][0].transcript;
            addMsg("You", msg, "user-txt");
            history.push({ role: "user", parts: [{ text: msg }] });
            
            s.innerText = "Thinking...";
            try {
                const res = await model.generateContent({ contents: history });
                const txt = res.response.text();
                history.push({ role: "model", parts: [{ text: txt }] });
                addMsg("Tutor", txt, "ai-txt");
                talk(txt);
            } catch (err) {
                if (err.message.includes("429")) {
                    s.innerText = "Quota limit! Wait 30 seconds.";
                } else {
                    s.innerText = "Error: Connection lost.";
                    console.error(err);
                }
            }
        };

        function talk(t) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(t.replace(/[*#]/g, ""));
            u.rate = 0.9;
            u.onstart = () => { v.play(); s.innerText = "Tutor Speaking..."; };
            u.onend = () => { v.pause(); s.innerText = "Listening..."; if(active) rec.start(); };
            window.speechSynthesis.speak(u);
        }

        window.pdf = async () => {
            s.innerText = "Generating SWOT...";
            const res = await model.generateContent("Create a 1-page SWOT report for this student: " + JSON.stringify(history));
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            doc.text("Omani English Tutor: Progress Report", 10, 20);
            doc.setFontSize(10);
            doc.text(doc.splitTextToSize(res.response.text(), 180), 10, 35);
            doc.save("Tutor_Report.pdf");
            s.innerText = "Downloaded!";
        };

        function addMsg(n, t, cls) {
            const d = document.createElement('div');
            d.className = cls;
            d.innerHTML = `<b>${n}:</b> ${t}`;
            c.appendChild(d);
            c.scrollTop = c.scrollHeight;
        }

        rec.onend = () => { if(active && !window.speechSynthesis.speaking) rec.start(); };
    </script>
</body>
</html>
"""

# --- 4. RENDER ---
final_html = html_template.replace("MY_KEY", gemini_key).replace("VIDEO_DATA", video_src)
components.html(final_html, height=580)
