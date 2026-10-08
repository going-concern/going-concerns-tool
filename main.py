import json
from pathlib import Path
from typing import Any, Dict

from src.control_model import ControlTestRequest, parse_control_input
from src.toe_generator import generate_toe_workbook


def main() -> None:
    input_path = Path("examples/manual_control_input.json")
    output_path = Path("output/toe_working_paper.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    request = parse_control_input(payload)
    generate_toe_workbook(request, str(output_path))
    print(f"TOE working paper generated: {output_path}")


if __name__ == "__main__":
    main()
