import openai
import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class CustomerAnalyzer:
    """AI-powered customer analysis using OpenAI GPT-4"""
    
    def __init__(self):
        """Initialize the customer analyzer with OpenAI client"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4"
        
    async def analyze_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a customer using AI to extract insights, pain points, and opportunities
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Prepare customer data for analysis
            customer_context = self._prepare_customer_context(customer_data)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(customer_context)
            
            # Get AI analysis
            analysis_response = await self._get_ai_analysis(prompt)
            
            # Parse and structure the response
            structured_analysis = self._parse_analysis_response(analysis_response, customer_data)
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing customer: {e}")
            # Return fallback analysis
            return self._get_fallback_analysis(customer_data)
    
    def _prepare_customer_context(self, customer_data: Dict[str, Any]) -> str:
        """Prepare customer data as context for AI analysis"""
        company = customer_data.get("company", {})
        contact = customer_data.get("contact", {})
        behavioral = customer_data.get("behavioral_data", {})
        engagement = customer_data.get("engagement_history", {})
        
        context = f"""
        Company Information:
        - Name: {company.get('name', 'N/A')}
        - Industry: {company.get('industry', 'N/A')}
        - Size: {company.get('size', 'N/A')}
        - Location: {company.get('location', 'N/A')}
        - Website: {company.get('website', 'N/A')}
        
        Contact Information:
        - Name: {contact.get('name', 'N/A')}
        - Role: {contact.get('role', 'N/A')}
        - Email: {contact.get('email', 'N/A')}
        - Phone: {contact.get('phone', 'N/A')}
        
        Behavioral Data:
        - Recent Activities: {', '.join(behavioral.get('recent_activities', []))}
        - Pain Points: {', '.join(behavioral.get('pain_points', []))}
        - Budget Range: {behavioral.get('budget_range', 'N/A')}
        - Decision Timeline: {behavioral.get('decision_timeline', 'N/A')}
        
        Engagement History:
        - Last Contact: {engagement.get('last_contact', 'N/A')}
        - Interaction Frequency: {engagement.get('interaction_frequency', 'N/A')}
        - Preferred Communication: {engagement.get('preferred_communication', 'N/A')}
        - Previous Purchases: {', '.join(engagement.get('previous_purchases', []))}
        """
        
        return context
    
    def _create_analysis_prompt(self, customer_context: str) -> str:
        """Create the AI analysis prompt"""
        prompt = f"""
        You are an expert sales analyst specializing in B2B customer analysis. Analyze the following customer data and provide insights for a promotional products company.

        Customer Data:
        {customer_context}

        Please provide a comprehensive analysis in the following JSON format:
        {{
            "analysis": {{
                "company_profile": "Brief analysis of the company's profile and position in their industry",
                "decision_making_factors": "Key factors that influence their purchasing decisions",
                "budget_analysis": "Analysis of their budget range and spending patterns",
                "timeline_insights": "Insights about their decision timeline and urgency",
                "communication_preferences": "Analysis of their preferred communication methods",
                "previous_purchase_insights": "What their previous purchases reveal about their needs"
            }},
            "pain_points": [
                "List 3-5 specific pain points this customer is facing",
                "Focus on areas where promotional products could help"
            ],
            "opportunities": [
                "List 3-5 specific sales opportunities",
                "Include specific product categories or use cases"
            ],
            "confidence_score": 0.85
        }}

        Focus on actionable insights that would help a sales team understand how to approach this customer and what products to recommend.
        """
        
        return prompt
    
    async def _get_ai_analysis(self, prompt: str) -> str:
        """Get analysis from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert sales analyst. Provide detailed, actionable insights in the requested JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}")
            raise
    
    def _parse_analysis_response(self, ai_response: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the AI response into structured format"""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                # Fallback parsing
                parsed = self._fallback_parsing(ai_response)
            
            # Ensure all required fields are present
            structured_response = {
                "analysis": parsed.get("analysis", {}),
                "pain_points": parsed.get("pain_points", []),
                "opportunities": parsed.get("opportunities", []),
                "confidence_score": parsed.get("confidence_score", 0.7)
            }
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._get_fallback_analysis(customer_data)
    
    def _fallback_parsing(self, ai_response: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        # Extract key information using simple text parsing
        pain_points = []
        opportunities = []
        
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if 'pain point' in line.lower() or 'challenge' in line.lower():
                pain_points.append(line)
            elif 'opportunity' in line.lower() or 'potential' in line.lower():
                opportunities.append(line)
        
        return {
            "analysis": {
                "company_profile": "Analysis based on available data",
                "decision_making_factors": "Budget and timeline considerations",
                "budget_analysis": "Based on provided budget range",
                "timeline_insights": "Based on decision timeline",
                "communication_preferences": "Based on preferred communication method",
                "previous_purchase_insights": "Based on purchase history"
            },
            "pain_points": pain_points[:5] if pain_points else ["Need to increase brand visibility", "Looking for employee engagement solutions"],
            "opportunities": opportunities[:5] if opportunities else ["Custom promotional products", "Employee recognition items"],
            "confidence_score": 0.6
        }
    
    def _get_fallback_analysis(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback analysis when AI fails"""
        company = customer_data.get("company", {})
        behavioral = customer_data.get("behavioral_data", {})
        
        return {
            "analysis": {
                "company_profile": f"{company.get('name', 'Company')} operates in the {company.get('industry', 'business')} industry with {company.get('size', 'medium')} size team.",
                "decision_making_factors": "Budget considerations and timeline constraints are key factors.",
                "budget_analysis": f"Budget range: {behavioral.get('budget_range', 'Not specified')}",
                "timeline_insights": f"Decision timeline: {behavioral.get('decision_timeline', 'Not specified')}",
                "communication_preferences": "Email and phone communication preferred.",
                "previous_purchase_insights": "Previous purchases indicate interest in branded items."
            },
            "pain_points": behavioral.get("pain_points", ["Need to increase brand visibility", "Looking for employee engagement solutions"]),
            "opportunities": ["Custom promotional products", "Employee recognition items", "Brand awareness materials"],
            "confidence_score": 0.5
        }
    
    async def get_customer_segment(self, customer_data: Dict[str, Any]) -> str:
        """Determine customer segment based on analysis"""
        try:
            company = customer_data.get("company", {})
            behavioral = customer_data.get("behavioral_data", {})
            
            # Simple segmentation logic
            size = company.get("size", "")
            budget = behavioral.get("budget_range", "")
            
            if "500+" in size or "$25,000" in budget:
                return "Enterprise"
            elif "100-500" in size or "$15,000" in budget:
                return "Mid-Market"
            elif "50-100" in size or "$10,000" in budget:
                return "Small Business"
            else:
                return "Startup"
                
        except Exception as e:
            logger.error(f"Error determining customer segment: {e}")
            return "Small Business"
    
    async def get_urgency_score(self, customer_data: Dict[str, Any]) -> float:
        """Calculate urgency score for the customer"""
        try:
            behavioral = customer_data.get("behavioral_data", {})
            timeline = behavioral.get("decision_timeline", "")
            
            # Simple urgency scoring
            if "1 month" in timeline or "immediate" in timeline.lower():
                return 0.9
            elif "2-3 months" in timeline:
                return 0.7
            elif "3-4 months" in timeline:
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"Error calculating urgency score: {e}")
            return 0.5 