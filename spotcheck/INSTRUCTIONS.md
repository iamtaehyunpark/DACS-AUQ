# Spot check — instructions

150 agent steps, blinded. For each, answer ONE question:

> Given only the information the agent had **at that moment** — the task, the
> history so far, and the action it proposed — was proposing this action a
> **reasonable decision**?

Write `ok` or `bad` in `annotator_verdict`. Use `annotator_note` for anything
you found ambiguous.

**This is an ex-ante judgement, not hindsight.** An action that was sensible to
try and happened not to work is `ok`. That distinction is the entire point of
the exercise: it is where the label families disagree, and your answer is what
decides which one matches human judgement on the contested band.

You are not being asked whether the step made progress, and you cannot see
whether it did.

Do not open `key.json` before finishing. It holds the labels, including 20
calibration controls whose answer is not in dispute.

Return `sheet.csv` with the verdict column filled. Agreement per construct is
computed on return.
