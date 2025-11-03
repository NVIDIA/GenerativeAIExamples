# Predictive Maintenance Agent - Modern Web UI

A professional, modern web interface for the NVIDIA Predictive Maintenance Agent, inspired by the AIQ Research Assistant design.

## Features

✨ **Modern UI/UX Design**
- Clean, professional interface with NVIDIA branding
- Dark/Light theme support
- Responsive design for desktop and mobile
- Smooth animations and transitions

🎯 **Key Capabilities**
- Real-time chat interface with streaming responses
- Interactive example prompts for quick start
- Visualization display for plots and charts
- Intermediate step visibility toggle
- Configurable settings panel

📊 **Visualization Support**
- Automatic detection of generated plots
- Embedded display of Plotly HTML visualizations
- Direct access to output files

⚙️ **Flexible Configuration**
- Customizable API endpoint
- HTTP streaming and WebSocket support
- Auto-scroll preferences
- Theme customization

## Quick Start

### Prerequisites

- Node.js v18+ installed
- NeMo Agent Toolkit server running (default: `http://localhost:8000`)

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the server:
```bash
npm start
```

4. Open your browser:
```
http://localhost:3000
```

### Using with NAT Server

Make sure your NeMo Agent Toolkit server is running:

```bash
cd /path/to/predictive_maintenance_agent
nat serve --config_file=configs/config-reasoning.yml
```

The frontend will automatically proxy requests to `http://localhost:8000`.

## Configuration

### Environment Variables

You can customize the frontend behavior using environment variables:

```bash
# Port for the frontend server (default: 3000)
PORT=3000

# NeMo Agent Toolkit API URL (default: http://localhost:8000)
NAT_API_URL=http://localhost:8000

# Start with custom settings
npm start
```

### UI Settings

Click the ⚙️ Settings icon in the header to configure:

- **API Endpoint**: Change the backend server URL
- **Streaming Mode**: HTTP Streaming (recommended) or WebSocket
- **Theme**: Dark or Light mode
- **Auto-scroll**: Toggle automatic scrolling to new messages

## File Structure

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Modern UI styles
├── app.js             # Frontend JavaScript logic
├── server.js          # Express server with proxy
├── package.json       # Node.js dependencies
└── README.md          # This file
```

## Features Breakdown

### 1. Chat Interface

The main chat interface supports:
- Real-time message streaming
- User and assistant message differentiation
- Markdown-style formatting (bold, italic, code)
- Loading indicators during processing

### 2. Example Prompts

Quick-start buttons for common queries:
- Data retrieval and visualization
- RUL prediction with comparisons
- Anomaly detection analysis
- Distribution analysis

### 3. Visualization Display

Automatic detection and rendering of:
- Plotly HTML files
- Interactive charts
- Direct embedding in chat

### 4. Intermediate Steps

Toggle visibility of:
- Tool calls
- Agent reasoning steps
- SQL queries
- Code generation steps

## Differences from NeMo-Agent-Toolkit-UI

This custom UI provides several enhancements over the standard NAT UI:

| Feature | NAT-UI | Custom UI |
|---------|--------|-----------|
| Design | Generic chat | NVIDIA-branded, modern |
| Visualizations | External links | Embedded display |
| Example prompts | None | Domain-specific examples |
| Theme support | Limited | Full dark/light themes |
| Mobile responsive | Basic | Fully optimized |
| Branding | Generic | Predictive maintenance focused |

## Troubleshooting

### Frontend won't connect to backend

1. Verify NAT server is running:
```bash
curl http://localhost:8000/health
```

2. Check the proxy configuration in settings
3. Look for CORS errors in browser console

### Visualizations not displaying

1. Ensure output files are generated in `output_data/`
2. Check file paths in assistant responses
3. Verify the `/output` route is serving files correctly

### Port already in use

Change the port:
```bash
PORT=3001 npm start
```

## Development

### Adding New Features

1. **Modify HTML**: Edit `index.html` for structure changes
2. **Update Styles**: Edit `styles.css` for visual changes
3. **Add Logic**: Edit `app.js` for new functionality
4. **Update Server**: Edit `server.js` for backend changes

### Hot Reload

For development with auto-reload:
```bash
npm install -g nodemon
nodemon server.js
```

## Integration with AIQ Concepts

This UI draws inspiration from the AIQ Research Assistant while adapting to predictive maintenance:

| AIQ Feature | PDM Equivalent |
|-------------|----------------|
| Document upload | Database pre-loaded |
| Research plan | Example prompts |
| Report generation | Visualization generation |
| Source citations | Data source tracking |
| Human-in-the-loop | Interactive queries |

## License

Apache-2.0 - See LICENSE file for details

## Support

For issues or questions:
1. Check the main README in parent directory
2. Review NAT documentation
3. Examine browser console for errors
4. Verify all services are running

## Credits

- Design inspired by NVIDIA AIQ Research Assistant
- Built for NeMo Agent Toolkit integration
- Optimized for predictive maintenance workflows

