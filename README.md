# Task-0 ML/MLOps Engineering Assessment

This repository contains a minimal MLOps-style batch job implemented in Python.  
The goal is to demonstrate reproducibility, observability, and deployment readiness.

---

## Overview
The batch job:
- Loads configuration from a YAML file
- Reads OHLCV market data from `data.csv` (uses only `close`)
- Computes a rolling mean
- Generates a binary trading signal
- Writes structured metrics to JSON
- Writes detailed logs
- Runs locally and inside Docker with a single command

---

## Reproducibility
- All parameters are loaded from `config.yaml`
- Random seed is fixed (`seed: 42`)
- Outputs are deterministic across runs

---

## Rolling Mean & Signal Logic
- Rolling mean is computed using the configured window size
- The first `window - 1` rows result in `NaN` rolling means
- Signals are generated only where rolling mean exists
- This avoids data leakage and ensures consistent behavior

---

## How to Run

### Local Execution
```bash
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

### Docker Execution
**Build Docker Image**
```bash
docker build -t mlops-task .           # `.` = current directory (where Dockerfile exists)
```

**Run Docker Container**
```bash
docker run --rm mlops-task
```

### Explanation

- `python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log`  
  Runs the batch job locally using the provided configuration and dataset, and writes metrics and logs.

- `docker build -t mlops-task .`  
  Builds a Docker image containing the project and its dependencies.

- `docker run --rm mlops-task`  
  Executes the batch job inside a Docker container and prints the final metrics JSON to stdout.
