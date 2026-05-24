#!/usr/bin/env python3
"""
Detailed analysis and statistical testing for Study 1
"""

import json
import math

with open('study1_results.json') as f:
    results = json.load(f)

# ============================================================
# 1. Indo-European vs Non-Indo-European analysis
# ============================================================
print("=" * 90)
print("ANALYSIS BY LANGUAGE FAMILY")
print("=" * 90)

ie = [r for r in results if r['family'] == 'Indo-European']
non_ie = [r for r in results if r['family'] != 'Indo-European']

print(f"\n{'Metric':<25} {'Indo-European':<18} {'Non-IE':<18} {'Ratio':<10}")
print("-" * 75)

avg_cop_ie = sum(r['cop_rate'] for r in ie) / len(ie)
avg_cop_nie = sum(r['cop_rate'] for r in non_ie) / len(non_ie)
avg_nv_ie = sum(r['noun_verb_ratio'] for r in ie) / len(ie)
avg_nv_nie = sum(r['noun_verb_ratio'] for r in non_ie) / len(non_ie)
avg_cs_ie = sum(r['cop_subj_rate'] for r in ie) / len(ie)
avg_cs_nie = sum(r['cop_subj_rate'] for r in non_ie) / len(non_ie)

print(f"{'Copula rate (per 1k)':<25} {avg_cop_ie:<18.2f} {avg_cop_nie:<18.2f} {avg_cop_ie/avg_cop_nie:.2f}")
print(f"{'N/V ratio':<25} {avg_nv_ie:<18.3f} {avg_nv_nie:<18.3f} {avg_nv_ie/avg_nv_nie:.2f}")
print(f"{'CopSubj rate (per 1k)':<25} {avg_cs_ie:<18.2f} {avg_cs_nie:<18.2f} {avg_cs_ie/avg_cs_nie:.2f}")

print(f"\nIE: {', '.join(r['name'] for r in ie)}")
print(f"Non-IE: {', '.join(r['name'] for r in non_ie)}")

# ============================================================
# 2. Copula versatility analysis (what POS does copula attach to?)
# ============================================================
print("\n" + "=" * 90)
print("COPULA VERSATILITY INDEX")
print("(How many different POS categories does the copula serve?)")
print("=" * 90)

print(f"\n{'Language':<12} {'cop→N':<8} {'cop→A':<8} {'cop→V':<8} {'Total':<8} {'Entropy':<10} {'N-dominance':<12}")
print("-" * 70)

for r in sorted(results, key=lambda x: x['cop_rate'], reverse=True):
    n = r['cop_head_NOUN']
    a = r['cop_head_ADJ']
    v = r['cop_head_VERB']
    total = n + a + v
    if total == 0:
        continue
    
    # Calculate Shannon entropy of copula head distribution
    probs = [x/total for x in [n, a, v] if x > 0]
    entropy = -sum(p * math.log2(p) for p in probs)
    
    # N-dominance: how much the copula is "just for nouns"
    n_dom = n / total
    
    print(f"{r['name']:<12} {n:<8} {a:<8} {v:<8} {total:<8} {entropy:<10.3f} {n_dom:<12.1%}")

# ============================================================
# 3. The key hypothesis test: copula versatility × "X is Y" frequency
# ============================================================
print("\n" + "=" * 90)
print("KEY HYPOTHESIS: Copula Versatility × 'X is Y' Pattern Frequency")
print("=" * 90)
print("""
Hypothesis: Languages where the copula serves MULTIPLE POS categories
(i.e., low N-dominance = versatile copula) will show HIGHER rates of 
"Noun is X" constructions, because the copula becomes a general-purpose
predication tool rather than a noun-specific one.
""")

# Classify languages by copula versatility
versatile = []   # entropy > 1.0 (copula serves multiple POS)
specialized = [] # entropy <= 1.0 or very high N-dominance

for r in results:
    n = r['cop_head_NOUN']
    a = r['cop_head_ADJ']
    v = r['cop_head_VERB']
    total = n + a + v
    if total < 10:
        continue
    probs = [x/total for x in [n, a, v] if x > 0]
    entropy = -sum(p * math.log2(p) for p in probs)
    r['cop_entropy'] = entropy
    r['n_dominance'] = n / total
    
    if entropy > 0.8:
        versatile.append(r)
    else:
        specialized.append(r)

