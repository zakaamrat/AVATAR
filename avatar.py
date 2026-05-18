import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from google import genai

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

# --- 3. INITIALIZE BACKEND CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize Python GenAI Client securely 
client = genai.Client(api_key=gemini_key)

# --- 4. STREAMLIT BACKEND LISTENER ---
# This catches the text from the browser mic, processes it via Python safely, and updates the response
query_params = st.query_params
if "user_speech" in query_params:
    user_text = query_params["user_speech"]
    
    # Append to state history
    st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_text}]})
    
    # Secure server-to-server call to Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=st.session_state.chat_history,
            config={"system_instruction": "You are an English tutor for Omani students. Use a Case Study approach. Keep replies under 20 words. Correct grammar gently."}
        )
        ai_response = response.text
        st.session_state.chat_history.append({"role": "model", "parts": [{"text": ai_response}]})
    except Exception as e:
        ai_response = "Sorry, I am having trouble connecting to my brain right now."
    
    # Clear the parameter so it doesn't loop
    st.query_params.clear()
    # Force rerun to push the new message down to the HTML app
    st.rerun()

# --- 5. INTERFACE TEMPLATE ---
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
        .btn-pdf { background: #fbbf24; color: #0f172a; flex-grow: 1; }
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
        <div id="chat">CHAT_HISTORY_DATA</div>
        <div class="controls">
            <button id="mBtn" class="btn-mic" onclick="run()">🚀 Start Session</button>
            <button id="pBtn" class="btn-pdf" onclick="pdf()">📄 Report</button>
        </div>
    </div>

    <script>
        let active = false;
        const v = document.getElementById('v');
        const s = document.getElementById('status');
        const c = document.getElementById('chat');
        c.scrollTop = c.scrollHeight;

        const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new Speech();
        rec.lang = 'en-US';

        window.run = () => {
            if (!active) {
                active = true;
                document.getElementById('mBtn').innerText = "Mic Active...";
                s.innerText = "Listening...";
                rec.start();
            } else {
                active = false;
                document.getElementById('mBtn').innerText = "🚀 Resume";
                rec.stop();
            }
        };

        rec.onresult = (e) => {
            const msg = e.results[0][0].transcript;
            s.innerText = "Sending to Python backend...";
            
            // SAFELY SEND TEXT BACK TO PYTHON VIA URL COMPONENT PARAMETERS
            parent.window.location.search = `?user_speech=${encodeURIComponent(msg)}`;
        };

        // Automatic voice playback for the last incoming Tutor message
        window.addEventListener('load', () => {
            const messages = document.getElementsByClassName('ai-txt');
            if(messages.length > 0) {
                const lastTutorMsg = messages[messages.length - 1].innerText.replace("Tutor:", "").trim();
                talk(lastTutorMsg);
            }
        });

        function talk(t) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(t);
            u.rate = 0.9;
            u.onstart = () => { v.play(); s.innerText = "Tutor Speaking..."; };
            u.onend = () => { v.pause(); s.innerText = "Session Active"; };
            window.speechSynthesis.speak(u);
        }

        window.pdf = () => {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            doc.text("Omani English Tutor: Progress Report", 10, 20);
            doc.setFontSize(10);
            let textOutput = c.innerText || "No sessions recorded yet.";
            doc.text(doc.splitTextToSize(textOutput, 180), 10, 35);
            doc.save("Tutor_Report.pdf");
        };
    </script>
</body>
</html>
"""

# --- 6. RENDER DATA CONVERSION ---
# Render messages dynamically out of Streamlit's server history cache
chat_html_injection = ""
for msg in st.session_state.chat_history:
    role_class = "user-txt" if msg["role"] == "user" else "ai-txt"
    role_name = "You" if msg["role"] == "user" else "Tutor"
    text_content = msg["parts"][0]["text"]
    chat_html_injection += f'<div class="{role_class}"><b>{role_name}:</b> {text_content}</div>'

final_html = html_template.replace("CHAT_HISTORY_DATA", chat_html_injection).replace("VIDEO_DATA", video_src)
components.html(final_html, height=580)
