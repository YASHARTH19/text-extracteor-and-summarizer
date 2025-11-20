import streamlit as st
import fitz
from groq import Groq
from PIL import Image
import pytesseract

st.set_page_config(page_title="AI Text Extractor & Summarizer", layout="wide")

# ----------------------------
# FIXED + STREAMLIT-SAFE CSS
# ----------------------------
st.markdown("""
<style>

    /* --- Safe fade-in animation without breaking Streamlit widgets --- */
    .main-container {
        animation: fadeIn 1.1s ease-out forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0px); }
    }

    /* --- Background (bottom 2 colors) --- */
    .stApp {
        background: linear-gradient(160deg, #748D92, #D3D9D4);
        background-size: cover;
        font-family: 'Inter', sans-serif;
    }

    /* --- Main card (teal sheet) --- */
    div[data-testid="stVerticalBlock"] {
        background: rgba(18, 78, 102, 0.92);
        padding: 28px;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        backdrop-filter: blur(14px);
    }

    /* --- Title & Subtitle --- */
    .title {
        text-align: center;
        font-size: 40px;
        font-weight: 800;
        color: #212A31;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #2E3944;
        margin-bottom: 25px;
    }

    /* --- Buttons --- */
    .stButton button {
        background: linear-gradient(145deg, #212A31, #2E3944);
        color: #FFFFFF;
        border-radius: 28px;
        border: 2px solid #212A31;
        padding: 12px 24px;
        font-size: 18px;
        font-weight: 600;
        transition: 0.25s ease-in-out;
    }

    .stButton button:hover {
        transform: scale(1.06);
        box-shadow: 0 0 18px rgba(33, 42, 49, 0.65);
    }

    .stButton button:active {
        transform: scale(0.97);
        background: #124E66 !important;
        border-color: #2E3944 !important;
    }

    /* --- Inputs --- */
    textarea, input {
        background-color: #D3D9D4 !important;
        color: #212A31 !important;
        border-radius: 10px !important;
        border: 2px solid #748D92 !important;
    }

    textarea:focus, input:focus {
        border-color: #124E66 !important;
        box-shadow: 0 0 12px rgba(18, 78, 102, 0.9) !important;
    }

</style>
""", unsafe_allow_html=True)


# ----------------------------
# HEADER
# ----------------------------
st.markdown('<div class="title">📄 AI Text Extractor & Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload → Extract → Summarize with AI</div>', unsafe_allow_html=True)


# ----------------------------
# API KEY
# ----------------------------
groq_client = Groq(api_key="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")


# ----------------------------
# FUNCTIONS
# ----------------------------
def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def extract_text_from_image(uploaded_file):
    img = Image.open(uploaded_file)
    return pytesseract.image_to_string(img)

def extract_text_from_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8")

def summarize_text(long_text, chunk_size=2500):
    """
    Splits text into chunks small enough for Groq
    and summarizes each, then summarizes the combined summary.
    """
    import math
    
    # Split text into safe chunks
    words = long_text.split()
    chunks = [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

    partial_summaries = []

    # Summarize chunk by chunk
    for idx, chunk in enumerate(chunks):
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert summarizer."},
                    {"role": "user", "content": f"Summarize this text chunk:\n\n{chunk}"}
                ],
                temperature=0.2,
                max_tokens=300
            )
            part_sum = response.choices[0].message.content.strip()
            partial_summaries.append(part_sum)

        except Exception as e:
            partial_summaries.append(f"Error in chunk {idx}: {e}")

    # Combine all summaries into one final summary
    combined = "\n\n".join(partial_summaries)

    # Summarize the combined partial summaries
    final_response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert summarizer."},
            {"role": "user", "content": f"Now summarize all these partial summaries into one concise summary:\n\n{combined}"}
        ],
        temperature=0.2,
        max_tokens=400
    )

    return final_response.choices[0].message.content.strip()



# ----------------------------
# MAIN UI CARD — SAFE VERSION
# ----------------------------
with st.container():
    uploaded_file = st.file_uploader("📤 Upload PDF, Image, or Text File",
                                     type=["pdf", "png", "jpg", "jpeg", "txt"])

    if "extracted_text" not in st.session_state:
        st.session_state.extracted_text = ""

    if "summary" not in st.session_state:
        st.session_state.summary = ""

    col1, col2 = st.columns(2)

    # LEFT SIDE — Extract
    with col1:
        if st.button("📌 Extract Text"):
            if uploaded_file:
                ext = uploaded_file.name.split(".")[-1]
                if ext == "pdf":
                    st.session_state.extracted_text = extract_text_from_pdf(uploaded_file)
                elif ext in ["png", "jpg", "jpeg"]:
                    st.session_state.extracted_text = extract_text_from_image(uploaded_file)
                else:
                    st.session_state.extracted_text = extract_text_from_txt(uploaded_file)
                st.success("✅ Text extracted!")

        st.text_area("📃 Extracted Text", st.session_state.extracted_text, height=270)

    # RIGHT SIDE — Summarize
    with col2:
        if st.button("✨ Summarize Text"):
            if st.session_state.extracted_text.strip():
                with st.spinner("⏳ Summarizing..."):
                    st.session_state.summary = summarize_text(st.session_state.extracted_text)
            else:
                st.warning("⚠ Extract text first!")

        st.text_area("📝 Summary", st.session_state.summary, height=270)
