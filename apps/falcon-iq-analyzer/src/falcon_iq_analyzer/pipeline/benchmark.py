from __future__ import annotations

import logging

from falcon_iq_analyzer.config import Settings
from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.domain import AnalysisResult, BenchmarkResult
from falcon_iq_analyzer.pipeline.job_manager import JobManager
from falcon_iq_analyzer.services.benchmark_report_generator import generate_benchmark_report
from falcon_iq_analyzer.services.prompt_evaluator import evaluate_single_prompt, summarize_evaluations
from falcon_iq_analyzer.services.prompt_generator import generate_prompts
from falcon_iq_analyzer.storage import create_storage_service

logger = logging.getLogger(__name__)


async def run_benchmark(
    result_a: AnalysisResult,
    result_b: AnalysisResult,
    num_prompts: int,
    llm: LLMClient,
    settings: Settings,
    job_manager: JobManager,
    job_id: str,
) -> None:
    """Run the full benchmark pipeline."""
    try:
        storage = create_storage_service()
        total_steps = 1 + num_prompts + 1 + 1  # generate + evaluate each + summarize + report
        step = 0

        # Step 1: Generate prompts
        step += 1
        job_manager.update_status(job_id, "running", f"Step {step}/{total_steps}: Generating {num_prompts} prompts...")
        gen_result = await generate_prompts(llm, result_a, result_b, num_prompts)
        prompts = gen_result.prompts
        actual_total = 1 + len(prompts) + 1 + 1
        logger.info("Benchmark: generated %d prompts", len(prompts))

        # Step 2: Evaluate each prompt sequentially
        evaluations = []
        for i, prompt in enumerate(prompts):
            step += 1
            job_manager.update_status(
                job_id, "running",
                f"Step {step}/{actual_total}: Evaluating prompt {i + 1}/{len(prompts)} ({prompt.category})..."
            )
            evaluation = await evaluate_single_prompt(llm, prompt, result_a.company_name, result_b.company_name)
            evaluations.append(evaluation)
            logger.info("Benchmark: evaluated prompt %d/%d — winner: %s", i + 1, len(prompts), evaluation.winner)

        # Step 3: Summarize
        step += 1
        job_manager.update_status(job_id, "running", f"Step {step}/{actual_total}: Summarizing results...")
        summary = await summarize_evaluations(llm, result_a.company_name, result_b.company_name, evaluations)
        logger.info("Benchmark: summary complete — %s wins: %d, %s wins: %d",
                     result_a.company_name, summary.company_a_wins,
                     result_b.company_name, summary.company_b_wins)

        # Step 4: Generate report
        step += 1
        job_manager.update_status(job_id, "running", f"Step {step}/{actual_total}: Generating report...")
        benchmark_result = BenchmarkResult(
            company_a=result_a.company_name,
            company_b=result_b.company_name,
            prompts=prompts,
            evaluations=evaluations,
            summary=summary,
        )
        benchmark_result.markdown_report = generate_benchmark_report(benchmark_result)

        # Save report and full result via storage service
        report_key = f"benchmarks/benchmark-{job_id}.md"
        storage.save_file(report_key, benchmark_result.markdown_report, "text/markdown")
        logger.info("Benchmark report saved to %s", report_key)

        result_key = f"benchmarks/benchmark-result-{job_id}.json"
        storage.save_file(result_key, benchmark_result.model_dump_json(indent=2), "application/json")
        logger.info("Persisted benchmark result to %s", result_key)

        job_manager.set_benchmark_result(job_id, benchmark_result)

    except Exception as e:
        logger.exception("Benchmark pipeline failed")
        job_manager.set_error(job_id, str(e))
