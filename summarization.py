import fitz  # PyMuPDF
import cohere
from PIL import Image
import io
import pytesseract

def get_text_and_images_from_pdf(uploaded_file):
    text = ""
    images = []
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            image_text = pytesseract.image_to_string(image)
            images.append(image_text)

    return text, images

def summarize_large_text(text, co):
    if len(text) > 5000:
        chunks = [text[i:i + 5000] for i in range(0, len(text), 5000)]
        summary = ""
        for chunk in chunks:
            response = co.summarize(
                text=chunk,
                model="summarize-xlarge",  # Use an available summarization model
                length="long"
            )
            summary += response.summary + " "
        return summary
    else:
        response = co.summarize(
            text=text,
            model="summarize-xlarge",  # Use an available summarization model
            length="long"
        )
        return response.summary
