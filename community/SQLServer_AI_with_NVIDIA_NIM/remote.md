## **Remote Scenario**

### **Prerequisites**
1. **Local Installation of Windows:**
    - Same as above: Windows 11 Enterprise multi-session 24H2 26100.6899, SQL Server 2025 (RC), SSMS 11.0.0 Preview 3.0.
2. **Azure Cloud Account** with access to Azure Portal.

### **Installation Steps**
1. **Create Azure Container Apps (ACA):**
    - Use the Azure Portal, create Container Apps with defaults.
    - Ingress: ON, target port: 8000.
    - This provides the HTTPS address of the NIM endpoint.
2. **Configure Container Apps Environment:**
    - Use a Consumption base profile with NVIDIA A100 GPU (Consumption-GPU-NC24-A100).
    - GPU is used to run NIM containers.
    - Cost is only for compute time.
3. **Set Container Properties:**
    - Click *Containers* tab in the app.
    - Set ACA container name (e.g., ngc-test).
    - Image source: Docker HUB and other registries.
    - Image type: Private, Registry login: nvcr.io.
    - Image and tag: e.g., nim/nvidia/nv-embedqa-e5-v5:latest.
4. **Set Environment Variables:**
    - NGC_API_KEY: Application API key for NGC (nvcr.io).
    - OPENSSL_FORCE_FIPS_MODE: Set value to 0 (ACA does not support OpenSSL FIPS).
5. **Start Application:**
    - Wait until the ACA revision is running with assigned replicas.
6. **Ready to Use:**
    - The NIM endpoint is now available for remote communication.