# SL2Utilities (`sl2util`)

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/tests-14%20passed-brightgreen)](#testing)
[![Docker](https://img.shields.io/badge/container-docker%20ready-2496ED?logo=docker&logoColor=white)](#docker-containerization)

> **Steelmaking & Industrial Automation Level 2 Utilities**  
> Modernized, cross-platform Python suite for supervisory process automation, cryptographic configuration management, high-performance database connectivity, Level 1 PLC communication, service watchdogs, and production tracking.

---

## Architecture & Modules

`sl2util` provides core infrastructure shared across Level 2 supervisory computer systems in steel manufacturing (electric arc furnaces, ladle furnaces, continuous casters, and rolling mills):

| Module | Description | Key Capabilities |
| :--- | :--- | :--- |
| **`configdatareader`** | Secure Configuration | Fernet symmetric encryption, SHA-256 key derivation, XML encode/decode, token & license expiration math. |
| **`logger`** | Robust File Logging | Rolling logs with size rotation (`setKeepSize`) and automated aging purge (`setKeepDays`, `purger`), bridging to standard `logging`. |
| **`dbhandler`** | Database Abstraction | Dual support for Oracle (`python-oracledb` Thin mode, clientless) and SQL Server (`pyodbc`) with dictionary-mapped rows and parameterized queries. |
| **`l1handler`** | Level 1 (PLC) OPC-UA | Industrial OPC-UA client for reading PLC automation tags (supporting `asyncua` and legacy `opcua`). |
| **`watchdog`** | TCP Service Daemon | Non-blocking TCP heartbeat listener responding with `RUN` to health probes; automatic DB service registry. |
| **`watchdog_reader`**| Service Monitor | TCP health prober and status updater for Level 2 microservices and container probes. |
| **`utils`** | Automation Helpers | Steelmaking production text templating (`%Heat`, `%Shift`, `%WW`), cross-platform zip compression (`zipfile`), SMTP / Outlook email notifications, FTP uploads, and file management. |
| **`loader`** | App Bootstrapper | Safe environment initialization, configuration decoding, and automatic watchdog startup. |

---

## What's New in v2.0.0 (Modernization Highlights)

- **Standard PEP 621 / PEP 517 Packaging:** Migrated from deprecated `distutils.core` to `pyproject.toml` and modern `setuptools`.
- **Pure-Python Oracle (`python-oracledb`):** Replaced obsolete `cx_Oracle`. Runs in Thin mode without requiring Oracle Instant Client binaries—runs seamlessly on macOS, Linux, and inside Docker containers out of the box!
- **Cross-Platform Compatibility:** Eliminated hardcoded Windows paths (`\\`) in favor of `pathlib.Path`. Works identically on Linux, macOS, and Windows.
- **Pure-Python Zip Compression:** Replaced external `7z` command dependency with standard library `zipfile`.
- **Modern Email Engine:** Added standard `smtplib` + MIME email dispatch with graceful fallback to Windows Outlook COM only when running on Windows.
- **Zero Side-Effects on Import:** Removed top-level socket bindings, file operations, and print statements during library import.
- **Full Type Annotations:** Added typing across all module functions and classes.
- **Docker & Compose Ready:** Multi-stage `Dockerfile` with non-root security user, container healthchecks, and `docker-compose.yml`.
- **Automated Test Suite:** Comprehensive `pytest` test suite replacing interactive terminal scripts.

---

## Installation

### From Source / Repository

```bash
git clone https://github.com/SergioChavezRangel/SL2Utilities-master.git
cd SL2Utilities-master

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install base package
pip install -e .

# Or install with optional extras (MSSQL, OPC-UA, dev/test tools)
pip install -e ".[all]"
```

### Installation Extras

- `sl2util[mssql]`: Installs `pyodbc` for SQL Server.
- `sl2util[opcua]`: Installs `asyncua` for OPC-UA Level 1 communication.
- `sl2util[dev]`: Installs `pytest` and `ruff` for testing and linting.
- `sl2util[all]`: Installs all optional drivers and development dependencies.

---

## Quickstart & Code Examples

### 1. Encrypt and Decrypt Configuration Files

```python
from pathlib import Path
import sl2util.configdatareader as cryptlib

# Derive 32-byte Fernet key from password
key = cryptlib.get_key(b"MySteelmakingSecret")
cryptlib.set_key(key)

# Encrypt XML configuration
cryptlib.setDecFilePath("Config_Decrypted.xml")
cryptlib.setEncFilePath("Config_Encrypted.xml")
cryptlib.encodeXML(log=False)

# Read encrypted configuration directly to dictionary
config = cryptlib.decodeXML(save_file=False)
print("Furnace ID:", config.get("FURNACE_ID"))
```

### 2. Steelmaking Production String Formatting (`text_decorator`)

Format heat, shift, treatment, sequence, and week tokens into report filenames or headers:

```python
import datetime
import sl2util.utils as util

template = "Report_%Shift_%Heat_Seq%Seq_%yyyy%mm%dd.pdf"

# Shift 21 maps to 'A', 22 to 'B', 23 to 'C'
filename = util.text_decorator(
    text=template,
    date=datetime.date.today(),
    shift=21,
    heat=994512,
    tmt=1,
    sequence=4,
    in_seq=2,
)

print(filename)
# Output: Report_A_994512_Seq4_20261020.pdf
```

### 3. Oracle & SQL Server Database Connectivity

```python
from sl2util.dbhandler import DbOra, DbSQL

# Oracle (Thin mode, no Oracle Client binaries needed!)
with DbOra("myuser/mypassword@myoraclehost:1521/PROD_SERVICE") as ora:
    rows = ora.getrows("SELECT HEAT_ID, GRADE, STEEL_WEIGHT FROM SL2_HEATS WHERE STATUS = :status", {"status": "ACTIVE"})
    for row in rows:
        print(row["HEAT_ID"], row["GRADE"])

# SQL Server (via pyodbc)
with DbSQL("DRIVER={ODBC Driver 18 for SQL Server};SERVER=sqlserver.local;DATABASE=SL2;UID=sa;PWD=secret;TrustServerCertificate=yes") as sql:
    latest = sql.getrow("SELECT TOP 1 * FROM SL2_SERVICES_CONFIG ORDER BY ID DESC")
    print(latest)
```

### 4. Watchdog Service & Health Monitoring

Start a TCP heartbeat server responding to external monitoring probes:

```python
import sl2util.watchdog as watchdog
import sl2util.watchdog_reader as reader

# Start watchdog server on port 65001
server = watchdog.start_watchdog(service_name="FurnaceModelDaemon", port=65001)

# Probe the service from another thread, process, or container
status = reader.call_service("127.0.0.1", 65001)
print(status)  # Prints: 'RUN'

# Gracefully stop
watchdog.stop_watchdog()
```

---

## Docker Containerization

### Running the Watchdog Service in Docker

`sl2util` includes a hardened, multi-stage `Dockerfile` (running as a non-privileged `appuser`) with an embedded Docker `HEALTHCHECK`.

```bash
# Build the Docker image
docker build -t sl2util-watchdog:latest .

# Run the container
docker run -d \
  --name sl2util-watchdog \
  -p 65001:65001 \
  -v $(pwd)/log:/app/log \
  sl2util-watchdog:latest
```

### Using Docker Compose

```bash
docker compose up -d
```

Verify container health:
```bash
docker inspect --format='{{json .State.Health.Status}}' sl2util-watchdog
# Output: "healthy"
```

---

## Testing & Quality

Run the modern automated test suite:

```bash
# Run tests with pytest
pytest tests/

# Run fast linting with Ruff
ruff check sl2util/ tests/
```

To run the legacy interactive terminal testing menu:
```bash
python tests/test_sl2util.py
```

---

## Release History

* **2.0.0 (Modernization)**
  * Migrated packaging to standard `pyproject.toml` (PEP 517/621).
  * Upgraded Oracle engine to `python-oracledb` Thin mode (100% clientless, cross-platform).
  * Converted external `7z` dependency to Python standard library `zipfile`.
  * Added cross-platform SMTP email dispatch alongside Windows Outlook COM fallback.
  * Added multi-stage `Dockerfile`, `docker-compose.yml`, and container healthchecks.
  * Replaced interactive terminal testing with comprehensive automated `pytest` test suite.
  * Added GitHub Actions continuous integration matrix (Linux, macOS, Windows).
* **1.2.3**
  * Added watchdog handler for services.
* **1.0.5**
  * Added Level 1 Handler (OPC-UA connection).
* **1.0.3**
  * Added utils, Mail sender, and text parser.
* **1.0.1**
  * Added Database Handler for Oracle and SQL Server.
* **1.0.0**
  * Initial packaged release.

---

## License

Distributed under the MIT License. See [LICENSE.txt](LICENSE.txt) for details.

**Author:** Sergio Chávez Rangel – `l2.steel.automation@gmail.com`  
[GitHub Profile](https://github.com/SergioChavezRangel/)
