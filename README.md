# Going Concerns Tool

This project is a starter implementation for an automated control testing tool for auditors. It focuses on manual controls as the initial version and outputs a standard TOE (Test of Effectiveness) working paper in Excel format.

## What it does

- Accepts a control test input in JSON or via a Streamlit form
- Evaluates sample results against configured tolerances
- Produces a workbook with a TOE-style template
- Includes sections for:
  - control summary
  - design & implementation criteria
  - testing parameters
  - sample results
  - supporting documents
  - conclusion and reviewer notes

## Example workflow

1. Run the CLI flow:
   python main.py
2. Or run the Streamlit app once it is added.
3. Review the generated workbook and adjust the control conclusions as needed.

## Current MVP scope

- Manual controls only
- Single-control Excel output
- Sample-based pass/fail evaluation
- Excel template with summary and working paper sections
- Extensible data model for future automation and document intake support

## Tech stack

- Python 3.11+
- openpyxl
- pydantic

## Project structure

- `main.py` - CLI entry point
- `src/control_model.py` - validated control data structures and evaluation logic
- `src/toe_generator.py` - Excel output generation
- `examples/manual_control_input.json` - sample input
