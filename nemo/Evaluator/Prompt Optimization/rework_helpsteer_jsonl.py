#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Dict, Any, Optional


def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at {path} line {line_number}: {e}") from e


def rework_record(record: Dict[str, Any]) -> Dict[str, Any]:
    prompt: Optional[str] = record.get("prompt")
    response: Optional[str] = record.get("response")
    # Prefer original 'helpfulness' but allow already-renamed 'reference_helpfulness'
    helpfulness_value = (
        record["helpfulness"] if "helpfulness" in record else record.get("reference_helpfulness")
    )

    return {
        "prompt": prompt,
        "response": response,
        "reference_helpfulness": helpfulness_value,
    }


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")


def process_file(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transformed = (rework_record(r) for r in read_jsonl(input_path))
    write_jsonl(output_path, transformed)


def default_inputs_for_script_dir(script_path: Path) -> Iterable[Path]:
    # Assumes input files are located alongside this script
    directory = script_path.parent
    return [
        directory / "helpsteer2_dataset.jsonl",
        directory / "helpsteer2_dataset_validation.jsonl",
    ]


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rework JSONL files to only include prompt, response, reference_helpfulness (renamed from helpfulness).",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input JSONL files. If omitted, defaults to the two helpsteer2 JSONL files next to this script.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Optional output directory. Defaults to input file directory.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    script_path = Path(__file__).resolve()

    input_paths: Iterable[Path]
    if args.inputs:
        input_paths = [Path(p).resolve() for p in args.inputs]
    else:
        input_paths = default_inputs_for_script_dir(script_path)

    out_dir: Optional[Path] = Path(args.out_dir).resolve() if args.out_dir else None

    for input_path in input_paths:
        if not input_path.exists():
            print(f"Skipping missing file: {input_path}", file=sys.stderr)
            continue
        output_directory = out_dir if out_dir is not None else input_path.parent
        output_path = output_directory / f"{input_path.stem}.reworked.jsonl"
        process_file(input_path, output_path)
        print(f"Wrote: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
