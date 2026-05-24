#!/usr/bin/env python3
"""
Deep Analysis: How abstract vs concrete concepts are actually used in corpora
Key question: Do invisible processes get nominalized more than visible ones?
"""

import os
from collections import defaultdict

def parse_conllu_detailed(filepath):
    """Parse CoNLL-U and return list of sentences with full token info."""
    sentences = []
    current = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            if line == '':
                if current:
                    sentences.append(current)
                current = []
                continue
            parts = line.split('\t')
            if len(parts) != 10 or '-' in parts[0] or '.' in parts[0]:
                continue
            current.append({
                'id': parts[0], 'form': parts[1].lower(), 'lemma': parts[2].lower(),
                'upos': parts[3], 'feats': parts[5], 'head': parts[6],
                'deprel': parts[7].split(':')[0]
            })
    if current:
        sentences.append(current)
    return sentences

# ============================================================
# Define concept pairs: verb form / noun form / visibility
# ============================================================

# English concept pairs
en_concepts = {
    # INVISIBLE processes (philosophical hard problem candidates)
    'love': {'verb_lemmas': ['love'], 'noun_lemmas': ['love'], 'type': 'invisible',
             'ing_forms': ['loving']},
    'think': {'verb_lemmas': ['think'], 'noun_lemmas': ['thought', 'thinking'], 'type': 'invisible',
              'ing_forms': ['thinking']},
    'know': {'verb_lemmas': ['know'], 'noun_lemmas': ['knowledge', 'knowing'], 'type': 'invisible',
             'ing_forms': ['knowing']},
    'believe': {'verb_lemmas': ['believe'], 'noun_lemmas': ['belief', 'believing'], 'type': 'invisible',
                'ing_forms': ['believing']},
    'feel': {'verb_lemmas': ['feel'], 'noun_lemmas': ['feeling', 'emotion'], 'type': 'invisible',
             'ing_forms': ['feeling']},
    'hope': {'verb_lemmas': ['hope'], 'noun_lemmas': ['hope'], 'type': 'invisible',
             'ing_forms': ['hoping']},
    'fear': {'verb_lemmas': ['fear'], 'noun_lemmas': ['fear'], 'type': 'invisible',
             'ing_forms': ['fearing']},
    'trust': {'verb_lemmas': ['trust'], 'noun_lemmas': ['trust'], 'type': 'invisible',
              'ing_forms': ['trusting']},
    'judge': {'verb_lemmas': ['judge'], 'noun_lemmas': ['judgment', 'judgement'], 'type': 'invisible',
              'ing_forms': ['judging']},
    'understand': {'verb_lemmas': ['understand'], 'noun_lemmas': ['understanding'], 'type': 'invisible',
                   'ing_forms': ['understanding']},
    'suffer': {'verb_lemmas': ['suffer'], 'noun_lemmas': ['suffering', 'pain'], 'type': 'invisible',
               'ing_forms': ['suffering']},
    'desire': {'verb_lemmas': ['desire'], 'noun_lemmas': ['desire'], 'type': 'invisible',
               'ing_forms': ['desiring']},
    'doubt': {'verb_lemmas': ['doubt'], 'noun_lemmas': ['doubt'], 'type': 'invisible',
              'ing_forms': ['doubting']},
    'reason': {'verb_lemmas': ['reason'], 'noun_lemmas': ['reason', 'reasoning'], 'type': 'invisible',
               'ing_forms': ['reasoning']},
    'intend': {'verb_lemmas': ['intend'], 'noun_lemmas': ['intention', 'intent'], 'type': 'invisible',
               'ing_forms': ['intending']},

    # VISIBLE processes (no hard problem)
    'run': {'verb_lemmas': ['run'], 'noun_lemmas': ['run', 'running'], 'type': 'visible',
            'ing_forms': ['running']},
    'eat': {'verb_lemmas': ['eat'], 'noun_lemmas': ['eating', 'meal'], 'type': 'visible',
            'ing_forms': ['eating']},
    'walk': {'verb_lemmas': ['walk'], 'noun_lemmas': ['walk', 'walking'], 'type': 'visible',
             'ing_forms': ['walking']},
    'build': {'verb_lemmas': ['build'], 'noun_lemmas': ['building', 'construction'], 'type': 'visible',
              'ing_forms': ['building']},
    'write': {'verb_lemmas': ['write'], 'noun_lemmas': ['writing', 'text'], 'type': 'visible',
              'ing_forms': ['writing']},
    'fight': {'verb_lemmas': ['fight'], 'noun_lemmas': ['fight', 'fighting'], 'type': 'visible',
              'ing_forms': ['fighting']},
    'dance': {'verb_lemmas': ['dance'], 'noun_lemmas': ['dance', 'dancing'], 'type': 'visible',
              'ing_forms': ['dancing']},
    'cook': {'verb_lemmas': ['cook'], 'noun_lemmas': ['cooking', 'cook'], 'type': 'visible',
             'ing_forms': ['cooking']},
    'drive': {'verb_lemmas': ['drive'], 'noun_lemmas': ['drive', 'driving'], 'type': 'visible',
              'ing_forms': ['driving']},
    'swim': {'verb_lemmas': ['swim'], 'noun_lemmas': ['swim', 'swimming'], 'type': 'visible',
             'ing_forms': ['swimming']},
    'play': {'verb_lemmas': ['play'], 'noun_lemmas': ['play', 'playing'], 'type': 'visible',
             'ing_forms': ['playing']},
    'sing': {'verb_lemmas': ['sing'], 'noun_lemmas': ['singing', 'song'], 'type': 'visible',
             'ing_forms': ['singing']},
    'paint': {'verb_lemmas': ['paint'], 'noun_lemmas': ['painting', 'paint'], 'type': 'visible',
              'ing_forms': ['painting']},
    'climb': {'verb_lemmas': ['climb'], 'noun_lemmas': ['climb', 'climbing'], 'type': 'visible',
              'ing_forms': ['climbing']},
    'throw': {'verb_lemmas': ['throw'], 'noun_lemmas': ['throw', 'throwing'], 'type': 'visible',
              'ing_forms': ['throwing']},
}

