#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="根据 manifest 将页面切成适合分派给子 agent 的连续页块.",
    )
    parser.add_argument("manifest", help="render_courseware_pages.py 生成的 manifest.json 路径")
    parser.add_argument(
        "--pages-per-chunk",
        type=int,
        default=10,
        help="每个页块的目标页数, 默认 10",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=0,
        help="相邻页块的重叠页数, 默认 0",
    )
    parser.add_argument("--output", help="输出 JSON 路径, 不传则打印到 stdout")
    return parser.parse_args()


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def load_manifest(path: Path):
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        fail(f"manifest 不存在: {path}")
    except json.JSONDecodeError as exc:
        fail(f"manifest JSON 无效: {exc}")

    pages = data.get("pages")
    if not isinstance(data, dict) or not isinstance(pages, list) or not pages:
        fail("manifest 缺少有效的 pages 列表")

    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            fail(f"第 {index} 个页面条目不是对象")
        if "page" not in page or "label" not in page or "image_path" not in page:
            fail(f"第 {index} 个页面条目缺少 page, label 或 image_path")
    return data


def build_chunks(manifest, pages_per_chunk: int, overlap: int):
    if pages_per_chunk <= 0:
        fail("--pages-per-chunk 必须大于 0")
    if overlap < 0:
        fail("--overlap 不能小于 0")
    if overlap >= pages_per_chunk:
        fail("--overlap 必须小于 --pages-per-chunk")

    pages = manifest["pages"]
    step = pages_per_chunk - overlap
    chunks = []
    start = 0
    chunk_index = 1

    while start < len(pages):
        selected = pages[start : start + pages_per_chunk]
        chunk_id = f"C{chunk_index:03d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "start_page": selected[0]["page"],
                "end_page": selected[-1]["page"],
                "start_label": selected[0]["label"],
                "end_label": selected[-1]["label"],
                "page_count": len(selected),
                "pages": [
                    {
                        "page": page["page"],
                        "label": page["label"],
                        "image_path": page["image_path"],
                    }
                    for page in selected
                ],
            }
        )
        start += step
        chunk_index += 1

    return {
        "source_path": manifest.get("source_path"),
        "page_count": manifest.get("page_count", len(pages)),
        "pages_per_chunk": pages_per_chunk,
        "overlap": overlap,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def main():
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else None

    manifest = load_manifest(manifest_path)
    payload = build_chunks(manifest, args.pages_per_chunk, args.overlap)
    serialized = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"

    if output_path is None:
        print(serialized, end="")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialized)
    print(f"分块文件: {output_path}")


if __name__ == "__main__":
    main()
