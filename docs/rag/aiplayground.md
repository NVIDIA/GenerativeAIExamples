# NVIDIA AI Foundation

**NVIDIA AI Foundation** lets developers to experience state of the art LLMs accelerated by NVIDIA. Developers get **free credits for 10K requests** to any of the available models. 

## Prepare the environment

1.  Navigate to https://catalog.ngc.nvidia.com/ai-foundation-models.

2. Select any model and click ``Learn More``.

![Diagram](./images/image5.png)

3. Select the ```API``` navigation bar and click on the ```Generate key``` option..

![Diagram](./images/image6.png)

4. Save the generated API key.

## Deploy

1.  Clone the Generative AI examples Git repository. 

> ⚠️ **NOTE**: This example requires Git Large File Support (LFS)

```
$ sudo apt -y install git-lfs
$ git lfs pull
$ git clone git@github.com:NVIDIA/GenerativeAIExamples.git
Cloning into 'GenerativeAIExamples'...
```

2. Configure <i>compose.env</i> to use the NVIDIA endpoint.

```
  export AI_PLAYGROUND_API_KEY="nvapi-*"
```
3. Deploy the developer RAG example via Docker compose.

```
$ source compose.env; docker compose build

$ source compose.env; docker compose up -d

$ docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
CONTAINER ID   NAMES                     STATUS
853b74f11e65   llm-playground            Up 15 minutes
9964f1a797a3   query-router              Up 15 minutes
e3e3d4871f1a   jupyter-notebook-server   Up 15 minutes
09150764b74a   triton-inference-server   Up 15 minutes (unhealthy)
2285b01dbe0c   milvus-standalone         Up 40 minutes (healthy)
2c96084539ce   milvus-minio              Up 40 minutes (healthy)
a839261973b8   milvus-etcd               Up 40 minutes (healthy)
```

## Test

- Interact with the pipeline using UI as as mentioned [here.](../../RetrievalAugmentedGeneration/README.md#step-4-run-the-sample-web-application)

- Example [notebook 6](../../notebooks/06_AI_playground.ipynb) showcases the usage of AI Playground based LLM. You can access the notebook server at `http://host-ip:8888` from your web browser.