# Japanese concept pairs 
ja_concepts = {
    'love': {'verb_lemmas': ['愛する', '愛す'], 'noun_lemmas': ['愛', '愛情'], 'type': 'invisible'},
    'think': {'verb_lemmas': ['考える', '思う', '思考する'], 'noun_lemmas': ['考え', '思考', '思い'], 'type': 'invisible'},
    'know': {'verb_lemmas': ['知る', '分かる'], 'noun_lemmas': ['知識', '知恵'], 'type': 'invisible'},
    'believe': {'verb_lemmas': ['信じる', '信ずる'], 'noun_lemmas': ['信仰', '信念', '信頼'], 'type': 'invisible'},
    'feel': {'verb_lemmas': ['感じる'], 'noun_lemmas': ['感情', '気持ち', '感覚'], 'type': 'invisible'},
    'run': {'verb_lemmas': ['走る', '駆ける'], 'noun_lemmas': ['走り'], 'type': 'visible'},
    'eat': {'verb_lemmas': ['食べる', '食う'], 'noun_lemmas': ['食事', '食'], 'type': 'visible'},
    'walk': {'verb_lemmas': ['歩く', '歩む'], 'noun_lemmas': ['歩き', '散歩'], 'type': 'visible'},
    'build': {'verb_lemmas': ['建てる', '作る'], 'noun_lemmas': ['建築', '建物'], 'type': 'visible'},
    'write': {'verb_lemmas': ['書く'], 'noun_lemmas': ['書き', '文章'], 'type': 'visible'},
}

print("=" * 100)
print("DEEP ANALYSIS: Abstract vs Concrete Concept Usage Patterns")
print("=" * 100)

# ============================================================
# English Analysis
# ============================================================
print("\n>>> Processing English corpus...")
en_sents = parse_conllu_detailed('ud_data/en.conllu')

