# Evidence and ROI — what may and may not be claimed

One contested number discounts every other number you have given them. This
document exists so that does not happen.

The rule underneath all of it: **present a range with assumptions visible,
never a guarantee.** Write the assumptions on the same page as the number. A
sponsor who later finds an assumption buried will re-read every figure you
ever gave them, and they will be right to.

---

## Claims and the minimum evidence for each

| Claim | Minimum evidence | Common way it goes wrong |
|---|---|---|
| **Time saved** | Frozen baseline; **net** time including human verification; at least 10 instances; same task; same staff | Measuring drafting time only, while review time silently doubles |
| **Quality improved** | Error definition agreed *before* measuring; blind review by someone who is not you | Defining "error" after seeing the results |
| **Financial ROI** | Only levers the client already measures | Modelling a lever whose measurement you introduced — you are then reporting on your own instrument |
| **Risk reduced** | A specific prior exposure, now closed, with the evidence | "More governance" is not a measurement |

## Never a success metric

- Number of runs, tokens, or agent actions. Activity is not outcome.
- Volume of output produced.
- Staff enthusiasm in month one. It is real and it is not durable.
- A clean gate suite. That proves the system behaves as specified, which is a
  prerequisite for value, not evidence of it.

---

## The measurement this kit produces that others do not

**Correction burden over time.**

Every run leaves a trace. Failing runs cluster by failure mode. Over weeks,
the rate at which a human has to correct or reject output is a curve drawn
from data you were logging anyway — not from a survey and not from a recalled
estimate.

It is the strongest evidence available here, for three reasons:

1. It is **observed, not modelled.** No assumptions to bury.
2. The client can **watch it fall**, which is more persuasive than any figure
   you present at a readout.
3. It is **falsifiable**, which is precisely why it is credible. If the curve
   is flat, the honest report is that it is flat.

Present the curve. Do not present a projection of the curve.

---

## The net-time trap, in detail

The arithmetic that actually matters:

```
net time = drafting time + verification time + exception handling time
```

Most AI time-savings claims measure the first term and ignore the other two.
For a reporting workflow the second term is where the time goes, because a
figure you cannot trust costs more to check than to have written yourself.

This is why every figure in a drafted report cites its source inline. It is
not a transparency gesture — **it is the intervention that makes verification
cheap enough for the net number to come out positive.** If you strip the
citations, the time saving disappears and the claim with it.

---

## What the kit cannot tell you

State these plainly, in the deliverable, not in a footnote:

- **Whether a figure is right.** It verifies that a number traces to the
  source claiming it. A wrong number in a correct source passes every gate.
- **Whether the source is any good.** It reports staleness and unconfirmed
  ownership. It cannot assess whether the collection method is sound.
- **Anything about a regulatory position.** Grant terms and jurisdiction are
  specific. Read the actual agreement or ask counsel.
- **Whether the organization will keep using it.** That depends on a named
  internal owner still being there in ninety days, which is a management
  question and not a technical one.

---

## Writing the readout

Lead with the finding, not the method. In order:

1. **What we found** — usually a data or ownership problem, and usually the
   most valuable part.
2. **What changed** — the net-time number, with its assumptions on the page.
3. **What is still open** — dispositioned: fixed, deferred with a date and an
   owner, or accepted by a named human.
4. **What would break it** — the dependencies, and what happens when the
   named owner leaves.

Item 4 is the one people omit, and it is the one that determines whether
anything survives to month four.
