# Modular RAG Evaluation Framework

A production-ready evaluation suite for Retrieval-Augmented Generation (RAG) systems. This architecture implements component-level benchmarking (Retrieval, Generation) as well as end-to-end evaluation using the RAG Triad framework (Contextual Recall, Contextual Precision, Faithfulness, and Answer Relevancy).

---

## Architecture Overview

The system evaluates three distinct layers of a RAG pipeline:

```
+-------------------------------------------------------------------------------+
|                             RAG PIPELINE LAYERS                               |
+-------------------------------------------------------------------------------+

  [ Source Text ] ---> [ Chunker & Embedder ] ---> [ ChromaDB Vector Store ]
                                                             |
                                                             v
  [ User Query ]  -----------------------------------> [ Retrieval ]
                                                             |
                                                     (Top-K Contexts)
                                                             |
                                                             v
                                              [ LLM Generator (Groq/OpenAI) ]
                                                             |
                                                             v
                                                      [ Final Answer ]

+-------------------------------------------------------------------------------+
|                            EVALUATION BENCHMARKS                              |
+-------------------------------------------------------------------------------+

  1. RETRIEVAL EVALUATION   : Contextual Recall & Contextual Precision
  2. GENERATOR EVALUATION   : Faithfulness & Answer Relevancy
  3. PIPELINE EVALUATION    : End-to-End RAG Triad Validation
```

---

## Core Features

- **Component Isolation**: Independently evaluate the retriever without executing LLM generation, or evaluate generator capabilities on fixed ground-truth contexts.
- **Local & Cloud Embeddings**: Supports 100% offline, zero-cost dense embeddings via Hugging Face `sentence-transformers` (`all-MiniLM-L6-v2`, `BAAI/bge-small-en-v1.5`, `all-mpnet-base-v2`), as well as OpenAI and Google Gemini embeddings.
- **Multi-Provider LLM Generation**: Built-in support for Groq (LLaMA-3.3, LLaMA-3.1, Qwen-2.5), OpenAI (GPT-4o, GPT-4o-mini), and Google Gemini.
- **Dynamic Model Discovery**: Automatic fallback discovery that queries active cloud endpoints to prevent model ID deprecation failures.
- **Automated Reporting**: Generates formatted JSON analysis reports and CLI summary tables for all evaluation runs.

---

## Project Structure

```
RAG_EVAL_2/
|-- .env.example                     # Template environment configuration
|-- .gitignore                       # Git ignore rules for clean repo tracking
|-- requirements.txt                 # Python package dependencies
|-- config.py                        # Centralized configuration schema (Pydantic)
|-- main.py                          # CLI entry point for ingestion, evals & queries
|
|-- chunking_embeddings/
|   |-- chunker.py                   # Recursive text splitting with overlap
|   |-- embedder.py                  # Local & cloud embedding generator
|   |-- ingester.py                  # Ingestion workflow to ChromaDB
|
|-- database/
|   |-- vector_db.py                 # ChromaDB client, collection & query manager
|
|-- RAG_EVAL/
|   |-- retrieval/
|   |   |-- retriever.py             # Top-K context retrieval engine
|   |   |-- eval_retrieval.py        # Contextual Recall & Precision evaluator
|   |-- generator/
|   |   |-- generator.py             # Multi-provider LLM prompt & response engine
|   |   |-- eval_generator.py        # Faithfulness & Answer Relevancy evaluator
|   |-- rag_pipeline/
|       |-- pipeline.py              # End-to-end RAG orchestrator
|       |-- eval_pipeline.py         # Full RAG Triad benchmark evaluator
|
|-- data/
|   |-- achemist.txt                 # Source corpus (The Alchemist by Paulo Coelho)
|   |-- golden_retrieval.json        # 35 Ground-truth test cases for retrieval
|   |-- golden_generator.json        # 35 Ground-truth test cases for generator
|   |-- golden_rag_pipeline.json     # 30 Ground-truth test cases for pipeline
|
|-- analyses/                        # Timestamped JSON evaluation reports
`-- utils/
    |-- logger.py                    # Structured logging utility
    `-- report_generator.py          # Report export utility
```

