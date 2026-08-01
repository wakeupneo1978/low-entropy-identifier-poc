# One hundred million is not entropy

[Español](README.md) · [Methodology](research/dossier.md) · [Ethical scope](ETHICS.md)

[![CI](https://github.com/wakeupneo1978/low-entropy-identifier-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/wakeupneo1978/low-entropy-identifier-poc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Synthetic data only](https://img.shields.io/badge/data-100%25%20synthetic-22c55e)](ETHICS.md)

A reproducible laboratory showing why deterministic SHA-256 without a separate
secret provides little protection for identifiers drawn from a small domain.
The Spanish DNI/NIF is the case study: eight digits plus a deterministic check
letter produce 100,000,000 syntactic candidates, approximately 26.58 bits.

> **This repository uses synthetic identities only.** It contains no
> identifiers sourced from real people, personal data, breach material or
> precomputed lookup tables. It
> must not be used to process third-party information.

SHA-256 is not broken. The issue is that an attacker who can enumerate every
possible input can calculate the corresponding digests and compare them with
extracted values. A 256-bit output does not turn a predictable input into a
256-bit secret.

![Cover: One hundred million is not entropy](research/portada_linkedin_cien_millones_entropia.jpg)

## Reproduced result

The PoC creates seven synthetic tables and demonstrates three independent
attribution paths: hash enumeration, linkage through a stable key and reversal
of weak obfuscation. The recorded baseline recovered all 12 synthetic targets
and reconstructed 12 profiles without consistency failures.

| Recorded baseline | Result | Time |
| --- | ---: | ---: |
| One target, full domain | 1/1 recovered | 32.92 s |
| Twelve targets and cross-table reconstruction | 12/12 recovered | 35.90 s |
| One target with a known global salt | 1/1 recovered | 36.54 s |

These measurements were recorded on Linux x86_64 with nine logical threads and
are not universal performance claims. Exact environment and methodology data
are included in [`results/`](results/README.md).

## Quick reproduction

Requirements: Python 3.11+, GCC or Clang, `make`, OpenSSL 3 development headers
and POSIX threads.

```bash
git clone https://github.com/wakeupneo1978/low-entropy-identifier-poc.git
cd low-entropy-identifier-poc
make clean test
python3 src/generate_lab.py --output lab/synthetic_identity.db
python3 src/run_reconstruction.py \
  --database lab/synthetic_identity.db \
  --cracker build/dni_sha256_enum \
  --output results/reconstruction_local.json \
  --limit 100000000
```

Use `--limit 1000000` for a quick smoke test. It is not a full-domain result.

For macOS, install the native dependencies and expose Homebrew's OpenSSL
metadata before building:

```bash
xcode-select --install
brew install openssl@3 pkg-config python@3.12
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"
```

The visual Jupyter workflow and publication-ready figures are in
[`notebooks/Fulcrum_DNI_PoC_Mac.ipynb`](notebooks/Fulcrum_DNI_PoC_Mac.ipynb).
The accompanying [macOS guide](notebooks/GUIA_MAC_JUPYTER.md) is in Spanish.

## Experimental model

The deterministic generator creates 12 identities labelled
`PERSONA_SINTETICA_001`, email addresses under the reserved `.invalid` domain
and manifestly fictitious financial surrogates. The seven tables model
plaintext staging, a stable linkage key, unsalted hashes, weak substitution,
password KDF records and defensive alternatives.

The canonical input is the full NIF:

```text
00000000T
00000001R
...
99999999R
```

Non-issued values would reduce the real candidate set, never increase it. This
PoC models the syntactic space and makes no claim about the administrative
registry of issued documents. A generated string could accidentally match an
issued identifier, but it was not sourced from a person and is not linked to
real attributes.

## Defensive interpretation

| Design | Effect after database extraction |
| --- | --- |
| `SHA256(DNI)` | One pass can test every target sharing the same normalization and transform. |
| Known global salt | Requires a new pass for that salt, but the pass remains shareable across rows. |
| Stored per-row salt | Prevents amortising one mass pass; does not prevent a targeted per-record search. |
| HMAC with a separated key | Candidates cannot be validated without the key. Key custody and context separation are critical. |
| Random token and separated mapping | Removes the mathematical relation to enumerate; the mapping becomes the critical asset. |

## Limits and responsible use

- This laboratory demonstrates technical recoverability in a defined model; it
  does not determine an organisation's legal compliance by itself.
- Cross-dataset linkage depends on matching normalization, transformation, key
  or context.
- FulcrumSec actor statements, GRIT's published assessment and this project's
  independent results are kept distinct.
- Regulatory analysis is informational and requires legal review for any
  specific case.

Read [`ETHICS.md`](ETHICS.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`SECURITY.md`](SECURITY.md) before using or modifying the project. Citation
metadata is provided in [`CITATION.cff`](CITATION.cff). The code is licensed
under the [MIT License](LICENSE).
