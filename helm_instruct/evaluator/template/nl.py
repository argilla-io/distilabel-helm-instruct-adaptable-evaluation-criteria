template = """{task_description}

Instructie:
{prompt}

Reactie:
{response}

{criterion_question}
Opties:
{criterion_options}

Je antwoord moet in het volgende formaat zijn:

<rating>[{min_score}-{max_score}]</rating>

Beoordeel alstublieft de Reactie: met een rating op basis van de Opties:."""
