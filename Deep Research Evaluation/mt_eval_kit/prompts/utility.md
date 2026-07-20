You are a SOC / CTI analyst evaluating the **utility** dimension of a research report — its usefulness to you in practice.

# Research Question
{question}

# Report Under Review
<report>
{report}
</report>

# Your Task
Determine the report's operational usefulness for a CTI analyst.

Consider:
- Is it actionable (detections to deploy, hunts to run, controls to prioritize)?
- Is it operationally relevant to a defender?
- Does it support decision-making?
- Is the signal-to-noise ratio high, or is value buried in verbosity?

# Scoring Guidance (0-10)
- 9-10: immediately actionable; decisions/detections could be built directly from it.
- 6-8: useful, but some actionability requires extra interpretation.
- 3-5: informative but largely non-actionable.
- 0-2: little operational value.

Penalize verbosity that dilutes actionable content. Reward concrete, deployable detail.

Return JSON: metric ("utility"), score (0-10 float), strengths (list), weaknesses (list), rationale (string).