---

## Prerequisites and Installation

### 1. Clone the Repository and Navigate to Root
```bash
cd d:\VSCODE-PROJECTS\RAG_EVAL_2
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Copy the `.env.example` file to create your `.env` configuration:

```bash
copy .env.example .env     # Windows
cp .env.example .env       # Linux / macOS
```

### Supported Embedding Options

| Provider | Model Name | Description |
| :--- | :--- | :--- |
| `local` *(Default)* | `BAAI/bge-small-en-v1.5` | High precision, compact (130 MB), top ranking on MTEB. |
| `local` | `all-MiniLM-L6-v2` | Ultra-fast local model (90 MB). |
| `local` | `all-mpnet-base-v2` | State-of-the-art semantic accuracy (420 MB). |
| `openai` | `text-embedding-3-small` | OpenAI cloud embedding (1536 dimensions). |
| `gemini` | `models/text-embedding-004` | Google AI Studio cloud embedding. |

---

## Step-by-Step Execution Guide

### Step 1: Ingest Document into Vector Store
Before running evaluations or queries, chunk and index the document (`./data/achemist.txt`) into ChromaDB:

```bash
# Standard ingestion
python main.py ingest

# Clean rebuild (Mandatory whenever chunk size or embedding model changes)
python main.py ingest --reset
```

---

### Step 2: Component-Level Evaluations

#### A. Retrieval Evaluation (Independent)
Evaluates context retrieval quality against 35 ground-truth query cases:
- **Contextual Recall**: Proportion of expected facts retrieved in top-K passages.
- **Contextual Precision**: Quality of ranking (are the most relevant chunks positioned at Rank #1?).

```bash
python main.py eval-retrieval
```

#### B. Generator Evaluation (Independent)
Evaluates LLM response generation on ground-truth contexts without vector retrieval variance:
- **Faithfulness**: Verifies whether all claims in the generated response are grounded in the provided context (absence of hallucinations).
- **Answer Relevancy**: Verifies that the answer directly addresses the question and aligns with expected outputs.

```bash
python main.py eval-generator
```

---

### Step 3: End-to-End Pipeline Evaluation (The RAG Triad)
Executes the full RAG pipeline (Query -> Retrieval -> LLM Generation -> Triad Scoring) across 30 comprehensive benchmark scenarios:

```bash
python main.py eval-pipeline
```

---

### Step 4: Run the Complete Benchmark Suite
Runs Retrieval, Generator, and Pipeline evaluations sequentially in one command:

```bash
python main.py eval-all
```

---

### Step 5: Interactive Querying
To query the live RAG pipeline with custom questions and inspect both the generated answer and retrieved passages:

```bash
python main.py query "Who is the King of Salem and what did he give Santiago?"
```

```bash
python main.py query "What is the Emerald Tablet in alchemy?"
```

```bash
python main.py query "Where did Santiago find his treasure in the end?"
```

---

## Evaluation Metrics Summary

| Metric | Target Layer | Definition | Pass Threshold |
| :--- | :--- | :--- | :--- |
| **Contextual Recall** | Retrieval | Percentage of relevant information retrieved from the corpus. | `>= 0.70` (70%) |
| **Contextual Precision** | Retrieval | Measure of search ranking (relevance score weighted by rank position). | `>= 0.70` (70%) |
| **Faithfulness** | Generation | Degree to which the generated answer is strictly factual to the context. | `>= 0.60` (60%) |
| **Answer Relevancy** | Generation | Directness and completeness of the response to the user query. | `>= 0.60` (60%) |

---

## Output Reports

Every evaluation run automatically generates a timestamped report saved to the `./analyses/` directory:
- `analyses/retrieval_evaluation_YYYYMMDD_HHMMSS.json`
- `analyses/generator_evaluation_YYYYMMDD_HHMMSS.json`
- `analyses/rag_pipeline_evaluation_YYYYMMDD_HHMMSS.json`

Each report contains overall summary scores as well as per-test-case queries, retrieved contexts, generated outputs, and individual metric breakdowns.