en_results = {}
for concept_name, concept in en_concepts.items():
    verb_count = 0
    noun_count = 0
    ing_as_noun = 0  # -ing form used as noun
    ing_as_verb = 0  # -ing form used as verb
    in_cop_construction = 0  # appears as subject of copula
    
    for sent in en_sents:
        token_map = {t['id']: t for t in sent}
        
        for token in sent:
            lemma = token['lemma']
            form = token['form']
            upos = token['upos']
            
            # Count verb uses
            if lemma in concept['verb_lemmas'] and upos == 'VERB':
                verb_count += 1
            
            # Count noun uses
            if lemma in concept['noun_lemmas'] and upos == 'NOUN':
                noun_count += 1
                
                # Check if this noun is in a copula construction
                head_id = token['head']
                if head_id in token_map:
                    head = token_map[head_id]
                    has_cop = any(t['deprel'] == 'cop' and t['head'] == head_id for t in sent)
                    if has_cop and token['deprel'] == 'nsubj':
                        in_cop_construction += 1
            
            # Track -ing forms specifically
            if form in concept.get('ing_forms', []):
                if upos == 'NOUN':
                    ing_as_noun += 1
                elif upos in ('VERB', 'ADJ'):
                    ing_as_verb += 1
    
    total = verb_count + noun_count
    if total > 0:
        noun_ratio = noun_count / total
        en_results[concept_name] = {
            'type': concept['type'],
            'verb': verb_count,
            'noun': noun_count,
            'total': total,
            'noun_ratio': noun_ratio,
            'ing_as_noun': ing_as_noun,
            'ing_as_verb': ing_as_verb,
            'in_cop': in_cop_construction,
        }

# Print English results
print("\n" + "=" * 100)
print("ENGLISH: Verb vs Noun Usage for Abstract & Concrete Concepts")
print("=" * 100)
print(f"{'Concept':<15} {'Type':<10} {'Verb':<8} {'Noun':<8} {'Total':<8} {'Noun%':<8} {'ing→N':<8} {'ing→V':<8} {'InCop':<8}")
print("-" * 95)

invisible = [(k, v) for k, v in en_results.items() if v['type'] == 'invisible']
visible = [(k, v) for k, v in en_results.items() if v['type'] == 'visible']

print("--- INVISIBLE PROCESSES ---")
for name, r in sorted(invisible, key=lambda x: -x[1]['noun_ratio']):
    print(f"{name:<15} {r['type']:<10} {r['verb']:<8} {r['noun']:<8} {r['total']:<8} {r['noun_ratio']:<8.1%} {r['ing_as_noun']:<8} {r['ing_as_verb']:<8} {r['in_cop']:<8}")

print("\n--- VISIBLE PROCESSES ---")
for name, r in sorted(visible, key=lambda x: -x[1]['noun_ratio']):
    print(f"{name:<15} {r['type']:<10} {r['verb']:<8} {r['noun']:<8} {r['total']:<8} {r['noun_ratio']:<8.1%} {r['ing_as_noun']:<8} {r['ing_as_verb']:<8} {r['in_cop']:<8}")

# Aggregate comparison
print("\n" + "=" * 100)
print("AGGREGATE: Invisible vs Visible Processes")
print("=" * 100)

inv_total_v = sum(v['verb'] for _, v in invisible)
inv_total_n = sum(v['noun'] for _, v in invisible)
vis_total_v = sum(v['verb'] for _, v in visible)
vis_total_n = sum(v['noun'] for _, v in visible)
inv_cop = sum(v['in_cop'] for _, v in invisible)
vis_cop = sum(v['in_cop'] for _, v in visible)
inv_ing_n = sum(v['ing_as_noun'] for _, v in invisible)
inv_ing_v = sum(v['ing_as_verb'] for _, v in invisible)
vis_ing_n = sum(v['ing_as_noun'] for _, v in visible)
vis_ing_v = sum(v['ing_as_verb'] for _, v in visible)

inv_ratio = inv_total_n / (inv_total_v + inv_total_n) if (inv_total_v + inv_total_n) > 0 else 0
vis_ratio = vis_total_n / (vis_total_v + vis_total_n) if (vis_total_v + vis_total_n) > 0 else 0

