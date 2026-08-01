# Recorded baseline results

The committed JSON files are release evidence, not universal performance
claims. They were produced on the environment recorded inside each file using
entirely synthetic targets.

- `benchmark.json` records one short pass, one complete unsalted pass and one
  complete pass with a known global salt.
- `reconstruction.json` records recovery of 12 synthetic hashes and the
  subsequent joins across seven synthetic tables.
- `validation.json` records package, notebook and test validation.
- `manifest.sha256` binds the release documentation, code and baseline results.

Machine-specific notebook runs are intentionally ignored by Git. Publish such
results only when the hardware, operating system, compiler, OpenSSL version,
thread count and exact source revision are included.
