// Web Scraper JavaScript Application with GSAP Animations

let currentScrapeType = 'text';
let currentResults = null;

// DOM Elements
const urlInput = document.getElementById('urlInput');
const scrapeBtn = document.getElementById('scrapeBtn');
const scrapeBtnBottom = document.getElementById('scrapeBtnBottom');
const typeButtons = document.querySelectorAll('.type-btn-modern');
const optionsSection = document.getElementById('optionsSection');
const optionsContent = document.getElementById('optionsContent');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const resultsContent = document.getElementById('resultsContent');
const errorSection = document.getElementById('errorSection');
const errorContent = document.getElementById('errorContent');
const exportBtn = document.getElementById('exportBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const clearBtn = document.getElementById('clearBtn');

// Initialize GSAP Animations
function initGSAPAnimations() {
    // Check if GSAP is loaded
    if (typeof gsap === 'undefined') {
        console.warn('GSAP not loaded, animations disabled');
        // Ensure all content is visible
        document.querySelectorAll('.card-modern, .type-btn-modern').forEach(el => {
            el.style.opacity = '1';
            el.style.visibility = 'visible';
        });
        return;
    }
    
    // Make sure content is visible first
    document.querySelectorAll('.card-modern, .type-btn-modern').forEach(el => {
        el.style.opacity = '1';
        el.style.visibility = 'visible';
    });
    
    // Spider icon rotation
    const spiderIcon = document.getElementById('spider-icon');
    if (spiderIcon) {
        gsap.to(spiderIcon, {
            rotation: 360,
            duration: 20,
            repeat: -1,
            ease: 'none'
        });

        // Float animation for spider
        gsap.to(spiderIcon, {
            y: -10,
            duration: 2,
            repeat: -1,
            yoyo: true,
            ease: 'power1.inOut'
        });
    }

    // Create floating particles
    createParticles();
}

// Create animated particles
function createParticles() {
    // Check if GSAP is loaded
    if (typeof gsap === 'undefined') {
        return;
    }
    
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#3b82f6'];
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = Math.random() * 10 + 5 + 'px';
        particle.style.height = particle.style.width;
        particle.style.borderRadius = '50%';
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.opacity = '0.3';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particlesContainer.appendChild(particle);

        gsap.to(particle, {
            y: -Math.random() * 100 - 50,
            x: Math.random() * 100 - 50,
            opacity: 0,
            duration: Math.random() * 3 + 2,
            repeat: -1,
            ease: 'power1.inOut'
        });
    }
}

// Initialize Barba.js for smooth page transitions
function initBarba() {
    if (typeof barba !== 'undefined') {
        barba.init({
            transitions: [{
                name: 'fade',
                leave(data) {
                    return gsap.to(data.current.container, {
                        opacity: 0,
                        duration: 0.5
                    });
                },
                enter(data) {
                    return gsap.from(data.next.container, {
                        opacity: 0,
                        duration: 0.5
                    });
                }
            }]
        });
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Verify all required elements exist
    if (!urlInput) {
        console.error('URL input not found!');
        return;
    }
    if (!scrapeBtn) {
        console.error('Scrape button not found!');
        return;
    }
    
    initializeEventListeners();
    loadOptionsForType('text');
    initGSAPAnimations();
    initBarba();
    
    // Focus on URL input for better UX
    urlInput.focus();
});

// Event Listeners
function initializeEventListeners() {
    // Type button clicks
    typeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            setActiveType(type);
            loadOptionsForType(type);
        });
    });

    // Scrape button
    if (scrapeBtn) {
        scrapeBtn.addEventListener('click', handleScrape);
        scrapeBtn.style.display = 'inline-flex';
        scrapeBtn.disabled = false;
    }

    // Bottom scrape button
    if (scrapeBtnBottom) {
        scrapeBtnBottom.addEventListener('click', handleScrape);
        scrapeBtnBottom.style.display = 'inline-flex';
        scrapeBtnBottom.disabled = false;
    }

    // Enter key on URL input
    if (urlInput) {
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleScrape();
            }
        });
    }

    // Export button
    if (exportBtn) {
        exportBtn.addEventListener('click', handleExport);
    }

    // Export PDF button
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', handleExportPdf);
    }

    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener('click', handleClear);
    }
}

