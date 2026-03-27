"""Command line entry points for PSD Smart Cut."""

from __future__ import annotations

import argparse
import json

from skills.psd_parser.level9_integration import run_full_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m skills.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Run the full PSD Smart Cut pipeline.")
    process_parser.add_argument("psd_path", help="Path to the PSD file.")
    process_parser.add_argument("--output", default="./output", help="Directory for generated artifacts.")
    process_parser.add_argument("--strategy", default="SMART_MERGE", help="Preferred cut strategy.")
    process_parser.add_argument(
        "--formats",
        default="png",
        help="Comma-separated export formats, for example: png,webp",
    )
    process_parser.add_argument(
        "--no-recognizer",
        action="store_true",
        help="Skip the recognition stage and use metadata/classification only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "process":
        formats = [item.strip() for item in args.formats.split(",") if item.strip()]
        result = run_full_pipeline(
            psd_path=args.psd_path,
            output_dir=args.output,
            strategy=args.strategy,
            formats=formats,
            use_recognizer=not args.no_recognizer,
        )
        print(
            json.dumps(
                {
                    "psd_path": result.psd_path,
                    "output_dir": result.output_dir,
                    "total_layers": result.total_layers,
                    "strategy": result.strategy,
                    "export_formats": result.export_formats,
                    "manifests": result.manifest_paths,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
