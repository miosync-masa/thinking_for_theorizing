#!/usr/bin/env python3
"""
Study 2 Revision — Gemini variant (Phase C continued)

Same design as study2_revision.py but using Google Gemini embeddings.
This enables cross-model robustness analysis: do BOTH OpenAI and Gemini
show the same visibility × form interaction across multiple anchor sets?

USAGE on Boss's Mac:
  cd /Users/iizumimasamichi/tft
  source env/bin/activate
  pip install google-generativeai python-dotenv numpy  # if not already installed
  python study2_revision_gemini.py

  Auto-loads .env from cwd or parents. Expected:
    GEMINI_API_KEY=...
    (or GOOGLE_API_KEY=...)

OUTPUT:
  study2_revised_results_gemini.json
  study2_revised_summary_gemini.txt
"""

import os
import json
import time
import sys
import numpy as np
from typing import List, Dict

# ============================================================
# Load .env
# ============================================================
try:
    from dotenv import load_dotenv
    from pathlib import Path
    cwd = Path.cwd()
    for path in [cwd] + list(cwd.parents):
        env_file = path / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✓ Loaded .env from: {env_file}")
            break
except ImportError:
    print("ℹ️ python-dotenv not installed.")

import google.generativeai as genai

# ============================================================
# Configuration
# ============================================================
# Use gemini-embedding-001 if available (3072 dim, matches OpenAI for fair comparison)
# Fallback to text-embedding-004 (768 dim) if 001 not available
EMBEDDING_MODELS_TO_TRY = [
    "models/gemini-embedding-001",
    "models/text-embedding-004",
    "models/embedding-001",
]
OUTPUT_FILE = "study2_revised_results_gemini.json"
SUMMARY_FILE = "study2_revised_summary_gemini.txt"

# ============================================================
# Stimuli — same as OpenAI version for direct comparison
# ============================================================

CONCEPTS = {
    "invisible": ["love", "consciousness", "truth", "beauty", "justice", "freedom"],
    "visible": ["running", "swimming", "dancing", "eating", "walking", "cooking"],
}

def build_stimuli(concept: str, visibility_class: str) -> Dict[str, List[str]]:
    """Build six grammatical forms × multiple templates for one concept."""
    if visibility_class == "invisible":
        if concept == "love":
            verb, ing_form, agentive, bare_noun = "love", "loving", "a lover of music", "love"
        elif concept == "consciousness":
            verb, ing_form, agentive, bare_noun = "be conscious of something", "being conscious", "(no agentive)", "consciousness"
        elif concept == "truth":
            verb, ing_form, agentive, bare_noun = "tell the truth", "being truthful", "(no agentive)", "truth"
        elif concept == "beauty":
            verb, ing_form, agentive, bare_noun = "be beautiful", "being beautiful", "(no agentive)", "beauty"
        elif concept == "justice":
            verb, ing_form, agentive, bare_noun = "act justly", "acting justly", "(no agentive)", "justice"
        elif concept == "freedom":
            verb, ing_form, agentive, bare_noun = "be free", "being free", "(no agentive)", "freedom"
        else:
            raise ValueError(f"Unknown invisible concept: {concept}")
    else:
        if concept == "running":
            verb, ing_form, agentive, bare_noun = "run", "running", "a runner", "running"
        elif concept == "swimming":
            verb, ing_form, agentive, bare_noun = "swim", "swimming", "a swimmer", "swimming"
        elif concept == "dancing":
            verb, ing_form, agentive, bare_noun = "dance", "dancing", "a dancer", "dancing"
        elif concept == "eating":
            verb, ing_form, agentive, bare_noun = "eat", "eating", "(no agentive)", "eating"
        elif concept == "walking":
            verb, ing_form, agentive, bare_noun = "walk", "walking", "a walker", "walking"
        elif concept == "cooking":
            verb, ing_form, agentive, bare_noun = "cook", "cooking", "a cook", "cooking"
        else:
            raise ValueError(f"Unknown visible concept: {concept}")

    stimuli = {
        "verb": [
            f"to {verb}",
            f"people {ing_form}" if concept in ("love",) else f"someone {ing_form}",
        ],
        "progressive": [
            f"{ing_form}",
            f"{ing_form} something" if concept == "love" else f"{ing_form} naturally",
        ],
        "agentive": [agentive] if "no agentive" not in agentive else [],
        "noun_minimal": [bare_noun],
        "noun_with_word": [f"the word {bare_noun}"],
        "noun_with_feeling": [f"the feeling of {bare_noun}"] if visibility_class == "invisible" else [],
        "noun_with_act": [f"the act of {bare_noun}"] if visibility_class == "visible" else [],
        "copula_what_is": [f"what is {bare_noun}"],
        "copula_X_is_Y": [f"{bare_noun} is something"],
        "copula_means": [f"{bare_noun} means"],
    }
    return {k: v for k, v in stimuli.items() if v}

