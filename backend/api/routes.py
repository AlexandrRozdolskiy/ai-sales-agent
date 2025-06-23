from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import json
import os
import logging
from datetime import datetime

# Import models and agents
from backend.api.models import (
    CustomerAnalysisRequest, CustomerAnalysisResponse,
    ProductRecommendationRequest, ProductRecommendationResponse, ProductRecommendation,
    EmailGenerationRequest, EmailGenerationResponse,
    MockupCreationRequest, MockupCreationResponse,
    Customer, Product, EmailTemplate, HealthResponse
)
from backend.agents.customer_analyzer import CustomerAnalyzer
from backend.agents.product_recommender import ProductRecommender
from backend.agents.email_generator import EmailGenerator
from backend.agents.mockup_creator import MockupCreator

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize agents
customer_analyzer = CustomerAnalyzer()
product_recommender = ProductRecommender()
email_generator = EmailGenerator()
mockup_creator = MockupCreator()

# Load mock data
def load_mock_data():
    """Load mock data from JSON files"""
    try:
        # Load customers
        with open("backend/data/mock_customers.json", "r") as f:
            customers = json.load(f)
        
        # Load products
        with open("backend/data/product_catalog.json", "r") as f:
            products = json.load(f)
        
        # Load email templates
        with open("backend/data/email_templates.json", "r") as f:
            email_templates = json.load(f)
        
        return customers, products, email_templates
    except Exception as e:
        logger.error(f"Error loading mock data: {e}")
        return [], [], []

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="AI Sales Agent PoC",
        version="1.0.0"
    )

@router.get("/customers", response_model=List[Customer])
async def get_customers():
    """Get all available customers"""
    try:
        customers, _, _ = load_mock_data()
        return customers
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to load customers")

@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: int):
    """Get a specific customer by ID"""
    try:
        customers, _, _ = load_mock_data()
        customer = next((c for c in customers if c["id"] == customer_id), None)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load customer")

@router.get("/products", response_model=List[Product])
async def get_products():
    """Get all available products"""
    try:
        _, products, _ = load_mock_data()
        return products
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Failed to load products")

@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    """Get a specific product by ID"""
    try:
        _, products, _ = load_mock_data()
        product = next((p for p in products if p["id"] == product_id), None)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load product")

