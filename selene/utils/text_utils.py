"""
Text processing helpers for SELENE
"""

import re
import logging
from typing import List, Optional, Tuple, Set


def extract_between_markers(text: str, start_marker: str, end_marker: str) -> List[str]:
    """Extract text between start and end markers
    
    Args:
        text: Input text
        start_marker: Starting delimiter
        end_marker: Ending delimiter
        
    Returns:
        list: List of extracted text segments
    """
    segments = []
    
    # Escape special regex characters
    start_escaped = re.escape(start_marker)
    end_escaped = re.escape(end_marker)
    
    # Create pattern
    pattern = f'{start_escaped}(.*?){end_escaped}'
    
    # Find all matches
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        segments.append(match.group(1).strip())
    
    return segments


def find_all_numbers(text: str, include_units: bool = True) -> List[str]:
    """Find all numeric values in text
    
    Args:
        text: Input text
        include_units: Whether to include unit suffixes
        
    Returns:
        list: List of found numbers (with units if requested)
    """
    if include_units:
        # Pattern for numbers with optional units
        pattern = r'[\d.]+\s*[kMGTmµnp]?[ΩFHVAWHz°]?'
    else:
        # Just numbers (including decimals)
        pattern = r'[\d.]+'
    
    matches = re.findall(pattern, text)
    
    # Filter out lone decimal points
    return [match for match in matches if not match.strip() == '.']


