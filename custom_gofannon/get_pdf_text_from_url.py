# gofannon/pdf_reader/read_pdf_from_url.py
from gofannon.base import BaseTool

import logging
import requests
import io # For in-memory buffer
import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError # For handling PDF parsing errors

logger = logging.getLogger(__name__)

class ReadPdfFromUrl(BaseTool):
    """
    A tool for downloading a PDF from a URL and extracting its text content.

    This class provides a function that takes a URL pointing to a PDF file,
    downloads the PDF, and then extracts and returns its text content as a string.
    """
    def __init__(self, name="read_pdf_from_url"):
        super().__init__()
        self.name = name

    @property
    def definition(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Downloads a PDF from a given URL and extracts its text content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pdf_url": {
                            "type": "string",
                            "description": "The URL of the PDF file to be read."
                        }
                    },
                    "required": ["pdf_url"]
                }
            }
        }

    def fn(self, pdf_url: str) -> str:
        logger.debug(f"Attempting to read PDF from URL: {pdf_url}")
        try:
            # Download the PDF content
            headers = {
                'User-Agent': ( # Add a common user-agent to avoid potential blocking
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/91.0.4472.124 Safari/537.36 GofannonTool/1.0'
                )
            }
            response = requests.get(pdf_url, headers=headers, timeout=30) # Added timeout
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Check content type (optional but good practice)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                logger.warn(
                    f"Content-Type for URL {pdf_url} is '{content_type}', not 'application/pdf'. "
                    "Attempting to parse as PDF anyway."
                )

                # Create an in-memory buffer from the PDF content
            pdf_buffer = io.BytesIO(response.content)

            text_content = []
            with pdfplumber.open(pdf_buffer) as pdf:
                if not pdf.pages:
                    logger.warn(f"PDF from URL {pdf_url} has no pages.")
                    return f"Error: The PDF from URL '{pdf_url}' contains no pages."

                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                    else:
                        logger.debug(f"No text extracted from page {page_num + 1} of PDF from URL {pdf_url}")

            if not text_content:
                logger.warn(f"No text could be extracted from the PDF at URL: {pdf_url}")
                return "No text content could be extracted from this PDF."

            logger.info(f"Successfully extracted text from PDF at URL: {pdf_url}")
            return "\n".join(text_content)

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error downloading PDF from URL {pdf_url}: {e}")
            return f"Error: Failed to download PDF due to HTTP error - {e.response.status_code} {e.response.reason}."
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error downloading PDF from URL {pdf_url}: {e}")
            return f"Error: Failed to connect to the server to download PDF - {e}."
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout downloading PDF from URL {pdf_url}: {e}")
            return f"Error: The request timed out while downloading PDF - {e}."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF from URL {pdf_url}: {e}")
            return f"Error: Could not download PDF from URL '{pdf_url}'. Request Error: {e}"
        except PDFSyntaxError:
            logger.error(f"Error parsing PDF (syntax error) from URL: {pdf_url}")
            return f"Error: Could not parse PDF from URL '{pdf_url}'. It might be corrupted or not a valid PDF."
        except pdfplumber.exceptions.PDFPasswordIncorrect:
            logger.error(f"PDF from URL {pdf_url} is password protected.")
            return f"Error: The PDF at URL '{pdf_url}' is password protected and cannot be read."
        except Exception as e:
            logger.error(f"An unexpected error occurred while reading PDF from URL '{pdf_url}': {e}", exc_info=True)
            return f"Error reading PDF from URL '{pdf_url}': An unexpected error occurred - {e}"
