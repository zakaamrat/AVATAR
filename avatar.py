import streamlit as st
import streamlit.components.v1 as components
import base64
import os

st.set_page_config(page_title="Omani AI Tutor", layout="centered")

# --- 1. SECURE KEY ACCESS ---
# Make sure to add GEMINI_API_KEY to your Streamlit Secrets dashboard
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API Key not found! Go to Streamlit Settings > Secrets and add: GEMINI_API_KEY = 'YOUR_KEY'")
    st.stop()

# --- 2. VIDEO ENCODING ---
def get_video_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

video_base64 = get_video_base64("omaniavata.mp4")
# Fallback message if video is missing
if not video_base64:
    st.warning("Video file 'omaniavata.mp4' not found in the repository folder.")
video_src = f"data:video/mp4;base64,{video_base64}" if video_base64 else ""

# --- 3. HTML TEMPLATE ---
# Using a regular string to avoid f-string { } curly brace errors
html_template = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; text-align: center; margin: 0; overflow: hidden; }
        .container { width: 95%; max-width: 450px; margin: 10px auto; background: #1e293b; padding: 20px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        #avatar-container { width: 140px; height: 140px; border-radius: 50%; overflow: hidden; margin: 0 auto 15px; border: 4px solid #38bdf8; background: #000; }
        video { width: 100%; height: 100%; object-fit: cover; object-position: center 15%; }
        #chat-window { height: 150px; overflow-y: auto; background: #0f172a; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; font-size: 0.85em; border: 1px solid #334155; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button { padding: 12px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn-start { background: #22c55e; color: white; }
        .btn-report { background: #fbbf24; color: #0f172a; }
        button:hover { opacity: 0.8; }
        #status { color: #38bdf8; font-size: 0.75em; margin-bottom: 5px; height: 15px; }
    </style>
</head>
<body>
    <div style="font-size: 0.7em; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">FUNDED BY SHANNAQ</div>
    <div class="container">
        <div id="avatar-container">
            <video id="avatarVideo" src="VIDEO_SOURCE_HERE" loop muted playsinline></video>
        </div>
        <div id="status">Ready</div>
        <div id="chat-window">
            <div style="color:#94a3b8">Tutor: Marhaba! Click Start to begin the Omani Case Study practice.</div>
        </div>
        <div class="controls">
            <button id="mainBtn" class="btn-start" onclick="toggleSession()">🚀 Start Tutor</button>
            <button id="reportBtn" class="btn-report" onclick="generateReport()" style="display:none;">📄 Get SWOT</button>
        </div>
    </div>

    <script type="module">
    import { GoogleGenerativeAI } from "https://esm.run/@google/generative-ai";

    const genAI = new GoogleGenerativeAI("API_KEY_HERE");
    // Use the 2026 Ultra-Efficient Stable Model
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash-lite" });

    let isSessionActive = false;
    let lastCall = 0; // Cooldown timer

    // ... (rest of your video and recognition setup) ...

    recognition.onresult = async (event) => {
        const now = Date.now();
        if (now - lastCall < 2000) return; // Wait 2 seconds between requests
        lastCall = now;

        const prompt = event.results[0][0].transcript;
        appendMsg("You", prompt);
        
        status.innerText = "Tutor is thinking...";
        try {
            const result = await model.generateContent({
                contents: [{ role: "user", parts: [{ text: "You are an English tutor for Omani students. Answer briefly: " + prompt }] }]
            });
            const text = result.response.text();
            appendMsg("Tutor", text);
            speak(text);
        } catch (err) {
            if (err.message.includes("429")) {
                status.innerText = "Quota full. Wait 1 minute.";
            } else {
                status.innerText = "Error: " + err.message;
            }
        }
    };
</script>
</body>
</html>
"""

# --- 4. DATA INJECTION & RENDER ---
final_html = html_template.replace("API_KEY_HERE", gemini_key).replace("VIDEO_SOURCE_HERE", video_src)
components.html(final_html, height=550)
