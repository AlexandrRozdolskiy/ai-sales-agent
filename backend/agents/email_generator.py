import openai
import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class EmailGenerator:
    """AI-powered email generation system"""
    
    def __init__(self):
        """Initialize the email generator with OpenAI client"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4"
        
    async def generate_email(self, customer_data: Dict[str, Any], products: List[Dict[str, Any]], 
                           email_style: str, template: Optional[Dict[str, Any]] = None, 
                           custom_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a personalized email for a customer
        
        Args:
            customer_data: Dictionary containing customer information
            products: List of selected products
            email_style: Style of email (formal, casual, consultative, enthusiastic)
            template: Optional email template to use
            custom_message: Optional additional custom message
            
        Returns:
            Dictionary with generated email content
        """
        try:
            # Prepare customer and product data
            customer_context = self._prepare_customer_context(customer_data)
            product_context = self._prepare_product_context(products)
            
            # Create email generation prompt
            prompt = self._create_email_prompt(customer_context, product_context, email_style, template, custom_message)
            
            # Get AI-generated email
            email_response = await self._get_ai_email(prompt)
            
            # Parse and structure the response
            structured_email = self._parse_email_response(email_response, customer_data, products, email_style)
            
            return structured_email
            
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            # Return fallback email
            return self._get_fallback_email(customer_data, products, email_style, template)
    
    def _prepare_customer_context(self, customer_data: Dict[str, Any]) -> str:
        """Prepare customer data as context for email generation"""
        company = customer_data.get("company", {})
        contact = customer_data.get("contact", {})
        behavioral = customer_data.get("behavioral_data", {})
        engagement = customer_data.get("engagement_history", {})
        
        context = f"""
        Customer Information:
        - Company: {company.get('name', 'N/A')}
        - Industry: {company.get('industry', 'N/A')}
        - Company Size: {company.get('size', 'N/A')}
        - Location: {company.get('location', 'N/A')}
        - Website: {company.get('website', 'N/A')}
        
        Contact Person:
        - Name: {contact.get('name', 'N/A')}
        - Role: {contact.get('role', 'N/A')}
        - Email: {contact.get('email', 'N/A')}
        - Phone: {contact.get('phone', 'N/A')}
        
        Customer Needs:
        - Pain Points: {', '.join(behavioral.get('pain_points', []))}
        - Budget Range: {behavioral.get('budget_range', 'N/A')}
        - Decision Timeline: {behavioral.get('decision_timeline', 'N/A')}
        - Recent Activities: {', '.join(behavioral.get('recent_activities', []))}
        
        Relationship Context:
        - Last Contact: {engagement.get('last_contact', 'N/A')}
        - Interaction Frequency: {engagement.get('interaction_frequency', 'N/A')}
        - Preferred Communication: {engagement.get('preferred_communication', 'N/A')}
        - Previous Purchases: {', '.join(engagement.get('previous_purchases', []))}
        """
        
        return context
    
    def _prepare_product_context(self, products: List[Dict[str, Any]]) -> str:
        """Prepare product information for email generation"""
        if not products:
            return "No specific products selected"
        
        product_summaries = []
        for product in products:
            summary = f"""
            Product: {product.get('name', 'N/A')}
            Category: {product.get('category', 'N/A')}
            Price Range: {product.get('price_range', 'N/A')}
            Description: {product.get('description', 'N/A')}
            Benefits: {', '.join(product.get('benefits', []))}
            Target Use Cases: {', '.join(product.get('target_audience', {}).get('use_cases', []))}
            """
            product_summaries.append(summary)
        
        return "\n".join(product_summaries)
    
    def _create_email_prompt(self, customer_context: str, product_context: str, 
                           email_style: str, template: Optional[Dict[str, Any]] = None, 
                           custom_message: Optional[str] = None) -> str:
        """Create the AI email generation prompt"""
        
        # Style-specific instructions
        style_instructions = {
            "formal": "Use professional, business-like language with formal greetings and closings. Focus on facts and data.",
            "casual": "Use friendly, conversational tone with casual greetings. Be approachable and personable.",
            "consultative": "Use expert, advisory tone with questions and insights. Position as a trusted consultant.",
            "enthusiastic": "Use energetic, positive language with exclamation points. Show excitement and urgency."
        }
        
        style_guide = style_instructions.get(email_style, "Use professional but friendly tone.")
        
        # Template context
        template_context = ""
        if template:
            template_context = f"""
            Email Template to Follow:
            Subject: {template.get('subject_template', 'Custom Solutions for {company_name}')}
            Style: {template.get('style', 'professional')}
            Template Structure: {template.get('template', {})}
            """
        
        # Custom message context
        custom_context = ""
        if custom_message:
            custom_context = f"""
            Additional Custom Message to Include:
            {custom_message}
            """
        
        prompt = f"""
        You are an expert sales professional writing personalized emails for promotional products. Generate a compelling email based on the following information.

        Customer Profile:
        {customer_context}

        Product Information:
        {product_context}

        Email Requirements:
        - Style: {email_style}
        - Style Guide: {style_guide}
        {template_context}
        {custom_context}

        Please generate the email in the following JSON format:
        {{
            "subject": "Compelling email subject line",
            "body": "Complete email body with proper formatting",
            "personalization_score": 0.95,
            "call_to_action": "Clear next step or call to action",
            "key_points": ["List of key points covered in the email"]
        }}

        Guidelines:
        1. Personalize using customer's name, company, and specific details
        2. Address their pain points and recent activities
        3. Highlight relevant product benefits
        4. Include a clear call to action
        5. Match the specified email style
        6. Keep the email concise but comprehensive
        7. Use their preferred communication style
        8. Reference previous interactions if applicable

        Make the email feel personal and relevant to this specific customer.
        """
        
        return prompt
    
    async def _get_ai_email(self, prompt: str) -> str:
        """Get email from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert sales professional. Generate compelling, personalized emails in the requested JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting AI email: {e}")
            raise
    
    def _parse_email_response(self, ai_response: str, customer_data: Dict[str, Any], 
                            products: List[Dict[str, Any]], email_style: str) -> Dict[str, Any]:
        """Parse the AI response into structured email format"""
        try:
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                # Fallback parsing
                parsed = self._fallback_parsing(ai_response, customer_data, products)
            
            # Ensure all required fields are present
            structured_email = {
                "subject": parsed.get("subject", "Custom Solutions for Your Business"),
                "body": parsed.get("body", "Thank you for your interest in our products."),
                "personalization_score": parsed.get("personalization_score", 0.7),
                "call_to_action": parsed.get("call_to_action", "Please let me know if you have any questions."),
                "key_points": parsed.get("key_points", [])
            }
            
            return structured_email
            
        except Exception as e:
            logger.error(f"Error parsing email response: {e}")
            return self._get_fallback_email(customer_data, products, email_style)
    
    def _fallback_parsing(self, ai_response: str, customer_data: Dict[str, Any], 
                         products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        # Extract key information using simple text parsing
        lines = ai_response.split('\n')
        subject = "Custom Solutions for Your Business"
        body = ai_response
        call_to_action = "Please let me know if you have any questions."
        
        # Try to extract subject if it starts with "Subject:"
        for line in lines:
            if line.strip().startswith("Subject:"):
                subject = line.replace("Subject:", "").strip()
                break
        
        # Try to extract call to action
        for line in lines:
            if any(phrase in line.lower() for phrase in ["call", "contact", "schedule", "meeting", "discuss"]):
                call_to_action = line.strip()
                break
        
        return {
            "subject": subject,
            "body": body,
            "personalization_score": 0.6,
            "call_to_action": call_to_action,
            "key_points": ["Product recommendations", "Personalized solutions", "Next steps"]
        }
    
    def _get_fallback_email(self, customer_data: Dict[str, Any], products: List[Dict[str, Any]], 
                           email_style: str, template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provide fallback email when AI fails"""
        try:
            company = customer_data.get("company", {})
            contact = customer_data.get("contact", {})
            behavioral = customer_data.get("behavioral_data", {})
            
            # Generate basic email content
            company_name = company.get("name", "your company")
            contact_name = contact.get("name", "there")
            industry = company.get("industry", "business")
            pain_points = behavioral.get("pain_points", ["increasing brand visibility"])
            
            # Style-specific content
            if email_style == "formal":
                greeting = f"Dear {contact_name},"
                closing = "Best regards,"
                tone = "professional"
            elif email_style == "casual":
                greeting = f"Hi {contact_name},"
                closing = "Best,"
                tone = "friendly"
            elif email_style == "consultative":
                greeting = f"Hello {contact_name},"
                closing = "Looking forward to our discussion,"
                tone = "consultative"
            elif email_style == "enthusiastic":
                greeting = f"Hi {contact_name}!"
                closing = "Excited to work with you!"
                tone = "enthusiastic"
            else:
                greeting = f"Dear {contact_name},"
                closing = "Best regards,"
                tone = "professional"
            
            # Generate subject
            if template and template.get("subject_template"):
                subject = template["subject_template"].format(company_name=company_name)
            else:
                subject = f"Custom Solutions for {company_name}"
            
            # Generate body
            body_parts = [
                greeting,
                "",
                f"I hope this email finds you well. I recently came across {company_name} and was impressed by your work in the {industry} industry.",
                "",
                f"I understand you're looking to {', '.join(pain_points[:2])}. At [Your Company], we specialize in creating custom promotional solutions that help companies like yours achieve their goals.",
                ""
            ]
            
            if products:
                product_names = [p.get("name", "") for p in products[:2]]
                body_parts.extend([
                    f"I'd like to share some specific solutions that could benefit {company_name}, including our {', '.join(product_names)}.",
                    ""
                ])
            
            body_parts.extend([
                "Would you be available for a brief 15-minute call next week to discuss how we can help your team? I'd be happy to share some examples of our work with similar companies in your industry.",
                "",
                "I look forward to the opportunity to connect and learn more about your goals.",
                "",
                closing,
                "[Your Name]",
                "[Your Title]",
                "[Your Company]"
            ])
            
            body = "\n".join(body_parts)
            
            return {
                "subject": subject,
                "body": body,
                "personalization_score": 0.7,
                "call_to_action": "Schedule a 15-minute call to discuss solutions",
                "key_points": [
                    f"Personalized for {company_name}",
                    f"Addresses {industry} industry needs",
                    "Product recommendations included",
                    "Clear next steps"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in fallback email: {e}")
            return {
                "subject": "Custom Solutions for Your Business",
                "body": "Thank you for your interest in our products. I'd be happy to discuss how we can help your business.",
                "personalization_score": 0.5,
                "call_to_action": "Please contact us to learn more",
                "key_points": ["Product solutions", "Business benefits", "Next steps"]
            }
    
    async def generate_email_variations(self, customer_data: Dict[str, Any], products: List[Dict[str, Any]], 
                                      base_template: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate multiple email variations for A/B testing"""
        try:
            variations = []
            styles = ["formal", "casual", "consultative", "enthusiastic"]
            
            for style in styles:
                email = await self.generate_email(customer_data, products, style, base_template)
                email["style"] = style
                variations.append(email)
            
            return variations
            
        except Exception as e:
            logger.error(f"Error generating email variations: {e}")
            return []
    
    async def optimize_email_for_response(self, customer_data: Dict[str, Any], products: List[Dict[str, Any]], 
                                        email_style: str) -> Dict[str, Any]:
        """Optimize email for maximum response rate"""
        try:
            # Add response optimization to the prompt
            optimization_prompt = f"""
            Optimize the following email for maximum response rate:
            
            Customer: {customer_data.get('company', {}).get('name', 'N/A')}
            Industry: {customer_data.get('company', {}).get('industry', 'N/A')}
            Preferred Communication: {customer_data.get('engagement_history', {}).get('preferred_communication', 'N/A')}
            
            Focus on:
            1. Compelling subject line that creates curiosity
            2. Strong opening that grabs attention
            3. Clear value proposition
            4. Specific, actionable call to action
            5. Social proof or urgency elements
            6. Personalization that shows research
            """
            
            # Get optimized email
            optimized_response = await self._get_ai_email(optimization_prompt)
            return self._parse_email_response(optimized_response, customer_data, products, email_style)
            
        except Exception as e:
            logger.error(f"Error optimizing email: {e}")
            return await self.generate_email(customer_data, products, email_style) 