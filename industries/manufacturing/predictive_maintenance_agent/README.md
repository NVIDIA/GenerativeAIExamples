# Predictive Maintenance Agent

A comprehensive AI-powered predictive maintenance system built with NVIDIA AIQ Toolkit for turbofan engine health monitoring and failure prediction.

Work done by: Vineeth Kalluru, Janaki Vamaraju, Sugandha Sharma, Ze Yang and Viraj Modak

## Table of Contents
- [Need for Predictive Maintenance](#need-for-predictive-maintenance)
- [NASA Turbofan Engine Dataset](#nasa-turbofan-engine-dataset)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
- [Launching AIQ Server and Frontend](#launching-aiq-server-and-frontend)
- [Testing with Example Prompts](#testing-with-example-prompts)
- [Appendix: Phoenix Observability](#appendix-phoenix-observability)
- [Next Steps](#next-steps)

## Need for Predictive Maintenance

In today's industrial landscape, unplanned equipment failures can cost organizations millions of dollars in downtime, emergency repairs, and lost productivity. Traditional reactive maintenance approaches wait for equipment to fail before taking action, while scheduled preventive maintenance often leads to unnecessary interventions and costs.

**Predictive maintenance** revolutionizes this approach by:

- **Preventing Costly Downtime**: Identifying potential failures before they occur, allowing for planned maintenance windows
- **Optimizing Maintenance Schedules**: Performing maintenance only when needed, reducing unnecessary interventions
- **Extending Equipment Lifespan**: Monitoring equipment health to maximize operational efficiency
- **Improving Safety**: Preventing catastrophic failures that could endanger personnel
- **Reducing Costs**: Minimizing emergency repairs, spare parts inventory, and operational disruptions

This predictive maintenance agent leverages AI and machine learning to analyze sensor data from turbofan engines, predict remaining useful life (RUL), and provide actionable insights for maintenance teams.

## NASA Turbofan Engine Dataset

The system utilizes the **NASA Turbofan Engine Degradation Simulation Dataset (C-MAPSS)**, a widely-used benchmark dataset for prognostics and health management research in manufacturing domain.

### Dataset Overview

The NASA dataset contains simulated turbofan engine run-to-failure data with the following characteristics:

- **21 Sensor Measurements**: Including temperature, pressure, vibration, and flow measurements
- **3 Operational Settings**: Different flight conditions and altitudes
- **Multiple Engine Units**: Each with unique degradation patterns
- **Run-to-Failure Data**: Complete lifecycle from healthy operation to failure

### Key Sensor Parameters

| Sensor ID | Description | Unit |
|-----------|-------------|------|
| sensor_1 | Total temperature at fan inlet | °R |
| sensor_2 | Total temperature at LPC outlet | °R |
| sensor_3 | Total temperature at HPC outlet | °R |
| sensor_4 | Total temperature at LPT outlet | °R |
| sensor_11 | Static pressure at HPC outlet | psia |
| sensor_13 | Corrected fan speed | rpm |
| sensor_20 | Ratio of fuel flow to Ps30 | pps/psi |
| sensor_21 | Corrected fan speed | rpm |

### Dataset Structure

```
Training Data: Engine run-to-failure trajectories
Test Data: Engine trajectories of unknown remaining cycles
Ground Truth: Actual RUL values for test engines
```

The dataset enables the development of prognostic models that can predict when an engine will require maintenance based on its current sensor readings and historical degradation patterns.

## Architecture

The Predictive Maintenance Agent follows a modular, multi-agent architecture built on the NVIDIA AIQ Toolkit framework:

```
<insert-pic>
```

### Key Components

#### 1. **React Agent Workflow**
- Main orchestration layer using ReAct (Reasoning + Acting) pattern
- Coordinates between different tools and agents
- Handles user queries and tool selection

#### 2. **SQL Retriever Tool**
- Generates SQL queries using NIM LLM
- Retrieves sensor data from SQLite database
- Uses vector embeddings for semantic query understanding

#### 3. **RUL Prediction Tool**
- Predicts Remaining Useful Life using pre-trained XGBoost model
- Processes sensor data through feature engineering pipeline
- Provides uncertainty estimates and confidence intervals

#### 4. **Plotting Agent**
- Multi-tool agent for data visualization
- Generates interactive charts and plots
- Supports line charts, distributions, and comparisons

#### 5. **Vector Database**
- ChromaDB for storing and retrieving database schema information
- Enables semantic search over table structures and relationships

## Setup and Installation

### Prerequisites

- Python 3.11+ (< 3.13)
- Conda or Miniconda
- NVIDIA NIM API access
- Node.js v18+ (for AgentIQ web interface)
- Docker (for Phoenix observability - optional)

### 1. Create a New Conda Environment

Create and activate a dedicated conda environment for the predictive maintenance agent:

```bash
# Create new conda environment
conda create -n pdm python=3.11

# Activate the environment
conda activate pdm
```

### 2. Install NVIDIA AgentIQ from Source

Clone and install the NVIDIA AIQToolkit following the [official installation guide](https://docs.nvidia.com/agentiq/latest/intro/install.html#install-from-source):

```bash
# Clone the AIQToolkit repository
git clone https://github.com/NVIDIA/AIQToolkit.git
cd AIQToolkit

# Install AIQ from source
uv pip install -e .

# Verify installation
aiq --help

# Optional: Remove the cloned repository after installation
# You can safely delete the AIQToolkit directory once installation is complete
# cd .. && rm -rf AIQToolkit
```

### 3. Install the Predictive Maintenance Workflow

Now install the predictive maintenance agent as a custom workflow

```bash
# Navigate back to your working directory
cd ..

# Clone the Generative AI examples repository
git clone https://github.com/NVIDIA/GenerativeAIExamples.git
cd GenerativeAIExamples/industries/manufacturing/predictive_maintenance_agent

# Install the workflow and its dependencies
uv pip install -e .
```

This will install the predictive maintenance agent as a custom AgentIQ workflow with all required dependencies.

### 4. Environment Setup

Create a `.env` file in the predictive maintenance agent directory with your NVIDIA NIM credentials:

```bash
# .env file
NVIDIA_API_KEY=your_nvidia_api_key_here
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

**Important**: Make sure to replace `your_nvidia_api_key_here` with your actual NVIDIA API key.

The environment variables need to be loaded before starting the AIQ server. You have several options:

**Source the environment manually**
```bash
# Load environment variables manually (Linux/Mac)
export $(cat .env | grep -v '^#' | xargs)

# For Windows Command Prompt
for /f "tokens=*" %i in (.env) do set %i

# For Windows PowerShell
Get-Content .env | ForEach-Object { if ($_ -match "^([^#].*)=(.*)") { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
```

### 5. Database Setup

The predictive maintenance agent requires the NASA turbofan dataset to be loaded into a SQLite database. We provide a comprehensive setup script to convert the original NASA text files into a structured database.

#### Download the NASA Dataset

First, download the NASA Turbofan Engine Degradation Simulation Dataset (C-MAPSS):

1. Visit the [NASA Prognostics Data Repository](https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/)
2. Download the "Turbofan Engine Degradation Simulation Data Set"
3. Extract all text files to a `data/` directory in your project

The dataset should include these files:
```
data/
├── train_FD001.txt    # Training data - Sea level, single fault mode
├── train_FD002.txt    # Training data - Sea level, multiple fault modes  
├── train_FD003.txt    # Training data - High altitude, single fault mode
├── train_FD004.txt    # Training data - High altitude, multiple fault modes
├── test_FD001.txt     # Test data - Sea level, single fault mode
├── test_FD002.txt     # Test data - Sea level, multiple fault modes
├── test_FD003.txt     # Test data - High altitude, single fault mode
├── test_FD004.txt     # Test data - High altitude, multiple fault modes
├── RUL_FD001.txt      # Ground truth RUL values for test data
├── RUL_FD002.txt      # Ground truth RUL values for test data
├── RUL_FD003.txt      # Ground truth RUL values for test data
└── RUL_FD004.txt      # Ground truth RUL values for test data
```

#### Run the Database Setup Script

Convert the NASA text files to SQLite database:

```bash
# Basic usage (assumes data/ directory exists)
python setup_database.py

# Custom data directory and database path
python setup_database.py --data-dir /path/to/nasa/files --db-path /path/to/output.db

# Get help on available options
python setup_database.py --help
```

The script will create a comprehensive SQLite database with the following structure:

#### Database Tables Created

| Table Name | Description | Records |
|------------|-------------|---------|
| `training_data` | Complete engine run-to-failure trajectories | ~20,000+ |
| `test_data` | Engine test trajectories (unknown RUL) | ~13,000+ |
| `rul_data` | Ground truth RUL values for test engines | ~400+ |
| `sensor_metadata` | Descriptions of all 21 sensors | 21 |
| `dataset_metadata` | Information about the 4 sub-datasets | 4 |

#### Database Views Created

| View Name | Purpose |
|-----------|---------|
| `latest_sensor_readings` | Most recent sensor readings per engine |
| `engine_health_summary` | Aggregated health statistics per engine |

#### Sample Database Queries

Once the database is set up, you can run sample queries:

```sql
-- View engine health summary
SELECT * FROM engine_health_summary LIMIT 5;

-- Get sensor readings for a specific engine
SELECT unit_number, time_in_cycles, sensor_measurement_1, sensor_measurement_11, RUL 
FROM training_data 
WHERE unit_number = 1 AND dataset = 'FD001' 
ORDER BY time_in_cycles;

-- Find engines with shortest operational life
SELECT unit_number, dataset, MAX(time_in_cycles) as total_cycles
FROM training_data 
GROUP BY unit_number, dataset 
ORDER BY total_cycles 
LIMIT 10;
```

#### Verification

The setup script automatically validates the database creation. You should see output similar to:

```
✅ Database created successfully at: PredM_db/nasa_turbo.db

Database contains the following tables:
- training_data: Engine run-to-failure trajectories
- test_data: Engine test trajectories  
- rul_data: Ground truth RUL values
- sensor_metadata: Sensor descriptions
- dataset_metadata: Dataset information

Useful views created:
- latest_sensor_readings: Latest readings per engine
- engine_health_summary: Engine health statistics
```

### 6. Configure Paths

Update the paths in `configs/config.yml` to match your local environment:

```yaml
functions:
  sql_retriever:
    vector_store_path: "/path/to/your/PredM_db"
    db_path: "/path/to/your/PredM_db/nasa_turbo.db"
    output_folder: "/path/to/your/output_data"
  predict_rul:
    scaler_path: "/path/to/your/models/scaler_model.pkl"
    model_path: "/path/to/your/models/xgb_model_fd001.pkl"
    output_folder: "/path/to/your/output_data"
```

### 7. Verify Installation

Verify that both AIQ and the workflow are properly installed:

```bash
pip list | grep -E "aiq|predictive"
```

## Launching AIQ Server and Frontend

### 1. Start the AIQ Server

**Important**: Ensure environment variables are loaded before starting the server.

#### Load environment variables

If you prefer to load environment variables manually:

```bash
# Linux/Mac: Load environment variables and start server
export $(cat .env | grep -v '^#' | xargs) && aiq serve --config_file=configs/config.yml

# Alternative: Source variables first, then start server
source <(cat .env | grep -v '^#' | sed 's/^/export /')
aiq serve --config_file=configs/config.yml
```

The server will start on `http://localhost:8000` by default and you should see output similar to:

```
2025-03-07 12:54:20,394 - aiq.cli.commands.start - INFO - Starting AgentIQ from config file: 'configs/config.yml'
INFO:     Started server process [47250]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

**Note**: If you see any errors related to missing API keys, verify that your `.env` file is properly formatted and that environment variables are loaded correctly.

### 2. Launch the AgentIQ Web User Interface

AgentIQ provides a dedicated web interface that requires Node.js v18+.

#### Setup the AIQtoolkit UI

The NVIDIA AIQToolkit UI provides a modern web interface for interacting with AIQ workflows. Follow these steps to set up the UI:

**Prerequisites:**
- Node.js v18+ 
- Git

**Installation:**

1. **Clone the AIQToolkit-UI repository:**
   ```bash
   git clone https://github.com/NVIDIA/AIQToolkit-UI.git
   cd AIQToolkit-UI
   ```

2. **Install dependencies:**
   ```bash
   npm ci
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

**Alternative: Docker Deployment**

For production or containerized environments:

```bash
# Build the Docker image
docker build -t aiqtoolkit-ui .

# Run the container
docker run -p 3000:3000 aiqtoolkit-ui
```

#### Configure the UI Settings

Once the UI is running:

1. Open the web interface in your browser at `http://localhost:3000`
2. Click the **Settings** icon in the bottom left corner
3. Configure the connection settings:
   - **HTTP URL for Chat Completion**: Choose your preferred endpoint:
     - `/generate` - Non-streaming responses
     - `/generate/stream` - Streaming responses (recommended)
     - `/chat` - Chat-based non-streaming
     - `/chat/stream` - Chat-based streaming (recommended for intermediate results)
   - **Theme**: Select Light or Dark theme
   - **WebSocket URL**: For real-time connections (if needed)

**Note**: The UI supports both HTTP requests (OpenAI compatible) and WebSocket connections for server communication.

### 3. Alternative: Direct API Interaction

You can also interact with the server directly via REST API:

```bash
# Non-streaming request
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"input_message": "What is the current health status of engine unit 1?", "use_knowledge_base": true}'

# Chat-based request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current health status of engine unit 1?"}'
```

### 4. Verify Installation

Once both server and frontend are running:

1. Navigate to the web interface (`http://localhost:3000`)
2. Configure the settings to point to your server
3. Test with a simple question like: "Show me sensor data for engine unit 1"
4. Verify you receive both intermediate steps and final results

## Testing with Example Prompts

Here are comprehensive example prompts to test different capabilities of the predictive maintenance agent:

### Data Retrieval and Analysis

* **Basic Data Query**
   ```
   Show me the sensor readings for engine unit 1 for the last 50 cycles.
   ```

* **Sensor Analysis**
   ```
   What are the temperature sensor readings (sensors 1-4) for engine units 1-5 over their operational lifetime?
   ```

* **Operational Settings Analysis**
   ```
   Compare the operational settings across different engine units and show me which units operated under the most severe conditions.
   ```

* **Operational Settings Data Retrieval**
   ```
   Retrieve the time_in_cycles and operational_setting_1 from the test_FD001 table for unit number 1. Then plot operational_setting_1 over time_in_cycles.
   ```

* **RUL Data Analysis**
   ```
   Retrieve RUL of each unit from the train_FD001 table. Then plot the distribution of RUL.
   ```

### Data Visualization

* **Trend Analysis**
   ```
   Plot the degradation trend of sensor_measurement_11 vs time_in_cycles for engine unit 2.
   ```

* **Multi-Engine Comparison**
   ```
   Create a comparison plot showing sensor_measurement_21 for engines 1 and 2 to identify different degradation patterns.
   ```

* **Distribution Analysis**
   ```
   Show me the distribution of sensor_measurement_4 values across all engine units to identify outliers.
   ```

### Predictive Analytics

* **RUL Prediction**
   ```
   Predict the remaining useful life for engine unit 5 based on its current sensor readings.
   ```

### Advanced Queries

* **Comprehensive RUL Analysis with Comparison**
   ```
   Retrieve time in cycles, all sensor measurements and RUL value for engine unit 24 from FD001 test and RUL tables. Predict RUL for it. Finally, generate a plot to compare actual RUL value with predicted RUL value across time.
   ```

* **Anomaly Detection**
   ```
   Identify any anomalous sensor readings in the last 100 cycles for all active engines.
   ```

## Appendix: Phoenix Observability

[Phoenix](https://phoenix.arize.com/) provides comprehensive observability and monitoring for your AI applications, enabling you to track performance, debug issues, and optimize your predictive maintenance system.

### Starting Phoenix

#### Option 1: Docker (Recommended)

```bash
# Start Phoenix server
docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest

# Phoenix will be available at http://localhost:6006
```

#### Option 2: Python Package

```bash
# Install Phoenix
uv pip install arize-phoenix

# Start Phoenix server
phoenix serve
```

### Configuration

Phoenix is pre-configured in `configs/config.yml`:

```yaml
general:
  tracing:
    phoenix:
      _type: phoenix
      endpoint: http://localhost:6006/v1/traces
      project: predictive-maintenance-app
```

### Monitoring Capabilities

Once Phoenix is running and your agents are active, you can monitor:

1. **Trace Analysis**: View detailed execution traces of agent workflows
2. **LLM Interactions**: Monitor all LLM calls, prompts, and responses
3. **Tool Usage**: Track which tools are being used and their performance
4. **Error Detection**: Identify and debug failures in the agent pipeline
5. **Performance Metrics**: Analyze response times and system performance
6. **Cost Tracking**: Monitor API usage and associated costs

### Accessing Phoenix Dashboard

1. Navigate to `http://localhost:6006`
2. Select the `predictive-maintenance-app` project
3. Explore traces, sessions, and performance metrics
4. Use filters to focus on specific time periods or components

### Best Practices

- **Regular Monitoring**: Check Phoenix dashboard regularly for performance insights
- **Error Analysis**: Use trace data to quickly identify and resolve issues
- **Optimization**: Identify slow components and optimize based on performance data
- **Cost Management**: Monitor API usage to optimize costs

## Next Steps

The predictive maintenance agent provides a solid foundation for industrial AI applications. Here are planned enhancements to further improve its capabilities:

### 1. Adding Memory Layer

**Objective**: Enable the agent to remember previous interactions and build context over time.

**Implementation Plan**:
- Integrate conversation memory using LangChain's memory components
- Store user preferences and historical analysis patterns
- Implement semantic memory for retaining domain knowledge
- Add session persistence for multi-turn conversations

**Benefits**:
- Improved user experience with contextual responses
- Better understanding of recurring maintenance patterns
- Personalized recommendations based on user history

### 2. Parallel Tool Calls for Data Visualization

**Objective**: Enhance performance by executing multiple visualization tasks simultaneously.

**Implementation Plan**:
- Implement async tool execution framework
- Create parallel plotting workflows for multiple engine units
- Add batch processing for large-scale data analysis
- Optimize resource utilization for concurrent operations

**Benefits**:
- Significantly faster response times for complex queries
- Improved system scalability
- Enhanced user experience with rapid visualizations

### 3. Action Recommendation Reasoning Agent

**Objective**: Develop an intelligent agent that provides specific maintenance recommendations.

**Implementation Plan**:
- Create a specialized reasoning agent using advanced prompt engineering
- Integrate maintenance best practices and industry standards
- Implement cost-benefit analysis for maintenance decisions
- Add integration with maintenance management systems

**Capabilities**:
- Prioritized maintenance recommendations
- Risk assessment and mitigation strategies
- Resource allocation optimization
- Compliance with safety regulations

### 4. Fault Detection Agent

**Objective**: Implement real-time fault detection and classification capabilities.

**Implementation Plan**:
- Develop anomaly detection algorithms using statistical methods
- Implement pattern recognition for fault signatures
- Create alert systems for critical failures
- Add fault classification and root cause analysis

**Features**:
- Real-time monitoring and alerting
- Automated fault classification
- Historical fault pattern analysis
- Integration with existing monitoring systems

### 5. NV-Tesseract Foundation Model Integration

**Objective**: Replace existing ML models with NVIDIA's state-of-the-art [NV-Tesseract time series foundation models](https://developer.nvidia.com/blog/new-nvidia-nv-tesseract-time-series-models-advance-dataset-processing-and-anomaly-detection/).

#### About NV-Tesseract

NV-Tesseract represents a breakthrough in time-series AI, offering specialized models for different predictive tasks:

- **Advanced Architecture**: Transformer-based embeddings with multi-head attention layers
- **Modular Design**: Purpose-built models for anomaly detection, forecasting, and classification
- **Superior Performance**: 5-20% accuracy improvements over traditional methods
- **Industry Applications**: Proven success in manufacturing, finance, healthcare, and industrial processes

#### Integration Plan

**Phase 1: Model Evaluation**
- Benchmark NV-Tesseract against current XGBoost models
- Evaluate performance on NASA turbofan dataset
- Compare accuracy, precision, and recall metrics

**Phase 2: Architecture Migration**
- Replace existing prediction pipeline with NV-Tesseract models
- Implement transformer-based feature processing
- Optimize inference performance for real-time predictions

**Phase 3: Enhanced Capabilities**
- **Anomaly Detection**: Implement real-time operational anomaly detection with F1 scores up to 0.96
- **Advanced Forecasting**: Add multi-horizon forecasting for maintenance planning
- **Classification**: Enhance fault type classification with improved accuracy

**Expected Benefits**:
- **Improved Accuracy**: Superior prediction performance, especially on complex multivariate datasets
- **Better Generalization**: Enhanced ability to handle unfamiliar data patterns
- **Real-time Processing**: Optimized inference for production environments
- **Reduced False Positives**: More precise anomaly detection reducing unnecessary maintenance

#### Implementation Timeline

1. **Q2 2025**: NV-Tesseract model evaluation and integration planning
2. **Q3 2025**: Core model replacement and testing
3. **Q4 2025**: Production deployment and performance optimization

### Getting Started with Next Steps

To contribute to these enhancements:

1. **Fork the Repository**: Create your own branch for development
2. **Review Current Architecture**: Understand the existing codebase structure
3. **Choose Enhancement**: Select a specific improvement area to focus on
4. **Development Plan**: Create detailed implementation plan
5. **Testing Strategy**: Develop comprehensive testing approach
6. **Documentation**: Update documentation and examples

For more information about contributing or to discuss specific enhancements, please reach out to the development team.

---

**Contact Information**:
- Author: Vineeth Kalluru
- Maintainer: NVIDIA Corporation
- Framework: NVIDIA AIQ Toolkit

**Additional Resources**:
- [NVIDIA AIQ Toolkit Documentation](https://docs.nvidia.com/aiq-toolkit/)
- [NV-Tesseract Model Information](https://developer.nvidia.com/blog/new-nvidia-nv-tesseract-time-series-models-advance-dataset-processing-and-anomaly-detection/)
- [Phoenix Observability Platform](https://phoenix.arize.com/) 