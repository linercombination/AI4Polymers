from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ffv_pretrain.io_utils import load_yaml
from ffv_pretrain.predict import predict_ffv_from_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use the pretrained external FFV GNN to augment a target CSV.")
    parser.add_argument("--config", required=True, help="Path to the inference YAML config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_yaml(args.config)
    output_path = predict_ffv_from_config(config)
    print(f"Predicted FFV CSV written to: {output_path}")


if __name__ == "__main__":
    main()
