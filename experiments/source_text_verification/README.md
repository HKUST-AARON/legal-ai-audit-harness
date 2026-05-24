# Public source text anchor verification

This layer checks whether issue-manifest support items have anchors in public source text snapshots.

It is not a merits review and does not decide whether a legal proposition is doctrinally correct. It adds an external source-grounding check to the source-supported model-output repairs by testing whether support terms from the manifest can be located in public case, statute, regulation or court-material text where that text is accessible.

Run:

```bash
python scripts/verify_source_text_anchors.py
```

Refresh public snapshots:

```bash
python scripts/verify_source_text_anchors.py --refresh
```

Outputs:

- `snapshots/`: extracted public source text and metadata hashes.
- `results/source_text_anchor_verification.json`
- `results/source_text_anchor_verification.md`
