import streamlit as st
import fitz  # PyMuPDF for PDF handling
import cohere
from PIL import Image
import io
from docx import Document
from pptx import Presentation
import textwrap
from gtts import gTTS
import os
import tempfile

# Initialize Cohere client
COHERE_API_KEY = 'l3VRlgNFDQDd0qEz2SK0PmmLyv5KvY49lF8ExMIB'
co = cohere.Client(COHERE_API_KEY)

# Constants
TOKEN_LIMIT = 4081  # Adjust based on the API's token limit
CHUNK_SIZE = 2000  # Size of each text chunk to avoid exceeding token limits

# Extract text and images from PDF
def extract_text_and_images_from_pdf(file):
    text = ""
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    
    # Extract text using PyMuPDF
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text()

    # Extract images using PyMuPDF
    images_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        for img_index, img in enumerate(page.get_images(full=True)):
            base_image = fitz.Pixmap(pdf_document, img[0])
            if base_image.n < 5:  # GRAYSCALE or RGB image
                try:
                    img_data = base_image.tobytes("png")
                    pil_image = Image.open(io.BytesIO(img_data))
                    # images_text += pytesseract.image_to_string(pil_image)
                except ValueError:
                    # Unsupported color space, skip the image
                    continue
            else:
                # Handle CMYK or other color spaces if needed
                # For now, skip these images
                continue

    return text, images_text

# Extract text from Word document
def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Extract text from PowerPoint presentation
def extract_text_from_pptx(file):
    presentation = Presentation(file)
    text = ""
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

# Summarize a chunk of text using Cohere API
def summarize_chunk(chunk):
    response = co.generate(
        model='command',  # Replace with the correct model ID
        prompt=f"Summarize the following text:\n\n{chunk}\n\nSummary:",
        max_tokens=300  # Adjust as needed
    )
    return response.generations[0].text.strip()

# Chunk and summarize text
def summarize_text(text):
    chunks = textwrap.wrap(text, width=CHUNK_SIZE)  # Chunk text
    summaries = [summarize_chunk(chunk) for chunk in chunks]
    return " ".join(summaries)

# Answer questions using Cohere API with chunking
def answer_question(question, context):
    chunks = textwrap.wrap(context, width=CHUNK_SIZE)  # Chunk text
    answers = []
    
    for chunk in chunks:
        response = co.generate(
            model='command',  # Replace with the correct model ID
            prompt=f"Context: {chunk}\n\nQuestion: {question}\nAnswer:",
            max_tokens=300  # Adjust as needed
        )
        answers.append(response.generations[0].text.strip())
    
    return " ".join(answers)

# Generate additional context-related data
def generate_additional_context(context):
    chunks = textwrap.wrap(context, width=CHUNK_SIZE)  # Chunk text
    additional_contexts = []
    
    for chunk in chunks:
        response = co.generate(
            model='command',  # Replace with the correct model ID
            prompt=f"Context: {chunk}\n\nProvide additional context related to the document:",
            max_tokens=400  # Adjust as needed
        )
        additional_contexts.append(response.generations[0].text.strip())
    
    return " ".join(additional_contexts)

# Convert text to speech and save to a temporary file
def text_to_speech(text):
    tts = gTTS(text, lang='en')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(temp_file.name)
    return temp_file.name

def main():
    st.title("Document Summarizer and Q&A")

    file_type = st.selectbox("Select file type", ["Select", "PDF", "Word", "PowerPoint"])
    
    if file_type == "Select":
        st.write("Please select a document type.")
        return

    if file_type == "PDF":
        file_types = ["pdf"]
    elif file_type == "Word":
        file_types = ["docx"]
    elif file_type == "PowerPoint":
        file_types = ["pptx"]
    else:
        st.write("Invalid file type selected.")
        return

    uploaded_file = st.file_uploader(f"Upload a {file_type} file", type=file_types)

    if uploaded_file is not None:
        if file_type == "PDF":
            text, images_text = extract_text_and_images_from_pdf(uploaded_file)
        elif file_type == "Word":
            text = extract_text_from_docx(uploaded_file)
            images_text = ""  # No image extraction for Word
        elif file_type == "PowerPoint":
            text = extract_text_from_pptx(uploaded_file)
            images_text = ""  # No image extraction for PowerPoint

        combined_text = text + " " + images_text

        if combined_text:
            show_text = st.checkbox("Show Document Text", value=False)

            if show_text:
                st.subheader("Extracted Text")
                st.write(combined_text)

            if st.button("Summarize Text"):
                st.subheader("Summarized Text")
                summary = summarize_text(combined_text)
                st.write(summary)

                # Generate and play speech for the summary
                if summary:
                    audio_file = text_to_speech(summary)
                    st.audio(audio_file)

            st.subheader("Ask a Question")
            question = st.text_input("Enter your question:")
            if question:
                # Generate additional context related to the document
                additional_context = generate_additional_context(combined_text)
                
                # Combine additional context with the extracted text
                full_context = combined_text + " " + additional_context
                answer = answer_question(question, full_context)
                st.write(answer)

                # Generate and play speech for the answer
                if answer:
                    audio_file = text_to_speech(answer)
                    st.audio(audio_file)
        else:
            st.error("Could not extract text from the uploaded file.")

if __name__ == "__main__":
    main()
