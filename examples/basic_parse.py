#!/usr/bin/env python3
"""Basic PSD parsing example for PSD Smart Cut."""

from __future__ import annotations

import os
import sys

# Allow running the example directly from the repository root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.psd_parser.level1_parse import LayerFilter, extract_pages, parse_psd, read_layers


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python examples/basic_parse.py <path-to-psd>")
        raise SystemExit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        raise SystemExit(1)

    print("=" * 50)
    print("PSD Smart Cut - Basic Parse Example")
    print("=" * 50)

    print(f"\n[1] Parsing PSD file: {file_path}")
    document = parse_psd(file_path)
    print(f"    Version: {document.version}")
    print(f"    Size: {document.width} x {document.height}")
    print(f"    Pages: {document.page_count}")
    print(f"    Layers: {document.total_layers}")

    print("\n[2] Extracting pages")
    page_result = extract_pages(file_path)
    print(f"    Pages found: {page_result.page_count}")
    for page in page_result.pages:
        print(
            f"    - Page {page['index']}: {page['name']} "
            f"({page['width']}x{page['height']})"
        )

    print("\n[3] Reading all layers on page 0")
    all_layers = read_layers(file_path, page_index=0, filter_type=LayerFilter.ALL)
    print(f"    Total layers: {all_layers.layer_count}")

    kind_count: dict[str, int] = {}
    for layer in all_layers.layers:
        kind = layer["kind"]
        kind_count[kind] = kind_count.get(kind, 0) + 1

    print("    Layer types:")
    for kind, count in sorted(kind_count.items()):
        print(f"    - {kind}: {count}")

    print("\n[4] Reading visible layers")
    visible_layers = read_layers(file_path, page_index=0, filter_type=LayerFilter.VISIBLE)
    print(f"    Visible layers: {visible_layers.layer_count}")

    print("\n[5] Reading hidden layers")
    hidden_layers = read_layers(file_path, page_index=0, filter_type=LayerFilter.HIDDEN)
    print(f"    Hidden layers: {hidden_layers.layer_count}")
    for layer in hidden_layers.layers[:5]:
        print(f"    - {layer['name']} (id: {layer['id']})")

    print("\n" + "=" * 50)
    print("Done.")
    print("=" * 50)


if __name__ == "__main__":
    main()
