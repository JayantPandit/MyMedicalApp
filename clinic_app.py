import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import re
from datetime import datetime

# --- CONFIG ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5)
    )
)

st.set_page_config(page_title="Clinic AI 2026", layout="wide", page_icon="🏥")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stDownloadButton>button { width: 100%; background-color: #28a745; color: white; }
    </style>
    """, unsafe_allow_html=True)

if "last_result" not in st.session_state:
    st.session_state.last_result = ""

# --- PDF GENERATOR ---
def create_pdf(name, age, therapy, content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], alignment=1, textColor=colors.darkblue)
    body_style = styles['Normal']
    
    elements = [
        Paragraph("CLINICAL REPORT", title_style),
        Spacer(1, 12),
        Paragraph(f"<b>Patient:</b> {name} ({age}y) | <b>Method:</b> {therapy}", body_style),
        Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", body_style),
        HRFlowable(width="100%", thickness=1, color=colors.grey, spaceBefore=10, spaceAfter=10)
    ]
    
    clean_text = re.sub('<[^>]*>', '', content).replace('**', '').replace('*', '')
    for line in clean_text.split('\n'):
        if line.strip():
            elements.append(Paragraph(line, body_style))
            elements.append(Spacer(1, 4))
            
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏥 Patient Portal")
    p_name = st.text_input("Name", "Guest")
    p_age = st.number_input("Age", 1, 110, 30)
    p_problem = st.text_input("Chief Complaint")
    p_symptoms = st.text_area("Symptoms")
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Lab PDF", type=["pdf"])
    report_text = ""
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        report_text = " ".join([p.extract_text() for p in reader.pages])
        st.success("Lab Data Processed")

# --- MAIN ---
st.title("Integrative Diagnostic Suite")

c1, c2 = st.columns(2)
with c1:
    modality = st.selectbox("Modality", ["Dr. Tan (Balance)", "TCM", "Dr. Tung", "Allopathy", "Ayurveda"])
    btn = st.button("🚀 Generate Full Plan")

with c2:
    st.write(" ")
    if st.session_state.last_result:
        pdf = create_pdf(p_name, p_age, modality, st.session_state.last_result)
        st.download_button("📥 Download PDF", pdf, f"Report_{p_name}.pdf", "application/pdf")

if btn and p_problem:
    with st.spinner("AI analyzing..."):
        # We try 2.5-flash as it is currently the most stable GA model
        try:
            prompt = f"Expert {modality} analysis for {p_name}, {p_age}y. Complaint: {p_problem}. Symptoms: {p_symptoms}. Labs: {report_text[:1500]}"
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            st.session_state.last_result = response.text
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}. Try checking your API key or model version.")

if st.session_state.last_result:
    st.divider()
    st.markdown(st.session_state.last_result)
