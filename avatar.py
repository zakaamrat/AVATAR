import streamlit as st
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="Omani AI Tutor", layout="centered")

# 2. Access the API Key from Streamlit Secrets
# (We will set this up in Step 2)
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API Key not found! Please add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# 3. Define the HTML & JS Code
# Note: I've updated the script to receive the key from Python
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; text-align: center; margin: 0; padding: 10px; }}
        .funding-notice {{ font-size: 0.8em; color: #94a3b8; letter-spacing: 2px; margin-bottom: 20px; }}
        .container {{ width: 100%; max-width: 450px; margin: auto; background: #1e293b; padding: 20px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        #avatar-container {{ width: 150px; height: 150px; border-radius: 50%; overflow: hidden; margin: 0 auto 15px; border: 4px solid #38bdf8; background: #000; }}
        video {{ width: 100%; height: 100%; object-fit: cover; object-position: center 15%; }}
        #chat-window {{ height: 200px; overflow-y: auto; background: #0f172a; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; font-size: 0.85em; border: 1px solid #334155; }}
        .msg {{ margin-bottom: 8px; padding: 8px; border-radius: 8px; }}
        .ai-msg {{ background: #334155; border-left: 3px solid #38bdf8; }}
        .user-msg {{ background: #38bdf8; color: #0f172a; margin-left: 10%; }}
        .controls {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        button {{ padding: 12px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; }}
        .btn-start {{ background: #22c55e; color: white; }}
        .btn-report {{ background: #fbbf24; color: #0f172a; }}
    </style>
</head>
<body>
    <div class="funding-notice">This work is funded by Shannaq</div>
    <div class="container">
        <div id="avatar-container">
        <video id="avatarVideo" src="https://github.com/zakaamrat/AVATAR/blob/main/omaniavata.mp4" loop muted playsinline></video>

        </div>
        <div id="status" style="font-size:0.8em; margin-bottom:10px; color:#38bdf8;">Ready to start...</div>
        <div id="chat-window"></div>
        <div class="controls">
            <button id="mainBtn" class="btn-start" onclick="toggleSession()">🚀 Start Session</button>
            <button id="reportBtn" class="btn-report" onclick="generateReport()" style="display:none;">📄 Get SWOT PDF</button>
        </div>
    </div>

    <script type="module">
        import {{ GoogleGenAI }} from "https://esm.run/@google/genai";

        // THE KEY IS INJECTED HERE BY PYTHON
        const API_KEY = "{gemini_key}"; 
        const ai = new GoogleGenAI({{ apiKey: API_KEY }});
        
        const video = document.getElementById('avatarVideo');
        const status = document.getElementById('status');
        const chatWindow = document.getElementById('chat-window');
        let isSessionActive = false;
        let chatHistory = [{{ role: "user", parts: [{{ text: "You are an English tutor for Omani students. Use a Case Study approach. Keep spoken replies very short and slow. Correct mistakes gently." }}] }}];

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';

        window.toggleSession = function() {{
            if (!isSessionActive) {{
                isSessionActive = true;
                document.getElementById('mainBtn').innerText = "Stop Mic";
                document.getElementById('reportBtn').style.display = "block";
                recognition.start();
            }} else {{
                isSessionActive = false;
                document.getElementById('mainBtn').innerText = "🚀 Resume";
                recognition.stop();
            }}
        }};

        recognition.onresult = async (event) => {{
            const text = event.results[0][0].transcript;
            appendMessage('user-msg', text);
            chatHistory.push({{ role: "user", parts: [{{ text: text }}] }});
            
            try {{
                const result = await ai.models.generateContent({{
                    model: "gemini-2.5-flash",
                    contents: chatHistory,
                }});
                const aiText = result.text;
                appendMessage('ai-msg', aiText);
                chatHistory.push({{ role: "model", parts: [{{ text: aiText }}] }});
                speak(aiText);
            }} catch (e) {{ console.error(e); }}
        }};

        recognition.onend = () => {{ if (isSessionActive && !window.speechSynthesis.speaking) recognition.start(); }};

        function speak(text) {{
            window.speechSynthesis.cancel();
            const cleanText = text.replace(/\*\*/g, "").replace(/\*/g, "").replace(/#/g, "");
            const utter = new SpeechSynthesisUtterance(cleanText);
            utter.rate = 0.8;
            utter.onstart = () => {{ video.play(); status.innerText = "Tutor Speaking..."; }};
            utter.onend = () => {{ 
                video.pause(); 
                video.currentTime = 0; 
                status.innerText = "Listening..."; 
                if(isSessionActive) recognition.start(); 
            }};
            window.speechSynthesis.speak(utter);
        }}

        window.generateReport = async function() {{
            const prompt = "Summarize the student progress in SWOT format.";
            chatHistory.push({{ role: "user", parts: [{{ text: prompt }}] }});
            const result = await ai.models.generateContent({{ model: "gemini-2.5-flash", contents: chatHistory }});
            const reportData = result.text;
            
            const {{ jsPDF }} = window.jspdf;
            const doc = new jsPDF();
            doc.text("Shannaq Funding: English SWOT Report", 10, 20);
            doc.setFontSize(10);
            doc.text(doc.splitTextToSize(reportData, 180), 10, 30);
            doc.save("Tutor_Report.pdf");
        }};

        function appendMessage(className, text) {{
            const div = document.createElement('div');
            div.className = `msg ${{className}}`;
            div.innerText = text;
            chatWindow.appendChild(div);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }}
    </script>
</body>
</html>
"""

# 4. Render the Component
components.html(html_code, height=650)
