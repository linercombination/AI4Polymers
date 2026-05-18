from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ffv_pretrain.io_utils import load_yaml
from ffv_pretrain.training import train_from_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a standalone GNN on the external FFV dataset.")
    parser.add_argument("--config", required=True, help="Path to the FFV pretraining YAML config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_yaml(args.config)
    run_dir = train_from_config(config)
    print(f"Training finished. Outputs written to: {run_dir}")


if __name__ == "__main__":
    main()

