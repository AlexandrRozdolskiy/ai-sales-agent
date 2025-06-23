// Tab switching logic (robust)
window.switchTab = function(tab) {
    const tabs = ['analysis', 'customers', 'products'];
    tabs.forEach(t => {
        document.getElementById('tabContent' + capitalize(t)).style.display = (t === tab) ? 'block' : 'none';
        document.getElementById('tab' + capitalize(t) + 'Btn').classList.toggle('active', t === tab);
    });
    if (tab === 'customers') renderCustomersTable();
    if (tab === 'products') renderProductsGrid();
};

// Global variables
let currentCustomer = null;
let currentAnalysis = null;
let currentRecommendations = null;
let selectedProducts = new Set();

// --- Customers Database Tab ---
let customersTableData = [];
let customersTableSort = { column: 'company', asc: true };
let customersSynced = false; // Track if CRM sync has occurred

// --- Products Catalog Tab ---
let productsGridData = [];
let productsGridCategory = 'All';
let productsAddedToRecs = new Set();

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Test API connection
        const connection = await api.testConnection();
        updateAPIStatus(connection.connected);
        
        if (connection.connected) {
            await loadCustomers();
            setupEventListeners();
            console.log('AI Sales Agent initialized successfully');
        } else {
            showNotification('API connection failed', 'error');
        }
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showNotification('Failed to initialize application', 'error');
    }
}

// Update API status indicator
function updateAPIStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (connected) {
        statusDot.style.background = 'var(--success-green)';
        statusText.textContent = 'API Connected';
    } else {
        statusDot.style.background = 'var(--error-red)';
        statusText.textContent = 'API Disconnected';
    }
}

// Load customers from API
async function loadCustomers() {
    try {
        const customers = await api.getCustomers();
        populateCustomerSelect(customers);
    } catch (error) {
        console.error('Error loading customers:', error);
        showNotification('Failed to load customers', 'error');
    }
}

