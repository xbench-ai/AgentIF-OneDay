# LLM Auto Scoring Script

A standalone LLM-based auto-scoring tool that evaluates agent responses against predefined criteria. No database, Redis, or MinIO dependencies required.

[中文文档](README_cn.md)

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Preparing Your Data](#preparing-your-data)
- [Running the Scorer](#running-the-scorer)
- [Output Format](#output-format)
- [Available Models](#available-models)
- [Advanced Configuration](#advanced-configuration)

## Features

- **Multi-model Support**: Gemini, ChatGPT, and OpenRouter models
- **Concurrent Processing**: Configurable parallel scoring for efficiency
- **Attachment Parsing**: Supports PDF, Word, Excel, PowerPoint, images, HTML, and code files
- **Checkpoint Resume**: Automatically saves progress, resume from interruption
- **Flexible Filtering**: Score specific questions or agents only

## Quick Start

```bash
# 1. Clone and setup environment
conda create -n llm_score python=3.11
conda activate llm_score
pip install -r requirements.txt
playwright install chromium

# 2. Configure API keys
cp env.example .env
# Edit .env and add your API keys

# 3. Prepare your data files (questions.jsonl, answers.jsonl)

# 4. Edit llm_score/main.py to set file paths

# 5. Run scoring
python -m llm_score.main
```

## Installation

### Prerequisites

- Python 3.11+
- Conda (recommended) or pip

### Step 1: Create Environment

```bash
conda create -n llm_score python=3.11
conda activate llm_score
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install Playwright Browser

Playwright is required for HTML rendering:

```bash
playwright install chromium
```

### Step 4: Install System Dependencies (for pdf2image)

For PDF/PPTX rendering, you need poppler:

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Download from [poppler releases](https://github.com/osber/poppler-windows/releases) and add to PATH.

## Configuration

### Setting Up API Keys

Create a `.env` file in the project root directory:

```bash
cp env.example .env
```

Edit `.env` and configure your LLM API keys:

```env
# LLM API Keys (configure the ones you need)
GEMINI_API_KEY=your-gemini-api-key
CHATGPT_API_KEY=your-chatgpt-api-key
OPENROUTER_API_KEY=your-openrouter-api-key

# LLM Settings
LLM_DEFAULT_MODEL=OpenRouter-Gemini-3.0-Pro
LLM_MAX_CONCURRENT=5
LLM_MAX_RETRIES=3
LLM_TIMEOUT=180
```

You only need to configure the API key for the model you plan to use.

## Preparing Your Data

### Directory Structure

Organize your files as follows:

```
your_project/
├── .env                          # API configuration
├── questions.jsonl               # Questions file
├── answers.jsonl                 # Answers file
└── Attachments/                  # Attachments directory
    ├── Questions/                # Question attachments
    │   ├── task1_image.png
    │   └── task2_doc.pdf
    ├── MyAgent-2511/             # Agent answer attachments
    │   ├── result.xlsx
    │   └── report.md
    ├── AnotherAgent/             # Another agent's attachments
    │   └── output.zip
    └── Reference_answer/         # Reference answer attachments (optional)
        └── expected_result.xlsx
```

### Questions File (questions.jsonl)

Each line is a JSON object representing a question:

```json
{
  "question_id": "taskif_1",
  "title": "Data Analysis Task",
  "description": "Please analyze the provided dataset and generate a summary report...",
  "attachment_filenames": ["dataset.xlsx", "instructions.pdf"],
  "score_criteria": [
    {"content": "Report includes correct data summary", "score": 2},
    {"content": "Charts are properly formatted", "score": 1},
    {"content": "Missing required sections (deduction)", "score": -1}
  ],
  "reference_answer_description": "The report should contain...",
  "reference_answer_attachment_filenames": ["expected_report.pdf"]
}
```

**Field Descriptions:**

| Field | Required | Description |
|-------|----------|-------------|
| `question_id` | Yes | Unique identifier for the question |
| `title` | Yes | Question title |
| `description` | Yes | Detailed question description |
| `attachment_filenames` | No | List of question attachment filenames (in `Attachments/Questions/`) |
| `score_criteria` | Yes | List of scoring criteria |
| `score_criteria[].content` | Yes | Criterion description |
| `score_criteria[].score` | Yes | Points for this criterion (negative for deductions) |
| `reference_answer_description` | No | Text description of expected answer |
| `reference_answer_attachment_filenames` | No | Reference answer attachments (in `Attachments/Reference_answer/`) |

### Answers File (answers.jsonl)

Each line is a JSON object representing an agent's answer:

```json
{
  "question_id": "taskif_1",
  "agent_name": "MyAgent-2511",
  "content": {"text": "Here is my analysis of the dataset...\n\nThe key findings are..."},
  "attachment_filenames": ["analysis_report.xlsx", "charts.png"]
}
```

**Field Descriptions:**

| Field | Required | Description |
|-------|----------|-------------|
| `question_id` | Yes | Must match a question_id in questions file |
| `agent_name` | Yes | Name of the agent (also the attachment subdirectory name) |
| `content` | Yes | Answer content object |
| `content.text` | Yes | Text content of the answer |
| `attachment_filenames` | No | List of answer attachments (in `Attachments/{agent_name}/`) |

### Attachment Path Rules

- **Question attachments**: `Attachments/Questions/{filename}`
- **Answer attachments**: `Attachments/{agent_name}/{filename}`
- **Reference answer attachments**: `Attachments/Reference_answer/{filename}`

### Supported Attachment Formats

| Category | Extensions |
|----------|------------|
| Documents | `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.csv` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp` |
| Web | `.html`, `.htm` |
| Code | `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.md`, `.txt`, `.json`, `.xml`, `.yaml` |
| Archives | `.zip` (contents will be extracted and parsed) |
| Notebooks | `.ipynb` |

## Running the Scorer

### Step 1: Configure Input/Output Paths

Edit the configuration section at the top of `llm_score/main.py`:

```python
# Input file paths
QUESTIONS_FILE = "path/to/your/questions.jsonl"
ANSWERS_FILE = "path/to/your/answers.jsonl"

# Output file prefix (timestamp will be added automatically)
OUTPUT_FILE_PREFIX = "results"

# LLM Model to use
MODEL_NAME = "OpenRouter-Gemini-3.0-Pro"

# Concurrency settings (optional, uses .env defaults if None)
MAX_CONCURRENT = None
MAX_RETRIES = None

# Attachment base path
ATTACHMENT_BASE_PATH = "Attachments"

# Filter settings (optional)
QUESTION_IDS = None  # e.g., ["taskif_1", "taskif_2"] to score specific questions
AGENT_NAMES = None   # e.g., ["MyAgent-2511"] to score specific agents

# Verbose logging
VERBOSE = False
```

### Step 2: Run the Script

```bash
python -m llm_score.main
```

## Testing with Sample Data

The project includes test samples in the `sample/` directory for quick testing:

- `sample/sample_questions_10.jsonl` - 10 sample questions covering various task types
- `sample/sample_answers_10.jsonl` - 10 corresponding sample answers
- `sample/sample_results_10.jsonl` - Expected scoring results for reference

### Quick Test Run

To test the scoring system with sample data:

1. **Update the configuration in `llm_score/main.py`:**

```python
# Input file paths
QUESTIONS_FILE = "sample/sample_questions_10.jsonl"
ANSWERS_FILE = "sample/sample_answers_10.jsonl"
```

2. **Run the scorer:**

```bash
python -m llm_score.main
```

3. **Compare results** (optional):

After running, you can compare your output with `sample/sample_results_10.jsonl` to verify the scoring behavior. The sample results file contains scoring outputs for all criteria across all 10 question-answer pairs, showing:
- Whether each criterion was satisfied (`satisfied: true/false`)
- The reasoning provided by the LLM judge
- The scoring method used

### Sample Data Overview

The sample data includes diverse question types:

- **Quantum Computing Tasks**: Resource estimation, algorithm implementation
- **Web Development**: GUI updates, HTML generation
- **Data Extraction**: Paper data extraction, scholar information collection
- **Research Tasks**: Market research, paper compilation
- **Creative Tasks**: Image generation, marketing material design
- **Analysis Tasks**: Cost analysis, upgrade planning

Each sample question includes:
- Complete question description
- Scoring criteria with positive and negative points
- Reference answer descriptions
- Attachment file references (if applicable)

Each sample answer includes:
- Agent response text
- Attachment file references (if applicable)
- Proper JSONL formatting

The sample results file demonstrates:
- Expected output format for scoring results
- How different criteria are evaluated
- Examples of satisfied and unsatisfied criteria
- Reasoning patterns from the LLM judge

**Note**: The sample data is designed for testing the scoring pipeline. For production use, replace with your actual questions and answers files.

### Example Output

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

## Output Format

Results are saved as JSONL, one scoring result per line:

```json
{
  "question_id": "taskif_1",
  "agent_name": "MyAgent-2511",
  "method": "OpenRouter-Gemini-3.0-Pro",
  "criterion_content": "Report includes correct data summary",
  "criterion_score": 2,
  "satisfied": true,
  "reasoning": "The agent's report correctly summarizes all key data points including..."
}
```

**Output Fields:**

| Field | Description |
|-------|-------------|
| `question_id` | Question identifier |
| `agent_name` | Agent that provided the answer |
| `method` | LLM model used for scoring |
| `criterion_content` | The scoring criterion being evaluated |
| `criterion_score` | Points for this criterion |
| `satisfied` | Whether the criterion was met (true/false) |
| `reasoning` | LLM's explanation for the scoring decision |

## Available Models

| Model Name | Provider | Notes |
|------------|----------|-------|
| `Gemini-2.5-Pro` | Google | High capability, multimodal |
| `Gemini-2.5-Flash` | Google | Faster, cost-effective |
| `Gemini-2.5-Flash-Lite` | Google | Lightweight version |
| `Gemini-3-Pro-preview` | Google | Latest preview |
| `ChatGPT-4o` | OpenAI | High capability |
| `ChatGPT-4o-Mini` | OpenAI | Faster, cost-effective |
| `ChatGPT-4-Turbo` | OpenAI | High context window |
| `ChatGPT-4.1` | OpenAI | Latest stable |
| `ChatGPT-5` | OpenAI | Latest generation |
| `ChatGPT-5.1` | OpenAI | Latest generation |
| `OpenRouter-Gemini-3.0-Pro` | OpenRouter | Recommended for scoring |
| `OpenRouter-Gemini-2.5-Pro` | OpenRouter | Via OpenRouter |
| `OpenRouter-Gemini-2.5-Flash` | OpenRouter | Via OpenRouter |
| `OpenRouter-GPT-4o` | OpenRouter | Via OpenRouter |
| `OpenRouter-GPT-4o-Mini` | OpenRouter | Via OpenRouter |
| `OpenRouter-GPT-5.1` | OpenRouter | Via OpenRouter |

## Advanced Configuration

### Environment Variables

All settings in `.env`:

```env
# LLM API Keys
GEMINI_API_KEY=
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
CHATGPT_API_KEY=
CHATGPT_BASE_URL=https://api.openai.com/v1
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Default Settings
LLM_DEFAULT_MODEL=OpenRouter-Gemini-3.0-Pro
LLM_MAX_CONCURRENT=5
LLM_MAX_RETRIES=3
LLM_TIMEOUT=180

# Retry Settings
LLM_RETRY_MIN_WAIT=1
LLM_RETRY_MAX_WAIT=30

# Google Search Grounding (Gemini only)
ENABLE_GOOGLE_SEARCH_GROUNDING=false

# PPTX Rendering
PPTX_RENDER_MODE=text  # text | image | auto
PPTX_RENDER_DPI=150
PPTX_RENDER_MAX_SLIDES=50

# HTML Content Limit
MAX_HTML_CONTENT_LENGTH=100000
```

### Checkpoint Resume

The script automatically supports checkpoint resume:
- Results are saved immediately after each question-answer pair is scored
- Re-running the script will NOT automatically skip completed items
- Set `skip_existing=True` in the code if you want to skip already scored items

### Logging

Logs are saved to `logs/scoring_YYYYMMDD_HHMMSS.log` with detailed information about:
- API calls and responses
- Attachment parsing
- Errors and retries

Enable verbose mode by setting `VERBOSE = True` in `main.py`.

## Troubleshooting

### Common Issues

**1. API Key Error**
```
ValueError: OpenRouter API Key not configured
```
Solution: Ensure your API key is correctly set in `.env`

**2. Attachment Not Found**
```
WARNING: Answer attachment does not exist: MyAgent-2511/result.xlsx
```
Solution: Check that the file exists in `Attachments/{agent_name}/`

**3. Playwright Not Installed**
```
playwright._impl._errors.Error: Executable doesn't exist
```
Solution: Run `playwright install chromium`

**4. poppler Not Found (pdf2image)**
```
pdf2image.exceptions.PDFInfoNotInstalledError
```
Solution: Install poppler-utils (see Installation section)

## License

MIT License
