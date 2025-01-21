import os

from fastapi import APIRouter, File, Form, UploadFile
from pypdf import PdfReader

# # Define a directory for temporary file storage
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


# Function to extract text from a PDF file
def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {e}")


# Utility function to handle file uploads and temporary storage
def save_uploaded_file(file: UploadFile) -> str:
    try:
        temp_file_path = os.path.join(TEMP_DIR, file.filename)
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file.file.read())
        return temp_file_path
    except Exception as e:
        raise ValueError(f"Error saving uploaded file: {e}")
