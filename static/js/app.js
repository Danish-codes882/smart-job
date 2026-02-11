class CareerIntel {
    static config = {
        apiBaseUrl: '/api/v1',
        currentTheme: 'corporate-light',
        userData: null
    };

    static init() {
        this.loadConfig();
        this.setupEventListeners();
        this.initializeUI();
        console.log('CareerIntel initialized');
    }

    static loadConfig() {
        const savedTheme = localStorage.getItem('careerintel_theme');
        if (savedTheme) {
            this.config.currentTheme = savedTheme;
        }
        
        const savedData = localStorage.getItem('careerintel_user');
        if (savedData) {
            this.config.userData = JSON.parse(savedData);
        }
    }

    static setTheme(themeName) {
        const themeCSS = document.getElementById('theme-css');
        if (themeCSS) {
            themeCSS.href = `/static/css/themes/${themeName}.css`;
            document.documentElement.setAttribute('data-theme', themeName);
            this.config.currentTheme = themeName;
            localStorage.setItem('careerintel_theme', themeName);
            
            // Update theme selector if exists
            const selector = document.getElementById('theme-selector');
            if (selector) {
                selector.value = themeName;
            }
        }
    }

    static async searchJobs(query, location = '', remote = false) {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.config.apiBaseUrl}/jobs/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    location: location,
                    remote: remote,
                    sources: ['linkedin', 'indeed']
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayJobs(data.jobs);
                this.updateStats(data.jobs);
                return data;
            } else {
                throw new Error(data.error || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Failed to search jobs. Please try again.');
            return null;
        } finally {
            this.hideLoading();
        }
    }

    static async analyzeCV(cvData) {
        try {
            this.showLoading('Analyzing CV...');
            
            const formData = new FormData();
            if (cvData.file) {
                formData.append('cv_file', cvData.file);
            } else if (cvData.text) {
                formData.append('cv_text', cvData.text);
            }
            
            const response = await fetch(`${this.config.apiBaseUrl}/cv/analyze`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayCVAnalysis(data.analysis);
                return data;
            } else {
                throw new Error(data.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('CV analysis error:', error);
            this.showError('Failed to analyze CV. Please try again.');
            return null;
        } finally {
            this.hideLoading();
        }
    }

    static displayJobs(jobs) {
        const container = document.getElementById('jobs-container');
        if (!container) return;
        
        if (!jobs || jobs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search fa-3x"></i>
                    <h3>No jobs found</h3>
                    <p>Try adjusting your search criteria</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        jobs.forEach(job => {
            html += `
                <div class="job-card">
                    <div class="job-header">
                        <div class="company-logo">
                            <i class="fas fa-building"></i>
                        </div>
                        <div class="job-meta">
                            ${job.match_score ? `<span class="match-badge">${job.match_score}% Match</span>` : ''}
                            <button class="bookmark-btn" onclick="CareerIntel.toggleBookmark(this)">
                                <i class="far fa-bookmark"></i>
                            </button>
                        </div>
                    </div>
                    <h3 class="job-title">${this.escapeHtml(job.title)}</h3>
                    <p class="company-name">${this.escapeHtml(job.company)}</p>
                    <div class="job-details">
                        <span><i class="fas fa-map-marker-alt"></i> ${this.escapeHtml(job.location)}</span>
                        <span><i class="fas fa-home"></i> ${job.work_mode || 'Not specified'}</span>
                        <span><i class="fas fa-clock"></i> ${job.posted_date || 'Recently'}</span>
                    </div>
                    <div class="job-actions">
                        <button class="btn-primary" onclick="CareerIntel.applyJob('${this.escapeHtml(job.apply_url || '')}')">
                            Apply Now
                        </button>
                        <button class="btn-secondary" onclick="CareerIntel.viewJobDetails(${JSON.stringify(job).replace(/'/g, "\\'")})">
                            View Details
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    static displayCVAnalysis(analysis) {
        // Update CV score display
        const scoreDisplay = document.getElementById('cv-score-display');
        if (scoreDisplay) {
            scoreDisplay.textContent = analysis.overall_score || 0;
        }
        
        // Update CV score arc
        const scoreArc = document.getElementById('score-arc');
        if (scoreArc && analysis.overall_score) {
            const percentage = analysis.overall_score;
            const offset = 314 - (percentage * 314) / 100;
            scoreArc.style.strokeDashoffset = offset;
        }
        
        // Update recommendations
        const recContainer = document.getElementById('cv-recommendations');
        if (recContainer && analysis.recommendations) {
            let html = '';
            analysis.recommendations.forEach(rec => {
                html += `<li><i class="fas fa-exclamation-circle"></i> ${this.escapeHtml(rec)}</li>`;
            });
            recContainer.innerHTML = html;
        }
        
        // Update stats
        const cvScoreElement = document.getElementById('cv-score');
        if (cvScoreElement) {
            cvScoreElement.textContent = `${analysis.overall_score || 0}/100`;
        }
    }

    static updateStats(jobs) {
        const totalJobs = jobs.length;
        const remoteJobs = jobs.filter(job => 
            job.work_mode && job.work_mode.toLowerCase().includes('remote')
        ).length;
        
        // Update UI elements
        const jobsCount = document.getElementById('jobs-count');
        if (jobsCount) {
            jobsCount.textContent = totalJobs;
        }
        
        const remoteJobsElement = document.getElementById('remote-jobs');
        if (remoteJobsElement) {
            remoteJobsElement.textContent = remoteJobs;
        }
        
        // Calculate average match score
        const jobsWithScores = jobs.filter(job => job.match_score);
        if (jobsWithScores.length > 0) {
            const avgScore = jobsWithScores.reduce((sum, job) => sum + job.match_score, 0) / jobsWithScores.length;
            const matchScoreElement = document.getElementById('match-score');
            const matchProgressElement = document.getElementById('match-progress');
            
            if (matchScoreElement) {
                matchScoreElement.textContent = `${Math.round(avgScore)}%`;
            }
            if (matchProgressElement) {
                matchProgressElement.style.width = `${avgScore}%`;
            }
        }
    }

    static applyJob(url) {
        if (url) {
            window.open(url, '_blank');
        } else {
            this.showError('No apply URL available for this job');
        }
    }

    static viewJobDetails(job) {
        // Create and show job details modal
        const modal = this.createJobDetailsModal(job);
        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }

    static createJobDetailsModal(job) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'job-details-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${this.escapeHtml(job.title)}</h3>
                    <button class="modal-close" onclick="this.closest('.modal').style.display='none'">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="job-details-full">
                        <div class="detail-row">
                            <strong>Company:</strong> ${this.escapeHtml(job.company)}
                        </div>
                        <div class="detail-row">
                            <strong>Location:</strong> ${this.escapeHtml(job.location)}
                        </div>
                        <div class="detail-row">
                            <strong>Work Mode:</strong> ${job.work_mode || 'Not specified'}
                        </div>
                        <div class="detail-row">
                            <strong>Posted:</strong> ${job.posted_date || 'Recently'}
                        </div>
                        <div class="detail-row">
                            <strong>Source:</strong> ${job.source || 'Unknown'}
                        </div>
                        ${job.match_score ? `
                        <div class="detail-row">
                            <strong>Match Score:</strong> ${job.match_score}%
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.modal').style.display='none'">Close</button>
                    <button class="btn-primary" onclick="CareerIntel.applyJob('${this.escapeHtml(job.apply_url || '')}')">
                        Apply Now
                    </button>
                </div>
            </div>
        `;
        return modal;
    }

    static toggleBookmark(button) {
        const icon = button.querySelector('i');
        if (icon.classList.contains('far')) {
            icon.classList.remove('far');
            icon.classList.add('fas');
            this.showSuccess('Job bookmarked');
        } else {
            icon.classList.remove('fas');
            icon.classList.add('far');
            this.showInfo('Bookmark removed');
        }
    }

    static showLoading(message = 'Loading...') {
        let loading = document.getElementById('loading-overlay');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'loading-overlay';
            loading.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            `;
            loading.innerHTML = `
                <div style="background: white; padding: 2rem; border-radius: 8px; text-align: center;">
                    <div class="loading-spinner" style="border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem;"></div>
                    <p>${message}</p>
                </div>
            `;
            document.body.appendChild(loading);
            
            // Add spin animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        } else {
            loading.style.display = 'flex';
        }
    }

    static hideLoading() {
        const loading = document.getElementById('loading-overlay');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    static showError(message, duration = 5000) {
        this.showNotification(message, 'error', duration);
    }

    static showSuccess(message, duration = 3000) {
        this.showNotification(message, 'success', duration);
    }

    static showInfo(message, duration = 3000) {
        this.showNotification(message, 'info', duration);
    }

    static showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        const colors = {
            error: '#ef4444',
            success: '#10b981',
            info: '#3b82f6',
            warning: '#f59e0b'
        };
        
        notification.style.background = colors[type] || colors.info;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static setupEventListeners() {
        // Global search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && globalSearch.value.trim()) {
                    this.searchJobs(globalSearch.value.trim());
                }
            });
        }
        
        // CV file upload
        const cvFileInput = document.getElementById('cv-file');
        if (cvFileInput) {
            cvFileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.analyzeCV({ file: file });
                }
            });
        }
        
        // Drop zone for CV
        const dropZone = document.getElementById('drop-zone');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#3b82f6';
                dropZone.style.background = 'rgba(59, 130, 246, 0.05)';
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '';
                dropZone.style.background = '';
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '';
                dropZone.style.background = '';
                
                const file = e.dataTransfer.files[0];
                if (file && (file.type === 'application/pdf' || 
                             file.type === 'application/msword' ||
                             file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                             file.type === 'text/plain')) {
                    this.analyzeCV({ file: file });
                } else {
                    this.showError('Please upload a PDF, DOC, DOCX, or TXT file');
                }
            });
        }
    }

    static initializeUI() {
        // Set theme
        this.setTheme(this.config.currentTheme);
        
        // Set current year in footer if exists
        const yearElement = document.getElementById('current-year');
        if (yearElement) {
            yearElement.textContent = new Date().getFullYear();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CareerIntel.init();
});

