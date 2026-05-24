# Thinking for Theorizing

**Code and data for the manuscript:**
*Thinking for Theorizing: How the Definitional Copular Frame Channels Processual Concepts into Entity-Search Reasoning*

This repository contains the analysis scripts, data, and reproducibility materials for the cross-linguistic corpus analysis (Study 1) and the distributional-semantic embedding analysis (Study 2) reported in the paper.

---

## Overview

The paper investigates the hypothesis that the definitional copular frame *"What is X?"* — the canonical question form of much Western philosophical inquiry — functions as a **grammatical funnel** that channels processual concepts into nominalized, entity-like forms. Two studies provide converging evidence:

- **Study 1** — A cross-linguistic analysis of 15 Universal Dependencies treebanks (~3.2 million tokens, five language families) cross-referenced with WALS copula typology data, showing that languages with shared nominal-locational predication and high copular versatility exhibit substantially higher rates of noun-subject copular constructions (HIGH/LOW constraint ratio ≈ 2.63×). The effect is structural rather than genealogical: Indo-European versus non-Indo-European languages show no difference in copula rate (ratio ≈ 1.00).

- **Study 2** — A distributional-semantic analysis using hypothesis-free stimuli and two independent embedding models (OpenAI `text-embedding-3-large` and Google `gemini-embedding-001`), cross-validated across three independent anchor pole formulations. Across all eight grammatical forms tested, invisible-process concepts (*love*, *consciousness*, *truth*, ...) occupy more entity-oriented distributional positions than visible-process concepts (*running*, *swimming*, ...). The visible/invisible classification is independently validated against Brysbaert et al.'s (2014) concreteness ratings.

The framework is *not* a claim of grammatical determinism. It is a co-evolutionary account in which grammatical affordances, the institutional objective of definition, the social requirements of communal discourse, and the observational invisibility of certain processes jointly stabilize entity-search reasoning as the default mode of theoretical inquiry into invisible concepts.

---

## Repository structure

```
thinking_for_theorizing/
├── README.md                          # This file
├── src/                                # Analysis scripts
│   ├── study1_corpus_analysis.py       # UD treebank analysis (Study 1)
│   ├── study2_revision.py              # OpenAI embedding analysis (Study 2)
│   ├── study2_revision_gemini.py       # Gemini embedding analysis (Study 2 cross-model)
│   ├── phase_b_bootstrap.py            # Bootstrap CIs, Cohen's d, Mann–Whitney, regression
│   ├── additional_stats.py             # Effect size analyses (HIGH vs LOW)
│   └── generate_figures.py             # Generate all paper figures from data
└── Result/                             # Output files
    ├── study1_results.json              # Per-language UD analysis results
    ├── study2_revised_results.json      # OpenAI embedding results (126 stimuli)
    ├── study2_revised_results_gemini.json  # Gemini embedding results
    ├── brysbaert_results.json           # Brysbaert concreteness validation
    └── figures/                         # Generated figures (PDF + PNG)
```

---

## Reproducing the analyses

### Requirements

- Python 3.11+
- `numpy`, `scipy`, `matplotlib`
- `openai` (for OpenAI embedding analysis)
- `google-generativeai` (for Gemini embedding analysis)
- `python-dotenv` (for loading API credentials from `.env`)
- TeX Live with `xelatex` (for compiling the paper itself)

```bash
pip install numpy scipy matplotlib openai google-generativeai python-dotenv
```

### API credentials

Create a `.env` file in the working directory with:

```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

The scripts will load credentials automatically; **no keys are hard-coded**.

### Reproducing Study 1

Study 1 requires Universal Dependencies v2 treebanks. Download from <https://universaldependencies.org/> for the 15 languages listed in §3.1.2 of the paper.

```bash
cd src/
python study1_corpus_analysis.py
```

This produces `study1_results.json` with per-language copula frequencies, head distributions, and Shannon entropy of copula heads.

### Reproducing Study 2

```bash
# OpenAI variant
python study2_revision.py

# Gemini variant (for cross-model robustness)
python study2_revision_gemini.py
```

Each script embeds 126 stimuli across 3 anchor pole sets (essence vs. activity, object vs. event, definition vs. change) and writes per-stimulus E-P gap values to JSON.

**Runtime**: ~5–10 minutes per model. Cost: <\$1 in API calls.

### Reproducing statistics

```bash
python phase_b_bootstrap.py      # Bootstrap CIs, Cohen's d, regression
python additional_stats.py        # HIGH vs LOW constraint analysis
```

### Generating figures

```bash
python generate_figures.py
```

Outputs five figures to `figures/` in both PDF and PNG formats.

---

## Data sources

| Resource | Source | Citation |
|---|---|---|
| Universal Dependencies treebanks | <https://universaldependencies.org/> | Nivre et al. (2020) |
| WALS typology data | <https://wals.info/> | Dryer & Haspelmath (2013) |
| Brysbaert concreteness ratings | Springer supplementary materials | Brysbaert, Warriner, & Kuperman (2014) |
| OpenAI embedding model | `text-embedding-3-large` (3,072 dim) | Commercial API |
| Google Gemini embedding model | `gemini-embedding-001` (3,072 dim) | Commercial API |

---

## Key results

| Comparison | Effect size | Status |
|---|---|---|
| WALS 119A Shared vs Split (CopSubj rate) | Cohen's *d* = 0.82 | Predicted direction |
| WALS 120A Required vs Zero OK (cop rate) | Cohen's *d* = 1.17 | Predicted direction |
| HIGH vs LOW constraint composite | Ratio = 2.63× | Predicted direction |
| **IE vs Non-IE control** | **Cohen's *d* = −0.03** | **Family is not a confound** |
| Brysbaert concreteness (visible vs invisible) | Cohen's *d* = 5.08 | Visibility classification validated |
| Cross-model agreement (OpenAI vs Gemini) | 8/8 forms same direction | Robust interaction |
| Pearson r between models | 0.73 | Substantial agreement on relative magnitudes |

---

## Citation

If you use this code or data, please cite:

```bibtex
@unpublished{iizumi2026thinking,
  author = {Iizumi, Masamichi},
  title = {Thinking for Theorizing: How the Definitional Copular Frame
           Channels Processual Concepts into Entity-Search Reasoning},
  year = {2026},
  note = {Manuscript under review}
}
```

Citation will be updated upon publication.

---

## Random seed

All bootstrap and permutation analyses use **random seed = 42** for reproducibility.

---

## License

Code is released under the MIT License. See `LICENSE` for details.

Data files derived from third-party sources (UD treebanks, WALS, Brysbaert ratings) retain their respective licenses; please consult the original sources.

---

## Contact

For questions about the code or to report issues, please open an issue on GitHub or contact the corresponding author.

**Repository**: <https://github.com/miosync-masa/thinking_for_theorizing>
