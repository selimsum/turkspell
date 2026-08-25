import os
import json
import pickle
import time
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def _tlc(s: str) -> str:
    """Turkish lowercase."""
    return s.replace('I', 'ı').replace('İ', 'i').lower()

def get_last_vowel(word: str) -> str:
    for c in reversed(word):
        if c in 'aeıioöuüâîûAEIİOÖUÜÂÎÛ':
            return c.lower()
    return ''

def count_vowels(word: str) -> int:
    return sum(1 for c in word if c in 'aeıioöuüâîûAEIİOÖUÜÂÎÛ')

def discover_corpus_affixes():
    t_start = time.time()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    freq_path = os.path.join(base_dir, 'scripts', 'phase1', 'data', 'ts_timeline_frequencies.txt')
    clean_pickle_path = os.path.join(base_dir, 'scripts', 'phase1', 'data', 'corpus_words_clean.pickle')
    tdk_path = os.path.join(base_dir, 'raw_data', 'tdk_words.txt')
    dd_path = os.path.join(base_dir, 'raw_data', 'dil_dernegi_words.txt')
    output_path = os.path.join(base_dir, 'raw_data', 'corpus_attested_attributes.json')

    print("Step 1: Loading frequency data and clean corpus...")
    freq_map = {}
    if os.path.exists(freq_path):
        with open(freq_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    freq_map[_tlc(parts[0])] = int(parts[1])
        print(f"  Loaded {len(freq_map):,} frequency entries from ts_timeline_frequencies.txt.")
    else:
        print(f"  Warning: {freq_path} not found.")

    clean_corpus = set()
    if os.path.exists(clean_pickle_path):
        with open(clean_pickle_path, 'rb') as f:
            clean_corpus = pickle.load(f)
        print(f"  Loaded {len(clean_corpus):,} words from corpus_words_clean.pickle.")
    else:
        print(f"  Warning: {clean_pickle_path} not found.")

    print("\nStep 2: Gathering authority vocabulary from TDK & Dil Derneği...")
    authority_words = set()
    for p in [tdk_path, dd_path]:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith('#'):
                        if '/' in w:
                            w = w.split('/')[0].strip()
                        if ' ' not in w:
                            authority_words.add(_tlc(w))
    print(f"  Total authority vocabulary to analyze: {len(authority_words):,} words.")

    print("\nStep 3: Running morphological and phonological attestation analysis...")
    discovered_attributes = {}

    vowels = 'aeıioöuüâîû'
    back_vowels = 'aıouâû'
    front_vowels = 'eiöüî'
    voicing_table = {
        'p': 'b',
        'ç': 'c',
        't': 'd',
        'k': 'ğ',
        'g': 'ğ'
    }

    noun_ends_excl = {
        'parmak', 'ırmak', 'ekmek', 'yemek', 'çakmak', 'tokmak', 'yaşmak',
        'kaymak', 'ilmek', 'basamak', 'mercimek', 'damak', 'yumak', 'oymak',
        'yamak', 'hamak', 'sumak', 'kaçamak', 'kuymak', 'ramak', 'somak', 'tomak', 'emek'
    }

    stats = {
        'voicing': 0,
        'novoicing': 0,
        'vowel_drop': 0,
        'doubling': 0,
        'inverse_harmony': 0,
        'aorist_i': 0,
        'aorist_a': 0,
        'derivations': 0
    }

    for word in sorted(authority_words):
        if not word or len(word) < 2:
            continue

        attrs = set()
        is_verb = word.endswith(('mak', 'mek')) and word not in noun_ends_excl
        last_v = get_last_vowel(word)
        v_count = count_vowels(word)

        if is_verb:
            root = word[:-3]
            if root and root[-1] not in vowels:
                # Test Aorist: -Ir vs -Ar
                # Aorist_I: -ır, -ir, -ur, -ür, -ırlar, -irler, -uruz, -ürüz
                # Aorist_A: -ar, -er, -arlar, -erler, -arız, -eriz
                aor_i_cands = [f"{root}ır", f"{root}ir", f"{root}ur", f"{root}ür", f"{root}ırlar", f"{root}irler", f"{root}uruz", f"{root}ürüz"]
                aor_a_cands = [f"{root}ar", f"{root}er", f"{root}arlar", f"{root}erler", f"{root}arız", f"{root}eriz"]
                
                f_i = sum(freq_map.get(c, 0) for c in aor_i_cands) + sum(1 for c in aor_i_cands if c in clean_corpus)
                f_a = sum(freq_map.get(c, 0) for c in aor_a_cands) + sum(1 for c in aor_a_cands if c in clean_corpus)

                if f_i > f_a and f_i >= 2:
                    attrs.add('Aorist_I')
                    stats['aorist_i'] += 1
                elif f_a > f_i and f_a >= 2:
                    attrs.add('Aorist_A')
                    stats['aorist_a'] += 1

                # Verb Root Voicing: In Turkish, only 5 specific verbs (and their compounds) voice in the root
                if root in ('et', 'git', 'tat', 'güt', 'dit') or any(root.endswith(v) for v in ('et', 'git', 'tat', 'güt', 'dit')):
                    attrs.add('Voicing')
                    stats['voicing'] += 1

        else:
            # 1. Noun Voicing / NoVoicing
            if word[-1] in 'pçtkg':
                v_char = voicing_table[word[-1]]
                if word.endswith('nk'):
                    v_char = 'g'
                v_stem = word[:-1] + v_char

                # Suffix probes with vowel
                v_probes = ['ı', 'i', 'u', 'ü', 'a', 'e', 'ın', 'in', 'un', 'ün', 'ım', 'im', 'um', 'üm', 'ımız', 'imiz', 'umuz', 'ümüz', 'ınız', 'iniz', 'unuz', 'ünüz', 'e', 'a']
                v_cands = [f"{v_stem}{s}" for s in v_probes]
                uv_cands = [f"{word}{s}" for s in v_probes]

                fv = sum(freq_map.get(c, 0) for c in v_cands) + sum(1 for c in v_cands if c in clean_corpus)
                fuv = sum(freq_map.get(c, 0) for c in uv_cands) + sum(1 for c in uv_cands if c in clean_corpus)

                if fv >= 20 or (fv > fuv and fv >= 3):
                    attrs.add('Voicing')
                    stats['voicing'] += 1
                elif fuv > fv * 5 and fuv >= 10 and fv == 0:
                    attrs.add('NoVoicing')
                    stats['novoicing'] += 1

            # 2. Last Vowel Drop (e.g. akıl -> aklı, şehir -> şehri, burun -> burnu)
            if v_count >= 2 and len(word) >= 4 and word[-1] not in vowels:
                penult_vowel = word[-2]
                if penult_vowel in 'ıiuü' and word[-3] not in vowels:
                    drop_stem = word[:-2] + word[-1]
                    drop_cands = [f"{drop_stem}{s}" for s in ['ı', 'i', 'u', 'ü', 'a', 'e', 'ın', 'in', 'un', 'ün', 'ım', 'im', 'um', 'üm', 'ımız', 'imiz']]
                    keep_cands = [f"{word}{s}" for s in ['ı', 'i', 'u', 'ü', 'a', 'e', 'ın', 'in', 'un', 'ün', 'ım', 'im', 'um', 'üm', 'ımız', 'imiz']]

                    fd = sum(freq_map.get(c, 0) for c in drop_cands) + sum(1 for c in drop_cands if c in clean_corpus)
                    fk = sum(freq_map.get(c, 0) for c in keep_cands) + sum(1 for c in keep_cands if c in clean_corpus)

                    if fd > fk and fd >= 5:
                        attrs.add('LastVowelDrop')
                        stats['vowel_drop'] += 1

            # 3. Consonant Doubling (Arapça kökenli ikizleşen tek heceli sözcükler)
            known_doubling = {
                'hak', 'his', 'hat', 'af', 'sır', 'zam', 'şer', 'had', 'ret', 'hal',
                'tıp', 'hac', 'cet', 'rab', 'haz', 'zan', 'sed', 'şak', 'fen', 'şan'
            }
            native_non_doubling = {
                'ben', 'sen', 'biz', 'siz', 'el', 'kol', 'dil', 'yol', 'göl', 'gün',
                'yıl', 'bin', 'on', 'son', 'ön', 'iç', 'dış', 'saç', 'uç', 'baş',
                'taş', 'can', 'kan', 'göz', 'bel', 'yan', 'üst', 'alt', 'kul', 'yol'
            }
            if v_count == 1 and word[-1] not in vowels:
                dbl_stem = word + word[-1]
                if word == 'ret':
                    dbl_stem = 'redd'
                elif word == 'cet':
                    dbl_stem = 'cedd'
                elif word == 'had':
                    dbl_stem = 'hadd'
                elif word == 'tıp':
                    dbl_stem = 'tıbb'
                dbl_cands = [f"{dbl_stem}{s}" for s in ['ı', 'i', 'u', 'ü', 'a', 'e', 'ın', 'in', 'un', 'ün', 'ım', 'im', 'um', 'üm']]
                sgl_cands = [f"{word}{s}" for s in ['ı', 'i', 'u', 'ü', 'a', 'e', 'ın', 'in', 'un', 'ün', 'ım', 'im', 'um', 'üm']]

                fd = sum(freq_map.get(c, 0) for c in dbl_cands) + sum(1 for c in dbl_cands if c in clean_corpus)
                fs = sum(freq_map.get(c, 0) for c in sgl_cands) + sum(1 for c in sgl_cands if c in clean_corpus)

                if word in known_doubling or (word not in native_non_doubling and fd >= 100 and fd > fs * 5):
                    attrs.add('Doubling')
                    stats['doubling'] += 1

            # 4. Inverse Vowel Harmony (harf -> harfi, saat -> saati, kontrol -> kontrolü)
            if last_v in back_vowels and word[-1] not in vowels and word not in ('ana', 'baba', 'abla'):
                front_cands = [f"{word}{s}" for s in ['i', 'e', 'in', 'im', 'imiz', 'iniz', 'ler', 'lerde', 'lerden', 'lerle', 'lerin', 'lik', 'siz', 'li']]
                back_cands = [f"{word}{s}" for s in ['ı', 'a', 'ın', 'ım', 'ımız', 'ınız', 'lar', 'larda', 'lardan', 'larla', 'ların', 'lık', 'sız', 'lı']]

                ff = sum(freq_map.get(c, 0) for c in front_cands) + sum(1 for c in front_cands if c in clean_corpus)
                fb = sum(freq_map.get(c, 0) for c in back_cands) + sum(1 for c in back_cands if c in clean_corpus)

                # Require strong front dominance or presence in confirmed loanword list
                known_inverse = {'kalp', 'saat', 'harf', 'rol', 'alkol', 'hâl', 'hal', 'metal', 'normal', 'ideal', 'gol', 'kontrol', 'petrol', 'sembol', 'şefkat', 'dikkat', 'polifenol', 'flavanol', 'kortizol', 'istirahat', 'santral', 'moral', 'helal', 'hilal', 'kemal', 'cemal', 'celal', 'hayal', 'ithal', 'ihlal', 'işgal', 'ihmal', 'zeval', 'ahval', 'suikast', 'intikal', 'infial', 'ihtimal', 'istiklal', 'kabul', 'makbul', 'mahsul', 'meçhul', 'resul', 'usul'}
                if (ff > fb * 3 and ff >= 10) or word in known_inverse or word.endswith(('âl', 'ûl')):
                    attrs.add('InverseHarmony')
                    stats['inverse_harmony'] += 1

            # 5. Attested Derivational Affixes
            deriv_flags = []
            for flag, suffixes in [
                ("CI", ["ci", "cı", "cu", "cü", "çi", "çı", "çu", "çü"]),
                ("LI", ["li", "lı", "lu", "lü"]),
                ("LK", ["lik", "lık", "luk", "lük"]),
                ("SZ", ["siz", "sız", "suz", "süz"]),
                ("SL", ["sal", "sel"]),
                ("DL", ["laş", "leş"]),
                ("DT", ["laştır", "leştir"]),
                ("DE", ["len", "leş"])
            ]:
                attested = False
                for suf in suffixes:
                    cand = f"{word}{suf}"
                    if cand in clean_corpus or freq_map.get(cand, 0) >= 1:
                        attested = True
                        break
                if attested:
                    deriv_flags.append(flag)

            if deriv_flags:
                attrs.add(f"Derivations:{','.join(deriv_flags)}")
                stats['derivations'] += 1

        if attrs:
            discovered_attributes[word] = sorted(list(attrs))

    print(f"\nStep 4: Writing results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(discovered_attributes, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t_start
    print(f"\nAffix Discovery Complete in {elapsed:.2f} seconds!")
    print(f"Total Stems with Discovered/Attested Attributes: {len(discovered_attributes):,}")
    print(f"  - Voicing Stems: {stats['voicing']:,}")
    print(f"  - NoVoicing Stems: {stats['novoicing']:,}")
    print(f"  - Last Vowel Drop Stems: {stats['vowel_drop']:,}")
    print(f"  - Consonant Doubling Stems: {stats['doubling']:,}")
    print(f"  - Inverse Harmony Stems: {stats['inverse_harmony']:,}")
    print(f"  - Verb Aorist_I: {stats['aorist_i']:,}")
    print(f"  - Verb Aorist_A: {stats['aorist_a']:,}")
    print(f"  - Stems with Attested Derivations: {stats['derivations']:,}")

if __name__ == '__main__':
    discover_corpus_affixes()
