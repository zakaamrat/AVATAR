import streamlit as st
import base64
import os
from google import genai
from streamlit_mic_recorder import mic_recorder

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
    st.session_state.last_ai_response = "Hello! Click the record button below to speak to me."

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

# --- 5. AUDIO INPUT & BACKEND PROCESSING ---
st.write("")
audio_data = mic_recorder(
    start_prompt="🚀 Start Speaking",
    stop_prompt="🛑 Stop & Send to Tutor",
    key='tutor_mic'
)

if audio_data:
    with st.spinner("Tutor is listening and preparing response..."):
        try:
            # Package the user speech bytes directly to Gemini Multimodal
            audio_part = genai.types.Part.from_bytes(
                data=audio_data['bytes'],
                mime_type="audio/wav"
            )
            
            # Send context history and fresh voice stream directly to Gemini
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "System instruction: You are an expert English tutor for Omani students. Use a Case Study approach. Keep replies under 20 words. Correct grammar gently.",
                    audio_part
                ]
            )
            
            # Extract Text and update history
            ai_text = response.text
            st.session_state.last_ai_response = ai_text
            st.session_state.chat_history.append({"role": "You", "text": "🗣️ Sent voice message"})
            st.session_state.chat_history.append({"role": "Tutor", "text": ai_text})
            
        except Exception as e:
            st.error(f"Connection Exception: {e}")

# --- 6. CHAT HISTORY DISPLAY ---
st.write("### 💬 Conversation Log")
chat_placeholder = st.empty()
with chat_placeholder.container():
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        cls = "user-txt" if msg["role"] == "You" else "ai-txt"
        st.markdown(f'<div class="{cls}"><b>{msg["role"]}:</b> {msg["text"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. BROWSER TEXT TO SPEECH AUDIO TRIGGER ---
# This injects clean JS execution to read the latest response text out loud and animate your video profile
js_speech_trigger = f"""
<script>
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance("{st.session_state.last_ai_response.replace('"', "'")}");
    utterance.rate = 0.9;
    
    utterance.onstart = () => {{
        const vids = parent.document.getElementsByTagName('video');
        for(let v of vids) {{ v.play(); }}
    }};
    utterance.onend = () => {{
        const vids = parent.document.getElementsByTagName('video');
        for(let v of vids) {{ v.pause(); }}
    }};
    
    window.speechSynthesis.speak(utterance);
</script>
"""
components.html(js_speech_trigger, height=0, width=0)

# --- 8. EXPORT REPORT FUNCTION ---
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