// Populate customer dropdown
function populateCustomerSelect(customers) {
    const select = document.getElementById('customerSelect');
    select.innerHTML = '<option value="">Choose customer...</option>';
    
    customers.forEach(customer => {
        const option = document.createElement('option');
        option.value = customer.id;
        option.textContent = `${customer.company.name} - ${customer.company.industry}`;
        select.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Customer selection
    document.getElementById('customerSelect').addEventListener('change', function() {
        const customerId = this.value;
        if (customerId) {
            loadCustomerProfile(parseInt(customerId));
        } else {
            resetApplication();
        }
    });
    // Section run buttons
    document.getElementById('runAnalysisBtn').addEventListener('click', runAnalysis);
    document.getElementById('runRecommendationsBtn').addEventListener('click', runRecommendations);
    document.getElementById('runEmailBtn').addEventListener('click', runEmail);
    document.getElementById('runMockupsBtn').addEventListener('click', runMockups);
    // Tab navigation buttons
    document.getElementById('tabAnalysisBtn').addEventListener('click', () => switchTab('analysis'));
    document.getElementById('tabCustomersBtn').addEventListener('click', () => switchTab('customers'));
    document.getElementById('tabProductsBtn').addEventListener('click', () => switchTab('products'));
}

// Load customer profile only
async function loadCustomerProfile(customerId) {
    try {
        currentCustomer = customerId;
        // Get customer data
        const customer = await api.getCustomer(customerId);
        updateCustomerDisplay(customer);
        updateCurrentCustomerName(customer.company.name);
        // Reset all results
        resetSectionStates();
    } catch (error) {
        console.error('Error loading customer profile:', error);
        showNotification('Failed to load customer data', 'error');
    }
}

// Reset all section states
function resetSectionStates() {
    ['statusProfile', 'statusAnalysis', 'statusProducts', 'statusEmail'].forEach(id => {
        updateProcessingStatus(id, 'pending');
    });
    document.getElementById('intelligenceContent').innerHTML = '';
    document.getElementById('recommendationsContent').innerHTML = '';
    document.getElementById('emailContent').innerHTML = '';
    document.getElementById('emailActions').style.display = 'none';
    document.getElementById('mockupGallery').innerHTML = '';
    document.getElementById('quickStats').style.display = 'none';
    document.getElementById('confidenceBar').style.width = '0%';
    document.getElementById('confidencePercent').textContent = '0%';
    document.getElementById('personalizationScore').textContent = '0%';
}

function skeletonLoaderHTML(type) {
    if (type === 'line') {
        return `<div class="skeleton-loader">
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
        </div>`;
    } else if (type === 'image') {
        return `<div class="skeleton-loader">
            <div class="skeleton-image"></div>
            <div class="skeleton-image"></div>
            <div class="skeleton-image"></div>
        </div>`;
    }
    return '';
}

// Helper to get and set analysis cache for a customer
function getAnalysisCache() {
    try {
        return JSON.parse(localStorage.getItem('analysisCache') || '{}');
    } catch {
        return {};
    }
}
function setAnalysisCache(customerId, data) {
    const cache = getAnalysisCache();
    cache[customerId] = { ...cache[customerId], ...data };
    localStorage.setItem('analysisCache', JSON.stringify(cache));
}

// Update isAnalysisCached to require all three: analysis, recommendations, email
function isAnalysisCached(customerId) {
    try {
        const cache = getAnalysisCache();
        const entry = cache[customerId];
        return !!(entry && entry.analysis && entry.recommendations && entry.email);
    } catch {
        return false;
    }
}

// Section: Run Analysis
async function runAnalysis() {
    if (!currentCustomer) {
        showNotification('Please select a customer first', 'error');
        return;
    }
    const btn = document.getElementById('runAnalysisBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner" style="width:18px;height:18px;border-width:3px;"></span> Running...';
    try {
        updateProcessingStatus('statusProfile', 'processing');
        document.getElementById('intelligenceContent').innerHTML = skeletonLoaderHTML('line');
        // Call API
        const result = await api.post('/analyze-customer', { customer_id: currentCustomer });
        currentAnalysis = result;
        setAnalysisCache(currentCustomer, { analysis: result });
        updateProcessingStatus('statusProfile', 'complete');
        showQuickStats();
        displayCustomerIntelligence();
    } catch (error) {
        updateProcessingStatus('statusProfile', 'error');
        showNotification('Analysis failed', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Run Analysis';
    }
}

// Section: Run Recommendations
async function runRecommendations() {
    if (!currentCustomer) {
        showNotification('Please select a customer first', 'error');
        return;
    }
    const btn = document.getElementById('runRecommendationsBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner" style="width:18px;height:18px;border-width:3px;"></span> Running...';
    try {
        updateProcessingStatus('statusAnalysis', 'processing');
        document.getElementById('recommendationsContent').innerHTML = skeletonLoaderHTML('line');
        // Call API
        const result = await api.post('/recommend-products', { customer_id: currentCustomer });
        currentRecommendations = result;
        setAnalysisCache(currentCustomer, { recommendations: result });
        updateProcessingStatus('statusAnalysis', 'complete');
        displayProductRecommendations();
    } catch (error) {
        updateProcessingStatus('statusAnalysis', 'error');
        showNotification('Failed to get recommendations', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Get Recommendations';
    }
}

// Section: Run Email
async function runEmail() {
    if (!currentCustomer) {
        showNotification('Please select a customer first', 'error');
        return;
    }
    if (!currentRecommendations || !currentRecommendations.recommendations.length) {
        showNotification('Please get recommendations first', 'error');
        return;
    }
    const btn = document.getElementById('runEmailBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner" style="width:18px;height:18px;border-width:3px;"></span> Running...';
    try {
        updateProcessingStatus('statusProducts', 'processing');
        document.getElementById('emailContent').innerHTML = skeletonLoaderHTML('line');
        // Use top product for demo simplicity
        const topProduct = currentRecommendations.recommendations[0];
        const result = await api.generateEmail(currentCustomer, [topProduct.product_id], 'consultative');
        setAnalysisCache(currentCustomer, { email: result });
        updateProcessingStatus('statusProducts', 'complete');
        updateProcessingStatus('statusEmail', 'complete');
        displayEmail(result);
    } catch (error) {
        updateProcessingStatus('statusProducts', 'error');
        updateProcessingStatus('statusEmail', 'error');
        showNotification('Failed to generate email', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Generate Email';
    }
}

// Section: Run Mockups
async function runMockups() {
    if (!currentCustomer) {
        showNotification('Please select a customer first', 'error');
        return;
    }
    if (!currentRecommendations || !currentRecommendations.recommendations.length) {
        showNotification('Please get recommendations first', 'error');
        return;
    }
    const btn = document.getElementById('runMockupsBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner" style="width:18px;height:18px;border-width:3px;"></span> Running...';
    try {
        document.getElementById('mockupGallery').innerHTML = skeletonLoaderHTML('image');
        // Use top product for demo simplicity
        const topProduct = currentRecommendations.recommendations[0];
        const customer = await api.getCustomer(currentCustomer);
        const result = await api.createMockup(
            currentCustomer,
            topProduct.product_id,
            'front cover',
            'blue',
            null,
            customer.company.name
        );
        displayMockups(result);
    } catch (error) {
        showNotification('Failed to generate mockups', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Generate Mockups';
    }
}

// Update customer display in sidebar
function updateCustomerDisplay(customer) {
    document.getElementById('profileCompany').textContent = customer.company.name;
    document.getElementById('profileIndustry').textContent = customer.company.industry;
    document.getElementById('profileSize').textContent = customer.company.size;
    document.getElementById('profileBudget').textContent = customer.behavioral_data.budget_range;
    
    document.getElementById('customerProfile').style.display = 'block';
}

// Update current customer name in header
function updateCurrentCustomerName(name) {
    document.querySelector('.customer-name').textContent = name;
}

// Start AI analysis
async function startAnalysis() {
    if (!currentCustomer) return;
    
    try {
        showLoading('Starting AI Analysis', 'Initializing customer intelligence analysis...');
        
        // Step 1: Customer Analysis
        updateProcessingStatus('statusProfile', 'processing');
        updateLoading('Analyzing Customer Profile', 'Extracting company insights and behavioral patterns...');
        
        currentAnalysis = await api.analyzeCustomer(currentCustomer);
        updateProcessingStatus('statusProfile', 'complete');
        
        // Step 2: Product Recommendations
        updateProcessingStatus('statusAnalysis', 'processing');
        updateLoading('Generating Product Recommendations', 'Matching customer needs with optimal solutions...');
        
        currentRecommendations = await api.getProductRecommendations(currentCustomer);
        updateProcessingStatus('statusAnalysis', 'complete');
        
        // Step 3: Email Generation
        updateProcessingStatus('statusProducts', 'processing');
        updateLoading('Preparing Email Generation', 'Setting up personalized email templates...');
        
        // Auto-generate email with first recommendation
        if (currentRecommendations.recommendations.length > 0) {
            const topProduct = currentRecommendations.recommendations[0];
            selectedProducts.add(topProduct.product_id);
            
            const emailResult = await api.generateEmail(
                currentCustomer, 
                [topProduct.product_id], 
                'consultative'
            );
            
            updateProcessingStatus('statusProducts', 'complete');
            updateProcessingStatus('statusEmail', 'complete');
            
            // Display results
            displayResults(emailResult);
        }
        
        hideLoading();
        showQuickStats();
        
    } catch (error) {
        console.error('Error during analysis:', error);
        hideLoading();
        showNotification('Analysis failed', 'error');
        updateProcessingStatus('statusProfile', 'error');
    }
}

// Update processing status
function updateProcessingStatus(statusId, status) {
    const statusItem = document.getElementById(statusId);
    const icon = statusItem.querySelector('.status-icon');
    
    statusItem.className = `status-item ${status}`;
    
    switch (status) {
        case 'processing':
            icon.textContent = '⏳';
            break;
        case 'complete':
            icon.textContent = '✅';
            break;
        case 'error':
            icon.textContent = '❌';
            break;
        default:
            icon.textContent = '⏸️';
    }
}

// Show quick stats
function showQuickStats() {
    if (currentAnalysis) {
        const confidencePercent = Math.round(currentAnalysis.confidence_score * 100);
        document.getElementById('confidenceScore').textContent = `${confidencePercent}%`;
        document.getElementById('responseRate').textContent = `${Math.round(confidencePercent * 0.4)}%`;
        document.getElementById('quickStats').style.display = 'block';
    }
}

// Display analysis results
function displayResults(emailResult) {
    // Display customer intelligence
    displayCustomerIntelligence();
    
    // Display product recommendations
    displayProductRecommendations();
    
    // Display email
    displayEmail(emailResult);
}

// Display customer intelligence
function displayCustomerIntelligence() {
    if (!currentAnalysis) return;
    
    const content = document.getElementById('intelligenceContent');
    const confidencePercent = Math.round(currentAnalysis.confidence_score * 100);
    
    // Update confidence bar
    document.getElementById('confidenceBar').style.width = `${confidencePercent}%`;
    document.getElementById('confidencePercent').textContent = `${confidencePercent}%`;
    
    content.innerHTML = `
        <div class="intelligence-section">
            <h4>Company Profile</h4>
            <p>${currentAnalysis.analysis.company_profile || 'Analysis not available'}</p>
        </div>
        <div class="intelligence-section">
            <h4>Pain Points</h4>
            <p>${currentAnalysis.pain_points.join(', ')}</p>
        </div>
        <div class="intelligence-section">
            <h4>Opportunities</h4>
            <p>${currentAnalysis.opportunities.join(', ')}</p>
        </div>
        <div class="intelligence-section">
            <h4>Decision Factors</h4>
            <p>${currentAnalysis.analysis.decision_making_factors || 'Analysis not available'}</p>
        </div>
    `;
}

// Display product recommendations
function displayProductRecommendations() {
    if (!currentRecommendations) return;
    
    const content = document.getElementById('recommendationsContent');
    
    const recommendationsHTML = currentRecommendations.recommendations.slice(0, 5).map(rec => {
        const matchPercent = Math.round(rec.match_score * 100);
        return `
            <div class="recommendation-item">
                <div class="recommendation-info">
                    <div class="recommendation-name">${rec.name}</div>
                    <div class="recommendation-details">${rec.category} • ${rec.price_range}</div>
                </div>
                <div class="match-score">${matchPercent}%</div>
            </div>
        `;
    }).join('');
    
    content.innerHTML = recommendationsHTML;
}

// Display email
function displayEmail(emailResult) {
    const content = document.getElementById('emailContent');
    const actions = document.getElementById('emailActions');
    const personalizationScore = Math.round(emailResult.personalization_score * 100);
    
    document.getElementById('personalizationScore').textContent = `${personalizationScore}%`;
    
    content.innerHTML = `
        <div class="email-subject">
            <strong>Subject:</strong> ${emailResult.subject}
        </div>
        <div class="email-body">${emailResult.body}</div>
    `;
    
    actions.style.display = 'flex';
    
    // Store email data for copy/download
    window.currentEmail = emailResult;
}

// Generate mockups
async function generateMockups() {
    if (!currentCustomer || !currentRecommendations) {
        showNotification('Please select a customer first', 'error');
        return;
    }
    
    try {
        showLoading('Creating Mockups', 'Generating branded product mockups...');
        
        const topProduct = currentRecommendations.recommendations[0];
        const customer = await api.getCustomer(currentCustomer);
        
        const mockupResult = await api.createMockup(
            currentCustomer,
            topProduct.product_id,
            'front cover',
            'blue',
            null,
            customer.company.name
        );
        
        displayMockups(mockupResult);
        hideLoading();
        
    } catch (error) {
        console.error('Error generating mockups:', error);
        hideLoading();
        showNotification('Failed to generate mockups', 'error');
    }
}

// Display mockups
function displayMockups(mockupResult) {
    const gallery = document.getElementById('mockupGallery');
    
    const mockupsHTML = mockupResult.mockup_images.map((imageData, index) => {
        const variation = mockupResult.variations[index] || { type: 'main', description: 'Main mockup' };
        
        return `
            <div class="mockup-item">
                <img src="${imageData}" alt="Mockup ${index + 1}" class="mockup-image">
                <div class="mockup-info">
                    <div class="mockup-type">${variation.type}</div>
                    <div class="mockup-description">${variation.description}</div>
                </div>
            </div>
        `;
    }).join('');
    
    gallery.innerHTML = mockupsHTML;
}

// Copy email to clipboard
async function copyEmail() {
    if (!window.currentEmail) return;
    
    const fullEmail = `Subject: ${window.currentEmail.subject}\n\n${window.currentEmail.body}`;
    
    try {
        await navigator.clipboard.writeText(fullEmail);
        showNotification('Email copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy email:', error);
        showNotification('Failed to copy email', 'error');
    }
}

// Download email
function downloadEmail() {
    if (!window.currentEmail) return;
    
    const fullEmail = `Subject: ${window.currentEmail.subject}\n\n${window.currentEmail.body}`;
    const blob = new Blob([fullEmail], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `email_${currentCustomer}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Email downloaded successfully!', 'success');
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Reset application
function resetApplication() {
    currentCustomer = null;
    currentAnalysis = null;
    currentRecommendations = null;
    selectedProducts.clear();
    
    // Reset UI
    document.getElementById('customerProfile').style.display = 'none';
    document.getElementById('quickStats').style.display = 'none';
    document.querySelector('.customer-name').textContent = 'Select a customer to begin';
    
    // Reset processing status
    ['statusProfile', 'statusAnalysis', 'statusProducts', 'statusEmail'].forEach(id => {
        updateProcessingStatus(id, 'pending');
    });
    
    // Reset content
    document.getElementById('intelligenceContent').innerHTML = skeletonLoaderHTML('line');
    document.getElementById('recommendationsContent').innerHTML = skeletonLoaderHTML('line');
    document.getElementById('emailContent').innerHTML = skeletonLoaderHTML('line');
    document.getElementById('emailActions').style.display = 'none';
    document.getElementById('mockupGallery').innerHTML = skeletonLoaderHTML('image');
}

// Loading functions
function showLoading(title, message) {
    document.getElementById('loadingTitle').textContent = title;
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function updateLoading(title, message) {
    document.getElementById('loadingTitle').textContent = title;
    document.getElementById('loadingMessage').textContent = message;
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Notification system
function showNotification(message, type = 'info') {
    const notificationArea = document.getElementById('notificationArea');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    notification.innerHTML = `
        <h4>${type.charAt(0).toUpperCase() + type.slice(1)}</h4>
        <p>${message}</p>
    `;
    
    notificationArea.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Export functions for global access
window.selectCustomer = selectCustomer;
window.generateMockups = generateMockups;
window.copyEmail = copyEmail;
window.downloadEmail = downloadEmail;
window.toggleSidebar = toggleSidebar;

// On page load, render default tab content
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => switchTab('analysis'));
} else {
    switchTab('analysis');
}

function capitalize(str) { return str.charAt(0).toUpperCase() + str.slice(1); }

// Render Customers Table
async function renderCustomersTable() {
    const container = document.getElementById('customersTableContainer');
    if (!customersSynced) {
        // Show sync button and empty state
        container.innerHTML = `
            <button id="syncCrmBtn" class="btn btn-primary" style="margin-bottom:18px;">Sync from CRM</button>
            <div class="loading-text">No customers loaded. Click 'Sync from CRM' to fetch data.</div>
        `;
        document.getElementById('syncCrmBtn').onclick = async function() {
            container.innerHTML = '<div class="loading-text">Syncing with CRM...</div>';
            // Simulate loading delay
            setTimeout(async () => {
                customersTableData = await api.getCustomers();
                customersSynced = true;
                renderCustomersTableUI();
            }, 1200);
        };
        return;
    }
    // Fetch customers from API if not already loaded
    if (!customersTableData.length) {
        customersTableData = await api.getCustomers();
    }
    renderCustomersTableUI();
}

function renderCustomersTableUI() {
    const container = document.getElementById('customersTableContainer');
    if (!customersTableData.length) {
        container.innerHTML = '<div class="loading-text">No customers found.</div>';
        return;
    }
    // Add 'Send out emails' button
    const sendEmailsBtn = `<button id="sendEmailsBtn" class="btn btn-primary" style="margin-bottom:18px;float:right;">Send out emails</button>`;
    // Search/filter box
    const searchBox = `<input type="text" id="customersSearchBox" class="form-control" placeholder="Search customers..." style="margin-bottom:12px;max-width:320px;">`;
    // Table header
    const columns = [
        { key: 'company', label: 'Company Name' },
        { key: 'industry', label: 'Industry' },
        { key: 'size', label: 'Size' },
        { key: 'location', label: 'Location' },
        { key: 'budget', label: 'Budget' },
        { key: 'pain_points', label: 'Pain Points' },
        { key: 'last_activity', label: 'Last Activity' },
        { key: 'reachout_ready', label: 'Reachout Info Ready' }
    ];
    const ths = columns.map(col =>
        `<th class="sortable" data-col="${col.key}">${col.label} <span class="sort-arrow"></span></th>`
    ).join('');
    // Table body
    let filtered = customersTableData;
    const searchVal = (document.getElementById('customersSearchBox')||{}).value || '';
    if (searchVal) {
        filtered = filtered.filter(c =>
            c.company.name.toLowerCase().includes(searchVal.toLowerCase()) ||
            c.company.industry.toLowerCase().includes(searchVal.toLowerCase()) ||
            c.company.size.toLowerCase().includes(searchVal.toLowerCase()) ||
            c.company.location.toLowerCase().includes(searchVal.toLowerCase()) ||
            (c.behavioral_data.budget_range||'').toLowerCase().includes(searchVal.toLowerCase()) ||
            (c.behavioral_data.pain_points||[]).join(',').toLowerCase().includes(searchVal.toLowerCase())
        );
    }
    // Sort
    filtered = filtered.slice().sort((a, b) => {
        let aVal, bVal;
        switch (customersTableSort.column) {
            case 'company': aVal = a.company.name; bVal = b.company.name; break;
            case 'industry': aVal = a.company.industry; bVal = b.company.industry; break;
            case 'size': aVal = a.company.size; bVal = b.company.size; break;
            case 'location': aVal = a.company.location; bVal = b.company.location; break;
            case 'budget': aVal = a.behavioral_data.budget_range; bVal = b.behavioral_data.budget_range; break;
            case 'pain_points': aVal = (a.behavioral_data.pain_points||[]).join(', '); bVal = (b.behavioral_data.pain_points||[]).join(', '); break;
            case 'last_activity': aVal = a.behavioral_data.recent_activities?.[0] || ''; bVal = b.behavioral_data.recent_activities?.[0] || ''; break;
            case 'reachout_ready':
                aVal = isAnalysisCached(a.id) ? 1 : 0;
                bVal = isAnalysisCached(b.id) ? 1 : 0;
                break;
            default: aVal = ''; bVal = '';
        }
        if (aVal === undefined) aVal = '';
        if (bVal === undefined) bVal = '';
        if (aVal < bVal) return customersTableSort.asc ? -1 : 1;
        if (aVal > bVal) return customersTableSort.asc ? 1 : -1;
        return 0;
    });
    // Table rows
    const trs = filtered.map(c => {
        const ready = isAnalysisCached(c.id);
        return `<tr class="crm-row" data-id="${c.id}">
            <td>${c.company.name}</td>
            <td>${c.company.industry}</td>
            <td>${c.company.size}</td>
            <td>${c.company.location}</td>
            <td>${c.behavioral_data.budget_range||''}</td>
            <td>${(c.behavioral_data.pain_points||[]).join('<br>')}</td>
            <td>${(c.behavioral_data.recent_activities||[])[0]||''}</td>
            <td>${ready ? '<span class="status-done">✅</span>' : '—'}</td>
        </tr>`;
    }).join('');
    // Table HTML
    container.innerHTML = `
        ${sendEmailsBtn}
        ${searchBox}
        <div class="crm-table-scroll">
        <table class="crm-table">
            <thead><tr>${ths}</tr></thead>
            <tbody>${trs}</tbody>
        </table>
        </div>
    `;
    // Event listeners
    document.getElementById('customersSearchBox').oninput = renderCustomersTableUI;
    document.getElementById('sendEmailsBtn').onclick = function() { /* placeholder */ };
    Array.from(container.querySelectorAll('th.sortable')).forEach((th, idx) => {
        th.onclick = () => {
            const col = columns[idx].key;
            if (customersTableSort.column === col) {
                customersTableSort.asc = !customersTableSort.asc;
            } else {
                customersTableSort.column = col;
                customersTableSort.asc = true;
            }
            renderCustomersTableUI();
        };
        // Set sort arrow
        if (customersTableSort.column === columns[idx].key) {
            th.querySelector('.sort-arrow').textContent = customersTableSort.asc ? '▲' : '▼';
        } else {
            th.querySelector('.sort-arrow').textContent = '';
        }
    });
    // Row click
    Array.from(container.querySelectorAll('tr.crm-row')).forEach(row => {
        row.onclick = () => {
            const id = parseInt(row.getAttribute('data-id'));
            if (id) {
                loadCustomerProfile(id);
                switchTab('analysis');
            }
        };
    });
}

// Render Products Grid
async function renderProductsGrid() {
    // Fetch products from API
    try {
        productsGridData = await api.getProducts();
    } catch (e) {
        document.getElementById('productsGridContainer').innerHTML = '<div class="error-x">Failed to load products</div>';
        return;
    }
    renderProductsGridUI();
}

// SVG generator for product mockups
function generateProductSVG(product, width = 120, height = 80) {
    const color = product.color || '#4F8EF7';
    const name = product.name || 'Product';
    return `
        <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="background:#fff;border-radius:10px;">
            <rect x="5" y="5" width="${width-10}" height="${height-10}" rx="12" fill="${color}" stroke="#333" stroke-width="2"/>
            <text x="50%" y="55%" text-anchor="middle" fill="#fff" font-size="16" font-family="sans-serif" dy=".3em">${name}</text>
        </svg>
    `;
}

function renderProductsGridUI() {
    const container = document.getElementById('productsGridContainer');
    if (!productsGridData.length) {
        container.innerHTML = '<div class="loading-text">No products found.</div>';
        return;
    }
    // Category filter dropdown
    const categories = Array.from(new Set(productsGridData.map(p => p.category))).sort();
    const filterBox = `<select id="productsCategoryFilter" class="form-control" style="max-width:220px;margin-bottom:14px;">
        <option value="All">All Categories</option>
        ${categories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
    </select>`;
    // Filtered products
    let filtered = productsGridData;
    if (productsGridCategory !== 'All') {
        filtered = filtered.filter(p => p.category === productsGridCategory);
    }
    // Product cards
    const cards = filtered.map(p =>
        `<div class="product-card${productsAddedToRecs.has(p.id) ? ' added' : ''}" data-id="${p.id}">
            <div class="product-image-wrap">
                ${generateProductSVG(p, 120, 80)}
            </div>
            <div class="product-info">
                <div class="product-name">${p.name}</div>
                <div class="product-category">${p.category}</div>
                <div class="product-price">${p.price_range}</div>
                <div class="product-customization">${Object.keys(p.customization_options||{}).join(', ')}</div>
                <div class="product-bestfor">${(p.target_audience?.industries||[]).join(', ')}</div>
            </div>
            <button class="btn btn-secondary add-recommend-btn">${productsAddedToRecs.has(p.id) ? 'Added' : 'Add to Recommendations'}</button>
        </div>`
    ).join('');
    container.innerHTML = `
        ${filterBox}
        <div class="products-grid">
            ${cards}
        </div>
    `;
    // Event listeners
    document.getElementById('productsCategoryFilter').onchange = function() {
        productsGridCategory = this.value;
        renderProductsGridUI();
    };
    Array.from(container.querySelectorAll('.product-card')).forEach(card => {
        card.querySelector('.add-recommend-btn').onclick = (e) => {
            e.stopPropagation();
            const id = parseInt(card.getAttribute('data-id'));
            if (productsAddedToRecs.has(id)) return;
            productsAddedToRecs.add(id);
            renderProductsGridUI();
        };
    });
} 