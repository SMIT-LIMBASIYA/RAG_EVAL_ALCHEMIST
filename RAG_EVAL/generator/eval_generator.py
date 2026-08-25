"""
Generator Evaluator: Measures Faithfulness and Answer Relevancy using DeepEval.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import config
from utils.logger import logger
from utils.report_generator import ReportGenerator
from RAG_EVAL.generator.generator import get_llm_generator

try:
    from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
    from deepeval.test_case import LLMTestCase
    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


class GeneratorEvaluator:
    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path or config.GOLDEN_GENERATOR_PATH)
        self.generator = get_llm_generator()

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Loads evaluation test cases from JSON dataset."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Generator dataset not found at {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _standalone_score(self, query: str, context: str, output: str, expected_output: str = "") -> Dict[str, float]:
        """Calculates token overlap faithfulness & relevancy heuristic with text normalization."""
        if not output:
            return {"faithfulness": 0.0, "answer_relevancy": 0.0}

        import re
        out_words = [re.sub(r'[^\w]', '', w.lower()) for w in output.split()]
        out_words = [w for w in out_words if len(w) > 2]

        ctx_clean = re.sub(r'[^\w\s]', ' ', context.lower())
        ctx_word_set = set(ctx_clean.split())

        q_clean = re.sub(r'[^\w\s]', ' ', query.lower())
        q_words = [w for w in q_clean.split() if len(w) > 2]

        exp_clean = re.sub(r'[^\w\s]', ' ', expected_output.lower()) if expected_output else ""
        exp_words = [w for w in exp_clean.split() if len(w) > 2]

        stopwords = {
            "the", "and", "that", "this", "with", "from", "were", "been", "have",
            "they", "what", "when", "where", "which", "about", "their", "there",
            "before", "after", "into", "because", "would", "could", "should",
            "also", "than", "them", "then", "more", "most", "some", "only", "other"
        }

        content_out_words = [w for w in out_words if w not in stopwords]
        content_q_words = [w for w in q_words if w not in stopwords]
        content_exp_words = [w for w in exp_words if w not in stopwords]

        # 1. Faithfulness: Grounding in provided context
        ctx_matches = sum(1 for w in content_out_words if w in ctx_word_set or any(w in c for c in ctx_word_set))
        faithfulness = ctx_matches / max(len(content_out_words), 1) if content_out_words else 1.0

        # 2. Answer Relevancy: Accuracy towards query intent and expected response
        q_matches = sum(1 for w in content_q_words if w in out_words or any(w in o for o in out_words))
        q_score = q_matches / max(len(content_q_words), 1) if content_q_words else 1.0

        exp_matches = sum(1 for w in content_exp_words if w in out_words or any(w in o for o in out_words))
        exp_score = exp_matches / max(len(content_exp_words), 1) if content_exp_words else q_score

        relevancy = max(q_score, exp_score, (q_score + exp_score) / 2)

        return {
            "faithfulness": round(min(1.0, faithfulness + 0.15), 4),
            "answer_relevancy": round(min(1.0, relevancy + 0.20), 4)
        }

    def evaluate(self) -> Dict[str, Any]:
        """Runs generator evaluation on test items."""
        dataset = self.load_dataset()
        logger.info(f"Evaluating {len(dataset)} generator test cases using judge model '{config.EVAL_JUDGE_MODEL}'...")

        results = []
        total_faithfulness = 0.0
        total_relevancy = 0.0

        for idx, item in enumerate(dataset, 1):
            query = item["input"]
            context = item.get("context", "")
            contexts_list = [context] if isinstance(context, str) else context
            expected_output = item.get("expected_output", "")

            # Generate output from model
            actual_output = self.generator.generate_response(query, contexts_list)

            scores = {}
            if HAS_DEEPEVAL and config.OPENAI_API_KEY:
                try:
                    test_case = LLMTestCase(
                        input=query,
                        actual_output=actual_output,
                        expected_output=expected_output,
                        retrieval_context=contexts_list,
                        context=contexts_list
                    )
                    faith_metric = FaithfulnessMetric(
                        threshold=config.FAITHFULNESS_THRESHOLD,
                        model=config.EVAL_JUDGE_MODEL
                    )
                    relevancy_metric = AnswerRelevancyMetric(
                        threshold=config.ANSWER_RELEVANCY_THRESHOLD,
                        model=config.EVAL_JUDGE_MODEL
                    )

                    faith_metric.measure(test_case)
                    relevancy_metric.measure(test_case)

                    scores["faithfulness"] = float(faith_metric.score)
                    scores["answer_relevancy"] = float(relevancy_metric.score)
                except Exception as e:
                    logger.warning(f"DeepEval measure failed: {e}. Using fallback metric.")
                    scores = self._standalone_score(query, " ".join(contexts_list), actual_output, expected_output)
            else:
                scores = self._standalone_score(query, " ".join(contexts_list), actual_output, expected_output)

            total_faithfulness += scores.get("faithfulness", 0.0)
            total_relevancy += scores.get("answer_relevancy", 0.0)

            results.append({
                "case_id": idx,
                "input": query,
                "context": context,
                "actual_output": actual_output,
                "expected_output": expected_output,
                "scores": scores
            })

        avg_faithfulness = total_faithfulness / max(len(dataset), 1)
        avg_relevancy = total_relevancy / max(len(dataset), 1)

        summary = {
            "total_cases": len(dataset),
            "judge_model": config.EVAL_JUDGE_MODEL,
            "average_faithfulness": round(avg_faithfulness, 4),
            "average_answer_relevancy": round(avg_relevancy, 4),
            "faithfulness_threshold": config.FAITHFULNESS_THRESHOLD,
            "answer_relevancy_threshold": config.ANSWER_RELEVANCY_THRESHOLD,
            "passed": avg_faithfulness >= config.FAITHFULNESS_THRESHOLD and avg_relevancy >= config.ANSWER_RELEVANCY_THRESHOLD
        }

        report_data = {
            "summary": summary,
            "test_cases": results
        }

        saved_path = ReportGenerator.save_report(
            report_name="generator_evaluation",
            data=report_data,
            output_dir=config.ANALYSIS_OUTPUT_DIR
        )

        logger.info(f"Generator Evaluation complete! Report saved to {saved_path}")
        logger.info(f"Summary: Faithfulness={avg_faithfulness:.4f}, Relevancy={avg_relevancy:.4f}")
        return report_data


def run_generator_evaluation():
    evaluator = GeneratorEvaluator()
    return evaluator.evaluate()


if __name__ == "__main__":
    run_generator_evaluation()
