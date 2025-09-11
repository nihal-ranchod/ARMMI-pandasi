// Main Application Logic
class AMINAApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.datasets = [];
        this.queryHistory = [];
        this.currentQuery = null;
        this.outsideClickListenerAdded = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        // Show user info section immediately (will be populated when data loads)
        const userInfo = document.getElementById('userInfo');
        if (userInfo) userInfo.style.display = 'flex';
        
        // User is already authenticated since they reached this page
        this.loadInitialData();
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
            this.loadSharedDatasets();
        });
        
        document.getElementById('refreshHistory')?.addEventListener('click', () => {
            this.loadQueryHistory();
        });
        
        document.getElementById('clearHistory')?.addEventListener('click', () => {
            this.clearQueryHistory();
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
        
        // User dropdown functionality
        this.setupUserDropdown();
    }
    
    async loadInitialData() {
        try {
            // Load user info first to determine user role
            await this.loadUserInfo();
            
            // Then load data based on user role
            await Promise.all([
                this.loadSharedDatasets(),
                this.loadQueryHistory()
            ]);
            this.updateDashboard();
        } catch (error) {
            console.error('Error loading initial data:', error);
            
            // Handle authentication errors
            if (error.message && error.message.includes('Authentication required')) {
                // Redirect to login page
                window.location.href = '/login';
            } else {
                UI.showToast('Error loading data', 'error');
            }
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
            this.loadSharedDatasets();
        } else if (sectionName === 'query') {
            this.updateQueryDatasetsList();
        } else if (sectionName === 'history') {
            this.loadQueryHistory();
        } else if (sectionName === 'dashboard') {
            this.loadDashboardData();
        }
    }
    
    // Legacy loadDatasets method removed - replaced with loadSharedDatasets
    
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
                    <button class="action-icon" onclick="app.renameSharedDataset('${dataset.id}')" title="Rename">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-icon danger" onclick="app.deleteSharedDataset('${dataset.id}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    updateQueryDatasetsList() {
        const container = document.getElementById('datasetSummary');
        
        if (this.datasets.length === 0) {
            const emptyMessage = this.currentUser?.is_admin ? 
                'No datasets available. Upload datasets in the Datasets section.' :
                'No shared datasets available. Contact an administrator to upload datasets.';
            
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <p>${emptyMessage}</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="shared-datasets-info">
                <p class="info-text">
                    <i class="fas fa-info-circle"></i>
                    Your query will automatically search across all ${this.datasets.length} available shared dataset${this.datasets.length > 1 ? 's' : ''}:
                </p>
            </div>
            ${this.datasets.map(dataset => `
                <div class="dataset-info-item">
                    <div class="dataset-icon">
                        <i class="fas fa-table"></i>
                    </div>
                    <div class="dataset-details">
                        <strong>${dataset.name}</strong>
                        <small>${dataset.rows.toLocaleString()} rows • ${dataset.columns} columns</small>
                    </div>
                    <div class="dataset-status">
                        <i class="fas fa-check-circle text-success"></i>
                    </div>
                </div>
            `).join('')}
        `;
    }
    
    // Dataset selection methods no longer needed in shared architecture
    // All available shared datasets are automatically included in queries
    
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
            
            // Use admin upload endpoint for admin users
            const response = this.currentUser?.is_admin ? 
                await API.uploadSharedDataset(file) : 
                await API.uploadDataset(file);
            
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            
            if (response.success) {
                uploadStatus.textContent = 'Upload successful!';
                UI.showToast(`Successfully uploaded ${file.name}`, 'success');
                
                // Refresh datasets
                await this.loadSharedDatasets();
                
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
                const response = await API.renameSharedDataset(datasetId, newName);
                
                if (response.success) {
                    UI.showToast('Dataset renamed successfully', 'success');
                    await this.loadSharedDatasets();
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error('Rename error:', error);
                UI.showToast('Failed to rename dataset', 'error');
            }
        }
    }
    
    
    async executeQuery() {
        const queryText = document.getElementById('queryInput').value.trim();
        
        if (!queryText) {
            UI.showToast('Please enter a query', 'warning');
            return;
        }
        
        if (this.datasets.length === 0) {
            UI.showToast('No datasets available for querying', 'warning');
            return;
        }
        
        const executeBtn = document.getElementById('executeQueryBtn');
        const resultsContainer = document.getElementById('queryResults');
        const resultsContent = document.getElementById('resultsContent');
        
        try {
            executeBtn.disabled = true;
            executeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
            
            const response = await API.executeQuery(queryText);
            
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
        
        // Show visualizations/charts if generated
        if (result.visualizations && result.visualizations.length > 0) {
            console.log('Adding visualizations:', result.visualizations.length); // Debug log
            result.visualizations.forEach((viz, index) => {
                html += `
                    <div class="result-item">
                        <h4><i class="fas fa-chart-bar"></i> ${viz.title}</h4>
                        <div class="visualization">
                            <img src="${viz.url}" alt="${viz.title}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" 
                                 onload="console.log('Chart loaded successfully')" 
                                 onerror="console.error('Failed to load chart:', this.src); this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <div style="display: none; text-align: center; color: #666; padding: 20px;">
                                <i class="fas fa-exclamation-triangle"></i>
                                <p>Failed to load chart</p>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        // Show data tables if present
        if (result.data_tables && result.data_tables.length > 0) {
            console.log('Adding data tables:', result.data_tables.length); // Debug log
            result.data_tables.forEach((table, index) => {
                html += `
                    <div class="result-item">
                        <h4><i class="fas fa-table"></i> ${table.title}</h4>
                        <div class="data-table-container">
                            ${this.renderDataTable(table)}
                        </div>
                    </div>
                `;
            });
        }
        
        content.innerHTML = html;
    }
    
    renderDataTable(table) {
        if (!table.data || !table.columns || table.data.length === 0) {
            return '<p class="no-data">No data to display</p>';
        }
        
        let html = '<div class="table-wrapper"><table class="data-table">';
        
        // Table header
        html += '<thead><tr>';
        table.columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead>';
        
        // Table body
        html += '<tbody>';
        table.data.forEach(row => {
            html += '<tr>';
            table.columns.forEach(col => {
                const value = row[col];
                const displayValue = value === null || value === undefined ? '' : value;
                html += `<td>${displayValue}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        
        return html;
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
                // Update dashboard when query history changes
                this.updateDashboard();
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
            <div class="history-item ${item.success ? 'clickable' : ''}" ${item.success ? `onclick="app.showQueryResult('${item.id}')"` : ''}>
                <div class="history-info">
                    <h4>${item.query}</h4>
                    <div class="history-meta">
                        ${new Date(item.timestamp).toLocaleString()} • 
                        Datasets: ${item.datasets.join(', ')}
                        ${item.success ? ' • Click to view results' : ''}
                    </div>
                </div>
                <div class="history-status">
                    <span class="${item.success ? 'status-success' : 'status-error'}">
                        <i class="fas fa-${item.success ? 'check-circle' : 'exclamation-circle'}"></i>
                        ${item.success ? 'Success' : item.error ? item.error : 'Failed'}
                    </span>
                </div>
            </div>
        `).join('');
    }
    
    async clearQueryHistory() {
        if (!confirm('Are you sure you want to clear all query history? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await API.clearQueryHistory();
            
            if (response.success) {
                UI.showToast('Query history cleared successfully', 'success');
                await this.loadQueryHistory();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Clear history error:', error);
            UI.showToast('Failed to clear query history', 'error');
        }
    }
    
    async showQueryResult(queryId) {
        try {
            // Find the query in history
            const query = this.queryHistory.find(q => q.id === queryId);
            if (!query) {
                UI.showToast('Query not found', 'error');
                return;
            }
            
            // Fetch the full query result with charts
            const response = await API.getQueryResult(queryId);
            
            if (response.success && response.result) {
                // Switch to query section to show results
                this.switchSection('query');
                
                // Display the stored result
                this.currentQuery = response.result;
                this.renderQueryResults(response.result);
                
                // Show the results container
                const resultsContainer = document.getElementById('queryResults');
                resultsContainer.style.display = 'block';
                
                // Scroll to results
                resultsContainer.scrollIntoView({ behavior: 'smooth' });
                
                UI.showToast('Showing results from history', 'success');
            } else {
                // Fallback for older queries without full results
                UI.showToast('Query result viewing is not available for this query. Original query: "' + query.query + '"', 'info');
            }
        } catch (error) {
            console.error('Error loading query result:', error);
            UI.showToast('Failed to load query result', 'error');
        }
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
    
    setupUserDropdown() {
        // Remove existing event listeners to prevent duplicates
        const dropdownBtn = document.getElementById('userDropdownBtn');
        if (dropdownBtn) {
            // Clone node to remove existing listeners
            const newBtn = dropdownBtn.cloneNode(true);
            dropdownBtn.parentNode.replaceChild(newBtn, dropdownBtn);
            
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleUserDropdown();
            });
        }

        // Set up user settings button
        const userSettingsBtn = document.getElementById('userSettingsBtn');
        if (userSettingsBtn) {
            userSettingsBtn.addEventListener('click', () => {
                this.closeUserDropdown();
                this.showUserSettings();
            });
        }

        // Set up logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.closeUserDropdown();
                this.handleLogout();
            });
        }

        // Set up click outside to close
        if (!this.outsideClickListenerAdded) {
            document.addEventListener('click', (e) => {
                const dropdown = document.getElementById('userDropdown');
                const userMenu = document.querySelector('.user-menu');
                
                if (dropdown && !userMenu?.contains(e.target)) {
                    this.closeUserDropdown();
                }
            });
            this.outsideClickListenerAdded = true;
        }
    }
    
    toggleUserDropdown() {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            const isVisible = dropdown.style.display === 'block';
            dropdown.style.display = isVisible ? 'none' : 'block';
            
            // Fix positioning issues when showing
            if (dropdown.style.display === 'block') {
                const userMenu = dropdown.closest('.user-menu');
                const userMenuRect = userMenu?.getBoundingClientRect();
                
                // Use fixed positioning relative to the button
                if (userMenuRect) {
                    dropdown.style.position = 'fixed';
                    dropdown.style.top = `${userMenuRect.bottom + 8}px`;
                    dropdown.style.right = `${window.innerWidth - userMenuRect.right}px`;
                    dropdown.style.left = 'auto';
                    dropdown.style.zIndex = '1100';
                }
            }
        }
    }
    
    closeUserDropdown() {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }
    
    async showUserSettings() {
        try {
            // Fetch current user data from API
            const response = await fetch('/api/auth/me', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.success && data.user) {
                const user = data.user;
                
                const userSettingsContent = `
                    <div class="user-settings-modal">
                        <div class="user-settings-header">
                            <div class="user-avatar-large">
                                <span class="user-initials-large">${user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}</span>
                            </div>
                            <div class="user-basic-info">
                                <h3 class="user-full-name">${user.name}</h3>
                                <p class="user-email">${user.email}</p>
                                <div class="user-role-badge-large ${user.is_admin ? 'admin' : 'user'}">
                                    <i class="fas fa-${user.is_admin ? 'shield-alt' : 'user'}"></i>
                                    ${user.is_admin ? 'Administrator' : 'User'}
                                </div>
                            </div>
                        </div>
                        
                        <div class="settings-divider"></div>
                        
                        <div class="user-details-grid">
                            <div class="detail-section">
                                <h4 class="section-title">
                                    <i class="fas fa-user-circle"></i>
                                    Account Information
                                </h4>
                                <div class="detail-items">
                                    <div class="detail-item">
                                        <span class="detail-label">User ID:</span>
                                        <span class="detail-value">${user.user_id}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Full Name:</span>
                                        <span class="detail-value">${user.name}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Email Address:</span>
                                        <span class="detail-value">${user.email}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Account Type:</span>
                                        <span class="detail-value role-badge ${user.is_admin ? 'admin' : 'user'}">
                                            <i class="fas fa-${user.is_admin ? 'shield-alt' : 'user'}"></i>
                                            ${user.is_admin ? 'Administrator' : 'Standard User'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h4 class="section-title">
                                    <i class="fas fa-clock"></i>
                                    Activity Information
                                </h4>
                                <div class="detail-items">
                                    <div class="detail-item">
                                        <span class="detail-label">Member Since:</span>
                                        <span class="detail-value">${new Date(user.created_at).toLocaleDateString('en-US', { 
                                            year: 'numeric', 
                                            month: 'long', 
                                            day: 'numeric' 
                                        })}</span>
                                    </div>
                                    ${user.last_login ? `
                                    <div class="detail-item">
                                        <span class="detail-label">Last Login:</span>
                                        <span class="detail-value">${new Date(user.last_login).toLocaleDateString('en-US', { 
                                            year: 'numeric', 
                                            month: 'long', 
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}</span>
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h4 class="section-title">
                                    <i class="fas fa-chart-bar"></i>
                                    Usage Statistics
                                </h4>
                                <div class="detail-items">
                                    <div class="detail-item">
                                        <span class="detail-label">Total Datasets:</span>
                                        <span class="detail-value stat-number">${this.datasets.length}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Total Queries:</span>
                                        <span class="detail-value stat-number">${this.queryHistory.length}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Total Records:</span>
                                        <span class="detail-value stat-number">${this.datasets.reduce((sum, d) => sum + d.rows, 0).toLocaleString()}</span>
                                    </div>
                                </div>
                            </div>
                            
                            ${user.is_admin ? `
                            <div class="detail-section admin-section">
                                <h4 class="section-title">
                                    <i class="fas fa-shield-alt"></i>
                                    Administrator Privileges
                                </h4>
                                <div class="detail-items">
                                    <div class="admin-privilege">
                                        <i class="fas fa-upload"></i>
                                        <span>Upload shared datasets</span>
                                    </div>
                                    <div class="admin-privilege">
                                        <i class="fas fa-edit"></i>
                                        <span>Manage existing datasets</span>
                                    </div>
                                    <div class="admin-privilege">
                                        <i class="fas fa-users"></i>
                                        <span>System administration</span>
                                    </div>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                `;
                
                this.showModal('User Settings', userSettingsContent);
            } else {
                UI.showToast('Unable to load user settings', 'error');
            }
        } catch (error) {
            console.error('Error loading user settings:', error);
            UI.showToast('Error loading user settings', 'error');
        }
    }

    showHelp() {
        const helpContent = `
            <div class="help-content">
                <h4>AMMINA Platform Help</h4>
                <p style="color: var(--secondary-color); margin-bottom: 2rem; font-style: italic;">African Manufacturing Market Intelligence & Network Analysis</p>
                
                <div class="help-section">
                    <h5>Getting Started</h5>
                    <ol>
                        <li>Upload your manufacturing datasets (CSV or Excel files)</li>
                        <li>Select datasets you want to analyze</li>
                        <li>Ask questions about African manufacturing markets</li>
                        <li>View insights with automatic visualizations</li>
                    </ol>
                </div>
                
                <div class="help-section">
                    <h5>Example Queries</h5>
                    <ul>
                        <li>"Show me the distribution of manufacturers by country"</li>
                        <li>"What are the most common product classes in Kenya?"</li>
                        <li>"Plot organizations by therapeutic areas"</li>
                        <li>"List all vaccine manufacturers in East Africa"</li>
                        <li>"Compare manufacturing capacity across regions"</li>
                        <li>"Show market intelligence for diagnostics products"</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h5>Supported File Formats</h5>
                    <ul>
                        <li>CSV files (.csv)</li>
                        <li>Excel files (.xlsx, .xls)</li>
                        <li>Maximum file size: 100MB</li>
                        <li>Multiple encodings supported</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h5>Platform Features</h5>
                    <ul>
                        <li>AI-powered market intelligence queries</li>
                        <li>Interactive data visualizations and charts</li>
                        <li>Manufacturing network analysis</li>
                        <li>Dataset statistics and previews</li>
                        <li>Query history tracking</li>
                        <li>Multi-dataset comparative analysis</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h5>About</h5>
                    <p>AMMINA is developed by <strong>Health 4 Development (H4D)</strong> to provide comprehensive market intelligence and network analysis for African manufacturing ecosystems.</p>
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
    
    async loadDashboardData() {
        // Force reload dashboard data when switching to dashboard
        try {
            await Promise.all([
                this.loadSharedDatasets(),
                this.loadQueryHistory()
            ]);
            // Dashboard will be updated automatically by the load methods
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    
    async loadUserInfo() {
        try {
            const response = await fetch('/api/auth/me', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.success && data.user) {
                const user = data.user;
                this.currentUser = user;
                
                // Update user info display
                const userInfo = document.getElementById('userInfo');
                const userName = document.getElementById('userName');
                
                // New dropdown elements
                const dropdownRole = document.getElementById('dropdownRole');
                const dropdownInitials = document.getElementById('dropdownInitials');
                
                if (userInfo) {
                    userInfo.style.display = 'flex';
                }
                if (userName) userName.textContent = user.name;
                
                // Generate user initials
                const initials = user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                
                // Populate dropdown with user info
                if (dropdownRole) {
                    dropdownRole.textContent = user.is_admin ? 'Administrator' : 'User';
                    dropdownRole.className = `user-role-badge ${user.is_admin ? 'admin' : 'user'}`;
                }
                if (dropdownInitials) dropdownInitials.textContent = initials;
                
                // Set up dropdown functionality after user info is loaded
                this.setupUserDropdown();
                
                // Configure UI based on user role
                this.configureUIForUserRole(user);
            }
        } catch (error) {
            console.error('Error loading user info:', error);
        }
    }

    configureUIForUserRole(user) {
        // Show/hide admin-only elements
        const adminUploadSection = document.getElementById('adminUploadSection');
        const datasetsTitle = document.getElementById('datasetsTitle');
        const datasetsDescription = document.getElementById('datasetsDescription');
        const datasetsListTitle = document.getElementById('datasetsListTitle');
        
        if (user.is_admin) {
            // Admin user - show upload functionality
            if (adminUploadSection) adminUploadSection.style.display = 'block';
            if (datasetsTitle) datasetsTitle.textContent = 'Shared Dataset Management';
            if (datasetsDescription) datasetsDescription.textContent = 'Upload and manage datasets available to all users';
            if (datasetsListTitle) datasetsListTitle.textContent = 'Manage Shared Datasets';
            
            // Update Quick Actions for admin
            this.updateQuickActionsForAdmin();
        } else {
            // Regular user - hide upload functionality
            if (adminUploadSection) adminUploadSection.style.display = 'none';
            if (datasetsTitle) datasetsTitle.textContent = 'Available Datasets';
            if (datasetsDescription) datasetsDescription.textContent = 'View shared datasets available for querying';
            if (datasetsListTitle) datasetsListTitle.textContent = 'Shared Datasets';
        }
        
        // Load appropriate datasets
        this.loadSharedDatasets();
        
        // Update query section
        this.updateQuerySectionForUserRole(user);
    }

    updateQuickActionsForAdmin() {
        const quickActions = document.querySelector('.action-buttons');
        if (quickActions) {
            quickActions.innerHTML = `
                <button class="action-btn admin-action" onclick="switchSection('datasets')">
                    <i class="fas fa-upload"></i>
                    Manage Datasets
                </button>
                <button class="action-btn" onclick="switchSection('query')">
                    <i class="fas fa-search"></i>
                    New Query
                </button>
                <button class="action-btn" onclick="switchSection('history')">
                    <i class="fas fa-history"></i>
                    View History
                </button>
            `;
        }
    }

    async loadDatasetsForUserRole(user) {
        // Load shared datasets for both admin and regular users
        await this.loadSharedDatasets();
    }

    async loadSharedDatasets() {
        try {
            console.log('loadSharedDatasets() called');
            console.log('currentUser:', this.currentUser);
            
            UI.showLoading('datasetsList');
            
            // Use API methods instead of direct fetch
            let response;
            if (this.currentUser?.is_admin) {
                console.log('Loading admin shared datasets...');
                response = await API.getAdminSharedDatasets();
            } else {
                console.log('Loading regular shared datasets...');
                response = await API.getSharedDatasets();
            }
            
            console.log('API response:', response);
            
            if (response.success) {
                this.datasets = response.datasets;
                console.log('Loaded datasets:', this.datasets.length, 'datasets');
                this.renderSharedDatasetsList();
                this.updateQueryDatasetsList();
                this.updateDashboard();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Error loading shared datasets:', error);
            UI.showError('datasetsList', 'Failed to load datasets');
            UI.showToast('Failed to load datasets', 'error');
        }
    }

    renderSharedDatasetsList() {
        const container = document.getElementById('datasetsList');
        
        if (this.datasets.length === 0) {
            const emptyMessage = this.currentUser?.is_admin ? 
                'No shared datasets uploaded yet. Upload the first dataset above.' :
                'No shared datasets available. Contact an administrator to upload datasets.';
            
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <p>${emptyMessage}</p>
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
                        ${dataset.uploaded_by ? `<span><i class="fas fa-user"></i> ${dataset.uploaded_by}</span>` : ''}
                    </div>
                </div>
                <div class="dataset-actions">
                    ${this.currentUser?.is_admin ? `
                        <button class="action-icon admin-action" onclick="app.renameSharedDataset('${dataset.id}')" title="Rename">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-icon admin-action danger" onclick="app.deleteSharedDataset('${dataset.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : `
                        <span class="dataset-status">Available for querying</span>
                    `}
                </div>
            </div>
        `).join('');
    }

    updateQuerySectionForUserRole(user) {
        // Update the query section to show available datasets info
        this.updateAvailableDatasetsSummary();
    }

    async updateAvailableDatasetsSummary() {
        const summaryContainer = document.getElementById('datasetSummary');
        if (!summaryContainer) return;

        if (this.datasets.length === 0) {
            summaryContainer.innerHTML = `
                <div class="empty-state">
                    <p>No datasets available for querying. ${this.currentUser?.is_admin ? 'Upload datasets in the Datasets section.' : 'Contact an administrator to upload datasets.'}</p>
                </div>
            `;
        } else {
            const totalRows = this.datasets.reduce((sum, ds) => sum + ds.rows, 0);
            summaryContainer.innerHTML = `
                <div class="dataset-summary-grid">
                    <div class="summary-card">
                        <div class="summary-number">${this.datasets.length}</div>
                        <div class="summary-label">Datasets Available</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">${totalRows.toLocaleString()}</div>
                        <div class="summary-label">Total Records</div>
                    </div>
                </div>
                <div class="dataset-list-compact">
                    ${this.datasets.map(ds => `
                        <div class="dataset-compact-item">
                            <span class="dataset-name">${ds.name}</span>
                            <span class="dataset-rows">${ds.rows.toLocaleString()} rows</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }

    async renameSharedDataset(datasetId) {
        if (!this.currentUser?.is_admin) return;
        
        const dataset = this.datasets.find(d => d.id === datasetId);
        if (!dataset) return;
        
        const newName = prompt('Enter new name for dataset:', dataset.name);
        if (!newName || newName.trim() === '' || newName === dataset.name) return;
        
        try {
            const response = await API.renameSharedDataset(datasetId, newName.trim());
            if (response.success) {
                UI.showToast('Dataset renamed successfully', 'success');
                await this.loadSharedDatasets();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Error renaming dataset:', error);
            UI.showToast('Failed to rename dataset', 'error');
        }
    }

    async deleteSharedDataset(datasetId) {
        if (!this.currentUser?.is_admin) return;
        
        const dataset = this.datasets.find(d => d.id === datasetId);
        if (!dataset) return;
        
        if (!confirm(`Are you sure you want to delete "${dataset.name}"? This action cannot be undone.`)) return;
        
        try {
            const response = await API.deleteSharedDataset(datasetId);
            if (response.success) {
                UI.showToast('Dataset deleted successfully', 'success');
                await this.loadSharedDatasets();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Error deleting dataset:', error);
            UI.showToast('Failed to delete dataset', 'error');
        }
    }
    
    async handleLogout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success) {
                UI.showToast('Logged out successfully', 'success');
                // Redirect to login page
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1000);
            } else {
                UI.showToast('Logout failed', 'error');
            }
        } catch (error) {
            console.error('Logout error:', error);
            // Force redirect even if logout request fails
            UI.showToast('Logged out', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        }
    }
}

// Global functions
window.switchSection = (section) => app.switchSection(section);
window.setExampleQuery = (query) => app.setExampleQuery(query);
window.clearResults = () => app.clearResults();
window.closeModal = () => app.closeModal();
window.toggleUserDropdown = () => app.toggleUserDropdown();

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AMINAApp();
});