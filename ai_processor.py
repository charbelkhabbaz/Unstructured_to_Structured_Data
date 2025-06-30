import requests
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging to track what's happening during execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProcessor:
    """
    AI processor using OpenRouter API with DeepSeek model for data structuring.
    This class handles all communication with the AI model to convert unstructured text to structured data.
    Optimized for performance with connection pooling and caching.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the AI processor with API credentials and model settings.
        
        Args:
            api_key: OpenRouter API key (uses default from config if not provided)
            model: AI model to use (uses default from config if not provided)
        """
        # Use provided API key or fall back to the one in config file
        self.api_key = api_key or OPENROUTER_API_KEY
        # Use provided model or fall back to the default DeepSeek model
        self.model = model or DEFAULT_MODEL
        # Base URL for OpenRouter API endpoints
        self.base_url = OPENROUTER_BASE_URL
        
        # Create optimized session with connection pooling and retries
        self.session = self._create_optimized_session()
        
        # Cache for storing processed results
        self._cache = {}
    
    def _create_optimized_session(self) -> requests.Session:
        """
        Create an optimized requests session with connection pooling and retry logic.
        
        Returns:
            Optimized requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # Number of retries
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        )
        
        # Create adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Maximum number of connections in pool
        )
        
        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def structure_data(self, unstructured_text: str, output_format: str = "json", 
                      custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Main function to convert unstructured text to structured data using AI.
        Optimized with caching for repeated requests.
        
        Args:
            unstructured_text: The raw text extracted from documents (PDF, images, etc.)
            output_format: Desired output format ("json", "csv", "table")
            custom_prompt: Optional custom prompt to override default AI instructions
        
        Returns:
            Dictionary containing structured data and processing metadata
        """
        try:
            # Create cache key for this request
            cache_key = f"{hash(unstructured_text)}:{output_format}:{hash(custom_prompt or '')}"
            
            # Check if we have cached result
            if cache_key in self._cache:
                logger.info("Using cached result for structure_data")
                return self._cache[cache_key]
            
            # Step 1: Create the prompt that will be sent to the AI model
            prompt = self._create_prompt(unstructured_text, output_format, custom_prompt)
            
            # Step 2: Send the prompt to the AI model via OpenRouter API
            start_time = time.time()
            response = self._call_ai_model(prompt)
            processing_time = time.time() - start_time
            
            # Step 3: Parse and validate the AI response
            structured_data = self._parse_response(response, output_format)
            
            # Step 4: Create result with performance metrics
            result = {
                'success': True,
                'structured_data': structured_data,
                'output_format': output_format,
                'model_used': self.model,
                'original_text_length': len(unstructured_text),
                'processing_time': processing_time,
                'cached': False
            }
            
            # Cache the result for future use
            self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            # If anything goes wrong, log the error and return failure result
            logger.error(f"Error in AI processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_text': unstructured_text,
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def _create_prompt(self, text: str, output_format: str, custom_prompt: Optional[str] = None) -> str:
        """
        Create a prompt for the AI model by combining instructions with the text to process.
        
        Args:
            text: The unstructured text to structure
            output_format: Desired output format
            custom_prompt: Optional custom instructions
        
        Returns:
            Complete prompt string to send to AI model
        """
        # Use custom prompt if provided, otherwise get default prompt for the output format
        if custom_prompt:
            base_prompt = custom_prompt
        else:
            base_prompt = self._get_default_prompt(output_format)
        
        # Combine the base prompt with the actual text to process
        return f"""
{base_prompt}

Raw Text to Structure:
{text}

Please analyze the above text and convert it to structured data in {output_format.upper()} format.
Ensure the output is valid and well-formatted.
"""
    
    def _get_default_prompt(self, output_format: str) -> str:
        """
        Get the default AI prompt based on the desired output format.
        Each format has specific instructions for how the AI should structure the data.
        
        Args:
            output_format: The format we want the data in ("json", "csv", "table")
        
        Returns:
            Prompt string with specific instructions for that format
        """
        prompts = {
            "json": """
You are a data structuring expert. Your task is to convert unstructured text into well-structured JSON data.

Guidelines:
1. Identify key entities, relationships, and data points in the text
2. Create a logical JSON structure with appropriate keys
3. Use consistent data types (strings, numbers, booleans, arrays, objects)
4. Handle missing or unclear data gracefully
5. Preserve important information while organizing it logically
6. Use descriptive key names that clearly indicate the data content

Output only valid JSON without any additional text or explanations.
""",
            "csv": """
You are a data structuring expert. Your task is to convert unstructured text into CSV format.

Guidelines:
1. Identify the main data entities and their attributes
2. Create appropriate column headers
3. Extract data rows from the text
4. Use commas to separate values
5. Handle missing data with empty fields
6. Ensure the CSV is properly formatted

Output the CSV data with headers on the first line, followed by data rows.
""",
            "table": """
You are a data structuring expert. Your task is to convert unstructured text into a structured table format.

Guidelines:
1. Identify the main data entities and their attributes
2. Create a clear table structure with headers
3. Extract and organize the data into rows and columns
4. Use consistent formatting
5. Handle missing data appropriately

Output a well-formatted table with clear headers and organized data.
"""
        }
        
        # Return the appropriate prompt, defaulting to JSON if format not found
        return prompts.get(output_format, prompts["json"])
    
    def _call_ai_model(self, prompt: str) -> str:
        """
        Make an HTTP request to the OpenRouter API to get AI-generated structured data.
        Optimized with connection pooling and retry logic.
        
        Args:
            prompt: The complete prompt to send to the AI model
        
        Returns:
            The AI model's response as a string
        
        Raises:
            Exception: If the API request fails
        """
        try:
            # Set up HTTP headers for the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",  # API authentication
                "Content-Type": "application/json",  # Tell server we're sending JSON
                "HTTP-Referer": "https://github.com/your-repo",  # Optional but recommended
                "X-Title": "Unstructured to Structured Data Converter"  # Optional but recommended
            }
            
            # Prepare the data payload for the API request
            data = {
                "model": self.model,  # Which AI model to use (DeepSeek)
                "messages": [
                    {"role": "system", "content": "You are a data structuring expert. Always respond with valid, well-formatted data."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # Low temperature for consistent, predictable results
                "max_tokens": 4000   # Maximum length of AI response
            }
            
            # Make the HTTP POST request to OpenRouter API using optimized session
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/chat/completions",  # API endpoint
                headers=headers,
                json=data,
                timeout=60  # Wait up to 60 seconds for response
            )
            request_time = time.time() - start_time
            
            logger.info(f"API request completed in {request_time:.2f} seconds")
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response and extract the AI's text
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                # If request failed, create error message and raise exception
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            # Handle network/connection errors
            logger.error(f"Request error: {e}")
            raise e
        except Exception as e:
            # Handle any other errors
            logger.error(f"Error calling AI model: {e}")
            raise e
    
    def _parse_response(self, response: str, output_format: str) -> Any:
        """
        Parse and validate the AI model's response based on the expected output format.
        
        Args:
            response: The raw text response from the AI model
            output_format: Expected format of the response
        
        Returns:
            Parsed data in the appropriate format
        """
        try:
            if output_format == "json":
                # For JSON format, try to extract valid JSON from the response
                json_start = response.find('{')  # Find start of JSON object
                json_end = response.rfind('}') + 1  # Find end of JSON object
                
                if json_start != -1 and json_end != 0:
                    # Extract the JSON string and parse it
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # If no JSON brackets found, try to parse the entire response
                    return json.loads(response)
            
            elif output_format == "csv":
                # For CSV format, just return the response as-is (it should be CSV text)
                return response.strip()
            
            elif output_format == "table":
                # For table format, just return the response as-is (it should be formatted table)
                return response.strip()
            
            else:
                # For any other format, return the response as-is
                return response.strip()
                
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw response with error info
            logger.warning(f"JSON parsing failed: {e}")
            return {"raw_response": response, "parse_error": str(e)}
        except Exception as e:
            # Handle any other parsing errors
            logger.error(f"Response parsing error: {e}")
            return {"raw_response": response, "parse_error": str(e)}
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities (people, organizations, locations, etc.) from text using AI.
        Optimized with caching.
        
        Args:
            text: The text to analyze for entities
        
        Returns:
            Dictionary containing different types of extracted entities
        """
        # Create cache key for entity extraction
        cache_key = f"entities:{hash(text)}"
        if cache_key in self._cache:
            logger.info("Using cached result for entity extraction")
            return self._cache[cache_key]
        
        # Create a specific prompt for entity extraction
        prompt = f"""
Extract named entities from the following text and return them as JSON with the following structure:
{{
    "persons": ["list of person names"],
    "organizations": ["list of organization names"],
    "locations": ["list of location names"],
    "dates": ["list of dates"],
    "numbers": ["list of important numbers"],
    "emails": ["list of email addresses"],
    "phones": ["list of phone numbers"]
}}

Text to analyze:
{text}

Return only valid JSON.
"""
        
        try:
            # Call the AI model to extract entities
            start_time = time.time()
            response = self._call_ai_model(prompt)
            result = self._parse_response(response, "json")
            result['processing_time'] = time.time() - start_time
            
            # Cache the result
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"error": str(e)}
    
    def classify_document(self, text: str) -> Dict[str, Any]:
        """
        Classify the type of document (invoice, report, email, etc.) using AI.
        Optimized with caching.
        
        Args:
            text: The document text to classify
        
        Returns:
            Dictionary containing classification results
        """
        # Create cache key for document classification
        cache_key = f"classification:{hash(text)}"
        if cache_key in self._cache:
            logger.info("Using cached result for document classification")
            return self._cache[cache_key]
        
        # Create a specific prompt for document classification
        prompt = f"""
Classify the following document and return the result as JSON:
{{
    "document_type": "type of document (e.g., invoice, report, email, form, etc.)",
    "confidence": "confidence level (0-1)",
    "key_topics": ["list of main topics"],
    "language": "detected language",
    "sentiment": "overall sentiment (positive, negative, neutral)"
}}

Document text:
{text}

Return only valid JSON.
"""
        
        try:
            # Call the AI model to classify the document
            start_time = time.time()
            response = self._call_ai_model(prompt)
            result = self._parse_response(response, "json")
            result['processing_time'] = time.time() - start_time
            
            # Cache the result
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return {"error": str(e)}
    
    def create_summary(self, text: str, max_length: int = 200) -> str:
        """
        Create a concise summary of the text using AI.
        Optimized with caching.
        
        Args:
            text: The text to summarize
            max_length: Maximum number of words for the summary
        
        Returns:
            Summary text
        """
        # Create cache key for summarization
        cache_key = f"summary:{hash(text)}:{max_length}"
        if cache_key in self._cache:
            logger.info("Using cached result for summarization")
            return self._cache[cache_key]
        
        # Create a specific prompt for summarization
        prompt = f"""
Create a concise summary of the following text in {max_length} words or less:

{text}

Summary:
"""
        
        try:
            # Call the AI model to create a summary
            start_time = time.time()
            response = self._call_ai_model(prompt)
            summary = response.strip()
            
            # Cache the result
            self._cache[cache_key] = summary
            return summary
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return f"Error creating summary: {str(e)}"
    
    def clear_cache(self):
        """Clear the internal cache to free memory."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache usage."""
        return {
            'cache_size': len(self._cache),
            'cache_keys': list(self._cache.keys())
        }


class DataStructuringPipeline:
    """
    Complete pipeline for converting unstructured data to structured data.
    This class orchestrates the entire process from extraction to final structured output.
    Optimized for performance with parallel processing capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the pipeline with an AI processor.
        
        Args:
            api_key: Optional API key to use for AI processing
        """
        # Create an AI processor instance to handle all AI operations
        self.ai_processor = AIProcessor(api_key)
    
    def process_document(self, extracted_data: Dict[str, Any], 
                        output_format: Union[str, List[str]] = "json",
                        custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline: structure data, extract entities, 
        classify document, and create summary. Optimized for performance.
        
        Args:
            extracted_data: Data extracted from the document (contains 'text' field)
            output_format: Desired output format(s) for structured data
            custom_prompt: Optional custom prompt for structuring
            
        Returns:
            Complete processing results including structured data, entities, classification, and summary
        """
        try:
            # Get the extracted text from the document
            text = extracted_data.get('text', '')
            
            # Check if we have text to process
            if not text:
                return {
                    'success': False,
                    'error': 'No text content found in extracted data'
                }
            
            # Track overall processing time
            start_time = time.time()
            
            # For simplicity, we use the first format for structuring if multiple are provided
            main_output_format = output_format[0] if isinstance(output_format, list) and output_format else \
                                (output_format if isinstance(output_format, str) else "json")
            
            # Step 1: Structure the data using AI (this is the main operation)
            structured_result = self.ai_processor.structure_data(
                text, main_output_format, custom_prompt
            )
            
            # Step 2: Extract named entities from the text
            entities = self.ai_processor.extract_entities(text)
            
            # Step 3: Classify the type of document
            classification = self.ai_processor.classify_document(text)
            
            # Step 4: Create a summary of the document
            summary = self.ai_processor.create_summary(text)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            # Step 5: Return all results in a comprehensive dictionary
            return {
                'success': True,
                'original_data': extracted_data,  # Keep the original extracted data
                'structured_data': structured_result.get('structured_data'),  # The main structured output
                'entities': entities,  # Named entities found in the text
                'classification': classification,  # Document type and metadata
                'summary': summary,  # Brief summary of the document
                'processing_metadata': {
                    'output_format': output_format,
                    'model_used': self.ai_processor.model,
                    'text_length': len(text),
                    'total_processing_time': total_time,
                    'ai_processing_time': structured_result.get('processing_time', 0),
                    'cache_stats': self.ai_processor.get_cache_stats()
                }
            }
            
        except Exception as e:
            # If anything goes wrong, log the error and return failure result
            logger.error(f"Error in processing pipeline: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_data': extracted_data
            } 