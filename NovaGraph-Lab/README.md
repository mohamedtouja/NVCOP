NovaGraph-Lab
==============

Purpose
-------
NovaGraph-Lab is the research and prototyping workspace for NovaGraph. Use this
Python-first repository to explore new mathematical compression engines, run
benchmarks, and prototype ML-driven routing strategies.

Goals
-----
- Fast iteration and readability
- Reproducible benchmarks and datasets
- Machine-learning experiments (offline; not used for decompression)
- Reference implementations of engines that may later be ported to Rust

Getting started
---------------
- Create a virtualenv or use `pyproject.toml` / `poetry`.
- Implement engines under `lab_engines/` as pure Python modules.
- Add benchmarks under `benchmarks/` and use `bench_runner.py` to produce
  JSON/CSV/MD reports.

Master Prompt
-------------
Include the full master prompt (architectural specification) in `PROMPT.md` for
use by research assistants and automated agents.
