# Graph reliability and identity sensitivity

Task2C reread all three bound graph files. Researcher networks include every
Researcher node, including isolates, and accepted `COAUTHORED_WITH` pairs. Degree
counts neighbors; strength sums positive fractional coauthorship weights. Cached
paired betweenness uses the **same 256 common pivots**, inverse positive fractional
weights as distances, and the same historical computation/seed. Candidate degree
and strength caches were independently reconciled to graph-derived values before
using cached betweenness. This reruns topology censuses, not the expensive shortest
paths, and makes no claim to reproduce the original production ranking definition.

| Census | Frozen v4 | Candidate-v3 | Task2B |
| --- | ---: | ---: | ---: |
| Researcher nodes | 32,189 | 32,023 | 32,077 |
| Coauthor pairs | 80,482 | 78,694 | 79,389 |
| Components | 2,936 | 3,069 | 3,032 |
| Isolates | 414 | 452 | 440 |
| Largest-component share | 64.54% | 63.05% | 63.64% |
| Organization collaboration pairs | 13,031 | 12,797 | 12,843 |
| Researcher-topic aggregates | 5,622 | 5,477 | 5,528 |
| Organization-topic aggregates | 2,332 | 2,322 | 2,323 |

Full component-size distributions, relation-support changes, IDs, names and scores
are in `analysis/graph-sensitivity.json` (see README for retained artifact location).
Publication, citation, taxonomy and paper-topic inventories retain their counts;
no model or topic classification was changed.

## Stable and unstable conclusions

| Comparison | Degree top-20 overlap | Strength top-20 overlap | Betweenness top-20 overlap |
| --- | ---: | ---: | ---: |
| v3 / Task2B | 19/20 | 17/20 | 18/20 |
| v3 / frozen v4 | 19/20 | 16/20 | 11/20 |
| Task2B / frozen v4 | 20/20 | 19/20 | 12/20 |

Over common researchers, Spearman correlations for v3/Task2B are .998270, .995693,
.995383 respectively. For v3/v4 they are .995440, .985461, .989650; for Task2B/v4
.996763, .988938, .993427. High whole-population correlations coexist with substantial
movement at the top of bridge rankings. There are many low-degree nodes and ties;
correlation does not imply stable influence case studies or semantic correctness.

Examples using stable IDs: Lei Feng (`A5100682348`) is betweenness rank 2 in the
paired v4 analysis versus 55 in Task2B; Hau Chan (`A5046420136`) is rank 4 versus
176; Chen Chen (`A5100418485`) is rank 159 versus 19. These observations describe
sensitivity of the current approximate network metric, not proven rank changes
among real disambiguated people. Their own accepted positions need not change:
a shortest path elsewhere can alter an otherwise unchanged researcher's ranking.
Shu-Tao Xia (`A5034104790`) also has directly changed identity support. The machine
report flags direct-support changes separately from network-mediated effects.

Task2B versus v3 adds 695 coauthor pairs and changes support/weight on 3 retained
pairs. It adds 46 organization collaboration pairs and changes support on 129;
adds 51 researcher-topic aggregates and changes 1; adds 1 organization-topic
aggregate and changes 44. More derived support is scientifically justified only
if the newly accepted underlying author identity and paper-specific affiliation
are correct. Same-person dual affiliation cannot independently establish organization
collaboration; the existing distinct-author rule was preserved.

## Shared-assignment sensitivity scenario

Across all three checkpoints, **738** positions on **675** papers differ, involving
**223** accepted researcher IDs. These are policy disagreements, not measured errors.
Remove every differing position and retain only identical assignments shared by all
three: **49,732 positions**, **32,015 researchers**, **78,676 coauthor pairs**,
**3,069 components**, **452 isolates**. Nodes are researchers with a remaining
accepted authorship; this denominator differs from simply deleting edges while
retaining all original nodes. This conservative intersection is a diagnostic
scenario, not a proposed fourth candidate or independently verified core. Unchanged
assignments can still contain false merges, and uncertain identities elsewhere
can remain shared by all policies.

The existence of a large connected component and broad degree ordering is relatively
stable under these candidate policies. Exact bridge rankings, boundary component
membership, organization collaboration support and thresholded researcher-topic
profiles need identity uncertainty caveats. Do not infer that a larger component,
fewer isolates, stronger cross-organization connection or a recovered bridge is an
improvement without semantic evidence. No organization/topic repair, Explorer
redesign, database import or production write was performed.
