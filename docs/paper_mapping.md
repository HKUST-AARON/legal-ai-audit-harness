# Paper-to-Harness Mapping

This repository implements the paper's evaluation framework as a runnable audit harness.

| Paper concept | Harness field |
| --- | --- |
| Output effect `E(o)` | `claimed_status` and the scenario description |
| System role `R(o)` | scenario metadata, optional deployment context |
| Audit vector `A(o)` | `scores.S`, `scores.Q`, `scores.H`, `scores.K`, `scores.T`, `scores.L` |
| Source and corpus verifiability | `S` |
| Query and version traceability | `Q` |
| Authority hierarchy | `H` |
| Ranking and counter-material verifiability | `K` |
| Contestability | `T` |
| Adoption logging and audit responsibility | `L` |
| Counter-authority recall | `counter_authority.known` and `counter_authority.retrieved` |
| Downgrade and withdrawal | `failure_flags` |

The harness is not a legal merits evaluator. It does not decide whether a legal answer is correct. It decides the highest procedural status that an output may claim given the audit artefacts available.
