from pathlib import Path

from opik.evaluation import evaluate
from opik.evaluation.metrics import AnswerRelevance, Hallucination, Moderation

from second_brain_online import opik_utils
from second_brain_online.application.agents import agents, extract_tool_responses
from second_brain_online.config import settings

from .summary_density_heuristics import SummaryDensityHeuristic
from .summary_density_judge import SummaryDensityJudge

opik_utils.configure()


def evaluate_agent(prompts: list[str], retriever_config_path: Path) -> None:
    assert settings.COMET_API_KEY, (
        "COMET_API_KEY is not set. We need it to track the experiment with Opik."
    )

    print("Starting evaluation...")
    print(f"Evaluating agent with {len(prompts)} prompts.")

    def evaluation_task(x: dict) -> dict:
        """Call agentic app logic to evaluate."""

        agent = agents.get_agent(retriever_config_path=retriever_config_path)
        response = agent.run(x["input"])
        context = extract_tool_responses(agent)

        return {
            "input": x["input"],
            "context": context,
            "output": response,
        }

    # Get or create dataset
    dataset_name = "second_brain_rag_agentic_app_evaluation_dataset"
    dataset = opik_utils.get_or_create_dataset(name=dataset_name, prompts=prompts)

    # Evaluate
    agent = agents.get_agent(retriever_config_path=retriever_config_path)
    experiment_config = {
        "model_id": settings.OPENAI_MODEL_ID,
        "retriever_config_path": retriever_config_path,
        "agent_config": {
            "max_steps": agent.max_steps,
            "agent_name": agent.agent_name,
        },
    }
    scoring_metrics = [
        Hallucination(),
        AnswerRelevance(),
        Moderation(),
        SummaryDensityHeuristic(),
        SummaryDensityJudge(),
    ]

    if dataset:
        print("Evaluation details:")
        print(f"Dataset: {dataset_name}")
        print(f"Metrics: {[m.__class__.__name__ for m in scoring_metrics]}")

        evaluate(
            dataset=dataset,
            task=evaluation_task,
            scoring_metrics=scoring_metrics,
            experiment_config=experiment_config,
            task_threads=2,
        )
    else:
        print("Can't run the evaluation as the dataset items are empty.")