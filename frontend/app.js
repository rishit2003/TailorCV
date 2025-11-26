// ==========================================
// Configuration
// ==========================================

const API_BASE_URL = "http://localhost:8000/api";

// Global state
let selectedCVId = null;
let selectedCVFilename = null;

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    setupTabSwitching();
    
    // Load CVs with a small delay to ensure DOM is ready
    setTimeout(() => {
        console.log('Loading CVs...');
        loadCVs();
    }, 500);
});

// ==========================================
// Tab Switching
// ==========================================

function setupTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            
            // Add active class to clicked button and corresponding tab
            button.classList.add('active');
            const tabId = button.dataset.tab;
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// ==========================================
// CV Upload Functions
// ==========================================

async function uploadCVText() {
    const cvText = document.getElementById('cv-text-input').value;
    
    if (!cvText.trim()) {
        showError('Please paste your CV text first!');
        return;
    }
    
    showLoading('Uploading and structuring your CV...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload_cv_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cv_text: cvText })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to upload CV');
        }
        
        hideLoading();
        showUploadSuccess(data);
        
        // Clear text area
        document.getElementById('cv-text-input').value = '';
        
        // Reload CV list
        await loadCVs();
        
    } catch (error) {
        hideLoading();
        showError(`Upload failed: ${error.message}`);
    }
}

async function uploadCVPDF() {
    const fileInput = document.getElementById('pdf-file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Please select a PDF file first!');
        return;
    }
    
    showLoading('Extracting text from PDF and structuring...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/upload_cv_pdf`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to upload PDF');
        }
        
        hideLoading();
        showUploadSuccess(data);
        
        // Reset file input
        fileInput.value = '';
        document.getElementById('file-name').textContent = 'Choose PDF file or drag here';
        
        // Reload CV list
        await loadCVs();
        
    } catch (error) {
        hideLoading();
        showError(`Upload failed: ${error.message}`);
    }
}

function handlePDFSelection() {
    const fileInput = document.getElementById('pdf-file-input');
    const fileNameSpan = document.getElementById('file-name');
    
    if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
    }
}

function showUploadSuccess(data) {
    const statusDiv = document.getElementById('upload-status');
    statusDiv.className = 'status-message success';
    statusDiv.innerHTML = `
        ✅ ${data.message}<br>
        <strong>Filename:</strong> ${data.filename}<br>
        <strong>CV ID:</strong> ${data.cv_id.substring(0, 16)}...<br>
        <strong>Status:</strong> ${data.status}
    `;
}

// ==========================================
// CV Selection Functions
// ==========================================

