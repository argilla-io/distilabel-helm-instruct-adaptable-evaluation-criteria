import os

from criterion.en import default_criterion
from data import load_data_helm_insruct
from distilabel.dataset import DatasetCheckpoint
from distilabel.llm import OpenAILLM
from distilabel.pipeline import Pipeline
from distilabel.tasks import TextGenerationTask
from evaluator.evaluator import HelmInstructTask
from evaluator.template.en import template

scores = [rating.value for rating in default_criterion["Helpfulness"].ratings]
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# phase1 - generate responses
dataset = load_data_helm_insruct()
response_pipeline = Pipeline(
    generator=OpenAILLM(
        model="gpt-4-1106-preview",  # gpt-4 turbo
        task=TextGenerationTask(),
        max_new_tokens=512,
        num_threads=8,
        api_key=OPENAI_API_TOKEN,
        temperature=0.3,
    )
)
dataset = response_pipeline.generate(
    dataset,
    num_generations=1,
    batch_size=16,
    skip_dry_run=True,
)
dataset = dataset.rename_column("input", "prompt")
dataset = dataset.rename_column("generations", "response")
dataset = dataset.map(lambda x: {"response": x["response"][0], "prompt": x["prompt"]})

# phase2 - review responses
checkpoint_strategy = DatasetCheckpoint(
    extra_kwargs={
        "repo_id": "helm_instruct",
        "token": HF_API_TOKEN,
        "private": True,
        "split": "train",
    },
    save_frequency=500,
)
skip_dry_run = True
for criterion_key in default_criterion:
    pipe = Pipeline(
        labeller=OpenAILLM(
            model="gpt-4-1106-preview",  # gpt-4 turbo
            task=HelmInstructTask(template=template, criterion=criterion_key),
            max_new_tokens=512,
            num_threads=8,
            api_key=OPENAI_API_TOKEN,
            temperature=0.3,
        )
    )
    dataset = pipe.generate(
        dataset,
        num_generations=1,
        batch_size=16,
        skip_dry_run=skip_dry_run,
        # checkpoint_strategy=checkpoint_strategy,
    )
    dataset = dataset.rename_column("rating", f"rating_{criterion_key}")
    dataset = dataset.rename_column("rationale", f"rationale_{criterion_key}")
    skip_dry_run = False
# dataset.push_to_hub(NEW_DATASET_NAME, token=HF_API_TOKEN)
