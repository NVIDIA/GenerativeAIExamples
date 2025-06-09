# 5G Network Simulator Lab with Agentic Workflow

This repository contains Jupyter notebooks to set up and run an open-source 5G Network Simulator lab, coupled with an Agentic Generative AI solution for dynamic bandwidth allocation. The lab uses Open Air Interface (OAI) for the 5G Core and RAN, FlexRIC for slice management, and iPerf for traffic generation, with performance data logged in a Kinetica database. The agentic workflow, powered by a LangGraph agent, analyzes traffic data and optimizes bandwidth allocation.

## Overview

The repository is organized into two main tasks:
1. **Lab Setup**: Configures a 5G network simulation environment with a core network, gNodeB, two User Equipment (UE) simulators, and traffic generation tools.
2. **Agentic Workflow**: Runs a LangGraph-based UI to monitor network performance and adjust bandwidth allocation dynamically.

A shutdown notebook is also provided to reinitialize the lab if needed.

## Prerequisites

To run the lab, ensure you have:
- **Operating System**: Ubuntu (tested on 20.04 or later).
- **Hardware**:
  - CPU: 12+ cores @ 3,8 GHz, AVX-512 is a necessary
  - RAM: 32 GB
  - OS: Modern Linux (e.g., Ubuntu 22.04)
  - Docker & Docker Compose (latest stable)
- **Software**:
  - Docker and Docker Compose for the 5G Core Network.
  - Python 3.10+ with Jupyter Notebook.
  - iPerf3 (`sudo apt install -y iperf3`).
  - Kinetica database access (credentials in `.env` file).
- **Dependencies**: Listed in `requirements.txt` in the respective directories.

## Lab Setup

The lab setup configures a fully functional 5G network simulation environment. To set up the lab, first you will need to run autonomous_5g_slicing_lab/Automatic_5G_Network_Lab_Setup.ipynb to configure your environment, and then you will need to run the Jupyter notebook located at `autonomous_5g_slicing_lab/llm-slicing-5g-lab/DLI_Lab_Setup.ipynb`. The notebook automates the following steps:

1. **Install Dependencies**: Installs iPerf3 and Python packages required for the lab, then restarts the Jupyter kernel to apply changes.
2. **Compile FlexRIC and gNodeB**: Builds the FlexRIC and gNodeB components using a provided script, preparing the RAN Intelligent Controller and base station software.
3. **Set Up 5G Core Network**: Launches the 5G Core Network functions for two network slices using Docker Compose, ensuring each slice has its own Session Management Function (SMF) and User Plane Function (UPF).
4. **Start FlexRIC**: Activates the FlexRIC to manage gNodeB parameters dynamically, logging output for troubleshooting.
5. **Start gNodeB**: Runs the OAI softmodem to simulate the gNodeB, connecting it to the core network and FlexRIC.
6. **Initialize Bandwidth Allocation**: Sets an initial 50/50 bandwidth split between the two slices, ensuring balanced resource allocation.
7. **Start User Equipment (UEs)**: Launches two UE simulators (UE1 and UE3), each connected to a separate slice, to interact with the gNodeB.
8. **Start iPerf Server**: Runs two iPerf3 servers on the external network to receive traffic from the UEs via the UPF.
9. **Generate Traffic and Log Data**: Runs iPerf clients on the UEs to generate UDP traffic at alternating speeds (30 Mbps and 120 Mbps), logging performance metrics (e.g., bitrate, packet loss) to a Kinetica database and local log files.

In summary, to start your lab, you need to follow these steps:
1. **Open 'autonomous_5g_slicing_lab/Automatic_5G_Network_Lab_Setup.ipynb' in the main directory and set up your environment keys
2. **Open 'autonomous_5g_slicing_lab/llm-slicing-5g-lab/DLI_Lab_Setup.ipynb and set up your 5G Network Environment

## Running the Agentic Workflow

Once the lab is set up, you can run the agentic workflow to monitor network performance and dynamically adjust bandwidth allocation. The workflow uses a LangGraph-based agent to analyze Kinetica database logs and optimize slice configurations.

To run the agentic workflow:
1. Open the Jupyter notebook at `autonomous_5g_slicing_lab/agentic-llm/agentic_pipeline-DLI.ipynb` in Jupyter Notebook.
2. Execute the cells to launch the LangGraph agent UI. The UI interacts with the 5G network simulator, retrieves performance data from the Kinetica database, and issues commands to FlexRIC to adjust bandwidth allocation based on traffic demands.

Ensure the lab setup (`DLI_Lab_Setup.ipynb`) is fully running before starting the agentic workflow, as it relies on the active 5G network simulation and traffic generation.

