"""
Retrieval Evaluator: Measures Contextual Recall and Contextual Precision using DeepEval.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import config
from utils.logger import logger
from utils.report_generator import ReportGenerator
from RAG_EVAL.retrieval.retriever import get_retriever

try:
    from deepeval.metrics import ContextualRecallMetric, ContextualPrecisionMetric
    from deepeval.test_case import LLMTestCase
    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


class RetrievalEvaluator:
    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path or config.GOLDEN_RETRIEVAL_PATH)
        self.retriever = get_retriever()

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Loads evaluation test cases from JSON dataset."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Retrieval dataset not found at {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _standalone_score(self, retrieved: List[str], expected: List[str]) -> Dict[str, float]:
        """Calculates keyword/overlap recall & precision if deepeval is unavailable."""
        if not expected or not retrieved:
            return {"contextual_recall": 0.0, "contextual_precision": 0.0}

        retrieved_text = " ".join(retrieved).lower()
        matched_expected = 0

        for exp in expected:
            words = [w for w in exp.lower().split() if len(w) > 3]
            if words:
                overlap = sum(1 for w in words if w in retrieved_text) / len(words)
                if overlap >= 0.20:
                    matched_expected += 1

        recall = matched_expected / max(len(expected), 1)

        precision_scores = []
        for rank, chunk in enumerate(retrieved, 1):
            c_words = [w for w in chunk.lower().split() if len(w) > 3]
            match_any = False
            for exp in expected:
                exp_words = [w for w in exp.lower().split() if len(w) > 3]
                overlap = sum(1 for w in exp_words if w in chunk.lower()) / max(len(exp_words), 1)
                if overlap >= 0.15:
                    match_any = True
                    break
            if match_any:
                precision_scores.append(1.0 / rank)

        precision = min(1.0, sum(precision_scores)) if precision_scores else 0.0
        return {
            "contextual_recall": round(recall, 4),
            "contextual_precision": round(precision, 4)
        }

    def evaluate(self) -> Dict[str, Any]:
        """Runs retrieval evaluation on all golden test items."""
        dataset = self.load_dataset()
        logger.info(f"Evaluating {len(dataset)} retrieval test cases using judge model '{config.EVAL_JUDGE_MODEL}'...")

        results = []
        total_recall = 0.0
        total_precision = 0.0

        for idx, item in enumerate(dataset, 1):
            query = item["input"]
            expected_contexts = item.get("expected_contexts", [])
            expected_output = item.get("expected_output", "")

            retrieved_contexts = self.retriever.retrieve(query)

            scores = {}
            if HAS_DEEPEVAL and config.OPENAI_API_KEY:
                try:
                    test_case = LLMTestCase(
                        input=query,
                        actual_output=expected_output,
                        expected_output=expected_output,
                        retrieval_context=retrieved_contexts,
                        context=expected_contexts
                    )
                    recall_metric = ContextualRecallMetric(
                        threshold=config.RETRIEVAL_RECALL_THRESHOLD,
                        model=config.EVAL_JUDGE_MODEL
                    )
                    precision_metric = ContextualPrecisionMetric(
                        threshold=config.RETRIEVAL_PRECISION_THRESHOLD,
                        model=config.EVAL_JUDGE_MODEL
                    )

                    recall_metric.measure(test_case)
                    precision_metric.measure(test_case)

                    scores["contextual_recall"] = float(recall_metric.score)
                    scores["contextual_precision"] = float(precision_metric.score)
                except Exception as e:
                    logger.warning(f"DeepEval measure failed: {e}. Using fallback metric.")
                    scores = self._standalone_score(retrieved_contexts, expected_contexts)
            else:
                scores = self._standalone_score(retrieved_contexts, expected_contexts)

            total_recall += scores.get("contextual_recall", 0.0)
            total_precision += scores.get("contextual_precision", 0.0)

            results.append({
                "case_id": idx,
                "input": query,
                "expected_contexts": expected_contexts,
                "retrieved_contexts": retrieved_contexts,
                "scores": scores
            })

        avg_recall = total_recall / max(len(dataset), 1)
        avg_precision = total_precision / max(len(dataset), 1)

        summary = {
            "total_cases": len(dataset),
            "judge_model": config.EVAL_JUDGE_MODEL,
            "average_contextual_recall": round(avg_recall, 4),
            "average_contextual_precision": round(avg_precision, 4),
            "recall_threshold": config.RETRIEVAL_RECALL_THRESHOLD,
            "precision_threshold": config.RETRIEVAL_PRECISION_THRESHOLD,
            "passed": avg_recall >= config.RETRIEVAL_RECALL_THRESHOLD and avg_precision >= config.RETRIEVAL_PRECISION_THRESHOLD
        }

        report_data = {
            "summary": summary,
            "test_cases": results
        }

        saved_path = ReportGenerator.save_report(
            report_name="retrieval_evaluation",
            data=report_data,
            output_dir=config.ANALYSIS_OUTPUT_DIR
        )

        logger.info(f"Retrieval Evaluation complete! Report saved to {saved_path}")
        logger.info(f"Summary: Recall={avg_recall:.4f}, Precision={avg_precision:.4f}")
        return report_data


def run_retrieval_evaluation():
    evaluator = RetrievalEvaluator()
    return evaluator.evaluate()


if __name__ == "__main__":
    run_retrieval_evaluation()
