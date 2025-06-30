import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import io
import os
from typing import List, Dict, Any, Optional
import logging

# Configure logging to track extraction processes and any errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractor:
    """
    Base class for data extraction from different file formats.
    This is an abstract class that defines the interface for all extractors.
    """
    
    def __init__(self):
        """Initialize the extractor with empty text and metadata."""
        self.extracted_text = ""  # Will store the extracted text content
        self.metadata = {}        # Will store file metadata (size, format, etc.)
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract data from file and return structured information.
        This method must be implemented by subclasses.
        
        Args:
            file_path: Path to the file to extract data from
        
        Returns:
            Dictionary containing extracted text and metadata
        """
        raise NotImplementedError
    
    def get_text(self) -> str:
        """Return the extracted text content."""
        return self.extracted_text
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return the file metadata."""
        return self.metadata


class PDFExtractor(DataExtractor):
    """
    Extract text and data from PDF files using pdfplumber.
    This class handles PDF documents and extracts both text content and metadata.
    """
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract data from PDF using pdfplumber library.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Dictionary containing extracted text, metadata, page count, and extraction method
        """
        try:
            # Extract text content from the PDF
            self.extracted_text = self._extract_with_pdfplumber(file_path)
            
            # Extract metadata (title, author, creation date, etc.)
            self.metadata = self._extract_metadata(file_path)
            
            # Return comprehensive extraction results
            return {
                'text': self.extracted_text,
                'metadata': self.metadata,
                'pages': self._get_page_count(file_path),
                'extraction_method': 'pdfplumber'
            }
            
        except Exception as e:
            # Log any errors and return error information
            logger.error(f"Error extracting PDF: {e}")
            return {'error': str(e)}
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """
        Extract text from PDF using pdfplumber library.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Extracted text as a string
        """
        text = ""
        try:
            # Open the PDF file using pdfplumber
            with pdfplumber.open(file_path) as pdf:
                # Iterate through each page in the PDF
                for page in pdf.pages:
                    # Extract text from the current page
                    page_text = page.extract_text()
                    if page_text:
                        # Add page text to the total, with a newline separator
                        text += page_text + "\n"
        except Exception as e:
            # Log warning if pdfplumber extraction fails
            logger.warning(f"pdfplumber extraction failed: {e}")
        return text
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file (title, author, creation date, etc.).
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            # Open PDF and extract metadata
            with pdfplumber.open(file_path) as pdf:
                return {
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'creator': pdf.metadata.get('Creator', ''),
                    'producer': pdf.metadata.get('Producer', ''),
                    'creation_date': pdf.metadata.get('CreationDate', ''),
                    'modification_date': pdf.metadata.get('ModDate', '')
                }
        except:
            # Return empty dict if metadata extraction fails
            return {}
    
    def _get_page_count(self, file_path: str) -> int:
        """
        Get the total number of pages in the PDF.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Number of pages in the PDF
        """
        try:
            # Open PDF and count pages
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except:
            # Return 0 if page counting fails
            return 0


class ImageExtractor(DataExtractor):
    """
    Extract text from images using OCR (Optical Character Recognition).
    This class uses Tesseract OCR to convert text in images to readable text.
    """
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from image using OCR technology.
        
        Args:
            file_path: Path to the image file
        
        Returns:
            Dictionary containing extracted text, image metadata, and OCR confidence
        """
        try:
            # Open the image file using PIL (Python Imaging Library)
            image = Image.open(file_path)
            
            # Extract text from image using Tesseract OCR
            self.extracted_text = pytesseract.image_to_string(
                image, 
                config='--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
            )
            
            # Extract image metadata (format, size, dimensions)
            self.metadata = {
                'format': image.format,      # Image format (PNG, JPEG, etc.)
                'mode': image.mode,          # Color mode (RGB, RGBA, etc.)
                'size': image.size,          # Image dimensions as tuple
                'width': image.width,        # Image width in pixels
                'height': image.height       # Image height in pixels
            }
            
            # Return extraction results with OCR confidence score
            return {
                'text': self.extracted_text,
                'metadata': self.metadata,
                'ocr_confidence': self._get_ocr_confidence(image)
            }
            
        except Exception as e:
            # Log any errors and return error information
            logger.error(f"Error extracting image: {e}")
            return {'error': str(e)}
    
    def _get_ocr_confidence(self, image: Image.Image) -> float:
        """
        Calculate the average confidence score of OCR results.
        
        Args:
            image: PIL Image object
        
        Returns:
            Average confidence score (0-100)
        """
        try:
            # Get detailed OCR data including confidence scores
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            # Extract confidence scores for all detected text
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            # Calculate average confidence
            return sum(confidences) / len(confidences) if confidences else 0
        except:
            # Return 0 if confidence calculation fails
            return 0


