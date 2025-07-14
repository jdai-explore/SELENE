"""
Build analysis context combining schematic and datasheet information - Fixed version
"""

import logging
from typing import Dict, Optional, List, Any
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.prompts import PROMPT_TEMPLATES
import config


class ContextBuilder:
    """Build comprehensive analysis context from multiple sources"""
    
    def __init__(self):
        """Initialize context builder"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Context builder initialized")
    
    def build_analysis_context(
        self,
        schematic_path: str,
        datasheet_data: Dict[str, Any],
        query_type: str,
        custom_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build complete analysis context
        
        Args:
            schematic_path: Path to schematic image
            datasheet_data: Parsed datasheet information
            query_type: Type of analysis requested
            custom_query: Custom query text if applicable
            
        Returns:
            dict: Complete context for analysis
        """
        try:
            # Ensure datasheet_data is a dict
            if not isinstance(datasheet_data, dict):
                self.logger.warning(f"datasheet_data is not a dict, got {type(datasheet_data)}")
                datasheet_data = {}
            
            context = {
                'schematic_path': schematic_path,
                'query_type': query_type,
                'has_datasheet': bool(datasheet_data and datasheet_data.get('component_name') != 'Unknown'),
                'timestamp': self._get_timestamp()
            }
            
            # Add schematic context
            self.add_schematic_context(context, schematic_path)
            
            # Add datasheet context if available
            if datasheet_data:
                self.add_datasheet_context(context, datasheet_data)
            
            # Build the prompt
            if query_type == "Custom Query":
                context['prompt'] = self._build_custom_prompt(context, custom_query)
            else:
                context['prompt'] = self._build_preset_prompt(context, query_type)
            
            # Add analysis instructions
            context['instructions'] = self._get_analysis_instructions(query_type, context.get('has_datasheet', False))
            
            self.logger.info(f"Built context for {query_type} analysis")
            return context
            
        except Exception as e:
            self.logger.error(f"Error building analysis context: {e}")
            raise
    
    def add_schematic_context(self, context: Dict[str, Any], schematic_path: str) -> None:
        """Add schematic-specific context
        
        Args:
            context: Context dictionary to update
            schematic_path: Path to schematic image
        """
        context['schematic'] = {
            'path': schematic_path,
            'filename': os.path.basename(schematic_path),
            'analysis_hints': [
                "Look for component designators (R1, C1, U1, etc.)",
                "Check power supply connections (VCC, GND, etc.)",
                "Identify pin numbers and connections",
                "Note any test points or connectors",
                "Check for proper grounding and shielding"
            ]
        }
    
    def add_datasheet_context(self, context: Dict[str, Any], datasheet_data: Dict[str, Any]) -> None:
        """Add datasheet-specific context
        
        Args:
            context: Context dictionary to update
            datasheet_data: Parsed datasheet information
        """
        # Safely extract key information
        context['datasheet'] = {
            'component_name': datasheet_data.get('component_name', 'Unknown Component'),
            'has_pin_config': bool(datasheet_data.get('pin_config')),
            'has_electrical_specs': bool(datasheet_data.get('electrical_specs')),
            'has_recommended_circuits': bool(datasheet_data.get('recommended_circuits')),
            'summary': self._create_datasheet_summary(datasheet_data)
        }
        
        # Add specific sections if available
        pin_config = datasheet_data.get('pin_config')
        if pin_config:
            context['datasheet']['pin_configuration'] = self._format_pin_config(pin_config)
        
        electrical_specs = datasheet_data.get('electrical_specs')
        if electrical_specs:
            context['datasheet']['key_specifications'] = self._format_electrical_specs(electrical_specs)
        
        recommended_circuits = datasheet_data.get('recommended_circuits')
        if recommended_circuits:
            context['datasheet']['design_guidelines'] = self._format_recommended_circuits(recommended_circuits)
    
    def _create_datasheet_summary(self, datasheet_data: Dict[str, Any]) -> str:
        """Create a concise summary of datasheet information
        
        Args:
            datasheet_data: Parsed datasheet data
            
        Returns:
            str: Summary text
        """
        summary_parts = []
        
        # Component name
        component_name = datasheet_data.get('component_name')
        if component_name and component_name != 'Unknown':
            summary_parts.append(f"Component: {component_name}")
        
        # Key features
        features = datasheet_data.get('features', [])
        if features:
            if isinstance(features, list) and len(features) > 0:
                summary_parts.append(f"Features: {', '.join(features[:3])}")
            elif isinstance(features, str):
                summary_parts.append(f"Features: {features[:100]}")
        
        # Operating conditions
        operating_conditions = datasheet_data.get('operating_conditions')
        if operating_conditions:
            summary_parts.append("Has operating conditions specifications")
        
        # Package information
        package_info = datasheet_data.get('package_info')
        if package_info and package_info != 'Unknown' and package_info != 'Package information not found':
            summary_parts.append(f"Package: {package_info}")
        
        return " | ".join(summary_parts) if summary_parts else "Limited datasheet information available"
    
    def _format_pin_config(self, pin_config: Any) -> str:
        """Format pin configuration for context
        
        Args:
            pin_config: Pin configuration data
            
        Returns:
            str: Formatted pin configuration
        """
        if isinstance(pin_config, str):
            return pin_config[:1000]  # Limit length
        elif isinstance(pin_config, list):
            # Format as numbered list
            formatted = []
            for i, pin in enumerate(pin_config[:20], 1):  # Limit to first 20 pins
                if isinstance(pin, dict):
                    pin_str = f"Pin {pin.get('number', i)}: {pin.get('name', 'Unknown')} - {pin.get('function', 'N/A')}"
                else:
                    pin_str = f"Pin {i}: {str(pin)}"
                formatted.append(pin_str)
            return "\n".join(formatted)
        elif isinstance(pin_config, dict):
            # Format key-value pairs
            formatted = []
            for pin, desc in list(pin_config.items())[:20]:
                formatted.append(f"{pin}: {desc}")
            return "\n".join(formatted)
        else:
            return str(pin_config)[:1000]
    
    def _format_electrical_specs(self, specs: Any) -> str:
        """Format electrical specifications for context
        
        Args:
            specs: Electrical specifications data
            
        Returns:
            str: Formatted specifications
        """
        if isinstance(specs, str):
            return specs[:1000]
        elif isinstance(specs, dict):
            formatted = []
            priority_keys = ['voltage', 'current', 'power', 'frequency', 'temperature']
            
            # Add priority specs first
            for key in priority_keys:
                for spec_key, value in specs.items():
                    if key in spec_key.lower():
                        formatted.append(f"{spec_key}: {value}")
            
            # Add remaining specs
            for key, value in specs.items():
                if not any(pk in key.lower() for pk in priority_keys):
                    if len(formatted) < 15:  # Limit number of specs
                        formatted.append(f"{key}: {value}")
            
            return "\n".join(formatted)
        else:
            return str(specs)[:1000]
    
    def _format_recommended_circuits(self, circuits: Any) -> str:
        """Format recommended circuits information
        
        Args:
            circuits: Recommended circuits data
            
        Returns:
            str: Formatted circuit recommendations
        """
        if isinstance(circuits, str):
            return circuits[:1000]
        elif isinstance(circuits, list):
            formatted = []
            for i, circuit in enumerate(circuits[:5], 1):  # Limit to 5 circuits
                if isinstance(circuit, dict):
                    circuit_str = f"{i}. {circuit.get('name', 'Circuit')}: {circuit.get('description', 'N/A')}"
                else:
                    circuit_str = f"{i}. {str(circuit)}"
                formatted.append(circuit_str)
            return "\n".join(formatted)
        else:
            return str(circuits)[:1000]
    
    def _build_preset_prompt(self, context: Dict[str, Any], query_type: str) -> str:
        """Build prompt for preset analysis type
        
        Args:
            context: Analysis context
            query_type: Type of preset analysis
            
        Returns:
            str: Complete prompt
        """
        # Get base template
        template = PROMPT_TEMPLATES.get(query_type, PROMPT_TEMPLATES.get("Custom Query", "Please analyze this schematic."))
        
        # Build comprehensive prompt
        prompt_parts = [
            "You are analyzing an electronic schematic with the following context:",
            ""
        ]
        
        # Add datasheet context if available
        if context.get('has_datasheet'):
            datasheet = context.get('datasheet', {})
            prompt_parts.extend([
                "DATASHEET INFORMATION:",
                f"Component: {datasheet.get('component_name', 'Unknown')}",
                f"Summary: {datasheet.get('summary', 'No summary available')}",
                ""
            ])
            
            if datasheet.get('pin_configuration'):
                prompt_parts.extend([
                    "PIN CONFIGURATION:",
                    datasheet['pin_configuration'][:500] + ("..." if len(datasheet['pin_configuration']) > 500 else ""),
                    ""
                ])
            
            if datasheet.get('key_specifications'):
                prompt_parts.extend([
                    "KEY SPECIFICATIONS:",
                    datasheet['key_specifications'][:500] + ("..." if len(datasheet['key_specifications']) > 500 else ""),
                    ""
                ])
        
        # Add analysis request
        prompt_parts.extend([
            "ANALYSIS REQUEST:",
            template,
            "",
            "Please analyze the schematic image and provide specific, actionable feedback."
        ])
        
        if context.get('has_datasheet'):
            prompt_parts.append("Reference the datasheet information where applicable.")
        
        return "\n".join(prompt_parts)
    
    def _build_custom_prompt(self, context: Dict[str, Any], custom_query: str) -> str:
        """Build prompt for custom query
        
        Args:
            context: Analysis context
            custom_query: User's custom query
            
        Returns:
            str: Complete prompt
        """
        if not custom_query:
            custom_query = "Please analyze this schematic for any issues or recommendations."
        
        prompt_parts = [
            "You are analyzing an electronic schematic. "
        ]
        
        # Add datasheet context if available
        if context.get('has_datasheet'):
            datasheet = context.get('datasheet', {})
            component_name = datasheet.get('component_name', 'Unknown Component')
            prompt_parts.append(f"The schematic is for a {component_name}. ")
            prompt_parts.append("I have provided relevant datasheet information below for reference. ")
        
        prompt_parts.extend([
            "\n\nUSER QUERY:",
            custom_query,
            ""
        ])
        
        # Add datasheet details if available
        if context.get('has_datasheet'):
            datasheet = context.get('datasheet', {})
            prompt_parts.extend([
                "\nDATASHEET CONTEXT:",
                f"Component: {datasheet.get('component_name', 'Unknown')}",
                f"Summary: {datasheet.get('summary', 'No summary available')}"
            ])
            
            if datasheet.get('pin_configuration'):
                pin_config = datasheet['pin_configuration']
                prompt_parts.extend([
                    "\nPIN CONFIGURATION:",
                    pin_config[:500] + ("..." if len(pin_config) > 500 else "")
                ])
        
        prompt_parts.extend([
            "",
            "Please analyze the schematic image and answer the user's query. "
            "Provide specific details and reference the datasheet where applicable."
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_analysis_instructions(self, query_type: str, has_datasheet: bool) -> List[str]:
        """Get specific analysis instructions
        
        Args:
            query_type: Type of analysis
            has_datasheet: Whether datasheet is available
            
        Returns:
            list: Analysis instructions
        """
        instructions = [
            "Examine the schematic image carefully",
            "Identify all relevant components and connections",
            "Check for common design issues or errors"
        ]
        
        if has_datasheet:
            instructions.extend([
                "Cross-reference with datasheet specifications",
                "Verify pin assignments match datasheet",
                "Check component values against recommendations"
            ])
        
        # Add query-specific instructions
        if query_type == "Component Verification":
            instructions.extend([
                "Verify all component values are appropriate",
                "Check for missing pull-up/pull-down resistors",
                "Ensure proper decoupling capacitors"
            ])
        elif query_type == "Pin Configuration Check":
            instructions.extend([
                "Verify each pin connection",
                "Check for floating pins that should be tied",
                "Ensure power pins have proper connections"
            ])
        elif query_type == "Power Supply Analysis":
            instructions.extend([
                "Check voltage regulator configuration",
                "Verify decoupling capacitor placement",
                "Analyze power distribution network"
            ])
        
        return instructions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp
        
        Returns:
            str: ISO format timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def format_prompt(self, template: str, context_data: Dict[str, Any]) -> str:
        """Format a prompt template with context data
        
        Args:
            template: Prompt template with placeholders
            context_data: Data to fill placeholders
            
        Returns:
            str: Formatted prompt
        """
        try:
            # Simple string formatting
            return template.format(**context_data)
        except KeyError as e:
            self.logger.warning(f"Missing context data for prompt: {e}")
            return template
        except Exception as e:
            self.logger.error(f"Error formatting prompt: {e}")
            return template


def merge_contexts(contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple contexts into one
    
    Args:
        contexts: List of context dictionaries
        
    Returns:
        dict: Merged context
    """
    merged = {}
    
    for context in contexts:
        for key, value in context.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # Merge dictionaries
                merged[key].update(value)
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Extend lists
                merged[key].extend(value)
            else:
                # Override with latest value
                merged[key] = value
    
    return merged


if __name__ == "__main__":
    # Test the context builder
    import logging
    logging.basicConfig(level=logging.INFO)
    
    builder = ContextBuilder()
    
    # Test with sample data
    test_datasheet = {
        'component_name': 'LM7805',
        'pin_config': {
            'Pin 1': 'Input (VIN)',
            'Pin 2': 'Ground (GND)',
            'Pin 3': 'Output (VOUT)'
        },
        'electrical_specs': {
            'Input Voltage': '7V to 35V',
            'Output Voltage': '5V ±4%',
            'Output Current': '1A max'
        }
    }
    
    # Build context
    context = builder.build_analysis_context(
        schematic_path="test_schematic.png",
        datasheet_data=test_datasheet,
        query_type="Component Verification"
    )
    
    print("Built Context:")
    print(f"Query Type: {context['query_type']}")
    print(f"Has Datasheet: {context['has_datasheet']}")
    print(f"\nPrompt Preview (first 500 chars):")
    print(context['prompt'][:500] + "...")
    print(f"\nInstructions: {len(context['instructions'])} items")