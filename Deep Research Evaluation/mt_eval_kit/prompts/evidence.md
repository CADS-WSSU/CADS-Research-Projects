You are a senior cyber threat intelligence analyst evaluating the **evidence_support** dimension of a research report. The report was produced by an LLM operating inside a fixed research framework; judge the report on its merits.

# Research Question
{question}

# Report Under Review
<report>
{report}
</report>

# Your Task
Assess whether the report's findings appear **supported by evidence and reasoning** presented within the report. There is no gold answer — judge only what is in front of you.

Consider:
- Are conclusions traceable to stated sources, observations, or reasoning?
- Are citations/references actually connected to the claims they support?
- Does the reasoning from evidence to conclusion hold up, or are there unsupported leaps?

# Scoring Guidance (0-10)
- 9-10: nearly every consequential claim is supported by cited evidence or sound reasoning.
- 6-8: most claims supported; a few under-evidenced assertions.
- 3-5: several important conclusions lack visible support.
- 0-2: largely unsupported assertions; evidence does not connect to claims.

Penalize fabricated-looking specifics presented without basis. Reward explicit attribution and transparent reasoning.

Return JSON: metric ("evidence_support"), score (0-10 float), strengths (list), weaknesses (list), rationale (string).
