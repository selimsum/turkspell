import json
import re
from pathlib import Path
from collections import Counter

# Scientific and technical suffixes and roots
SCIENTIFIC_SUFFIX_PATTERNS = [
    # International Greek/Latin scientific suffixes adapted to Turkish
    r'.*(?:ik|tik|mik|nik|lik|rik|bik|dik|fik|sik|vik|zik)$',         # -ik adjectives (biyotik, dinamik, kanonik, agastrik)
    r'.*(?:ist|izm|izma)$',                                           # -ist, -izm (agonist, pozitivizm, sembolizm)
    r'.*(?:it|tit|sit|lit|nit|rit|mit|dit|bit|git)$',                 # -it (agranülosit, eritrosit, dolomit, grafit, dendrit)
    r'.*(?:ant|ent|ans|ens)$',                                        # -ant, -ent, -ans, -ens (aglutinant, ablukant, rezonans)
    r'.*(?:at|tat|nat|rat|mat|lat|bat|gat)$',                         # -at (agat, agregat, agonat, karbonat, hidrat)
    r'.*(?:in|tin|sin|lin|nin|rin|min|din|bin|gin)$',                 # -in (albümin, asetilen, kromatin, aktin)
    r'.*(?:en|ter|tor|tör|sor|sör|ör|er)$',                           # -en, -tor, -tör (benzen, izomer, reaktör, indikatör)
    r'.*(?:on|ton|son|lon|non|ron|mon|don|bon|gon)$',                 # -on (elektron, nötron, foton, plazmon)
    r'.*(?:az|öz|oz|id|ed)$',                                         # -az (polimeraz, kinaz), -öz/-oz (glikoz), -id/-ed (peptit/peptid)
    r'.*(?:oid|oit|oidik|oidit)$',                                    # -oid (kolloit/kolloid, asteroit, lipoit)
    # Bio/Chem/Phys/Med combining forms
    r'.*(?:jen|jenik|jeniklik|jenikçe)$',                             # -jen, -jenik (karsinojenik, aglutinojenik, teratojen)
    r'.*(?:grafi|grafik|gram)$',                                      # -grafi, -grafik (biyografi, monografi, tomografi)
    r'.*(?:loji|lojik|log)$',                                         # -loji, -lojik (biyoloji, filoloji, taksonomi)
    r'.*(?:skop|skopi|skopik)$',                                      # -skop, -skopik (endoskop, mikroskopik, stetoskop)
    r'.*(?:metr|metre|metri|metrik)$',                                # -metre, -metrik (barometre, altimetre, fotometrik)
    r'.*(?:fil|filik|fob|fobik)$',                                    # -fil, -filik, -fob, -fobik (aglutinofilik, klaustrofobik)
    r'.*(?:trop|tropik|trofi|trofik)$',                               # -trop, -tropik (heterotrof, gonadotropik)
    r'.*(?:morf|morfik|morfoloji)$',                                  # -morf, -morfik (pleomorfik, amorf)
    r'.*(?:sfer|sferik)$',                                            # -sfer (atmosfer, litosfer, hidrosfer)
    r'.*(?:faz|fazik)$',                                              # -faz, -fazik (polifazik, monofazik)
    r'.*(?:tip|tipik|tipleme)$',                                      # -tip (alelotip, fenotip, genotip)
    r'.*(?:lize|lizis|litik)$',                                       # -liz, -litik (otolitik, elektrolit, piroliz)
    r'.*(?:kardi|vasküler|krino|nöro|psi)$',                          # Medical prefixes/stems
    # Turkish scientific neologisms and standard derivations
    r'.*(?:sel|sal)$',                                                # -sel, -sal (bilişsel, kütleçekimsel, evrensel)
    r'.*(?:ölçer|sayar|yazar|çizer|atar|çeker)$',                     # -ölçer, -sayar (akıntıölçer, adımsayar, sismograf)
    r'.*(?:gen|gan)$',                                                # -gen, -gan (üçgen, dörgen, indirgen)
    r'.*(?:bilim|bilgisel|bilimsel)$',                                # -bilim (yerbilim, gökbilim)
    r'.*(?:aç|geç)$',                                                 # -aç, -geç (süzgeç, sayaç, ayıraç)
]

RE_SCIENTIFIC = re.compile("|".join(SCIENTIFIC_SUFFIX_PATTERNS), re.IGNORECASE)

# Dialect patterns to EXCLUDE (Derleme Sözlüğü mouth markers)
DIALECT_EXCLUDE_PATTERNS = [
    r'.*(?:cık|cik|cuk|cük|cük)$',                                    # Anatolian mouth diminutives on unknown stems (aggucuk, alecik)
    r'^[a-z]{1,3}(?:bak|güt|lak|rak|mak|rak)$',                       # Short mouth sound effects / reduplications (ağabbak, aggüt)
    r'.*(?:abak|ebek|ibik|obuk|übür)$',
    r'.*(?:akına|ana|ola|ula|aca|ala)$',                              # Dialect mouth adverbs (acabakına, acabana)
    r'^(?:ag|ab|al|av|ay|ak)[a-z]*(?:cuk|cik|güt|bak|lak)$',         # Agg- / Ağ- dialect variants
]

RE_DIALECT_EXCLUDE = re.compile("|".join(DIALECT_EXCLUDE_PATTERNS), re.IGNORECASE)

def is_valid_scientific_term(word: str) -> bool:
    w = word.strip().lower()
    if len(w) < 3 or len(w) > 30:
        return False
    # Standard Turkish characters only
    if not all(c in "abcçdefgğhıijklmnoöprsştuüvyzâîû" for c in w):
        return False
    # No repeated character triples (e.g. aaa, bbb)
    if re.search(r"(.)\1\1", w):
        return False
    # Check if matches dialect markers
    if RE_DIALECT_EXCLUDE.match(w):
        return False
    # Must match scientific suffix or morphology
    if not RE_SCIENTIFIC.match(w):
        return False
    return True

# Test on parsed colab entries
with open('raw_data/triage/colab_parsed_terimler.json', encoding='utf-8') as f:
    parsed = json.load(f)

with open('raw_data/tdk_words.txt', encoding='utf-8') as f:
    tdk_words = set(line.strip().split('/')[0].lower() for line in f if line.strip())

valid = [x for x in parsed if x.get('lemma')]
filtered_terms = []
for x in valid:
    lem = x['lemma'].strip().lower()
    if lem in tdk_words:
        continue
    if is_valid_scientific_term(lem):
        filtered_terms.append(x)

print(f"Total valid parsed: {len(valid)}")
print(f"Passed scientific/technical filter: {len(filtered_terms)}")
print("Sample filtered scientific terms:")
for item in filtered_terms[:30]:
    print(f"  {item['lemma']} [{item.get('pos')}] attrs={item.get('attributes')}")