# ============================================================
# Anchor sets — identical to OpenAI version
# ============================================================

ANCHOR_SETS = {
    "essence_vs_activity": {
        "entity": [
            "an essence",
            "a fixed nature",
            "an eternal kind",
            "the underlying being",
            "what something fundamentally is",
        ],
        "process": [
            "an activity",
            "an ongoing doing",
            "something happening",
            "people performing actions",
            "what someone is doing",
        ],
    },
    "object_vs_event": {
        "entity": [
            "an object",
            "a thing that exists",
            "an entity",
            "a permanent item",
            "a stable substance",
        ],
        "process": [
            "an event",
            "something that occurs",
            "an episode",
            "an unfolding occurrence",
            "an action in time",
        ],
    },
    "definition_vs_change": {
        "entity": [
            "something that has a definition",
            "a category with criteria",
            "a concept with fixed meaning",
            "an item that can be characterized",
            "a referent that can be specified",
        ],
        "process": [
            "an ongoing change",
            "a transformation",
            "something developing",
            "a continuous flow",
            "movement through time",
        ],
    },
}

# ============================================================
# Gemini API
# ============================================================

def find_working_model(api_key: str) -> str:
    """Try each candidate model until one works."""
    genai.configure(api_key=api_key)
    for model_name in EMBEDDING_MODELS_TO_TRY:
        try:
            # Test the model with a simple call
            result = genai.embed_content(
                model=model_name,
                content="test",
                task_type="SEMANTIC_SIMILARITY",
            )
            if result and "embedding" in result:
                print(f"✓ Using model: {model_name} (dim={len(result['embedding'])})")
                return model_name
        except Exception as e:
            print(f"  Model {model_name} not available: {str(e)[:100]}")
            continue
    raise RuntimeError("No working Gemini embedding model found.")

def get_embedding(text: str, model: str) -> np.ndarray:
    """Get embedding from Gemini API."""
    text = text.replace("\n", " ").strip()
    for attempt in range(5):
        try:
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="SEMANTIC_SIMILARITY",
            )
            return np.array(result["embedding"])
        except Exception as e:
            err_str = str(e).lower()
            if "rate" in err_str or "quota" in err_str or "429" in err_str:
                wait_time = 2 ** attempt
                print(f"  Rate limit. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Attempt {attempt+1} error: {str(e)[:100]}")
                time.sleep(2)
    raise RuntimeError(f"Failed to get embedding for: {text}")

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ============================================================
# Main
# ============================================================

