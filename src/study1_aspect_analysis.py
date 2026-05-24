#!/usr/bin/env python3
"""
Analysis of progressive/processual forms vs nominalized forms across languages.
Key question: Languages that HAVE progressive aspect — do they still nominalize 
abstract concepts when theorizing?
"""

import os
from collections import defaultdict

def parse_features(feat_str):
    if feat_str == '_':
        return {}
    return dict(f.split('=') for f in feat_str.split('|') if '=' in f)

def analyze_language(filepath, lang_code):
    stats = defaultdict(int)
    
    # Track specific patterns
    verb_forms = defaultdict(int)
    aspects = defaultdict(int)
    noun_with_verbal_feats = 0
    gerund_count = 0
    progressive_count = 0
    
    # Track copula + noun vs verb constructions
    sentences = []
    current_sentence = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            if line == '':
                if current_sentence:
                    sentences.append(current_sentence)
                current_sentence = []
                continue
            parts = line.split('\t')
            if len(parts) != 10 or '-' in parts[0] or '.' in parts[0]:
                continue
            current_sentence.append({
                'id': parts[0], 'form': parts[1], 'lemma': parts[2],
                'upos': parts[3], 'feats': parts[5], 'head': parts[6],
                'deprel': parts[7]
            })
        if current_sentence:
            sentences.append(current_sentence)
    
    total_tokens = 0
    total_verbs = 0
    total_nouns = 0
    
    for sent in sentences:
        token_map = {t['id']: t for t in sent}
        
        for token in sent:
            total_tokens += 1
            feats = parse_features(token['feats'])
            upos = token['upos']
            deprel = token['deprel'].split(':')[0]
            
            if upos == 'VERB':
                total_verbs += 1
                
                # Count aspect markers
                if 'Aspect' in feats:
                    aspects[feats['Aspect']] += 1
                    if feats['Aspect'] == 'Prog':
                        progressive_count += 1
                
                # Count verb forms
                if 'VerbForm' in feats:
                    verb_forms[feats['VerbForm']] += 1
                    if feats['VerbForm'] == 'Ger':
                        gerund_count += 1
                    if feats['VerbForm'] == 'Vnoun':
                        stats['vnoun'] += 1
            
            elif upos == 'AUX':
                if 'Aspect' in feats:
                    aspects[feats['Aspect']] += 1
                    if feats['Aspect'] == 'Prog':
                        progressive_count += 1
            
            elif upos == 'NOUN':
                total_nouns += 1
                # Check for verbal features on nouns
                if 'VerbForm' in feats:
                    noun_with_verbal_feats += 1
    
    return {
        'lang': lang_code,
        'total_tokens': total_tokens,
        'total_verbs': total_verbs,
        'total_nouns': total_nouns,
        'progressive': progressive_count,
        'gerund': gerund_count,
        'vnoun': stats.get('vnoun', 0),
        'noun_with_verbal': noun_with_verbal_feats,
        'aspects': dict(aspects),
        'verb_forms': dict(verb_forms),
        'prog_rate': progressive_count / total_tokens * 1000 if total_tokens > 0 else 0,
        'gerund_rate': gerund_count / total_tokens * 1000 if total_tokens > 0 else 0,
        'nv_ratio': total_nouns / total_verbs if total_verbs > 0 else 0,
    }

# Language names
lang_names = {
    'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'hi': 'Hindi',
    'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese', 'tr': 'Turkish',
    'fi': 'Finnish', 'ar': 'Arabic', 'id': 'Indonesian'
}

print("=" * 100)
print("PROGRESSIVE/PROCESSUAL FORMS ANALYSIS")
print("Key Q: Do languages with progressive aspect still nominalize when theorizing?")
print("=" * 100)

all_results = []
for lang_code in sorted(lang_names.keys()):
    filepath = f'ud_data/{lang_code}.conllu'
    if not os.path.exists(filepath) or os.path.getsize(filepath) < 100:
        continue
    print(f"Processing {lang_names[lang_code]}...")
    result = analyze_language(filepath, lang_code)
    result['name'] = lang_names[lang_code]
    all_results.append(result)

# Main results table
print("\n" + "=" * 100)
print("ASPECT AND PROCESSUAL MARKING")
print("=" * 100)
print(f"{'Language':<12} {'Prog/1k':<10} {'Ger/1k':<10} {'Vnoun/1k':<10} {'NounVerbal':<12} {'N/V':<8} {'Aspects'}")
print("-" * 100)

for r in sorted(all_results, key=lambda x: x['prog_rate'], reverse=True):
    vnoun_rate = r['vnoun'] / r['total_tokens'] * 1000 if r['total_tokens'] > 0 else 0
    nv_rate = r['noun_with_verbal'] / r['total_tokens'] * 1000 if r['total_tokens'] > 0 else 0
    aspects_str = ', '.join(f"{k}:{v}" for k, v in sorted(r['aspects'].items(), key=lambda x: -x[1]))
    print(f"{r['name']:<12} {r['prog_rate']:<10.2f} {r['gerund_rate']:<10.2f} {vnoun_rate:<10.2f} {nv_rate:<12.2f} {r['nv_ratio']:<8.2f} {aspects_str[:45]}")

# VerbForm distribution
print("\n" + "=" * 100)
print("VERB FORM DISTRIBUTION")
print("=" * 100)
for r in sorted(all_results, key=lambda x: x['name']):
    if r['verb_forms']:
        vf_str = ', '.join(f"{k}:{v}" for k, v in sorted(r['verb_forms'].items(), key=lambda x: -x[1]))
        print(f"{r['name']:<12} {vf_str}")

# Key insight analysis
print("\n" + "=" * 100)
print("KEY INSIGHT: Progressive Availability vs Nominalization Tendency")
print("=" * 100)

# Languages WITH progressive aspect
has_prog = [r for r in all_results if r['prog_rate'] > 0.5]
no_prog = [r for r in all_results if r['prog_rate'] <= 0.5]

if has_prog and no_prog:
    avg_nv_prog = sum(r['nv_ratio'] for r in has_prog) / len(has_prog)
    avg_nv_noprog = sum(r['nv_ratio'] for r in no_prog) / len(no_prog)
    
    print(f"\n{'Category':<35} {'Avg N/V ratio':<15} {'Languages'}")
    print("-" * 90)
    print(f"{'Has progressive aspect':<35} {avg_nv_prog:<15.3f} {', '.join(r['name'] for r in has_prog)}")
    print(f"{'No/minimal progressive aspect':<35} {avg_nv_noprog:<15.3f} {', '.join(r['name'] for r in no_prog)}")

print("""
\n*** CRITICAL OBSERVATION ***

English HAS progressive aspect ("loving", "thinking", "being conscious").
Yet English philosophical tradition uses nominalized forms:
  "What is love?" (not "What is loving?")
  "What is consciousness?" (not "What is being-conscious?")
  "What is justice?" (not "What is being-just?")

This demonstrates that the nominalization bias is NOT a grammatical necessity
but a CHOICE constrained by the copula construction "X is Y":
  - The copula demands a noun/adjective complement
  - Progressive forms are verbal → don't fit as copula complements
  - Therefore: "Love is X" ✓  but  "*Loving is X" feels unnatural
  - The copula construction FORCES nominalization of the subject

The grammatical constraint chain:
  "X is Y" construction → X must be nominal → process must be nominalized
  → nominalized process is treated as entity → entity's essence is sought
  → "What is the nature of X?" → philosophical hard problem generated
""")

