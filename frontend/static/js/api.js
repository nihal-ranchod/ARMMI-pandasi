// API Interface for AMMINA Platform
class API {
    static baseURL = '/api';
    
    static async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            credentials: 'include', // Include cookies for session management
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        // Don't set Content-Type for FormData (file uploads)
        if (options.body instanceof FormData) {
            delete defaultOptions.headers['Content-Type'];
        }
        
        const config = {
            ...defaultOptions,
            ...options,
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            // Handle authentication errors
            if (!response.ok) {
                if (response.status === 401 && data.auth_error) {
                    // Authentication required - redirect to login
                    if (window.authManager) {
                        window.authManager.showAuthModal();
                    }
                    throw new Error('Authentication required');
                }
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Please check your connection and try again.');
            }
            throw error;
        }
    }
    
    // Dataset Management
    static async getDatasets() {
        return this.request('/datasets');
    }
    
    static async uploadDataset(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return this.request('/upload', {
            method: 'POST',
            body: formData,
        });
    }
    
    static async getDatasetPreview(datasetId) {
        return this.request(`/datasets/${datasetId}/preview`);
    }
    
    static async getDatasetStats(datasetId) {
        return this.request(`/datasets/${datasetId}/stats`);
    }
    
    static async renameDataset(datasetId, newName) {
        return this.request(`/datasets/${datasetId}/rename`, {
            method: 'PUT',
            body: JSON.stringify({ name: newName }),
        });
    }
    
    static async deleteDataset(datasetId) {
        return this.request(`/datasets/${datasetId}`, {
            method: 'DELETE',
        });
    }
    
    // Admin Shared Dataset Management
    static async getSharedDatasets() {
        return this.request('/shared-datasets');
    }

    static async getAdminSharedDatasets() {
        return this.request('/admin/shared-datasets');
    }
    
    static async uploadSharedDataset(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return this.request('/admin/shared-datasets/upload', {
            method: 'POST',
            body: formData,
        });
    }
    
    static async renameSharedDataset(datasetId, newName) {
        return this.request(`/admin/shared-datasets/${datasetId}/rename`, {
            method: 'PUT',
            body: JSON.stringify({ name: newName }),
        });
    }
    
    static async deleteSharedDataset(datasetId) {
        return this.request(`/admin/shared-datasets/${datasetId}`, {
            method: 'DELETE',
        });
    }

    // Query Execution (Updated for new architecture)
    static async executeQuery(query) {
        return this.request('/query', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
            }),
        });
    }
    
    // Query History
    static async getQueryHistory() {
        return this.request('/query-history');
    }
    
    static async clearQueryHistory() {
        return this.request('/query-history', {
            method: 'DELETE',
        });
    }
    
    static async getQueryResult(queryId) {
        return this.request(`/query-result/${queryId}`);
    }
    
    // Export
    static async exportResults(resultId, format = 'csv') {
        const url = `${this.baseURL}/export/${resultId}?format=${format}`;
        
        try {
            const response = await fetch(url, {
                credentials: 'include' // Include session cookies
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Authentication required
                    if (window.authManager) {
                        window.authManager.showAuthModal();
                    }
                    throw new Error('Authentication required');
                }
                const errorData = await response.json();
                throw new Error(errorData.error || 'Export failed');
            }
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = `query_results_${resultId}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            
            return { success: true };
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    }
    
    // Health check
    static async healthCheck() {
        try {
            const response = await fetch('/');
            return response.ok;
        } catch {
            return false;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}