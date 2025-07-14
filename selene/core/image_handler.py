"""
Image processing and manipulation module
"""

import logging
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance
import base64
import io
import os
import sys
from typing import Optional, Tuple, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ImageHandler:
    """Handle image processing for schematic analysis"""
    
    # Maximum dimensions for Ollama (to prevent memory issues)
    MAX_OLLAMA_WIDTH = 1920
    MAX_OLLAMA_HEIGHT = 1080
    
    # Display thumbnail size
    THUMBNAIL_SIZE = (200, 150)
    
    def __init__(self):
        """Initialize image handler"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Image handler initialized")
    
    def load_image(self, image_path: str) -> Image.Image:
        """Load and validate image
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL.Image: Loaded image
        """
        path = Path(image_path)
        
        # Validate path
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Validate format
        if not self.validate_image_format(image_path):
            raise ValueError(f"Unsupported image format: {path.suffix}")
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > config.MAX_FILE_SIZE_MB:
            raise ValueError(f"Image file too large: {file_size_mb:.1f} MB (max: {config.MAX_FILE_SIZE_MB} MB)")
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary (for consistency)
            if image.mode not in ('RGB', 'L'):
                if image.mode == 'RGBA':
                    # Create white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert('RGB')
            
            self.logger.info(f"Loaded image: {path.name} ({image.width}x{image.height}, {image.mode})")
            return image
            
        except Exception as e:
            self.logger.error(f"Error loading image: {e}")
            raise Exception(f"Failed to load image: {e}")
    
    def validate_image_format(self, image_path: str) -> bool:
        """Check if image format is supported
        
        Args:
            image_path: Path to image file
            
        Returns:
            bool: True if format is supported
        """
        path = Path(image_path)
        return path.suffix.lower() in config.SUPPORTED_IMAGE_FORMATS
    
    def resize_for_display(self, image: Image.Image, size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """Create thumbnail for display
        
        Args:
            image: PIL Image
            size: Target size (width, height), defaults to THUMBNAIL_SIZE
            
        Returns:
            PIL.Image: Resized image
        """
        target_size = size or self.THUMBNAIL_SIZE
        
        try:
            # Create a copy to avoid modifying original
            thumbnail = image.copy()
            
            # Use high-quality downsampling
            thumbnail.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            self.logger.debug(f"Created thumbnail: {thumbnail.size}")
            return thumbnail
            
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {e}")
            raise
    
    def prepare_for_ollama(self, image: Image.Image) -> Image.Image:
        """Optimize image for Ollama analysis
        
        Args:
            image: PIL Image
            
        Returns:
            PIL.Image: Optimized image
        """
        try:
            # Check if resizing is needed
            if image.width > self.MAX_OLLAMA_WIDTH or image.height > self.MAX_OLLAMA_HEIGHT:
                # Calculate scaling factor
                scale = min(
                    self.MAX_OLLAMA_WIDTH / image.width,
                    self.MAX_OLLAMA_HEIGHT / image.height
                )
                
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                
                # Resize image
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(f"Resized image for Ollama: {new_width}x{new_height}")
            
            # Enhance image for better OCR/analysis
            image = self.enhance_for_analysis(image)
            
            return image
            
        except Exception as e:
            self.logger.error(f"Error preparing image for Ollama: {e}")
            raise
    
    def enhance_for_analysis(self, image: Image.Image) -> Image.Image:
        """Enhance image for better analysis
        
        Args:
            image: PIL Image
            
        Returns:
            PIL.Image: Enhanced image
        """
        try:
            # Auto-orient based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Enhance contrast slightly for schematics
            if image.mode == 'RGB':
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.1)  # Slight contrast boost
                
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.2)  # Slight sharpness boost
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Error enhancing image: {e}")
            return image  # Return original if enhancement fails
    
    def convert_to_base64(self, image: Image.Image, format: str = 'PNG') -> str:
        """Convert image to base64 string
        
        Args:
            image: PIL Image
            format: Image format for encoding
            
        Returns:
            str: Base64 encoded image
        """
        try:
            # Save image to bytes buffer
            buffer = io.BytesIO()
            
            # Use appropriate format and quality
            if format.upper() == 'JPEG':
                image.save(buffer, format=format, quality=85, optimize=True)
            else:
                image.save(buffer, format=format, optimize=True)
            
            # Get bytes and encode
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            encoded = base64.b64encode(image_bytes).decode('utf-8')
            
            self.logger.debug(f"Encoded image to base64: {len(encoded)} chars")
            return encoded
            
        except Exception as e:
            self.logger.error(f"Error encoding image to base64: {e}")
            raise
    
    def save_temp_image(self, image: Image.Image, prefix: str = "temp") -> str:
        """Save image to temporary file
        
        Args:
            image: PIL Image
            prefix: Filename prefix
            
        Returns:
            str: Path to saved file
        """
        try:
            # Create temp directory if needed
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate filename
            import time
            timestamp = int(time.time())
            filename = f"{prefix}_{timestamp}.png"
            filepath = temp_dir / filename
            
            # Save image
            image.save(filepath, 'PNG')
            
            self.logger.info(f"Saved temporary image: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving temporary image: {e}")
            raise
    
    def get_image_info(self, image_path: str) -> Dict[str, any]:
        """Get image information
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Image information
        """
        path = Path(image_path)
        
        info = {
            'path': str(path),
            'filename': path.name,
            'size_bytes': path.stat().st_size,
            'format': path.suffix.upper()[1:],  # Remove dot
        }
        
        try:
            with Image.open(image_path) as img:
                info.update({
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'dpi': img.info.get('dpi', (72, 72)),
                    'has_transparency': img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info
                })
                
                # Calculate megapixels
                info['megapixels'] = (img.width * img.height) / 1_000_000
                
        except Exception as e:
            self.logger.error(f"Error getting image info: {e}")
        
        return info
    
    def extract_schematic_regions(self, image: Image.Image) -> Dict[str, any]:
        """Extract regions of interest from schematic (placeholder for future enhancement)
        
        Args:
            image: PIL Image
            
        Returns:
            dict: Extracted regions information
        """
        # This is a placeholder for future computer vision enhancements
        # Could use OpenCV to detect:
        # - Component symbols
        # - Text regions
        # - Connection lines
        # - Power rails
        
        regions = {
            'full_image': {
                'bounds': (0, 0, image.width, image.height),
                'description': 'Complete schematic'
            }
        }
        
        return regions
    
    def create_analysis_package(self, image_path: str) -> Dict[str, any]:
        """Create a complete package for analysis
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Analysis package with image data and metadata
        """
        try:
            # Load image
            image = self.load_image(image_path)
            
            # Prepare for Ollama
            optimized = self.prepare_for_ollama(image)
            
            # Convert to base64
            base64_image = self.convert_to_base64(optimized)
            
            # Get image info
            info = self.get_image_info(image_path)
            
            # Create package
            package = {
                'original_path': image_path,
                'base64_image': base64_image,
                'metadata': info,
                'optimized_size': (optimized.width, optimized.height),
                'ready': True
            }
            
            return package
            
        except Exception as e:
            self.logger.error(f"Error creating analysis package: {e}")
            return {
                'original_path': image_path,
                'error': str(e),
                'ready': False
            }


def optimize_image_size(image: Image.Image, max_size_mb: float = 5.0) -> Image.Image:
    """Optimize image size while maintaining quality
    
    Args:
        image: PIL Image
        max_size_mb: Maximum size in megabytes
        
    Returns:
        PIL.Image: Optimized image
    """
    # Estimate current size
    temp_buffer = io.BytesIO()
    image.save(temp_buffer, format='PNG')
    current_size_mb = len(temp_buffer.getvalue()) / (1024 * 1024)
    
    if current_size_mb <= max_size_mb:
        return image
    
    # Calculate required scale
    scale = (max_size_mb / current_size_mb) ** 0.5
    new_width = int(image.width * scale)
    new_height = int(image.height * scale)
    
    # Resize image
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    # Test the image handler
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample image if provided
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        handler = ImageHandler()
        
        print(f"Testing image handler with: {image_path}")
        
        # Get info
        info = handler.get_image_info(image_path)
        print(f"\nImage Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Load and process
        image = handler.load_image(image_path)
        print(f"\nLoaded image: {image.size}")
        
        # Create thumbnail
        thumbnail = handler.resize_for_display(image)
        print(f"Thumbnail size: {thumbnail.size}")
        
        # Prepare for Ollama
        ollama_ready = handler.prepare_for_ollama(image)
        print(f"Ollama-ready size: {ollama_ready.size}")
        
        # Create analysis package
        package = handler.create_analysis_package(image_path)
        print(f"\nAnalysis package ready: {package['ready']}")
        if package['ready']:
            print(f"Base64 length: {len(package['base64_image'])} chars")
    else:
        print("Usage: python image_handler.py <image_file>")