// Global functions for HTML onclick handlers
function performSearch() {
    const searchInput = document.getElementById('global-search');
    if (searchInput && searchInput.value.trim()) {
        CareerIntel.searchJobs(searchInput.value.trim());
    }
}

function analyzeCV() {
    document.getElementById('cv-modal').style.display = 'block';
}

function analyzeUploadedCV() {
    const cvText = document.getElementById('cv-text');
    const cvFile = document.getElementById('cv-file');
    
    if (cvFile.files.length > 0) {
        CareerIntel.analyzeCV({ file: cvFile.files[0] });
        document.getElementById('cv-modal').style.display = 'none';
    } else if (cvText && cvText.value.trim()) {
        CareerIntel.analyzeCV({ text: cvText.value.trim() });
        document.getElementById('cv-modal').style.display = 'none';
    } else {
        CareerIntel.showError('Please upload a file or paste your CV text');
    }
}

function changeTheme(themeName) {
    CareerIntel.setTheme(themeName);
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function showSearchModal() {
    document.getElementById('search-modal').style.display = 'block';
}

function performAdvancedSearch() {
    const query = document.getElementById('search-query').value;
    const location = document.getElementById('search-location').value;
    const remote = document.getElementById('search-remote').checked;
    
    if (query.trim()) {
        CareerIntel.searchJobs(query.trim(), location.trim(), remote);
        document.getElementById('search-modal').style.display = 'none';
    } else {
        CareerIntel.showError('Please enter a job title or keywords');
    }
}

function improveCV() {
    CareerIntel.showInfo('CV improvement feature coming soon!');
}
