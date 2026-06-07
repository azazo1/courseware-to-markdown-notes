---
name: courseware-to-markdown-notes
description: 将课堂幻灯片, 培训课件, 导出的 PPT/PDF 讲义, 以及幻灯片图片集转换为完整且适合初学者阅读的 Markdown 笔记. 默认先将材料渲染为页面图片, 再按每批约 10 页切分给多个 sub-agent 逐块目视阅读, 由主 agent 只负责调度, 结构整合, 终稿修订, 从而避免主上下文因持续加载图片而失败. 当 Codex 需要逐页阅读课件图片, 保留完整结构与教学内容, 用 LaTeX 重写公式与符号, 并避免依赖 OCR 或原始文本提取时使用.
---

# 课件转 Markdown 笔记

将课件逐页视为图片来阅读, 但不要让同一个 agent 长时间持有大量图片上下文. 默认把图片阅读工作切给多个 sub-agent, 让主 agent 只保留结构, 分工, 和整合所需的文本上下文.

## 核心原则

- 页面图片是主要事实来源. 不要用 OCR, PDF 文本提取, 或直接复制幻灯片文字来替代阅读.
- 默认启用分块工作流. 只有当材料很短, 或当前环境确实没有 sub-agent 能力时, 才回退到单 agent 模式.
- 主 agent 不要持续逐页读图. 主 agent 负责渲染, 切块, 搭骨架, 派发任务, 合并结果, 修订终稿.
- 子 agent 负责读取自己那一小块页面图片, 一次通常处理 8 到 10 页, 尽量不要超过 10 页.
- 不要把整套课件或所有已完成块的详细结果一次性再塞回主 agent. 采用逐块交付, 逐块整合, 逐块清空注意力的节奏.
- 最终产物仍然是完整, 自洽, 适合初学者阅读的 Markdown 笔记, 不是分块摘要的拼接.

## 快速开始

1. 先将材料规范化为页面图片.
   - 对于 `.pdf`, 运行 `uv run python scripts/render_courseware_pages.py <input.pdf> --output-dir <scratch-dir>`.
   - 对于幻灯片图片目录, 也用同一个脚本处理整个目录.
2. 创建逐页记录模板.
   - 运行 `uv run python scripts/init_page_capture_template.py <scratch-dir>/manifest.json --output <scratch-dir>/page-capture.md`.
3. 创建分块计划.
   - 运行 `uv run python scripts/split_manifest_chunks.py <scratch-dir>/manifest.json --output <scratch-dir>/chunks.json`.
   - 默认每块 10 页. 如果页面很密, 可改成 6 到 8 页.
4. 尽早创建最终笔记文件.
   - 一旦能看出章节结构, 就立刻写入暂定标题和高层级章节骨架.
5. 逐块派发给子 agent.
   - 每个子 agent 只读取自己那一块的图片.
   - 主 agent 不要在派发后继续逐页重读同一批图片, 除非子 agent 报告了歧义, 冲突, 或明显缺页.
6. 主 agent 按块整合结果并持续落盘.
   - 每收到一个稳定块, 就把对应章节写入最终 Markdown.
7. 定稿前按需阅读这些 reference.
   - [references/output-contract.md](references/output-contract.md)
   - [references/latex-and-tables.md](references/latex-and-tables.md)
   - [references/subagent-chunk-contract.md](references/subagent-chunk-contract.md)

## 默认分块工作流

### 1. 主 agent 先做准备, 不先吞图片

- 先渲染整套讲义, 生成 `manifest.json`.
- 再根据 `manifest.json` 切出连续页块, 不要一上来直接打开整套图片.
- 主 agent 可以快速抽样查看极少量页面来判断章节边界, 但不要自己承担完整读图工作.
- 如果很早就能看出章节边界, 先把最终笔记的章节骨架写出来.

### 2. 切块规则

- 默认每块 10 页, 推荐范围是 8 到 10 页.
- 如果某几页表格, 公式, 或图示非常密集, 这块就主动缩小到 4 到 8 页.
- 如果某个章节天然连续但超过 10 页, 就拆成多个连续块, 由主 agent 在整合阶段合并叙述.
- 只有当章节边界非常模糊时, 才允许相邻块保留 1 页重叠. 默认不要重叠.

### 3. 子 agent 只做局部读图和局部成稿

- 每个子 agent 只接收:
  - 当前块的页码范围
  - 当前块的图片路径
  - 这块在整套讲义中的简短定位
  - 必要的输出契约
- 不要把整段对话历史, 全部已完成章节, 或所有其他块的结果一起传给子 agent.
- 如果工具支持, 优先使用不继承完整上下文的最小上下文派发方式.
- 子 agent 应只围绕分配给自己的页面交付结果, 不复述全局规则.

### 4. 主 agent 只整合文本结果, 不重复读图

- 主 agent 接收的主要输入应该是子 agent 的分块结果, 而不是一批批图片.
- 主 agent 应按块读取, 按块整合, 按块写入最终笔记, 不要攒到最后一次性合并.
- 当两个相邻块实际属于同一主题时, 在主 agent 侧把它们合并成一个连贯小节.
- 只有在以下情况才重新打开个别页面图片:
  - 子 agent 报告内容冲突
  - 子 agent 无法识别公式, 图表, 或页间衔接
  - 主 agent 在整合时发现明显缺失

### 5. 单 agent 回退策略

- 仅当总页数很少, 例如不超过 10 页, 或当前环境没有可用的 sub-agent 能力时, 才用单 agent 模式.
- 即使是单 agent 模式, 也要按块推进, 每次只读取一个小窗口的图片, 不要把整套图片连续压进上下文.

## 主 agent 的职责

- 维护全局覆盖, 确保没有页面无声消失.
- 维护最终 Markdown 的章节结构, 术语一致性, 和页码引用范围.
- 将相邻块整合成自然的知识叙述, 避免最终笔记退化成逐页流水账.
- 必要时回头修订前文, 但不要为了等待所有块完成而一直不动笔.
- 定稿前用 `references/output-contract.md` 做完整性和可读性复查.

## 子 agent 的职责

- 逐页读取自己负责的图片, 不跳页.
- 记录这几页在当前论述中的作用, 必须保留的内容块, 公式, 表格, 图示含义, 警告, 例子, 边界条件.
- 将碎片化幻灯片内容重建成局部可读的 Markdown 草稿.
- 明确指出需要主 agent 决策的歧义, 交叉引用, 或重复内容.
- 交付格式遵循 [references/subagent-chunk-contract.md](references/subagent-chunk-contract.md).

## 写作与格式要求

- 最终笔记默认使用中文, 但 Markdown 中统一使用半角标点和半角符号.
- 中文与英文, 数字, 行内公式之间遵循盘古之白.
- 公式和特殊符号统一改写为 LaTeX.
- 重要表格转换为 Markdown 表格, 图表和示意图要解释其实际含义.
- 首次出现的专有名词, 缩写, 或英文术语, 要补出全称和中文对应说明.
- 写知识本身, 不写 `这一页介绍了什么` 这类对课件的评论.

## 何时读取额外 reference

- 需要检查最终笔记是否完整, 自洽, 且适合初学者时, 读取 [references/output-contract.md](references/output-contract.md).
- 需要重写公式, 符号, 矩阵, 或信息密集表格时, 读取 [references/latex-and-tables.md](references/latex-and-tables.md).
- 需要组织子 agent 的交付格式, 或控制主子 agent 之间的上下文流量时, 读取 [references/subagent-chunk-contract.md](references/subagent-chunk-contract.md).