// Set active type with animation
function setActiveType(type) {
    currentScrapeType = type;
    typeButtons.forEach(btn => {
        if (btn.dataset.type === type) {
            btn.classList.add('active');
            // Animate active button only if GSAP is available
            if (typeof gsap !== 'undefined') {
                gsap.fromTo(btn, 
                    { scale: 1 },
                    { scale: 1.1, duration: 0.3, yoyo: true, repeat: 1, ease: 'power2.inOut' }
                );
            }
        } else {
            btn.classList.remove('active');
        }
    });
}

// Load options based on type with animation
function loadOptionsForType(type) {
    let optionsHTML = '';

    if (type === 'text') {
        optionsHTML = `
            <div class="option-group">
                <label class="text-lg font-semibold text-gray-700">Method</label>
                <div class="flex gap-4 flex-wrap mt-3">
                    <label class="flex items-center gap-3 cursor-pointer group">
                        <input type="radio" name="textMethod" value="keyword" checked class="w-5 h-5 text-purple-600">
                        <span class="text-gray-700 group-hover:text-purple-600 transition-colors font-medium">Search by Keyword</span>
                    </label>
                    <label class="flex items-center gap-3 cursor-pointer group">
                        <input type="radio" name="textMethod" value="ai" class="w-5 h-5 text-purple-600">
                        <span class="text-gray-700 group-hover:text-purple-600 transition-colors font-medium">AI Topic Query</span>
                    </label>
                </div>
            </div>
            <div class="option-group" id="textKeywordGroup">
                <label for="textKeyword" class="text-lg font-semibold text-gray-700">Keyword</label>
                <input type="text" id="textKeyword" placeholder="e.g., about us, notice, alert" class="mt-2">
            </div>
            <div class="option-group hidden" id="textAIGroup">
                <label for="textTopicQuery" class="text-lg font-semibold text-gray-700">AI Topic Query</label>
                <textarea id="textTopicQuery" placeholder="Examples:
- Extract all results from the Results section
- Get all job listings from Latest Jobs
- Extract admit cards from the Admit Cards section
- Summarize the latest developments on Tesla's Gigafactories
- Get all notifications from the website" class="mt-2"></textarea>
                <small class="text-gray-500 mt-2 block">
                    AI will automatically detect and extract text content or result lists based on your query. Perfect for extracting results, jobs, admit cards, and other structured data. API key will be used from config.py
                </small>
            </div>
        `;
    } else if (type === 'image') {
        optionsHTML = `
            <div class="option-group">
                <label class="text-lg font-semibold text-gray-700">Method</label>
                <div class="flex gap-4 flex-wrap mt-3">
                    <label class="flex items-center gap-3 cursor-pointer group">
                        <input type="radio" name="imageMethod" value="keyword" checked class="w-5 h-5 text-purple-600">
                        <span class="text-gray-700 group-hover:text-purple-600 transition-colors font-medium">Search by Keyword</span>
                    </label>
                    <label class="flex items-center gap-3 cursor-pointer group">
                        <input type="radio" name="imageMethod" value="list_all" class="w-5 h-5 text-purple-600">
                        <span class="text-gray-700 group-hover:text-purple-600 transition-colors font-medium">List All Images</span>
                    </label>
                </div>
            </div>
            <div class="option-group" id="imageKeywordGroup">
                <label for="imageKeyword" class="text-lg font-semibold text-gray-700">Keyword</label>
                <input type="text" id="imageKeyword" placeholder="e.g., logo, product, banner" class="mt-2">
            </div>
        `;
    } else if (type === 'link') {
        optionsHTML = `
            <div class="option-group">
                <label for="linkKeyword" class="text-lg font-semibold text-gray-700">Keyword</label>
                <input type="text" id="linkKeyword" placeholder="e.g., contact, buy, cart" class="mt-2">
            </div>
        `;
    } else if (type === 'card') {
        optionsHTML = `
            <div class="option-group">
                <label class="text-lg font-semibold text-gray-700">Auto-detection</label>
                <p class="text-gray-600 mt-2 bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                    The scraper will automatically detect card-based layouts on the page.
                </p>
            </div>
        `;
    }

    // Animate transition only if GSAP is available
    if (typeof gsap !== 'undefined') {
        gsap.to(optionsContent, {
            opacity: 0,
            duration: 0.2,
            onComplete: () => {
                optionsContent.innerHTML = optionsHTML;
                setupOptionListeners();
                gsap.to(optionsContent, { opacity: 1, duration: 0.3 });
            }
        });
    } else {
        optionsContent.innerHTML = optionsHTML;
        setupOptionListeners();
    }
}