def extract_component_values(text: str) -> List[str]:
    """Extract electronic component values from text
    
    Args:
        text: Input text
        
    Returns:
        list: List of component values (e.g., "10kΩ", "100nF", "3.3V")
    """
    component_values = []
    
    # Common component value patterns
    patterns = [
        # Resistors
        r'\d+\.?\d*\s*[kMGT]?Ω',
        r'\d+\.?\d*\s*[kMGT]?[Oo]hm',
        
        # Capacitors
        r'\d+\.?\d*\s*[µμnpm]?F',
        r'\d+\.?\d*\s*[µμ]?[Ff]arad',
        
        # Inductors
        r'\d+\.?\d*\s*[µμnmm]?H',
        r'\d+\.?\d*\s*[µμnmm]?[Hh]enry',
        
        # Voltages
        r'\d+\.?\d*\s*[mkMG]?V',
        r'\d+\.?\d*\s*[Vv]olt',
        
        # Currents
        r'\d+\.?\d*\s*[mkMG]?A',
        r'\d+\.?\d*\s*[Aa]mp',
        
        # Frequencies
        r'\d+\.?\d*\s*[kMGT]?Hz',
        
        # Power
        r'\d+\.?\d*\s*[mkMG]?W',
        r'\d+\.?\d*\s*[Ww]att',
        
        # Temperatures
        r'\d+\.?\d*\s*°?[CF]'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        component_values.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_values = []
    for value in component_values:
        normalized = value.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique_values.append(value.strip())
    
    return unique_values


def clean_whitespace(text: str) -> str:
    """Clean excessive whitespace from text
    
    Args:
        text: Input text
        
    Returns:
        str: Cleaned text
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace from lines
    lines = text.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    
    # Remove empty lines at start and end
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)


def highlight_text_segments(text: str, segments: List[str], 
                          start_tag: str = '<mark>', end_tag: str = '</mark>') -> str:
    """Highlight specific text segments
    
    Args:
        text: Input text
        segments: List of text segments to highlight
        start_tag: Opening tag for highlighting
        end_tag: Closing tag for highlighting
        
    Returns:
        str: Text with highlighted segments
    """
    result = text
    
    # Sort segments by length (longest first) to avoid partial replacements
    sorted_segments = sorted(segments, key=len, reverse=True)
    
    for segment in sorted_segments:
        if segment in result:
            # Use word boundaries to avoid partial matches
            pattern = re.escape(segment)
            replacement = f'{start_tag}{segment}{end_tag}'
            result = re.sub(pattern, replacement, result)
    
    return result


def extract_pin_references(text: str) -> List[str]:
    """Extract pin references from text (e.g., Pin 1, PIN_A, etc.)
    
    Args:
        text: Input text
        
    Returns:
        list: List of pin references
    """
    pin_patterns = [
        r'[Pp]in\s*\d+',          # Pin 1, pin 2, etc.
        r'PIN\s*\d+',             # PIN 1, PIN 2, etc.
        r'[Pp]in\s*[A-Z]\d*',     # Pin A, Pin A1, etc.
        r'PIN_[A-Z]\d*',          # PIN_A, PIN_A1, etc.
        r'[A-Z]+\d*\s*pin',       # VCC pin, GND pin, etc.
        r'[A-Z]+\d*/[A-Z]+\d*',   # VCC/VDD, SDA/SCL, etc.
    ]
    
    pins = []
    for pattern in pin_patterns:
        matches = re.findall(pattern, text)
        pins.extend(matches)
    
    # Remove duplicates and clean up
    unique_pins = []
    seen = set()
    for pin in pins:
        cleaned = pin.strip()
        if cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            unique_pins.append(cleaned)
    
    return unique_pins


def extract_component_references(text: str) -> List[str]:
    """Extract component references (R1, C2, U3, etc.)
    
    Args:
        text: Input text
        
    Returns:
        list: List of component references
    """
    # Common component reference patterns
    patterns = [
        r'[RrCcLlUuQqDdJjXxYy]\d+',  # R1, C2, L3, U4, Q5, D6, J7, X8, Y9
        r'[RCLQD]_?\d+',              # R_1, C_2, etc.
        r'[A-Z]{1,3}\d+[A-Z]?',       # IC1, LED2, SW3A, etc.
    ]
    
    components = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        components.extend(matches)
    
    # Remove duplicates and sort
    unique_components = list(set(components))
    unique_components.sort()
    
    return unique_components


def extract_voltage_references(text: str) -> List[str]:
    """Extract voltage rail references (VCC, VDD, GND, etc.)
    
    Args:
        text: Input text
        
    Returns:
        list: List of voltage references
    """
    voltage_patterns = [
        r'V[CDSAIO][CDSAIO]?',     # VCC, VDD, VSS, VIO, etc.
        r'V[+-]?\d+[V.]?\d*',      # V3.3, V+5, V-12, etc.
        r'GND|GROUND',             # Ground references
        r'V[A-Z]{2,4}',            # VBAT, VREF, VCORE, etc.
        r'[+-]?\d+V\d*',           # +5V, -12V, 3V3, etc.
        r'AVDD|DVDD|AVSS|DVSS',    # Analog/Digital supplies
    ]
    
    voltages = []
    for pattern in voltage_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        voltages.extend(matches)
    
    # Remove duplicates and clean up
    unique_voltages = []
    seen = set()
    for voltage in voltages:
        cleaned = voltage.upper().strip()
        if cleaned not in seen:
            seen.add(cleaned)
            unique_voltages.append(cleaned)
    
    return unique_voltages


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences
    
    Args:
        text: Input text
        
    Returns:
        list: List of sentences
    """
    # Simple sentence splitting - can be enhanced
    sentences = re.split(r'[.!?]+\s+', text)
    
    # Clean up sentences
    cleaned_sentences = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned and len(cleaned) > 5:  # Minimum sentence length
            cleaned_sentences.append(cleaned)
    
    return cleaned_sentences


def extract_technical_terms(text: str) -> Set[str]:
    """Extract technical terms and acronyms
    
    Args:
        text: Input text
        
    Returns:
        set: Set of technical terms
    """
    terms = set()
    
    # Acronyms (2-6 uppercase letters)
    acronyms = re.findall(r'\b[A-Z]{2,6}\b', text)
    terms.update(acronyms)
    
    # Technical terms with numbers
    tech_terms = re.findall(r'\b[A-Z][a-z]*\d+[A-Za-z]*\b', text)
    terms.update(tech_terms)
    
    # Common electronic terms
    electronic_terms = [
        'amplifier', 'oscillator', 'regulator', 'converter', 'multiplexer',
        'comparator', 'operational', 'differential', 'transistor', 'diode',
        'capacitor', 'resistor', 'inductor', 'transformer', 'relay',
        'microcontroller', 'processor', 'memory', 'flash', 'eeprom',
        'analog', 'digital', 'pwm', 'adc', 'dac', 'uart', 'spi', 'i2c'
    ]
    
    for term in electronic_terms:
        if term.lower() in text.lower():
            terms.add(term.title())
    
    return terms


def normalize_component_value(value: str) -> str:
    """Normalize component value format
    
    Args:
        value: Component value string
        
    Returns:
        str: Normalized value
    """
    value = value.strip()
    
    # Common normalizations
    normalizations = {
        # Resistance
        'ohm': 'Ω', 'ohms': 'Ω', 'Ohm': 'Ω', 'Ohms': 'Ω',
        'kohm': 'kΩ', 'kohms': 'kΩ', 'KOhm': 'kΩ', 'KOhms': 'kΩ',
        'megohm': 'MΩ', 'megohms': 'MΩ', 'MOhm': 'MΩ', 'MOhms': 'MΩ',
        
        # Capacitance  
        'farad': 'F', 'farads': 'F', 'Farad': 'F', 'Farads': 'F',
        'uF': 'µF', 'uf': 'µF', 'microfarad': 'µF', 'microfarads': 'µF',
        'nF': 'nF', 'nf': 'nF', 'nanofarad': 'nF', 'nanofarads': 'nF',
        'pF': 'pF', 'pf': 'pF', 'picofarad': 'pF', 'picofarads': 'pF',
        
        # Inductance
        'henry': 'H', 'henries': 'H', 'Henry': 'H', 'Henries': 'H',
        'mH': 'mH', 'mh': 'mH', 'millihenry': 'mH', 'millihenries': 'mH',
        'uH': 'µH', 'uh': 'µH', 'microhenry': 'µH', 'microhenries': 'µH',
        
        # Voltage
        'volt': 'V', 'volts': 'V', 'Volt': 'V', 'Volts': 'V',
        'mV': 'mV', 'mv': 'mV', 'millivolt': 'mV', 'millivolts': 'mV',
        'kV': 'kV', 'kv': 'kV', 'kilovolt': 'kV', 'kilovolts': 'kV',
        
        # Current
        'amp': 'A', 'amps': 'A', 'ampere': 'A', 'amperes': 'A',
        'mA': 'mA', 'ma': 'mA', 'milliamp': 'mA', 'milliamps': 'mA',
        'uA': 'µA', 'ua': 'µA', 'microamp': 'µA', 'microamps': 'µA',
        
        # Power
        'watt': 'W', 'watts': 'W', 'Watt': 'W', 'Watts': 'W',
        'mW': 'mW', 'mw': 'mW', 'milliwatt': 'mW', 'milliwatts': 'mW',
        'kW': 'kW', 'kw': 'kW', 'kilowatt': 'kW', 'kilowatts': 'kW',
        
        # Frequency
        'hertz': 'Hz', 'Hertz': 'Hz', 'hz': 'Hz',
        'kHz': 'kHz', 'khz': 'kHz', 'kilohertz': 'kHz',
        'MHz': 'MHz', 'mhz': 'MHz', 'megahertz': 'MHz',
        'GHz': 'GHz', 'ghz': 'GHz', 'gigahertz': 'GHz'
    }
    
    # Apply normalizations
    for old, new in normalizations.items():
        value = value.replace(old, new)
    
    # Remove extra spaces
    value = re.sub(r'\s+', ' ', value)
    
    return value.strip()


def find_datasheet_sections(text: str) -> List[Tuple[str, int, int]]:
    """Find major sections in datasheet text
    
    Args:
        text: Datasheet text
        
    Returns:
        list: List of (section_name, start_pos, end_pos) tuples
    """
    sections = []
    
    # Common datasheet section patterns
    section_patterns = [
        r'(?i)(features?)\s*:?\s*\n',
        r'(?i)(pin\s+configuration)\s*:?\s*\n',
        r'(?i)(pin\s+description)\s*:?\s*\n',
        r'(?i)(electrical\s+characteristics)\s*:?\s*\n',
        r'(?i)(absolute\s+maximum\s+ratings?)\s*:?\s*\n',
        r'(?i)(recommended\s+operating\s+conditions?)\s*:?\s*\n',
        r'(?i)(typical\s+application)\s*:?\s*\n',
        r'(?i)(application\s+circuit)\s*:?\s*\n',
        r'(?i)(timing\s+diagram)\s*:?\s*\n',
        r'(?i)(package\s+information)\s*:?\s*\n',
        r'(?i)(ordering\s+information)\s*:?\s*\n'
    ]
    
    for pattern in section_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            section_name = match.group(1).strip()
            start_pos = match.start()
            
            # Find end position (next section or end of text)
            next_section_pos = len(text)
            for other_pattern in section_patterns:
                if other_pattern != pattern:
                    other_matches = re.finditer(other_pattern, text[start_pos + len(match.group(0)):])
                    for other_match in other_matches:
                        candidate_end = start_pos + len(match.group(0)) + other_match.start()
                        if candidate_end < next_section_pos:
                            next_section_pos = candidate_end
                        break
            
            sections.append((section_name, start_pos, next_section_pos))
    
    # Sort by position
    sections.sort(key=lambda x: x[1])
    
    return sections


def extract_table_like_data(text: str) -> List[List[str]]:
    """Extract table-like data from text
    
    Args:
        text: Text potentially containing tables
        
    Returns:
        list: List of table rows, each row is a list of cells
    """
    tables = []
    lines = text.split('\n')
    
    current_table = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_table and current_table:
                tables.extend(current_table)
                current_table = []
                in_table = False
            continue
        
        # Check if line looks like a table row (has delimiters)
        delimiters = ['|', '\t']
        has_delimiter = any(delimiter in line for delimiter in delimiters)
        
        # Or has multiple spaced items
        spaced_items = len(re.findall(r'\S+', line)) >= 3
        has_aligned_spacing = len(re.findall(r'\s{2,}', line)) >= 2
        
        if has_delimiter or (spaced_items and has_aligned_spacing):
            # Parse the row
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|')]
            elif '\t' in line:
                cells = [cell.strip() for cell in line.split('\t')]
            else:
                # Split on multiple spaces
                cells = [cell.strip() for cell in re.split(r'\s{2,}', line)]
            
            # Filter out empty cells
            cells = [cell for cell in cells if cell]
            
            if len(cells) >= 2:  # Minimum columns for a table
                current_table.append(cells)
                in_table = True
        else:
            if in_table and current_table:
                tables.extend(current_table)
                current_table = []
                in_table = False
    
    # Add any remaining table
    if current_table:
        tables.extend(current_table)
    
    return tables


if __name__ == "__main__":
    # Test the text utilities
    test_text = """
    LM7805 5V Regulator
    
    Features:
    • Output current up to 1A
    • Input voltage range: 7V to 35V
    • Built-in thermal protection
    
    Pin Configuration:
    Pin 1 (INPUT): Connect to unregulated DC input through C1 (0.33µF)
    Pin 2 (GND): Connect to ground plane
    Pin 3 (OUTPUT): Regulated 5V output with C2 (0.1µF) to ground
    
    Typical Application:
    Use R1 = 10kΩ, C1 = 100nF, and LED1 for power indication.
    Connect VCC to Pin 1, GND to Pin 2.
    """
    
    print("Text Utilities Test:")
    print(f"Component values: {extract_component_values(test_text)}")
    print(f"Pin references: {extract_pin_references(test_text)}")
    print(f"Component references: {extract_component_references(test_text)}")
    print(f"Voltage references: {extract_voltage_references(test_text)}")
    print(f"Numbers found: {find_all_numbers(test_text)}")
    
    # Test normalization
    test_values = ["10kohm", "100nF", "3.3V", "1mA", "50MHz"]
    print(f"Normalized values: {[normalize_component_value(v) for v in test_values]}")