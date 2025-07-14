"""
Ollama API client for multi-modal analysis
"""

import requests
import json
import base64
import logging
from pathlib import Path
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url=None):
        """Initialize Ollama client
        
        Args:
            base_url: Override default Ollama URL from config
        """
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.tags_endpoint = f"{self.base_url}/api/tags"
        
        # Check connection on initialization
        self.is_connected = self.check_connection()
        
        self.logger.info(f"Ollama client initialized - Connected: {self.is_connected}")
    
    def check_connection(self):
        """Verify Ollama is running and model is available
        
        Returns:
            bool: True if connected and model available
        """
        try:
            # Check if Ollama is running
            response = requests.get(self.tags_endpoint, timeout=5)
            
            if response.status_code != 200:
                self.logger.warning(f"Ollama API returned status: {response.status_code}")
                return False
            
            # Check if llava model is available
            data = response.json()
            models = data.get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            # Check for exact model or model family
            model_available = any(
                self.model in name or name.startswith(self.model.split(':')[0])
                for name in model_names
            )
            
            if not model_available:
                self.logger.warning(f"Model '{self.model}' not found. Available models: {model_names}")
                return False
            
            self.logger.info(f"Ollama connection verified. Model '{self.model}' is available")
            return True
            
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Ollama connection timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error checking Ollama connection: {e}")
            return False
    
    def encode_image(self, image_path):
        """Encode image to base64 for API
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Base64 encoded image
        """
        try:
            path = Path(image_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Read and encode image
            with open(path, 'rb') as f:
                image_data = f.read()
            
            # Encode to base64
            encoded = base64.b64encode(image_data).decode('utf-8')
            
            self.logger.debug(f"Encoded image: {path.name} ({len(encoded)} chars)")
            return encoded
            
        except Exception as e:
            self.logger.error(f"Error encoding image: {e}")
            raise
    
    def generate(self, prompt, images=None, model=None, stream=False, options=None):
        """Generate response from Ollama
        
        Args:
            prompt: Text prompt
            images: List of image paths or base64 encoded images
            model: Override default model
            stream: Whether to stream response
            options: Additional model options (temperature, etc.)
            
        Returns:
            dict: API response with generated text
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Ollama. Please check if Ollama is running.")
        
        try:
            # Prepare request data
            data = {
                'model': model or self.model,
                'prompt': prompt,
                'stream': stream
            }
            
            # Add images if provided
            if images:
                encoded_images = []
                
                for image in images:
                    if isinstance(image, str) and os.path.exists(image):
                        # It's a file path, encode it
                        encoded_images.append(self.encode_image(image))
                    elif isinstance(image, str):
                        # Assume it's already base64 encoded
                        encoded_images.append(image)
                    else:
                        self.logger.warning(f"Skipping invalid image: {image}")
                
                if encoded_images:
                    data['images'] = encoded_images
            
            # Add options if provided
            if options:
                data['options'] = options
            
            # Log request info
            self.logger.info(f"Generating with model '{data['model']}', prompt length: {len(prompt)}")
            if images:
                self.logger.info(f"Including {len(data.get('images', []))} images")
            
            # Make request
            start_time = time.time()
            response = requests.post(
                self.generate_endpoint,
                json=data,
                timeout=self.timeout,
                stream=stream
            )
            
            # Check response
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
            
            # Parse response
            if stream:
                # For streaming, return the response object
                return response
            else:
                # Parse JSON response
                result = response.json()
                
                # Log timing
                elapsed = time.time() - start_time
                self.logger.info(f"Generation completed in {elapsed:.2f}s")
                
                return result
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out after {self.timeout}s")
            raise Exception("Ollama request timed out. Try a shorter prompt or increase timeout.")
        except requests.exceptions.ConnectionError:
            self.logger.error("Lost connection to Ollama")
            self.is_connected = False
            raise Exception("Lost connection to Ollama. Please check if it's still running.")
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    def parse_response(self, response):
        """Extract generated text from API response
        
        Args:
            response: API response dict
            
        Returns:
            str: Generated text
        """
        try:
            if isinstance(response, dict):
                # Standard response format
                return response.get('response', '')
            elif isinstance(response, str):
                # Already a string
                return response
            else:
                # Try to convert to string
                return str(response)
                
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            return ""
    
    def stream_generate(self, prompt, images=None, callback=None):
        """Generate response with streaming
        
        Args:
            prompt: Text prompt
            images: List of image paths
            callback: Function to call with each chunk
            
        Returns:
            str: Complete generated text
        """
        try:
            # Get streaming response
            response = self.generate(prompt, images, stream=True)
            
            # Process stream
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        # Parse JSON chunk
                        chunk = json.loads(line.decode('utf-8'))
                        
                        # Extract text
                        text = chunk.get('response', '')
                        full_response += text
                        
                        # Call callback if provided
                        if callback and text:
                            callback(text)
                        
                        # Check if done
                        if chunk.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse chunk: {line}")
                        continue
            
            return full_response
            
        except Exception as e:
            self.logger.error(f"Error in streaming generation: {e}")
            raise
    
    def test_connection(self):
        """Test connection with a simple prompt
        
        Returns:
            bool: True if test successful
        """
        try:
            # Simple test prompt
            test_prompt = "Hello, please respond with 'OK' if you can read this."
            
            response = self.generate(test_prompt, options={'temperature': 0})
            text = self.parse_response(response)
            
            success = bool(text and len(text) > 0)
            
            if success:
                self.logger.info("Ollama connection test successful")
            else:
                self.logger.warning("Ollama test returned empty response")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ollama connection test failed: {e}")
            return False


def verify_ollama_status():
    """Standalone function to verify Ollama status
    
    Returns:
        dict: Status information
    """
    try:
        client = OllamaClient()
        
        status = {
            'running': client.is_connected,
            'url': client.base_url,
            'model': client.model,
            'model_available': False,
            'test_passed': False
        }
        
        if client.is_connected:
            # Get available models
            response = requests.get(client.tags_endpoint, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                status['available_models'] = models
                status['model_available'] = any(client.model in m for m in models)
            
            # Run test
            status['test_passed'] = client.test_connection()
        
        return status
        
    except Exception as e:
        return {
            'running': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Ollama client...")
    status = verify_ollama_status()
    
    print("\nOllama Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")