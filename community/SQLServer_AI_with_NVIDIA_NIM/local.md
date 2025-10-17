## **Local Scenario**

### **1. TLS Certificate Setup**
- Create Root CA (`ca_cert.pem`) and server key (`ssl_key.pem`).
- For Ubuntu VM: certificate SAN includes IP:192.168.10.218.
- For WSL 2: certificate SAN includes DNS:localhost, IP:127.0.0.1.

### **2. Import the CA Certificate to Windows**
- **Ubuntu VM:** Copy via scp  
  `scp user@192.168.10.218:/home/user/nim_certs/ca_cert.pem C:\SQL2025\nim-ca.cer`
- **WSL 2:** Copy directly  
  `cp ~/nim_certs/ca_cert.pem /mnt/c/SQL2025/nim-ca.cer`
- **Import and restart SQL Server:**  
  `certutil -f -addstore Root "C:\SQL2025\nim-ca.cer"`  
  `Get-Service SQL | ? {$_.Status -eq 'Running'} | Restart-Service`

### **3. Run NIM Container**
- Login to nvcr.io using NGC API key and pull:  
  `docker pull nvcr.io/nim/nvidia/nv-embedqa-e5-v5:latest`
- **Ubuntu VM:** Expose on all interfaces:  
  `-p 0.0.0.0:8000:8000`
- **WSL 2:** Expose to Windows via loopback:  
  `-p 8000:8000`
- Enable TLS with mounted ssl_key.pem and ssl_cert.pem.

### **4. Verify with curl (from Windows)**
- **Ubuntu VM:**  
  `curl --ssl-no-revoke --cacert C:\SQL2025\nim-ca.cer https://192.168.10.218:8000/v1/models`
- **WSL 2:**  
  `curl --ssl-no-revoke --cacert C:\SQL2025\nim-ca.cer https://localhost:8000/v1/models`

### **5. Enable REST Integration in SQL Server**
Enable the built-in REST endpoint feature:  
`EXEC sp_configure 'external rest endpoint enabled', 1;`  
`RECONFIGURE WITH OVERRIDE;`
Grant permission (if not sysadmin):  
`GRANT EXECUTE ANY EXTERNAL ENDPOINT TO [YourLogin];`

### **6. Test SQL Server Integration**
- **Direct REST Call**  
  `DECLARE @Url nvarchar(4000)=N'https://<SERVER_OR_LOCALHOST>:8000/v1/embeddings';`  
  `EXEC sys.sp_invoke_external_rest_endpoint @url=@Url, ...;`
- **AI_GENERATE_EMBEDDINGS Model**  
  `CREATE EXTERNAL MODEL [EmbedE5_OpenAI]`  
  `WITH (LOCATION='https://<SERVER_OR_LOCALHOST>:8000/v1/embeddings', API_FORMAT='OpenAI', MODEL_TYPE=EMBEDDINGS);`  
  `SELECT AI_GENERATE_EMBEDDINGS(N'Test' USE MODEL EmbedE5_OpenAI);`

---

## **Key Differences Between VM and WSL 2**

| **Aspect**            | **Ubuntu VM**            | **Ubuntu WSL 2**                |
|-----------------------|-------------------------|----------------------------------|
| Server Address        | 192.168.10.218          | localhost                        |
| Certificate SAN       | IP:192.168.10.218       | DNS:localhost, IP:127.0.0.1      |
| Copy Method           | scp over SSH            | cp /mnt/c/...                    |
| Firewall              | Required                | Not required                     |
| SQL/REST URL          | https://192.168.10.218:8000/... | https://localhost:8000/... |