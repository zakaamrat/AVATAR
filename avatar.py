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

# --- 3. SESSION STATE FOR CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_ai_response" not in st.session_state:
    st.session_state.last_ai_response = "Hello! Click Start Session once, and we can just talk freely."

client = genai.Client(api_key=gemini_key)

# --- 4. STREAMLIT APP LAYOUT (CUSTOM CSS) ---
st.markdown(f"""
<style>
    .reportview-container {{ background: #0f172a; }}
    .container {{ width: 100%; max-width: 420px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); text-align: center; color: white; font-family: 'Segoe UI', sans-serif;}}
    .avatar-box {{ width: 150px; height: 150px; border-radius: 50%; overflow: hidden; margin: 0 auto 15px; border: 4px solid #38bdf8; background: #000; }}
    video {{ width: 100%; height: 100%; object-fit: cover; }}
    .chat-box {{ height: 200px; overflow-y: auto; background: #0f172a; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; font-size: 0.9em; border: 1px solid #334155; color: white; }}
    .user-txt {{ color: #38bdf8; margin-bottom: 5px; }}
    .ai-txt {{ color: #f1f5f9; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px; }}
    .funding {{ font-size: 0.7em; color: #64748b; text-align: center; margin-bottom: 5px;}}
    
    /* Completely hide Streamlit's structural widget borders around our bridge */
    div[data-testid="stForm"] {{ border: none !important; padding: 0 !important; }}
</style>
""", unsafe_allow_html=True)

# Render Interface Top
st.markdown('<div class="funding">FUNDED BY SHANNAQ</div>', unsafe_allow_html=True)

# Build HTML structural container
container_html = f"""
<div class="container">
    <div class="avatar-box">
        <video id="avatar-vid" src="{video_src}" loop autoplay muted playsinline></video>
    </div>
</div>
"""
st.markdown(container_html, unsafe_allow_html=True)

# --- 5. THE AUTOMATED DATA BRIDGE ---
# We use a native Streamlit form with a hidden text input that JavaScript can submit automatically
with st.form(key="speech_form", clear_on_submit=True):
    # This input acts as our data pipeline catcher
    user_voice_transcript = st.text_input("Hidden Voice Input", key="hidden_voice", label_visibility="collapsed")
    submit_button = st.form_submit_with_no_label = st.form_submit_button(label="Processing...", help="Hidden submit trigger")

# If text enters our hidden form, Python immediately processes it safely server-to-server
if user_voice_transcript:
    st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_voice_transcript}]})
    with st.spinner("Tutor is thinking..."):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=st.session_state.chat_history,
                config={"system_instruction": "You are an English tutor for Omani students. Use a Case Study approach. Keep replies under 20 words. Correct grammar gently."}
            )
            ai_text = response.text
            st.session_state.last_ai_response = ai_text
            st.session_state.chat_history.append({"role": "model", "parts": [{"text": ai_text}]})
        except Exception as e:
            st.error(f"Error: {e}")

# --- 6. CHAT HISTORY DISPLAY ---
st.write("### 💬 Conversation Log")
st.markdown('<div class="chat-box">', unsafe_allow_html=True)
for msg in st.session_state.chat_history:
    role_class = "user-txt" if msg["role"] == "user" else "ai-txt"
    role_name = "You" if msg["role"] == "user" else "Tutor"
    text_content = msg["parts"][0]["text"]
    st.markdown(f'<div class="{role_class}"><b>{role_name}:</b> {text_content}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. CONTINUOUS HANDS-FREE JAVASCRIPT CONTROLLER ---
# This controller handles continuous microphone listening and plays back audio smoothly without breaking
js_interface = f"""
<div style="text-align:center;">
    <button id="mBtn" style="padding: 12px 30px; background:#22c55e; color:white; border-radius:12px; border:none; font-weight:bold; cursor:pointer;" onclick="toggleSession()">🎙️ Start Continuous Session</button>
    <div id="status" style="color: #38bdf8; font-size: 0.85em; margin-top: 10px;">Click above to turn on hands-free mode</div>
</div>

<script>
    let active = false;
    let isSpeaking = false;
    const s = document.getElementById('status');
    const mBtn = document.getElementById('mBtn');

    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech();
    rec.lang = 'en-US';
    rec.continuous = false; // We use explicit single-turn triggers linked with TTS hooks for total stability

    window.toggleSession = () => {{
        if (!active) {{
            active = true;
            mBtn.innerText = "🛑 Stop Continuous Session";
            mBtn.style.background = "#ef4444";
            startListening();
        }} else {{
            active = false;
            isSpeaking = false;
            mBtn.innerText = "🎙️ Start Continuous Session";
            mBtn.style.background = "#22c55e";
            s.innerText = "Session Stopped.";
            rec.stop();
            window.speechSynthesis.cancel();
        }}
    }};

    function startListening() {{
        if(!active || isSpeaking) return;
        s.innerText = "Listening... Speak now!";
        try {{ rec.start(); }} catch(e) {{}}
    }}

    rec.onresult = (e) => {{
        const msg = e.results[0][0].transcript;
        s.innerText = "Processing speech...";
        
        // Find Streamlit's native input field outside the iframe and insert the text
        const inputs = parent.document.getElementsByTagName('input');
        if(inputs.length > 0) {{
            inputs[0].value = msg;
            inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            // Find the hidden form's submit button and click it automatically
            setTimeout(() => {{
                const buttons = parent.document.getElementsByTagName('button');
                for(let b of buttons) {{
                    if(b.innerText === "Processing...") {{
                        b.click();
                        break;
                    }}
                }}
            }}, 200);
        }}
    }};

    // Fallback automated recovery loop if the student goes silent
    rec.onend = () => {{
        if(active && !isSpeaking) {{
            setTimeout(startListening, 400);
        }}
    }};

    // Automatically check for incoming responses on page update
    window.addEventListener('load', () => {{
        const lastResponse = "{st.session_state.last_ai_response.replace('"', "'").replace('\\n', ' ')}";
        if(lastResponse && lastResponse !== "Hello! Click Start Session once, and we can just talk freely.") {{
            talk(lastResponse);
        }}
    }});

    function talk(text) {{
        isSpeaking = true;
        rec.stop();
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        
        utterance.onstart = () => {{
            s.innerText = "Tutor is speaking...";
            const vids = parent.document.getElementsByTagName('video');
            for(let v of vids) {{ v.play(); }}
        }};
        
        utterance.onend = () => {{
            const vids = parent.document.getElementsByTagName('video');
            for(let v of vids) {{ v.pause(); }}
            isSpeaking = false;
            if(active) {{
                setTimeout(startListening, 300);
            }}
        }};
        
        window.speechSynthesis.speak(utterance);
    }}
</script>
"""
components.html(js_interface, height=100)

# --- 8. EXPORT REPORT FUNCTION ---
st.write("")
if st.button("📄 Generate Progress Report"):
    st.success("Creating SWOT analysis based on session performance...")
    if len(st.session_state.chat_history) > 0:
        report_res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Create a short 1-page SWOT progress report for an Omani student based on this chat log data: {str(st.session_state.chat_history)}"
        )
        st.text_area("Your Academic Report", value=report_res.text, height=250)
    else:
        st.warning("Please complete at least one conversation turn to parse a report profile.")
