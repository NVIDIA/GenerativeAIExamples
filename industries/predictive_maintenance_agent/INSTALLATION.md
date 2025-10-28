# Installation Guide

This guide explains how to install the Predictive Maintenance Agent with different database and vector store options.

## Base Installation

Install the core package with default dependencies (ChromaDB + SQLite):

```bash
pip install -e .
```

This includes:
- **ChromaDB** - Default vector store for SQL retriever
- **SQLite** - Built-in database support (no additional packages needed)
- **SQLAlchemy** - Generic SQL database support framework
- All core ML and visualization dependencies

## Optional Dependencies

Install additional packages based on your needs:

### Elasticsearch Vector Store

For production deployments with Elasticsearch as the vector store:

```bash
pip install -e ".[elasticsearch]"
```

### PostgreSQL Database

For PostgreSQL database support:

```bash
pip install -e ".[postgres]"
```

### MySQL Database

For MySQL database support:

```bash
pip install -e ".[mysql]"
```

### SQL Server Database

For Microsoft SQL Server support:

```bash
pip install -e ".[sqlserver]"
```

**Note:** You also need to install the Microsoft ODBC Driver for SQL Server from [Microsoft's website](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

### Oracle Database

For Oracle database support:

```bash
pip install -e ".[oracle]"
```

**Note:** You also need to install Oracle Instant Client from [Oracle's website](https://www.oracle.com/database/technologies/instant-client.html).

## Combined Installations

### All Databases

Install support for all SQL databases at once:

```bash
pip install -e ".[all-databases]"
```

This includes: PostgreSQL, MySQL, SQL Server, and Oracle drivers.

### Everything

Install all optional dependencies (Elasticsearch + all databases):

```bash
pip install -e ".[all]"
```

## Installation Examples by Use Case

### Development Setup (Simplest)
```bash
# Base installation - ChromaDB + SQLite
pip install -e .
```

### Production with PostgreSQL
```bash
# Base + PostgreSQL
pip install -e ".[postgres]"
```

### Production with Elasticsearch and PostgreSQL
```bash
# Base + Elasticsearch + PostgreSQL
pip install -e ".[elasticsearch,postgres]"
```

### Enterprise with All Options
```bash
# Everything
pip install -e ".[all]"
```

## Verification

After installation, verify your setup:

```python
# Check installed packages
import chromadb  # Should work with base install
import sqlalchemy  # Should work with base install

# Optional packages (only if installed)
import elasticsearch  # If [elasticsearch] installed
import psycopg2  # If [postgres] installed
import pymysql  # If [mysql] installed
import pyodbc  # If [sqlserver] installed
import cx_Oracle  # If [oracle] installed
```

## System Requirements

- **Python:** 3.11 or 3.12 (Python 3.13 not yet supported)
- **OS:** Linux, macOS, or Windows
- **Memory:** Minimum 8GB RAM recommended
- **Disk:** Minimum 10GB free space

## External Service Requirements

Depending on your configuration, you may need:

### Elasticsearch (Optional)
- Elasticsearch 8.0 or higher running
- Network access to Elasticsearch cluster
- Authentication credentials (API key or username/password)

### Database Servers (Optional)
- **PostgreSQL:** PostgreSQL 12 or higher
- **MySQL:** MySQL 8.0 or higher  
- **SQL Server:** SQL Server 2016 or higher
- **Oracle:** Oracle 19c or higher

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'elasticsearch'`  
**Solution:** Install elasticsearch support: `pip install -e ".[elasticsearch]"`

**Problem:** `ModuleNotFoundError: No module named 'psycopg2'`  
**Solution:** Install PostgreSQL support: `pip install -e ".[postgres]"`

### Binary Dependencies

**SQL Server on Linux/Mac:**
```bash
# Install unixODBC first
# macOS:
brew install unixodbc

# Ubuntu/Debian:
sudo apt-get install unixodbc unixodbc-dev

# Then install ODBC driver from Microsoft
```

**Oracle:**
- Download and install Oracle Instant Client
- Set environment variables:
  ```bash
  export ORACLE_HOME=/path/to/instantclient
  export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
  ```

## Next Steps

After installation, see:
- **Configuration Guide:** `configs/README.md` - How to configure vector stores and databases
- **Examples:** `config_examples.yaml` - Sample configurations
- **Getting Started:** Run the predictive maintenance workflow

## Support

For issues or questions:
1. Check the configuration guide: `configs/README.md`
2. Review example configs: `config_examples.yaml`
3. See troubleshooting sections in the README
