# 5G Network Agent: Grafana & InfluxDB Integration Guide

This guide explains how to set up and use the enhanced real-time metrics dashboard for the 5G Network Agent, using **Grafana** and **InfluxDB** for professional, interactive visualization. It is tailored for users starting from the original [NVIDIA/GenerativeAIExamples](https://github.com/NVIDIA/GenerativeAIExamples/tree/main) repository, and reflects all recent changes and improvements.

---

## 🚀 Overview: What's New

- **Grafana Dashboards**: Interactive, real-time time-series visualizations
- **InfluxDB**: High-performance time-series database for metrics storage
- **Automated Docker Setup**: One-command startup for Grafana & InfluxDB
- **Streamlit UI**: Embedded Grafana dashboard in the main app
- **Test & Utility Scripts**: Easy verification and troubleshooting

---

## 📁 File Structure (Grafana Integration)

```
agentic-llm/
├── chatbot_DLI.py                # Main Streamlit app (Grafana embedded)
├── influxdb_utils.py             # InfluxDB client utility (metrics API)
├── test_influxdb.py              # Script to test InfluxDB connectivity
├── docker-compose.yml            # Docker Compose for Grafana & InfluxDB
├── start_grafana_services.sh     # Linux/Mac startup script
├── start_grafana_services.bat    # Windows startup script
├── requirements_grafana.txt      # Python dependencies
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── influxdb.yaml     # InfluxDB datasource config
│   │   └── dashboards/
│   │       └── dashboard.yaml    # Dashboard provisioning config
│   └── dashboards/
│       └── 5g-metrics-dashboard.json  # Dashboard definition (edit here)
├── config.yaml                   # App configuration (log file paths, etc.)
└── README_GRAFANA.md             # This guide
```

---

## 🛠️ Setup Instructions

### 1. Prerequisites
-** Install docker compose if not installed
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version
```

- **Python 3.8+**

### 2. Install Python Dependencies

```bash
cd ./autonomous_5g_slicing_lab/agentic-llm
pip install -r requirements_grafana.txt
```

### 3. Start Grafana & InfluxDB Services

**On Linux/Mac:**
```bash
chmod +x start_grafana_services.sh
./start_grafana_services.sh
```

**On Windows:**
```cmd
start_grafana_services.bat
```

This will:
- Stop any existing containers
- Start Grafana (http://localhost:9002) and InfluxDB (http://localhost:9001)
- Provision the dashboard and datasource automatically

### 4. Verify Services
- Graphana Services are running in the following ports. Please make sure you are exposing these ports in your environment.
- **Grafana**: [http://localhost:9002](http://localhost:9002) (Press "Skip" to avoid the user and password authentication)
- **InfluxDB**: [http://localhost:9001](http://localhost:9001)

### 5. Get Variable for Dashboard in Graphana
- **Go to **Grafana**: [http://localhost:9002](http://localhost:9002)
- **Get the letter combination for your created dashboard. 
E.g. https://9002-3yqhu0mm9.brevlab.com/?orgId=1&from=now-6h&to=now&timezone=browser  - letter combination is 3yqhu0mm9 and store it in the file config.yaml under /autonomous_5g_slicing_lab/agentic-llm
- See the picture showing how to get the number

![Alt text](/agentic-llm/images/graphana.png)

