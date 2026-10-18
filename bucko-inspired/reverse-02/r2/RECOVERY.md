# REVERSE 02 R2 - recovery, 2026-10-18

The previous REVERSE02 working directory and undelivered results were absent after session restoration. Only the preregistered protocol was recovered from GitHub (commit 9de25335c3ad15f24ee091eed9c32162b2755143). REVERSE01, its embedded RECON04 data and causal signal traces were intact. This is a new, explicitly versioned implementation of that protocol. It does not modify the prior source or signal definitions. Earlier conversational results are not accepted as evidence or targeted during implementation. All delivered statistics will be recomputed and distinguished from those unrecoverable results.

Recovered protocol refinements made explicit before this rerun: source trace days include zero-signal days; new accounts exclude first and last partial sessions. Candidate marks use conservative adverse excursion until actual exit (open exits do not use that bar's later H/L); a gap across a session/curfew or contract end is data unresolved. Funded risk remains capped at USD200. Chronological and resampled paths use the same state machine. No alternative parameter selection is introduced.

The requested next-open execution uses that observable open to establish the bracket, without using its high/low/close. S-family reproduces the inherited slipped-entry target formula. M-family uses original structural stop distance from the common next-open reference. Neither implies a bracket price known before observing the next open.

Bootstrap sampling uses complete sessions only (excluding the first and last observed partial sessions); source warmup and chronological end observations are retained. This boundary restriction was set before R2 economic review.
