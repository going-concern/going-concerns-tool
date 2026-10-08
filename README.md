import json
from pathlib import Path

from src.control_model import parse_control_input
from src.control_service import ControlService
from src.database import initialize_database
from src.toe_generator import generate_toe_workbook


def main() -> None:
    input_path = Path("examples/manual_control_input.json")
    output_path = Path("output/toe_working_paper.xlsx")
    db_path = Path("data/going_concerns.db")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    initialize_database(db_path)

    with input_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    service = ControlService(db_path=db_path)
    control = service.create_control(payload, created_by="CLI")
    generate_toe_workbook(control, str(output_path))

    print(f"Control '{control.control_id}' saved to SQLite database: {db_path}")
    print(f"Workbook generated: {output_path}")


if __name__ == "__main__":
    main()
