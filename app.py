import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from PIL import Image
import os
import base64
from io import BytesIO

load_dotenv()

# ===== Clipboard Function =====
def copy_to_clipboard(text):
    """Copy text to clipboard using JavaScript"""
    js = f"""
    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText(`{text}`);
    }}
    copyToClipboard();
    </script>
    """
    st.components.v1.html(js)

# ===== Image Helper =====
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def add_logo(logo_path, width=100):
    """Read and resize a logo image"""
    logo = Image.open(logo_path)
    modified_logo = logo.resize((width, int(width * logo.size[1] / logo.size[0])))
    return modified_logo

# ===== Enhanced Language Detection =====
def should_translate(text, target_language):
    """Improved detection that properly identifies different languages"""
    detection_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Analyze this text to determine if it needs translation to {target_language}.
        Follow these rules:
        1. Return 'True' if the text is in a different language than {target_language}
        2. Return 'True' if the text contains mixed languages
        3. Return 'False' ONLY if the text is entirely in {target_language}
        
        Examples:
        - Text: "Bonjour" → Target: English → Return 'True'
        - Text: "Hello" → Target: English → Return 'False'
        - Text: "Namaste" → Target: Hindi → Return 'True'
        - Text: "Yeh mera kutta hai" → Target: English → Return 'True'
        
        Respond ONLY with 'True' or 'False'."""),
        ("user", "{text}")
    ])
    
    groq_llm = ChatGroq(model="llama3-8b-8192", temperature=0)
    prompt = detection_prompt.invoke({"text": text})
    response = groq_llm.invoke(prompt).content.strip().lower()
    return response == 'true'

# ===== Custom CSS for Dark Theme ===========
st.markdown("""
<style>
    .main {
        background-color: #000000;
        color: #ffffff;
    }
    .stApp {
        background-color: #000000;
    }
    .stTextArea>div>div>textarea {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 12px;
    }
    .stSelectbox>div>div>select {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        border: none;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #4338ca;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .title-with-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.5rem;
    }
    .title-text {
        color: #ffffff;
        font-weight: bold;
        font-size: 2.5rem;
        margin: 0;
    }
    .logo-img {
        height: 2.5em;
        vertical-align: middle;
        margin-bottom: 0.3em;
    }
    .subheader {
        color: #a1a1a1;
        margin-bottom: 1.5rem;
    }
    .translation-box {
        background-color: #1e1e1e;
        color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
        border-left: 4px solid #4f46e5;
    }
    .footer {
        color: #666666;
        font-size: 0.8rem;
    }
    .copy-btn {
        background-color: #333 !important;
        border: 1px solid #444 !important;
        margin-top: 10px;
    }
    .copy-btn:hover {
        background-color: #444 !important;
    }
</style>
""", unsafe_allow_html=True)

# ===== UI ===========
# Header with integrated logo
try:
    logo = add_logo("logo.jpg", width=60)
    logo_html = f'<img class="logo-img" src="data:image/png;base64,{image_to_base64(logo)}">'
except:
    logo_html = '<span class="logo-img">🌐</span>'

st.markdown(
    f"""
    <div class="title-with-logo">
        <h1 class="title-text">AI TRANSLATOR</h1>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()
st.markdown('<h2 class="subheader">Seamless Translation Across Languages</h2>', unsafe_allow_html=True)

# Language selection
language_to_translate = st.selectbox(
    label="**Target Language**",
    options=["Hindi", "English", "Spanish", "French", "Japanese", "Korean", "German", "Portuguese", "Punjabi", "Chinese", "Tamil", "Bengali"],
    index=0
)

# Text area
text_to_translate = st.text_area(
    "**Text to Translate**",
    placeholder="Enter or paste the text you want to translate here...",
    height=150,
    key="text_input"
)

# Translate button
translate_btn = st.button("Translate Text →", type="primary")

# ===== Translation Logic ===========
if translate_btn or ('translation_result' in st.session_state):
    if not text_to_translate.strip():
        st.error("⚠️ Please provide text to translate.")
    else:
        if translate_btn:
            with st.spinner('Analyzing text...'):
                try:
                    needs_translation = should_translate(text_to_translate, language_to_translate)
                    
                    if not needs_translation:
                        st.error(f"❌ The text appears to already be in {language_to_translate}. Please provide text in a different language.")
                        st.session_state.translation_result = None
                    else:
                        with st.spinner('Translating...'):
                            groq_llm = ChatGroq(model="llama3-8b-8192", temperature=0.3)
                            chat_prompt_template = ChatPromptTemplate.from_messages([
                                ("system", "You are a professional translator. Translate the following text to {language} maintaining the original meaning."),
                                ("user", "{text}")
                            ])
                            
                            prompt = chat_prompt_template.invoke({
                                "language": language_to_translate,
                                "text": text_to_translate
                            })
                            
                            full_translation = ""
                            for chunk in groq_llm.stream(prompt):
                                full_translation += chunk.content
                            
                            st.session_state.translation_result = full_translation
                except Exception as e:
                    st.error(f"⚠️ Error analyzing text: {str(e)}")
                    st.session_state.translation_result = None

        # Display translation if available
        if 'translation_result' in st.session_state and st.session_state.translation_result:
            st.markdown("### Translation Result")
            with st.expander("View Translation", expanded=True):
                st.markdown(f'<div class="translation-box">{st.session_state.translation_result}</div>', unsafe_allow_html=True)
                st.code(st.session_state.translation_result, language='text')
                
                if st.button("📋 Copy Translation", key="copy_btn"):
                    copy_to_clipboard(st.session_state.translation_result)
                    st.toast("Copied to clipboard!")

# Footer
st.divider()
st.markdown('<div class="footer">AI Translator Pro • Powered by Groq and Llama 3</div>', unsafe_allow_html=True)