def main():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Neither GEMINI_API_KEY nor GOOGLE_API_KEY found.")
        print("       Add one to .env:")
        print("         GEMINI_API_KEY=...")
        sys.exit(1)

    embedding_model = find_working_model(api_key)
    print()

    # Anchor embeddings
    print("=" * 70)
    print("Step 1: Embedding anchor sentences")
    print("=" * 70)
    anchor_embeddings = {}
    for anchor_name, poles in ANCHOR_SETS.items():
        anchor_embeddings[anchor_name] = {"entity": [], "process": []}
        for pole, sentences in poles.items():
            for sent in sentences:
                emb = get_embedding(sent, embedding_model)
                anchor_embeddings[anchor_name][pole].append(emb)
                print(f"  [{anchor_name}/{pole}] {sent}")
                time.sleep(0.1)  # gentle pacing
        anchor_embeddings[anchor_name]["entity_centroid"] = np.mean(anchor_embeddings[anchor_name]["entity"], axis=0)
        anchor_embeddings[anchor_name]["process_centroid"] = np.mean(anchor_embeddings[anchor_name]["process"], axis=0)
    print()

    # Stimuli embeddings
    print("=" * 70)
    print("Step 2: Embedding stimuli and computing E-P gaps")
    print("=" * 70)

    all_results = []
    for visibility_class, concepts in CONCEPTS.items():
        for concept in concepts:
            stimuli = build_stimuli(concept, visibility_class)
            print(f"\nConcept: {concept} ({visibility_class})")
            for form, phrases in stimuli.items():
                for phrase in phrases:
                    emb = get_embedding(phrase, embedding_model)
                    gaps = {}
                    for anchor_name in ANCHOR_SETS:
                        ent_sim = cosine_sim(emb, anchor_embeddings[anchor_name]["entity_centroid"])
                        proc_sim = cosine_sim(emb, anchor_embeddings[anchor_name]["process_centroid"])
                        gaps[anchor_name] = {
                            "entity_sim": ent_sim,
                            "process_sim": proc_sim,
                            "gap": ent_sim - proc_sim,
                        }
                    mean_gap = float(np.mean([gaps[a]["gap"] for a in gaps]))
                    signs = [1 if gaps[a]["gap"] > 0 else -1 for a in gaps]
                    sign_agreement = abs(sum(signs)) == len(signs)
                    result = {
                        "concept": concept,
                        "visibility_class": visibility_class,
                        "form": form,
                        "phrase": phrase,
                        "anchor_gaps": gaps,
                        "mean_gap": mean_gap,
                        "sign_agreement_across_anchors": sign_agreement,
                    }
                    all_results.append(result)
                    print(f"  [{form}] '{phrase}': mean E-P = {mean_gap:+.4f} (agree: {sign_agreement})")
                    time.sleep(0.1)

    # Aggregate
    print("\n" + "=" * 70)
    print("Step 3: Aggregate analyses")
    print("=" * 70)

    by_cell = {}
    for r in all_results:
        key = (r["form"], r["visibility_class"])
        by_cell.setdefault(key, []).append(r["mean_gap"])

    print(f"\n{'Form':<22} {'Visibility':<10} {'Mean E-P':>10} {'n':>4}")
    for (form, vis), gaps in sorted(by_cell.items()):
        print(f"  {form:<22} {vis:<10} {np.mean(gaps):>+10.4f} {len(gaps):>4}")

    n_agree = sum(1 for r in all_results if r["sign_agreement_across_anchors"])
    print(f"\nSign agreement across 3 anchors: {n_agree}/{len(all_results)} ({100*n_agree/len(all_results):.1f}%)")

    # Save
    output = {
        "model": embedding_model,
        "anchor_sets": list(ANCHOR_SETS.keys()),
        "n_stimuli": len(all_results),
        "stimulus_results": all_results,
        "by_form_visibility": {
            f"{form}_{vis}": {
                "mean_gap": float(np.mean(gaps)),
                "n": len(gaps),
            }
            for (form, vis), gaps in by_cell.items()
        },
        "sign_agreement_rate": n_agree / len(all_results),
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ Saved: {OUTPUT_FILE}")

    with open(SUMMARY_FILE, "w") as f:
        f.write("Study 2 Revision (Gemini) — Summary\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Model: {embedding_model}\n")
        f.write(f"Anchor sets: {list(ANCHOR_SETS.keys())}\n")
        f.write(f"Total stimuli: {len(all_results)}\n")
        f.write(f"Sign agreement: {n_agree}/{len(all_results)} ({100*n_agree/len(all_results):.1f}%)\n\n")
        f.write("MEAN E-P GAP BY FORM × VISIBILITY (averaged over 3 anchor sets)\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Form':<22} {'Visibility':<10} {'Mean E-P':>10} {'n':>4}\n")
        for (form, vis), gaps in sorted(by_cell.items()):
            f.write(f"{form:<22} {vis:<10} {np.mean(gaps):>+10.4f} {len(gaps):>4}\n")
    print(f"✓ Saved: {SUMMARY_FILE}")

    print("\nDone. Please send back study2_revised_results_gemini.json and study2_revised_summary_gemini.txt")

if __name__ == "__main__":
    main()