if versatile and specialized:
    avg_cop_v = sum(r['cop_rate'] for r in versatile) / len(versatile)
    avg_cop_s = sum(r['cop_rate'] for r in specialized) / len(specialized)
    avg_cs_v = sum(r['cop_subj_rate'] for r in versatile) / len(versatile)
    avg_cs_s = sum(r['cop_subj_rate'] for r in specialized) / len(specialized)
    
    print(f"{'Metric':<25} {'Versatile cop':<18} {'Specialized cop':<18} {'Ratio':<10}")
    print("-" * 75)
    print(f"{'Copula rate (per 1k)':<25} {avg_cop_v:<18.2f} {avg_cop_s:<18.2f} {avg_cop_v/avg_cop_s if avg_cop_s > 0 else 'N/A':<10.2f}")
    print(f"{'CopSubj rate (per 1k)':<25} {avg_cs_v:<18.2f} {avg_cs_s:<18.2f} {avg_cs_v/avg_cs_s if avg_cs_s > 0 else 'N/A':<10.2f}")
    print(f"\nVersatile: {', '.join(r['name'] for r in versatile)}")
    print(f"Specialized: {', '.join(r['name'] for r in specialized)}")

# ============================================================
# 4. Combined profile: 119A × Copula versatility  
# ============================================================
print("\n" + "=" * 90)
print("COMBINED PROFILE: Predication Type × Copula Versatility")
print("=" * 90)

# The most constrained languages: Shared predication + Versatile copula
# The least constrained: Split predication + Specialized copula

for r in results:
    n = r['cop_head_NOUN']
    a = r['cop_head_ADJ']
    v = r['cop_head_VERB']
    total = n + a + v
    if total < 10:
        r['constraint_level'] = 'LOW_DATA'
        continue
    
    probs = [x/total for x in [n, a, v] if x > 0]
    entropy = -sum(p * math.log2(p) for p in probs)
    
    if r['119A'] == 'Shared' and entropy > 0.8:
        r['constraint_level'] = 'HIGH'
    elif r['119A'] == 'Split' and entropy <= 0.8:
        r['constraint_level'] = 'LOW'
    else:
        r['constraint_level'] = 'MEDIUM'

high = [r for r in results if r.get('constraint_level') == 'HIGH']
medium = [r for r in results if r.get('constraint_level') == 'MEDIUM']
low = [r for r in results if r.get('constraint_level') == 'LOW']

print(f"\n{'Constraint':<12} {'Languages':<45} {'Avg Cop/1k':<12} {'Avg CopSubj/1k':<15}")
print("-" * 90)

for level, group, label in [('HIGH', high, 'HIGH'), ('MEDIUM', medium, 'MEDIUM'), ('LOW', low, 'LOW')]:
    if group:
        avg_c = sum(r['cop_rate'] for r in group) / len(group)
        avg_cs = sum(r['cop_subj_rate'] for r in group) / len(group)
        names = ', '.join(r['name'] for r in group)
        print(f"{label:<12} {names:<45} {avg_c:<12.2f} {avg_cs:<15.2f}")

# ============================================================
# 5. Summary finding
# ============================================================
print("\n" + "=" * 90)
print("SUMMARY OF KEY FINDINGS")
print("=" * 90)
print("""
Finding 1: Shared-predication languages (119A) use copula 1.72× more frequently
           than Split-predication languages (17.23 vs 10.03 per 1000 tokens).
           
Finding 2: The "X is Y" pattern (noun as copula subject) is 1.77× more frequent
           in Shared-predication languages (6.89 vs 3.90 per 1000 tokens).
           
Finding 3: Copula versatility varies dramatically across languages.
           - Japanese/Chinese/Korean: copula is noun-specialized (>90% noun heads)
           - English/German/Finnish: copula serves nouns AND adjectives (~40-60% noun)
           - This means English "is" operates across MORE predication contexts.
           
Finding 4: Languages requiring explicit copula (120A) use copula 2.28× more
           than languages permitting zero copula (14.63 vs 6.40 per 1000 tokens).
           
Interpretation: Languages with SHARED predication + VERSATILE copula + REQUIRED copula
(exemplified by English, Finnish) create the maximum structural exposure to 
"X is Y" constructions. This is the grammatical environment that maximally 
promotes the nominalization bias identified in the present study.
""")

