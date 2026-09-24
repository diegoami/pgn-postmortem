# Review records

- **Naming:** `reviews/NNN-<slug>-impl-NN.md`. `NN` starts at `01` and
  increments per review round of the same implementation stage; the third round
  that does not end clean goes to the owner ([`PRINCIPLES.md`](../PRINCIPLES.md)).
- The verdict opens with **the revision it covers** (the commit sha), the file
  list the reviewer checked and how it was obtained (the pull request's files,
  or the local diff from the merge base), the reviewer's display name and model
  id, and the mode. Findings name files from that list; a mismatch or an empty
  list is a wrong target, not a finding.
- **Findings** are numbered, each marked `blocking` — it must be fixed before
  the change is approved — or `non-blocking`, each with `file:line` or a short
  quote as evidence.
- **The final lines** are:

  ```
  — <display name> (<model id with variant>), reviewer
  AGREE
  ```

  in OpenCode mode — the marker line contains only `AGREE` or only `BLOCK`. In
  Claude mode, replace the marker with one line stating whether any blocking
  finding remains; there is no marker and no design stage.
- **A comment, not an approval:** the verdict is written here and posted as the
  issue or pull-request comment when a remote exists; it is never an approval
  action. The file stays canonical.
- **Completion.** When the change lands, the implementer appends a
  `## Completion` section — the done-when items and the evidence that closed
  them — owned and signed by the implementer. In Claude mode, which has no
  design record, the note goes in the final implementation review file: the
  last round whose final line states that no blocking finding remains. The
  note's boundary and non-material status are in
  [`PRINCIPLES.md`](../PRINCIPLES.md).
- **The meaning of the verdict** — what it covers, materiality, fallback,
  waiver — is owned by [`PRINCIPLES.md`](../PRINCIPLES.md).
