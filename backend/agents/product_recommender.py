import openai
import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ProductRecommender:
    """AI-powered product recommendation system"""
    
    def __init__(self):
        """Initialize the product recommender with OpenAI client"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4"
        
    async def recommend_products(self, customer_data: Dict[str, Any], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Recommend products for a customer based on their profile and needs
        
        Args:
            customer_data: Dictionary containing customer information
            products: List of available products
            
        Returns:
            List of recommended products with match scores
        """
        try:
            # Prepare customer and product data
            customer_context = self._prepare_customer_context(customer_data)
            product_context = self._prepare_product_context(products)
            
            # Create recommendation prompt
            prompt = self._create_recommendation_prompt(customer_context, product_context)
            
            # Get AI recommendations
            recommendation_response = await self._get_ai_recommendations(prompt)
            
            # Parse and structure the response
            structured_recommendations = self._parse_recommendation_response(
                recommendation_response, products, customer_data
            )
            
            return structured_recommendations
            
        except Exception as e:
            logger.error(f"Error recommending products: {e}")
            # Return fallback recommendations
            return self._get_fallback_recommendations(customer_data, products)
    
    def _prepare_customer_context(self, customer_data: Dict[str, Any]) -> str:
        """Prepare customer data as context for product recommendations"""
        company = customer_data.get("company", {})
        behavioral = customer_data.get("behavioral_data", {})
        engagement = customer_data.get("engagement_history", {})
        
        context = f"""
        Customer Profile:
        - Company: {company.get('name', 'N/A')}
        - Industry: {company.get('industry', 'N/A')}
        - Company Size: {company.get('size', 'N/A')}
        - Location: {company.get('location', 'N/A')}
        
        Customer Needs:
        - Pain Points: {', '.join(behavioral.get('pain_points', []))}
        - Budget Range: {behavioral.get('budget_range', 'N/A')}
        - Decision Timeline: {behavioral.get('decision_timeline', 'N/A')}
        - Recent Activities: {', '.join(behavioral.get('recent_activities', []))}
        
        Purchase History:
        - Previous Purchases: {', '.join(engagement.get('previous_purchases', []))}
        - Interaction Frequency: {engagement.get('interaction_frequency', 'N/A')}
        """
        
        return context
    
    def _prepare_product_context(self, products: List[Dict[str, Any]]) -> str:
        """Prepare product catalog as context"""
        product_summaries = []
        
        for product in products:
            target_audience = product.get("target_audience", {})
            customization = product.get("customization_options", {})
            
            summary = f"""
            Product ID: {product.get('id')}
            Name: {product.get('name')}
            Category: {product.get('category')}
            Price Range: {product.get('price_range')}
            Description: {product.get('description')}
            Target Industries: {', '.join(target_audience.get('industries', []))}
            Target Company Sizes: {', '.join(target_audience.get('company_size', []))}
            Use Cases: {', '.join(target_audience.get('use_cases', []))}
            Benefits: {', '.join(product.get('benefits', []))}
            Customization Options: {', '.join(customization.get('colors', [])[:3])}
            """
            product_summaries.append(summary)
        
        return "\n".join(product_summaries)
    
    def _create_recommendation_prompt(self, customer_context: str, product_context: str) -> str:
        """Create the AI recommendation prompt"""
        prompt = f"""
        You are an expert sales consultant specializing in promotional products. Analyze the customer profile and recommend the best products from the catalog.

        Customer Profile:
        {customer_context}

        Available Products:
        {product_context}

        Please provide product recommendations in the following JSON format:
        {{
            "recommendations": [
                {{
                    "product_id": 1,
                    "match_score": 0.95,
                    "reasoning": "Detailed explanation of why this product is a good match",
                    "customization_suggestions": ["Specific customization recommendations"]
                }}
            ]
        }}

        Consider the following factors:
        1. Industry alignment
        2. Company size appropriateness
        3. Budget compatibility
        4. Pain point solutions
        5. Previous purchase patterns
        6. Use case relevance

        Provide 5-8 recommendations with match scores between 0.0 and 1.0, where 1.0 is a perfect match.
        Focus on actionable insights and specific customization suggestions.
        """
        
        return prompt
    
    async def _get_ai_recommendations(self, prompt: str) -> str:
        """Get recommendations from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert sales consultant. Provide detailed product recommendations in the requested JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            raise
    
    def _parse_recommendation_response(self, ai_response: str, products: List[Dict[str, Any]], customer_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the AI response into structured recommendations"""
        try:
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                recommendations = parsed.get("recommendations", [])
            else:
                # Fallback parsing
                recommendations = self._fallback_parsing(ai_response, products)
            
            # Enrich recommendations with product details
            enriched_recommendations = []
            for rec in recommendations:
                product_id = rec.get("product_id")
                product = next((p for p in products if p["id"] == product_id), None)
                
                if product:
                    enriched_rec = {
                        "product_id": product_id,
                        "name": product.get("name", ""),
                        "category": product.get("category", ""),
                        "price_range": product.get("price_range", ""),
                        "match_score": rec.get("match_score", 0.5),
                        "reasoning": rec.get("reasoning", "Good match based on customer profile"),
                        "customization_suggestions": rec.get("customization_suggestions", [])
                    }
                    enriched_recommendations.append(enriched_rec)
            
            # Sort by match score
            enriched_recommendations.sort(key=lambda x: x["match_score"], reverse=True)
            
            return enriched_recommendations[:8]  # Return top 8 recommendations
            
        except Exception as e:
            logger.error(f"Error parsing recommendation response: {e}")
            return self._get_fallback_recommendations(customer_data, products)
    
    def _fallback_parsing(self, ai_response: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback parsing when JSON extraction fails"""
        recommendations = []
        
        # Simple keyword-based matching
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if 'product' in line.lower() and any(str(p["id"]) in line for p in products):
                # Extract product ID if present
                for product in products:
                    if str(product["id"]) in line:
                        recommendations.append({
                            "product_id": product["id"],
                            "match_score": 0.7,
                            "reasoning": "Recommended based on customer profile analysis",
                            "customization_suggestions": ["Standard customization options"]
                        })
                        break
        
        return recommendations
    
    def _get_fallback_recommendations(self, customer_data: Dict[str, Any], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Provide fallback recommendations when AI fails"""
        try:
            company = customer_data.get("company", {})
            behavioral = customer_data.get("behavioral_data", {})
            engagement = customer_data.get("engagement_history", {})
            
            # Simple rule-based recommendations
            recommendations = []
            
            # Get customer characteristics
            industry = company.get("industry", "").lower()
            size = company.get("size", "").lower()
            budget = behavioral.get("budget_range", "").lower()
            pain_points = [p.lower() for p in behavioral.get("pain_points", [])]
            previous_purchases = [p.lower() for p in engagement.get("previous_purchases", [])]
            
            for product in products:
                match_score = 0.5  # Base score
                reasoning = []
                customization_suggestions = []
                
                # Industry matching
                target_industries = [i.lower() for i in product.get("target_audience", {}).get("industries", [])]
                if industry in target_industries or any(ind in industry for ind in target_industries):
                    match_score += 0.2
                    reasoning.append("Industry alignment")
                
                # Company size matching
                target_sizes = [s.lower() for s in product.get("target_audience", {}).get("company_size", [])]
                if size in target_sizes or any(s in size for s in target_sizes):
                    match_score += 0.15
                    reasoning.append("Company size appropriate")
                
                # Budget matching
                price_range = product.get("price_range", "")
                if self._budget_matches(price_range, budget):
                    match_score += 0.15
                    reasoning.append("Budget compatible")
                
                # Pain point matching
                benefits = [b.lower() for b in product.get("benefits", [])]
                for pain_point in pain_points:
                    if any(benefit in pain_point or pain_point in benefit for benefit in benefits):
                        match_score += 0.1
                        reasoning.append(f"Addresses pain point: {pain_point}")
                
                # Previous purchase pattern matching
                for purchase in previous_purchases:
                    if any(word in purchase for word in product.get("name", "").lower().split()):
                        match_score += 0.1
                        reasoning.append("Similar to previous purchases")
                
                # Add customization suggestions
                customization_options = product.get("customization_options", {})
                if customization_options.get("colors"):
                    customization_suggestions.append(f"Choose from {len(customization_options['colors'])} color options")
                if customization_options.get("logo_placement"):
                    customization_suggestions.append(f"Logo placement: {', '.join(customization_options['logo_placement'][:2])}")
                
                if match_score > 0.6:  # Only include good matches
                    recommendations.append({
                        "product_id": product["id"],
                        "name": product["name"],
                        "category": product["category"],
                        "price_range": product["price_range"],
                        "match_score": min(match_score, 0.95),  # Cap at 0.95
                        "reasoning": "; ".join(reasoning) if reasoning else "Good match based on customer profile",
                        "customization_suggestions": customization_suggestions
                    })
            
            # Sort by match score and return top recommendations
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)
            return recommendations[:8]
            
        except Exception as e:
            logger.error(f"Error in fallback recommendations: {e}")
            # Return basic recommendations
            return [
                {
                    "product_id": products[0]["id"] if products else 1,
                    "name": products[0]["name"] if products else "Premium Executive Notebook",
                    "category": products[0]["category"] if products else "Office Supplies",
                    "price_range": products[0]["price_range"] if products else "$15-$25",
                    "match_score": 0.7,
                    "reasoning": "Recommended based on general business needs",
                    "customization_suggestions": ["Standard customization options available"]
                }
            ]
    
    def _budget_matches(self, price_range: str, budget_range: str) -> bool:
        """Check if product price range matches customer budget"""
        try:
            # Extract numeric values from price and budget ranges
            import re
            
            price_match = re.search(r'\$(\d+)-?\$?(\d+)?', price_range)
            budget_match = re.search(r'\$(\d+)-?\$?(\d+)?', budget_range)
            
            if price_match and budget_match:
                price_min = int(price_match.group(1))
                price_max = int(price_match.group(2)) if price_match.group(2) else price_min
                budget_min = int(budget_match.group(1))
                budget_max = int(budget_match.group(2)) if budget_match.group(2) else budget_min
                
                # Check if there's overlap
                return not (price_max < budget_min or price_min > budget_max)
            
            return True  # Default to True if parsing fails
            
        except Exception:
            return True
    
    async def get_personalized_suggestions(self, customer_data: Dict[str, Any], product: Dict[str, Any]) -> List[str]:
        """Get personalized customization suggestions for a specific product"""
        try:
            company = customer_data.get("company", {})
            behavioral = customer_data.get("behavioral_data", {})
            
            suggestions = []
            customization_options = product.get("customization_options", {})
            
            # Industry-specific suggestions
            industry = company.get("industry", "").lower()
            if "tech" in industry or "software" in industry:
                suggestions.append("Modern, minimalist design with tech-focused colors")
            elif "healthcare" in industry or "medical" in industry:
                suggestions.append("Professional, clean design with healthcare-appropriate colors")
            elif "construction" in industry or "manufacturing" in industry:
                suggestions.append("Durable materials with safety-focused branding")
            
            # Company size suggestions
            size = company.get("size", "").lower()
            if "startup" in size or "small" in size:
                suggestions.append("Cost-effective options with maximum brand visibility")
            elif "enterprise" in size or "large" in size:
                suggestions.append("Premium materials with sophisticated branding")
            
            # Budget-based suggestions
            budget = behavioral.get("budget_range", "").lower()
            if "high" in budget or "premium" in budget:
                suggestions.append("Premium customization options with luxury finishes")
            else:
                suggestions.append("Standard customization with good value options")
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            logger.error(f"Error getting personalized suggestions: {e}")
            return ["Standard customization options recommended"] 