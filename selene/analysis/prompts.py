"""
Enhanced prompt templates for different analysis types
"""

# Comprehensive prompt templates for each analysis type
PROMPT_TEMPLATES = {
    "Component Verification": """
Analyze the schematic components against the provided datasheet:
1. Verify component values match datasheet recommendations
   - Check resistor values for pull-ups, pull-downs, and biasing
   - Verify capacitor values for decoupling, filtering, and timing
   - Confirm inductor/transformer specifications if present

2. Check pin configurations are correct
   - Verify all pins are connected according to function
   - Identify any unconnected pins that require termination
   - Check for proper power and ground connections

3. Identify missing components mentioned in datasheet
   - Look for required external components (crystals, capacitors, etc.)
   - Check for recommended protection circuits
   - Verify presence of decoupling capacitors

4. Validate power supply requirements
   - Confirm voltage levels match specifications
   - Check current capacity is adequate
   - Verify proper power sequencing if required

Please provide specific findings with component designators (R1, C1, etc.) and reference relevant datasheet sections.
""",

    "Pin Configuration Check": """
Review pin connections against datasheet specifications:
1. Check all pin assignments are correct
   - Verify each pin number matches its intended function
   - Confirm no pins are swapped or misconnected
   - Check differential pairs are properly routed

2. Verify required pull-ups/pull-downs are present
   - Identify pins requiring pull-up resistors
   - Check for pins needing pull-down resistors
   - Verify resistor values match recommendations

3. Validate power and ground connections
   - Ensure all power pins are connected
   - Verify all ground pins are connected
   - Check for proper power supply decoupling

4. Check for unused pins handling
   - Identify floating inputs that should be tied
   - Verify unused outputs are left unconnected
   - Check special pins (test, mode selection, etc.)

Reference the datasheet pin configuration table and provide specific pin numbers in your findings.
""",

    "Power Supply Analysis": """
Analyze power supply design using datasheet specifications:
1. Verify voltage levels match datasheet requirements
   - Check input voltage range compliance
   - Verify regulated output voltages
   - Confirm voltage tolerances are met

2. Check decoupling capacitor values and placement
   - Verify capacitor values match recommendations
   - Check for proper capacitor types (ceramic, electrolytic)
   - Confirm placement near power pins

3. Validate current capacity requirements
   - Calculate total current consumption
   - Verify regulator current rating is adequate
   - Check for proper heat dissipation

4. Review power sequencing if applicable
   - Verify correct power-up sequence
   - Check for required delays between rails
   - Confirm power-good signals if used

Compare against datasheet electrical characteristics and reference application notes.
""",

    "Design Compliance": """
Check overall design compliance with datasheet recommendations:
1. Compare to reference designs in datasheet
   - Identify deviations from recommended circuits
   - Check if modifications are acceptable
   - Verify critical circuit sections match

2. Verify all recommended external components
   - Check for presence of all suggested components
   - Verify component values and tolerances
   - Confirm component placement guidelines

3. Check thermal considerations
   - Verify adequate copper area for heat dissipation
   - Check for thermal vias if recommended
   - Confirm ambient temperature specifications

4. Validate application circuit examples
   - Compare against typical application circuits
   - Verify any additional features are properly implemented
   - Check for application-specific requirements

Provide detailed comparison with datasheet recommendations and note any concerns.
""",

    "Missing Components": """
Identify components missing from schematic but required by datasheet:
1. Check for missing protection circuits
   - ESD protection diodes
   - Overvoltage protection
   - Reverse polarity protection
   - Current limiting resistors

2. Verify all required external components
   - Crystal/oscillator and load capacitors
   - Reset circuit components
   - Bias resistors and capacitors
   - Compensation components

3. Check for missing filter components
   - Input/output filter capacitors
   - EMI suppression components
   - Power supply filters
   - Signal conditioning components

4. Validate crystal/clock circuitry
   - Crystal and load capacitors
   - Feedback resistor if required
   - Clock buffer/driver components

List each missing component with its purpose and datasheet reference.
""",

    "Custom Query": """
Analyze the schematic based on the user's specific question.

Consider the following aspects if relevant:
- Component values and ratings
- Pin connections and signal routing  
- Power supply design
- Grounding and shielding
- Signal integrity
- Thermal management
- EMC/EMI considerations
- Safety and protection circuits

Provide a detailed response addressing the user's query with specific references to components and connections visible in the schematic.
"""
}


