from PIL import Image, ImageDraw, ImageFont
import os
import logging
import base64
import io
from typing import Dict, List, Any, Optional
import random

# Configure logging
logger = logging.getLogger(__name__)

class MockupCreator:
    """AI-powered mockup creation system using Pillow"""
    
    def __init__(self):
        """Initialize the mockup creator"""
        self.default_font_size = 24
        self.default_logo_size = (100, 100)
        self.supported_formats = ['PNG', 'JPEG', 'JPG']
        
    async def create_mockup(self, product_data: Dict[str, Any], customer_data: Dict[str, Any], 
                          logo_placement: str, color_scheme: str, custom_text: Optional[str] = None, 
                          company_name: str = "") -> Dict[str, Any]:
        """
        Create branded mockups for a product
        
        Args:
            product_data: Dictionary containing product information
            customer_data: Dictionary containing customer information
            logo_placement: Preferred logo placement
            color_scheme: Color scheme preference
            custom_text: Optional custom text to add
            company_name: Company name for branding
            
        Returns:
            Dictionary with mockup images and variations
        """
        try:
            # Create base mockup
            base_mockup = await self._create_base_mockup(product_data, customer_data)
            
            # Apply branding
            branded_mockup = await self._apply_branding(
                base_mockup, company_name, logo_placement, color_scheme, custom_text
            )
            
            # Generate variations
            variations = await self._generate_variations(branded_mockup, product_data, customer_data)
            
            # Encode images to base64
            mockup_images = [self._encode_image_to_base64(branded_mockup)]
            variation_images = [self._encode_image_to_base64(var) for var in variations]
            
            return {
                "mockup_images": mockup_images + variation_images,
                "variations": [
                    {
                        "type": "color_variation",
                        "description": f"Mockup with {color_scheme} color scheme"
                    },
                    {
                        "type": "logo_placement",
                        "description": f"Mockup with logo on {logo_placement}"
                    },
                    {
                        "type": "text_overlay",
                        "description": "Mockup with custom text overlay"
                    }
                ],
                "customization_applied": {
                    "company_name": company_name,
                    "logo_placement": logo_placement,
                    "color_scheme": color_scheme,
                    "custom_text": custom_text,
                    "product_name": product_data.get("name", ""),
                    "product_category": product_data.get("category", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating mockup: {e}")
            return self._get_fallback_mockup(product_data, customer_data, company_name)
    
    async def _create_base_mockup(self, product_data: Dict[str, Any], customer_data: Dict[str, Any]) -> Image.Image:
        """Create a base mockup image for the product"""
        try:
            # Get product dimensions based on category
            dimensions = self._get_product_dimensions(product_data.get("category", ""))
            
            # Create base image
            base_image = Image.new('RGB', dimensions, self._get_background_color(product_data))
            
            # Add product shape/outline
            base_image = self._add_product_shape(base_image, product_data)
            
            return base_image
            
        except Exception as e:
            logger.error(f"Error creating base mockup: {e}")
            # Return a simple placeholder
            return Image.new('RGB', (400, 300), (240, 240, 240))
    
    def _get_product_dimensions(self, category: str) -> tuple:
        """Get appropriate dimensions for different product categories"""
        dimensions_map = {
            "Office Supplies": (400, 300),
            "Lifestyle": (350, 250),
            "Business Accessories": (450, 350),
            "Apparel": (300, 400),
            "Writing Instruments": (200, 150),
            "Safety & PPE": (400, 300),
            "Technology": (350, 250),
            "Kitchen & Dining": (300, 200),
            "Office Organization": (400, 300),
            "Outdoor & Recreation": (450, 350),
            "Health & Wellness": (400, 300),
            "Business Tools": (450, 350),
            "Seasonal": (400, 300),
            "Educational": (350, 250),
            "Premium Gifts": (500, 400)
        }
        
        return dimensions_map.get(category, (400, 300))
    
    def _get_background_color(self, product_data: Dict[str, Any]) -> tuple:
        """Get background color based on product category"""
        category = product_data.get("category", "").lower()
        
        color_map = {
            "office": (245, 245, 245),  # Light gray
            "lifestyle": (240, 248, 255),  # Alice blue
            "business": (255, 250, 240),  # Floral white
            "apparel": (255, 240, 245),  # Lavender blush
            "writing": (248, 248, 255),  # Ghost white
            "safety": (255, 245, 238),  # Seashell
            "technology": (240, 255, 240),  # Honeydew
            "kitchen": (255, 250, 250),  # Misty rose
            "outdoor": (245, 255, 250),  # Mint cream
            "health": (240, 255, 255),  # Azure
            "premium": (250, 235, 215),  # Antique white
            "seasonal": (255, 248, 220),  # Cornsilk
            "educational": (248, 255, 248)  # Honeydew
        }
        
        for key, color in color_map.items():
            if key in category:
                return color
        
        return (245, 245, 245)  # Default light gray
    
    def _add_product_shape(self, image: Image.Image, product_data: Dict[str, Any]) -> Image.Image:
        """Add product shape/outline to the mockup"""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Get product category for shape
            category = product_data.get("category", "").lower()
            
            # Define shape based on category
            if "notebook" in product_data.get("name", "").lower() or "office" in category:
                # Rectangle for notebooks, portfolios
                shape_coords = [width//4, height//4, 3*width//4, 3*height//4]
                draw.rectangle(shape_coords, outline=(100, 100, 100), width=3, fill=(255, 255, 255))
                
            elif "bottle" in product_data.get("name", "").lower() or "lifestyle" in category:
                # Oval for bottles, mugs
                shape_coords = [width//3, height//4, 2*width//3, 3*height//4]
                draw.ellipse(shape_coords, outline=(100, 100, 100), width=3, fill=(255, 255, 255))
                
            elif "shirt" in product_data.get("name", "").lower() or "apparel" in category:
                # T-shirt shape
                shape_coords = [width//4, height//3, 3*width//4, 4*height//5]
                draw.rectangle(shape_coords, outline=(100, 100, 100), width=3, fill=(255, 255, 255))
                
            elif "pen" in product_data.get("name", "").lower() or "writing" in category:
                # Long rectangle for pens
                shape_coords = [width//3, height//3, 2*width//3, 2*height//3]
                draw.rectangle(shape_coords, outline=(100, 100, 100), width=3, fill=(255, 255, 255))
                
            else:
                # Default rectangle
                shape_coords = [width//4, height//4, 3*width//4, 3*height//4]
                draw.rectangle(shape_coords, outline=(100, 100, 100), width=3, fill=(255, 255, 255))
            
            return image
            
        except Exception as e:
            logger.error(f"Error adding product shape: {e}")
            return image
    
    async def _apply_branding(self, image: Image.Image, company_name: str, logo_placement: str, 
                            color_scheme: str, custom_text: Optional[str] = None) -> Image.Image:
        """Apply branding elements to the mockup"""
        try:
            # Create a copy to work with
            branded_image = image.copy()
            draw = ImageDraw.Draw(branded_image)
            
            # Get color scheme
            colors = self._get_color_scheme(color_scheme)
            
            # Add company name
            if company_name:
                self._add_company_name(branded_image, company_name, logo_placement, colors)
            
            # Add custom text
            if custom_text:
                self._add_custom_text(branded_image, custom_text, colors)
            
            # Add logo placeholder
            self._add_logo_placeholder(branded_image, logo_placement, colors)
            
            return branded_image
            
        except Exception as e:
            logger.error(f"Error applying branding: {e}")
            return image
    
    def _get_color_scheme(self, color_scheme: str) -> Dict[str, tuple]:
        """Get color scheme based on preference"""
        color_schemes = {
            "blue": {"primary": (0, 102, 204), "secondary": (51, 153, 255), "accent": (0, 51, 102)},
            "green": {"primary": (0, 128, 0), "secondary": (34, 139, 34), "accent": (0, 100, 0)},
            "red": {"primary": (204, 0, 0), "secondary": (255, 51, 51), "accent": (153, 0, 0)},
            "purple": {"primary": (128, 0, 128), "secondary": (147, 112, 219), "accent": (75, 0, 130)},
            "orange": {"primary": (255, 140, 0), "secondary": (255, 165, 0), "accent": (255, 69, 0)},
            "gray": {"primary": (128, 128, 128), "secondary": (169, 169, 169), "accent": (105, 105, 105)},
            "black": {"primary": (0, 0, 0), "secondary": (64, 64, 64), "accent": (32, 32, 32)},
            "white": {"primary": (255, 255, 255), "secondary": (245, 245, 245), "accent": (220, 220, 220)}
        }
        
        return color_schemes.get(color_scheme.lower(), color_schemes["blue"])
    
    def _add_company_name(self, image: Image.Image, company_name: str, logo_placement: str, colors: Dict[str, tuple]):
        """Add company name to the mockup"""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", self.default_font_size)
            except:
                font = ImageFont.load_default()
            
            # Position based on logo placement
            if logo_placement.lower() in ["front cover", "center front"]:
                position = (width//2, height//3)
                anchor = "mm"
            elif logo_placement.lower() in ["side panel", "left chest"]:
                position = (width//4, height//2)
                anchor = "mm"
            elif logo_placement.lower() in ["back", "back panel"]:
                position = (width//2, 2*height//3)
                anchor = "mm"
            else:
                position = (width//2, height//2)
                anchor = "mm"
            
            # Draw company name
            draw.text(position, company_name, fill=colors["primary"], font=font, anchor=anchor)
            
        except Exception as e:
            logger.error(f"Error adding company name: {e}")
    
    def _add_custom_text(self, image: Image.Image, custom_text: str, colors: Dict[str, tuple]):
        """Add custom text to the mockup"""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", self.default_font_size - 4)
            except:
                font = ImageFont.load_default()
            
            # Position custom text below company name
            position = (width//2, 3*height//4)
            
            # Draw custom text
            draw.text(position, custom_text, fill=colors["secondary"], font=font, anchor="mm")
            
        except Exception as e:
            logger.error(f"Error adding custom text: {e}")
    
    def _add_logo_placeholder(self, image: Image.Image, logo_placement: str, colors: Dict[str, tuple]):
        """Add a logo placeholder to the mockup"""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Create a simple logo placeholder (circle with "LOGO" text)
            if logo_placement.lower() in ["front cover", "center front"]:
                center = (width//2, height//4)
            elif logo_placement.lower() in ["side panel", "left chest"]:
                center = (width//4, height//3)
            elif logo_placement.lower() in ["back", "back panel"]:
                center = (width//2, height//4)
            else:
                center = (width//2, height//3)
            
            # Draw logo circle
            logo_size = 40
            logo_coords = [
                center[0] - logo_size//2,
                center[1] - logo_size//2,
                center[0] + logo_size//2,
                center[1] + logo_size//2
            ]
            
            draw.ellipse(logo_coords, fill=colors["primary"], outline=colors["accent"], width=2)
            
            # Add "LOGO" text
            try:
                font = ImageFont.truetype("arial.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            draw.text(center, "LOGO", fill=colors["secondary"], font=font, anchor="mm")
            
        except Exception as e:
            logger.error(f"Error adding logo placeholder: {e}")
    
    async def _generate_variations(self, base_mockup: Image.Image, product_data: Dict[str, Any], 
                                 customer_data: Dict[str, Any]) -> List[Image.Image]:
        """Generate different variations of the mockup"""
        try:
            variations = []
            
            # Color variations
            color_variations = ["blue", "green", "red", "purple"]
            for color in color_variations[:2]:  # Limit to 2 color variations
                variation = base_mockup.copy()
                colors = self._get_color_scheme(color)
                company_name = customer_data.get("company", {}).get("name", "Company")
                
                # Reapply branding with different colors
                variation = await self._apply_branding(variation, company_name, "center front", color)
                variations.append(variation)
            
            # Logo placement variations
            placements = ["front cover", "side panel", "back"]
            for placement in placements[:2]:  # Limit to 2 placement variations
                variation = base_mockup.copy()
                company_name = customer_data.get("company", {}).get("name", "Company")
                
                # Reapply branding with different placement
                variation = await self._apply_branding(variation, company_name, placement, "blue")
                variations.append(variation)
            
            return variations
            
        except Exception as e:
            logger.error(f"Error generating variations: {e}")
            return []
    
    def _encode_image_to_base64(self, image: Image.Image) -> str:
        """Encode image to base64 string"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Encode to base64
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
            
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            return ""
    
    def _get_fallback_mockup(self, product_data: Dict[str, Any], customer_data: Dict[str, Any], 
                           company_name: str) -> Dict[str, Any]:
        """Provide fallback mockup when creation fails"""
        try:
            # Create a simple fallback mockup
            width, height = self._get_product_dimensions(product_data.get("category", ""))
            fallback_image = Image.new('RGB', (width, height), (240, 240, 240))
            
            # Add basic text
            draw = ImageDraw.Draw(fallback_image)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Add product name
            product_name = product_data.get("name", "Product")
            draw.text((width//2, height//3), product_name, fill=(100, 100, 100), font=font, anchor="mm")
            
            # Add company name
            if company_name:
                draw.text((width//2, 2*height//3), company_name, fill=(150, 150, 150), font=font, anchor="mm")
            
            # Encode to base64
            mockup_base64 = self._encode_image_to_base64(fallback_image)
            
            return {
                "mockup_images": [mockup_base64],
                "variations": [
                    {
                        "type": "fallback",
                        "description": "Basic mockup with product and company name"
                    }
                ],
                "customization_applied": {
                    "company_name": company_name,
                    "logo_placement": "center",
                    "color_scheme": "gray",
                    "custom_text": None,
                    "product_name": product_data.get("name", ""),
                    "product_category": product_data.get("category", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating fallback mockup: {e}")
            return {
                "mockup_images": [],
                "variations": [],
                "customization_applied": {}
            }
    
    async def create_product_preview(self, product_data: Dict[str, Any], customer_data: Dict[str, Any]) -> str:
        """Create a simple product preview image"""
        try:
            # Create a smaller preview image
            preview_image = Image.new('RGB', (200, 150), (245, 245, 245))
            draw = ImageDraw.Draw(preview_image)
            
            # Add product name
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            product_name = product_data.get("name", "Product")
            draw.text((100, 75), product_name, fill=(100, 100, 100), font=font, anchor="mm")
            
            return self._encode_image_to_base64(preview_image)
            
        except Exception as e:
            logger.error(f"Error creating product preview: {e}")
            return "" 