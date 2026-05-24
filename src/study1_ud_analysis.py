#!/usr/bin/env python3
"""
Study 1: WALS Copula Typology × UD Nominalization Frequency
Analysis of copula usage patterns and nominalization ratios across languages
"""

import os
import csv
import json
from collections import defaultdict

def parse_conllu(filepath):
    """Parse CoNLL-U file and extract POS tags, dependency relations, and features."""
    stats = defaultdict(int)
    cop_constructions = []
    
    current_sentence = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            if line == '':
                # Process sentence
                if current_sentence:
                    process_sentence(current_sentence, stats, cop_constructions)
                current_sentence = []
                continue
            
            parts = line.split('\t')
            if len(parts) != 10:
                continue
            # Skip multi-word tokens and empty nodes
            if '-' in parts[0] or '.' in parts[0]:
                continue
            
            current_sentence.append({
                'id': parts[0],
                'form': parts[1],
                'lemma': parts[2],
                'upos': parts[3],
                'xpos': parts[4],
                'feats': parts[5],
                'head': parts[6],
                'deprel': parts[7],
                'deps': parts[8],
                'misc': parts[9]
            })
    
    # Process last sentence
    if current_sentence:
        process_sentence(current_sentence, stats, cop_constructions)
    
    return stats, cop_constructions

def process_sentence(tokens, stats, cop_constructions):
    """Process a single sentence for statistics."""
    stats['total_tokens'] += len(tokens)
    stats['total_sentences'] += 1
    
    token_map = {t['id']: t for t in tokens}
    
    for token in tokens:
        upos = token['upos']
        deprel = token['deprel'].split(':')[0]  # Get base relation
        feats = token['feats']
        
        # Count POS tags
        stats[f'pos_{upos}'] += 1
        
        # Count dependency relations
        stats[f'dep_{deprel}'] += 1
        
        # Count copula relations specifically
        if deprel == 'cop':
            stats['copula_count'] += 1
            # Find what the copula is attached to
            head_id = token['head']
            if head_id in token_map:
                head = token_map[head_id]
                stats[f'cop_head_pos_{head["upos"]}'] += 1
        
        # Count verbal nouns / nominalized forms
        if feats != '_':
            feat_dict = dict(f.split('=') for f in feats.split('|') if '=' in f)
            
            if upos == 'NOUN':
                # Check for verbal features on nouns (nominalization markers)
                if 'VerbForm' in feat_dict:
                    stats['verbal_noun'] += 1
                if 'Derivation' in feat_dict:
                    stats['derived_noun'] += 1
                    
            if 'VerbForm' in feat_dict:
                stats[f'verbform_{feat_dict["VerbForm"]}'] += 1
        
        # Count abstract noun patterns (nouns as nsubj of cop constructions)
        if deprel == 'nsubj':
            head_id = token['head']
            if head_id in token_map:
                head = token_map[head_id]
                # Check if this nsubj's head has a cop dependent
                has_cop = any(t['deprel'].split(':')[0] == 'cop' and t['head'] == head_id 
                           for t in tokens)
                if has_cop and upos == 'NOUN':
                    stats['noun_as_cop_subject'] += 1

# Language metadata
lang_info = {
    'en': {'name': 'English', 'family': 'Indo-European', 'branch': 'Germanic'},
    'de': {'name': 'German', 'family': 'Indo-European', 'branch': 'Germanic'},
    'fr': {'name': 'French', 'family': 'Indo-European', 'branch': 'Romance'},
    'es': {'name': 'Spanish', 'family': 'Indo-European', 'branch': 'Romance'},
    'it': {'name': 'Italian', 'family': 'Indo-European', 'branch': 'Romance'},
    'pt': {'name': 'Portuguese', 'family': 'Indo-European', 'branch': 'Romance'},
    'ru': {'name': 'Russian', 'family': 'Indo-European', 'branch': 'Slavic'},
    'hi': {'name': 'Hindi', 'family': 'Indo-European', 'branch': 'Indo-Aryan'},
    'ja': {'name': 'Japanese', 'family': 'Japonic', 'branch': 'Japonic'},
    'ko': {'name': 'Korean', 'family': 'Koreanic', 'branch': 'Koreanic'},
    'zh': {'name': 'Chinese', 'family': 'Sino-Tibetan', 'branch': 'Sinitic'},
    'tr': {'name': 'Turkish', 'family': 'Turkic', 'branch': 'Oghuz'},
    'fi': {'name': 'Finnish', 'family': 'Uralic', 'branch': 'Finnic'},
    'ar': {'name': 'Arabic', 'family': 'Afro-Asiatic', 'branch': 'Semitic'},
    'id': {'name': 'Indonesian', 'family': 'Austronesian', 'branch': 'Malayo-Polynesian'},
}