async function loadCVs() {
    try {
        console.log('Loading CVs from:', `${API_BASE_URL}/my_cvs`);
        
        const response = await fetch(`${API_BASE_URL}/my_cvs`);
        
        if (!response.ok) {
            throw new Error(`Failed to load CVs: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('CVs loaded:', data);
        
        const dropdown = document.getElementById('cv-dropdown');
        
        // Clear existing options except first
        dropdown.innerHTML = '<option value="">-- Select a CV --</option>';
        
        // Add CVs to dropdown
        if (data.success && data.cvs && data.cvs.length > 0) {
            console.log(`Adding ${data.cvs.length} CVs to dropdown`);
            
            data.cvs.forEach(cv => {
                const option = document.createElement('option');
                option.value = cv.cv_id;
                option.textContent = `${cv.filename} (${cv.cv_id.substring(0, 8)}...)`;
                option.dataset.filename = cv.filename;
                dropdown.appendChild(option);
            });
            
            // Auto-select first CV if none selected
            if (!selectedCVId && data.cvs.length > 0) {
                dropdown.value = data.cvs[0].cv_id;
                handleCVSelection();
            }
            
            console.log('Dropdown populated successfully');
        } else {
            console.log('No CVs found');
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No CVs uploaded yet';
            dropdown.appendChild(option);
        }
        
    } catch (error) {
        console.error('Failed to load CVs:', error);
        showError(`Failed to load CVs: ${error.message}`);
    }
}

function handleCVSelection() {
    const dropdown = document.getElementById('cv-dropdown');
    const selectedOption = dropdown.options[dropdown.selectedIndex];
    
    if (dropdown.value) {
        selectedCVId = dropdown.value;
        selectedCVFilename = selectedOption.dataset.filename;
        
        const infoBox = document.getElementById('selected-cv-info');
        infoBox.innerHTML = `
            ✅ <strong>Selected CV:</strong> ${selectedCVFilename}<br>
            <strong>CV ID:</strong> ${selectedCVId.substring(0, 24)}...
        `;
    } else {
        selectedCVId = null;
        selectedCVFilename = null;
        document.getElementById('selected-cv-info').innerHTML = '';
    }
}

// ==========================================
// Analysis Functions
// ==========================================

async function analyzeKeywords() {
    if (!selectedCVId) {
        showError('Please select a CV from the dropdown first!');
        return;
    }
    
    const jobDescription = document.getElementById('job-description-input').value;
    
    if (!jobDescription.trim()) {
        showError('Please paste a job description first!');
        return;
    }
    
    showLoading('Analyzing keywords with AI...');
    clearResults();
    
    try {
        const response = await fetch(`${API_BASE_URL}/keywords`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cv_id: selectedCVId,
                job_description: jobDescription
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to analyze keywords');
        }
        
        hideLoading();
        displayKeywordsResults(data);
        
    } catch (error) {
        hideLoading();
        showError(`Analysis failed: ${error.message}`);
    }
}

async function calculateScore() {
    if (!selectedCVId) {
        showError('Please select a CV from the dropdown first!');
        return;
    }
    
    const jobDescription = document.getElementById('job-description-input').value;
    
    if (!jobDescription.trim()) {
        showError('Please paste a job description first!');
        return;
    }
    
    showLoading('Calculating CV score with AI...');
    clearResults();
    
    try {
        const response = await fetch(`${API_BASE_URL}/score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cv_id: selectedCVId,
                job_description: jobDescription
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to calculate score');
        }
        
        hideLoading();
        displayScoreResults(data);
        
    } catch (error) {
        hideLoading();
        showError(`Calculation failed: ${error.message}`);
    }
}

// ==========================================
// Display Results Functions
// ==========================================

function displayKeywordsResults(data) {
    const container = document.getElementById('keywords-results');
    const content = document.getElementById('keywords-content');
    
    let html = `
        <div class="keywords-group">
            <h4>✅ Keywords You HAVE</h4>
            <div class="keyword-pills">
    `;
    
    // Technical skills you have
    if (data.keywords_you_have.technical.length > 0) {
        html += '<div style="width: 100%; margin-bottom: 15px;"><strong>Technical:</strong></div>';
        data.keywords_you_have.technical.forEach(keyword => {
            html += `<span class="keyword-pill keyword-have">${keyword}</span>`;
        });
    }
    
    // Soft skills you have
    if (data.keywords_you_have.soft.length > 0) {
        html += '<div style="width: 100%; margin-top: 15px; margin-bottom: 15px;"><strong>Soft Skills:</strong></div>';
        data.keywords_you_have.soft.forEach(keyword => {
            html += `<span class="keyword-pill keyword-have">${keyword}</span>`;
        });
    }
    
    html += `
            </div>
        </div>
        <div class="keywords-group">
            <h4>❌ Keywords You're MISSING</h4>
            <div class="keyword-pills">
    `;
    
    // Technical skills missing
    if (data.keywords_missing.technical.length > 0) {
        html += '<div style="width: 100%; margin-bottom: 15px;"><strong>Technical:</strong></div>';
        data.keywords_missing.technical.forEach(keyword => {
            html += `<span class="keyword-pill keyword-missing">${keyword}</span>`;
        });
    }
    
    // Soft skills missing
    if (data.keywords_missing.soft.length > 0) {
        html += '<div style="width: 100%; margin-top: 15px; margin-bottom: 15px;"><strong>Soft Skills:</strong></div>';
        data.keywords_missing.soft.forEach(keyword => {
            html += `<span class="keyword-pill keyword-missing">${keyword}</span>`;
        });
    }
    
    html += `
            </div>
        </div>
    `;
    
    content.innerHTML = html;
    container.classList.remove('hidden');
    document.getElementById('results-container').classList.remove('hidden');
}

function displayScoreResults(data) {
    const container = document.getElementById('score-results');
    const content = document.getElementById('score-content');
    
    let html = `
        <div class="score-overview">
            <div class="score-circle">
                <div class="score-number">${data.overall_score}</div>
                <div class="score-max">/ ${data.max_score}</div>
            </div>
            <div class="score-rating">${data.rating}</div>
        </div>
        
        <h4>Category Breakdown</h4>
    `;
    
    // Category scores
    for (const [categoryKey, categoryData] of Object.entries(data.category_scores)) {
        const categoryName = categoryKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `
            <div class="category-score">
                <h5>
                    <span>${categoryName}</span>
                    <span>${categoryData.score} / ${categoryData.max_score} (${categoryData.percentage}%)</span>
                </h5>
                <div class="score-bar">
                    <div class="score-bar-fill" style="width: ${categoryData.percentage}%">
                        ${categoryData.percentage}%
                    </div>
                </div>
                <p style="margin-top: 8px; color: #6c757d; font-size: 0.9em;">${categoryData.explanation}</p>
            </div>
        `;
    }
    
    // Strengths
    if (data.strengths && data.strengths.length > 0) {
        html += `
            <div class="list-section">
                <h5>💪 Strengths</h5>
                <ul>
        `;
        data.strengths.forEach(strength => {
            html += `<li>${strength}</li>`;
        });
        html += `
                </ul>
            </div>
        `;
    }
    
    // Gaps
    if (data.gaps && data.gaps.length > 0) {
        html += `
            <div class="list-section">
                <h5>⚠️ Areas for Improvement</h5>
                <ul>
        `;
        data.gaps.forEach(gap => {
            html += `<li>${gap}</li>`;
        });
        html += `
                </ul>
            </div>
        `;
    }
    
    // Recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        html += `
            <div class="list-section">
                <h5>💡 Recommendations</h5>
                <ul>
        `;
        data.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        html += `
                </ul>
            </div>
        `;
    }
    
    content.innerHTML = html;
    container.classList.remove('hidden');
    document.getElementById('results-container').classList.remove('hidden');
}

// ==========================================
// Utility Functions
// ==========================================

function showLoading(message) {
    document.getElementById('loading-message').textContent = message;
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('error-message').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    hideLoading();
}

async function generateTailoredBullets() {
    const jobDescription = document.getElementById('job-description-input').value;
    
    if (!jobDescription.trim()) {
        showError('Please paste a job description first!');
        return;
    }
    
    showLoading('Finding similar CV chunks and generating tailored bullets...');
    clearResults();
    
    try {
        const response = await fetch(`${API_BASE_URL}/tailored_bullets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_description: jobDescription
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to generate tailored bullets');
        }
        
        hideLoading();
        displayBulletsResults(data);
        
    } catch (error) {
        hideLoading();
        showError(`Generation failed: ${error.message}`);
    }
}

function displayBulletsResults(data) {
    const container = document.getElementById('bullets-results');
    const content = document.getElementById('bullets-content');
    
    let html = `
        <div class="bullets-info">
            <p><strong>Generated:</strong> ${data.count} bullet points</p>
            <p><strong>Chunks Used:</strong> ${data.chunks_used || 'N/A'}</p>
        </div>
        <div class="bullets-list">
    `;
    
    if (data.tailored_bullets && data.tailored_bullets.length > 0) {
        data.tailored_bullets.forEach((bullet, index) => {
            html += `
                <div class="bullet-item">
                    <span class="bullet-number">${index + 1}.</span>
                    <span class="bullet-text">${bullet}</span>
                </div>
            `;
        });
    } else {
        html += '<p>No bullets generated. Try uploading more CVs or adjusting your job description.</p>';
    }
    
    html += '</div>';
    
    content.innerHTML = html;
    container.classList.remove('hidden');
    document.getElementById('results-container').classList.remove('hidden');
}

function clearResults() {
    document.getElementById('keywords-results').classList.add('hidden');
    document.getElementById('score-results').classList.add('hidden');
    document.getElementById('bullets-results').classList.add('hidden');
    document.getElementById('error-message').classList.add('hidden');
}

