#!/usr/bin/env python3
"""
Study 2 Revision (Phase C):
- Addresses Muni's Major 4: hypothesis-laden stimuli in original Study 2
- Implements:
  1. Multiple noun-context templates (removes "as a concept" bias)
  2. Three entity anchor sets (essence / object / definition)
  3. Three process anchor sets (activity / event / change)
  4. Anchor sensitivity analysis

USAGE on Boss's Mac:
  cd /Users/iizumimasamichi/tft
  source env/bin/activate
  pip install openai numpy python-dotenv  # if not already installed
  python study2_revision.py

  The script auto-loads .env from the current directory or any parent.
  Expected .env contents:
    OPENAI_API_KEY=sk-...

OUTPUT:
  study2_revised_results.json  — full results
  study2_revised_summary.txt   — human-readable summary
"""

import os
import json
import time
import sys
import numpy as np
from typing import List, Dict
import openai

# ============================================================
# Load .env if present (looks in current directory and parents)
# ============================================================
try:
    from dotenv import load_dotenv
    # Search current dir and parent dirs for .env
    from pathlib import Path
    cwd = Path.cwd()
    env_loaded = False
    for path in [cwd] + list(cwd.parents):
        env_file = path / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✓ Loaded .env from: {env_file}")
            env_loaded = True
            break
    if not env_loaded:
        print("⚠️ No .env file found in current dir or parents. Will use environment variables only.")
except ImportError:
    print("ℹ️ python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Falling back to OS environment variables.")

# ============================================================
# Configuration
# ============================================================
EMBEDDING_MODEL = "text-embedding-3-large"  # 3072 dimensions
OUTPUT_FILE = "study2_revised_results.json"
SUMMARY_FILE = "study2_revised_summary.txt"

# ============================================================
# Stimuli design
# ============================================================

# Six invisible-process concepts and six visible-process concepts
CONCEPTS = {
    "invisible": ["love", "consciousness", "truth", "beauty", "justice", "freedom"],
    "visible": ["running", "swimming", "dancing", "eating", "walking", "cooking"],
}

# Mapping from -ing form back to verb root (for stimulus templates)
VERB_ROOTS = {
    "love": ("love", "loving", "lover"),
    "consciousness": ("be conscious", "being conscious", "(no agentive)"),
    "truth": ("tell the truth", "being truthful", "(no agentive)"),
    "beauty": ("be beautiful", "being beautiful", "(no agentive)"),
    "justice": ("act justly", "acting justly", "(no agentive)"),
    "freedom": ("be free", "being free", "(no agentive)"),
    "running": ("run", "running", "runner"),
    "swimming": ("swim", "swimming", "swimmer"),
    "dancing": ("dance", "dancing", "dancer"),
    "eating": ("eat", "eating", "eater"),
    "walking": ("walk", "walking", "walker"),
    "cooking": ("cook", "cooking", "cooker"),
}

