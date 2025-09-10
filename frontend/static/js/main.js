// Main Application Logic
class PharmaQueryApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.datasets = [];
        this.queryHistory = [];
        this.currentQuery = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.switchSection('dashboard');
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.switchSection(section);
            });
        });
        
        // File upload
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleFileSelect(e);
        });
        
        // Refresh buttons
        document.getElementById('refreshDatasets')?.addEventListener('click', () => {
            this.loadDatasets();
        });
        
        document.getElementById('refreshHistory')?.addEventListener('click', () => {
            this.loadQueryHistory();
        });
        
        // Query execution
        document.getElementById('executeQueryBtn')?.addEventListener('click', () => {
            this.executeQuery();
        });
        
        // Modal close
        document.getElementById('modalOverlay')?.addEventListener('click', (e) => {
            if (e.target.id === 'modalOverlay') {
                this.closeModal();
            }
        });
        
        // Help button
        document.getElementById('helpBtn')?.addEventListener('click', () => {
            this.showHelp();
        });
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadDatasets(),
                this.loadQueryHistory()
            ]);
            this.updateDashboard();
        } catch (error) {
            console.error('Error loading initial data:', error);
            UI.showToast('Error loading data', 'error');
        }
    }
    
    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${sectionName}-section`).classList.add('active');
        
        this.currentSection = sectionName;
        
        // Load section-specific data
        if (sectionName === 'datasets') {
            this.loadDatasets();
        } else if (sectionName === 'query') {
            this.updateQueryDatasetsList();
        } else if (sectionName === 'history') {
            this.loadQueryHistory();
        } else if (sectionName === 'dashboard') {
            this.updateDashboard();
        }
    }
    
    async loadDatasets() {
        try {
            UI.showLoading('datasetsList');
            const response = await API.getDatasets();
            
            if (response.success) {
                this.datasets = response.datasets;
                this.renderDatasetsList();
                this.updateQueryDatasetsList();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Error loading datasets:', error);
            UI.showError('datasetsList', 'Failed to load datasets');
            UI.showToast('Failed to load datasets', 'error');
        }
    }
    
    renderDatasetsList() {
        const container = document.getElementById('datasetsList');
        
        if (this.datasets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plus-circle"></i>
                    <p>No datasets uploaded yet. Upload your first dataset above.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.datasets.map(dataset => `
            <div class="dataset-item" data-id="${dataset.id}">
                <div class="dataset-info">
                    <h4>${dataset.name}</h4>
                    <div class="dataset-meta">
                        <span><i class="fas fa-table"></i> ${dataset.rows.toLocaleString()} rows</span>
                        <span><i class="fas fa-columns"></i> ${dataset.columns} columns</span>
                        <span><i class="fas fa-calendar"></i> ${new Date(dataset.upload_date).toLocaleDateString()}</span>
                        <span><i class="fas fa-weight"></i> ${this.formatFileSize(dataset.size_bytes)}</span>
                    </div>
                </div>
                <div class="dataset-actions">
                    <button class="action-icon" onclick="app.previewDataset('${dataset.id}')" title="Preview">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-icon" onclick="app.showDatasetStats('${dataset.id}')" title="Statistics">
                        <i class="fas fa-chart-bar"></i>
                    </button>
                    <button class="action-icon" onclick="app.renameDataset('${dataset.id}')" title="Rename">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-icon danger" onclick="app.deleteDataset('${dataset.id}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    updateQueryDatasetsList() {
        const container = document.getElementById('queryDatasetsList');
        
        if (this.datasets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No datasets available. <a href="#" onclick="app.switchSection('datasets')">Upload datasets first</a></p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.datasets.map(dataset => `
            <div class="dataset-checkbox" onclick="app.toggleDatasetSelection('${dataset.id}')">
                <input type="checkbox" id="dataset-${dataset.id}" value="${dataset.id}">
                <label for="dataset-${dataset.id}">
                    <strong>${dataset.name}</strong>
                    <small>(${dataset.rows.toLocaleString()} rows, ${dataset.columns} columns)</small>
                </label>
            </div>
        `).join('');
    }
    
    toggleDatasetSelection(datasetId) {
        const checkbox = document.getElementById(`dataset-${datasetId}`);
        const container = checkbox.closest('.dataset-checkbox');
        
        checkbox.checked = !checkbox.checked;
        container.classList.toggle('selected', checkbox.checked);
    }
    
    getSelectedDatasets() {
        return Array.from(document.querySelectorAll('#queryDatasetsList input[type="checkbox"]:checked'))
            .map(cb => cb.value);
    }
    
    async handleFileSelect(event) {
        const files = event.dataTransfer ? event.dataTransfer.files : event.target.files;
        
        for (const file of files) {
            await this.uploadFile(file);
        }
        
        // Clear file input
        document.getElementById('fileInput').value = '';
    }
    
    async uploadFile(file) {
        const progressContainer = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const uploadStatus = document.getElementById('uploadStatus');
        
        try {
            progressContainer.style.display = 'block';
            uploadStatus.textContent = `Uploading ${file.name}...`;
            progressFill.style.width = '0%';
            
            // Simulate progress
            const progressInterval = setInterval(() => {
                const currentWidth = parseInt(progressFill.style.width) || 0;
                if (currentWidth < 90) {
                    progressFill.style.width = (currentWidth + 10) + '%';
                }
            }, 200);
            
            const response = await API.uploadDataset(file);
            
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            
            if (response.success) {
                uploadStatus.textContent = 'Upload successful!';
                UI.showToast(`Successfully uploaded ${file.name}`, 'success');
                
                // Refresh datasets
                await this.loadDatasets();
                
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 2000);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Upload error:', error);
            uploadStatus.textContent = 'Upload failed';
            UI.showToast(`Failed to upload ${file.name}: ${error.message}`, 'error');
            
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 3000);
        }
    }
    
    async previewDataset(datasetId) {
        try {
            const response = await API.getDatasetPreview(datasetId);
            
            if (response.success) {
                const dataset = this.datasets.find(d => d.id === datasetId);
                this.showModal('Dataset Preview', this.renderDatasetPreview(dataset, response.preview));
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Preview error:', error);
            UI.showToast('Failed to load dataset preview', 'error');
        }
    }
    
    renderDatasetPreview(dataset, preview) {
        return `
            <div class="dataset-preview">
                <div class="preview-info">
                    <h4>${dataset.name}</h4>
                    <p>Showing first 5 rows of ${preview.total_rows.toLocaleString()} total rows</p>
                </div>
                <div class="result-table">
                    <table>
                        <thead>
                            <tr>
                                ${preview.columns.map(col => `<th>${col}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${preview.data.map(row => `
                                <tr>
                                    ${preview.columns.map(col => `<td>${row[col] || ''}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    async showDatasetStats(datasetId) {
        try {
            const response = await API.getDatasetStats(datasetId);
            
            if (response.success) {
                const dataset = this.datasets.find(d => d.id === datasetId);
                this.showModal('Dataset Statistics', this.renderDatasetStats(dataset, response.stats));
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Stats error:', error);
            UI.showToast('Failed to load dataset statistics', 'error');
        }
    }
    
    renderDatasetStats(dataset, stats) {
        return `
            <div class="dataset-stats">
                <h4>${dataset.name} - Statistics</h4>
                
                <div class="stats-section">
                    <h5>Basic Information</h5>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-label">Rows:</span>
                            <span class="stat-value">${stats.basic_info.rows.toLocaleString()}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Columns:</span>
                            <span class="stat-value">${stats.basic_info.columns}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">File Size:</span>
                            <span class="stat-value">${this.formatFileSize(stats.basic_info.size_bytes)}</span>
                        </div>
                    </div>
                </div>
                
                ${Object.keys(stats.numeric_stats).length > 0 ? `
                    <div class="stats-section">
                        <h5>Numeric Columns</h5>
                        <div class="result-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Column</th>
                                        <th>Mean</th>
                                        <th>Median</th>
                                        <th>Std Dev</th>
                                        <th>Min</th>
                                        <th>Max</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(stats.numeric_stats).map(([col, stat]) => `
                                        <tr>
                                            <td>${col}</td>
                                            <td>${stat.mean?.toFixed(2) || 'N/A'}</td>
                                            <td>${stat.median?.toFixed(2) || 'N/A'}</td>
                                            <td>${stat.std?.toFixed(2) || 'N/A'}</td>
                                            <td>${stat.min?.toFixed(2) || 'N/A'}</td>
                                            <td>${stat.max?.toFixed(2) || 'N/A'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : ''}
                
                ${Object.keys(stats.categorical_stats).length > 0 ? `
                    <div class="stats-section">
                        <h5>Categorical Columns</h5>
                        ${Object.entries(stats.categorical_stats).map(([col, stat]) => `
                            <div class="categorical-stat">
                                <h6>${col}</h6>
                                <p>Unique values: ${stat.unique_count}</p>
                                <div class="value-counts">
                                    ${Object.entries(stat.most_common).slice(0, 5).map(([value, count]) => `
                                        <div class="value-count-item">
                                            <span>${value}: ${count}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    async renameDataset(datasetId) {
        const dataset = this.datasets.find(d => d.id === datasetId);
        const newName = prompt('Enter new name for dataset:', dataset.name);
        
        if (newName && newName !== dataset.name) {
            try {
                const response = await API.renameDataset(datasetId, newName);
                
                if (response.success) {
                    UI.showToast('Dataset renamed successfully', 'success');
                    await this.loadDatasets();
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error('Rename error:', error);
                UI.showToast('Failed to rename dataset', 'error');
            }
        }
    }
    
    async deleteDataset(datasetId) {
        const dataset = this.datasets.find(d => d.id === datasetId);
        
        if (confirm(`Are you sure you want to delete "${dataset.name}"? This action cannot be undone.`)) {
            try {
                const response = await API.deleteDataset(datasetId);
                
                if (response.success) {
                    UI.showToast('Dataset deleted successfully', 'success');
                    await this.loadDatasets();
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error('Delete error:', error);
                UI.showToast('Failed to delete dataset', 'error');
            }
        }
    }
    
    async executeQuery() {
        const queryText = document.getElementById('queryInput').value.trim();
        const selectedDatasets = this.getSelectedDatasets();
        
        if (!queryText) {
            UI.showToast('Please enter a query', 'warning');
            return;
        }
        
        if (selectedDatasets.length === 0) {
            UI.showToast('Please select at least one dataset', 'warning');
            return;
        }
        
        const executeBtn = document.getElementById('executeQueryBtn');
        const resultsContainer = document.getElementById('queryResults');
        const resultsContent = document.getElementById('resultsContent');
        
        try {
            executeBtn.disabled = true;
            executeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
            
            const response = await API.executeQuery(queryText, selectedDatasets);
            
            if (response.success) {
                this.currentQuery = response.result;
                this.renderQueryResults(response.result);
                resultsContainer.style.display = 'block';
                UI.showToast('Query executed successfully', 'success');
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Query error:', error);
            UI.showToast(`Query failed: ${error.message}`, 'error');
            resultsContainer.style.display = 'none';
        } finally {
            executeBtn.disabled = false;
            executeBtn.innerHTML = '<i class="fas fa-search"></i> Execute Query';
        }
    }
    
    renderQueryResults(result) {
        console.log('Rendering query results:', result); // Debug log
        const content = document.getElementById('resultsContent');
        
        let html = `
            <div class="result-item">
                <h4>Query: "${result.query}"</h4>
                <div class="result-meta">
                    <span>Executed on: ${new Date(result.timestamp).toLocaleString()}</span>
                    <span>Datasets used: ${result.datasets_used.join(', ')}</span>
                </div>
            </div>
        `;
        
        // Show ONLY the LLM response text (formatted nicely)
        if (result.response && result.response.trim() !== '') {
            console.log('Adding response content'); // Debug log
            html += `
                <div class="result-item">
                    <div class="response-content">
                        ${this.formatResponseText(result.response)}
                    </div>
                </div>
            `;
        }
        
        // Show ONLY visualizations/charts if generated
        const vizIds = []; // Store IDs to use consistently
        if (result.visualizations && result.visualizations.length > 0) {
            console.log('Adding visualizations:', result.visualizations.length); // Debug log
            result.visualizations.forEach((viz, index) => {
                const vizId = `viz-${Date.now()}-${index}`;
                vizIds.push(vizId); // Store the ID
                html += `
                    <div class="result-item">
                        <h4><i class="fas fa-chart-bar"></i> ${viz.title}</h4>
                        <div class="visualization" id="${vizId}">
                            <div class="viz-loading">
                                <i class="fas fa-spinner fa-spin"></i>
                                <span>Rendering chart...</span>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        content.innerHTML = html;
        
        // Render visualizations after DOM update using stored IDs
        if (result.visualizations && result.visualizations.length > 0) {
            result.visualizations.forEach((viz, index) => {
                console.log('Rendering viz:', viz); // Debug log
                this.renderVisualization(viz, vizIds[index]); // Use stored ID
            });
        }
    }
    
    formatResponseText(text) {
        if (!text) return '';
        
        // Convert line breaks to HTML
        return text.replace(/\n/g, '<br>');
    }
    
    renderFormattedResponse(formatted_response) {
        if (!formatted_response) return '';
        
        let html = '<div class="result-item"><h4><i class="fas fa-brain"></i> Analysis</h4>';
        
        if (formatted_response.type === 'structured') {
            html += '<div class="formatted-response">';
            formatted_response.content.forEach(item => {
                switch (item.type) {
                    case 'header':
                        html += `<h5 class="response-header">${item.content}</h5>`;
                        break;
                    case 'paragraph':
                        html += `<p class="response-paragraph">${item.content}</p>`;
                        break;
                    case 'list_item':
                        html += `<div class="response-list-item">${item.content}</div>`;
                        break;
                    default:
                        html += `<p class="response-paragraph">${item.content}</p>`;
                }
            });
            html += '</div>';
        } else {
            html += `<div class="result-text">${formatted_response.content}</div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    renderVisualization(viz, containerId) {
        console.log('renderVisualization called with:', { containerId, viz }); // Debug log
        setTimeout(() => {
            const container = document.getElementById(containerId);
            console.log('Container found:', !!container); // Debug log
            
            if (!container) {
                console.error('Container not found:', containerId);
                return;
            }

            try {
                if (viz.type === 'chart' && viz.url) {
                    // Simple image rendering for PNG charts
                    console.log('Rendering chart from URL:', viz.url);
                    container.innerHTML = `<img src="${viz.url}" style="max-width: 100%; height: auto;" alt="${viz.title}" />`;
                    console.log('Chart image inserted successfully');
                } else if (viz.html) {
                    // Fallback for HTML-based visualizations
                    console.log('Rendering HTML visualization');
                    container.innerHTML = viz.html;
                    console.log('HTML visualization inserted');
                } else {
                    console.error('No renderable content found in viz:', viz);
                    container.innerHTML = `
                        <div class="viz-error">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span>No visualization content available</span>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error rendering visualization:', error);
                container.innerHTML = `
                    <div class="viz-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Error rendering chart: ${error.message}</span>
                    </div>
                `;
            }
        }, 100);
    }
    
    setExampleQuery(query) {
        document.getElementById('queryInput').value = query;
    }
    
    clearResults() {
        document.getElementById('queryResults').style.display = 'none';
        this.currentQuery = null;
    }
    
    async loadQueryHistory() {
        try {
            const response = await API.getQueryHistory();
            
            if (response.success) {
                this.queryHistory = response.history;
                this.renderQueryHistory();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('History error:', error);
            UI.showError('historyList', 'Failed to load query history');
        }
    }
    
    renderQueryHistory() {
        const container = document.getElementById('historyList');
        
        if (this.queryHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <p>No query history available. <a href="#" onclick="app.switchSection('query')">Execute your first query</a></p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.queryHistory.map(item => `
            <div class="history-item">
                <div class="history-info">
                    <h4>${item.query}</h4>
                    <div class="history-meta">
                        ${new Date(item.timestamp).toLocaleString()} • 
                        Datasets: ${item.datasets.join(', ')}
                    </div>
                </div>
                <div class="history-status">
                    <span class="${item.success ? 'status-success' : 'status-error'}">
                        <i class="fas fa-${item.success ? 'check-circle' : 'exclamation-circle'}"></i>
                        ${item.success ? 'Success' : 'Failed'}
                    </span>
                </div>
            </div>
        `).join('');
    }
    
    updateDashboard() {
        // Update stats
        document.getElementById('totalDatasets').textContent = this.datasets.length;
        document.getElementById('totalQueries').textContent = this.queryHistory.length;
        document.getElementById('totalRecords').textContent = this.datasets
            .reduce((sum, dataset) => sum + dataset.rows, 0)
            .toLocaleString();
        
        // Update recent activity
        const lastActivity = this.queryHistory.length > 0 
            ? new Date(this.queryHistory[0].timestamp).toLocaleDateString()
            : 'No recent activity';
        document.getElementById('lastActivity').textContent = lastActivity;
        
        // Update recent datasets
        const recentDatasets = this.datasets.slice(0, 5);
        const recentList = document.getElementById('recentDatasetsList');
        
        if (recentDatasets.length === 0) {
            recentList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-plus-circle"></i>
                    <p>No datasets uploaded yet. <a href="#" onclick="app.switchSection('datasets')">Upload your first dataset</a></p>
                </div>
            `;
        } else {
            recentList.innerHTML = recentDatasets.map(dataset => `
                <div class="dataset-summary">
                    <strong>${dataset.name}</strong>
                    <small>${dataset.rows.toLocaleString()} rows • ${new Date(dataset.upload_date).toLocaleDateString()}</small>
                </div>
            `).join('');
        }
    }
    
    showModal(title, content) {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalContent').innerHTML = content;
        document.getElementById('modalOverlay').classList.add('active');
    }
    
    closeModal() {
        document.getElementById('modalOverlay').classList.remove('active');
    }
    
    showHelp() {
        const helpContent = `
            <div class="help-content">
                <h4>PharmaQuery Help</h4>
                
                <div class="help-section">
                    <h5>Getting Started</h5>
                    <ol>
                        <li>Upload your pharmaceutical datasets (CSV or Excel files)</li>
                        <li>Select datasets you want to query</li>
                        <li>Ask questions in natural language</li>
                        <li>Review results and visualizations</li>
                    </ol>
                </div>
                
                <div class="help-section">
                    <h5>Example Queries</h5>
                    <ul>
                        <li>"Show me the distribution of patient ages"</li>
                        <li>"What is the average efficacy score by treatment group?"</li>
                        <li>"Find correlations between dose and adverse events"</li>
                        <li>"Plot the trend of enrollment over time"</li>
                        <li>"Which drugs have the highest success rate?"</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h5>Supported File Formats</h5>
                    <ul>
                        <li>CSV files (.csv)</li>
                        <li>Excel files (.xlsx, .xls)</li>
                        <li>Maximum file size: 100MB</li>
                        <li>Maximum rows: 1,000,000</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h5>Features</h5>
                    <ul>
                        <li>Natural language data querying</li>
                        <li>Automatic data visualizations</li>
                        <li>Dataset statistics and preview</li>
                        <li>Query history tracking</li>
                        <li>Export results to CSV</li>
                    </ul>
                </div>
            </div>
        `;
        
        this.showModal('Help', helpContent);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Global functions
window.switchSection = (section) => app.switchSection(section);
window.setExampleQuery = (query) => app.setExampleQuery(query);
window.clearResults = () => app.clearResults();

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PharmaQueryApp();
});