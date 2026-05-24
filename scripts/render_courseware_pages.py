#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="将课件渲染为规范化的页面图片和 manifest.",
    )
    parser.add_argument("input_path", help="PDF 文件, 图片文件, 或幻灯片图片目录")
    parser.add_argument("--output-dir", required=True, help="用于存放图片和 manifest 的临时目录")
    parser.add_argument("--dpi", type=int, default=180, help="PDF 输入的渲染 DPI")
    return parser.parse_args()


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def ensure_empty_output_dir(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    if images_dir.exists() and any(images_dir.iterdir()):
        fail(f"{images_dir} 不是空目录, 请使用新的临时目录")
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def numeric_suffix(path: Path):
    suffix = path.stem.split("-")[-1]
    return int(suffix) if suffix.isdigit() else 0


def render_pdf(input_path: Path, images_dir: Path, dpi: int):
    cmd = [
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        str(input_path),
        str(images_dir / "page"),
    ]
    subprocess.run(cmd, check=True)

    rendered = sorted(images_dir.glob("page-*.png"), key=numeric_suffix)
    if not rendered:
        fail("pdftoppm 没有生成任何页面图片")

    normalized = []
    for index, source in enumerate(rendered, start=1):
        destination = images_dir / f"page-{index:04d}.png"
        source.rename(destination)
        normalized.append(destination)
    return normalized


def collect_images(input_path: Path):
    if input_path.is_file():
        return [input_path]

    images = [
        path
        for path in sorted(input_path.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if not images:
        fail("输入目录中没有找到支持的图片")
    return images


def normalize_images(input_path: Path, images_dir: Path):
    normalized = []
    for index, source in enumerate(collect_images(input_path), start=1):
        destination = images_dir / f"page-{index:04d}.png"
        cmd = ["magick", str(source), "-auto-orient", str(destination)]
        subprocess.run(cmd, check=True)
        normalized.append(destination)
    return normalized


def build_manifest(input_path: Path, source_type: str, pages, output_dir: Path):
    manifest = {
        "source_path": str(input_path.resolve()),
        "source_type": source_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "pages": [
            {
                "page": index,
                "label": f"P{index:03d}",
                "image_path": str(page.resolve()),
            }
            for index, page in enumerate(pages, start=1)
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")
    return manifest_path


def detect_source_type(input_path: Path):
    if input_path.is_dir():
        return "image-directory"
    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "single-image"
    fail(
        f"不支持的输入类型 '{suffix or input_path.name}'. 请先将幻灯片导出为 PDF, "
        "或提供一个幻灯片图片目录",
    )


def main():
    args = parse_args()
    input_path = Path(args.input_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not input_path.exists():
        fail(f"输入路径不存在: {input_path}")

    source_type = detect_source_type(input_path)
    required_binaries = ("pdftoppm",) if source_type == "pdf" else ("magick",)
    for binary in required_binaries:
        if shutil.which(binary) is None:
            fail(f"PATH 中缺少必需工具: {binary}")

    images_dir = ensure_empty_output_dir(output_dir)

    if source_type == "pdf":
        pages = render_pdf(input_path, images_dir, args.dpi)
    else:
        pages = normalize_images(input_path, images_dir)

    manifest_path = build_manifest(input_path, source_type, pages, output_dir)

    print(f"已渲染 {len(pages)} 页")
    print(f"图片目录: {images_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
