# Running NVIDIA NIM with SQL Server 2025 AI on Azure Cloud and Azure Local

---

## Abstract

Unlock newly announced AI features in Microsoft SQL Server 2025 using NVIDIA NIM Microservices for accelerated AI inference on both Azure Cloud and Azure Local.  
This guide demonstrates efficient and secure integration of Microsoft SQL Server 2025 with NVIDIA NeMo Retrieval E5 Embedding v5, running in the cloud via Azure Container Apps and on-premises using Azure Local with Windows, WSL 2, and/or Ubuntu.  
The guide provides an enterprise-level architecture and a demo implementation leveraging the latest versions of Microsoft SQL Server and NVIDIA NeMo Text Embedding NIM.

---

## Overview

Microsoft SQL Server 2025 introduces several new features. One of the most notable is AI Integration, which includes:
- AI-Enhanced Analytics: Improved support for embedding and leveraging AI models, including new system stored procedures for scoring and prediction.
- External REST Endpoints: New T-SQL commands to invoke REST APIs (including AI services) directly from SQL Server, such as sp_invoke_external_rest_endpoint.

Implementation of these features is mostly based on integration with Azure OpenAI and Ollama services.  
This repository demonstrates a new approach using NVIDIA NIM Microservices to perform enterprise-level, secure, GPU-accelerated, Docker-based SQL Server inference with custom models on Azure Cloud and/or Azure Local.

---

## Architecture

Below is the proposed architecture (Pic 1):

Pic.1: Architecture Diagram Placeholder

**Key Points:**
- New AI functionality is based on secure (HTTPS) communication with external endpoints to SQL Server, which could be in the cloud or on-premises.
- SQL Server sends POST requests to endpoints and retrieves requested information (such as embeddings).
- External services should support existing communication protocols implanted in SQL Server (OpenAI, Ollama etc.)
- External services must provide secure, fast, standard responses using custom inference models, for both cloud and on-premises scenarios.
- Meets SQL Server requirements for security, performance, and ease of deployment.

**Highlights of proposed approach**
- NVIDIA Enterprise NIMs provide optimized inference models running on GPU.
- All NIMs use Docker containers, simplifying deployment and ensuring compatibility across cloud and local Windows/Linux environments with NVIDIA GPU.
- NVIDIA NIM supports OpenAI standards.
- It provides secure, direct communication (TLS certificates for encryption and mutual trust) for on-premises deployment.
- For remote (cloud) deployment, Azure Container Apps are used, connecting directly to the NVIDIA NIM repository for always-up-to-date models.
- Inference models can be changed by customers.

**Benefits:**
- Serverless container orchestration (no infrastructure management like AKS)
- Flexible manual/automatic scaling
- Event-driven architecture (HTTPS requests)
- Cost efficiency (pay only for compute time)
- High developer productivity and simplicity. No extra development is required—just correct environment settings, parameters, certificates, and adherence to standards.
- Managed, secure environment
- Fast provisioning and updates from NVIDIA NIM repository
- Multi-container support

---

## Demo

This section explains how to use the proposed architecture for SQL Server 2025 AI functionality with NVIDIA Retrieval QA using E5 Embedding v5.

**Scenarios demonstrated:**
- Remote (Azure Cloud): Using Azure Container Apps as a wrapper for NVIDIA NIMs. SQL Server 2025 can be installed locally or on cloud.
- On-premises (Azure Local): Using Azure Local GPU-based VMs (Windows 11 VM and Ubuntu 24.04 VM). The same approach applies to other local GPU setups.

**Covers:**
- Windows Server, Windows 11, or Windows VM
- Azure Local with Windows VM, WSL 2, Docker Desktop, SQL Server 2025
- Linux or Linux VM, Azure Local with Linux VM, Docker, SQL Server 2025
- Hybrid: Windows VM and Linux VM (current demo)

---

## Demo Prerequisites

- Azure Local Windows VM:
  - Windows 11 Enterprise multi-session 24H2 26100.6899
  - SQL Server 2025 (RC) – 17.0.950.3
  - SQL Server 2025 Management Studio 11.0.0 Preview 3.0
- Ubuntu VM:
  - Ubuntu 22.04.2 LTS
  - Dedicated IP (e.g., 192.168.10.218)
  - NVIDIA L4 GPU, Driver 580.82.07, CUDA 13.0
  - OpenSSL, NGC API key, port 8000 open

---

## Local Scenario

### 1. TLS Certificate Setup
- Create Root CA (ca_cert.pem) and server key (ssl_key.pem).
- For Ubuntu VM: certificate SAN includes IP:192.168.10.218.
- For WSL 2: certificate SAN includes DNS:localhost, IP:127.0.0.1.

### 2. Import the CA Certificate to Windows
- Ubuntu VM: Copy via scp  
  `scp user@192.168.10.218:/home/user/nim_certs/ca_cert.pem C:\SQL2025\nim-ca.cer`
- WSL 2: Copy directly  
  `cp ~/nim_certs/ca_cert.pem /mnt/c/SQL2025/nim-ca.cer`
