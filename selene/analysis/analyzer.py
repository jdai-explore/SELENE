"""
Main analysis orchestration for SELENE - Fixed version
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ollama_client import OllamaClient
from core.context_builder import ContextBuilder
from core.image_handler import ImageHandler
from analysis.prompts import get_prompt_template, format_finding, SEVERITY_LEVELS
import config


class SchematicAnalyzer:
    """Main analysis orchestration class"""
    
    def __init__(self, ollama_client: OllamaClient):
        """Initialize the analyzer
        
        Args:
            ollama_client: Initialized Ollama client
        """
        self.ollama_client = ollama_client
        self.context_builder = ContextBuilder()
        self.image_handler = ImageHandler()
        self.logger = logging.getLogger(__name__)
        
        # Analysis settings
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        self.logger.info("Schematic analyzer initialized")
    
    def analyze(self, schematic_path: str, datasheet_data: Dict[str, Any], 
                analysis_type: str, custom_query: Optional[str] = None) -> Dict[str, Any]:
        """Perform schematic analysis
        
        Args:
            schematic_path: Path to schematic image
            datasheet_data: Parsed datasheet information
            analysis_type: Type of analysis to perform
            custom_query: Custom query text (for custom analysis)
            
        Returns:
            dict: Analysis results
        """
        self.logger.info(f"Starting {analysis_type} analysis")
        start_time = time.time()
        
        try:
            # CRITICAL FIX: Ensure datasheet_data is always a dict
            if not isinstance(datasheet_data, dict):
                self.logger.warning(f"datasheet_data is not a dict (got {type(datasheet_data)}), creating empty dict")
                datasheet_data = {}
            
            # Validate inputs
            self.validate_analysis_inputs(schematic_path, analysis_type)
            
            # Prepare analysis request
            analysis_context = self.prepare_analysis_request(
                schematic_path, datasheet_data, analysis_type, custom_query
            )
            
            # Perform the analysis
            raw_response = self.perform_ollama_analysis(analysis_context)
            
            # Process and format the response
            results = self.process_response(raw_response, analysis_context)
            
            # Add timing and metadata
            elapsed_time = time.time() - start_time
            results['metadata']['analysis_time'] = elapsed_time
            results['metadata']['timestamp'] = datetime.now().isoformat()
            
            self.logger.info(f"Analysis completed in {elapsed_time:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return self.create_error_result(str(e), analysis_type)
    
    def validate_analysis_inputs(self, schematic_path: str, analysis_type: str):
        """Validate analysis inputs
        
        Args:
            schematic_path: Path to schematic image
            analysis_type: Type of analysis
        """
        # Check if schematic file exists
        if not os.path.exists(schematic_path):
            raise FileNotFoundError(f"Schematic file not found: {schematic_path}")
        
        # Check if analysis type is valid
        valid_types = ["Component Verification", "Pin Configuration Check", "Power Supply Analysis", 
                      "Design Compliance", "Missing Components", "Custom Query"]
        if analysis_type not in valid_types:
            raise ValueError(f"Invalid analysis type: {analysis_type}")
        
        # Check Ollama connection
        if not self.ollama_client.check_connection():
            raise ConnectionError("Ollama client is not connected")
    
    def prepare_analysis_request(self, schematic_path: str, datasheet_data: Dict[str, Any],
                               analysis_type: str, custom_query: Optional[str]) -> Dict[str, Any]:
        """Prepare the analysis request context
        
        Args:
            schematic_path: Path to schematic image
            datasheet_data: Parsed datasheet data
            analysis_type: Type of analysis
            custom_query: Custom query if applicable
            
        Returns:
            dict: Analysis context
        """
        self.logger.info("Preparing analysis context")
        
        # Ensure datasheet_data is a dict
        if not isinstance(datasheet_data, dict):
            datasheet_data = {}
        
        # Build context using context builder
        context = self.context_builder.build_analysis_context(
            schematic_path=schematic_path,
            datasheet_data=datasheet_data,
            query_type=analysis_type,
            custom_query=custom_query
        )
        
        # Prepare image for analysis
        image_package = self.image_handler.create_analysis_package(schematic_path)
        
        if not image_package['ready']:
            raise Exception(f"Failed to prepare image: {image_package.get('error', 'Unknown error')}")
        
        context['image_data'] = image_package
        
        return context
    
    def perform_ollama_analysis(self, analysis_context: Dict[str, Any]) -> str:
        """Perform the actual Ollama analysis with retries
        
        Args:
            analysis_context: Prepared analysis context
            
        Returns:
            str: Raw response from Ollama
        """
        prompt = analysis_context['prompt']
        image_data = analysis_context['image_data']['base64_image']
        
        # Ollama options for better analysis
        ollama_options = {
            'temperature': 0.1,  # Low temperature for consistent technical analysis
            'top_p': 0.9,
            'top_k': 40,
            'num_predict': 2048  # Allow longer responses
        }
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Ollama analysis attempt {attempt + 1}/{self.max_retries}")
                
                # Call Ollama with image
                response = self.ollama_client.generate(
                    prompt=prompt,
                    images=[image_data],
                    options=ollama_options
                )
                
                # Extract text from response
                response_text = self.ollama_client.parse_response(response)
                
                if response_text and len(response_text.strip()) > 10:
                    self.logger.info(f"Ollama analysis successful (attempt {attempt + 1})")
                    return response_text
                else:
                    raise Exception("Empty or too short response from Ollama")
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Ollama analysis attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
        
        # All attempts failed
        raise Exception(f"Ollama analysis failed after {self.max_retries} attempts: {last_error}")
    
    def process_response(self, raw_response: str, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and format the raw Ollama response
        
        Args:
            raw_response: Raw text response from Ollama
            analysis_context: Analysis context
            
        Returns:
            dict: Formatted analysis results
        """
        self.logger.info("Processing analysis response")
        
        # Extract key information
        findings = self.extract_findings(raw_response)
        recommendations = self.extract_recommendations(raw_response)
        issues = self.identify_issues(raw_response)
        
        # Create formatted results
        results = {
            'analysis_type': analysis_context['query_type'],
            'summary': self.create_summary(raw_response, findings, issues),
            'content': self.format_analysis_content(raw_response, findings, recommendations, issues),
            'findings': findings,
            'recommendations': recommendations,
            'issues': issues,
            'raw_response': raw_response,
            'metadata': {
                'schematic_file': analysis_context['schematic']['filename'],
                'has_datasheet': analysis_context['has_datasheet'],
                'datasheet_component': analysis_context.get('datasheet', {}).get('component_name', 'N/A'),
                'confidence': self.estimate_confidence(raw_response, analysis_context),
                'analysis_quality': self.assess_analysis_quality(raw_response)
            }
        }
        
        return results
    
    def extract_findings(self, response_text: str) -> List[Dict[str, str]]:
        """Extract structured findings from response"""
        findings = []
        
        # Look for common finding patterns
        finding_patterns = [
            r'(?i)issue[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)problem[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)concern[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)warning[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)error[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        import re
        
        for pattern in finding_patterns:
            matches = re.finditer(pattern, response_text, re.DOTALL)
            for match in matches:
                finding_text = match.group(1).strip()
                if finding_text and len(finding_text) > 10:
                    severity = self.determine_severity(finding_text)
                    findings.append({
                        'description': finding_text,
                        'severity': severity,
                        'type': 'issue'
                    })
        
        return findings[:10]  # Limit to 10 findings
    
    def extract_recommendations(self, response_text: str) -> List[str]:
        """Extract recommendations from response"""
        recommendations = []
        
        import re
        
        # Look for recommendation patterns
        rec_patterns = [
            r'(?i)recommend[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)suggest[s]?\s*:?\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)should\s+(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)consider\s+(.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in rec_patterns:
            matches = re.finditer(pattern, response_text, re.DOTALL)
            for match in matches:
                rec_text = match.group(1).strip()
                if rec_text and len(rec_text) > 10:
                    recommendations.append(rec_text)
        
        return recommendations[:8]  # Limit to 8 recommendations
    
    def identify_issues(self, response_text: str) -> List[Dict[str, str]]:
        """Identify and categorize issues from response"""
        issues = []
        
        # Define issue keywords and their severity
        issue_keywords = {
            'CRITICAL': ['missing', 'incorrect', 'wrong', 'error', 'fault', 'broken', 'failed'],
            'HIGH': ['warning', 'concern', 'problem', 'issue', 'mismatch', 'violation'],
            'MEDIUM': ['suboptimal', 'improvement', 'better', 'alternative', 'consider'],
            'LOW': ['minor', 'cosmetic', 'style', 'preference', 'optional']
        }
        
        import re
        
        # Split response into sentences
        sentences = re.split(r'[.!?]+', response_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            # Check for issue keywords
            for severity, keywords in issue_keywords.items():
                if any(keyword.lower() in sentence.lower() for keyword in keywords):
                    # Try to extract component reference
                    component_match = re.search(r'([RCLUQDJXYrclugdxj]\d+|pin\s*\d+)', sentence, re.IGNORECASE)
                    component = component_match.group(1) if component_match else 'General'
                    
                    issues.append({
                        'description': sentence,
                        'severity': severity,
                        'component': component,
                        'category': self.categorize_issue(sentence)
                    })
                    break  # Only assign one severity per sentence
        
        return issues[:8]  # Limit to 8 issues
    
    def determine_severity(self, finding_text: str) -> str:
        """Determine severity of a finding"""
        text_lower = finding_text.lower()
        
        # Critical issues
        if any(word in text_lower for word in ['missing', 'incorrect', 'wrong', 'error', 'fault', 'broken']):
            return 'CRITICAL'
        
        # High issues
        if any(word in text_lower for word in ['warning', 'concern', 'problem', 'issue', 'violation']):
            return 'HIGH'
        
        # Medium issues
        if any(word in text_lower for word in ['suboptimal', 'improvement', 'better', 'consider']):
            return 'MEDIUM'
        
        # Low issues
        if any(word in text_lower for word in ['minor', 'cosmetic', 'style', 'optional']):
            return 'LOW'
        
        # Default to INFO for positive findings
        return 'INFO'
    
    def categorize_issue(self, issue_text: str) -> str:
        """Categorize an issue by type"""
        text_lower = issue_text.lower()
        
        if any(word in text_lower for word in ['pin', 'connection', 'wire', 'trace']):
            return 'connectivity'
        elif any(word in text_lower for word in ['voltage', 'power', 'supply', 'vcc', 'gnd']):
            return 'power'
        elif any(word in text_lower for word in ['capacitor', 'resistor', 'inductor', 'component']):
            return 'components'
        elif any(word in text_lower for word in ['value', 'rating', 'specification']):
            return 'specifications'
        else:
            return 'general'
    
    def create_summary(self, response_text: str, findings: List[Dict], issues: List[Dict]) -> str:
        """Create a summary of the analysis"""
        # Count issues by severity
        severity_counts = {}
        for issue in issues:
            severity = issue['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Build summary
        summary_parts = []
        
        # Issue summary
        if severity_counts:
            total_issues = sum(severity_counts.values())
            summary_parts.append(f"Found {total_issues} potential issues")
            
            if severity_counts.get('CRITICAL', 0) > 0:
                summary_parts.append(f"{severity_counts['CRITICAL']} critical")
            if severity_counts.get('HIGH', 0) > 0:
                summary_parts.append(f"{severity_counts['HIGH']} high priority")
        else:
            summary_parts.append("No significant issues identified")
        
        # Add positive findings
        positive_findings = [f for f in findings if f.get('type') == 'verification']
        if positive_findings:
            summary_parts.append(f"{len(positive_findings)} items verified as correct")
        
        return ". ".join(summary_parts) + "."
    
    def format_analysis_content(self, raw_response: str, findings: List[Dict], 
                              recommendations: List[str], issues: List[Dict]) -> str:
        """Format the analysis content for display"""
        formatted_parts = []
        
        # Add structured findings if we have them
        if findings:
            formatted_parts.append("## Key Findings\n")
            for i, finding in enumerate(findings, 1):
                severity_icon = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠', 
                    'MEDIUM': '🟡',
                    'LOW': '🟢',
                    'INFO': 'ℹ️'
                }.get(finding['severity'], '•')
                
                formatted_parts.append(f"{i}. {severity_icon} {finding['description']}\n")
        
        # Add recommendations
        if recommendations:
            formatted_parts.append("\n## Recommendations\n")
            for i, rec in enumerate(recommendations, 1):
                formatted_parts.append(f"{i}. 💡 {rec}\n")
        
        # Add original response if no structured content
        if not findings and not recommendations:
            formatted_parts.append(raw_response)
        
        return "\n".join(formatted_parts)
    
    def estimate_confidence(self, response_text: str, analysis_context: Dict[str, Any]) -> str:
        """Estimate confidence level of the analysis"""
        confidence_score = 0.5  # Base score
        
        # Boost confidence if datasheet is available
        if analysis_context.get('has_datasheet'):
            confidence_score += 0.3
        
        # Boost confidence for longer, detailed responses
        if len(response_text) > 500:
            confidence_score += 0.1
        
        # Boost confidence if specific components/pins are mentioned
        import re
        component_refs = len(re.findall(r'[RCLUQDrclugd]\d+|pin\s*\d+', response_text, re.IGNORECASE))
        if component_refs > 3:
            confidence_score += 0.1
        
        # Clamp to valid range
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        if confidence_score >= 0.8:
            return "High"
        elif confidence_score >= 0.6:
            return "Medium"
        else:
            return "Low"
    
    def assess_analysis_quality(self, response_text: str) -> str:
        """Assess the quality of the analysis"""
        quality_score = 0
        
        # Check for technical depth
        technical_terms = ['voltage', 'current', 'resistance', 'capacitance', 'frequency', 'power']
        tech_count = sum(1 for term in technical_terms if term.lower() in response_text.lower())
        quality_score += min(tech_count, 5)
        
        # Check for specific references
        import re
        specific_refs = len(re.findall(r'\d+[kMGT]?[ΩFHVAWHz]|pin\s*\d+|[RCLUQDrclugd]\d+', response_text, re.IGNORECASE))
        quality_score += min(specific_refs, 10)
        
        # Check response length (indicates thoroughness)
        if len(response_text) > 300:
            quality_score += 2
        if len(response_text) > 600:
            quality_score += 2
        
        if quality_score >= 15:
            return "Excellent"
        elif quality_score >= 10:
            return "Good"
        elif quality_score >= 5:
            return "Fair"
        else:
            return "Basic"
    
    def create_error_result(self, error_message: str, analysis_type: str) -> Dict[str, Any]:
        """Create an error result when analysis fails"""
        return {
            'analysis_type': analysis_type,
            'summary': f"Analysis failed: {error_message}",
            'content': f"❌ **Analysis Error**\n\n{error_message}\n\nPlease check:\n"
                      "• Ollama is running and accessible\n"
                      "• The schematic image is valid\n"
                      "• Network connectivity is stable\n\n"
                      "Try running the analysis again or contact support if the problem persists.",
            'findings': [],
            'recommendations': ["Retry the analysis", "Check system requirements", "Verify file formats"],
            'issues': [{
                'description': f"Analysis failed: {error_message}",
                'severity': 'CRITICAL',
                'component': 'System',
                'category': 'error'
            }],
            'raw_response': f"Error: {error_message}",
            'metadata': {
                'schematic_file': 'Unknown',
                'has_datasheet': False,
                'datasheet_component': 'N/A',
                'confidence': 'N/A',
                'analysis_quality': 'Error',
                'error': True,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat()
            }
        }