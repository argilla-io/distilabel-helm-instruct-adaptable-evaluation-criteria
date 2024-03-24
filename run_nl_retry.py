import os

from datasets import concatenate_datasets, load_dataset
from distilabel.dataset import DatasetCheckpoint
from distilabel.llm import OpenAILLM
from distilabel.pipeline import Pipeline

from helm_instruct.criterion.base import Criterion, Rating
from helm_instruct.criterion.nl import default_criterion
from helm_instruct.evaluator.evaluator import HelmInstructTask
from helm_instruct.evaluator.template.nl import template

OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_AUTH_TOKEN")
NEW_DATASET_NAME = "davidberenstein1957/ultra_feedback_dutch_cleaned_helm_instruct_geitje_ultra_vs_gpt4_turbo_clean"
dataset = load_dataset(
    "davidberenstein1957/ultra_feedback_dutch_cleaned_rated_split_model_and_criterion"
)
column_select = ["idx", "prompt", "response", "rating"]
models = ["geitje", "gpt-4"]

system_prompt_dutch = "Je bent een AI-responsbeoordelaar die zich richt op het beoordelen van instructies die duidelijk, interessant en complex zijn voor het verfijnen van open source LLM's."
task_description_dutch = "Het volgende is een instructie geschreven door een mens en een reactie op de instructie geschreven door een AI-model. Beantwoord alstublieft de volgende vragen over de reactie van het AI-model."

default_criterion["Dutchness"] = Criterion(
    question="Is de tekst in vlot en gramaticaal correct Nederlands geschreven? Negeer code-fragmenten in je analyse en richt je enkel op lopende tekst. Leenwoorden uit andere talen mogen gebruikt worden als dat gewoonlijk is in het veld (bv. bij software).",
    ratings=[
        Rating(
            value=1,
            description="De tekst is onleesbaar of bevat veel grammaticale fouten.",
        ),
        Rating(
            value=2,
            description="De tekst is moeilijk te begrijpen of bevat veel grammaticale fouten.",
        ),
        Rating(
            value=3,
            description="De tekst is begrijpelijk maar bevat enkele grammaticale fouten.",
        ),
        Rating(
            value=4,
            description="De tekst is goed geschreven en bevat weinig grammaticale fouten.",
        ),
        Rating(
            value=5,
            description="De tekst is uitstekend geschreven en bevat geen grammaticale fouten.",
        ),
    ],
)
del default_criterion["Harmlessness"]
del default_criterion["Understandability"]
del default_criterion["Completeness"]

criteria = ["Dutchness", "Conciseness", "Helpfulness"]

dataset["geitje.Helpfulness_retry"] = dataset["geitje.Helpfulness"]
# Merge retry splits with original sets
retry_splits = [split for split in dataset if "retry" in split]
for retry_split in retry_splits:
    original_split = retry_split.replace("_retry", "")
    dataset[retry_split] = dataset[retry_split].filter(
        lambda x: x["rating"] is not None
    )
    unique_idx = dataset[retry_split].unique("idx")
    dataset[retry_split] = dataset[original_split].filter(
        lambda x: x["idx"] not in unique_idx
    )
    dataset[original_split] = concatenate_datasets(
        [dataset[retry_split], dataset[original_split]]
    )
    del dataset[retry_split]
assert "geitje.Helpfulness_retry" not in dataset
assert len(dataset["geitje.Helpfulness"].filter(lambda x: x["rating"] is None)) == 0

# phase2 - review responses
for criterion in criteria:
    for split in dataset:
        if all(x is None for x in dataset[split]["rating"]):
            pass
        else:
            split = split + "_retry"
        dataset = dataset[split].filter(lambda x: x["rating"] is None)
        if len(dataset):
            checkpoint_strategy = DatasetCheckpoint(
                strategy="hf-hub",
                extra_kwargs={
                    "repo_id": NEW_DATASET_NAME,
                    "token": HF_API_TOKEN,
                    "private": False,
                    "split": split,
                },
                save_frequency=5,
            )

            pipe = Pipeline(
                labeller=OpenAILLM(
                    model="gpt-4-1106-preview",  # gpt-4 turbo
                    task=HelmInstructTask(
                        template=template,
                        criterion=criterion,
                        system_prompt=system_prompt_dutch,
                        task_description=task_description_dutch,
                    ),
                    max_new_tokens=8,
                    num_threads=8,
                    api_key=OPENAI_API_TOKEN,
                    temperature=0.3,
                )
            )
            dataset = pipe.generate(
                dataset,
                batch_size=100,
                skip_dry_run=False,
                checkpoint_strategy=checkpoint_strategy,
            )

    # convert back to original column name to avoid losing data
    dataset.push_to_hub(
        NEW_DATASET_NAME, token=HF_API_TOKEN, split=split, private=False
    )
