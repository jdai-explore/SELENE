"""
Parse and structure datasheet content for analysis
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.text_utils import (
    extract_between_markers, find_all_numbers, 
    extract_component_values, clean_whitespace
)


class DatasheetParser:
    """Extract structured information from datasheet text"""
    
    def __init__(self):
        """Initialize datasheet parser"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Datasheet parser initialized")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Main parsing method to extract all relevant information
        
        Args:
            text: Full datasheet text
            
        Returns:
            dict: Structured datasheet information
        """
        try:
            # Clean text first
            text = clean_whitespace(text)
            
            # Extract all components
            parsed_data = {
                'component_name': self.extract_component_name(text),
                'pin_config': self.extract_pin_configuration(text),
                'electrical_specs': self.extract_electrical_specs(text),
                'recommended_circuits': self.extract_recommended_circuits(text),
                'key_parameters': self.extract_key_parameters(text),
                'features': self.extract_features(text),
                'operating_conditions': self.extract_operating_conditions(text),
                'package_info': self.extract_package_info(text),
                'application_notes': self.extract_application_notes(text),
                'full_text': text  # Keep full text for reference
            }
            
            # Log summary
            self.logger.info(f"Parsed datasheet for: {parsed_data['component_name']}")
            self.logger.info(f"Found {len(parsed_data['pin_config'])} pin configurations")
            self.logger.info(f"Found {len(parsed_data['electrical_specs'])} electrical specs")
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error parsing datasheet: {e}")
            return {
                'component_name': 'Unknown',
                'error': str(e),
                'full_text': text
            }
    
    def extract_component_name(self, text: str) -> str:
        """Extract component name/part number
        
        Args:
            text: Datasheet text
            
        Returns:
            str: Component name
        """
        # Common patterns for component names
        patterns = [
            r'^([A-Z]+\d+[A-Z]*)\s',  # Start of document
            r'Part Number:\s*([A-Z]+\d+[A-Z]*)',
            r'Device:\s*([A-Z]+\d+[A-Z]*)',
            r'([A-Z]{2,}\d{3,}[A-Z]*)',  # General IC pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:1000], re.MULTILINE)  # Check first 1000 chars
            if match:
                return match.group(1)
        
        # Fallback: look for common IC prefixes
        ic_prefixes = ['LM', 'TL', 'AD', 'MAX', 'LT', 'MC', 'NE', 'OP', 'TPS', 'STM']
        for prefix in ic_prefixes:
            match = re.search(f'{prefix}\\d{{3,}}[A-Z]*', text[:1000])
            if match:
                return match.group(0)
        
        return "Unknown Component"
    
    def extract_pin_configuration(self, text: str) -> Dict[str, str]:
        """Extract pin configuration information
        
        Args:
            text: Datasheet text
            
        Returns:
            dict: Pin number/name to function mapping
        """
        pin_config = {}
        
        # Look for pin configuration section
        pin_sections = self._find_sections(text, [
            'pin configuration', 'pin description', 'pinout', 
            'pin assignment', 'pin functions', 'terminal functions'
        ])
        
        for section in pin_sections:
            # Extract pin information from section
            pins = self._parse_pin_table(section)
            pin_config.update(pins)
        
        # Also try pattern matching for pin descriptions
        # Pattern: Pin number followed by name/function
        pin_patterns = [
            r'Pin\s+(\d+)[:\s]+([A-Z]+\d*/?[A-Z]*)[:\s]+(.+?)(?=Pin\s+\d+|$)',
            r'(\d+)\s+([A-Z]+\d*/?[A-Z]*)\s+(.+?)(?=\d+\s+[A-Z]|$)',
            r'([A-Z]+\d+)\s*[-–]\s*(.+?)(?=[A-Z]+\d+\s*[-–]|$)'
        ]
        
        for pattern in pin_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.groups()) >= 2:
                    pin_id = match.group(1)
                    if len(match.groups()) >= 3:
                        pin_name = match.group(2)
                        pin_function = match.group(3).strip()
                        pin_config[pin_id] = f"{pin_name}: {pin_function}"
                    else:
                        pin_function = match.group(2).strip()
                        pin_config[pin_id] = pin_function
        
        return pin_config
    
    def extract_electrical_specs(self, text: str) -> Dict[str, str]:
        """Extract electrical characteristics
        
        Args:
            text: Datasheet text
            
        Returns:
            dict: Parameter to value mapping
        """
        specs = {}
        
        # Find electrical characteristics section
        elec_sections = self._find_sections(text, [
            'electrical characteristics', 'electrical specifications',
            'dc characteristics', 'ac characteristics', 'absolute maximum ratings'
        ])
        
        # Common electrical parameters to look for
        parameters = [
            ('supply voltage', r'[Vv]cc|[Vv]dd|[Vv]supply'),
            ('operating voltage', r'[Vv]op|[Vv]operating'),
            ('input voltage', r'[Vv]in|[Vv]input'),
            ('output voltage', r'[Vv]out|[Vv]output'),
            ('supply current', r'[Ii]cc|[Ii]dd|[Ii]supply'),
            ('operating current', r'[Ii]op|[Ii]operating'),
            ('power dissipation', r'[Pp]d|[Pp]ower'),
            ('operating temperature', r'[Tt]op|[Tt]emp'),
            ('frequency', r'[Ff]req|[Ff]clk|MHz|kHz'),
            ('input offset voltage', r'[Vv]os|[Vv]offset'),
            ('gain bandwidth', r'GBW|GBWP'),
            ('slew rate', r'SR|[Ss]lew')
        ]
        
        for section in elec_sections:
            for param_name, pattern in parameters:
                # Look for parameter with value
                param_regex = f'{pattern}.*?([\\d.]+\\s*[mkMGT]?[VvAaWwHhzZ])'
                matches = re.finditer(param_regex, section, re.IGNORECASE)
                
                for match in matches:
                    value = match.group(1)
                    # Clean up the parameter name
                    full_match = match.group(0)
                    param_key = param_name
                    
                    # Try to extract min/max/typ
                    if 'min' in full_match.lower():
                        param_key += ' (min)'
                    elif 'max' in full_match.lower():
                        param_key += ' (max)'
                    elif 'typ' in full_match.lower():
                        param_key += ' (typ)'
                    
                    specs[param_key] = value
        
        # Also extract from tables
        table_specs = self._extract_specs_from_tables(text)
        specs.update(table_specs)
        
        return specs
    
    def extract_recommended_circuits(self, text: str) -> List[Dict[str, str]]:
        """Extract recommended circuit information
        
        Args:
            text: Datasheet text
            
        Returns:
            list: List of circuit descriptions
        """
        circuits = []
        
        # Find application/circuit sections
        circuit_sections = self._find_sections(text, [
            'typical application', 'application circuit', 'reference design',
            'recommended circuit', 'typical circuit', 'application example'
        ])
        
        for i, section in enumerate(circuit_sections):
            circuit_info = {
                'name': f'Application Circuit {i+1}',
                'description': self._extract_circuit_description(section),
                'components': self._extract_circuit_components(section)
            }
            
            # Try to find circuit name
            name_match = re.search(r'Figure\s+\d+[:.]\s*(.+?)(?:\n|$)', section)
            if name_match:
                circuit_info['name'] = name_match.group(1).strip()
            
            circuits.append(circuit_info)
        
        return circuits
    
    def extract_key_parameters(self, text: str) -> Dict[str, str]:
        """Extract key component parameters
        
        Args:
            text: Datasheet text
            
        Returns:
            dict: Key parameters
        """
        parameters = {}
        
        # Look for key features or parameters section
        param_sections = self._find_sections(text, [
            'key features', 'key parameters', 'features', 'highlights'
        ])
        
        # Extract bullet points or listed items
        for section in param_sections:
            # Find bullet points
            bullets = re.findall(r'[•▪▫◦‣⁃]\s*(.+?)(?=\n|$)', section)
            for i, bullet in enumerate(bullets[:10]):  # Limit to first 10
                parameters[f'feature_{i+1}'] = bullet.strip()
            
            # Find numbered items
            numbered = re.findall(r'^\d+\.\s*(.+?)(?=\n|$)', section, re.MULTILINE)
            for i, item in enumerate(numbered[:10]):
                parameters[f'spec_{i+1}'] = item.strip()
        
        return parameters
    
    def extract_features(self, text: str) -> List[str]:
        """Extract product features
        
        Args:
            text: Datasheet text
            
        Returns:
            list: List of features
        """
        features = []
        
        # Find features section
        feature_sections = self._find_sections(text, [
            'features', 'key features', 'product features', 'highlights'
        ])
        
        for section in feature_sections:
            # Extract bullet points
            bullets = re.findall(r'[•▪▫◦‣⁃]\s*(.+?)(?=\n|$)', section)
            features.extend([b.strip() for b in bullets])
            
            # Extract numbered features
            numbered = re.findall(r'^\d+\.\s*(.+?)(?=\n|$)', section, re.MULTILINE)
            features.extend([n.strip() for n in numbered])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for feature in features:
            if feature not in seen and len(feature) > 10:  # Min length filter
                seen.add(feature)
                unique_features.append(feature)
        
        return unique_features[:20]  # Limit to 20 features
    
    def extract_operating_conditions(self, text: str) -> Dict[str, str]:
        """Extract operating conditions
        
        Args:
            text: Datasheet text
            
        Returns:
            dict: Operating conditions
        """
        conditions = {}
        
        # Find operating conditions section
        op_sections = self._find_sections(text, [
            'operating conditions', 'recommended operating conditions',
            'operating ratings', 'environmental conditions'
        ])
        
        # Parameters to look for
        op_params = [
            ('temperature', r'[Tt]emperature.*?(-?\d+°?C?\s*to\s*\+?\d+°?C?)'),
            ('voltage', r'[Vv]oltage.*?(\d+\.?\d*\s*V?\s*to\s*\d+\.?\d*\s*V?)'),
            ('humidity', r'[Hh]umidity.*?(\d+%?\s*to\s*\d+%?)'),
            ('altitude', r'[Aa]ltitude.*?(\d+\s*m)'),
        ]
        
        for section in op_sections:
            for param_name, pattern in op_params:
                match = re.search(pattern, section)
                if match:
                    conditions[param_name] = match.group(1)
        
        return conditions
    
    def extract_package_info(self, text: str) -> str:
        """Extract package information
        
        Args:
            text: Datasheet text
            
        Returns:
            str: Package description
        """
        # Common package patterns
        package_patterns = [
            r'([A-Z]+\d+)\s*package',
            r'Package:\s*([A-Z]+\d+)',
            r'(DIP|SOIC|TSSOP|QFN|LQFP|BGA|SOT)[-\s]?\d+',
            r'\d+[-\s]?pin\s+([A-Z]+)',
        ]
        
        for pattern in package_patterns:
            match = re.search(pattern, text[:5000])  # Check first 5000 chars
            if match:
                return match.group(0)
        
        return "Package information not found"
    
    def extract_application_notes(self, text: str) -> List[str]:
        """Extract application notes and design guidelines
        
        Args:
            text: Datasheet text
            
        Returns:
            list: Application notes
        """
        notes = []
        
        # Find application notes sections
        app_sections = self._find_sections(text, [
            'application note', 'design note', 'layout guidelines',
            'pcb layout', 'design considerations', 'implementation'
        ])
        
        for section in app_sections:
            # Extract important notes (usually in bold or after "Note:")
            note_patterns = [
                r'Note:\s*(.+?)(?=\n|$)',
                r'Important:\s*(.+?)(?=\n|$)',
                r'Caution:\s*(.+?)(?=\n|$)',
                r'Warning:\s*(.+?)(?=\n|$)'
            ]
            
            for pattern in note_patterns:
                matches = re.finditer(pattern, section, re.IGNORECASE)
                for match in matches:
                    notes.append(match.group(1).strip())
        
        return notes[:10]  # Limit to 10 notes
    
    def _find_sections(self, text: str, keywords: List[str]) -> List[str]:
        """Find text sections containing keywords
        
        Args:
            text: Full text
            keywords: Keywords to search for
            
        Returns:
            list: Found sections
        """
        sections = []
        
        for keyword in keywords:
            # Case-insensitive search for section headers
            pattern = f'(?i){keyword}.*?\n(.*?)(?=\\n\\n|\\n[A-Z][A-Z\\s]+:|$)'
            matches = re.finditer(pattern, text, re.DOTALL)
            
            for match in matches:
                section_text = match.group(1)
                if len(section_text) > 50:  # Minimum section length
                    sections.append(section_text[:2000])  # Limit section length
        
        return sections
    
    def _parse_pin_table(self, text: str) -> Dict[str, str]:
        """Parse pin information from table-like text
        
        Args:
            text: Table text
            
        Returns:
            dict: Pin configurations
        """
        pins = {}
        
        # Try to parse table rows
        # Pattern: number, name, type, description
        row_pattern = r'(\d+)\s+([A-Z]+\d*/?[A-Z]*)\s+([IO/]+)?\s*(.+?)(?=\n\d+\s|$)'
        matches = re.finditer(row_pattern, text, re.MULTILINE)
        
        for match in matches:
            pin_num = match.group(1)
            pin_name = match.group(2)
            pin_type = match.group(3) or ''
            pin_desc = match.group(4).strip()
            
            pins[pin_num] = f"{pin_name} ({pin_type}): {pin_desc}".strip()
        
        return pins
    
    def _extract_specs_from_tables(self, text: str) -> Dict[str, str]:
        """Extract specifications from table-like structures
        
        Args:
            text: Text containing tables
            
        Returns:
            dict: Extracted specifications
        """
        specs = {}
        
        # Pattern for parameter-value pairs in tables
        # Parameter | Min | Typ | Max | Unit
        table_pattern = r'([A-Za-z\s]+)\s*\|\s*([\d.]+)?\s*\|\s*([\d.]+)?\s*\|\s*([\d.]+)?\s*\|\s*([A-Za-z]+)?'
        
        matches = re.finditer(table_pattern, text)
        for match in matches:
            param = match.group(1).strip()
            typ_val = match.group(3)
            unit = match.group(5) or ''
            
            if typ_val:
                specs[param] = f"{typ_val} {unit}".strip()
        
        return specs
    
    def _extract_circuit_description(self, text: str) -> str:
        """Extract circuit description from section
        
        Args:
            text: Circuit section text
            
        Returns:
            str: Circuit description
        """
        # Look for description at beginning of section
        desc_match = re.match(r'^(.{20,200}?)(?=[A-Z][a-z]+:|\n\n)', text, re.DOTALL)
        if desc_match:
            return desc_match.group(1).strip()
        
        # Otherwise return first few lines
        lines = text.split('\n')
        return ' '.join(lines[:3])
    
    def _extract_circuit_components(self, text: str) -> str:
        """Extract component list from circuit description
        
        Args:
            text: Circuit text
            
        Returns:
            str: Component list
        """
        components = []
        
        # Look for component values
        comp_values = extract_component_values(text)
        components.extend(comp_values)
        
        # Look for component references
        comp_refs = re.findall(r'[RCL]\d+', text)
        for ref in comp_refs:
            # Try to find associated value
            value_pattern = f'{ref}.*?([\\d.]+\\s*[kMmunp]?[ΩFH])'
            match = re.search(value_pattern, text)
            if match:
                components.append(f"{ref}: {match.group(1)}")
        
        return ', '.join(components[:10])  # Limit to 10 components


def identify_section_headers(text: str) -> List[Tuple[int, str]]:
    """Identify section headers in datasheet text
    
    Args:
        text: Datasheet text
        
    Returns:
        list: List of (position, header) tuples
    """
    headers = []
    
    # Common header patterns
    header_patterns = [
        r'^(\d+\.?\d*\s+[A-Z][A-Za-z\s]+)$',  # Numbered sections
        r'^([A-Z][A-Z\s]+):?$',  # All caps headers
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$'  # Title case headers
    ]
    
    lines = text.split('\n')
    position = 0
    
    for line in lines:
        for pattern in header_patterns:
            if re.match(pattern, line.strip()):
                headers.append((position, line.strip()))
                break
        position += len(line) + 1  # +1 for newline
    
    return headers


def parse_table_data(text_block: str) -> List[List[str]]:
    """Parse table data from text block
    
    Args:
        text_block: Text containing table
        
    Returns:
        list: Table as list of lists
    """
    rows = []
    
    # Split by lines
    lines = text_block.strip().split('\n')
    
    for line in lines:
        # Try different delimiters
        if '|' in line:
            cells = [cell.strip() for cell in line.split('|')]
        elif '\t' in line:
            cells = [cell.strip() for cell in line.split('\t')]
        elif re.search(r'\s{2,}', line):  # Multiple spaces
            cells = [cell.strip() for cell in re.split(r'\s{2,}', line)]
        else:
            continue
        
        if cells and len(cells) > 1:
            rows.append(cells)
    
    return rows


def normalize_units(value_string: str) -> str:
    """Normalize unit representations
    
    Args:
        value_string: Value with unit
        
    Returns:
        str: Normalized value
    """
    # Common unit normalizations
    normalizations = {
        'kohm': 'kΩ',
        'kohms': 'kΩ',
        'megohm': 'MΩ',
        'megohms': 'MΩ',
        'microfarad': 'µF',
        'microfarads': 'µF',
        'nanofarad': 'nF',
        'nanofarads': 'nF',
        'picofarad': 'pF',
        'picofarads': 'pF',
        'millihenry': 'mH',
        'millihenries': 'mH',
        'microhenry': 'µH',
        'microhenries': 'µH',
        'volts': 'V',
        'amps': 'A',
        'amperes': 'A',
        'watts': 'W',
        'hertz': 'Hz',
        'celsius': '°C',
        'fahrenheit': '°F'
    }
    
    # Convert to lowercase for matching
    lower_value = value_string.lower()
    
    # Replace known normalizations
    for old_unit, new_unit in normalizations.items():
        if old_unit in lower_value:
            return value_string.replace(old_unit, new_unit)
    
    # Handle common abbreviations
    # k = 1000, M = 1,000,000, etc.
    if re.search(r'\d+k(?![a-z])', value_string, re.IGNORECASE):
        return re.sub(r'(\d+)k(?![a-z])', r'\1k', value_string, flags=re.IGNORECASE)
    
    return value_string


if __name__ == "__main__":
    # Test the datasheet parser
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Sample datasheet text for testing
    test_text = """
    LM7805 DATASHEET
    
    FEATURES
    • Output Current up to 1A
    • Output Voltages of 5V
    • Thermal Overload Protection
    
    PIN CONFIGURATION
    Pin 1 INPUT - Connect to unregulated DC input
    Pin 2 GROUND - Connect to ground
    Pin 3 OUTPUT - Regulated 5V output
    
    ELECTRICAL CHARACTERISTICS
    Input Voltage: 7V to 35V
    Output Voltage: 5V ±4%
    Output Current: 1A max
    Power Dissipation: 15W max
    Operating Temperature: 0°C to 125°C
    
    TYPICAL APPLICATION
    The LM7805 requires only two external capacitors for operation.
    Input capacitor C1: 0.33µF
    Output capacitor C2: 0.1µF
    """
    
    parser = DatasheetParser()
    result = parser.parse(test_text)
    
    print("Datasheet Parser Test Results:")
    print(f"Component: {result['component_name']}")
    print(f"Features: {len(result['features'])} found")
    print(f"Pin Config: {len(result['pin_config'])} pins")
    print(f"Electrical Specs: {len(result['electrical_specs'])} parameters")
    print(f"Operating Conditions: {len(result['operating_conditions'])} conditions")