## Introduction
In this repository, we demonstrate the following:
* A customer care agent in Langgraph that has three specialist assistants: patient intake, medication assistance, and appointment making, with corresponding tools.
* A customer care agent in Langgraph for patient intake only. 
* A customer care agent in Langgraph for appointment making only.
* A customer care agent in Langgraph for medication lookup only.
* A Gradio based UI that allows us to use voice or typing to converse with any of the four agents.
* A chain server that allows ACE to connect to any of the four agents.

The agentic tool calling capability in each of the customer care assistants is powered by LLM NIMs - NVIDIA Inference Microservices. With the agentic capability, you can write your own tools to be utilized by LLMs.

## Running the chain server or simple UI 
### Compute Requirements
To get the healthcare assistant(s) up and running as either a chain server of an interactive UI with text and voice, there are no local GPU requirements. The LLMs utilized in LangGraph in this repo are by default set to calling NVIDIA AI Endpoints, as seen in the directory[`graph_definitions/`](./graph_definitions/).
```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA
llm_model = "meta/llama-3.1-70b-instruct"
assistant_llm = ChatNVIDIA(model=llm_model)
```
You will need an NVIDIA API KEY to call NVIDIA AI Endpoints. If you would like to host your own LLM NIM instance instead of calling NVIDIA AI Endpoints with an API key, please refer to the documentation of the LLM NIM on how to host, and add a `base_url` parameter to point to your own instance when specifying `ChatNVIDIA`.

### Add your API keys
In the file `vars.env`, add two API keys of your own:
```
NVIDIA_API_KEY="nvapi-" 
TAVILY_API_KEY="tvly-"
```
Note the Tavily key is only required if you want to run the full graph or the medication lookup graph. Get your API Key from the Tavily website. This is used in the tool named `medication_instruction_search_tool` in [`graph.py`](./graph_definitions/graph.py) or [`graph_medication_lookup_only.py`](./graph_definitions/graph_medication_lookup_only.py).

### Run a specific service with Docker Compose
#### 1. If running the chain server to connect to ACE
First, modify the [`docker-compose.yaml`](./docker-compose.yaml) file to specify the assistant you want to run.
```yaml
entrypoint: python3 chain_server/chain_server.py --assistant intake --port 8081
```
The `--assistant` arg has 4 choices: `full`, `intake`, `appointment`, `medication`, corresponding to the four assistants with their graphs shown in [`graph_definitions/graph_images/`](./graph_definitions/graph_images/).
Next, start the chain server container:
```sh
docker compose up -d chain-server
# or to build at this command:
docker compose up --build -d chain-server 
```

Note this will be running on port 8081 by default. If you need to run on a different port, modify the [`docker-compose.yaml`](./docker-compose.yaml) file's `chain-server` section and replace all mentions of 8081 with your own port number.

You can test your chain server by running a request demonstrated in [test_chain_server.ipynb](./chain_server/test_chain_server.ipynb).

To bring down the chain server:
```sh
docker compose down chain-server
```

##### Connecting to ACE
Connect to this chain server from your ACE stack by specifying the `<host url>:<port number>` of the chain server. If you're running on a cloud service provider's instance, please ensure that the instance has a publicly accessible URL and the port is exposed. 

For the steps of standing up your digital human ACE stack, please see the [Digital Human Blueprint Card](https://build.nvidia.com/nvidia/digital-humans-for-customer-service/blueprintcard), [GitHub repo for NIM Agent Blueprint: Digital Human for Customer Service](https://github.com/NVIDIA-NIM-Agent-Blueprints/digital-human), and [ACE Documentation](https://docs.nvidia.com/ace/latest/index.html).

#### 2. If running the simple voice/text UI
To spin up a simple Gradio based web UI that allows us to converse with one of the agents via voice or typing, run one of these following services.

##### 2.1 The patient intake agent 
Run the patient intake only agent.

```sh
# to run the container with the assumption we have done build:
docker compose up -d patient-intake-ui
# or to build at this command:
docker compose up --build -d patient-intake-ui
```

Note this will be running on port 7860 by default. If you need to run on a different port, modify the [`docker-compose.yaml`](./docker-compose.yaml) file's `patient-intake-ui` section and replace all mentions of 7860 with your own port number.

[Launch the web UI](#25-launch-the-web-ui) on your Chrome browser, you should see this interface:
![](./images/example_ui.png)

To bring down the patient intake UI:
```sh
docker compose down patient-intake-ui
```


##### 2.2 The appointment making agent 
Run the appointment making only agent.
```sh
# to run the container with the assumption we have done build:
docker compose up -d appointment-making-ui
# or to build at this command:
docker compose up --build -d appointment-making-ui
```

Note this will be running on port 7860 by default. If you need to run on a different port, modify the [`docker-compose.yaml`](./docker-compose.yaml) file's `appointment-making-ui` section and replace all mentions of 7860 with your own port number.

[Launch the web UI](#25-launch-the-web-ui) on your Chrome browser, you should see the same web interface as above.

To bring down the appointment making UI:
```sh
docker compose down appointment-making-ui
```

##### 2.3 The full agent 
Run the full agent comprising of three specialist agents.
```sh
# to run the container with the assumption we have done build:
docker compose up -d full-agent-ui
# or to build at this command:
docker compose up --build -d full-agent-ui
```

Note this will be running on port 7860 by default. If you need to run on a different port, modify the [`docker-compose.yaml`](./docker-compose.yaml) file's `full-agent-ui` section and replace all mentions of 7860 with your own port number.

[Launch the web UI](#25-launch-the-web-ui) on your Chrome browser, you should see the same web interface as above.

To bring down the full agent UI:
```sh
docker compose down full-agent-ui
```

##### 2.4 The medication lookup agent 
Run the medication lookup only agent.

```sh
# to run the container with the assumption we have done build:
docker compose up -d medication-lookup-ui
# or to build at this command:
docker compose up --build -d medication-lookup-ui
```

Note this will be running on port 7860 by default. If you need to run on a different port, modify the [`docker-compose.yaml`](./docker-compose.yaml) file's `medication-lookup-ui` section and replace all mentions of 7860 with your own port number.

[Launch the web UI](#25-launch-the-web-ui) on your Chrome browser, you should see the same web interface as above.

To bring down the medication lookup UI:
```sh
docker compose down medication-lookup-ui
```

##### 2.5 Launch the web UI

Go to your web browser, here we have tested with Google Chrome, and type in `<your machine's ip address>:<port number>`. The port number would be `7860` by default, or your modified port number if you changed the port number in [docker-compose.yaml](./docker-compose.yaml). Please note that, before you can use your mic/speaker to interact with the web UI, you will need to enable the origin ([reference](https://github.com/NVIDIA/GenerativeAIExamples/blob/main/docs/using-sample-web-application.md#troubleshooting)):

If you receive the following `"Media devices could not be accessed"` error message when you first attempt to transcribe a voice query, perform the following steps.

1. Open another browser tab and enter `chrome://flags` in the location field.

1. Enter `insecure origins treated as secure` in the search field.

1. Enter `http://<host-ip>:7860` (or your own port number) in the text box and select **Enabled** from the menu.

1. Click **Relaunch**.

1. After the browser opens, grant `http://host-ip:7860` (or your own port number) access to your microphone.

1. Retry your request on the web UI.

