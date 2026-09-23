# Note on this GitHub copy

This repository is a history-filtered mirror of the local research repository for the Adaptive Reflex Engine (23 pre-registered experiments, V0.1 to V1.10). Five sealed data files exceed GitHub's 100 MB per-file limit and were removed from history with git-filter-repo; everything else (code, results, reports, bug ledgers, bridge files, specs, tags) is intact. The local repository and the frozen per-version snapshots are unchanged and remain the reference copies.

## Files removed from history

They are attached, unmodified, to the GitHub Release `v1.10-final` (sha256 in `SHA256SUMS.txt` there). To restore, download and place each at its original path.

| Original path | Size | Used by |
| --- | --- | --- |
| results/v17/data/q1m_acq.jsonl | 200 MB | V1.7 acquisition split |
| results/v17/data/q1m_seal.jsonl | 300 MB | V1.7 sealed split |
| results/v17/data/q1m_replay.jsonl | 400 MB | V1.7 replay split |
| results/v18/data/devl.jsonl | 400 MB | V1.8 development split |
| results/v110/data/w400k_acq.jsonl | 103 MB | V1.10 acquisition split (its sha256 is also in results/v110/data/HASHES.json) |

## Commit hashes

Rewriting history changes commit ids. The reports and memory files cite the local hashes; this table maps each tag to its hash here.

| Tag | Local hash (cited in reports) | Hash in this repository |
| --- | --- | --- |
| v1.0-final | 932d339c | 932d339c |
| v1.0-parity | 49cc0f78 | 49cc0f78 |
| v1.1-final | 15dfd988 | 15dfd988 |
| v1.1-plan | 6cbe781d | 6cbe781d |
| v1.2-final | 80ba6c4e | 80ba6c4e |
| v1.2-plan | 36083d3a | 36083d3a |
| v1.3-final | f6cc4c06 | f6cc4c06 |
| v1.3-plan | 4e8b5071 | 4e8b5071 |
| v1.4-final | ad31ef2a | ad31ef2a |
| v1.4-plan | ff9759dc | ff9759dc |
| v1.5-final | 44c0b840 | 44c0b840 |
| v1.5-plan | 9e6abb88 | 9e6abb88 |
| v1.6-final | b72a344c | b72a344c |
| v1.6-plan | 36f3ee2f | 36f3ee2f |
| v1.7-final | 819115d5 | e884ccc6 |
| v1.7-plan | b87ff8f0 | b87ff8f0 |
| v1.8-final | 5c0393c0 | f9e8b25c |
| v1.8-plan | 09a29970 | b6058f30 |
| v1.9-final | dd412afe | e8705f92 |
| v1.9-plan | 209bba74 | c9c3aabe |
| v1.10-final | 94a5b7c9 | 2e606fd4 |
| v1.10-plan | 20731e39 | ebda949b |
| s1-final | d99a2218 | 7861d408 |
| s1-plan | 46d7d1a0 | 76480949 |

Tag names, tag messages, commit messages, authorship and dates are unchanged. The local `v1.10-final` commit is 94a5b7c9; the deliverable PDFs were committed after it as 5d026154 locally.

## Secrets

No credentials are tracked. The `.env` file holding the API key used by the bridge is gitignored, has never been committed, and is excluded from every snapshot.
