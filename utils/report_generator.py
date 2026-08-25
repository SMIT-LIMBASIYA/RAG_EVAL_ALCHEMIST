"""
Evaluation report generator for JSON and Markdown summaries.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class ReportGenerator:
    @staticmethod
    def save_report(report_name: str, data: Dict[str, Any], output_dir: str = "./analyses") -> str:
        """
        Saves structured evaluation results to JSON and generates a Markdown overview.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_{timestamp}.json"
        file_path = out_path / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Generate markdown summary
        md_file_path = out_path / f"{report_name}_{timestamp}.md"
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Evaluation Report: {report_name.replace('_', ' ').title()}\n\n")
            f.write(f"- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if "summary" in data:
                f.write(f"## Summary Metrics\n\n")
                f.write("| Metric | Average Score | Status |\n")
                f.write("| --- | --- | --- |\n")
                for k, v in data["summary"].items():
                    status = "✅ PASS" if isinstance(v, (int, float)) and v >= 0.70 else "ℹ️ N/A"
                    val_str = f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
                    f.write(f"| {k} | {val_str} | {status} |\n")
                f.write("\n")

            if "test_cases" in data:
                f.write(f"## Test Case Details ({len(data['test_cases'])} items)\n\n")
                for i, tc in enumerate(data["test_cases"], 1):
                    f.write(f"### Case {i}: {tc.get('input', 'Query')}\n")
                    if "scores" in tc:
                        f.write(f"- **Scores**: `{tc['scores']}`\n")
                    if "actual_output" in tc:
                        f.write(f"- **Generated Output**: {tc['actual_output']}\n")
                    if "retrieved_contexts" in tc:
                        f.write(f"- **Retrieved Context Count**: {len(tc['retrieved_contexts'])}\n")
                    f.write("\n")

        return str(file_path)
