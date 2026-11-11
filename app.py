from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# HARDCODE YOUR API KEY HERE
# ==========================================
client = genai.Client(api_key=st.secrets["AQ.Ab8RN6L5Yj6s3Hvm_lgRDDKycDq-WsTjm2i-IYxX2TWdxLV4qg"])

# Initialize Streamlit Page
st.set_page_config(
    page_title="OOPs Interactive Tutor", page_icon="⚡", layout="wide"
)

# System Instruction with strict formatting guidance
SYSTEM_INSTRUCTION = """
You are "OOPs Interactive Tutor", an expert software architecture and Object-Oriented Programming teaching assistant.

Guidelines:
1. When asked about concepts, explain clearly using a concise real-world analogy.
2. Provide precise, production-ready code snippets with inline comments.
3. Use language-specific best practices (e.g., virtual destructors in C++, interfaces in Java, dunder methods in Python).
4. If a user asks a quiz question or code prediction, provide hints first before revealing full answers.
"""


# Cache client initialization to prevent re-instantiating on every rerun
@st.cache_resource
def get_gemini_client(api_key: str):
  return genai.Client(api_key=api_key)


client = get_gemini_client(API_KEY)

# Initialize Chat Session in Streamlit State using Gemini 3.7 Flash
if "chat_session" not in st.session_state:
  st.session_state.chat_session = client.chats.create(
      model="gemini-3.7-flash",
      config=types.GenerateContentConfig(
          system_instruction=SYSTEM_INSTRUCTION,
          temperature=0.3,
          thinking_config={"thinking_level": "low"},  # Optimized for fast chat
      ),
  )

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "⚡ **Welcome to OOPs Interactive AI (Powered by Gemini 3.7"
          " Flash)!**\nPick a quick action from the sidebar or type any OOP"
          " question below to get started."
      ),
  }]

# ==========================================
# SIDEBAR CONTROLS & INTERACTIVE PRESETS
# ==========================================
with st.sidebar:
  st.title("⚙️ Interactive Controls")

  # Preferred Programming Language
  selected_lang = st.radio(
      "Preferred Code Language:", ["C++", "Python", "Java"], index=0
  )

  st.markdown("---")
  st.subheader("🚀 Quick Action Triggers")

  # Preset Action Buttons
  quiz_btn = st.button("❓ Give Me a Viva / Interview Quiz")
  debug_btn = st.button("🐞 Debug Common OOP Bug")
  design_btn = st.button("🏗️ Explain Design Pattern")
  clear_btn = st.button("🗑️ Clear Chat History")

# Clear chat logic
if clear_btn:
  st.session_state.messages = []
  st.session_state.chat_session = client.chats.create(
      model="gemini-3.7-flash",
      config=types.GenerateContentConfig(
          system_instruction=SYSTEM_INSTRUCTION,
          temperature=0.3,
          thinking_config={"thinking_level": "low"},
      ),
  )
  st.rerun()

# Determine if a sidebar quick action was triggered
preset_query = None
if quiz_btn:
  preset_query = f"Generate a challenging interview/viva question about OOP concepts using {selected_lang}. Include multiple choices and ask me to pick the correct answer."
elif debug_btn:
  preset_query = f"Show me a common OOP code bug/pitfall in {selected_lang} (e.g., object slicing, missing virtual destructor, or memory leak), ask me what's wrong, and explain the fix."
elif design_btn:
  preset_query = f"Explain the Factory Method design pattern with a real-world analogy and clean implementation code in {selected_lang}."

# ==========================================
# MAIN CHAT INTERFACE
# ==========================================
st.title("🎓 OOPs Interactive Learning Agent")
st.caption(
    f"Currently targeting code examples in **{selected_lang}** (Gemini 3.7"
    " Flash)"
)

# Display message history
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

# Capture user query
user_input = st.chat_input("Type your OOP question or code here...")
active_query = preset_query if preset_query else user_input

if active_query:
  final_prompt = (
      active_query
      if preset_query
      else f"[{selected_lang} Context] {active_query}"
  )

  st.session_state.messages.append({"role": "user", "content": active_query})
  with st.chat_message("user"):
    st.markdown(active_query)

  with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""

    try:
      response_stream = st.session_state.chat_session.send_message_stream(
          final_prompt
      )

      for chunk in response_stream:
        if chunk.text:
          full_response += chunk.text
          message_placeholder.markdown(full_response + "▌")

      message_placeholder.markdown(full_response)

      st.session_state.messages.append(
          {"role": "assistant", "content": full_response}
      )

    except Exception as e:
      st.error(f"Error communicating with Gemini: {e}")