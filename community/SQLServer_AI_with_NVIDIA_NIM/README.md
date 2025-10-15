## Running NVIDIA NIM with SQL Server 2025 (Windows + Ubuntu VM or WSL 2 + TLS)

### **Main Section**

[![Watch the video](https://img.youtube.com/vi/_DwH29OQIfw/hqdefault.jpg)](https://youtu.be/_DwH29OQIfw)

This guide explains how to securely connect **SQL Server 2025** (running on Windows) to **NVIDIA NIM** (running in Docker with GPU acceleration on Ubuntu), using **TLS certificates** for encryption and mutual trust.  
It supports two configurations:

[Watch the embedded YouTube video](https://www.youtube.com/embed/_DwH29OQIfw)

1. **Ubuntu as a separate VM** with its own IP (e.g., `192.168.10.218`)  
2. **Ubuntu as WSL 2 on the same Windows host**, reachable via `localhost`

---

### **Main Sections**

#### **0) Prerequisites**
- **Windows:** SQL Server 2025 Developer/Enterprise, PowerShell (admin), OpenSSH client, folder `C:\SQL2025`.  
- **Ubuntu:** Docker + NVIDIA toolkit, OpenSSL, NGC API key, port 8000 open (VM only).

---

#### **1) TLS Certificate Setup**
- Create Root CA (`ca_cert.pem`) and server key (`ssl_key.pem`).  
- **For Ubuntu VM:** certificate SAN includes `IP:192.168.10.218`.  
- **For WSL 2:** certificate SAN includes `DNS:localhost, IP:127.0.0.1`.

---

#### **2) Import the CA Certificate to Windows**
- **Ubuntu VM:** copy via `scp`  
  ```powershell
  scp user@192.168.10.218:/home/user/nim_certs/ca_cert.pem C:\SQL2025\nim-ca.cer
  ```
- **WSL 2:** copy directly  
  ```bash
  cp ~/nim_certs/ca_cert.pem /mnt/c/SQL2025/nim-ca.cer
  ```
- Import and restart SQL Server:
  ```powershell
  certutil -f -addstore Root "C:\SQL2025\nim-ca.cer"
  Get-Service *SQL* | ? {$_.Status -eq 'Running'} | Restart-Service
  ```

---

#### **3) Run NIM Container**
- Login to `nvcr.io` using NGC API key and pull:
  ```bash
  docker pull nvcr.io/nim/nvidia/nv-embedqa-e5-v5:latest
  ```
- **Ubuntu VM:** expose on all interfaces (`-p 0.0.0.0:8000:8000`)  
- **WSL 2:** expose to Windows via loopback (`-p 8000:8000`)  
- Enable TLS with mounted `ssl_key.pem` and `ssl_cert.pem`.

- ![Video](gifs/RunningNIM.gif)

---

#### **4) Verify with curl (from Windows)**
- **Ubuntu VM:**
  ```powershell
  curl --ssl-no-revoke --cacert C:\SQL2025\nim-ca.cer https://192.168.10.218:8000/v1/models
  ```
- **WSL 2:**
  ```powershell
  curl --ssl-no-revoke --cacert C:\SQL2025\nim-ca.cer https://localhost:8000/v1/models
  ```

---

#### **5) Enable REST Integration in SQL Server**
Enable the built-in REST endpoint feature:
```sql
EXEC sp_configure 'external rest endpoint enabled', 1;
RECONFIGURE WITH OVERRIDE;
```
Grant permission (if not sysadmin):
```sql
GRANT EXECUTE ANY EXTERNAL ENDPOINT TO [YourLogin];
```

---

#### **6) Test SQL Server Integration**
- **Direct REST Call**
  ```sql
  DECLARE @Url nvarchar(4000)=N'https://<SERVER_OR_LOCALHOST>:8000/v1/embeddings';
  EXEC sys.sp_invoke_external_rest_endpoint @url=@Url, ...
  ```
- **AI_GENERATE_EMBEDDINGS Model**
  ```sql
  CREATE EXTERNAL MODEL [EmbedE5_OpenAI]
  WITH (LOCATION='https://<SERVER_OR_LOCALHOST>:8000/v1/embeddings', API_FORMAT='OpenAI', MODEL_TYPE=EMBEDDINGS);
  SELECT AI_GENERATE_EMBEDDINGS(N'Test' USE MODEL EmbedE5_OpenAI);
  ```

---

#### **7) Diagnostics**
- **Common fixes:**
  - Use `--ssl-no-revoke` to skip CRL checks.
  - Re-import CA if TLS fails.
  - Use `/v1/embeddings` path exactly.
  - Firewall only required for VM case.

---

### **Key Differences Between VM and WSL 2**

| Aspect | Ubuntu VM | Ubuntu WSL 2 |
|--------|------------|--------------|
| Server Address | `192.168.10.218` | `localhost` |
| Certificate SAN | `IP:192.168.10.218` | `DNS:localhost, IP:127.0.0.1` |
| Copy Method | `scp` over SSH | `cp /mnt/c/...` |
| Firewall | Required | Not required |
| SQL/REST URL | `https://192.168.10.218:8000/...` | `https://localhost:8000/...` |

---

✅ **End Result:**  
You can run NVIDIA NIM securely with GPU support and TLS from **either** an Ubuntu VM or WSL 2 instance, and interact seamlessly with **SQL Server 2025** via REST or `AI_GENERATE_EMBEDDINGS`.