// Setup option listeners for dynamic option groups
function setupOptionListeners() {
    // Text method listeners
    const textMethods = document.querySelectorAll('input[name="textMethod"]');
    textMethods.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const keywordGroup = document.getElementById('textKeywordGroup');
            const aiGroup = document.getElementById('textAIGroup');
            
            if (typeof gsap !== 'undefined') {
                if (e.target.value === 'keyword') {
                    gsap.to(aiGroup, { height: 0, opacity: 0, duration: 0.3, onComplete: () => aiGroup.classList.add('hidden') });
                    keywordGroup.classList.remove('hidden');
                    gsap.fromTo(keywordGroup, { height: 0, opacity: 0 }, { height: 'auto', opacity: 1, duration: 0.3 });
                } else {
                    gsap.to(keywordGroup, { height: 0, opacity: 0, duration: 0.3, onComplete: () => keywordGroup.classList.add('hidden') });
                    aiGroup.classList.remove('hidden');
                    gsap.fromTo(aiGroup, { height: 0, opacity: 0 }, { height: 'auto', opacity: 1, duration: 0.3 });
                }
            } else {
                // Fallback without animations
                if (e.target.value === 'keyword') {
                    aiGroup.classList.add('hidden');
                    keywordGroup.classList.remove('hidden');
                } else {
                    keywordGroup.classList.add('hidden');
                    aiGroup.classList.remove('hidden');
                }
            }
        });
    });

    // Image method listeners
    const imageMethods = document.querySelectorAll('input[name="imageMethod"]');
    imageMethods.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const keywordGroup = document.getElementById('imageKeywordGroup');
            if (typeof gsap !== 'undefined') {
                if (e.target.value === 'keyword') {
                    keywordGroup.classList.remove('hidden');
                    gsap.fromTo(keywordGroup, { height: 0, opacity: 0 }, { height: 'auto', opacity: 1, duration: 0.3 });
                } else {
                    gsap.to(keywordGroup, { height: 0, opacity: 0, duration: 0.3, onComplete: () => keywordGroup.classList.add('hidden') });
                }
            } else {
                // Fallback without animations
                if (e.target.value === 'keyword') {
                    keywordGroup.classList.remove('hidden');
                } else {
                    keywordGroup.classList.add('hidden');
                }
            }
        });
    });
}

// Handle scrape
async function handleScrape() {
    const url = urlInput.value.trim();
    if (!url) {
        showError('Please enter a URL');
        return;
    }

    // Hide previous results and errors
    hideResults();
    hideError();

    // Show loading
    showLoading();

    // Get options
    const options = getOptions();

    // Make API request
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                type: currentScrapeType,
                options: options
            })
        });

        const data = await response.json();

        hideLoading();

        if (data.success) {
            currentResults = data.data;
            displayResults(data.data);
        } else {
            showError(data.error || 'An error occurred while scraping');
        }
    } catch (error) {
        hideLoading();
        showError('Network error: ' + error.message);
    }
}

// Get options based on current type
function getOptions() {
    const options = {};

    if (currentScrapeType === 'text') {
        const method = document.querySelector('input[name="textMethod"]:checked').value;
        options.method = method;
        if (method === 'keyword') {
            options.keyword = document.getElementById('textKeyword').value;
        } else if (method === 'ai') {
            options.topic_query = document.getElementById('textTopicQuery').value;
        }
    } else if (currentScrapeType === 'image') {
        const method = document.querySelector('input[name="imageMethod"]:checked').value;
        options.method = method;
        if (method === 'keyword') {
            options.keyword = document.getElementById('imageKeyword').value;
        }
    } else if (currentScrapeType === 'link') {
        options.method = 'keyword';
        options.keyword = document.getElementById('linkKeyword').value;
    } else if (currentScrapeType === 'card') {
        // Auto-detection, no options needed
    }

    return options;
}

