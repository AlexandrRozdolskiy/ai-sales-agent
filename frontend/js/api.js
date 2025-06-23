// API Client for FastAPI Backend
class APIClient {
    constructor(baseURL = 'http://localhost:8000/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw new Error(`API request failed: ${error.message}`);
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Health check
    async healthCheck() {
        return this.get('/health');
    }

    // Get all customers
    async getCustomers() {
        return this.get('/customers');
    }

    // Get specific customer
    async getCustomer(customerId) {
        return this.get(`/customers/${customerId}`);
    }

    // Get all products
    async getProducts() {
        return this.get('/products');
    }

    // Get specific product
    async getProduct(productId) {
        return this.get(`/products/${productId}`);
    }

    // Get email templates
    async getEmailTemplates() {
        return this.get('/email-templates');
    }

    // Analyze customer
    async analyzeCustomer(customerId) {
        return this.post('/analyze-customer', { customer_id: customerId });
    }

    // Get product recommendations
    async getProductRecommendations(customerId, options = {}) {
        const data = { customer_id: customerId, ...options };
        return this.post('/recommend-products', data);
    }

    // Generate email
    async generateEmail(customerId, productIds, emailStyle, templateId = null, customMessage = null) {
        const data = {
            customer_id: customerId,
            product_ids: productIds,
            email_style: emailStyle
        };

        if (templateId) data.template_id = templateId;
        if (customMessage) data.custom_message = customMessage;

        return this.post('/generate-email', data);
    }

    // Create mockup
    async createMockup(customerId, productId, logoPlacement, colorScheme, customText = null, companyName = '') {
        const data = {
            customer_id: customerId,
            product_id: productId,
            logo_placement: logoPlacement,
            color_scheme: colorScheme,
            company_name: companyName
        };

        if (customText) data.custom_text = customText;

        return this.post('/create-mockup', data);
    }

    // Test API connection
    async testConnection() {
        try {
            const health = await this.healthCheck();
            return {
                connected: true,
                status: health.status,
                service: health.service,
                version: health.version
            };
        } catch (error) {
            return {
                connected: false,
                error: error.message
            };
        }
    }
}

// Create global API instance
const api = new APIClient();

// Export for use in other modules
window.api = api; 