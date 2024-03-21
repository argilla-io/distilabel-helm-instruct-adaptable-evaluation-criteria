template = """{task_description}

Instruction:
{prompt}

Response:
{response}

{criterion_question}
Options:
{criterion_options}

Your answer must be in the following format:

<rating>[{min_score}-{max_score}]</rating>
<rationale>your rationale</rationale>

Please rate the Response: based on the Options: and provide a rationale for your rating."""