def get_prompt_template(analysis_type: str) -> str:
    """Get prompt template for specific analysis type
    
    Args:
        analysis_type: Type of analysis requested
        
    Returns:
        str: Prompt template
    """
    return PROMPT_TEMPLATES.get(analysis_type, PROMPT_TEMPLATES["Custom Query"])


def customize_prompt(template: str, parameters: dict) -> str:
    """Customize a prompt template with specific parameters
    
    Args:
        template: Base prompt template
        parameters: Dictionary of parameters to insert
        
    Returns:
        str: Customized prompt
    """
    # Simple parameter substitution
    for key, value in parameters.items():
        placeholder = f"{{{key}}}"
        if placeholder in template:
            template = template.replace(placeholder, str(value))
    
    return template


def add_datasheet_instructions(prompt: str) -> str:
    """Add datasheet-specific instructions to a prompt
    
    Args:
        prompt: Base prompt
        
    Returns:
        str: Enhanced prompt with datasheet instructions
    """
    datasheet_instructions = """

When referencing the datasheet:
- Cite specific section numbers or page numbers when possible
- Quote relevant specifications directly
- Mention table or figure numbers for easy reference
- Highlight any discrepancies between schematic and datasheet recommendations
"""
    
    return prompt + datasheet_instructions


# Additional context snippets for enhanced analysis
ANALYSIS_CONTEXT = {
    "component_identification": """
Focus on identifying components by their designators:
- Resistors: R1, R2, etc.
- Capacitors: C1, C2, etc.
- Inductors: L1, L2, etc.
- Integrated Circuits: U1, U2, etc.
- Transistors: Q1, Q2, etc.
- Diodes: D1, D2, etc.
""",

    "value_notation": """
Component value notations:
- Resistors: Ω, kΩ, MΩ (e.g., 10k = 10,000Ω)
- Capacitors: pF, nF, µF (e.g., 100n = 100nF = 0.1µF)
- Inductors: nH, µH, mH
- Voltages: V, mV
- Currents: A, mA, µA
""",

    "common_issues": """
Common schematic issues to check:
- Floating inputs (especially on CMOS devices)
- Missing bypass/decoupling capacitors
- Incorrect pull-up/pull-down values
- Power supply sequencing problems
- Ground loops or split grounds
- Missing termination resistors
- Incorrect crystal load capacitors
"""
}


def get_analysis_context(context_type: str) -> str:
    """Get additional context for analysis
    
    Args:
        context_type: Type of context needed
        
    Returns:
        str: Context information
    """
    return ANALYSIS_CONTEXT.get(context_type, "")


# Severity levels for findings
SEVERITY_LEVELS = {
    "CRITICAL": "🔴 Critical - Will prevent circuit from functioning",
    "HIGH": "🟠 High - May cause unreliable operation", 
    "MEDIUM": "🟡 Medium - Could affect performance",
    "LOW": "🟢 Low - Minor issue or improvement suggestion",
    "INFO": "ℹ️ Info - General observation or note"
}


def format_finding(severity: str, issue: str, recommendation: str = "", reference: str = "") -> str:
    """Format an analysis finding
    
    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
        issue: Description of the issue
        recommendation: Recommended action
        reference: Datasheet reference
        
    Returns:
        str: Formatted finding
    """
    severity_prefix = SEVERITY_LEVELS.get(severity, "")
    
    finding = f"{severity_prefix} {issue}"
    
    if recommendation:
        finding += f"\n   → Recommendation: {recommendation}"
    
    if reference:
        finding += f"\n   → Reference: {reference}"
    
    return finding