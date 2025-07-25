// MCP Client for Neo4j EHR Server
class MCPClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.requestId = 0;
        this.connected = false;
    }

    async connect() {
        try {
            // Test connection by calling initialize
            const response = await fetch(this.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'initialize',
                    params: {
                        protocolVersion: '2024-11-05',
                        capabilities: {}
                    },
                    id: ++this.requestId
                })
            });
            
            if (response.ok) {
                this.connected = true;
                return true;
            }
            return false;
        } catch (error) {
            console.error('Connection error:', error);
            return false;
        }
    }

    async callTool(toolName, args) {
        if (!this.connected) {
            throw new Error('Not connected to server');
        }

        try {
            const response = await fetch(this.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'tools/call',
                    params: {
                        name: toolName,
                        arguments: args
                    },
                    id: ++this.requestId
                })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error.message || 'Unknown error');
            }

            return data.result;
        } catch (error) {
            console.error('Tool call error:', error);
            throw error;
        }
    }
}

// Global variables
let client = null;
let isConnected = false;

// Connection management
async function toggleConnection() {
    const serverUrl = document.getElementById('server-url').value;
    const connectBtn = document.getElementById('connect-btn');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    if (!isConnected) {
        client = new MCPClient(serverUrl);
        const connected = await client.connect();
        
        if (connected) {
            isConnected = true;
            connectBtn.textContent = 'Disconnect';
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'Connected';
            showMessage('Connected to MCP server', 'success');
        } else {
            showMessage('Failed to connect to server', 'error');
        }
    } else {
        client = null;
        isConnected = false;
        connectBtn.textContent = 'Connect';
        statusIndicator.className = 'status-indicator';
        statusText.textContent = 'Disconnected';
        showMessage('Disconnected from server', 'info');
    }
}

// Tab management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

