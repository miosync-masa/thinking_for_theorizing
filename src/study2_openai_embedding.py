#!/usr/bin/env python3
"""
Study 2: Embedding-Space Analysis of Grammatical Form Shifts
Does nominalization shift concepts from process-space to entity-space?
"""

import os
import json
import numpy as np
from openai import OpenAI

OPENAI_KEY = "<YOUR_OPENAI_KEY>"

client = OpenAI(api_key=OPENAI_KEY)

# ============================================================
# Define concepts with grammatical forms
# ============================================================

concepts = {
    # INVISIBLE PROCESSES
    'love': {
        'type': 'invisible',
        'forms': {
            'verb': 'to love someone',
            'ing': 'loving someone deeply',
            'er': 'a lover',
            'ful': 'a loving and beautiful heart',
            'noun': 'love as a concept',
            'copula': 'what is love',
        }
    },
    'think': {
        'type': 'invisible',
        'forms': {
            'verb': 'to think about something',
            'ing': 'thinking carefully',
            'er': 'a great thinker',
            'ful': 'a thoughtful person',
            'noun': 'thought as a concept',
            'copula': 'what is thought',
        }
    },
    'consciousness': {
        'type': 'invisible',
        'forms': {
            'verb': 'to be conscious of something',
            'ing': 'being conscious and aware',
            'er': None,  # no -er form!
            'ful': 'a conscious and mindful state',
            'noun': 'consciousness as a phenomenon',
            'copula': 'what is consciousness',
        }
    },
    'beauty': {
        'type': 'invisible',
        'forms': {
            'verb': 'to beautify something',
            'ing': 'beautifying and decorating',
            'er': None,  # no -er form!
            'ful': 'something truly beautiful',
            'noun': 'beauty as a concept',
            'copula': 'what is beauty',
        }
    },
    'truth': {
        'type': 'invisible',
        'forms': {
            'verb': 'to tell the truth honestly',
            'ing': 'being truthful and honest',
            'er': None,  # no -er form!
            'ful': 'a truthful statement',
            'noun': 'truth as a concept',
            'copula': 'what is truth',
        }
    },
    'hope': {
        'type': 'invisible',
        'forms': {
            'verb': 'to hope for something better',
            'ing': 'hoping and wishing',
            'er': None,
            'ful': 'feeling hopeful about the future',
            'noun': 'hope as a concept',
            'copula': 'what is hope',
        }
    },
    'meaning': {
        'type': 'invisible',
        'forms': {
            'verb': 'to mean something important',
            'ing': 'meaning and significance',
            'er': None,
            'ful': 'a meaningful experience',
            'noun': 'meaning as a concept',
            'copula': 'what is meaning',
        }
    },
    # VISIBLE PROCESSES
    'run': {
        'type': 'visible',
        'forms': {
            'verb': 'to run quickly',
            'ing': 'running along the path',
            'er': 'a fast runner',
            'ful': None,  # no -ful form
            'noun': 'a morning run',
            'copula': 'what is running',
        }
    },
    'dance': {
        'type': 'visible',
        'forms': {
            'verb': 'to dance gracefully',
            'ing': 'dancing on the stage',
            'er': 'a professional dancer',
            'ful': None,
            'noun': 'a beautiful dance',
            'copula': 'what is dance',
        }
    },
    'swim': {
        'type': 'visible',
        'forms': {
            'verb': 'to swim in the ocean',
            'ing': 'swimming in the pool',
            'er': 'an olympic swimmer',
            'ful': None,
            'noun': 'a morning swim',
            'copula': 'what is swimming',
        }
    },
    'climb': {
        'type': 'visible',
        'forms': {
            'verb': 'to climb the mountain',
            'ing': 'climbing the steep rock',
            'er': 'a skilled climber',
            'ful': None,
            'noun': 'a difficult climb',
            'copula': 'what is climbing',
        }
    },
    'cook': {
        'type': 'visible',
        'forms': {
            'verb': 'to cook a delicious meal',
            'ing': 'cooking dinner tonight',
            'er': 'a talented cook',
            'ful': None,
            'noun': 'italian cooking',
            'copula': 'what is cooking',
        }
    },
}

# Reference anchor phrases for semantic poles
anchors = {
    'process_pole': [
        'an ongoing activity or process',
        'something that is happening right now',
        'a dynamic unfolding event',
        'continuous action in progress',
        'doing something actively',
    ],
    'entity_pole': [
        'a fixed and eternal essence',
        'an abstract entity that exists independently',
        'the fundamental nature of something',
        'a thing that has a definition',
        'a substance with inherent properties',
    ],
    'person_pole': [
        'a specific human individual',
        'a person who does something',
        'an identifiable human agent',
        'someone you can point to',
        'a visible acting person',
    ],
    'degree_pole': [
        'a matter of degree and intensity',
        'something that varies continuously',
        'a quality that can be more or less',
        'a spectrum from weak to strong',
        'gradual variation in amount',
    ],
}

# ============================================================
# Get embeddings
# ============================================================
def get_embeddings(texts, model="text-embedding-3-large"):
    """Get embeddings for a list of texts."""
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]

