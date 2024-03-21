import os

from datasets import load_dataset
from distilabel.dataset import DatasetCheckpoint
from distilabel.llm import OpenAILLM
from distilabel.pipeline import Pipeline

from helm_instruct.criterion.base import Criterion, Rating
from helm_instruct.criterion.nl import default_criterion
from helm_instruct.evaluator.evaluator import HelmInstructTask
from helm_instruct.evaluator.template.nl import template

OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_AUTH_TOKEN")
NEW_DATASET_NAME = "davidberenstein1957/ultra_feedback_dutch_cleaned_helm_instruct"
dataset = load_dataset("BramVanroy/ultra_feedback_dutch_cleaned")
dataset = dataset.rename_column("prompt", "prompt_english")
dataset = dataset.rename_column("prompt_dutch", "prompt")
dataset = dataset["train"].select(range(100))
irrelevant_columns = ["prompt", "prompt_english", "prompt_dutch"]
relevant_columns = [
    column_name
    for column_name in dataset.column_names
    if column_name not in irrelevant_columns
]

system_prompt_dutch = "Je bent een AI-responsbeoordelaar die zich richt op het beoordelen van instructies die duidelijk, interessant en complex zijn voor het verfijnen van open source LLM's."
task_description_dutch = "Het volgende is een instructie geschreven door een mens en een reactie op de instructie geschreven door een AI-model. Beantwoord alstublieft de volgende vragen over de reactie van het AI-model."

default_criterion["dutchness"] = Criterion(
    question="Is de tekst in vloeiend en gramaticaal correct Nederlands geschreven?",
    ratings=[
        Rating(
            value=1,
            description="De tekst is niet vloeiend en bevat veel grammaticale fouten",
        ),
        Rating(
            value=2,
            description="De tekst is niet vloeiend en bevat enkele grammaticale fouten",
        ),
        Rating(
            value=3,
            description="De tekst is vloeiend en bevat enkele grammaticale fouten",
        ),
        Rating(
            value=4,
            description="De tekst is vloeiend en bevat nauwelijks grammaticale fouten",
        ),
        Rating(
            value=5,
            description="De tekst is vloeiend en bevat geen grammaticale fouten",
        ),
    ],
)

# phase2 - review responses
checkpoint_strategy = DatasetCheckpoint(
    strategy="hf-hub",
    extra_kwargs={
        "repo_id": NEW_DATASET_NAME,
        "token": HF_API_TOKEN,
        "private": False,
        "split": "train",
    },
    save_frequency=1,
)
for column_name in relevant_columns:
    skip_dry_run = True
    dataset = dataset.rename_column(
        column_name, "response"
    )  # set column to correct input column
    for criterion_key, criterion_value in default_criterion.items():
        pipe = Pipeline(
            labeller=OpenAILLM(
                model="gpt-4-1106-preview",  # gpt-4 turbo
                task=HelmInstructTask(
                    template=template,
                    criterion=criterion_value,
                    system_prompt=system_prompt_dutch,
                    task_description=task_description_dutch,
                ),
                max_new_tokens=512,
                num_threads=8,
                api_key=OPENAI_API_TOKEN,
                temperature=0.3,
            )
        )
        dataset = pipe.generate(
            dataset,
            batch_size=100,
            skip_dry_run=skip_dry_run,
            checkpoint_strategy=checkpoint_strategy,
        )
        # rename columns to avoid overwriting data
        criterion_column = f"{criterion_key}_{column_name}"
        dataset = dataset.rename_column(
            "generations", f"generations_{criterion_column}"
        )
        dataset = dataset.rename_column("rating", f"rating_{criterion_column}")
        dataset = dataset.rename_column("rationale", f"rationale_{criterion_column}")
        skip_dry_run = False
        break
    # convert back to original column name to avoid losing data
    dataset = dataset.rename_column("response", column_name)
    if len(dataset) > 100:
        break
    print(len(dataset))
dataset.push_to_hub(NEW_DATASET_NAME, token=HF_API_TOKEN)