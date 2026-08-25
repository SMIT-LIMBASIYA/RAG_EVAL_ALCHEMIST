# Modular RAG Evaluation Architecture Implementation Plan

Reorganize and restructure the `RAG_EVALS` codebase into a clean, modular structure as requested.

## Proposed Project Structure

```text
RAG_EVALS/
├── config.py                           # Global Pydantic Settings
├── main.py                             # Main CLI Entry Point
├── requirements.txt                    # Project dependencies
├── .env                                # Environment variables
│
├── data/                               # Datasets & Source Text
│   ├── achemist.txt                    # Raw book text
│   ├── golden_retrieval.json           # Retrieval evaluation dataset (Recall & Precision)
│   ├── golden_generator.json           # Generator evaluation dataset (Faithfulness & Relevancy)
│   └── golden_rag_pipeline.json        # End-to-end pipeline evaluation dataset
│
├── database/                           # Vector Database Layer
│   ├── __init__.py
│   └── vector_db.py                    # ChromaDB Persistent Client & Collection Manager
│
├── embeddings/                         # Ingestion & Chunking Layer
│   ├── __init__.py
│   ├── chunker.py                      # Text splitter with chunk size/overlap tuning
│   └── ingester.py                     # Loads text files and populates ChromaDB
│
├── retrieval/                          # Retrieval Module & Evaluation
│   ├── __init__.py
│   ├── retriever.py                    # Vector search + keyword re-ranker
│   ├── recall/
│   │   ├── __init__.py
│   │   └── recall_evaluator.py         # Contextual Recall metric evaluation
│   ├── precision/
│   │   ├── __init__.py
│   │   └── precision_evaluator.py      # Contextual Precision metric evaluation
│   └── run_retrieval_eval.py           # Unified runner for Recall + Precision
│
├── generator/                          # Generator Module & Evaluation
│   ├── __init__.py
│   ├── llm_generator.py                # LLM response generation engine
│   ├── faithfulness/
│   │   ├── __init__.py
│   │   └── faithfulness_evaluator.py   # Faithfulness metric evaluation (hallucination check)
│   ├── answer_relevancy/
│   │   ├── __init__.py
│   │   └── relevancy_evaluator.py      # Answer Relevancy metric evaluation
│   └── run_generator_eval.py           # Unified runner for Faithfulness + Answer Relevancy
│
└── rag_pipeline/                       # End-to-End RAG Pipeline
    ├── __init__.py
    ├── pipeline.py                     # Joins Retrieval + Generator into unified RAG system
    └── run_pipeline_eval.py            # End-to-End RAG Triad evaluation
```

---

## Proposed Changes

### 1. Data Directory (`data/`)
- [NEW] [`data/golden_retrieval.json`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/data/golden_retrieval.json): Standardized QA dataset focused on retrieval metrics (`input`, `expected_contexts`, `expected_output`).
- [NEW] [`data/golden_generator.json`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/data/golden_generator.json): Dataset focused on generator fidelity & relevancy.
- [NEW] [`data/golden_rag_pipeline.json`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/data/golden_rag_pipeline.json): Complete end-to-end golden dataset.
- [PRESERVED] [`data/achemist.txt`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/data/achemist.txt): Source book text.

---

### 2. Database Module (`database/`)
- [NEW] [`database/vector_db.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/database/vector_db.py): Dedicated ChromaDB manager providing persistent vector storage, collection reset, and upsert capabilities.

---

### 3. Embeddings & Ingestion Module (`embeddings/`)
- [NEW] [`embeddings/chunker.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/embeddings/chunker.py): Configurable `RecursiveCharacterTextSplitter`.
- [NEW] [`embeddings/ingester.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/embeddings/ingester.py): Document loader that populates ChromaDB via `database/vector_db.py`.

---

### 4. Retrieval Module (`retrieval/`)
- [NEW] [`retrieval/retriever.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/retrieval/retriever.py): Retriever class with optional keyword re-ranker.
- [NEW] [`retrieval/recall/recall_evaluator.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/retrieval/recall/recall_evaluator.py): Evaluates **Contextual Recall**.
- [NEW] [`retrieval/precision/precision_evaluator.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/retrieval/precision/precision_evaluator.py): Evaluates **Contextual Precision**.
- [NEW] [`retrieval/run_retrieval_eval.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/retrieval/run_retrieval_eval.py): Single script running **both** Recall and Precision in one command and saving a JSON report to `analyses/`.

---

### 5. Generator Module (`generator/`)
- [NEW] [`generator/llm_generator.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/generator/llm_generator.py): Generator engine supporting OpenAI / Gemini / Offline rule-based response generation.
- [NEW] [`generator/faithfulness/faithfulness_evaluator.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/generator/faithfulness/faithfulness_evaluator.py): Evaluates **Faithfulness**.
- [NEW] [`generator/answer_relevancy/relevancy_evaluator.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/generator/answer_relevancy/relevancy_evaluator.py): Evaluates **Answer Relevancy**.
- [NEW] [`generator/run_generator_eval.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/generator/run_generator_eval.py): Single script running **both** Faithfulness and Answer Relevancy in one command.

---

### 6. RAG Pipeline Module (`rag_pipeline/`)
- [NEW] [`rag_pipeline/pipeline.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/rag_pipeline/pipeline.py): Combines `retrieval/retriever.py` and `generator/llm_generator.py`.
- [NEW] [`rag_pipeline/run_pipeline_eval.py`](file:///d:/VSCODE-PROJECTS/RAG_EVALS/rag_pipeline/run_pipeline_eval.py): Runs full RAG Triad evaluation.

---

### 7. Clean Up Legacy Folders
- [DELETE] `src/` (Replaced by modular top-level packages: `database/`, `embeddings/`, `retrieval/`, `generator/`, `rag_pipeline/`).
- [DELETE] `evals/` (Replaced by specialized module evaluation runners).
- [DELETE] `goldens/` (Replaced by `data/golden_retrieval.json`, `data/golden_generator.json`, `data/golden_rag_pipeline.json`).

---

## Verification Plan

### Automated Verification
1. Test Document Ingestion:
   ```bash
   python embeddings/ingester.py --file data/achemist.txt --reset
   ```
2. Test Retrieval Evaluation (Recall + Precision):
   ```bash
   python retrieval/run_retrieval_eval.py
   ```
3. Test Generator Evaluation (Faithfulness + Relevancy):
   ```bash
   python generator/run_generator_eval.py
   ```
4. Test End-to-End RAG Pipeline:
   ```bash
   python rag_pipeline/run_pipeline_eval.py
   ```
5. Test Unified `main.py` CLI interface.
