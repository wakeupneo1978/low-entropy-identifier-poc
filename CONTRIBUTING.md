# Contributing

Contributions that improve portability, reproducibility, documentation,
testing or defensive analysis are welcome.

Before opening a pull request:

1. Use only synthetic test data.
2. Do not add breach material, real identifiers or target lists.
3. Run `make clean test` on a supported platform.
4. Keep benchmark claims tied to exact hardware, software, candidate format,
   target count and thread count.
5. Explain whether a claim is measured, sourced or inferred.

The maintainers will reject features whose main purpose is ingesting arbitrary
third-party datasets, generating reusable lookup tables or identifying real
people.
