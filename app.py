import os
from pathlib import Path
import time
from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# PAGE CONFIG (Must be the first Streamlit call)
# ==========================================
st.set_page_config(
    page_title="OOPs Interactive Tutor", page_icon="⚡", layout="wide"
)

AVAILABLE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
]

SYSTEM_INSTRUCTION = """
You are "OOPs Interactive Tutor", an expert software architecture and Object-Oriented Programming teaching assistant.

Guidelines:
1. When asked about concepts, explain clearly using a concise real-world analogy.
2. Provide precise, production-ready code snippets with inline comments.
3. Use language-specific best practices (e.g., virtual destructors in C++, interfaces in Java, dunder methods in Python).
4. If a user asks a quiz question or code prediction, provide hints first before revealing full answers.
"""


def load_env_file() -> None:
  """Load .env from the app directory (or current working directory)."""
  env_path = Path(__file__).resolve().parent / ".env"
  if not env_path.exists():
    env_path = Path.cwd() / ".env"
  if not env_path.exists():
    return

  try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=env_path, override=True)
    return
  except ImportError:
    pass

  # Built-in fallback if python-dotenv is not installed
  for raw_line in env_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    if line.startswith("export "):
      line = line[len("export ") :].strip()
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
      value = value[1:-1]
    if key:
      os.environ[key] = value


def get_api_key() -> str:
  load_env_file()
  env_key = os.environ.get("GEMINI_API_KEY", "").strip()
  if env_key:
    return env_key
  try:
    return st.secrets.get("GEMINI_API_KEY", "").strip()
  except Exception:
    return ""


@st.cache_resource
def get_gemini_client(api_key: str):
  return genai.Client(api_key=api_key, vertexai=False)


def build_sdk_history(messages: list[dict]) -> list[types.Content]:
  history = []
  for m in messages:
    role = "model" if m["role"] == "assistant" else "user"
    history.append(
        types.Content(role=role, parts=[types.Part(text=m["content"])])
    )
  return history


def create_chat_session(client, model_id: str, history=None):
  return client.chats.create(
      model=model_id,
      config=types.GenerateContentConfig(
          system_instruction=SYSTEM_INSTRUCTION,
          temperature=0.3,
      ),
      history=history or [],
  )


api_key = get_api_key()

if not api_key:
  st.error(
      "`GEMINI_API_KEY` not found. Add `GEMINI_API_KEY=your_key` to your `.env`"
      " file next to `app.py` and restart Streamlit."
  )
  st.stop()

client = get_gemini_client(api_key)

# ==========================================
# SIDEBAR CONTROLS & INTERACTIVE PRESETS
# ==========================================
with st.sidebar:
  st.title("⚙️ Interactive Controls")

  selected_model = st.selectbox("Gemini Model:", AVAILABLE_MODELS, index=0)

  selected_lang = st.radio(
      "Preferred Code Language:", ["C++", "Python", "Java"], index=0
  )

  st.markdown("---")
  st.subheader("🚀 Quick Action Triggers")

  quiz_btn = st.button("❓ Give Me a Viva / Interview Quiz")
  debug_btn = st.button("🐞 Debug Common OOP Bug")
  design_btn = st.button("🏗️ Explain Design Pattern")
  clear_btn = st.button("🗑️ Clear Chat History")

# Initialize or reset session when API key or selected model changes
if (
    "chat_session" not in st.session_state
    or st.session_state.get("active_api_key") != api_key
    or st.session_state.get("active_model") != selected_model
):
  existing_msgs = st.session_state.get("messages", [])
  st.session_state.chat_session = create_chat_session(
      client,
      selected_model,
      history=build_sdk_history(existing_msgs),
  )
  st.session_state.active_api_key = api_key
  st.session_state.active_model = selected_model

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "⚡ **Welcome to OOPs Interactive AI (Powered by"
          f" `{selected_model}`)!**\nPick a quick action from the sidebar or"
          " type any OOP question below to get started."
      ),
  }]

# Clear chat logic
if clear_btn:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          f"⚡ **Chat cleared! Ready with `{selected_model}`.**\n"
          "Pick a quick action from the sidebar or type any OOP question"
          " below."
      ),
  }]
  st.session_state.chat_session = create_chat_session(client, selected_model)
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
    f"Currently targeting code examples in **{selected_lang}** (`{st.session_state.active_model}`)"
)

for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

user_input = st.chat_input("Type your OOP question or code here...")
active_query = preset_query if preset_query else user_input

if active_query:
  final_prompt = (
      active_query
      if preset_query
      else f"[{selected_lang} Context] {active_query}"
  )

  prior_history = build_sdk_history(st.session_state.messages)

  st.session_state.messages.append({"role": "user", "content": active_query})
  with st.chat_message("user"):
    st.markdown(active_query)

  with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""

    models_to_try = [st.session_state.active_model] + [
        m for m in AVAILABLE_MODELS if m != st.session_state.active_model
    ]

    last_error = None
    succeeded = False

    for model_idx, model_name in enumerate(models_to_try):
      if model_idx > 0:
        message_placeholder.info(
            f"`{models_to_try[model_idx - 1]}` is busy (503). Switching to"
            f" `{model_name}`..."
        )
        st.session_state.chat_session = create_chat_session(
            client, model_name, history=prior_history
        )
        st.session_state.active_model = model_name

      for attempt in range(2):
        try:
          full_response = ""
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
          succeeded = True
          break

        except Exception as e:
          last_error = e
          err_str = str(e)
          is_transient = any(
              code in err_str
              for code in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
          )
          if is_transient and not full_response:
            if attempt == 0:
              message_placeholder.info(
                  f"`{model_name}` is experiencing high demand. Retrying..."
              )
              time.sleep(1.5)
              continue
            break
          else:
            break

      if succeeded:
        break
      if last_error and not any(
          code in str(last_error)
          for code in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
      ):
        break

    if not succeeded:
      message_placeholder.empty()
      st.error(f"Error communicating with Gemini: {last_error}")