import os
import json
import pandas as pd
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension from file path."""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """Determine file type based on extension."""
        extension = FileUtils.get_file_extension(file_path)
        
        if extension == '.pdf':
            return 'pdf'
        elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return 'image'
        elif extension in ['.txt', '.csv', '.xlsx', '.xls']:
            return 'text'
        else:
            return 'unknown'
    
    @staticmethod
    def validate_file(file_path: str, max_size: int = 50 * 1024 * 1024) -> Dict[str, Any]:
        """Validate file for processing."""
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File does not exist'}
            
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return {'valid': False, 'error': f'File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)'}
            
            file_type = FileUtils.get_file_type(file_path)
            if file_type == 'unknown':
                return {'valid': False, 'error': 'Unsupported file type'}
            
            return {
                'valid': True,
                'file_size': file_size,
                'file_type': file_type,
                'extension': FileUtils.get_file_extension(file_path)
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    @staticmethod
    def create_temp_file(content: str, extension: str = '.txt') -> str:
        """Create a temporary file with given content."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False, encoding='utf-8') as f:
                f.write(content)
                return f.name
        except Exception as e:
            logger.error(f"Error creating temp file: {e}")
            raise e


class DataExporter:
    """Utility class for exporting structured data."""
    
    @staticmethod
    def export_to_json(data: Dict[str, Any], file_path: str) -> bool:
        """Export data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    @staticmethod
    def export_to_csv(data: Any, file_path: str) -> bool:
        """Export data to CSV file."""
        try:
            if isinstance(data, str):
                # If data is already CSV string
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            elif isinstance(data, dict):
                # Convert dict to DataFrame
                df = pd.DataFrame([data])
                df.to_csv(file_path, index=False)
            elif isinstance(data, list):
                # Convert list of dicts to DataFrame
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            else:
                logger.error(f"Unsupported data type for CSV export: {type(data)}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    @staticmethod
    def export_to_excel(data: Any, file_path: str) -> bool:
        """Export data to Excel file."""
        try:
            if isinstance(data, dict):
                # Convert dict to DataFrame
                df = pd.DataFrame([data])
            elif isinstance(data, list):
                # Convert list of dicts to DataFrame
                df = pd.DataFrame(data)
            else:
                logger.error(f"Unsupported data type for Excel export: {type(data)}")
                return False
            
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    @staticmethod
    def export_results(results: Dict[str, Any], output_dir: str, base_filename: str, formats: List[str]) -> Dict[str, str]:
        """Export all results to multiple formats."""
        exported_files = {}
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Export structured data
            structured_data = results.get('structured_data')
            if structured_data:
                # JSON export
                if 'json' in formats:
                    json_path = os.path.join(output_dir, f"{base_filename}_structured.json")
                    if DataExporter.export_to_json(structured_data, json_path):
                        exported_files['json'] = json_path
                
                # CSV export
                if 'csv' in formats:
                    csv_path = os.path.join(output_dir, f"{base_filename}_structured.csv")
                    if DataExporter.export_to_csv(structured_data, csv_path):
                        exported_files['csv'] = csv_path
                
                # Excel export
                if 'excel' in formats:
                    excel_path = os.path.join(output_dir, f"{base_filename}_structured.xlsx")
                    if DataExporter.export_to_excel(structured_data, excel_path):
                        exported_files['excel'] = excel_path
            
            # Export entities
            entities = results.get('entities')
            if entities:
                entities_path = os.path.join(output_dir, f"{base_filename}_entities.json")
                if DataExporter.export_to_json(entities, entities_path):
                    exported_files['entities'] = entities_path
            
            # Export classification
            classification = results.get('classification')
            if classification:
                classification_path = os.path.join(output_dir, f"{base_filename}_classification.json")
                if DataExporter.export_to_json(classification, classification_path):
                    exported_files['classification'] = classification_path
            
            # Export summary
            if 'summary' in formats:
                summary = results.get('summary')
                if summary:
                    summary_path = os.path.join(output_dir, f"{base_filename}_summary.txt")
                    try:
                        with open(summary_path, 'w', encoding='utf-8') as f:
                            f.write(summary)
                        exported_files['summary'] = summary_path
                    except Exception as e:
                        logger.error(f"Error exporting summary: {e}")
            
            # Export complete results
            complete_path = os.path.join(output_dir, f"{base_filename}_complete_results.json")
            if DataExporter.export_to_json(results, complete_path):
                exported_files['complete'] = complete_path
            
            return exported_files
            
        except Exception as e:
            logger.error(f"Error in export_results: {e}")
            return {}


class DataValidator:
    """Utility class for data validation."""
    
    @staticmethod
    def validate_json_structure(data: Any) -> Dict[str, Any]:
        """Validate JSON structure and provide feedback."""
        try:
            if not isinstance(data, dict):
                return {'valid': False, 'error': 'Data is not a dictionary'}
            
            # Check for common issues
            issues = []
            
            # Check for empty data
            if not data:
                issues.append("Data is empty")
            
            # Check for nested structures
            nested_count = 0
            for key, value in data.items():
                if isinstance(value, dict):
                    nested_count += 1
                elif isinstance(value, list):
                    nested_count += 1
            
            if nested_count == 0:
                issues.append("No nested structures found - data might be too flat")
            
            # Check for mixed data types in lists
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 1:
                    types = [type(item) for item in value]
                    if len(set(types)) > 1:
                        issues.append(f"Mixed data types in list '{key}'")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'structure_info': {
                    'total_keys': len(data),
                    'nested_structures': nested_count,
                    'data_types': {key: type(value).__name__ for key, value in data.items()}
                }
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    @staticmethod
    def validate_csv_structure(csv_data: str) -> Dict[str, Any]:
        """Validate CSV structure and provide feedback."""
        try:
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                return {'valid': False, 'error': 'CSV must have at least headers and one data row'}
            
            headers = lines[0].split(',')
            data_rows = lines[1:]
            
            issues = []
            
            # Check for consistent column count
            expected_columns = len(headers)
            for i, row in enumerate(data_rows, 1):
                columns = row.split(',')
                if len(columns) != expected_columns:
                    issues.append(f"Row {i} has {len(columns)} columns, expected {expected_columns}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'structure_info': {
                    'headers': headers,
                    'total_rows': len(data_rows),
                    'total_columns': expected_columns
                }
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class DataFormatter:
    """Utility class for formatting data for display."""
    
    @staticmethod
    def format_json_for_display(data: Dict[str, Any], max_depth: int = 3) -> str:
        """Format JSON data for better display."""
        try:
            def format_value(value, depth=0):
                if depth >= max_depth:
                    return str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                
                if isinstance(value, dict):
                    formatted = "{\n"
                    for key, val in value.items():
                        formatted += "  " * (depth + 1) + f'"{key}": {format_value(val, depth + 1)},\n'
                    formatted = formatted.rstrip(",\n") + "\n" + "  " * depth + "}"
                    return formatted
                elif isinstance(value, list):
                    if len(value) > 5:
                        return f"[{len(value)} items: {', '.join(str(v)[:20] for v in value[:3])}...]"
                    else:
                        formatted_values = [str(format_value(v, depth + 1)) for v in value]
                        return "[" + ", ".join(formatted_values) + "]"
                else:
                    return str(value)
            
            return format_value(data)
            
        except Exception as e:
            return str(data)
    
    @staticmethod
    def format_entities_for_display(entities: Dict[str, Any]) -> str:
        """Format entities for display."""
        try:
            if not entities or 'error' in entities:
                return str(entities)
            
            formatted = "Extracted Entities:\n\n"
            
            for entity_type, values in entities.items():
                if isinstance(values, list) and values:
                    formatted += f"{entity_type.title()}:\n"
                    for value in values[:10]:  # Limit to first 10
                        formatted += f"  • {value}\n"
                    if len(values) > 10:
                        formatted += f"  ... and {len(values) - 10} more\n"
                    formatted += "\n"
            
            return formatted
            
        except Exception as e:
            return str(entities)
    
    @staticmethod
    def format_classification_for_display(classification: Dict[str, Any]) -> str:
        """Format classification results for display."""
        try:
            if not classification or 'error' in classification:
                return str(classification)
            
            formatted = "Document Classification:\n\n"
            
            for key, value in classification.items():
                if key == 'key_topics' and isinstance(value, list):
                    formatted += f"{key.replace('_', ' ').title()}:\n"
                    for topic in value[:5]:  # Limit to first 5
                        formatted += f"  • {topic}\n"
                    if len(value) > 5:
                        formatted += f"  ... and {len(value) - 5} more\n"
                else:
                    formatted += f"{key.replace('_', ' ').title()}: {value}\n"
            
            return formatted
            
        except Exception as e:
            return str(classification) 