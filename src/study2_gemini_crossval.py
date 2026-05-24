#!/usr/bin/env python3
"""Study 2 Cross-Validation: Gemini Embedding 2 via REST API"""

import json, subprocess, numpy as np, time

GOOGLE_KEY = "<YOUR_GOOGLE_KEY>"
MODEL = "gemini-embedding-2"

def get_gemini_embedding(text):
    payload = json.dumps({
        "model": f"models/{MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": "SEMANTIC_SIMILARITY"
    })
    result = subprocess.run(
        ["curl", "-s", f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:embedContent?key={GOOGLE_KEY}",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    if 'embedding' in data:
        return data['embedding']['values']
    else:
        print(f"  ERROR: {data.get('error',{}).get('message','unknown')}")
        return None

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# Same structure as OpenAI analysis
anchors = {
    'process_pole': ['an ongoing activity or process', 'something that is happening right now',
        'a dynamic unfolding event', 'continuous action in progress', 'doing something actively'],
    'entity_pole': ['a fixed and eternal essence', 'an abstract entity that exists independently',
        'the fundamental nature of something', 'a thing that has a definition',
        'a substance with inherent properties'],
}

concepts = {
    'love': {'type': 'invisible', 'forms': {
        'verb': 'to love someone', 'ing': 'loving someone deeply', 'er': 'a lover',
        'ful': 'a loving and beautiful heart', 'noun': 'love as a concept', 'copula': 'what is love'}},
    'think': {'type': 'invisible', 'forms': {
        'verb': 'to think about something', 'ing': 'thinking carefully', 'er': 'a great thinker',
        'ful': 'a thoughtful person', 'noun': 'thought as a concept', 'copula': 'what is thought'}},
    'consciousness': {'type': 'invisible', 'forms': {
        'verb': 'to be conscious of something', 'ing': 'being conscious and aware',
        'ful': 'a conscious and mindful state', 'noun': 'consciousness as a phenomenon',
        'copula': 'what is consciousness'}},
    'beauty': {'type': 'invisible', 'forms': {
        'verb': 'to beautify something', 'ing': 'beautifying and decorating',
        'ful': 'something truly beautiful', 'noun': 'beauty as a concept', 'copula': 'what is beauty'}},
    'truth': {'type': 'invisible', 'forms': {
        'verb': 'to tell the truth honestly', 'ing': 'being truthful and honest',
        'ful': 'a truthful statement', 'noun': 'truth as a concept', 'copula': 'what is truth'}},
    'hope': {'type': 'invisible', 'forms': {
        'verb': 'to hope for something better', 'ing': 'hoping and wishing',
        'ful': 'feeling hopeful about the future', 'noun': 'hope as a concept', 'copula': 'what is hope'}},
    'meaning': {'type': 'invisible', 'forms': {
        'verb': 'to mean something important', 'ing': 'meaning and significance',
        'ful': 'a meaningful experience', 'noun': 'meaning as a concept', 'copula': 'what is meaning'}},
    'run': {'type': 'visible', 'forms': {
        'verb': 'to run quickly', 'ing': 'running along the path', 'er': 'a fast runner',
        'noun': 'a morning run', 'copula': 'what is running'}},
    'dance': {'type': 'visible', 'forms': {
        'verb': 'to dance gracefully', 'ing': 'dancing on the stage', 'er': 'a professional dancer',
        'noun': 'a beautiful dance', 'copula': 'what is dance'}},
    'swim': {'type': 'visible', 'forms': {
        'verb': 'to swim in the ocean', 'ing': 'swimming in the pool', 'er': 'an olympic swimmer',
        'noun': 'a morning swim', 'copula': 'what is swimming'}},
    'climb': {'type': 'visible', 'forms': {
        'verb': 'to climb the mountain', 'ing': 'climbing the steep rock', 'er': 'a skilled climber',
        'noun': 'a difficult climb', 'copula': 'what is climbing'}},
    'cook': {'type': 'visible', 'forms': {
        'verb': 'to cook a delicious meal', 'ing': 'cooking dinner tonight', 'er': 'a talented cook',
        'noun': 'italian cooking', 'copula': 'what is cooking'}},
}

print("=" * 100)
print(f"Study 2 Cross-Validation: Gemini {MODEL}")
print("=" * 100)

# Anchors
print("\n>>> Anchor embeddings...")
anchor_embs = {}
for pole, texts in anchors.items():
    embs = [get_gemini_embedding(t) for t in texts]
    embs = [e for e in embs if e is not None]
    anchor_embs[pole] = np.mean(embs, axis=0)
    print(f"  {pole}: done (dim={len(embs[0])})")
    time.sleep(0.3)

# Concepts
print("\n>>> Concept embeddings...")
gem_results = []
for cname, c in concepts.items():
    print(f"  {cname}...", end=' ', flush=True)
    r = {'concept': cname, 'type': c['type'], 'forms': {}}
    for fname, text in c['forms'].items():
        if text is None: continue
        emb = get_gemini_embedding(text)
        time.sleep(0.2)
        if emb:
            p = cosine_sim(emb, anchor_embs['process_pole'])
            e = cosine_sim(emb, anchor_embs['entity_pole'])
            r['forms'][fname] = {'process_sim': p, 'entity_sim': e, 'text': text}
    gem_results.append(r)
    print("done")

# Aggregate
print("\n" + "=" * 100)
print("GEMINI AGGREGATE: Entity-Process Gap by Form × Visibility")
print("=" * 100)

form_types = ['verb', 'ing', 'er', 'ful', 'noun', 'copula']
gem_agg = {}
for vt in ['invisible', 'visible']:
    print(f"\n--- {vt.upper()} ---")
    print(f"{'Form':<10} {'Process':<12} {'Entity':<12} {'E-P gap':<12} {'Dir'}")
    print("-" * 55)
    for ft in form_types:
        ps = [r['forms'][ft]['process_sim'] for r in gem_results if r['type']==vt and ft in r['forms']]
        es = [r['forms'][ft]['entity_sim'] for r in gem_results if r['type']==vt and ft in r['forms']]
        if ps:
            ap, ae = np.mean(ps), np.mean(es)
            gap = ae - ap
            d = "→ ENTITY" if gap > 0.02 else ("→ PROCESS" if gap < -0.02 else "NEUTRAL")
            gem_agg[(vt,ft)] = gap
            print(f"{ft:<10} {ap:<12.4f} {ae:<12.4f} {gap:<+12.4f} {d}")

# Cross-validation with OpenAI
print("\n\n" + "=" * 100)
print("CROSS-VALIDATION: OpenAI text-embedding-3-large vs Gemini embedding-2")
print("=" * 100)

with open('study2_embedding_results.json') as f:
    oai_results = json.load(f)

print(f"\n{'Visibility':<12} {'Form':<10} {'OpenAI E-P':<14} {'Gemini E-P':<14} {'Agreement'}")
print("-" * 65)

agreements = 0
total_comparisons = 0
for vt in ['invisible', 'visible']:
    for ft in form_types:
        oai_gaps = [r['forms'][ft]['entity_sim']-r['forms'][ft]['process_sim']
                    for r in oai_results if r['type']==vt and ft in r['forms']]
        gem_gap = gem_agg.get((vt,ft), None)
        if oai_gaps and gem_gap is not None:
            oai_avg = np.mean(oai_gaps)
            agree = "✓" if (oai_avg>0)==(gem_gap>0) else "✗"
            if agree == "✓": agreements += 1
            total_comparisons += 1
            print(f"{vt:<12} {ft:<10} {oai_avg:<+14.4f} {gem_gap:<+14.4f} {agree}")

print(f"\nAgreement rate: {agreements}/{total_comparisons} ({agreements/total_comparisons*100:.0f}%)")

# Key metric
print("\n" + "=" * 100)
print("KEY METRIC: ing→noun E-P Gap Swing")
print("=" * 100)

for model_name, results in [("OpenAI", oai_results), ("Gemini", gem_results)]:
    for vt in ['invisible', 'visible']:
        ing = [r['forms']['ing']['entity_sim']-r['forms']['ing']['process_sim']
               for r in results if r['type']==vt and 'ing' in r['forms']]
        noun = [r['forms']['noun']['entity_sim']-r['forms']['noun']['process_sim']
                for r in results if r['type']==vt and 'noun' in r['forms']]
        if ing and noun:
            swing = np.mean(noun) - np.mean(ing)
            print(f"  {model_name:<8} {vt:<12} ing→noun swing: {swing:+.4f}")
    # Ratio
    inv_swings = [(r['forms']['noun']['entity_sim']-r['forms']['noun']['process_sim']) - 
                  (r['forms']['ing']['entity_sim']-r['forms']['ing']['process_sim'])
                  for r in results if r['type']=='invisible' and 'ing' in r['forms'] and 'noun' in r['forms']]
    vis_swings = [(r['forms']['noun']['entity_sim']-r['forms']['noun']['process_sim']) - 
                  (r['forms']['ing']['entity_sim']-r['forms']['ing']['process_sim'])
                  for r in results if r['type']=='visible' and 'ing' in r['forms'] and 'noun' in r['forms']]
    if inv_swings and vis_swings:
        ratio = np.mean(inv_swings)/np.mean(vis_swings) if np.mean(vis_swings)!=0 else float('inf')
        print(f"  {model_name:<8} invisible/visible ratio: {ratio:.2f}x")

# Save
with open('study2_gemini_results.json', 'w') as f:
    save = [{'concept':r['concept'],'type':r['type'],'forms':r['forms']} for r in gem_results]
    json.dump(save, f, indent=2)

print("\nDone!")
