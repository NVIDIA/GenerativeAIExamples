# SQL Query and Retrieve Tool Configuration Guide

This comprehensive guide explains how to configure the SQL Query and Retrieve Tool, covering both vector store backends and SQL database connections.

## Table of Contents
1. [Vector Store Configuration](#vector-store-configuration)
2. [SQL Database Configuration](#sql-database-configuration)
3. [Complete Configuration Examples](#complete-configuration-examples)
4. [Troubleshooting](#troubleshooting)

---

## Vector Store Configuration

### Overview

The tool supports **two vector store backends** for storing Vanna AI SQL training data:
- **ChromaDB** (local, file-based) - Default
- **Elasticsearch** (distributed, server-based)

Both vector stores provide identical functionality and store the same data (DDL, documentation, question-SQL pairs).

### Quick Start - Vector Stores

#### Option 1: ChromaDB (Recommended for Development)

```yaml
functions:
  - name: my_sql_tool
    type: generate_sql_query_and_retrieve_tool
    llm_name: nim_llm
    embedding_name: nim_embeddings
    
    # ChromaDB Configuration (DEFAULT)
    vector_store_type: chromadb
    vector_store_path: ./vanna_vector_store
    
    # Database and other settings...
    db_connection_string_or_path: ./database.db
    db_type: sqlite
    output_folder: ./output
    vanna_training_data_path: ./training_data.yaml
```

**Requirements:**
- No additional services required
- No extra Python packages needed

#### Option 2: Elasticsearch (Recommended for Production)

```yaml
functions:
  - name: my_sql_tool
    type: generate_sql_query_and_retrieve_tool
    llm_name: nim_llm
    embedding_name: nim_embeddings
    
    # Elasticsearch Configuration
    vector_store_type: elasticsearch
    elasticsearch_url: http://localhost:9200
    elasticsearch_index_name: vanna_sql_vectors  # Optional
    elasticsearch_username: elastic              # Optional
    elasticsearch_password: changeme             # Optional
    
    # Database and other settings...
    db_connection_string_or_path: ./database.db
    db_type: sqlite
    output_folder: ./output
    vanna_training_data_path: ./training_data.yaml
```

**Requirements:**
- Elasticsearch service must be running
- Install: `pip install elasticsearch`

### Detailed Comparison - Vector Stores

| Feature | ChromaDB | Elasticsearch |
|---------|----------|---------------|
| **Setup Complexity** | Simple | Moderate |
| **External Services** | None required | Requires ES cluster |
| **Storage Type** | Local file-based | Distributed |
| **High Availability** | No | Yes (with clustering) |
| **Horizontal Scaling** | No | Yes |
| **Best For** | Dev, testing, single-server | Production, multi-user |
| **Authentication** | File system | API key or basic auth |
| **Performance** | Fast for single-user | Fast for multi-user |
| **Backup** | Copy directory | ES snapshots |

### When to Use Each Vector Store

#### Use ChromaDB When:
✅ Getting started or prototyping  
✅ Single-server deployment  
✅ Local development environment  
✅ Simple setup required  
✅ No existing Elasticsearch infrastructure  
✅ Small to medium data volume  

#### Use Elasticsearch When:
✅ Production environment  
✅ Multiple instances/users need access  
✅ Need high availability and clustering  
✅ Already have Elasticsearch infrastructure  
✅ Need advanced search capabilities  
✅ Distributed deployment required  
✅ Large scale deployments  

### Vector Store Configuration Parameters

#### Common Parameters (Both Vector Stores)
```yaml
llm_name: string                          # LLM to use
embedding_name: string                    # Embedding model to use
db_connection_string_or_path: string      # Database connection
db_type: string                           # 'sqlite', 'postgres', or 'sql'
output_folder: string                     # Output directory
vanna_training_data_path: string          # Training data YAML file
```

#### ChromaDB-Specific Parameters
```yaml
vector_store_type: chromadb              # Set to 'chromadb'
vector_store_path: string                # Directory for ChromaDB storage
```

#### Elasticsearch-Specific Parameters
```yaml
vector_store_type: elasticsearch         # Set to 'elasticsearch'
elasticsearch_url: string                # ES URL (e.g., http://localhost:9200)
elasticsearch_index_name: string         # Index name (default: vanna_vectors)
elasticsearch_username: string           # Optional: for basic auth
elasticsearch_password: string           # Optional: for basic auth
elasticsearch_api_key: string            # Optional: alternative to username/password
```

### Elasticsearch Authentication

Choose one of these authentication methods:

#### Option 1: API Key (Recommended)
```yaml
elasticsearch_api_key: your-api-key-here
```

#### Option 2: Basic Auth
```yaml
elasticsearch_username: elastic
elasticsearch_password: changeme
```

#### Option 3: No Auth (Development Only)
```yaml
# Omit all auth parameters
```

### Data Migration Between Vector Stores

#### From ChromaDB to Elasticsearch
1. Export training data from ChromaDB
2. Update configuration to use Elasticsearch
3. Run tool - it will auto-initialize Elasticsearch with training data

#### From Elasticsearch to ChromaDB
1. Training data is reloaded from YAML file automatically
2. Update configuration to use ChromaDB
3. Run tool - it will auto-initialize ChromaDB

### Vector Store Troubleshooting

#### ChromaDB Issues
**Problem:** `FileNotFoundError` or permission errors  
**Solution:** Ensure directory exists and has write permissions

**Problem:** Slow performance  
**Solution:** ChromaDB is single-threaded, consider Elasticsearch for better performance

#### Elasticsearch Issues
**Problem:** `ConnectionError` or `ConnectionTimeout`  
**Solution:** Verify Elasticsearch is running: `curl http://localhost:9200`

**Problem:** `AuthenticationException`  
**Solution:** Check username/password or API key

**Problem:** Index already exists with different mapping  
**Solution:** Delete index and let tool recreate: `curl -X DELETE http://localhost:9200/vanna_vectors`

---

## SQL Database Configuration

### Overview

The tool supports **multiple SQL database types** through a unified `db_connection_string_or_path` parameter:
- **SQLite** (local, file-based) - Default
- **PostgreSQL** (open-source RDBMS)
- **MySQL** (open-source RDBMS)
- **SQL Server** (Microsoft database)
- **Oracle** (enterprise database)
- **Any SQLAlchemy-compatible database**

### Quick Start - SQL Databases

#### Option 1: SQLite (File-Based, No Server Required)

```yaml
db_connection_string_or_path: ./database.db  # Just a file path
db_type: sqlite
```

**Requirements:**
- No additional services required
- No extra Python packages needed (sqlite3 is built-in)

#### Option 2: PostgreSQL

```yaml
db_connection_string_or_path: postgresql://user:password@localhost:5432/database
db_type: postgres
```

**Requirements:**
- PostgreSQL server must be running
- Install: `pip install psycopg2-binary`

#### Option 3: MySQL

```yaml
db_connection_string_or_path: mysql+pymysql://user:password@localhost:3306/database
db_type: sql  # Generic SQL via SQLAlchemy
```

**Requirements:**
- MySQL server must be running
- Install: `pip install pymysql sqlalchemy`

#### Option 4: SQL Server

```yaml
db_connection_string_or_path: mssql+pyodbc://user:pass@host:1433/db?driver=ODBC+Driver+17+for+SQL+Server
db_type: sql  # Generic SQL via SQLAlchemy
```

**Requirements:**
- SQL Server must be running
- Install: `pip install pyodbc sqlalchemy`
- Install ODBC Driver for SQL Server

#### Option 5: Oracle

```yaml
db_connection_string_or_path: oracle+cx_oracle://user:password@host:1521/?service_name=service
db_type: sql  # Generic SQL via SQLAlchemy
```

**Requirements:**
- Oracle database must be running
- Install: `pip install cx_Oracle sqlalchemy`

### Detailed Comparison - SQL Databases

| Feature | SQLite | PostgreSQL | MySQL | SQL Server | Oracle |
|---------|--------|------------|-------|------------|--------|
| **Setup** | None | Server required | Server required | Server required | Server required |
| **Cost** | Free | Free | Free | Licensed | Licensed |
| **Use Case** | Dev/testing | Production | Production | Enterprise | Enterprise |
| **Concurrent Users** | Limited | Excellent | Excellent | Excellent | Excellent |
| **File-Based** | Yes | No | No | No | No |
| **Advanced Features** | Basic | Advanced | Good | Advanced | Advanced |
| **Python Driver** | Built-in | psycopg2 | pymysql | pyodbc | cx_Oracle |

### When to Use Each Database

#### Use SQLite When:
✅ Development and testing  
✅ Prototyping and demos  
✅ Single-user applications  
✅ No server infrastructure required  
✅ Small to medium data volume  
✅ Embedded applications  
✅ Quick setup needed  

#### Use PostgreSQL When:
✅ Production deployments  
✅ Multi-user applications  
✅ Need advanced SQL features  
✅ Open-source preference  
✅ Need strong data integrity  
✅ Complex queries and analytics  
✅ GIS data support needed  

#### Use MySQL When:
✅ Web applications  
✅ Read-heavy workloads  
✅ Need wide compatibility  
✅ Open-source preference  
✅ Large-scale deployments  
✅ Replication required  

#### Use SQL Server When:
✅ Microsoft ecosystem  
✅ Enterprise applications  
✅ .NET integration needed  
✅ Advanced analytics (T-SQL)  
✅ Business intelligence  
✅ Existing SQL Server infrastructure  

#### Use Oracle When:
✅ Large enterprise deployments  
✅ Mission-critical applications  
✅ Need advanced features (RAC, Data Guard)  
✅ Existing Oracle infrastructure  
✅ High-availability requirements  
✅ Maximum performance needed  

### Connection String Formats

#### SQLite
```
Format: /path/to/database.db
Example: ./data/sales.db
Example: /var/app/database.db
```

#### PostgreSQL
```
Format: postgresql://username:password@host:port/database
Example: postgresql://admin:secret@db.example.com:5432/sales_db
Example: postgresql://user:pass@localhost:5432/mydb
```

#### MySQL
```
Format: mysql+pymysql://username:password@host:port/database
Example: mysql+pymysql://root:password@localhost:3306/inventory
Example: mysql+pymysql://dbuser:pass@192.168.1.10:3306/analytics
```

#### SQL Server
```
Format: mssql+pyodbc://user:pass@host:port/db?driver=ODBC+Driver+XX+for+SQL+Server
Example: mssql+pyodbc://sa:MyPass@localhost:1433/sales?driver=ODBC+Driver+17+for+SQL+Server
Example: mssql+pyodbc://user:pwd@server:1433/db?driver=ODBC+Driver+18+for+SQL+Server
```

#### Oracle
```
Format: oracle+cx_oracle://username:password@host:port/?service_name=service
Example: oracle+cx_oracle://admin:secret@localhost:1521/?service_name=ORCLPDB
Example: oracle+cx_oracle://user:pass@oracledb:1521/?service_name=PROD
```

### Database Configuration Parameters

```yaml
db_connection_string_or_path: string  # Path (SQLite) or connection string (others)
db_type: string                       # 'sqlite', 'postgres', or 'sql'
```

**db_type values:**
- `sqlite` - For SQLite databases (uses connect_to_sqlite internally)
- `postgres` or `postgresql` - For PostgreSQL databases (uses connect_to_postgres)
- `sql` - For generic SQL databases via SQLAlchemy (MySQL, SQL Server, Oracle, etc.)

### SQL Database Troubleshooting

#### SQLite Issues
**Problem:** `database is locked` error  
**Solution:** Close all connections or use WAL mode

**Problem:** `unable to open database file`  
**Solution:** Check file path and permissions

#### PostgreSQL Issues
**Problem:** `connection refused`  
**Solution:** Check PostgreSQL is running: `systemctl status postgresql`

**Problem:** `authentication failed`  
**Solution:** Verify credentials and check pg_hba.conf

**Problem:** `database does not exist`  
**Solution:** Create database: `createdb database_name`

#### MySQL Issues
**Problem:** `Access denied for user`  
**Solution:** Check credentials and user permissions: `GRANT ALL ON db.* TO 'user'@'host'`

**Problem:** `Can't connect to MySQL server`  
**Solution:** Check MySQL is running: `systemctl status mysql`

#### SQL Server Issues
**Problem:** `Login failed for user`  
**Solution:** Check SQL Server authentication mode and user permissions

**Problem:** `ODBC Driver not found`  
**Solution:** Install ODBC Driver: Download from Microsoft

**Problem:** `SSL Provider: No credentials are available`  
**Solution:** Add `TrustServerCertificate=yes` to connection string

#### Oracle Issues
**Problem:** `ORA-12541: TNS:no listener`  
**Solution:** Start Oracle listener: `lsnrctl start`

**Problem:** `ORA-01017: invalid username/password`  
**Solution:** Verify credentials and user exists

**Problem:** `cx_Oracle.DatabaseError`  
**Solution:** Check Oracle client libraries are installed

### Required Python Packages by Database

```bash
# SQLite (built-in, no packages needed)
# Already included with Python

# PostgreSQL
pip install psycopg2-binary

# MySQL
pip install pymysql sqlalchemy

# SQL Server
pip install pyodbc sqlalchemy
# Also install: Microsoft ODBC Driver for SQL Server

# Oracle
pip install cx_Oracle sqlalchemy
# Also install: Oracle Instant Client

# Generic SQL (covers MySQL, SQL Server, Oracle via SQLAlchemy)
pip install sqlalchemy
```

---

## Complete Configuration Examples

### Example 1: SQLite with ChromaDB (Simplest Setup)
```yaml
functions:
  - name: simple_sql_tool
    type: generate_sql_query_and_retrieve_tool
    llm_name: nim_llm
    embedding_name: nim_embeddings
    # Vector store
    vector_store_type: chromadb
    vector_store_path: ./vanna_vector_store
    # Database
    db_connection_string_or_path: ./database.db
    db_type: sqlite
    # Output
    output_folder: ./output
    vanna_training_data_path: ./training_data.yaml
```

### Example 2: PostgreSQL with Elasticsearch (Production Setup)
```yaml
functions:
  - name: production_sql_tool
    type: generate_sql_query_and_retrieve_tool
    llm_name: nim_llm
    embedding_name: nim_embeddings
    # Vector store
    vector_store_type: elasticsearch
    elasticsearch_url: http://elasticsearch:9200
    elasticsearch_username: elastic
    elasticsearch_password: changeme
    # Database
    db_connection_string_or_path: postgresql://dbuser:dbpass@postgres:5432/analytics
    db_type: postgres
    # Output
    output_folder: ./output
    vanna_training_data_path: ./training_data.yaml
```

### Example 3: MySQL with ChromaDB
```yaml
functions:
  - name: mysql_sql_tool
    type: generate_sql_query_and_retrieve_tool
    llm_name: nim_llm
    embedding_name: nim_embeddings
    # Vector store
    vector_store_type: chromadb
    vector_store_path: ./vanna_vector_store
    # Database
    db_connection_string_or_path: mysql+pymysql://root:password@localhost:3306/sales
    db_type: sql
    # Output
    output_folder: ./output
    vanna_training_data_path: ./training_data.yaml
```

---

## Architecture Notes

Both vector stores:
- Use the same NVIDIA embedding models
- Store identical training data
- Provide the same vector similarity search
- Are managed automatically by VannaManager
- Support the same training data YAML format

The tool automatically:
- Detects if vector store needs initialization
- Loads training data from YAML file
- Creates embeddings using NVIDIA models
- Manages vector store lifecycle

### Performance Tips

#### ChromaDB
- Keep on SSD for faster I/O
- Regular directory backups
- Monitor disk space

#### Elasticsearch
- Use SSD-backed storage
- Configure appropriate heap size
- Enable index caching
- Use snapshots for backups
- Monitor cluster health

---

## Quick Reference

### Configuration Matrix

| Database | Vector Store | db_type | Connection Format |
|----------|--------------|---------|-------------------|
| SQLite | ChromaDB | sqlite | `./database.db` |
| SQLite | Elasticsearch | sqlite | `./database.db` |
| PostgreSQL | ChromaDB | postgres | `postgresql://user:pass@host:port/db` |
| PostgreSQL | Elasticsearch | postgres | `postgresql://user:pass@host:port/db` |
| MySQL | ChromaDB | sql | `mysql+pymysql://user:pass@host:port/db` |
| MySQL | Elasticsearch | sql | `mysql+pymysql://user:pass@host:port/db` |
| SQL Server | ChromaDB | sql | `mssql+pyodbc://user:pass@host:port/db?driver=...` |
| SQL Server | Elasticsearch | sql | `mssql+pyodbc://user:pass@host:port/db?driver=...` |
| Oracle | ChromaDB | sql | `oracle+cx_oracle://user:pass@host:port/?service_name=...` |
| Oracle | Elasticsearch | sql | `oracle+cx_oracle://user:pass@host:port/?service_name=...` |

### Recommended Combinations

| Use Case | Vector Store | Database | Why |
|----------|--------------|----------|-----|
| **Development** | ChromaDB | SQLite | Simplest setup, no servers |
| **Production (Small)** | ChromaDB | PostgreSQL | Reliable, open-source |
| **Production (Large)** | Elasticsearch | PostgreSQL | Scalable, distributed |
| **Enterprise** | Elasticsearch | SQL Server/Oracle | Advanced features, HA |
| **Web App** | ChromaDB | MySQL | Standard web stack |
| **Analytics** | Elasticsearch | PostgreSQL | Complex queries, multi-user |

### Default Values

```yaml
vector_store_type: chromadb               # Default
elasticsearch_index_name: vanna_vectors   # Default ES index
db_type: sqlite                           # Default
```

---

## Additional Resources

For more detailed examples, see:
- **`config_examples.yaml`** - Complete working examples with all combinations of vector stores and databases
- **`vanna_manager.py`** - Implementation details for connection management
- **`vanna_util.py`** - Vector store implementations (ChromaDB and Elasticsearch)