// Display results with animation
function displayResults(data) {
    console.log('Display Results - Raw data:', data);
    console.log('Current scrape type:', currentScrapeType);
    
    if (!data || (Array.isArray(data) && data.length === 0)) {
        showError('No results found');
        return;
    }

    let html = '';

    // Check if data is a result list (array of objects with title/link) or regular text
    const isResultList = Array.isArray(data) && data.length > 0 && typeof data[0] === 'object' && 
                        data[0] !== null &&
                        (data.length > 1 || (data[0].hasOwnProperty('link') && data[0].link && data[0].link.trim() !== ''));
    
    if (isResultList) {
        // Display as result list
        data.forEach((item, index) => {
            const title = item.title || item.text || 'No title';
            html += `
                <div class="result-list-item" style="animation-delay: ${index * 0.05}s">
                    <strong class="text-lg">${index + 1}. ${title}</strong>
                    ${item.status ? `<span class="inline-block px-3 py-1 bg-yellow-400 text-white rounded-full text-sm ml-2">${item.status}</span>` : ''}
                    ${item.link && item.link.trim() ? `<p class="mt-2"><a href="${item.link}" target="_blank" rel="noopener noreferrer" class="text-purple-600 hover:text-purple-800 underline break-all">${item.link}</a></p>` : ''}
                    ${item.text && item.text !== title && !item.link ? `<p class="text-gray-600 mt-2">${item.text}</p>` : ''}
                </div>
            `;
        });
    } else if (currentScrapeType === 'card') {
        // Display as cards
        data.forEach((card, index) => {
            html += `
                <div class="result-item" style="animation-delay: ${index * 0.05}s">
                    <h3 class="text-xl font-bold mb-3">Card ${index + 1}: ${card.title || 'No title'}</h3>
                    ${card.description ? `<p class="text-gray-600 mb-2">${card.description}</p>` : ''}
                    ${card.link ? `<p class="mb-2"><a href="${card.link}" target="_blank" rel="noopener noreferrer" class="text-purple-600 hover:text-purple-800 underline break-all">${card.link}</a></p>` : ''}
                    ${card.image ? `<img src="${card.image}" alt="${card.title || 'Image'}" class="rounded-lg shadow-lg mt-3" onerror="this.style.display='none'">` : ''}
                </div>
            `;
        });
    } else if (currentScrapeType === 'image') {
        // Display images with actual image preview and download buttons
        console.log('Image data received:', data);
        const images = Array.isArray(data) ? data : [data];
        console.log('Images array:', images);
        
        if (images.length === 0 || (images.length === 1 && !images[0])) {
            showError('No images found');
            return;
        }
        
        images.forEach((img, index) => {
            // Handle if img is a string URL or object
            let imageUrl = '';
            if (typeof img === 'string') {
                imageUrl = img;
            } else if (typeof img === 'object' && img !== null) {
                imageUrl = img.src || img.url || img.href || img.image || '';
            }
            
            // Skip if no valid URL
            if (!imageUrl || imageUrl.trim() === '') {
                console.log('Skipping invalid image at index', index, img);
                return;
            }
            
            const safeUrl = imageUrl.replace(/'/g, "\\'");
            console.log(`Rendering image ${index + 1}:`, imageUrl);
            
            html += `
                <div class="result-item" style="animation-delay: ${index * 0.05}s">
                    <h3 class="text-xl font-bold mb-3">Image ${index + 1}</h3>
                    <div class="mb-3 bg-gray-100 rounded-lg p-4 text-center">
                        <img src="${imageUrl}" 
                             alt="Scraped image ${index + 1}" 
                             class="rounded-lg shadow-lg mx-auto" 
                             style="max-height: 400px; max-width: 100%; object-fit: contain;"
                             onerror="this.onerror=null; this.parentElement.innerHTML='<p class=\"text-red-500 font-semibold\">⚠️ Image failed to load<br><small class=\"text-gray-600\">${imageUrl}</small></p>';">
                    </div>
                    <div class="flex gap-3 mt-3 flex-wrap justify-center">
                        <a href="${imageUrl}" 
                           target="_blank" 
                           rel="noopener noreferrer" 
                           class="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-semibold shadow-lg">
                            <i class="fas fa-external-link-alt"></i>
                            <span>View Original</span>
                        </a>
                        <button onclick="downloadImage('${safeUrl}', 'image_${index + 1}.jpg')" 
                                class="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold shadow-lg">
                            <i class="fas fa-download"></i>
                            <span>Download JPG</span>
                        </button>
                    </div>
                    <p class="text-xs text-gray-500 mt-2 break-all text-center">${imageUrl}</p>
                </div>
            `;
        });
        
        if (html === '') {
            showError('No valid image URLs found in the results');
            return;
        }
    } else {
        // Display as text items
        const items = Array.isArray(data) ? data : [data];
        items.forEach((item, index) => {
            let content = '';
            let title = `Result ${index + 1}`;
            
            if (typeof item === 'string') {
                content = item;
            } else if (typeof item === 'object' && item !== null) {
                if (item.text) {
                    content = item.text;
                    if (item.title) {
                        title = item.title;
                    }
                } else {
                    content = JSON.stringify(item, null, 2);
                }
            } else {
                content = String(item);
            }
            
            html += `
                <div class="result-item" style="animation-delay: ${index * 0.05}s">
                    <h3 class="text-xl font-bold mb-3">${escapeHtml(title)}</h3>
                    <p class="whitespace-pre-wrap break-words text-gray-700">${escapeHtml(content)}</p>
                </div>
            `;
        });
    }
    
    resultsContent.innerHTML = html;
    showResults();
    
    // Animate result items only if GSAP is available
    if (typeof gsap !== 'undefined') {
        gsap.from('.result-item, .result-list-item', {
            opacity: 0,
            y: 30,
            stagger: 0.1,
            duration: 0.5,
            ease: 'power2.out'
        });
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show/hide sections with animations
function showLoading() {
    loadingSection.classList.remove('hidden');
    if (typeof gsap !== 'undefined') {
        gsap.fromTo(loadingSection, 
            { opacity: 0, scale: 0.9 },
            { opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(1.7)' }
        );
    }
    scrapeBtn.disabled = true;
}

function hideLoading() {
    if (typeof gsap !== 'undefined') {
        gsap.to(loadingSection, {
            opacity: 0,
            scale: 0.9,
            duration: 0.3,
            onComplete: () => loadingSection.classList.add('hidden')
        });
    } else {
        loadingSection.classList.add('hidden');
    }
    scrapeBtn.disabled = false;
}

function showResults() {
    resultsSection.classList.remove('hidden');
    if (typeof gsap !== 'undefined') {
        gsap.fromTo(resultsSection,
            { opacity: 0, y: 50 },
            { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
        );
    }
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideResults() {
    if (typeof gsap !== 'undefined') {
        gsap.to(resultsSection, {
            opacity: 0,
            y: 30,
            duration: 0.3,
            onComplete: () => resultsSection.classList.add('hidden')
        });
    } else {
        resultsSection.classList.add('hidden');
    }
}

function showError(message) {
    errorContent.textContent = message;
    errorSection.classList.remove('hidden');
    if (typeof gsap !== 'undefined') {
        gsap.fromTo(errorSection,
            { opacity: 0, x: -50 },
            { opacity: 1, x: 0, duration: 0.5, ease: 'power2.out' }
        );
    }
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
    if (typeof gsap !== 'undefined') {
        gsap.to(errorSection, {
            opacity: 0,
            x: -50,
            duration: 0.3,
            onComplete: () => errorSection.classList.add('hidden')
        });
    } else {
        errorSection.classList.add('hidden');
    }
}

// Handle export
async function handleExport() {
    if (!currentResults) {
        showError('No results to export');
        return;
    }

    try {
        const filename = prompt('Enter filename (without extension):', `scraped_data_${new Date().getTime()}`);
        if (!filename) return;

        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: currentResults,
                filename: filename
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Data exported successfully to ${data.filename}`);
            window.open(`/api/download/${data.filename.split('/').pop()}`, '_blank');
        } else {
            showError(data.error || 'Failed to export data');
        }
    } catch (error) {
        showError('Export error: ' + error.message);
    }
}

// Handle PDF export
function handleExportPdf() {
    if (!currentResults) {
        showError('No results to export');
        return;
    }

    try {
        // Check if jsPDF is loaded
        if (typeof window.jspdf === 'undefined') {
            showError('PDF library not loaded. Please refresh the page.');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Title
        doc.setFontSize(20);
        doc.setTextColor(99, 102, 241);
        doc.text('Web Scraper Results', 15, 20);
        
        // Date
        doc.setFontSize(10);
        doc.setTextColor(100, 100, 100);
        doc.text(`Generated: ${new Date().toLocaleString()}`, 15, 28);
        
        // Scrape type
        doc.setFontSize(12);
        doc.setTextColor(0, 0, 0);
        doc.text(`Type: ${currentScrapeType.toUpperCase()}`, 15, 36);
        
        let yPosition = 45;
        const pageHeight = doc.internal.pageSize.height;
        const marginBottom = 20;
        const lineHeight = 7;
        
        // Process results based on type
        const results = Array.isArray(currentResults) ? currentResults : [currentResults];
        
        results.forEach((item, index) => {
            // Check if we need a new page
            if (yPosition > pageHeight - marginBottom) {
                doc.addPage();
                yPosition = 20;
            }
            
            // Item number
            doc.setFontSize(12);
            doc.setTextColor(139, 92, 246);
            doc.text(`Item ${index + 1}`, 15, yPosition);
            yPosition += lineHeight;
            
            doc.setFontSize(10);
            doc.setTextColor(0, 0, 0);
            
            if (typeof item === 'string') {
                // Simple string result
                const lines = doc.splitTextToSize(item, 180);
                lines.forEach(line => {
                    if (yPosition > pageHeight - marginBottom) {
                        doc.addPage();
                        yPosition = 20;
                    }
                    doc.text(line, 20, yPosition);
                    yPosition += lineHeight;
                });
            } else if (typeof item === 'object' && item !== null) {
                // Object result (card, link, etc.)
                Object.entries(item).forEach(([key, value]) => {
                    if (yPosition > pageHeight - marginBottom) {
                        doc.addPage();
                        yPosition = 20;
                    }
                    
                    // Key in bold
                    doc.setFont(undefined, 'bold');
                    doc.text(`${key}:`, 20, yPosition);
                    doc.setFont(undefined, 'normal');
                    
                    // Value
                    const valueStr = String(value);
                    const lines = doc.splitTextToSize(valueStr, 150);
                    
                    if (lines.length === 1) {
                        doc.text(lines[0], 50, yPosition);
                        yPosition += lineHeight;
                    } else {
                        yPosition += lineHeight;
                        lines.forEach(line => {
                            if (yPosition > pageHeight - marginBottom) {
                                doc.addPage();
                                yPosition = 20;
                            }
                            doc.text(line, 25, yPosition);
                            yPosition += lineHeight;
                        });
                    }
                });
            }
            
            yPosition += 5; // Extra space between items
        });
        
        // Save the PDF
        const filename = `scraped_data_${new Date().getTime()}.pdf`;
        doc.save(filename);
        
        // Show success message
        if (typeof gsap !== 'undefined') {
            const message = document.createElement('div');
            message.textContent = '✅ PDF downloaded successfully!';
            message.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:16px 24px;border-radius:12px;font-weight:600;z-index:9999;box-shadow:0 10px 40px rgba(0,0,0,0.3);';
            document.body.appendChild(message);
            
            gsap.fromTo(message, 
                { x: 100, opacity: 0 },
                { x: 0, opacity: 1, duration: 0.5, ease: 'back.out' }
            );
            
            setTimeout(() => {
                gsap.to(message, {
                    x: 100,
                    opacity: 0,
                    duration: 0.3,
                    onComplete: () => message.remove()
                });
            }, 3000);
        } else {
            alert('PDF downloaded successfully!');
        }
        
    } catch (error) {
        console.error('PDF export error:', error);
        showError('Failed to export PDF: ' + error.message);
    }
}

// Handle clear with animation
function handleClear() {
    if (typeof gsap !== 'undefined') {
        gsap.to([resultsSection, errorSection], {
            opacity: 0,
            y: 20,
            duration: 0.3,
            onComplete: () => {
                currentResults = null;
                hideResults();
                hideError();
                urlInput.value = '';
                resultsContent.innerHTML = '';
                
                urlInput.focus();
                gsap.fromTo(urlInput, 
                    { scale: 1 },
                    { scale: 1.05, duration: 0.2, yoyo: true, repeat: 1 }
                );
            }
        });
    } else {
        currentResults = null;
        hideResults();
        hideError();
        urlInput.value = '';
        resultsContent.innerHTML = '';
        urlInput.focus();
    }
}

// Download image function
function downloadImage(imageUrl, filename) {
    console.log('Downloading:', imageUrl);
    
    // Try fetching the image first
    fetch(imageUrl, {
        mode: 'cors',
        credentials: 'omit'
    })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.blob();
        })
        .then(blob => {
            // Create object URL from blob
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up the blob URL after a short delay
            setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
            
            // Show success message
            console.log('Download started:', filename);
        })
        .catch(error => {
            console.log('Fetch failed, trying direct download...', error);
            // Fallback: try opening in new tab with download attribute
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = filename;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
}
