import streamlit as st
import streamlit.components.v1 as components
import base64
import os

st.set_page_config(page_title="Omani AI Tutor", layout="centered")

# --- 1. SECURE KEY ACCESS ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Please add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 2. VIDEO PROCESSING ---
# This converts your mp4 into a string so the iframe can't block it
def get_video_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    return None

video_base64 = get_video_base64("omaniavata.mp4")
video_src = f"data:video/mp4;base64,{video_base64}" if video_base64 else ""

# --- 3. THE COMPLETE HTML/JS ---
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; text-align: center; margin: 0; }}
        .container {{ width: 100%; max-width: 450px; margin: 20px auto; background: #1e293b; padding: 20px; border-radius: 24px; }}
        #avatar-container {{ width: 160px; height: 160px; border-radius: 50%; overflow: hidden; margin: 0 auto 15px; border: 4px solid #38bdf8; }}
        video {{ width: 100%; height: 100%; object-fit: cover; object-position: center 15%; }}
        #chat-window {{ height: 180px; overflow-y: auto; background: #0f172a; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; font-size: 0.85em; border: 1px solid #334155; }}
        button {{ padding: 12px 20px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; background: #38bdf8; color: #0f172a; }}
        #status {{ color: #38bdf8; font-size: 0.8em; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div style="font-size: 0.7em; color: #94a3b8; margin-top: 10px;">FUNDED BY SHANNAQ</div>
    <div class="container">
        <div id="avatar-container">
            <video id="avatarVideo" src="{video_src}" loop muted playsinline></video>
        </div>
        <div id="status">Ready</div>
        <div id="chat-window"></div>
        <button id="mainBtn" onclick="toggleSession()">🚀 Start Tutor</button>
    </div>

   <script type="module">
        import { GoogleGenerativeAI } from "https://esm.run/@google/generative-ai";

        const genAI = new GoogleGenerativeAI("{gemini_key}");
        // Updated to the 2026 stable model ID
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

        let isSessionActive = false;
        const video = document.getElementById('avatarVideo');
        const chatWindow = document.getElementById('chat-window');

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';

        window.toggleSession = function() {
            if (!isSessionActive) {
                isSessionActive = true;
                document.getElementById('mainBtn').innerText = "Stop Session";
                recognition.start();
            } else {
                isSessionActive = false;
                document.getElementById('mainBtn').innerText = "🚀 Start Tutor";
                recognition.stop();
            }
        };

        recognition.onresult = async (event) => {
            const prompt = event.results[0][0].transcript;
            appendMsg("You", prompt);
            
            document.getElementById('status').innerText = "Thinking...";

            try {
                // Simplified call for better reliability in 2026 SDK
                const result = await model.generateContent("You are an English tutor for Omani students. Answer briefly and correct this: " + prompt);
                const response = await result.response;
                const text = response.text();
                
                appendMsg("Tutor", text);
                speak(text);
            } catch (err) {
                document.getElementById('status').innerText = "Error: Model not found or API issue.";
                console.error("Full Error:", err);
            }
        };

        // ... keep the rest of your speak and appendMsg functions the same ...
    </script>

        function speak(text) {{
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(text.replace(/\*/g, ''));
            utter.rate = 0.8;
            utter.onstart = () => {{ video.play(); document.getElementById('status').innerText = "Speaking..."; }};
            utter.onend = () => {{ 
                video.pause(); 
                document.getElementById('status').innerText = "Listening...";
                if(isSessionActive) recognition.start(); 
            }};
            window.speechSynthesis.speak(utter);
        }}

        function appendMsg(who, txt) {{
            const d = document.createElement('div');
            d.innerHTML = `<b>${{who}}:</b> ${{txt}}`;
            d.style.marginBottom = "8px";
            chatWindow.appendChild(d);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }}

        recognition.onend = () => {{ if(isSessionActive && !window.speechSynthesis.speaking) recognition.start(); }};
    </script>
</body>
</html>
"""

# --- 4. RENDER WITH PERMISSIONS ---
# This is the most important part to fix your errors
components.html(html_code, height=600, scrolling=False)