# WALS 119A and 120A data (from our earlier extraction)
wals_data = {
    'en': {'119A': 'Shared', '120A': 'Required'},      # English: same copula for all
    'de': {'119A': 'Split', '120A': 'Required'},         # German (Viennese proxy)
    'fr': {'119A': 'Split', '120A': 'Required'},         # French (estimated from Romance pattern)
    'es': {'119A': 'Split', '120A': 'Required'},         # Spanish: ser/estar split
    'it': {'119A': 'Split', '120A': 'Required'},         # Italian (Turinese proxy)
    'pt': {'119A': 'Split', '120A': 'Required'},         # Portuguese (estimated)
    'ru': {'119A': 'Shared', '120A': 'Zero OK'},         # Russian: zero copula in present
    'hi': {'119A': 'Shared', '120A': 'Required'},        # Hindi
    'ja': {'119A': 'Split', '120A': 'Required'},         # Japanese: だ vs いる/ある
    'ko': {'119A': 'Split', '120A': 'Required'},         # Korean: 이다 vs 있다
    'zh': {'119A': 'Split', '120A': 'Zero OK'},          # Chinese: partial zero copula
    'tr': {'119A': 'Shared', '120A': 'Required'},        # Turkish
    'fi': {'119A': 'Shared', '120A': 'Required'},        # Finnish
    'ar': {'119A': 'Split', '120A': 'Zero OK'},          # Arabic: zero copula in present
    'id': {'119A': 'Split', '120A': 'Zero OK'},          # Indonesian
}

print("=" * 100)
print("Study 1: WALS Copula Typology × UD Nominalization Patterns")
print("=" * 100)

results = []

for lang_code in sorted(lang_info.keys()):
    filepath = f'ud_data/{lang_code}.conllu'
    if not os.path.exists(filepath) or os.path.getsize(filepath) < 100:
        continue
    
    info = lang_info[lang_code]
    wals = wals_data.get(lang_code, {})
    
    print(f"\nProcessing {info['name']} ({lang_code})...")
    stats, cops = parse_conllu(filepath)
    
    total = stats['total_tokens']
    if total == 0:
        continue
    
    nouns = stats.get('pos_NOUN', 0)
    verbs = stats.get('pos_VERB', 0)
    adjs = stats.get('pos_ADJ', 0)
    aux = stats.get('pos_AUX', 0)
    cop_count = stats.get('copula_count', 0)
    noun_cop_subj = stats.get('noun_as_cop_subject', 0)
    
    # Key metrics
    noun_verb_ratio = nouns / verbs if verbs > 0 else 0
    cop_rate = cop_count / total * 1000  # per 1000 tokens
    cop_subj_rate = noun_cop_subj / total * 1000
    
    result = {
        'lang': lang_code,
        'name': info['name'],
        'family': info['family'],
        'branch': info['branch'],
        '119A': wals.get('119A', '?'),
        '120A': wals.get('120A', '?'),
        'total_tokens': total,
        'nouns': nouns,
        'verbs': verbs,
        'noun_verb_ratio': round(noun_verb_ratio, 3),
        'cop_rate': round(cop_rate, 2),
        'cop_subj_rate': round(cop_subj_rate, 2),
        'cop_head_NOUN': stats.get('cop_head_pos_NOUN', 0),
        'cop_head_ADJ': stats.get('cop_head_pos_ADJ', 0),
        'cop_head_VERB': stats.get('cop_head_pos_VERB', 0),
        'verbal_noun': stats.get('verbal_noun', 0),
    }
    results.append(result)

# Print results table
print("\n" + "=" * 100)
print("RESULTS TABLE")
print("=" * 100)
print(f"{'Language':<12} {'Family':<16} {'119A':<8} {'120A':<10} {'N/V Ratio':<10} {'Cop/1k':<8} {'CopSubj/1k':<12} {'Tokens':<10}")
print("-" * 100)