def build_stimuli(concept: str, visibility_class: str) -> Dict[str, List[str]]:
    """
    Build six grammatical forms × multiple templates for one concept.
    Returns: dict mapping form_label -> list of stimulus phrases
    """
    if visibility_class == "invisible":
        # Map back to root
        if concept == "love":
            verb, ing_form, agentive = "love", "loving", "a lover of music"
            bare_noun = "love"
        elif concept == "consciousness":
            verb, ing_form, agentive = "be conscious of something", "being conscious", "(no agentive)"
            bare_noun = "consciousness"
        elif concept == "truth":
            verb, ing_form, agentive = "tell the truth", "being truthful", "(no agentive)"
            bare_noun = "truth"
        elif concept == "beauty":
            verb, ing_form, agentive = "be beautiful", "being beautiful", "(no agentive)"
            bare_noun = "beauty"
        elif concept == "justice":
            verb, ing_form, agentive = "act justly", "acting justly", "(no agentive)"
            bare_noun = "justice"
        elif concept == "freedom":
            verb, ing_form, agentive = "be free", "being free", "(no agentive)"
            bare_noun = "freedom"
        else:
            raise ValueError(f"Unknown invisible concept: {concept}")
    else:  # visible
        if concept == "running":
            verb, ing_form, agentive = "run", "running", "a runner"
            bare_noun = "running"
        elif concept == "swimming":
            verb, ing_form, agentive = "swim", "swimming", "a swimmer"
            bare_noun = "swimming"
        elif concept == "dancing":
            verb, ing_form, agentive = "dance", "dancing", "a dancer"
            bare_noun = "dancing"
        elif concept == "eating":
            verb, ing_form, agentive = "eat", "eating", "(no agentive)"
            bare_noun = "eating"
        elif concept == "walking":
            verb, ing_form, agentive = "walk", "walking", "a walker"
            bare_noun = "walking"
        elif concept == "cooking":
            verb, ing_form, agentive = "cook", "cooking", "a cook"
            bare_noun = "cooking"
        else:
            raise ValueError(f"Unknown visible concept: {concept}")

    stimuli = {
        # Form 1: verb (clean — no entity/process bias)
        "verb": [
            f"to {verb}",
            f"people {ing_form}" if concept in ("love",) else f"someone {ing_form}",
        ],
        # Form 2: -ing progressive/gerund
        "progressive": [
            f"{ing_form}",
            f"{ing_form} something" if concept == "love" else f"{ing_form} naturally",
        ],
        # Form 3: agentive (-er)
        "agentive": [agentive] if "no agentive" not in agentive else [],
        # Form 4: BARE NOUN — multiple templates to test for "as a concept" bias
        "noun_minimal": [bare_noun],
        "noun_with_word": [f"the word {bare_noun}"],
        "noun_with_feeling": [f"the feeling of {bare_noun}"] if visibility_class == "invisible" else [],
        "noun_with_act": [f"the act of {bare_noun}"] if visibility_class == "visible" else [],
        # Form 5: definitional copular frame — multiple variants
        "copula_what_is": [f"what is {bare_noun}"],
        "copula_X_is_Y": [f"{bare_noun} is something"],
        "copula_means": [f"{bare_noun} means"],
    }
    # Remove empty lists
    stimuli = {k: v for k, v in stimuli.items() if v}
    return stimuli

# ============================================================
# Anchor sets — three independent operationalizations of each pole
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
# Embedding API
# ============================================================

