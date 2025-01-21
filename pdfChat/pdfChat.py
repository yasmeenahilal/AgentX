from database import (
    get_pdf_file_details,
    get_pdf_files_by_user_and_index,
    insert_pdf_file,
)


class PDFDatabaseInterface:
    @staticmethod
    def save_pdf(
        file_id: str, index_name: str, user_id: str, file_name: str, extracted_text: str
    ):
        """
        Save a PDF record in the database.
        """
        insert_pdf_file(file_id, index_name, user_id, file_name, extracted_text)

    @staticmethod
    def list_pdfs(user_id: str, index_name: str):
        """
        List all PDF files for a user.
        """
        return get_pdf_files_by_user_and_index(user_id, index_name)

    @staticmethod
    def get_pdf(file_id: str, index_name: str):
        """
        Get details of a specific PDF file.
        """
        return get_pdf_file_details(file_id, index_name)