for r in sorted(results, key=lambda x: x['cop_rate'], reverse=True):
    print(f"{r['name']:<12} {r['family']:<16} {r['119A']:<8} {r['120A']:<10} {r['noun_verb_ratio']:<10} {r['cop_rate']:<8} {r['cop_subj_rate']:<12} {r['total_tokens']:<10}")

# Analysis by copula type
print("\n" + "=" * 100)
print("ANALYSIS BY WALS 119A (Nominal/Locational Predication)")
print("=" * 100)

shared = [r for r in results if r['119A'] == 'Shared']
split = [r for r in results if r['119A'] == 'Split']

if shared and split:
    avg_cop_shared = sum(r['cop_rate'] for r in shared) / len(shared)
    avg_cop_split = sum(r['cop_rate'] for r in split) / len(split)
    avg_nv_shared = sum(r['noun_verb_ratio'] for r in shared) / len(shared)
    avg_nv_split = sum(r['noun_verb_ratio'] for r in split) / len(split)
    avg_copsubj_shared = sum(r['cop_subj_rate'] for r in shared) / len(shared)
    avg_copsubj_split = sum(r['cop_subj_rate'] for r in split) / len(split)
    
    print(f"\n{'Metric':<25} {'Shared (fused)':<18} {'Split (separate)':<18} {'Ratio':<10}")
    print("-" * 75)
    print(f"{'Copula rate (per 1k)':<25} {avg_cop_shared:<18.2f} {avg_cop_split:<18.2f} {avg_cop_shared/avg_cop_split if avg_cop_split > 0 else 'N/A':<10.2f}")
    print(f"{'Noun/Verb ratio':<25} {avg_nv_shared:<18.3f} {avg_nv_split:<18.3f} {avg_nv_shared/avg_nv_split if avg_nv_split > 0 else 'N/A':<10.2f}")
    print(f"{'CopSubj rate (per 1k)':<25} {avg_copsubj_shared:<18.2f} {avg_copsubj_split:<18.2f} {avg_copsubj_shared/avg_copsubj_split if avg_copsubj_split > 0 else 'N/A':<10.2f}")
    
    print(f"\nShared languages: {', '.join(r['name'] for r in shared)}")
    print(f"Split languages: {', '.join(r['name'] for r in split)}")

print("\n" + "=" * 100)
print("ANALYSIS BY WALS 120A (Zero Copula)")  
print("=" * 100)

required = [r for r in results if r['120A'] == 'Required']
zero_ok = [r for r in results if r['120A'] == 'Zero OK']

if required and zero_ok:
    avg_cop_req = sum(r['cop_rate'] for r in required) / len(required)
    avg_cop_zero = sum(r['cop_rate'] for r in zero_ok) / len(zero_ok)
    avg_nv_req = sum(r['noun_verb_ratio'] for r in required) / len(required)
    avg_nv_zero = sum(r['noun_verb_ratio'] for r in zero_ok) / len(zero_ok)
    
    print(f"\n{'Metric':<25} {'Required':<18} {'Zero OK':<18} {'Ratio':<10}")
    print("-" * 75)
    print(f"{'Copula rate (per 1k)':<25} {avg_cop_req:<18.2f} {avg_cop_zero:<18.2f} {avg_cop_req/avg_cop_zero if avg_cop_zero > 0 else 'N/A':<10.2f}")
    print(f"{'Noun/Verb ratio':<25} {avg_nv_req:<18.3f} {avg_nv_zero:<18.3f} {avg_nv_req/avg_nv_zero if avg_nv_zero > 0 else 'N/A':<10.2f}")

# Copula head analysis
print("\n" + "=" * 100)
print("COPULA HEAD POS DISTRIBUTION (what follows the copula)")
print("=" * 100)
print(f"{'Language':<12} {'cop→NOUN':<12} {'cop→ADJ':<12} {'cop→VERB':<12} {'NOUN%':<10}")
print("-" * 60)
for r in sorted(results, key=lambda x: x['cop_rate'], reverse=True):
    total_cop_heads = r['cop_head_NOUN'] + r['cop_head_ADJ'] + r['cop_head_VERB']
    noun_pct = r['cop_head_NOUN'] / total_cop_heads * 100 if total_cop_heads > 0 else 0
    print(f"{r['name']:<12} {r['cop_head_NOUN']:<12} {r['cop_head_ADJ']:<12} {r['cop_head_VERB']:<12} {noun_pct:<10.1f}%")

# Save results
with open('study1_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nResults saved to study1_results.json")

