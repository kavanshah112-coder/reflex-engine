POST-SEAL AGENT OUTPUT — DELIBERATELY NOT INGESTED

A servicing agent from the W6 round finished after the haiku arm was
sealed, tagged (v1.3-final), snapshotted, and reported. Of the 112 rows
in these files, 97 were already ingested before the seal and are
reflected in the published numbers; 15 were not.

Those 15 are NOT ingested, and the directory is renamed so that
`service_bridge13.py ingest` cannot pick them up by accident.

Reason, in order of importance:

1. The convergence rule was declared BEFORE the numbers were read: each
   arm gets bounded servicing rounds, and whatever is unresolved is
   scored as an ABSTENTION. Servicing until a number improves has no
   fixed point -- every retry mints new retry prompts -- which is
   exactly why the rule exists.

2. These rows would most likely RAISE haiku's coverage, and haiku's
   1/38 = 2.63% is the single measurement that set OUTCOME D. Ingesting
   late-arriving work after seeing which measurement decided the verdict
   is the worst available version of tuning on the evaluation.

3. `run_v1_3_experiment.py` replays the arms from the frozen response
   cache. Ingesting these would make the replay disagree with the
   published report, silently.

If a future version wants this work, it belongs in V1.4 as a fresh,
pre-registered run -- not as an amendment to a sealed one.