@router.post("/analyze-customer", response_model=CustomerAnalysisResponse)
async def analyze_customer(request: CustomerAnalysisRequest):
    """Analyze a customer using AI, with local cache"""
    try:
        customers, _, _ = load_mock_data()
        customer = next((c for c in customers if c["id"] == request.customer_id), None)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Caching logic
        cache_dir = "backend/cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"customer_{request.customer_id}_analysis.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached = json.load(f)
                return CustomerAnalysisResponse(**cached)
            except Exception as e:
                logger.warning(f"Failed to load cache for customer {request.customer_id}: {e}")
        
        # Perform AI analysis
        analysis_result = await customer_analyzer.analyze_customer(customer)
        response = CustomerAnalysisResponse(
            customer_id=request.customer_id,
            analysis=analysis_result["analysis"],
            pain_points=analysis_result["pain_points"],
            opportunities=analysis_result["opportunities"],
            confidence_score=analysis_result["confidence_score"]
        )
        # Save to cache
        try:
            with open(cache_path, "w") as f:
                json.dump(json.loads(response.json()), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache for customer {request.customer_id}: {e}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing customer {request.customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze customer")

@router.post("/recommend-products", response_model=ProductRecommendationResponse)
async def recommend_products(request: ProductRecommendationRequest):
    """Get AI-powered product recommendations for a customer"""
    try:
        customers, products, _ = load_mock_data()
        customer = next((c for c in customers if c["id"] == request.customer_id), None)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Caching logic
        cache_dir = "backend/cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"customer_{request.customer_id}_recommendations.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached = json.load(f)
                return ProductRecommendationResponse(**cached)
            except Exception as e:
                logger.warning(f"Failed to load recommendations cache for customer {request.customer_id}: {e}")

        # Get product recommendations
        recommendations = await product_recommender.recommend_products(customer, products)
        top_recommendation = max(recommendations, key=lambda x: x["match_score"])
        response = ProductRecommendationResponse(
            customer_id=request.customer_id,
            recommendations=recommendations,
            top_recommendation=top_recommendation
        )
        # Save to cache
        try:
            with open(cache_path, "w") as f:
                json.dump(json.loads(response.json()), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save recommendations cache for customer {request.customer_id}: {e}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recommending products for customer {request.customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to recommend products")

@router.post("/generate-email", response_model=EmailGenerationResponse)
async def generate_email(request: EmailGenerationRequest):
    """Generate a personalized email for a customer"""
    try:
        customers, products, email_templates = load_mock_data()
        customer = next((c for c in customers if c["id"] == request.customer_id), None)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Caching logic
        cache_dir = "backend/cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"customer_{request.customer_id}_email.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached = json.load(f)
                return EmailGenerationResponse(**cached)
            except Exception as e:
                logger.warning(f"Failed to load email cache for customer {request.customer_id}: {e}")

        # Get selected products
        selected_products = [p for p in products if p["id"] in request.product_ids]
        if not selected_products:
            raise HTTPException(status_code=400, detail="No valid products selected")

        # Get email template if specified
        template = None
        if request.template_id:
            template = next((t for t in email_templates if t["id"] == request.template_id), None)

        # Generate email
        email_result = await email_generator.generate_email(
            customer, selected_products, request.email_style, template, request.custom_message
        )
        response = EmailGenerationResponse(
            customer_id=request.customer_id,
            subject=email_result["subject"],
            body=email_result["body"],
            style=request.email_style,
            personalization_score=email_result["personalization_score"],
            call_to_action=email_result["call_to_action"]
        )
        # Save to cache
        try:
            with open(cache_path, "w") as f:
                json.dump(json.loads(response.json()), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save email cache for customer {request.customer_id}: {e}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email for customer {request.customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate email")

@router.post("/create-mockup", response_model=MockupCreationResponse)
async def create_mockup(request: MockupCreationRequest):
    """Create branded mockups for a product"""
    try:
        customers, products, _ = load_mock_data()
        customer = next((c for c in customers if c["id"] == request.customer_id), None)
        product = next((p for p in products if p["id"] == request.product_id), None)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Create mockup
        mockup_result = await mockup_creator.create_mockup(
            product, customer, request.logo_placement, request.color_scheme, 
            request.custom_text, request.company_name
        )
        
        return MockupCreationResponse(
            customer_id=request.customer_id,
            product_id=request.product_id,
            mockup_images=mockup_result["mockup_images"],
            variations=mockup_result["variations"],
            customization_applied=mockup_result["customization_applied"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating mockup for customer {request.customer_id}, product {request.product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mockup")

@router.get("/email-templates", response_model=List[EmailTemplate])
async def get_email_templates():
    """Get all available email templates"""
    try:
        _, _, email_templates = load_mock_data()
        return email_templates
    except Exception as e:
        logger.error(f"Error getting email templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to load email templates")

@router.get("/email-templates/{template_id}", response_model=EmailTemplate)
async def get_email_template(template_id: int):
    """Get a specific email template by ID"""
    try:
        _, _, email_templates = load_mock_data()
        template = next((t for t in email_templates if t["id"] == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load email template")

# Background task for processing
async def process_customer_analysis(customer_id: int):
    """Background task for customer analysis"""
    try:
        customers, _, _ = load_mock_data()
        customer = next((c for c in customers if c["id"] == customer_id), None)
        
        if customer:
            analysis_result = await customer_analyzer.analyze_customer(customer)
            logger.info(f"Background analysis completed for customer {customer_id}")
            return analysis_result
    except Exception as e:
        logger.error(f"Background analysis failed for customer {customer_id}: {e}")

@router.post("/analyze-customer-async")
async def analyze_customer_async(request: CustomerAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze a customer asynchronously"""
    background_tasks.add_task(process_customer_analysis, request.customer_id)
    return {"message": "Customer analysis started in background", "customer_id": request.customer_id} 