"""Script to build and validate the 200 hand-annotated gold POS dataset.

Penn Treebank tag guidelines followed:
- VB: Base form verb (imperative: 'add', 'fix', 'update', 'remove')
- VBD: Past tense verb ('added', 'fixed', 'updated')
- VBG: Present participle / gerund ('adding', 'fixing', 'updating')
- VBN: Past participle ('deprecated', 'removed' in passive)
- VBZ: 3rd person singular present ('fixes', 'adds', 'updates')
- VBP: Non-3rd person singular present ('fix', 'do')
- NN: Singular noun ('login', 'issue', 'bug', 'patch', 'repo')
- NNS: Plural noun ('issues', 'tests', 'files', 'methods')
- NNP: Singular proper noun ('Python', 'Docker', 'GitHub', 'UserProfileSerializer')
- NNPS: Plural proper noun ('APIs')
- JJ: Adjective ('new', 'initial', 'deprecated', 'optional', 'internal')
- JJR: Comparative adjective ('better', 'faster')
- JJS: Superlative adjective ('best', 'cleanest')
- RB: Adverb ('always', 'lazily', 'correctly', 'not')
- RBR: Comparative adverb ('better', 'more')
- IN: Preposition / subordinating conjunction ('in', 'for', 'to', 'from', 'with', 'when')
- TO: Infinitive marker / preposition ('to')
- DT: Determiner ('the', 'a', 'an', 'this', 'all')
- CD: Cardinal number ('1', '2', '404', '1.2.3')
- RP: Particle in phrasal verbs ('up', 'out', 'off', 'down')
- MD: Modal ('can', 'should', 'will', 'must')
- PRP: Personal pronoun ('it', 'them', 'we')
- PRP$: Possessive pronoun ('its', 'their')
- CC: Coordinating conjunction ('and', 'or', 'but')
- POS: Possessive marker ("'s")
- FW: Foreign word
- SYM: Symbol ('+', '-', '=')
"""
from __future__ import annotations

import json
from pathlib import Path

VALID_PTB_TAGS = {
    "CC", "CD", "DT", "EX", "FW", "IN", "JJ", "JJR", "JJS", "LS", "MD",
    "NN", "NNS", "NNP", "NNPS", "PDT", "POS", "PRP", "PRP$", "RB", "RBR",
    "RBS", "RP", "SYM", "TO", "UH", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
    "WDT", "WP", "WP$", "WRB", ".", ",", ":", "(", ")", "''", "``", "$", "#"
}

def validate_and_write_gold():
    # Load gold records
    from scripts.gold_data import GOLD_RECORDS
    
    assert len(GOLD_RECORDS) == 200, f"Expected 200 records, got {len(GOLD_RECORDS)}"
    
    gold_file = Path("data/gold/pos_gold.jsonl")
    gold_file.parent.mkdir(parents=True, exist_ok=True)
    
    unsure_count = 0
    first_tag_dist = {}
    
    with open(gold_file, "w", encoding="utf-8") as f:
        for i, rec in enumerate(GOLD_RECORDS, 1):
            assert rec["id"] == i, f"Record id mismatch at {i}: {rec['id']}"
            assert len(rec["tokens"]) == len(rec["tags"]), (
                f"ID {i} ('{rec['title']}'): tokens length {len(rec['tokens'])} "
                f"!= tags length {len(rec['tags'])}"
            )
            for t in rec["tags"]:
                assert t in VALID_PTB_TAGS, f"ID {i} ('{rec['title']}'): invalid PTB tag '{t}'"
            assert rec["first_tag"] == rec["tags"][0], (
                f"ID {i} ('{rec['title']}'): first_tag '{rec['first_tag']}' != tags[0] '{rec['tags'][0]}'"
            )
            expected_imp = (rec["first_tag"] == "VB")
            assert rec["is_imperative"] == expected_imp, (
                f"ID {i} ('{rec['title']}'): is_imperative {rec['is_imperative']} != expected {expected_imp}"
            )
            if rec.get("unsure", False):
                unsure_count += 1
            
            ft = rec["first_tag"]
            first_tag_dist[ft] = first_tag_dist.get(ft, 0) + 1
            
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    print(f"Successfully validated and wrote {len(GOLD_RECORDS)} gold records to {gold_file}.")
    print(f"Unsure / linguistically ambiguous records tracked: {unsure_count}")
    print(f"First-tag distribution: {first_tag_dist}")

if __name__ == "__main__":
    validate_and_write_gold()
