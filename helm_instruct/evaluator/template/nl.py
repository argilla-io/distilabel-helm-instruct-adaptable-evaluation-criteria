template = """{task_description}

Instructie:
{prompt}

Reactie:
{response}

{criterion_question}
Opties:
{criterion_options}

Je antwoord moet in het volgende formaat zijn:

<score>[{min_score}-{max_score}]</score>
<reden>je reden</reden>

Beoordeel alstublieft de Reactie: op basis van de Opties: en geef een reden voor je beoordeling."""
