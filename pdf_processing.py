import fitz
import io
from PIL import Image

def extract_text_and_images_from_pdf(pdf_file):
    # Convert the uploaded file to a byte stream
    pdf_stream = io.BytesIO(pdf_file.read())
    
    doc = fitz.open(stream=pdf_stream, filetype='pdf')
    text = ""
    images = []

    for page in doc:
        text += page.get_text()
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)

    return text, images
