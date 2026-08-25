"""
Main CLI Entry Point for RAG Evaluation Architecture.

Usage:
  python main.py ingest [--reset]
  python main.py eval-retrieval
  python main.py eval-generator
  python main.py eval-pipeline
  python main.py eval-all
  python main.py query "Who is the King of Salem?"
"""

import sys
import argparse
from rich.console import Console
from rich.table import Table

from config import config
from utils.logger import logger
from chunking_embeddings.ingester import DocumentIngester
from RAG_EVAL.retrieval.eval_retrieval import run_retrieval_evaluation
from RAG_EVAL.generator.eval_generator import run_generator_evaluation
from RAG_EVAL.rag_pipeline.eval_pipeline import run_pipeline_evaluation
from RAG_EVAL.rag_pipeline.pipeline import get_rag_pipeline

console = Console()


def handle_ingest(args):
    console.print("\n[bold cyan]🚀 Starting Document Ingestion...[/bold cyan]")
    ingester = DocumentIngester()
    count = ingester.ingest(filepath=args.file, reset=args.reset)
    console.print(f"[bold green]✅ Successfully indexed {count} chunks in ChromaDB![/bold green]\n")


def handle_eval_retrieval(args):
    console.print("\n[bold cyan]🔍 Running Retrieval Evaluation (Recall & Precision)...[/bold cyan]")
    res = run_retrieval_evaluation()
    _print_summary_table("Retrieval Evaluation Results", res["summary"])


def handle_eval_generator(args):
    console.print("\n[bold cyan]🤖 Running Generator Evaluation (Faithfulness & Relevancy)...[/bold cyan]")
    res = run_generator_evaluation()
    _print_summary_table("Generator Evaluation Results", res["summary"])


def handle_eval_pipeline(args):
    console.print("\n[bold cyan]⚡ Running End-to-End RAG Pipeline Evaluation (The RAG Triad)...[/bold cyan]")
    res = run_pipeline_evaluation()
    _print_summary_table("RAG Pipeline Triad Results", res["summary"])


def handle_eval_all(args):
    console.print("\n[bold magenta]====================================================[/bold magenta]")
    console.print("[bold magenta]           FULL RAG BENCHMARK SUITE               [/bold magenta]")
    console.print("[bold magenta]====================================================[/bold magenta]\n")
    handle_eval_retrieval(args)
    handle_eval_generator(args)
    handle_eval_pipeline(args)
    console.print("\n[bold green]🎉 All evaluations finished! Reports saved to './analyses/' directory.[/bold green]\n")


from rich.panel import Panel

def handle_query(args):
    console.print(f"\n[bold cyan]🔎 Querying RAG Pipeline:[/bold cyan] [white]{args.query_text}[/white]\n")
    pipeline = get_rag_pipeline()
    res = pipeline.query(args.query_text)

    # 1. Output LLM Generated Answer
    provider_info = f"{config.LLM_PROVIDER.upper()} ({config.LLM_MODEL_NAME})"
    console.print(Panel(
        f"[bold white]{res['answer']}[/bold white]",
        title=f"[bold green]🤖 Generated Answer ({provider_info})[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))

    # 2. Output Retrieved Contexts
    console.print(f"\n[bold yellow]📚 Retrieved Context Passages ({res['num_contexts']}):[/bold yellow]")
    for i, c in enumerate(res["retrieved_contexts"], 1):
        clean_c = c.replace("\n", " ").strip()
        console.print(f"[bold cyan][{i}][/bold cyan] [dim]{clean_c[:250]}...[/dim]\n")


def _print_summary_table(title: str, summary: dict):
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("Threshold / Status", justify="center")

    threshold_map = {
        "average_contextual_recall": summary.get("recall_threshold", 0.70),
        "average_contextual_precision": summary.get("precision_threshold", 0.70),
        "average_faithfulness": summary.get("faithfulness_threshold", 0.60),
        "average_answer_relevancy": summary.get("answer_relevancy_threshold", 0.60),
    }

    for k, v in summary.items():
        if k in ["total_cases", "passed", "status", "recall_threshold", "precision_threshold", "faithfulness_threshold", "answer_relevancy_threshold"]:
            continue
        val_str = f"{v:.4f}" if isinstance(v, float) else str(v)
        thresh = threshold_map.get(k)
        if thresh is not None and isinstance(v, (int, float)):
            status = "✅ PASS" if v >= thresh else "❌ FAIL"
        else:
            status = "ℹ️ INFO"
        table.add_row(k.replace("_", " ").title(), val_str, status)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Modular RAG Evaluation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Ingestion
    ingest_parser = subparsers.add_parser("ingest", help="Ingest document into ChromaDB")
    ingest_parser.add_argument("--file", type=str, default=None, help="Document path")
    ingest_parser.add_argument("--reset", action="store_true", help="Reset existing collection")

    # Evals
    subparsers.add_parser("eval-retrieval", help="Run retrieval (Recall & Precision) eval")
    subparsers.add_parser("eval-generator", help="Run generator (Faithfulness & Relevancy) eval")
    subparsers.add_parser("eval-pipeline", help="Run end-to-end RAG Triad eval")
    subparsers.add_parser("eval-all", help="Run all evaluations")

    # Interactive Query
    query_parser = subparsers.add_parser("query", help="Ask a question to the RAG pipeline")
    query_parser.add_argument("query_text", type=str, help="Question to ask")

    args = parser.parse_args()

    if args.command == "ingest":
        handle_ingest(args)
    elif args.command == "eval-retrieval":
        handle_eval_retrieval(args)
    elif args.command == "eval-generator":
        handle_eval_generator(args)
    elif args.command == "eval-pipeline":
        handle_eval_pipeline(args)
    elif args.command == "eval-all":
        handle_eval_all(args)
    elif args.command == "query":
        handle_query(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
