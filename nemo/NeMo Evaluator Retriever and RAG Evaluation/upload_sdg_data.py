import huggingface_hub as hh
import requests

nmm_url = "https://datastore.stg.llm.ngc.nvidia.com"
token = "mock"
repo_name = "SDG_BEIR"
dir_path = "./synthetic"

# create repo
datasets_endpoint = nmm_url + "/v1/datasets"
post_body = {
  "name": repo_name,
  "description": "BEIR Data Created with SDG Pipeline"
}
repo_response = requests.post(datasets_endpoint, json=post_body, allow_redirects=True)

# upload dir
repo_full_name = f"nvidia/{repo_name}"
path_in_repo = "."
repo_type ="dataset"
hf_api = hh.HfApi(endpoint=nmm_url, token=token)
result = hf_api.upload_folder(repo_id=repo_full_name, folder_path=dir_path, path_in_repo=path_in_repo, repo_type=repo_type)

print(f"Dataset folder uploaded to: {result}")