def get_embedding(text: str, client) -> np.ndarray:
    """Get embedding from OpenAI API."""
    text = text.replace("\n", " ").strip()
    for attempt in range(5):
        try:
            response = client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
            return np.array(response.data[0].embedding)
        except openai.RateLimitError:
            wait_time = 2 ** attempt
            print(f"  Rate limit hit. Waiting {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"  Error on attempt {attempt+1}: {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed to get embedding for: {text}")

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# ============================================================
# Main analysis
# ============================================================

def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found.")
        print("       Either:")
        print("       (a) Place a .env file in the working directory with:")
        print("           OPENAI_API_KEY=sk-...")
        print("       (b) Run: export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)
    print(f"Using model: {EMBEDDING_MODEL}")
    print(f"Concept categories: {list(CONCEPTS.keys())}")
    print()

    # Embed all anchor sentences once
    print("=" * 70)
    print("Step 1: Embedding anchor sentences")
    print("=" * 70)
    anchor_embeddings = {}
    for anchor_name, poles in ANCHOR_SETS.items():
        anchor_embeddings[anchor_name] = {"entity": [], "process": []}
        for pole, sentences in poles.items():
            for sent in sentences:
                emb = get_embedding(sent, client)
                anchor_embeddings[anchor_name][pole].append(emb)
                print(f"  [{anchor_name}/{pole}] {sent}")
        # Average to get a single pole vector
        anchor_embeddings[anchor_name]["entity_centroid"] = np.mean(anchor_embeddings[anchor_name]["entity"], axis=0)
        anchor_embeddings[anchor_name]["process_centroid"] = np.mean(anchor_embeddings[anchor_name]["process"], axis=0)
    print()

    # Embed all stimuli and compute E-P gaps
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
                    emb = get_embedding(phrase, client)
                    # Compute E-P gap for each anchor set
                    gaps = {}
                    for anchor_name in ANCHOR_SETS:
                        ent_sim = cosine_sim(emb, anchor_embeddings[anchor_name]["entity_centroid"])
                        proc_sim = cosine_sim(emb, anchor_embeddings[anchor_name]["process_centroid"])
                        gap = ent_sim - proc_sim
                        gaps[anchor_name] = {
                            "entity_sim": ent_sim,
                            "process_sim": proc_sim,
                            "gap": gap,
                        }
                    # Average gap across anchor sets
                    mean_gap = float(np.mean([gaps[a]["gap"] for a in gaps]))
                    # Direction agreement
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
                    print(f"  [{form}] '{phrase}': mean E-P gap = {mean_gap:+.4f} (agreement: {sign_agreement})")

    # ============================================================
    # Step 3: Aggregate analyses
    # ============================================================
    print("\n" + "=" * 70)
    print("Step 3: Aggregate analyses")
    print("=" * 70)

    # Pre-aggregation: how many results
    print(f"\nTotal stimuli embedded: {len(all_results)}")

    # By form × visibility, averaged over anchor sets
    print("\n--- Mean E-P gap by form × visibility (averaged over 3 anchor sets) ---")
    by_cell = {}
    for r in all_results:
        key = (r["form"], r["visibility_class"])
        by_cell.setdefault(key, []).append(r["mean_gap"])

    print(f"\n{'Form':<22} {'Visibility':<10} {'Mean E-P':>10} {'n':>4}")
    for (form, vis), gaps in sorted(by_cell.items()):
        print(f"  {form:<22} {vis:<10} {np.mean(gaps):>+10.4f} {len(gaps):>4}")

    # Per-anchor breakdown
    print("\n--- Per-anchor sensitivity analysis (mean E-P gap by anchor set) ---")
    by_anchor = {}
    for r in all_results:
        for anchor in r["anchor_gaps"]:
            key = (anchor, r["form"], r["visibility_class"])
            by_anchor.setdefault(key, []).append(r["anchor_gaps"][anchor]["gap"])

    # Compare bare_noun_minimal "noun_minimal" effects across anchor sets
    print(f"\n{'Anchor set':<25} {'Form':<22} {'Visibility':<10} {'Mean E-P':>10}")
    for (anchor, form, vis), gaps in sorted(by_anchor.items()):
        if form in ("noun_minimal", "noun_with_word", "noun_with_feeling", "noun_with_act"):
            print(f"  {anchor:<25} {form:<22} {vis:<10} {np.mean(gaps):>+10.4f}")

    # Sign agreement summary
    n_agree = sum(1 for r in all_results if r["sign_agreement_across_anchors"])
    print(f"\nAnchor-set sign agreement: {n_agree}/{len(all_results)} stimuli ({100*n_agree/len(all_results):.1f}%)")

    # Nominalization swing per anchor
    print("\n--- Nominalization swing (verb → noun_minimal) per anchor ---")
    for anchor in ANCHOR_SETS:
        inv_gaps_verb = []
        inv_gaps_noun = []
        vis_gaps_verb = []
        vis_gaps_noun = []
        for r in all_results:
            g = r["anchor_gaps"][anchor]["gap"]
            if r["form"] == "verb":
                if r["visibility_class"] == "invisible":
                    inv_gaps_verb.append(g)
                else:
                    vis_gaps_verb.append(g)
            elif r["form"] == "noun_minimal":
                if r["visibility_class"] == "invisible":
                    inv_gaps_noun.append(g)
                else:
                    vis_gaps_noun.append(g)
        if inv_gaps_verb and inv_gaps_noun and vis_gaps_verb and vis_gaps_noun:
            inv_swing = np.mean(inv_gaps_noun) - np.mean(inv_gaps_verb)
            vis_swing = np.mean(vis_gaps_noun) - np.mean(vis_gaps_verb)
            ratio = inv_swing / vis_swing if abs(vis_swing) > 0.001 else float("inf")
            print(f"  {anchor:<28} invisible swing = {inv_swing:+.4f}, visible swing = {vis_swing:+.4f}, ratio = {ratio:.2f}×")

    # ============================================================
    # Save outputs
    # ============================================================
    output = {
        "model": EMBEDDING_MODEL,
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
    print(f"\n✓ Full results saved: {OUTPUT_FILE}")

    # Summary text
    with open(SUMMARY_FILE, "w") as f:
        f.write("Study 2 Revision — Summary\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Model: {EMBEDDING_MODEL}\n")
        f.write(f"Anchor sets: {list(ANCHOR_SETS.keys())}\n")
        f.write(f"Total stimuli: {len(all_results)}\n")
        f.write(f"Sign agreement across anchors: {n_agree}/{len(all_results)} ({100*n_agree/len(all_results):.1f}%)\n\n")
        f.write("MEAN E-P GAP BY FORM × VISIBILITY (averaged over 3 anchor sets)\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Form':<22} {'Visibility':<10} {'Mean E-P':>10} {'n':>4}\n")
        for (form, vis), gaps in sorted(by_cell.items()):
            f.write(f"{form:<22} {vis:<10} {np.mean(gaps):>+10.4f} {len(gaps):>4}\n")
    print(f"✓ Summary saved: {SUMMARY_FILE}")

    print("\nDone. Please send back study2_revised_results.json and study2_revised_summary.txt")

if __name__ == "__main__":
    main()
