# NVIDIA AI Foundation

**NVIDIA AI Foundation** lets developers to experience state of the art LLMs accelerated by NVIDIA. Developers get **free credits for 10K requests** to any of the available models. 

## Prepare the environment

1.  Navigate to https://catalog.ngc.nvidia.com/ai-foundation-models.

2. Find the <i>Llama 2 13B</i> model icon and click ``Learn More``.

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

2. Add your NGC API key to <i>compose.env</i> to use the NVIDIA endpoint.

```
$ cd GenerativeAIExamples
 
$ grep AI deploy/compose/compose.env
 export AI_PLAYGROUND_API_KEY="nvapi-*"
```
3. Deploy the developer RAG example via Docker compose.

```
$ source deploy/compose/compose.env;  docker compose -f deploy/compose/docker-compose-playground.yaml build

$ docker compose -f deploy/compose/docker-compose-palyground.yaml up -d

$ docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
CONTAINER ID   NAMES               STATUS
4cae4d242d12   llm-playground      Up 4 minutes
1c8383b10866   chain-server        Up 4 minutes
26c3d00367e4   milvus-standalone   Up 4 minutes (healthy)
3a0a0d719d09   milvus-minio        Up 4 minutes (healthy)
8e29db31f0de   notebook-server     Up 4 minutes
a9711883dc50   evaluation          Up 4 minutes
f2bee65460d0   milvus-etcd         Up 4 minutes (healthy)
```

## Test

1. Follow steps 1 - 5 in the ["Test" section of example 02](../../RetrievalAugmentedGeneration/README.md#02-test).

## Learn more

Example [notebook 6](../../notebooks/06_AI_playground.ipynb) showcases the usage of AI Playground based LLM. 

1. Access the notebook server at `http://host-ip:8888` from your web browser.

