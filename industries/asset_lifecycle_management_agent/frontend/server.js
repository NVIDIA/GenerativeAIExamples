const express = require('express');
const cors = require('cors');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;
const NAT_API_URL = process.env.NAT_API_URL || 'http://localhost:8000';

// Enable CORS
app.use(cors());

// Serve static files
app.use(express.static(path.join(__dirname)));

// Proxy API requests to NeMo Agent Toolkit server
app.use('/chat', createProxyMiddleware({
    target: NAT_API_URL,
    changeOrigin: true,
    onProxyReq: (proxyReq, req, res) => {
        console.log(`[Proxy] ${req.method} ${req.path} -> ${NAT_API_URL}${req.path}`);
    },
    onError: (err, req, res) => {
        console.error('[Proxy Error]', err);
        res.status(500).json({ 
            error: 'Proxy error', 
            message: err.message,
            hint: 'Make sure the NeMo Agent Toolkit server is running on ' + NAT_API_URL
        });
    }
}));

// Serve output data (visualizations)
const outputPath = path.join(__dirname, '..', 'output_data');
app.use('/output', express.static(outputPath));
console.log(`[Output] Serving visualizations from: ${outputPath}`);

// Serve index.html for root path
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        frontend: 'running',
        natApiUrl: NAT_API_URL 
    });
});

app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 Predictive Maintenance Agent UI                          ║
║                                                               ║
║   Frontend Server: http://localhost:${PORT}                      ║
║   Backend API:     ${NAT_API_URL}                  ║
║                                                               ║
║   📊 Output folder: ${outputPath}  
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    `);
});

