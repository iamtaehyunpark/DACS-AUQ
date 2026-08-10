#!/usr/bin/env python3
"""Answer-distribution tripwire — mandatory on every scoring pass.

Adopted as A35 after the S4 void: 44,573 hindsight records were written with
`route=main`, zero errors, and a clean-looking coverage table, while the top-1 token
was `The` on every single one.  The judge was continuing the agent's ReAct completion
instead of answering, because the prompt had been appended after a CLOSED chat
template.  Nothing downstream could see it: the requests succeeded, the files were
the right size, and U was non-null often enough to look like data.

The check that would have caught it in the first 100 records is trivial: a probe
answering a Yes/No question does not emit the same non-answer token 100% of the time.

Usage:

    tw = Tripwire("alfworld/Qwen3.5-4B")
    ...
    tw.observe(top_logprobs_list)      # per record; raises on the 100th if degenerate
    ...
    tw.report()                        # optional, for the run log

`observe` is cheap and does nothing after the window closes.
"""

WINDOW = 100          # records inspected
MAX_SHARE = 0.95      # any single top-1 token above this share -> abort
EXPECT = {"yes", "no"}   # a Yes/No probe should live in here


class TripwireError(RuntimeError):
    pass


class Tripwire(object):
    __slots__ = ("label", "n", "counts", "closed", "expect")

    def __init__(self, label, expect=EXPECT):
        self.label = label
        self.n = 0
        self.counts = {}
        self.closed = False
        self.expect = {e.lower() for e in expect} if expect else None

    def observe(self, top):
        """top = [{"token":..., "logprob":...}, ...] for ONE record."""
        if self.closed:
            return
        if not top:
            return
        best = max(top, key=lambda t: t["logprob"])
        tok = (best.get("token") or "").strip()
        self.counts[tok] = self.counts.get(tok, 0) + 1
        self.n += 1
        if self.n >= WINDOW:
            self.closed = True
            self._assert()

    def _assert(self):
        if not self.n:
            return
        tok, c = max(self.counts.items(), key=lambda kv: kv[1])
        share = c / float(self.n)
        if share > MAX_SHARE:
            in_expect = tok.lower() in self.expect if self.expect else True
            raise TripwireError(
                "ANSWER-DISTRIBUTION TRIPWIRE [%s]: top-1 token %r is %.0f%% of the "
                "first %d records (limit %.0f%%)%s.\n"
                "This is the S4 failure signature: the model is emitting one token "
                "regardless of input, which means it is not answering the question. "
                "Do NOT treat these records as data. Check that the prompt is a real "
                "user turn and not text appended after a closed chat template."
                % (self.label, tok, 100 * share, self.n, 100 * MAX_SHARE,
                   "" if in_expect else " and it is not a Yes/No answer"))

    def report(self):
        if not self.n:
            return "%s: tripwire saw no records" % self.label
        top = sorted(self.counts.items(), key=lambda kv: -kv[1])[:4]
        return ("%s: tripwire OK over %d records, top-1 distribution %s"
                % (self.label, self.n, dict(top)))
