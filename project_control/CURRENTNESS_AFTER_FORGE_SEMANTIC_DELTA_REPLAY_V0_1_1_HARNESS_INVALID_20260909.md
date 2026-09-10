# Control Currentness — Forge Semantic Delta Replay v0.1.1 HARNESS_INVALID — 2026-09-09

Status: **FORGE CORE HARNESS BOUNDARY / NOT ADMITTED**
Predecessor control `59edf0de14ebcb688c037611f72cba992ac51b4e` / CHECKPOINT `f3bb263e862db2aad798f7ca8df60d1a54f4987a54d23eb4b29ca50d13ce460d`.

v0.1.1 module `9a74bd3ec787c7ccf1e4d393b9d8ccba582d7635b0a323205a183dcaf6520315` and harness `765d45dccefa19111ede100a97242c7980c617cf114782b852ee106ff733cb79` executed once. Plan construction and operation application succeeded, but replay copied frozen MappingProxy-backed objects into a mutable SemanticFactBundle; freeze verification then failed in incumbent `asdict()`. Exact result `fbb81733340c955ab1157cc016ae4a21beb2c3ffa9d6f5b1858c58ccdba0da05`; exact local stderr hash `dde3af2d41dda0eabeca7d614d3f59023098d1ff99c8076e5a8c3197f36f5eb2`. PyGoat remained clean at `19d17cc8874861142b330636d068bbde54e86b85`.

No semantic replay claim admitted. Same v0.1.1 attempt non-replayable. NEW v0.1.2 may repair only mutable-workspace thawing of frozen nested values.
