import requests
from huggingface_hub import HfApi


def create_namespaces(entity_host, ds_host, namespace):
    # Create namespace in entity store
    entity_store_url = f"{entity_host}/v1/namespaces"
    resp = requests.post(entity_store_url, json={"id": namespace})
    assert resp.status_code in (200, 201, 409, 422), \
        f"Unexpected response from Entity Store during Namespace creation: {resp.status_code}"

    # Create namespace in datastore
    nds_url = f"{ds_host}/v1/datastore/namespaces"
    resp = requests.post(nds_url, data={"namespace": namespace})
    assert resp.status_code in (200, 201, 409, 422), \
        f"Unexpected response from datastore during Namespace creation: {resp.status_code}"
    

def setup_dataset_repo(hf_api, namespace, dataset_name, entity_host):
    repo_id = f"{namespace}/{dataset_name}"
    # Create the repo in datastore
    hf_api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    # Register dataset in entity store
    entity_store_url = f"{entity_host}/v1/datasets"
    payload = {
        "name": dataset_name,
        "namespace": namespace,
        "files_url": f"hf://datasets/{repo_id}",
    }
    resp = requests.post(entity_store_url, json=payload)
    assert resp.status_code in (200, 201, 409, 422), \
        f"Unexpected response from Entity Store creating dataset: {resp.status_code}"
    return repo_id
