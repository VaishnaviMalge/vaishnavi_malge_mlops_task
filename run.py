import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def setup_logging(log_file):
    """
    Configure logging to write both to a file and stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


def write_metrics(path, data):
    """
    Write metrics JSON to disk (used for both success and error cases).
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    # Track total job runtime
    start_time = time.time()

    # CLI arguments (no hardcoded paths)
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)
    args = parser.parse_args()

    setup_logging(args.log_file)
    logging.info("Job started")

    try:
        # -------- Load and validate config --------
        if not Path(args.config).exists():
            raise FileNotFoundError("Config file not found")

        with open(args.config, "r") as f:
            config = yaml.safe_load(f)

        # Required config fields
        for key in ["seed", "window", "version"]:
            if key not in config:
                raise ValueError(f"Missing config key: {key}")

        seed = int(config["seed"])
        window = int(config["window"])
        version = config["version"]

        # Ensure deterministic behavior
        np.random.seed(seed)

        logging.info(
            f"Config validated | seed={seed}, window={window}, version={version}"
        )

        # -------- Load and validate dataset --------
        if not Path(args.input).exists():
            raise FileNotFoundError("Input CSV not found")

        df = pd.read_csv(args.input)

        if df.empty:
            raise ValueError("Input CSV is empty")

        if "close" not in df.columns:
            raise ValueError("Missing required column: close")

        logging.info(f"Rows loaded: {len(df)}")

        # -------- Rolling mean computation --------
        # First (window - 1) rows will naturally produce NaNs
        df["rolling_mean"] = df["close"].rolling(window=window).mean()
        logging.info("Rolling mean computed")

        # -------- Signal generation --------
        df["signal"] = (df["close"] > df["rolling_mean"]).astype(int)

        rows_processed = len(df)
        signal_rate = float(df["signal"].dropna().mean())

        latency_ms = int((time.time() - start_time) * 1000)

        # -------- Metrics output --------
        metrics = {
            "version": version,
            "rows_processed": rows_processed,
            "metric": "signal_rate",
            "value": round(signal_rate, 4),
            "latency_ms": latency_ms,
            "seed": seed,
            "status": "success",
        }

        write_metrics(args.output, metrics)
        logging.info(f"Metrics summary: {metrics}")
        logging.info("Job completed successfully")

        # Print final metrics to stdout (required for Docker run)
        print(json.dumps(metrics, indent=2))
        sys.exit(0)

    except Exception as e:
        # Ensure metrics.json is written even on failure
        error_payload = {
            "version": config["version"] if "config" in locals() else "unknown",
            "status": "error",
            "error_message": str(e),
        }
        write_metrics(args.output, error_payload)
        logging.exception("Job failed")
        print(json.dumps(error_payload, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