// Tool functions
async function getPatientInfo() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const patientId = document.getElementById('patient-id').value;
    const format = document.getElementById('patient-format').value;
    
    // Get selected include options
    const includeCheckboxes = document.querySelectorAll('input[name="include"]:checked');
    const include = Array.from(includeCheckboxes).map(cb => cb.value);

    if (!patientId) {
        showMessage('Please enter a patient ID', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await client.callTool('ehr_patient', {
            subject_id: patientId,
            include: include.length > 0 ? include : ['demographics'],
            format: format
        });
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function searchNotes() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const query = document.getElementById('search-query').value;
    const searchType = document.getElementById('search-type').value;
    const patientId = document.getElementById('search-patient-id').value;
    const admissionId = document.getElementById('search-admission-id').value;
    const limit = parseInt(document.getElementById('search-limit').value);
    const format = document.getElementById('search-format').value;

    if (!query) {
        showMessage('Please enter a search query', 'error');
        return;
    }

    showLoading(true);
    try {
        const args = {
            query: query,
            search_type: searchType,
            limit: limit,
            format: format
        };
        
        if (patientId) args.subject_id = patientId;
        if (admissionId) args.admission_id = admissionId;

        const result = await client.callTool('ehr_search_notes', args);
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function listDiagnoses() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const patientId = document.getElementById('diagnoses-patient-id').value;
    const admissionId = document.getElementById('diagnoses-admission-id').value;
    const limit = parseInt(document.getElementById('diagnoses-limit').value);
    const format = document.getElementById('diagnoses-format').value;

    showLoading(true);
    try {
        const args = {
            limit: limit,
            format: format
        };
        
        if (patientId) args.subject_id = patientId;
        if (admissionId) args.admission_id = admissionId;

        const result = await client.callTool('ehr_list_diagnoses', args);
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function listMedications() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const patientId = document.getElementById('medications-patient-id').value;
    const admissionId = document.getElementById('medications-admission-id').value;
    const limit = parseInt(document.getElementById('medications-limit').value);
    const format = document.getElementById('medications-format').value;

    showLoading(true);
    try {
        const args = {
            limit: limit,
            format: format
        };
        
        if (patientId) args.subject_id = patientId;
        if (admissionId) args.admission_id = admissionId;

        const result = await client.callTool('ehr_list_medications', args);
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function listProcedures() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const patientId = document.getElementById('procedures-patient-id').value;
    const admissionId = document.getElementById('procedures-admission-id').value;
    const limit = parseInt(document.getElementById('procedures-limit').value);
    const format = document.getElementById('procedures-format').value;

    showLoading(true);
    try {
        const args = {
            limit: limit,
            format: format
        };
        
        if (patientId) args.subject_id = patientId;
        if (admissionId) args.admission_id = admissionId;

        const result = await client.callTool('ehr_list_procedures', args);
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function listLabEvents() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const patientId = document.getElementById('lab-patient-id').value;
    const admissionId = document.getElementById('lab-admission-id').value;
    const limit = parseInt(document.getElementById('lab-limit').value);
    const format = document.getElementById('lab-format').value;

    showLoading(true);
    try {
        const args = {
            limit: limit,
            format: format
        };
        
        if (patientId) args.subject_id = patientId;
        if (admissionId) args.admission_id = admissionId;

        const result = await client.callTool('ehr_list_lab_events', args);
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function naturalQuery() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const query = document.getElementById('natural-query').value;
    const limit = parseInt(document.getElementById('natural-limit').value);
    const format = document.getElementById('natural-format').value;

    if (!query) {
        showMessage('Please enter a question', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await client.callTool('ehr_natural_query', {
            query: query,
            limit: limit,
            format: format
        });
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function getSchema() {
    if (!isConnected) {
        showMessage('Please connect to the server first', 'error');
        return;
    }

    const format = document.getElementById('schema-format').value;

    showLoading(true);
    try {
        const result = await client.callTool('ehr_get_schema', {
            format: format
        });
        displayResults(result, format);
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Display functions
function displayResults(result, format) {
    const resultsDiv = document.getElementById('results');
    const resultsInfo = document.getElementById('results-info');
    
    // Clear previous results
    resultsDiv.innerHTML = '';
    
    if (!result || !result.content || result.content.length === 0) {
        resultsDiv.innerHTML = '<p class="no-results">No results found</p>';
        resultsInfo.textContent = 'No results';
        return;
    }

    // Get the actual content
    const content = result.content[0];
    
    if (format === 'json') {
        // Parse and display JSON
        try {
            const data = typeof content.text === 'string' ? JSON.parse(content.text) : content.text;
            resultsDiv.innerHTML = `<pre class="json-results">${JSON.stringify(data, null, 2)}</pre>`;
            
            // Update results info
            if (Array.isArray(data)) {
                resultsInfo.textContent = `${data.length} results`;
            } else if (data.results && Array.isArray(data.results)) {
                resultsInfo.textContent = `${data.results.length} results`;
            } else {
                resultsInfo.textContent = 'Results loaded';
            }
        } catch (e) {
            resultsDiv.innerHTML = `<pre class="json-results">${content.text}</pre>`;
            resultsInfo.textContent = 'Results loaded';
        }
    } else if (format === 'markdown') {
        // Display markdown as HTML (basic conversion)
        const html = convertMarkdownToHTML(content.text);
        resultsDiv.innerHTML = `<div class="markdown-results">${html}</div>`;
        resultsInfo.textContent = 'Results loaded';
    } else {
        // Display as plain text
        resultsDiv.innerHTML = `<pre class="text-results">${content.text}</pre>`;
        resultsInfo.textContent = 'Results loaded';
    }
}

function convertMarkdownToHTML(markdown) {
    // Basic markdown to HTML conversion
    let html = markdown
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^\* (.+)/gim, '<li>$1</li>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Wrap in paragraphs
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }
    
    return html;
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

function clearResults() {
    document.getElementById('results').innerHTML = '';
    document.getElementById('results-info').textContent = '';
}

function showMessage(message, type) {
    // Create a temporary message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Set default server URL
    const serverUrl = document.getElementById('server-url');
    if (!serverUrl.value) {
        serverUrl.value = 'http://localhost:8080';
    }
});