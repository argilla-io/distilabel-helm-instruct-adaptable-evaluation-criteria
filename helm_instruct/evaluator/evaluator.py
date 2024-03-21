"""
$ python dibt/synthetic_evaluator.py
"""

from dataclasses import dataclass
from typing import List, TypedDict

import regex as re
from distilabel.tasks import Prompt, TextGenerationTask

from helm_instruct.criterion.en import Rating, default_criterion


class HelmInstructOutput(TypedDict):
    """A `TypedDict` representing the output of an `PromptEvaluationTask`."""

    rating: float
    rationale: str


@dataclass
class HelmInstructTask(TextGenerationTask):
    """Rough translation from the guidelines for the labelling task:
    https://crfm.stanford.edu/2024/02/18/helm-instruct.html
    to a distilabel task.
    """

    template: str
    criterion: str = None
    task_description: str = (
        "The following is an instruction written by a human, and a response to the instruction written by an AI model. Please answer the following questions about the AI model’s response."
    )
    system_prompt: str = (
        "You are an AI response evaluator focused on rating prompts that are clear, interesting and complex for fine-tuning open source LLMs."
    )
    criterion_question: str = None
    criterion_options: List[Rating] = None

    @property
    def input_args_names(self) -> List[str]:
        """Returns the input args names for the task."""
        return ["prompt", "response"]

    def generate_prompt(self, prompt: str, response: str) -> Prompt:
        scores = [rating["value"] for rating in self.criterion_options]
        render_kwargs = {
            "task_description": self.task_description,
            "criterion_question": self.criterion_question,
            "criterion_options": self.criterion_options,
            "min_score": min(scores),
            "max_score": max(scores),
            "prompt": prompt,
            "response": response,
        }
        return Prompt(
            system_prompt=self.system_prompt,
            formatted_prompt=self.template.format(**render_kwargs),
        )

    @classmethod
    def for_helpfullness(cls):
        return cls(criterion="Helpfulness")

    @classmethod
    def for_understandability(cls):
        return cls(criterion="Understandability")

    @classmethod
    def for_completeness(cls):
        return cls(criterion="Completeness")

    @classmethod
    def for_conciseness(cls):
        return cls(criterion="Conciseness")

    @classmethod
    def for_harmlessness(cls):
        return cls(criterion="Harmlessness")

    def __post_init__(self):
        self.criterion_question = default_criterion[self.criterion]["question"]
        self.criterion_options = default_criterion[self.criterion]["ratings"]
        self.task_description = default_criterion[self.criterion]["question"]

    def parse_output(self, output: str) -> HelmInstructOutput:  # type: ignore
        """Parses the output of the model into the desired format."""
        pattern = r"<rating>(.*?)</rating>\s*<rationale>(.*?)</rationale>"
        match = re.findall(pattern, output, re.DOTALL)
        if match:
            return HelmInstructOutput(
                rating=float(match[0][0]),
                rationale=match[0][1].strip(),
            )
