# distilabel-helm-instruct-adaptable-evaluation-criteria

A repo that implements Stanford CRFM their HELM Instruct with adaptable evaluation criteria

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r helm_instruct/requirements.txt
```

## Run

```bash
python helm_instruct/main.py
```

## Create custom evaluation criteria

```python
from helm_instruct.evaluation_criteria import Rating,Criterion

criterion = {
    "childfriendliness"; Criterion(
        question="How child-friendly is the game?",
        ratings=[
            Rating(
                rating=1,
                description="Not child-friendly"
            ),
            Rating(
                rating=2,
                description="A bit child-friendly"
            ),
            Rating(
                rating=3,
                description="Child-friendly"
            ),
            Rating(
                rating=4,
                description="Very child-friendly"
            )
        ]
    )
}