import base64
import pymupdf

from typing import List
from PIL import Image
from fastapi import UploadFile
from io import BytesIO

async def convert_image_to_base64(image: UploadFile) -> str:
    """
    Convert an image file to a base64-encoded string.
    """
    image_bytes = await image.read()
    pil_image = Image.open(BytesIO(image_bytes)).resize(
        (768, 768), Image.LANCZOS
    )
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

async def convert_pdf_to_images(pdf_file: UploadFile) -> List[str]:
    """
    Convert a PDF file to a list of base64-encoded image strings.
    """
    try:
        pdf_bytes = await pdf_file.read()
        pdf = pymupdf.open(stream=pdf_bytes)
        pdf_images = []

        for page in pdf:
            try:
                pix = page.get_pixmap(matrix=pymupdf.Matrix(4, 4))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = img.resize((768, 768), Image.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                pdf_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
            except Exception as e:
                print(f"Error processing page {page.number}: {e}")
                continue

        return pdf_images
    except Exception as e:
        print(f"Error processing PDF file: {e}")
        return []