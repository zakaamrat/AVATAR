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

        // Placeholders replaced by Python
        const genAI = new GoogleGenerativeAI("API_KEY_HERE");
      const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

        let isSessionActive = false;
        let chatHistory = [];
        const video = document.getElementById('avatarVideo');
        const status = document.getElementById('status');
        const chatWindow = document.getElementById('chat-window');

        // Setup Voice Recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;

        window.toggleSession = function() {
            if (!isSessionActive) {
                isSessionActive = true;
                document.getElementById('mainBtn').innerText = "Stop Mic";
                document.getElementById('reportBtn').style.display = "block";
                recognition.start();
            } else {
                isSessionActive = false;
                document.getElementById('mainBtn').innerText = "🚀 Resume";
                recognition.stop();
            }
        };

        recognition.onresult = async (event) => {
            const prompt = event.results[0][0].transcript;
            appendMsg("You", prompt);
            chatHistory.push({ role: "user", parts: [{ text: prompt }] });
            
            status.innerText = "Tutor is thinking...";
            try {
                const result = await model.generateContent({
                    contents: chatHistory,
                    systemInstruction: "You are an English tutor for Omani students. Use Case Studies. Keep spoken replies under 25 words. Correct grammar briefly."
                });
                const aiText = result.response.text();
                chatHistory.push({ role: "model", parts: [{ text: aiText }] });
                appendMsg("Tutor", aiText);
                speak(aiText);
            } catch (err) {
                // This will print the actual error (like 403 Forbidden or 429 Too Many Requests)
    status.innerText = "Error: " + err.message; 
    console.error("Detailed Error:", err);
            }
        };

        function speak(text) {
            window.speechSynthesis.cancel();
            const cleanText = text.replace(/[*#]/g, "");
            const utter = new SpeechSynthesisUtterance(cleanText);
            utter.rate = 0.8;
            utter.onstart = () => { video.play(); status.innerText = "Speaking..."; };
            utter.onend = () => { 
                video.pause(); 
                status.innerText = "Listening...";
                if(isSessionActive) recognition.start(); 
            };
            window.speechSynthesis.speak(utter);
        }

        window.generateReport = async function() {
            status.innerText = "Creating PDF...";
            const reportPrompt = "Create a SWOT analysis for this student based on our chat. Format: STRENGTHS, WEAKNESSES, OPPORTUNITIES, THREATS. Add a 1-week plan.";
            try {
                const result = await model.generateContent(reportPrompt + " Context: " + JSON.stringify(chatHistory));
                const data = result.response.text();
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF();
                doc.setFontSize(14);
                doc.text("Shannaq Funding: Omani English Training Plan", 10, 20);
                doc.setFontSize(10);
                doc.text(doc.splitTextToSize(data, 180), 10, 30);
                doc.save("English_Plan.pdf");
                status.innerText = "Downloaded!";
            } catch (e) { alert("PDF Error"); }
        };

        function appendMsg(who, txt) {
            const d = document.createElement('div');
            d.innerHTML = `<b>${who}:</b> ${txt}`;
            d.style.marginBottom = "5px";
            chatWindow.appendChild(d);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        recognition.onend = () => { if(isSessionActive && !window.speechSynthesis.speaking) recognition.start(); };
    </script>
</body>
</html>
"""

# --- 4. DATA INJECTION & RENDER ---
final_html = html_template.replace("API_KEY_HERE", gemini_key).replace("VIDEO_SOURCE_HERE", video_src)
components.html(final_html, height=550)
