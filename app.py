import streamlit as st
import datetime
from google import genai

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="CBSE Class 10 Study Planner & AI Tutor",
    page_icon="📚",
    layout="wide"
)

# ==========================================
# 2. AUTOMATED API KEY RESOLUTION (Local + Cloud Safe)
# ==========================================
api_key = None

# Safely check Streamlit Secrets without throwing FileNotFoundError locally
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    # Triggered when running locally on your laptop without a secrets.toml file
    pass

# Fallback: If not found in secrets, prompt in sidebar for local testing
if not api_key:
    st.sidebar.warning("⚠️ Secrets file not found (Local Mode). Enter your key manually:")
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

# Stop execution until a key is provided
if not api_key:
    st.info("👈 Please enter your Gemini API Key in the sidebar (or configure Secrets on Streamlit Cloud) to start.")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=api_key)


# ==========================================
# 3. DYNAMIC DATE & DASHBOARD COUNTER
# ==========================================
st.sidebar.title("⚙️ Exam Settings")

# Default exam milestone: November 13, 2026
default_exam_date = datetime.date(2026, 11, 13)
exam_date = st.sidebar.date_input("Target Exam Date", value=default_exam_date)

today = datetime.date.today()
days_remaining = (exam_date - today).days

# Title Header & Countdown Counter
st.title("📚 CBSE Class 10 AI Tutor & Study Companion")
st.caption("Powered by Gemini AI | Deployed on Streamlit Cloud")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="Days Remaining", 
        value=f"{days_remaining} Days" if days_remaining >= 0 else "Exam Completed"
    )
with col2:
    st.metric(label="Target Date", value=exam_date.strftime("%b %d, %Y"))
with col3:
    st.metric(label="Status", value="On Track" if days_remaining > 0 else "Exam Day!")

st.divider()

# ==========================================
# 4. CHAT HISTORY & TUTOR INTERFACE
# ==========================================
# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": f"Hello! I'm your CBSE Class 10 AI Tutor. You have **{days_remaining} days** remaining until your exam on {exam_date.strftime('%B %d, %Y')}. What concept, NCERT problem, or revision schedule should we tackle today?"
        }
    ]

# Render previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask a question (e.g., 'Explain Quadratic Equations' or 'Give me 5 practice questions for Science')"):
    # Append & display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response from Gemini API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                system_instruction = (
                    f"You are an expert CBSE Class 10 AI tutor. Today's date is {today.strftime('%Y-%m-%d')}. "
                    f"The student's target exam date is {exam_date.strftime('%Y-%m-%d')} ({days_remaining} days away). "
                    "Provide clear, encouraging, step-by-step explanations strictly aligned with NCERT guidelines."
                )

                # Using official current active Flash endpoint
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config={
                        "system_instruction": system_instruction,
                        "temperature": 0.7
                    }
                )
                
                bot_reply = response.text
                st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            except Exception as e:
                err_msg = str(e)
                # Catches temporary 429 quota/spike limit errors on the free tier
                if any(k in err_msg.lower() for k in ["429", "resource_exhausted", "spike", "quota"]):
                    st.warning("⏱️ Free Tier usage limit reached temporarily. Please wait 15–20 seconds and resubmit your question!")
                else:
                    st.error(f"API Error: {err_msg}")