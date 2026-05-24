#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="根据渲染 manifest 创建逐页临时模板.",
    )
    parser.add_argument("manifest", help="来自 render_courseware_pages.py 的 manifest.json 路径")
    parser.add_argument("--output", required=True, help="输出 Markdown 路径")
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

    if not isinstance(data, dict) or "pages" not in data:
        fail("manifest 缺少 'pages' 字段")
    if not isinstance(data["pages"], list) or not data["pages"]:
        fail("manifest 中不包含任何页面")
    return data


def build_template(manifest):
    lines = [
        "# 逐页记录模板",
        "",
        "在阅读页面图片时, 用这个文件做临时记录.",
        "不要跳过任何页面, 即使它看起来重复, 或几乎全是视觉内容.",
        "这是一份覆盖情况台账, 不是逐页摘要模板.",
        "",
        f"- Source: `{manifest['source_path']}`",
        f"- Page count: `{manifest['page_count']}`",
        "",
    ]

    for page in manifest["pages"]:
        lines.extend(
            [
                f"## {page['label']}",
                "",
                f"- Image: `{page['image_path']}`",
                "- 这一页在当前章节或论述中的作用:",
                "- 需要保留的标题, 小标题, 列表, 和内容块:",
                "- 需要保留的定义, 结论, 阈值, 或判断:",
                "- 需要改写为 LaTeX 的公式或符号:",
                "- 需要补充缩写全称和中文对应翻译的专有名词, 缩写, 或技术术语:",
                "- 需要保留的表格, 图表, 示意图, 截图, 或视觉关系:",
                "- 需要保留的例子, 工作流程, 注意事项, 或边界情况:",
                "- 需要给初学者补一句解释的难点:",
                "- 必须明确写出来, 不能回指幻灯片的内容:",
                "- 这一页最终应映射成什么 Markdown 结构:",
                "- 可以提升可读性的机会, 例如小节, 表格, 简短总结, 列表, 过渡句:",
                "- 阅读邻近页面时需要顺手解决的问题或歧义:",
                "",
            ]
        )

    return "\n".join(lines)


def main():
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    manifest = load_manifest(manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_template(manifest) + "\n")

    print(f"模板文件: {output_path}")


if __name__ == "__main__":
    main()