class TextExtractor(DataExtractor):
    """
    Extract data from text files and spreadsheets.
    This class handles plain text files, CSV files, and Excel files.
    """
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract data from text files and spreadsheets based on file extension.
        
        Args:
            file_path: Path to the text/spreadsheet file
        
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Determine file type based on extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Route to appropriate extraction method
            if file_extension in ['.csv', '.xlsx', '.xls']:
                return self._extract_spreadsheet(file_path)
            else:
                return self._extract_text_file(file_path)
                
        except Exception as e:
            # Log any errors and return error information
            logger.error(f"Error extracting text file: {e}")
            return {'error': str(e)}
    
    def _extract_text_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from plain text files (TXT, etc.).
        
        Args:
            file_path: Path to the text file
        
        Returns:
            Dictionary containing extracted text and file metadata
        """
        try:
            # Read the entire text file with UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8') as file:
                self.extracted_text = file.read()
            
            # Extract file metadata
            self.metadata = {
                'file_size': os.path.getsize(file_path),  # File size in bytes
                'encoding': 'utf-8'                       # File encoding
            }
            
            # Return extraction results
            return {
                'text': self.extracted_text,
                'metadata': self.metadata,
                'line_count': len(self.extracted_text.split('\n'))  # Number of lines
            }
        except Exception as e:
            # Log any errors and return error information
            logger.error(f"Error reading text file: {e}")
            return {'error': str(e)}
    
    def _extract_spreadsheet(self, file_path: str) -> Dict[str, Any]:
        """
        Extract data from spreadsheet files (CSV, Excel).
        
        Args:
            file_path: Path to the spreadsheet file
        
        Returns:
            Dictionary containing extracted data and spreadsheet metadata
        """
        try:
            # Read spreadsheet based on file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Convert DataFrame to text representation for AI processing
            self.extracted_text = df.to_string(index=False)
            
            # Extract spreadsheet metadata
            self.metadata = {
                'rows': len(df),                    # Number of data rows
                'columns': len(df.columns),         # Number of columns
                'column_names': df.columns.tolist(), # List of column names
                'data_types': df.dtypes.to_dict()   # Data types of each column
            }
            
            # Return extraction results
            return {
                'text': self.extracted_text,
                'metadata': self.metadata,
                'dataframe': df,           # Keep the original DataFrame for reference
                'file_type': 'spreadsheet'
            }
            
        except Exception as e:
            # Log any errors and return error information
            logger.error(f"Error reading spreadsheet: {e}")
            return {'error': str(e)}


class DataExtractionManager:
    """
    Manager class to handle different types of data extraction.
    This class acts as a factory and coordinator for all extractor types.
    """
    
    def __init__(self):
        """Initialize the manager with all available extractors."""
        # Create instances of all available extractors
        self.extractors = {
            'pdf': PDFExtractor(),      # For PDF files
            'image': ImageExtractor(),  # For image files
            'text': TextExtractor()     # For text and spreadsheet files
        }
    
    def extract_data(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Extract data from file based on file type.
        
        Args:
            file_path: Path to the file to extract
            file_type: Type of file ('pdf', 'image', 'text')
        
        Returns:
            Dictionary containing extracted data and metadata
        
        Raises:
            ValueError: If file type is not supported
        """
        # Check if the file type is supported
        if file_type not in self.extractors:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Get the appropriate extractor and extract data
        extractor = self.extractors[file_type]
        return extractor.extract(file_path)
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get list of supported file formats for each file type.
        
        Returns:
            Dictionary mapping file types to their supported extensions
        """
        return {
            'pdf': ['.pdf'],
            'image': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'],
            'text': ['.txt', '.csv', '.xlsx', '.xls']
        } 