## Reinitializing the Lab

If you need to reset or reinitialize the lab (e.g., to clear logs, stop processes, or restart the environment), use the shutdown notebook:
- Open `autonomous_5g_slicing_lab/llm-slicing-5g-lab/DLI_Lab_Shutdown.ipynb` in Jupyter Notebook.
- Run the cells to gracefully stop all running processes (e.g., FlexRIC, gNodeB, UEs, iPerf servers) and clean up resources.

After running the shutdown notebook, you can restart the lab by re-running `DLI_Lab_Setup.ipynb`.

## Usage Notes

- **Execution Order**: Complete the lab setup before running the agentic workflow. The shutdown notebook can be used at any time to reset the environment.
- **Monitoring**: Check logs in `autonomous_5g_slicing_lab/llm-slicing-5g-lab/logs/` for debugging (e.g., `RIC.log`, `UE1.log`, `UE1_iperfc.log`).
- **Kinetica Access**: Use the credentials in `autonomous_5g_slicing_lab/llm-slicing-5g-lab/.env` (e.g., `KINETICA_USERNAME=nvidia_gtc_2025`, `KINETICA_PASSWORD=Kinetica123!`) to access the Kinetica database at `https://demo72.kinetica.com/gadmin/`.
- **Network Configuration**: The notebooks assume specific IP addresses (e.g., `12.1.1.2`, `192.168.70.135`). Modify these in the notebooks if your setup differs.
- **Environment**: The lab is designed for a controlled DLI environment. For personal machines, ensure all dependencies and the full repository directory are available.

## Repository Structure

- `autonomous_5g_slicing_lab/llm-slicing-5g-lab/`:
  - `DLI_Lab_Setup.ipynb`: Notebook for setting up the 5G network simulator.
  - `DLI_Lab_Shutdown.ipynb`: Notebook for reinitializing the lab.
  - `requirements.txt`: Python dependencies for the lab.
  - `build_ric_oai_ne.sh`: Script to compile FlexRIC and gNodeB.
  - `docker-compose-oai-cn-slice1.yaml`, `docker-compose-oai-cn-slice2.yaml`: Docker Compose files for 5G Core Network slices.
  - `ran-conf/`: Configuration files for gNodeB and UEs.
  - `multi_ue.sh`: Script to start UE simulators.
  - `change_rc_slice.sh`: Script to adjust bandwidth allocation.
  - `.env`: Environment variables (e.g., Kinetica credentials).
  - `logs/`: Directory for log files (created during execution).
- `autonomous_5g_slicing_lab/agentic-llm/`:
  - `agentic_pipeline-DLI.ipynb`: Notebook for running the LangGraph agent UI.
  - `requirements.txt`: Python dependencies for the agentic workflow.

## License
- This repository is based on OAI 5G RAN, CN, and UE, and it is released under [OAI Public License](https://openairinterface.org/legal/oai-public-license/)

## References

- [Open Air Interface 5G Core Network](https://openairinterface.org/oai-5g-core-network-project/)
- [OAI Softmodem RAN](https://github.com/simula/openairinterface5g/blob/dreibh/simulamet-testbed/doc/RUNMODEM.md)
- [iPerf Tool](https://iperf.fr/)
- [Kinetica Database](https://www.kinetica.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)

For issues or contributions, please open a GitHub issue or submit a pull request.

1. [Aaron Bossert](https://www.linkedin.com/in/aaron-bossert/), Director of Solutions Engineering, [Kinetica](https://www.kinetica.com/)
2. [Stefan Spettel](https://www.linkedin.com/in/stefan-spettel/), CEO & Co-Founder, [phine.tech](https://phine.tech/)
4. [Fransiscus Asisi Bimo](https://www.linkedin.com/in/fransiscusbimo/), Ph.D., National Taiwan University of Science and Technology
6. [Shibani Likhite](https://www.linkedin.com/in/shibani-likhite/), Solution Architect, NVIDIA
7. [Swastika Dutta](https://www.linkedin.com/in/swastika-dutta/), Solution Architect, NVIDIA
8. [Ari Uskudar](https://www.linkedin.com/in/ari-u-628b30148/), Product Manager, NVIDIA.
9. [Maria Amparo Canaveras Galdon](https://www.linkedin.com/in/amparo-canaveras-b2152522/), Senior Solution Architect, NVIDIA
10. [Ira Bargon III](https://www.linkedin.com/in/ira-bargon-iii-a8661514/), Sr. Director of Technology and Innovation, Sterling
11. [Lukas Rothender](https://www.linkedin.com/in/lukas-rotheneder-82984327a/), CTO & Co-Founder, [phine.tech](https://phine.tech/)





