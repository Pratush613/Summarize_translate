import streamlit as st
from transformers import pipeline
from newspaper import Article
from fpdf import FPDF, HTMLMixin
import base64
import torch

class MyFPDF(FPDF, HTMLMixin):
    pass

def convert_to_pdf(text):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    lines = text.split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))
    pdf_output = "output.pdf"
    pdf.output(pdf_output)
    return pdf_output

def convert_to_text(text):
    text_file = "output.txt"
    with open(text_file, "w", encoding='utf-8') as file:
        file.write(text)
    return text_file

def get_binary_file_downloader_html(bin_file, file_label):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{bin_file}">Download {file_label}</a>'
    return href

# Streamlit page setup
st.set_page_config(page_title="Summarize & Translate", layout="wide")
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: #032c40;
    }
    footer {
        visibility: hidden;
    }
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #808080;
        text-align: center;
        padding: 10px;
        font-size: 16px;
        color:  #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

sidebar_div_html = """
<div style='
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    text-align: center;
'>
    <h2 style='margin-bottom: 10px; color: #000000; font-size: 20px;'>
        Navigation Panel
    </h2>
</div>
<div style='
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    text-align: center;
'>
    <h3 style='margin-bottom: 10px; color: #333; font-size: 16px;'>
    Select the task you want
    </h3>
</div>
"""
st.sidebar.markdown(sidebar_div_html, unsafe_allow_html=True)

# Select task
summary_type = st.sidebar.radio(" ", ["Summarization", "Translation"])

# Summarization
if summary_type == "Summarization":
    st.title("Article Summarizer")
    try:
        st.write("Loading summarization model...")
        pipe = pipeline("summarization", model="t5-small")
        st.success("Model loaded successfully!")
    except Exception as e:
        st.error(f"Error loading summarization model: {e}")
        st.stop()

    summary_type = st.radio("Summarize from:", ["Text Input", "URL"])
    max_length = st.slider("Maximum Summary Length:", min_value=50, max_value=500, value=300)
    min_length = st.slider("Minimum Summary Length:", min_value=30, max_value=300, value=100)

    if summary_type == "Text Input":
        input_text = st.text_area("Enter text to summarize:", height=150)
        if st.button("Summarize"):
            if input_text:
                try:
                    with st.spinner('Summarizing...'):
                        pipe_out = pipe(input_text, max_length=max_length, min_length=min_length)
                    summary = pipe_out[0]["summary_text"]
                    st.write("Summary:")
                    st.write(summary)

                    pdf_file = convert_to_pdf(summary)
                    text_file = convert_to_text(summary)
                    st.markdown(get_binary_file_downloader_html(pdf_file, "Summary as PDF"), unsafe_allow_html=True)
                    st.markdown(get_binary_file_downloader_html(text_file, "Summary as Text"), unsafe_allow_html=True)
                except Exception as e:
                    st.error("Error summarizing the text. Please try again.")
                    st.error(str(e))

    elif summary_type == "URL":
        url = st.text_input("Enter URL to summarize:")
        if st.button("Fetch and Summarize"):
            if url and url.startswith(("http://", "https://")):
                try:
                    article = Article(url)
                    article.download()
                    article.parse()
                    input_text = article.text
                    with st.spinner('Summarizing...'):
                        pipe_out = pipe(input_text, max_length=max_length, min_length=min_length)
                    summary = pipe_out[0]["summary_text"]
                    st.write("Summary:")
                    st.write(summary)

                    pdf_file = convert_to_pdf(summary)
                    text_file = convert_to_text(summary)
                    st.markdown(get_binary_file_downloader_html(pdf_file, "Summary as PDF"), unsafe_allow_html=True)
                    st.markdown(get_binary_file_downloader_html(text_file, "Summary as Text"), unsafe_allow_html=True)
                except Exception as e:
                    st.error("Error fetching or summarizing the article. It might be protected against scraping or is not valid. Please try another URL.")
                    st.error(str(e))
            else:
                st.warning("Please enter a valid URL (starting with http:// or https://).")

# Translation
if summary_type == "Translation":
    st.title("Text Translator")
    source_lang = st.selectbox('Select the source language', ['en', 'fr', 'hi'])
    target_lang = st.selectbox('Select the target language', ['en', 'fr', 'hi'])

    model_map = {
        ('en', 'fr'): "Helsinki-NLP/opus-mt-en-fr",
        ('en', 'hi'): "Helsinki-NLP/opus-mt-en-hi",
        ('fr', 'en'): "Helsinki-NLP/opus-mt-fr-en",
        ('hi', 'en'): "Helsinki-NLP/opus-mt-hi-en",
        ('hi', 'fr'): "Helsinki-NLP/opus-mt-hi-fr",
        ('fr', 'hi'): "Helsinki-NLP/opus-mt-fr-hi"
    }

    model_name = model_map.get((source_lang, target_lang), "Helsinki-NLP/opus-mt-en-hi")

    st.write("Source Language:", source_lang)
    st.write("Target Language:", target_lang)

    try:
        st.write("Loading translation model...")
        translator = pipeline("translation", model=model_name, framework="pt")
        st.success("Translation model loaded successfully!")
    except Exception as e:
        st.error(f"Error loading translation model: {e}")
        st.stop()

    input_text = st.text_area("Enter text to translate:", height=150)
    if st.button("Translate"):
        if input_text:
            try:
                with st.spinner('Translating...'):
                    translation = translator(input_text)[0]["translation_text"]
                st.write("Translation:")
                st.write(translation)

                pdf_file = convert_to_pdf(translation)
                text_file = convert_to_text(translation)
                st.markdown(get_binary_file_downloader_html(pdf_file, "Translation as PDF"), unsafe_allow_html=True)
                st.markdown(get_binary_file_downloader_html(text_file, "Translation as Text"), unsafe_allow_html=True)
            except Exception as e:
                st.error("Error translating the text. Please try again.")
                st.error(str(e))

# Footer content with name
st.markdown(
    """
    <div class="custom-footer">
        @created by Pratush
    </div>
    """,
    unsafe_allow_html=True,
)