- Import and restart SQL Server:  
  `certutil -f -addstore Root "C:\SQL2025\nim-ca.cer"`  
  `Get-Service SQL | ? {$_.Status -eq 'Running'} | Restart-Service`

### 3. Run NIM Container
- Login to nvcr.io using NGC API key and pull:  
  `docker pull nvcr.io/nim/nvidia/nv-embedqa-e5-v5:latest`
- Ubuntu VM: Expose on all interfaces:  
  `-p 0.0.0.0:8000:8000`
- WSL 2: Expose to Windows via loopback:  
  `-p 8000:8000`
- Enable TLS with mounted ssl_key.pem and ssl_cert.pem.

### 4. Verify with curl (from Windows)
- Ubuntu VM:  
  `curl --ssl-no-revoke --cacert C:\SQL2025\nim-ca.cer https://192.168.10.218:8000/v1/models`
- WSL 2:  
  `curl --ssl-no-revoke --cacert C:\SQL2025\nim-ca.cer https://localhost:8000/v1/models`

### 5. Enable REST Integration in SQL Server
Enable the built-in REST endpoint feature:  
`EXEC sp_configure 'external rest endpoint enabled', 1;`  
`RECONFIGURE WITH OVERRIDE;`
Grant permission (if not sysadmin):  
`GRANT EXECUTE ANY EXTERNAL ENDPOINT TO [YourLogin];`

### 6. Test SQL Server Integration
- Direct REST Call  
  `DECLARE @Url nvarchar(4000)=N'https://<SERVER_OR_LOCALHOST>:8000/v1/embeddings';`  
  `EXEC sys.sp_invoke_external_rest_endpoint @url=@Url, ...;`
- AI_GENERATE_EMBEDDINGS Model  
  `CREATE EXTERNAL MODEL [EmbedE5_OpenAI]`  
  `WITH (LOCATION='https://<SERVER_OR_LOCALHOST>:8000/v1/embeddings', API_FORMAT='OpenAI', MODEL_TYPE=EMBEDDINGS);`  
  `SELECT AI_GENERATE_EMBEDDINGS(N'Test' USE MODEL EmbedE5_OpenAI);`

---

## Key Differences Between VM and WSL 2

| Aspect            | Ubuntu VM            | Ubuntu WSL 2                |
|-------------------|---------------------|-----------------------------|
| Server Address    | 192.168.10.218      | localhost                   |
| Certificate SAN   | IP:192.168.10.218   | DNS:localhost, IP:127.0.0.1 |
| Copy Method       | scp over SSH        | cp /mnt/c/...               |
| Firewall          | Required            | Not required                |
| SQL/REST URL      | https://192.168.10.218:8000/... | https://localhost:8000/... |

---

## Remote Scenario

### Prerequisites
1. Local Installation of Windows:
    - Same as above: Windows 11 Enterprise multi-session 24H2 26100.6899, SQL Server 2025 (RC), SSMS 11.0.0 Preview 3.0.
2. Azure Cloud Account with access to Azure Portal.

### Installation Steps
1. Create Azure Container Apps (ACA):
    - Use the Azure Portal, create Container Apps with defaults.
    - Ingress: ON, target port: 8000.
    - This provides the HTTPS address of the NIM endpoint.
2. Configure Container Apps Environment:
    - Use a Consumption base profile with NVIDIA A100 GPU (Consumption-GPU-NC24-A100).
    - GPU is used to run NIM containers.
    - Cost is only for compute time.
3. Set Container Properties:
    - Click Containers tab in the app.
    - Set ACA container name (e.g., ngc-test).
    - Image source: Docker HUB and other registries.
    - Image type: Private, Registry login: nvcr.io.
    - Image and tag: e.g., nim/nvidia/nv-embedqa-e5-v5:latest.
4. Set Environment Variables:
    - NGC_API_KEY: Application API key for NGC (nvcr.io).
    - OPENSSL_FORCE_FIPS_MODE: Set value to 0 (ACA does not support OpenSSL FIPS).
5. Start Application:
    - Wait until the ACA revision is running with assigned replicas.
6. Ready to Use:
    - The NIM endpoint is now available for remote communication.

---

## Running the Demo

- SQL scripts to demonstrate SQL Server communication with NVIDIA NIM for remote and local scenarios are in the scripts folder.
- Database for the demo can be generated using AdventureWorks.bacpac (copy in /data).
- Run scripts in order (as in demo video):
    1. Create AdventureWorks database.
    2. Create ProductDescriptionEmbeddings table.
    3. Check the table and view embeddings with Select_Embeddings.sql.
    4. Run proc*.sql scripts to register in the demo database.
    5. Create/modify External Model with the correct NIM location (local or remote).
    6. Execute demo scripts to populate embeddings via NVIDIA NIM.
    7. Verify using Select_Embeddings.sql again.

---

## References

- Microsoft SQL Server 2025 Docs
- NVIDIA NIM Documentation
- Azure Container Apps Documentation