print(f"\n{'Category':<25} {'Verb':<10} {'Noun':<10} {'Total':<10} {'Noun%':<10} {'InCop':<10} {'ing→N':<10} {'ing→V':<10}")
print("-" * 95)
print(f"{'INVISIBLE processes':<25} {inv_total_v:<10} {inv_total_n:<10} {inv_total_v+inv_total_n:<10} {inv_ratio:<10.1%} {inv_cop:<10} {inv_ing_n:<10} {inv_ing_v:<10}")
print(f"{'VISIBLE processes':<25} {vis_total_v:<10} {vis_total_n:<10} {vis_total_v+vis_total_n:<10} {vis_ratio:<10.1%} {vis_cop:<10} {vis_ing_n:<10} {vis_ing_v:<10}")
print(f"{'Ratio (inv/vis)':<25} {'':10} {'':10} {'':10} {inv_ratio/vis_ratio if vis_ratio > 0 else 'N/A':<10.2f}")

# ============================================================
# Japanese Analysis (simplified)
# ============================================================
print("\n\n" + "=" * 100)
print("JAPANESE: Verb vs Noun Usage")
print("=" * 100)

ja_sents = parse_conllu_detailed('ud_data/ja.conllu')

print(f"\n{'Concept':<15} {'Type':<10} {'Verb':<8} {'Noun':<8} {'Total':<8} {'Noun%':<8}")
print("-" * 60)

ja_inv_v, ja_inv_n = 0, 0
ja_vis_v, ja_vis_n = 0, 0

for concept_name, concept in ja_concepts.items():
    verb_count = 0
    noun_count = 0
    
    for sent in ja_sents:
        for token in sent:
            if token['lemma'] in concept['verb_lemmas'] and token['upos'] == 'VERB':
                verb_count += 1
            if token['lemma'] in concept['noun_lemmas'] and token['upos'] == 'NOUN':
                noun_count += 1
    
    total = verb_count + noun_count
    if total > 0:
        ratio = noun_count / total
        print(f"{concept_name:<15} {concept['type']:<10} {verb_count:<8} {noun_count:<8} {total:<8} {ratio:<8.1%}")
        
        if concept['type'] == 'invisible':
            ja_inv_v += verb_count
            ja_inv_n += noun_count
        else:
            ja_vis_v += verb_count
            ja_vis_n += noun_count

ja_inv_ratio = ja_inv_n / (ja_inv_v + ja_inv_n) if (ja_inv_v + ja_inv_n) > 0 else 0
ja_vis_ratio = ja_vis_n / (ja_vis_v + ja_vis_n) if (ja_vis_v + ja_vis_n) > 0 else 0

print(f"\n{'INVISIBLE (JA)':<25} {ja_inv_v:<10} {ja_inv_n:<10} {ja_inv_v+ja_inv_n:<10} {ja_inv_ratio:<10.1%}")
print(f"{'VISIBLE (JA)':<25} {ja_vis_v:<10} {ja_vis_n:<10} {ja_vis_v+ja_vis_n:<10} {ja_vis_ratio:<10.1%}")

# ============================================================
# Cross-linguistic comparison
# ============================================================
print("\n\n" + "=" * 100)
print("CROSS-LINGUISTIC COMPARISON: English vs Japanese")
print("=" * 100)

print(f"\n{'Metric':<40} {'English':<15} {'Japanese':<15}")
print("-" * 70)
print(f"{'Invisible: Noun ratio':<40} {inv_ratio:<15.1%} {ja_inv_ratio:<15.1%}")
print(f"{'Visible: Noun ratio':<40} {vis_ratio:<15.1%} {ja_vis_ratio:<15.1%}")
print(f"{'Invisible/Visible gap':<40} {inv_ratio - vis_ratio:<15.1%} {ja_inv_ratio - ja_vis_ratio:<15.1%}")

print("""
\n*** KEY OBSERVATION ***

If invisible processes show HIGHER noun ratios than visible processes,
this confirms: nominalization bias is SELECTIVE — it targets invisible 
processes more than visible ones.

If English shows a LARGER invisible/visible gap than Japanese,
this confirms: the copula construction amplifies the nominalization bias.

The -ing form analysis is critical:
- English HAS the -ing form (loving, thinking, knowing)
- But -ing forms used AS NOUNS vs AS VERBS tells us whether 
  even processual morphology gets co-opted into nominal function
""")