def cosine_sim(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print("=" * 100)
print("Study 2: Embedding-Space Analysis of Grammatical Form Shifts")
print("Model: text-embedding-3-large (3072 dimensions)")
print("=" * 100)

# Get anchor embeddings
print("\n>>> Getting anchor embeddings...")
anchor_embs = {}
for pole_name, phrases in anchors.items():
    embs = get_embeddings(phrases)
    # Average the anchor embeddings
    anchor_embs[pole_name] = np.mean(embs, axis=0)
    print(f"  {pole_name}: done")

# Get concept embeddings
print("\n>>> Getting concept embeddings...")
all_results = []

for concept_name, concept in concepts.items():
    print(f"\n  Processing: {concept_name} ({concept['type']})")
    
    forms_texts = []
    forms_names = []
    for form_name, text in concept['forms'].items():
        if text is not None:
            forms_texts.append(text)
            forms_names.append(form_name)
    
    embs = get_embeddings(forms_texts)
    
    # Calculate similarities to each pole
    result = {
        'concept': concept_name,
        'type': concept['type'],
        'forms': {}
    }
    
    for i, (form_name, emb) in enumerate(zip(forms_names, embs)):
        sims = {}
        for pole_name, pole_emb in anchor_embs.items():
            sims[pole_name] = cosine_sim(emb, pole_emb)
        
        result['forms'][form_name] = {
            'text': forms_texts[i],
            'process_sim': sims['process_pole'],
            'entity_sim': sims['entity_pole'],
            'person_sim': sims['person_pole'],
            'degree_sim': sims['degree_pole'],
            'embedding': emb,  # store for pairwise comparison
        }
    
    # Calculate pairwise distances between forms
    result['pairwise'] = {}
    for i, (name_i, _) in enumerate(zip(forms_names, embs)):
        for j, (name_j, _) in enumerate(zip(forms_names, embs)):
            if i < j:
                sim = cosine_sim(embs[i], embs[j])
                result['pairwise'][f'{name_i}-{name_j}'] = sim
    
    all_results.append(result)

# ============================================================
# Print results
# ============================================================
print("\n\n" + "=" * 100)
print("RESULTS: Similarity to Semantic Poles")
print("=" * 100)

print(f"\n{'Concept':<15} {'Form':<8} {'Process':<10} {'Entity':<10} {'Person':<10} {'Degree':<10} {'E-P gap':<10}")
print("-" * 80)

for r in all_results:
    concept = r['concept']
    ctype = r['type']
    for form_name, data in r['forms'].items():
        p = data['process_sim']
        e = data['entity_sim']
        per = data['person_sim']
        d = data['degree_sim']
        gap = e - p  # positive = more entity-like, negative = more process-like
        marker = "◀ ENTITY" if gap > 0.05 else ("◀ PROCESS" if gap < -0.05 else "")
        print(f"{concept:<15} {form_name:<8} {p:<10.4f} {e:<10.4f} {per:<10.4f} {d:<10.4f} {gap:<+10.4f} {marker}")
    print()

# ============================================================
# Aggregate: E-P gap by form type and visibility
# ============================================================
print("\n" + "=" * 100)
print("AGGREGATE: Entity-Process Gap by Form Type × Visibility")
print("=" * 100)

form_types = ['verb', 'ing', 'er', 'ful', 'noun', 'copula']
for vis_type in ['invisible', 'visible']:
    print(f"\n--- {vis_type.upper()} concepts ---")
    print(f"{'Form':<10} {'Avg Process':<12} {'Avg Entity':<12} {'Avg E-P gap':<12} {'Direction'}")
    print("-" * 60)
    
    for form_type in form_types:
        p_vals = []
        e_vals = []
        for r in all_results:
            if r['type'] == vis_type and form_type in r['forms']:
                p_vals.append(r['forms'][form_type]['process_sim'])
                e_vals.append(r['forms'][form_type]['entity_sim'])
        
        if p_vals:
            avg_p = np.mean(p_vals)
            avg_e = np.mean(e_vals)
            gap = avg_e - avg_p
            direction = "→ ENTITY" if gap > 0.02 else ("→ PROCESS" if gap < -0.02 else "NEUTRAL")
            print(f"{form_type:<10} {avg_p:<12.4f} {avg_e:<12.4f} {gap:<+12.4f} {direction}")

# ============================================================
# Pairwise: How far apart are the grammatical forms?
# ============================================================
print("\n\n" + "=" * 100)
print("PAIRWISE DISTANCES: How far do grammatical forms shift in embedding space?")
print("=" * 100)

key_pairs = ['verb-noun', 'verb-copula', 'ing-noun', 'ing-copula', 'verb-ing', 'verb-er', 'noun-copula']

print(f"\n{'Concept':<15} {'Type':<10}", end='')
for pair in key_pairs:
    print(f" {pair:<12}", end='')
print()
print("-" * 110)

for r in all_results:
    print(f"{r['concept']:<15} {r['type']:<10}", end='')
    for pair in key_pairs:
        val = r['pairwise'].get(pair, None)
        if val is not None:
            print(f" {val:<12.4f}", end='')
        else:
            print(f" {'N/A':<12}", end='')
    print()

# Aggregate pairwise by visibility
print(f"\n{'AGGREGATE':<15} {'':10}", end='')
for pair in key_pairs:
    print(f" {pair:<12}", end='')
print()
print("-" * 110)

for vis_type in ['invisible', 'visible']:
    print(f"{vis_type:<15} {'':10}", end='')
    for pair in key_pairs:
        vals = [r['pairwise'][pair] for r in all_results 
                if r['type'] == vis_type and pair in r['pairwise']]
        if vals:
            print(f" {np.mean(vals):<12.4f}", end='')
        else:
            print(f" {'N/A':<12}", end='')
    print()

# Save results (without embeddings for size)
save_results = []
for r in all_results:
    sr = {'concept': r['concept'], 'type': r['type'], 'forms': {}, 'pairwise': r['pairwise']}
    for form_name, data in r['forms'].items():
        sr['forms'][form_name] = {k: v for k, v in data.items() if k != 'embedding'}
    save_results.append(sr)

with open('study2_embedding_results.json', 'w') as f:
    json.dump(save_results, f, indent=2)

print("\n\nResults saved to study2_embedding_results.json")

