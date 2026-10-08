from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.control_model import ControlTestRequest, parse_control_input
from src.toe_generator import generate_toe_workbook


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a TOE working paper workbook for an auditor control test.")
    parser.add_argument("--input", required=True, help="Path to the JSON control input file.")
    parser.add_argument("--output", required=True, help="Path for the generated Excel workbook.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    request = parse_control_input(payload)
    generate_toe_workbook(request, output_path)
    print(f"TOE working paper generated: {output_path}")


if __name__ == "__main__":
    main()
