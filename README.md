# siliconbench

**Which local language model is actually useful as a study assistant on a 16 GB MacBook, in English and in Italian?**

I study Computer Engineering at Politecnico di Torino and Economics & Data Science at Università di Torino,
with lectures in English and an Italian language course. I wanted an assistant that runs offline on my laptop,
so I tested small open models on the kind of problems I actually solve for my exams.

## The test

The problems are generated with fresh random numbers from standard textbook formulas, so a model cannot have
memorised them, and every answer is checked automatically:

| Subject | Example | Checked by |
|---|---|---|
| Physics II | force between two charges, field of a point charge or an infinite plane | number within 2% |
| Macroeconomics | equilibrium output, spending and tax multipliers | number within 2% |
| Computer architecture | execution time from CPI and clock, binary → decimal, addressable memory | exact number |
| Math for economics | derivatives, compound interest, NPV | number within 0.5% |
| Italian grammar | passato prossimo, *ne*, plurals, comparatives (multiple choice) | letter |

**Every problem is asked twice, once in English and once in Italian, with the same numbers.** That gives a paired
measurement of how much a model loses when you study in Italian, with a bootstrap confidence interval.
Speed (tokens per second, time to first token) and memory are recorded on the same answers.

```text
python -m siliconbench show 2     # see what the questions look like
```

## Results

*Coming next: the run on my MacBook Pro M5 (16 GB) — `results/m5-16gb/REPORT.md`.*

The questions it answers:
1. Which model solves the most problems, and is the difference bigger than the noise?
2. How much worse is each model in Italian than in English?
3. Does an 8-bit version beat the default 4-bit version enough to be worth its memory and speed?
4. Which subject is hardest for small models: arithmetic-heavy physics, or multi-step economics?

## Run it on your Mac

```bash
# 1. install Ollama from https://ollama.com and start it
# 2. pull some models
ollama pull qwen2.5:3b && ollama pull llama3.2:3b
# 3. run (a few minutes per model)
pip install -r requirements.txt
python -m siliconbench run --models qwen2.5:3b llama3.2:3b --out results/my-mac
```

`REPORT.md`, `summary.csv`, `by_subject.csv` and two charts are written to the output folder. Any
OpenAI-compatible local server (llama.cpp, LM Studio, mlx_lm.server) also works with `--backend openai --host ...`.

## How it is built

```
siliconbench/tasks.py     problem generators (EN + IT), answer parser that understands 1,5 / 1.5 / 1.5×10^-3
siliconbench/backends.py  streaming clients for Ollama and OpenAI-compatible servers (standard library only)
siliconbench/run.py       asks every model every problem, saves raw answers
siliconbench/report.py    accuracy with Wilson intervals, paired EN−IT bootstrap, charts, REPORT.md
tests/                    end-to-end test against a fake local server
```

Temperature is 0 and the seed is fixed, so a run can be repeated.
