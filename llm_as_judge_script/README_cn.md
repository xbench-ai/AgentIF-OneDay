# LLM 自动评分脚本

基于大语言模型的自动评分工具，用于根据预定义标准评估 Agent 的回答。纯脚本运行，无需数据库、Redis 或 MinIO 等外部依赖。

[English Documentation](README.md)

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [安装](#安装)
- [配置](#配置)
- [准备数据](#准备数据)
- [运行评分](#运行评分)
- [输出格式](#输出格式)
- [可用模型](#可用模型)
- [高级配置](#高级配置)

## 功能特性

- **多模型支持**：Gemini、ChatGPT 和 OpenRouter 模型
- **并发处理**：可配置的并行评分，提高效率
- **附件解析**：支持 PDF、Word、Excel、PowerPoint、图片、HTML 和代码文件
- **断点续跑**：自动保存进度，支持中断后继续
- **灵活过滤**：可只评分特定题目或特定 Agent

## 快速开始

```bash
# 1. 克隆并设置环境
conda create -n llm_score python=3.11
conda activate llm_score
pip install -r requirements.txt
playwright install chromium

# 2. 配置 API 密钥
cp env.example .env
# 编辑 .env 文件，添加你的 API 密钥

# 3. 准备数据文件 (questions.jsonl, answers.jsonl)

# 4. 编辑 llm_score/main.py 设置文件路径

# 5. 运行评分
python -m llm_score.main
```

## 安装

### 环境要求

- Python 3.11+
- Conda（推荐）或 pip

### 步骤 1：创建环境

```bash
conda create -n llm_score python=3.11
conda activate llm_score
```

### 步骤 2：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 3：安装 Playwright 浏览器

Playwright 用于 HTML 渲染：

```bash
playwright install chromium
```

### 步骤 4：安装系统依赖（用于 pdf2image）

PDF/PPTX 渲染需要 poppler：

**Ubuntu/Debian：**
```bash
sudo apt-get install poppler-utils
```

**macOS：**
```bash
brew install poppler
```

**Windows：**
从 [poppler releases](https://github.com/osber/poppler-windows/releases) 下载并添加到 PATH。

## 配置

### 设置 API 密钥

在项目根目录创建 `.env` 文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，配置你的 LLM API 密钥：

```env
# LLM API 密钥（配置你需要使用的即可）
GEMINI_API_KEY=你的-gemini-api-key
CHATGPT_API_KEY=你的-chatgpt-api-key
OPENROUTER_API_KEY=你的-openrouter-api-key

# LLM 设置
LLM_DEFAULT_MODEL=OpenRouter-Gemini-3.0-Pro
LLM_MAX_CONCURRENT=5
LLM_MAX_RETRIES=3
LLM_TIMEOUT=180
```

只需配置你计划使用的模型对应的 API 密钥即可。

## 准备数据

### 目录结构

按以下结构组织你的文件：

```
your_project/
├── .env                          # API 配置
├── questions.jsonl               # 题目文件
├── answers.jsonl                 # 答案文件
└── Attachments/                  # 附件目录
    ├── Questions/                # 题目附件
    │   ├── task1_image.png
    │   └── task2_doc.pdf
    ├── MyAgent-2511/             # Agent 答案附件
    │   ├── result.xlsx
    │   └── report.md
    ├── AnotherAgent/             # 另一个 Agent 的附件
    │   └── output.zip
    └── Reference_answer/         # 参考答案附件（可选）
        └── expected_result.xlsx
```

### 题目文件 (questions.jsonl)

每行是一个表示题目的 JSON 对象：

```json
{
  "question_id": "taskif_1",
  "title": "数据分析任务",
  "description": "请分析提供的数据集并生成摘要报告...",
  "attachment_filenames": ["dataset.xlsx", "instructions.pdf"],
  "score_criteria": [
    {"content": "报告包含正确的数据摘要", "score": 2},
    {"content": "图表格式正确", "score": 1},
    {"content": "缺少必要章节（扣分）", "score": -1}
  ],
  "reference_answer_description": "报告应包含...",
  "reference_answer_attachment_filenames": ["expected_report.pdf"]
}
```

**字段说明：**

| 字段 | 必填 | 描述 |
|------|------|------|
| `question_id` | 是 | 题目唯一标识符 |
| `title` | 是 | 题目标题 |
| `description` | 是 | 详细题目描述 |
| `attachment_filenames` | 否 | 题目附件文件名列表（位于 `Attachments/Questions/`） |
| `score_criteria` | 是 | 评分标准列表 |
| `score_criteria[].content` | 是 | 评分标准描述 |
| `score_criteria[].score` | 是 | 该标准的分值（负数表示扣分） |
| `reference_answer_description` | 否 | 期望答案的文字描述 |
| `reference_answer_attachment_filenames` | 否 | 参考答案附件（位于 `Attachments/Reference_answer/`） |

### 答案文件 (answers.jsonl)

每行是一个表示 Agent 答案的 JSON 对象：

```json
{
  "question_id": "taskif_1",
  "agent_name": "MyAgent-2511",
  "content": {"text": "这是我对数据集的分析...\n\n主要发现是..."},
  "attachment_filenames": ["analysis_report.xlsx", "charts.png"]
}
```

**字段说明：**

| 字段 | 必填 | 描述 |
|------|------|------|
| `question_id` | 是 | 必须匹配题目文件中的 question_id |
| `agent_name` | 是 | Agent 名称（同时也是附件子目录名） |
| `content` | 是 | 答案内容对象 |
| `content.text` | 是 | 答案的文本内容 |
| `attachment_filenames` | 否 | 答案附件列表（位于 `Attachments/{agent_name}/`） |

### 附件路径规则

- **题目附件**：`Attachments/Questions/{filename}`
- **答案附件**：`Attachments/{agent_name}/{filename}`
- **参考答案附件**：`Attachments/Reference_answer/{filename}`

### 支持的附件格式

| 类别 | 扩展名 |
|------|--------|
| 文档 | `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv` |
| 图片 | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp` |
| 网页 | `.html`, `.htm` |
| 代码 | `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.md`, `.txt`, `.json`, `.xml`, `.yaml` |
| 压缩包 | `.zip`（内容会被解压并解析） |
| Notebook | `.ipynb` |

## 运行评分

### 步骤 1：配置输入输出路径

编辑 `llm_score/main.py` 顶部的配置部分：

```python
# 输入文件路径
QUESTIONS_FILE = "path/to/your/questions.jsonl"
ANSWERS_FILE = "path/to/your/answers.jsonl"

# 输出文件前缀（会自动添加时间戳）
OUTPUT_FILE_PREFIX = "results"

# 使用的 LLM 模型
MODEL_NAME = "OpenRouter-Gemini-3.0-Pro"

# 并发设置（可选，None 则使用 .env 中的默认值）
MAX_CONCURRENT = None
MAX_RETRIES = None

# 附件基础路径
ATTACHMENT_BASE_PATH = "Attachments"

# 过滤设置（可选）
QUESTION_IDS = None  # 例如 ["taskif_1", "taskif_2"] 只评分特定题目
AGENT_NAMES = None   # 例如 ["MyAgent-2511"] 只评分特定 Agent

# 详细日志
VERBOSE = False
```

### 步骤 2：运行脚本

```bash
python -m llm_score.main
```

## 使用测试样本

项目在 `sample/` 目录中提供了测试样本，方便快速测试：

- `sample/sample_questions_10.jsonl` - 包含 10 个测试题目，涵盖多种任务类型
- `sample/sample_answers_10.jsonl` - 包含 10 个对应的测试答案
- `sample/sample_results_10.jsonl` - 参考用的预期评分结果

### 快速测试运行

使用测试样本快速测试评分系统：

1. **更新 `llm_score/main.py` 中的配置：**

```python
# 输入文件路径
QUESTIONS_FILE = "sample/sample_questions_10.jsonl"
ANSWERS_FILE = "sample/sample_answers_10.jsonl"
```

2. **运行评分脚本：**

```bash
python -m llm_score.main
```

3. **对比结果**（可选）：

运行完成后，可以将你的输出结果与 `sample/sample_results_10.jsonl` 进行对比，以验证评分行为。样本结果文件包含了所有 10 个题目-答案对的所有评分标准的评分输出，展示了：
- 每个评分标准是否满足（`satisfied: true/false`）
- LLM 评委提供的推理过程
- 使用的评分方法

### 测试样本概览

测试样本包含多种类型的题目：

- **量子计算任务**：资源估算、算法实现
- **Web 开发**：GUI 更新、HTML 生成
- **数据提取**：论文数据提取、学者信息收集
- **研究任务**：市场调研、论文整理
- **创意任务**：图像生成、营销材料设计
- **分析任务**：成本分析、升级规划

每个测试题目包含：
- 完整的题目描述
- 评分标准（包含加分项和扣分项）
- 参考答案描述
- 附件文件引用（如适用）

每个测试答案包含：
- Agent 回答文本
- 附件文件引用（如适用）
- 符合规范的 JSONL 格式

测试结果文件展示了：
- 评分结果的预期输出格式
- 不同评分标准的评估方式
- 满足和未满足标准的示例
- LLM 评委的推理模式

**注意**：测试样本用于测试评分流程。生产环境使用时，请替换为你自己的题目和答案文件。

### 输出示例

```
============================================================
LLM Auto Scoring Script
============================================================
Questions file: questions.jsonl
Answers file: answers.jsonl
Output file: results_20251214_1530.jsonl
Model: OpenRouter-Gemini-3.0-Pro
Max concurrent: 5
Max retries: 3
Attachment path: Attachments
Question filter: All questions
Agent filter: All agents
============================================================

Raw data: 10 questions, 50 answers
Starting scoring...
Progress: 45/50 (90.0%) | Current: taskif_8 - MyAgent-2511...

============================================================
Scoring completed!
============================================================
Total scored items: 150
Total time: 245.3 seconds
Results saved to: results_20251214_1530.jsonl
============================================================
```

## 输出格式

结果保存为 JSONL 格式，每行一个评分结果：

```json
{
  "question_id": "taskif_1",
  "agent_name": "MyAgent-2511",
  "method": "OpenRouter-Gemini-3.0-Pro",
  "criterion_content": "报告包含正确的数据摘要",
  "criterion_score": 2,
  "satisfied": true,
  "reasoning": "Agent 的报告正确总结了所有关键数据点，包括..."
}
```

**输出字段：**

| 字段 | 描述 |
|------|------|
| `question_id` | 题目标识符 |
| `agent_name` | 提供答案的 Agent |
| `method` | 用于评分的 LLM 模型 |
| `criterion_content` | 正在评估的评分标准 |
| `criterion_score` | 该标准的分值 |
| `satisfied` | 是否满足标准（true/false） |
| `reasoning` | LLM 对评分决定的解释 |

## 可用模型

| 模型名称 | 提供商 | 说明 |
|----------|--------|------|
| `Gemini-2.5-Pro` | Google | 能力强，多模态 |
| `Gemini-2.5-Flash` | Google | 更快，性价比高 |
| `Gemini-2.5-Flash-Lite` | Google | 轻量版本 |
| `Gemini-3-Pro-preview` | Google | 最新预览版 |
| `ChatGPT-4o` | OpenAI | 能力强 |
| `ChatGPT-4o-Mini` | OpenAI | 更快，性价比高 |
| `ChatGPT-4-Turbo` | OpenAI | 大上下文窗口 |
| `ChatGPT-4.1` | OpenAI | 最新稳定版 |
| `ChatGPT-5` | OpenAI | 最新一代 |
| `ChatGPT-5.1` | OpenAI | 最新一代 |
| `OpenRouter-Gemini-3.0-Pro` | OpenRouter | 推荐用于评分 |
| `OpenRouter-Gemini-2.5-Pro` | OpenRouter | 通过 OpenRouter |
| `OpenRouter-Gemini-2.5-Flash` | OpenRouter | 通过 OpenRouter |
| `OpenRouter-GPT-4o` | OpenRouter | 通过 OpenRouter |
| `OpenRouter-GPT-4o-Mini` | OpenRouter | 通过 OpenRouter |
| `OpenRouter-GPT-5.1` | OpenRouter | 通过 OpenRouter |

## 高级配置

### 环境变量

`.env` 中的所有配置：

```env
# LLM API 密钥
GEMINI_API_KEY=
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
CHATGPT_API_KEY=
CHATGPT_BASE_URL=https://api.openai.com/v1
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# 默认设置
LLM_DEFAULT_MODEL=OpenRouter-Gemini-3.0-Pro
LLM_MAX_CONCURRENT=5
LLM_MAX_RETRIES=3
LLM_TIMEOUT=180

# 重试设置
LLM_RETRY_MIN_WAIT=1
LLM_RETRY_MAX_WAIT=30

# Google Search Grounding（仅 Gemini）
ENABLE_GOOGLE_SEARCH_GROUNDING=false

# PPTX 渲染
PPTX_RENDER_MODE=text  # text | image | auto
PPTX_RENDER_DPI=150
PPTX_RENDER_MAX_SLIDES=50

# HTML 内容限制
MAX_HTML_CONTENT_LENGTH=100000
```

### 断点续跑

脚本自动支持断点续跑：
- 每完成一个题目-答案对的评分，结果立即保存
- 重新运行脚本默认不会自动跳过已完成项
- 如需跳过已评分项，在代码中设置 `skip_existing=True`

### 日志

日志保存到 `logs/scoring_YYYYMMDD_HHMMSS.log`，包含以下详细信息：
- API 调用和响应
- 附件解析
- 错误和重试

在 `main.py` 中设置 `VERBOSE = True` 可启用详细模式。

## 常见问题

### 常见错误

**1. API 密钥错误**
```
ValueError: OpenRouter API Key not configured
```
解决方案：确保 `.env` 中正确设置了 API 密钥

**2. 附件未找到**
```
WARNING: Answer attachment does not exist: MyAgent-2511/result.xlsx
```
解决方案：检查文件是否存在于 `Attachments/{agent_name}/`

**3. Playwright 未安装**
```
playwright._impl._errors.Error: Executable doesn't exist
```
解决方案：运行 `playwright install chromium`

**4. poppler 未找到（pdf2image）**
```
pdf2image.exceptions.PDFInfoNotInstalledError
```
解决方案：安装 poppler-utils（参见安装章节）

## 许可证

MIT License

