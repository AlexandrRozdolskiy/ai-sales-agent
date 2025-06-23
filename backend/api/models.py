from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Customer Analysis Models
class CustomerAnalysisRequest(BaseModel):
    customer_id: int = Field(..., description="ID of the customer to analyze")
    
class CustomerAnalysisResponse(BaseModel):
    customer_id: int
    analysis: Dict[str, Any] = Field(..., description="AI-generated customer analysis")
    pain_points: List[str] = Field(..., description="Identified pain points")
    opportunities: List[str] = Field(..., description="Sales opportunities")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in analysis")
    timestamp: datetime = Field(default_factory=datetime.now)

# Product Recommendation Models
class ProductRecommendationRequest(BaseModel):
    customer_id: int = Field(..., description="ID of the customer")
    analysis_id: Optional[str] = Field(None, description="ID of previous analysis")
    budget_range: Optional[str] = Field(None, description="Budget range preference")
    
class ProductRecommendation(BaseModel):
    product_id: int
    name: str
    category: str
    price_range: str
    match_score: float = Field(..., ge=0.0, le=1.0, description="AI match score")
    reasoning: str = Field(..., description="AI reasoning for recommendation")
    customization_suggestions: List[str] = Field(..., description="Suggested customizations")
    
class ProductRecommendationResponse(BaseModel):
    customer_id: int
    recommendations: List[ProductRecommendation] = Field(..., description="Product recommendations")
    top_recommendation: ProductRecommendation = Field(..., description="Best match product")
    timestamp: datetime = Field(default_factory=datetime.now)

# Email Generation Models
class EmailGenerationRequest(BaseModel):
    customer_id: int = Field(..., description="ID of the customer")
    product_ids: List[int] = Field(..., description="Selected product IDs")
    email_style: str = Field(..., description="Email style: formal, casual, consultative, enthusiastic")
    template_id: Optional[int] = Field(None, description="Email template ID")
    custom_message: Optional[str] = Field(None, description="Additional custom message")
    
class EmailGenerationResponse(BaseModel):
    customer_id: int
    subject: str = Field(..., description="Generated email subject")
    body: str = Field(..., description="Generated email body")
    style: str = Field(..., description="Email style used")
    personalization_score: float = Field(..., ge=0.0, le=1.0, description="Personalization level")
    call_to_action: str = Field(..., description="Generated call to action")
    timestamp: datetime = Field(default_factory=datetime.now)

# Mockup Creation Models
class MockupCreationRequest(BaseModel):
    customer_id: int = Field(..., description="ID of the customer")
    product_id: int = Field(..., description="ID of the product")
    logo_placement: str = Field(..., description="Logo placement preference")
    color_scheme: str = Field(..., description="Color scheme preference")
    custom_text: Optional[str] = Field(None, description="Custom text to add")
    company_name: str = Field(..., description="Company name for branding")
    
class MockupCreationResponse(BaseModel):
    customer_id: int
    product_id: int
    mockup_images: List[str] = Field(..., description="Base64 encoded mockup images")
    variations: List[Dict[str, Any]] = Field(..., description="Different mockup variations")
    customization_applied: Dict[str, Any] = Field(..., description="Applied customizations")
    timestamp: datetime = Field(default_factory=datetime.now)

# Customer Data Models
class CompanyInfo(BaseModel):
    name: str
    industry: str
    size: str
    location: str
    website: str

class ContactInfo(BaseModel):
    name: str
    role: str
    email: str
    phone: str

class BehavioralData(BaseModel):
    recent_activities: List[str]
    pain_points: List[str]
    budget_range: str
    decision_timeline: str

class EngagementHistory(BaseModel):
    last_contact: str
    interaction_frequency: str
    preferred_communication: str
    previous_purchases: List[str]

class Customer(BaseModel):
    id: int
    company: CompanyInfo
    contact: ContactInfo
    behavioral_data: BehavioralData
    engagement_history: EngagementHistory

# Product Data Models
class CustomizationOptions(BaseModel):
    logo_placement: List[str]
    colors: List[str]
    text_options: List[str]
    sizes: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    features: Optional[List[str]] = None
    styles: Optional[List[str]] = None
    devices: Optional[List[str]] = None
    compartments: Optional[List[str]] = None
    contents: Optional[List[str]] = None
    themes: Optional[List[str]] = None

class TargetAudience(BaseModel):
    industries: List[str]
    company_size: List[str]
    use_cases: List[str]

class Product(BaseModel):
    id: int
    name: str
    category: str
    price_range: str
    description: str
    customization_options: CustomizationOptions
    target_audience: TargetAudience
    benefits: List[str]
    minimum_order: int
    lead_time: str

# Email Template Models
class EmailTemplate(BaseModel):
    id: int
    name: str
    subject_template: str
    style: str
    template: Dict[str, str]
    use_cases: List[str]

# Health Check Models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now) 