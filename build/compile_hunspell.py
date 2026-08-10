import os
import json
import re
import sys

# utf8_flag_mapping and generate_grammar_rules are siblings in build/. Python only
# adds this directory to sys.path when the file is run as a script, so importing
# compile_dictionary from elsewhere (e.g. tools/) would otherwise fail.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utf8_flag_mapping import LONG_TO_UTF8, remap_flag_string


# Vowels definition
FRONT_VOWELS = set('eioüîiöEİÖÜÎ')
BACK_VOWELS  = set('aıouâûAIOUÂÛ')

def get_last_vowel(word):
    all_vowel_chars = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
    for ch in reversed(word):
        if ch in all_vowel_chars:
            return ch.lower()
    return None

def turkish_capitalize(s: str) -> str:
    if not s:
        return s
    first = s[0]
    if first == 'i':
        first_cap = 'İ'
    elif first == 'ı':
        first_cap = 'I'
    else:
        first_cap = first.upper()
    return first_cap + s[1:]

ALL_CAPS_ABBREVS = {'abd', 'dna', 'gps', 'uuı', 'uv', 'bbc', 'vr', 'eeg', 'yz', 'sscb', 'esa', 'rfid', 'dehb', 'mit', 'ngc', 'hiv', 'sls', 'atp', 'cern', 'iq', 'tl'}

CASE_PRESERVED_OVERRIDES = {
    'khz': 'KHz',
    'mhz': 'MHz',
    'eugh': 'EuGH',
    'amerika birleşik devletleri': 'Amerika Birleşik Devletleri',
    'wi-fi': 'Wi-Fi',
}

def turkish_upper(s: str) -> str:
    return s.replace('i', 'İ').replace('ı', 'I').upper()

def get_voiced_stem(lemma: str) -> str:
    if not lemma:
        return ""
    last_char = lemma[-1].lower()
    if last_char == 'k' and lemma.lower().endswith('nk'):
        return lemma[:-1] + 'g'
    voicing_map = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'ğ', 'g': 'ğ'}
    if last_char in voicing_map:
        return lemma[:-1] + voicing_map[last_char]
    return lemma

def capitalize_word(s: str, base_lkey: str) -> str:
    if base_lkey in CASE_PRESERVED_OVERRIDES:
        return CASE_PRESERVED_OVERRIDES[base_lkey]
    if base_lkey in ALL_CAPS_ABBREVS:
        return turkish_upper(s)
    return turkish_capitalize(s)

def get_poss3sg_stems(lemma: str, voicing: bool = False) -> list[str]:
    if not lemma:
        return []
    
    # Detect last vowel
    vowels = 'aeıioöuüâîû'
    lv = None
    for ch in reversed(lemma):
        if ch.lower() in vowels:
            lv = ch.lower()
            break
    if not lv:
        lv = 'a'
        
    # Suffix vowel selection
    if lv in 'aıâ':
        s_vow = 'ı'
    elif lv in 'eiî':
        s_vow = 'i'
    elif lv in 'ouû':
        s_vow = 'u'
    else:
        s_vow = 'ü'
        
    # Check if ends in vowel
    ends_vow = lemma[-1].lower() in vowels
    
    if ends_vow:
        return [lemma + 's' + s_vow]
    else:
        # Consonant ending - check for voicing
        base = lemma[:-1]
        last_char = lemma[-1].lower()
        
        # Voicing rules
        voiced_char = last_char
        if last_char == 'k':
            if lemma.lower().endswith('nk'):
                voiced_char = 'g'
            else:
                voiced_char = 'ğ'
        elif last_char == 'p':
            voiced_char = 'b'
        elif last_char == 't':
            voiced_char = 'd'
        elif last_char == 'g':
            voiced_char = 'ğ'
        elif last_char == 'ç':
            voiced_char = 'c'
            
        if voiced_char != last_char and voicing:
            return [base + voiced_char + s_vow]
        else:
            return [lemma + s_vow]

def is_back_vowel(word):
    lv = get_last_vowel(word)
    if lv is None:
        return True # Default fallback
    return lv in 'aıouâû'

def ends_with_vowel(word):
    all_vowel_chars = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
    return len(word) > 0 and word[-1] in all_vowel_chars

def compile_dictionary():
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))

    def lexicon_file(name: str, required: bool = True) -> str:
        """Resolve a lexicon input to an absolute path.

        Looks in lexicons/ first, then falls back to the CWD so the script
        still works when invoked from a directory holding loose inputs.
        Required inputs that are missing raise instead of being skipped —
        a build that silently drops a lexicon is never a valid build.
        """
        path = os.path.join(base_dir, 'lexicons', name)
        if os.path.exists(path):
            return path
        if os.path.exists(name):
            return name
        if required:
            raise FileNotFoundError(
                f"Required lexicon '{name}' not found in "
                f"{os.path.join(base_dir, 'lexicons')} or {os.getcwd()}"
            )
        return ""

    lexicon_path = lexicon_file('zemberek_lexicon.json')
    print(f"Reading {lexicon_path}...")
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
        
    print(f"Loaded {len(lexicon)} entries from lexicon.")

    # -----------------------------------------------------------------------
    # TDK + Dil Derneği: authoritative sources of truth
    # -----------------------------------------------------------------------
    # Every word in either list must appear in tr.dic.
    # Zemberek is used only as a morphological helper — any Zemberek entry
    # whose lemma is not in TDK or Dil Derneği is excluded.
    def _tlc(s):
        """Turkish lowercase (I→ı, İ→i)."""
        return s.replace('I', 'ı').replace('İ', 'i').lower()

    _raw_dir = os.path.join(base_dir, 'raw_data')
    _tdk_set = set()
    _dd_set = set()
    
    for _fname, _target_set in [('tdk_pdf_words.txt', _tdk_set), ('dil_dernegi_words.txt', _dd_set)]:
        _fpath = os.path.join(_raw_dir, _fname)
        if not os.path.exists(_fpath):
            raise FileNotFoundError(
                f"Required authority wordlist '{_fname}' not found in {_raw_dir}. "
                f"Without it the Zemberek filter below would discard the entire lexicon."
            )
        with open(_fpath, encoding='utf-8') as _f:
            for _line in _f:
                _w = _line.strip()
                if not _w:
                    continue
                if '/' in _w:
                    _head, _, _alt = _w.partition('/')
                    _target_set.add(_tlc(_head))
                    _prefix = _head.rsplit(' ', 1)[0] if ' ' in _head else ''
                    _target_set.add(_tlc(f"{_prefix} {_alt}".strip()))
                    continue
                _target_set.add(_tlc(_w))
                
    def _strip_hat(s):
        return s.replace('â','a').replace('î','i').replace('û','u')

    _authority_set = set(_dd_set)
    _dd_unhatted_map = {}
    for w in _dd_set:
        unhatted = _strip_hat(w)
        if unhatted not in _dd_unhatted_map:
            _dd_unhatted_map[unhatted] = set()
        _dd_unhatted_map[unhatted].add(w)

    # Distinct unhatted words in TDK that have a different meaning from Dil Derneği's hatted version
    UNHATTED_EXCEPTIONS = {'ademiyet'}

    _dropped_unhatted = 0
    for w in _tdk_set:
        if w == _strip_hat(w): # w is unhatted
            if w in _dd_unhatted_map and w not in _dd_set and w not in UNHATTED_EXCEPTIONS:
                # DD has hatted version(s) of this word, but NOT the unhatted version.
                # User rule: "Eğer bir kelimenin Dil Derneği'nde şapkalı hâli varsa, TDK'daki şapkasız hâlini yoksay"
                _dropped_unhatted += 1
                continue
        _authority_set.add(w)
        
    print(f"Dropped {_dropped_unhatted} unhatted TDK words because Dil Derneği dictates the hatted form.")
    print(f"Authority set: {len(_authority_set):,} words from TDK + Dil Derneği.")

    # Filter Zemberek: keep only entries whose lemma is in TDK or Dil Derneği
    _before_filter = len(lexicon)
    lexicon = [e for e in lexicon if _tlc(e.get('lemma', '')) in _authority_set]
    print(f"Zemberek filtered: {_before_filter} -> {len(lexicon)} "
          f"({_before_filter - len(lexicon)} Zemberek-only entries removed.)")

    custom_entries = [
        # User requested additions:
        {'lemma': 'ahenk', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'diyalog', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'dip', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'dahaki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'imiş', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'idi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'idik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Atatürk', 'pos': 'ProperNoun', 'attributes': ['NoVoicing']},
        {'lemma': 'Türk', 'pos': 'ProperNoun', 'attributes': []},
        {'lemma': 'çarpıştırıcı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'patlama', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gezinge', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kafatas', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kolonileşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'moderatör', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'moralsizlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'yıldızlararası', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'ötegezegen', 'pos': 'Noun', 'attributes': []},
        # --- New custom entries for requested words ---
        {'lemma': 'web', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'online', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'offline', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'email', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'blog', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'server', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'chat', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'wifi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'arktik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'bulabilmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'gerekçelendirme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gerçekleştirme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'güçsüzleşme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'miting', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mitingi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'arkticte', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yükseltmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'wi-fi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'wi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'vb.', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'T.C.', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Mustafa', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Amerika Birleşik Devletleri', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'Devletleri', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'hal', 'pos': 'Noun', 'attributes': ['InverseHarmony', 'NoVoicing']},
        # Arabic-origin -al loanwords that take front suffixes despite the back
        # vowel ('ihlaller', not 'ihlallar'). Their siblings (ihmal, ihtimal,
        # misal, emsal) carry InverseHarmony from Zemberek, but these reach the
        # build only through the TDK/Dil Dernegi list, which has no attributes,
        # so they would otherwise default to back harmony.
        {'lemma': 'ihlal', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'istiklal', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'hilal', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'celal', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'implant', 'pos': 'Noun', 'attributes': ['NoVoicing']},
        {'lemma': 'konuşmacı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kriptografi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'planlamacı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'seferki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sistem', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yaralı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yerleşimci', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sadakat', 'pos': 'Noun', 'attributes': ['InverseHarmony', 'NoVoicing']},
        {'lemma': 'Atlantik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Neandertal', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'Sibirya', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Himalaya', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Zelanda', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Alaska', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'seddi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Paralimpik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'DNA', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Bahamalar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kutbu', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dağları', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'Pers', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'antiviral', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'karatlık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'korunmasız', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pörçük', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'amino', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'manipüle', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'anki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bugünkü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dünkü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yarınki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'şimdiki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sonraki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'önceki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bazlı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'merkezli', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'lob', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kütleçekimsel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kadarki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kirlilik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'dolanık', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'simüle', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'seçilim', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yakıtlı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sürelik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'kardiyovasküler', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gökcisim', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bozon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fisyon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'enfekte', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'asidik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'dioksit', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'amigdala', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kuark', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'senkronize', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'koronavirüs', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hipokampus', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'siber', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'galaktik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'onikiparmak', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'astrofizikçi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'paleontolog', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fosfin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'tarihlenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'zamanki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'krallık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'metabolik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mikrobiyal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'merceklenme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'merceklenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'mega', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'serebral', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kriyojenik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mikrobiyom', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'modifiye', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'probiyotik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'öngezegen', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'laktik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'oksipital', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dokunmatik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'embriyonik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hipotalamus', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sinaps', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sirkadiyen', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'zamansı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kuasar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mayoz', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'nöral', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pandemi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kozmolog', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'süperiletken', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gravastar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kortikal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'metaverse', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mitokondriyal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'psikedelik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pulpa', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yılki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'karbondioksit', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'membran', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'flavanol', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sinkrotron', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'epigenetik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'yetmezlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'kap', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'mod', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'abur', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'cubur', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'öki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fMRI', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fMR', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ithafen', 'pos': 'Adverb', 'attributes': []},
        {'lemma': 'adaptif', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'fütüristik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'jeomanyetik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'müon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'nükleik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'süperpozisyon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'asetilkolin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'biyometrik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'kriyonik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pulmoner', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'tiroid', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'holografik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'kontakt', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'teropod', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'şeyl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'grafen', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'invaziv', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'maglev', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'magnetar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'oksitosin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pestisit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'piksel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'polifenol', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'prebiyotik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ribozom', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sonik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'falanks', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hipotermi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'piezoelektrik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'progesteron', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'regolit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'stimülasyon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'vestibüler', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'adenozin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'biseps', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fleksör', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fotovoltaik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'hedonik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'kompulsif', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'mekânsal', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'sitokin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sitozin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'terapötik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'tübül', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'öngezegensel', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'önyıldız', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'anakol', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'astrofiziksel', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'biyomoleküler', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'lepton', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'nefron', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'psikiyatrik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'retikulum', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sfinkter', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'triseps', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'tünelleme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'amiloid', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'astrosit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'baryonik', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'fotoreseptör', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hepatosit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'interkostal', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'kril', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'makrofaj', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'metilasyon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'monoksit', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'organoit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'paramiliter', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'pterozor', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'siborg', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'singulat', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'alel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'antihidrojen', 'pos': 'Noun', 'attributes': []},
        {'lemma': "bonobo", 'pos': "Noun", 'attributes': []},
        {'lemma': "ekolokasyon", 'pos': "Noun", 'attributes': []},
        {'lemma': "endoplazmik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "etan", 'pos': "Noun", 'attributes': []},
        {'lemma': "hepatik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "hipersonik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "homeostatik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "kerosen", 'pos': "Noun", 'attributes': []},
        {'lemma': "kondensat", 'pos': "Noun", 'attributes': ['Voicing']},
        {'lemma': "kraniyal", 'pos': "Adjective", 'attributes': []},
        {'lemma': "laktat", 'pos': "Noun", 'attributes': []},
        {'lemma': "melanom", 'pos': "Noun", 'attributes': []},
        {'lemma': "noninvaziv", 'pos': "Adjective", 'attributes': []},
        {'lemma': "nükleus", 'pos': "Noun", 'attributes': []},
        {'lemma': "pelvik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "piroklastik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "sauropod", 'pos': "Noun", 'attributes': []},
        {'lemma': "simbiyotik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "sinovyal", 'pos': "Adjective", 'attributes': []},
        {'lemma': "trifosfat", 'pos': "Noun", 'attributes': []},
        {'lemma': "yörüngesel", 'pos': "Adjective", 'attributes': []},
        {'lemma': "ökaryot", 'pos': "Noun", 'attributes': []},
        {'lemma': "bütirat", 'pos': "Noun", 'attributes': []},
        {'lemma': "glukagon", 'pos': "Noun", 'attributes': []},
        {'lemma': "glutamat", 'pos': "Noun", 'attributes': []},
        {'lemma': "helyosfer", 'pos': "Noun", 'attributes': []},
        {'lemma': "hipoksi", 'pos': "Noun", 'attributes': []},
        {'lemma': "hominin", 'pos': "Noun", 'attributes': []},
        {'lemma': "immünoterapi", 'pos': "Noun", 'attributes': []},
        {'lemma': "koklear", 'pos': "Adjective", 'attributes': []},
        {'lemma': "luminol", 'pos': "Noun", 'attributes': []},
        {'lemma': "mikromerceklenme", 'pos': "Noun", 'attributes': []},
        {'lemma': "parazitoit", 'pos': "Noun", 'attributes': []},
        {'lemma': "prokaryot", 'pos': "Noun", 'attributes': []},
        {'lemma': "psikiyatrist", 'pos': "Noun", 'attributes': []},
        {'lemma': "salin", 'pos': "Noun", 'attributes': []},
        {'lemma': "silika", 'pos': "Noun", 'attributes': []},
        {'lemma': "spektroskopik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "talamus", 'pos': "Noun", 'attributes': []},
        {'lemma': "telomer", 'pos': "Noun", 'attributes': []},
        {'lemma': "timpanik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "turboşarj", 'pos': "Noun", 'attributes': []},
        {'lemma': "özofagus", 'pos': "Noun", 'attributes': []},
        {'lemma': "aminoasit", 'pos': "Noun", 'attributes': []},
        {'lemma': "amniyotik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "arkoloji", 'pos': "Noun", 'attributes': []},
        {'lemma': "dendrit", 'pos': "Noun", 'attributes': []},
        {'lemma': "dimetil", 'pos': "Noun", 'attributes': []},
        {'lemma': "epoksi", 'pos': "Noun", 'attributes': []},
        {'lemma': "feret", 'pos': "Noun", 'attributes': []},
        {'lemma': "ghrelin", 'pos': "Noun", 'attributes': []},
        {'lemma': "gliya", 'pos': "Noun", 'attributes': []},
        {'lemma': "hiperventilasyon", 'pos': "Noun", 'attributes': []},
        {'lemma': "kaldera", 'pos': "Noun", 'attributes': []},
        {'lemma': "koksiks", 'pos': "Noun", 'attributes': []},
        {'lemma': "limbik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "lomber", 'pos': "Adjective", 'attributes': []},
        {'lemma': "miyelin", 'pos': "Noun", 'attributes': []},
        {'lemma': "nükleotit", 'pos': "Noun", 'attributes': []},
        {'lemma': "servikal", 'pos': "Adjective", 'attributes': []},
        {'lemma': "somatosensoriyel", 'pos': "Adjective", 'attributes': []},
        {'lemma': "taçküre", 'pos': "Noun", 'attributes': []},
        {'lemma': "ultrasonik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "venöz", 'pos': "Adjective", 'attributes': []},
        {'lemma': "volkanizma", 'pos': "Noun", 'attributes': []},
        {'lemma': "antosiyanin", 'pos': "Noun", 'attributes': []},
        {'lemma': "arksaniye", 'pos': "Noun", 'attributes': []},
        {'lemma': "dehidrasyon", 'pos': "Noun", 'attributes': []},
        {'lemma': "depresif", 'pos': "Adjective", 'attributes': []},
        {'lemma': "deterministik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "dielektrik", 'pos': "Noun", 'attributes': []},
        {'lemma': "dipol", 'pos': "Noun", 'attributes': []},
        {'lemma': "ekstrüzyon", 'pos': "Noun", 'attributes': []},
        {'lemma': "endorfin", 'pos': "Noun", 'attributes': []},
        {'lemma': "enterik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "epizodik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "fallop", 'pos': "Noun", 'attributes': []},
        {'lemma': "faringeal", 'pos': "Adjective", 'attributes': []},
        {'lemma': "fotomultiplier", 'pos': "Noun", 'attributes': []},
        {'lemma': "fotosentetik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "hekzaflorür", 'pos': "Noun", 'attributes': []},
        {'lemma': "hidrazin", 'pos': "Noun", 'attributes': []},
        {'lemma': "jeostatik", 'pos': "Adjective", 'attributes': []},
        {'lemma': "karotenoid", 'pos': "Noun", 'attributes': []},
        {'lemma': "karpal", 'pos': "Adjective", 'attributes': []},
        {'lemma': "kortikotropin", 'pos': "Noun", 'attributes': []},
        {'lemma': "kriyoprotektan", 'pos': "Noun", 'attributes': []},
        {'lemma': "kuadriseps", 'pos': "Noun", 'attributes': []},
        {'lemma': "metakarp", 'pos': "Noun", 'attributes': []},
        {'lemma': "mosazor", 'pos': "Noun", 'attributes': []},
        {'lemma': "nanotüp", 'pos': "Noun", 'attributes': []},
        {'lemma': "nematod", 'pos': "Noun", 'attributes': []},
        {'lemma': "nitrik", 'pos': "Noun", 'attributes': []},
        {'lemma': "nörojenez", 'pos': "Noun", 'attributes': []},
        {'lemma': "psilosibin", 'pos': "Noun", 'attributes': []},
        {'lemma': "subklavyen", 'pos': "Adjective", 'attributes': []},
        {'lemma': "taktiksel", 'pos': "Adjective", 'attributes': []},
        {'lemma': "telekom", 'pos': "Noun", 'attributes': []},
        {'lemma': "tozlayıcı", 'pos': "Noun", 'attributes': []},
        {'lemma': "ventrikül", 'pos': "Noun", 'attributes': []},
        {'lemma': "adipoz", 'pos': "Adjective", 'attributes': []},
        {'lemma': "aksion", 'pos': "Noun", 'attributes': []},
        {'lemma': "amfetamin", 'pos': "Noun", 'attributes': []},
        {'lemma': "anakart", 'pos': "Noun", 'attributes': []},
        {'lemma': "apoptoz", 'pos': "Noun", 'attributes': []},
        {'lemma': "asetofenon", 'pos': "Noun", 'attributes': []},
        {'lemma': "binoküler", 'pos': "Adjective", 'attributes': []},
        {'lemma': "detrüsör", 'pos': "Noun", 'attributes': []},
        {'lemma': "ekstensor", 'pos': "Noun", 'attributes': []},
        {'lemma': "ekzokrin", 'pos': "Adjective", 'attributes': []},
        {'lemma': "emoji", 'pos': "Noun", 'attributes': []},
        {'lemma': "fasya", 'pos': "Noun", 'attributes': []},
        {'lemma': "geko", 'pos': "Noun", 'attributes': []},
        {'lemma': "hemoroid", 'pos': "Noun", 'attributes': []},
        {'lemma': "hipodermis", 'pos': "Noun", 'attributes': []},
        {'lemma': "hümör", 'pos': "Noun", 'attributes': []},
        {'lemma': "inflamasyon", 'pos': "Noun", 'attributes': []},
        {'lemma': "inhibe", 'pos': "Verb", 'attributes': []},
        {'lemma': "kapasitör", 'pos': "Noun", 'attributes': []},
        {'lemma': "kolibaktin", 'pos': "Noun", 'attributes': []},
        {'lemma': "kollajen", 'pos': "Noun", 'attributes': []},
        {'lemma': 'kod', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kodlamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'buzdolabı', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'gözlemevi', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'nötralize', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'spektrometre', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kayganlaştırıcı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ikonik', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'detoks', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ninja', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bip', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'haritalamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'radyal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yerçekimsel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sürdürülebilir', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sürdürülebilirlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'pulsar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'folikül', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'steroid', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kolonist', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mikroskopi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'nebula', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ivmelenme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'günkü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'implante', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'rejeneratif', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'fleksor', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'davemaoit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'böbreküstü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dejeneratif', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dizilim', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gluon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kıtasal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'lüsid', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mikrograf', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'miyozin', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pelvis', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pırıl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'rekombinasyon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'senkrotron', 'pos': 'Noun', 'attributes': []},
        # Missing Noun-to-Verb derivatives identified by SFT analysis and diagnostics
        {'lemma': 'vazolamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'daralmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'anahtarlamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'gözlemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'cisimleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'sertifikalamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'yayınlamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'yayınlanmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'modellemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'tetiklenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'tescillenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'ivmelenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'ölçeklemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'ölçeklenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'gençleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'şoklanmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'arazileşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kıraçlaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'türleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'bentlemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'bilgilemek', 'pos': 'Verb', 'attributes': []},
        # Custom entries to resolve unrecognized gaps:
        {'lemma': 'aracık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'derebeylik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'deneyimlemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'fiyatlamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'tarikatlaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'taşeronlaştırmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'zararlandırmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'çözümlemeci', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'anasıda', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'doğanay', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'doğarı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'emanetullah', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'emirimiz', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'eşitlilik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'garipçe', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'halli', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'havas', 'pos': 'Noun', 'attributes': ['Doubling']},
        {'lemma': 'hayaletimsi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'menekşemsi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'haylice', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kısımlı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mutlululuk', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'valililik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'sorumluk', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'başörtülü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'başörtüsüz', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ateşl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'duraks', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'garantil', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ilgil', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kekel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sırtl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'tell', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'zayıfl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'çalkal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'şişmanl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'azab', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'beyt', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'takib', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kırlangıc', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sürec', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'lapseki', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'havutçu', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'köprüaltı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'külhanbey', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'metalaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'polisçi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sivilcelenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'siyasileştirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'sorunsallaştırmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'sekülerleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'tanınırlık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'dilsizleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'tecavüzcü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yürüyüşçü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'zeytinyağlı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'çakkal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'örgüsel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'şovrum', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'termo', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kurlu', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kutucuk', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'süresimi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'doğrultası', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'edilemezlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'ferdileştirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'ferdileştirilmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'fonlanmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'fonlamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kimliklendirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kimliklendirilmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'zeybekçi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'nabızsız', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'derdirtmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'diyalogsuzluk', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'diyalogsuz', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gerekçe', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gerekçi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'geyikli', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gürül', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'halci', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hatlı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'işletmesel', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'karanlıklaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kargolamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kargolanmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kavimci', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kişililik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'koksal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kovalamaca', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mahsuplaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'menüsküs', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mutfakçı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'paranoyaklaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'politikasızlık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'refakatçi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'süreklenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'taşımacılı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yaprakçı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'tarihlemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'tarihleme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'pozlama', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'filtrelemek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'filtreleme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'filtrelenmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'gümbür', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kilometreküp', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'antidepresan', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hukukî', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'trend', 'pos': 'Noun', 'attributes': []},
        # Base stems added to support metrics and loan prefixes dynamically
        {'lemma': 'depresan', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'enflamatuvar', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'inflamatuvar', 'pos': 'Adjective', 'attributes': []},
        {'lemma': 'transmitter', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'transmiter', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'baskılayıcı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yazıcı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'immün', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'watt', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'volt', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'amper', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'metre', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gram', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'litre', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kalori', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kütle', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'hertz', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bayt', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bit', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'saniye', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dakika', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'gün', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yıl', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dejeneratif', 'pos': 'Noun', 'attributes': []},
        # kombin: base for kombinlere, kombinli, kombinli, etc.
        {'lemma': 'kombin', 'pos': 'Noun', 'attributes': []},
        # Unit apostrophe-derivation forms: unit+'lik/'lık (e.g. mm'lik, cm'lik)
        # These can't be generated by suffix rules because the units have no vowels
        {'lemma': "mm'lik", 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': "cm'lik", 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': "km'lik", 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': "kg'lık", 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': "m'lik", 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': "tl'lik", 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': "ml'lik", 'pos': 'Noun', 'attributes': ['Voicing']},
        # Note: 'ml' bare stem intentionally removed to prevent acceptance
        # of misspellings like 'mlla' -> 'malla' (ml + -la instrumental suffix)
        # Missing proper nouns to ensure they exist in lexicon
        {'lemma': "Ingiltere", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Italya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Rusya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Isveç", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Slovakya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Çekya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Iran", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Etyopya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Etiopya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Stockholm", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Bakü", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Mumbai", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Washington", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Toronto", 'pos': 'Noun', 'attributes': []},
        {'lemma': "stabilite", 'pos': 'Noun', 'attributes': []},
        {'lemma': "optimize", 'pos': 'Noun', 'attributes': []},
        {'lemma': "havalimanı", 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': "havaalanı", 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': "cumhurbaşkanı", 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': "Adnan", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Esenboğa", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Yandex", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Maps", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Navi", 'pos': 'Noun', 'attributes': []},
        {'lemma': "Sabiha", 'pos': 'Noun', 'attributes': []},
        {'lemma': "check-in", 'pos': 'Noun', 'attributes': []},
        {'lemma': "check", 'pos': 'Noun', 'attributes': []},
        # Apostrophe-prefixed suffixes to support inflected numbers (since digits are split by Hunspell)
        {'lemma': "'da", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'de", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ta", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'te", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'dan", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'den", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'tan", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ten", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'a", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'e", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ya", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ye", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ın", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'in", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'un", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ün", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'nın", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'nin", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'nun", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'nün", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'lık", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'lik", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'luk", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'lük", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ı", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'i", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'u", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'ü", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'yı", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'yi", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'yu", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'yü", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'la", 'pos': 'Noun', 'attributes': []},
        {'lemma': "'le", 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dijitalleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'dijitalleştirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'eşlikçi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'batım', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'İrlanda', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yarışmacı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'merkezi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sahnesi', 'pos': 'Noun', 'attributes': []},
        # Batch 3 custom entries
        {'lemma': 'inçlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'haşır', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'reflü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'değişikli', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'duraklamasız', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'dönüklük', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'sinyalleşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'sürüntü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'terabaytlık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'trilyonlarca', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yanlışlamak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'üssü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'öngörülemezlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'şifacı', 'pos': 'Noun', 'attributes': []},
        # Batch 4 custom entries
        {'lemma': 'basınç', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'basınçsız', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bilinirlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'computer', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'donanımsal', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'içeydim', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kargacık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'karşıya', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kullanışlı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'lisanssız', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'savunmacı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'serflik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'statüsüz', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'taşınım', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'yolcuk', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'zon', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'ıvır', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'zıvır', 'pos': 'Noun', 'attributes': []},
        # --- Deep agglutinative verbs & rare words to bypass Hunspell depth limit ---
        {'lemma': 'işlevselleştirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'işlevlendirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'sendikasızlaştırmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kaydileştirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kaydileşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kaydileştirme', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'bakmayıvermek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'bakıvermek', 'pos': 'Verb', 'attributes': []},
        # --- Intermediate stems to bypass Hunspell 2-stage suffixation limit ---
        {'lemma': 'algınlık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'göremezlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'kuşatıcı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kuşatıcılık', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'istikrarsızlaştırmak', 'pos': 'Verb', 'attributes': []},
        # --- Words added to fix benchmark drops ---
        {'lemma': 'anlaşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'bizimle', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kavuşmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'mı', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mi', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mu', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'mü', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'nemalanmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'yamultmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'Şii', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'değişmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'giriş', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'girişindeler', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'alp', 'pos': 'Noun', 'attributes': ['InverseHarmony']},
        {'lemma': 'alıvermek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'emzirmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'gever', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sarkmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'uçulmak', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'kuran', 'pos': 'Noun', 'attributes': []},
    ]
    # Inject all missing TDK words dynamically from scratch file
    import os
    missing_tdk_path = os.path.join(base_dir, 'scratch', 'all_missing_tdk_words.txt')
    if os.path.exists(missing_tdk_path):
        with open(missing_tdk_path, 'r', encoding='utf-8') as _mf:
            _mwords = [line.strip() for line in _mf if line.strip()]
        for _mw in _mwords:
            _pos = 'Verb' if (_mw.endswith('mak') or _mw.endswith('mek')) else 'Noun'
            custom_entries.append({'lemma': _mw, 'pos': _pos, 'attributes': []})
        print(f'Injected {len(_mwords)} missing TDK entries into custom_entries.')

    # Load dynamically parsed candidates from OSCAR/Corpus pipeline if available.
    # Genuinely optional: this is a generated pipeline artifact, not a source lexicon.
    import os
    oscar_path = lexicon_file('oscar_parsed_candidates.json', required=False)
    if oscar_path:
        with open(oscar_path, 'r', encoding='utf-8') as f:
            oscar_entries = json.load(f)
        print(f"Loaded {len(oscar_entries)} dynamically parsed candidates from {oscar_path}.")
        for entry in oscar_entries:
            if entry.get('lemma'):
                custom_entries.append({
                    'lemma': entry['lemma'],
                    'pos': entry['pos'],
                    'attributes': entry.get('attributes', [])
                })
    else:
        print("No oscar_parsed_candidates.json found - skipping (optional).")

    # Load custom abbreviations (required)
    abbrev_path = lexicon_file('custom_abbreviations.json')
    with open(abbrev_path, 'r', encoding='utf-8') as f:
        abbrev_list = json.load(f)
    custom_entries.extend(abbrev_list)
    print(f"Loaded {len(abbrev_list)} custom abbreviations.")

    # Load custom names (required)
    names_path = lexicon_file('custom_names.json')
    with open(names_path, 'r', encoding='utf-8') as f:
        names_list = json.load(f)
    custom_entries.extend(names_list)
    print(f"Loaded {len(names_list)} custom names.")

    lexicon.extend(custom_entries)

    # Add every TDK|DD word not already covered by Zemberek or custom_entries.
    # For words that differ from a Zemberek entry only in circumflex spelling
    # (e.g. TDK "halen" vs Zemberek "hâlen"), transfer the Zemberek POS and
    # attributes so that morphological correctness (voicing, inverse harmony…)
    # is preserved despite the spelling reform.
    def _strip_hat(s):
        return s.replace('â','a').replace('î','i').replace('û','u')

    # Build a lookup: stripped-lowercase lemma -> full Zemberek entry
    # (used only for the circumflex-transfer logic below)
    _zem_by_stripped = {}
    with open(lexicon_path, encoding='utf-8') as _zf:
        _zem_all = json.load(_zf)
    for _ze in _zem_all:
        _key = _strip_hat(_tlc(_ze['lemma']))
        if _key not in _zem_by_stripped:
            _zem_by_stripped[_key] = _ze

    _covered = {_tlc(e.get('lemma', '')) for e in lexicon}
    _noun_ends_excl = (
        'parmak', 'ırmak', 'ekmek', 'yemek', 'çakmak', 'tokmak', 'yaşmak',
        'kaymak', 'ilmek', 'basamak', 'mercimek', 'damak', 'yumak', 'oymak',
        'yamak', 'hamak', 'sumak', 'kaçamak', 'kuymak', 'ramak', 'somak', 'tomak', 'emek'
    )
    _tdk_added = 0
    _attrs_transferred = 0
    # Dil Derneği wrongly lists front-variant derivatives of the back-harmony
    # loanword emlak ("emlakçi", "emlakçilik"); TDK has only the back forms
    # (emlakçı, emlakçılık). They are also marked obsolete in
    # scratch/obsolete_lemmas.json. Exclude them so they are never accepted.
    _BAD_DD_VARIANTS = {'emlakçi', 'emlakçilik'}
    for _w in sorted(_authority_set):
        if _w in _BAD_DD_VARIANTS:
            print(f"Excluding Dil Derneği front-variant misspelling: {_w}")
            continue
        if _w not in _covered:
            # Check for a circumflex-spelling match in Zemberek
            _zem_match = _zem_by_stripped.get(_strip_hat(_w))
            if _zem_match and _tlc(_zem_match['lemma']) != _w:
                # Transfer POS + attributes from the Zemberek entry
                _pos  = _zem_match.get('pos', 'Noun')
                _attrs = list(_zem_match.get('attributes', []))
                # Remove Zemberek-internal flags that don't map to our system
                _attrs = [a for a in _attrs if a not in ('PronunciationGuessed', 'Ext', 'NoQuote')]
                if _pos == 'Verb':
                    pass  # keep Verb
                elif _pos not in ('Noun','Adjective','Adverb','Conjunction','Interjection',
                                  'Numeral','Pronoun','PostPositive','Determiner','Duplicator'):
                    _pos = 'Noun'
                lexicon.append({'lemma': _w, 'pos': _pos, 'attributes': _attrs})
                _attrs_transferred += 1
            else:
                _is_verb = _w.endswith(('mak', 'mek')) and not _w.endswith(_noun_ends_excl)
                lexicon.append({'lemma': _w, 'pos': 'Verb' if _is_verb else 'Noun', 'attributes': []})
            _tdk_added += 1
    print(f"Added {_tdk_added:,} TDK|DD-only entries ({_attrs_transferred} with transferred Zemberek attributes).")

    # Zemberek also lists capitalized (name) variants of some words — e.g.
    # "Şecaat", "Şefaat", "Fesahat", "Rikkat" — as separate Noun entries.
    # Once lowercased they collide with the real word and, lacking the
    # inverse-harmony attribute, generate a spurious back-voiced twin
    # (şecaad, şefaad, fesahad, rikkad). Drop such capitalized duplicates;
    # proper nouns (pos='ProperNoun') are kept for the apostrophe logic, and
    # capitalized lemmas without a lowercase twin (Ingiltere, Bakü, ...) are
    # unaffected.
    _lc_lemmas = {_tlc(it.get('lemma', '')) for it in lexicon
                  if it.get('lemma') == _tlc(it.get('lemma', ''))}
    _dup_count = 0
    _kept = []
    for _it in lexicon:
        _l = _tlc(_it.get('lemma', ''))
        if (_it.get('pos') != 'ProperNoun'
                and _it.get('lemma') != _l
                and _l in _lc_lemmas):
            _dup_count += 1
            continue
        _kept.append(_it)
    if _dup_count:
        print(f"Dropped {_dup_count} capitalized duplicates colliding with lowercase lemmas.")
    lexicon = _kept

    for item in lexicon:
        lemma = item.get('lemma', '')
        if len(lemma) > 1 and lemma.isupper():
            ALL_CAPS_ABBREVS.add(lemma.replace('I', 'ı').replace('İ', 'i').lower())
    
    # We will define a set of flags for our paradigms:
    # 1: Back Vowel ending in Consonant (e.g., yol)
    # 2: Front Vowel ending in Consonant (e.g., gün)
    # 3: Back Vowel ending in Vowel (e.g., oda)
    # 4: Front Vowel ending in Vowel (e.g., kedi)
    # 5: Back Vowel ending in p/ç/t/k with Voicing (e.g., kitap -> kitab-)
    # 6: Front Vowel ending in p/ç/t/k with Voicing (e.g., ağaç -> ağac-)
    # 7: Back Vowel with Vowel Drop (e.g., akıl -> aklı)
    # 8: Front Vowel with Vowel Drop (e.g., şehir -> şehri)
    
    dic_entries = []
    voicing_map = {}
    
    # Create a mapping of custom lemmas to their custom pos and attributes
    custom_map = {e['lemma'].lower(): e for e in custom_entries}
    
    for item in lexicon:
        orig_lemma = item['lemma']
        if orig_lemma.lower() in ('tl', "tl'lik"):
            lemma = 'TL' if orig_lemma.lower() == 'tl' else "TL'lik"
        elif orig_lemma == 'Atatürk':
            lemma = 'Atatürk'
        elif orig_lemma.lower() == 'bi':
            lemma = 'Bi'
        else:
            lemma = orig_lemma.replace('I', 'ı').replace('İ', 'i').lower()
            
        if 'kağıt' in lemma:
            lemma = lemma.replace('kağıt', 'kâğıt')
        
        # Override with custom entry if present and has matching POS.
        # An empty custom "attributes" list means "unspecified", not "strip all
        # morphology" — abbreviation entries that case-collide with a real word
        # (ant/ANT, bağ, haz, öz) would otherwise silently drop Voicing /
        # NoVoicing / Doubling and break their inflected forms.
        custom_item = custom_map.get(lemma.lower())
        if custom_item and custom_item['pos'] == item['pos']:
            pos = custom_item['pos']
            attrs = set(custom_item['attributes']) or set(item['attributes'])
        else:
            pos = item['pos']
            attrs = set(item['attributes'])
        
        # Skip abbreviations, punctuation, or single-character noise
        # Skip empty or single-character noise
        if not lemma or len(lemma.strip()) == 0:
            continue

        # A '/' inside a lemma would be read by Hunspell as the flag separator,
        # turning the rest of the word into garbage flags. Source lists should
        # already be expanded upstream; this is the last line of defence.
        if '/' in lemma:
            print(f"  Skipping malformed lemma containing '/': {lemma!r}")
            continue


        # Skip short (1-3 char) zemberek 'PronunciationGuessed' entries — they are
        # chemical element symbols / abbreviations that produce spurious inflected
        # forms which silently accept misspellings (false negatives).
        # Exception: meaningful Turkish words like 'ay', 'çay', 'ray', 'çin', 'nil'.
        PRONUNCIATION_GUESSED_ALLOWLIST = {'ay', 'çay', 'ray', 'çin', 'nil', 'nil', 'rn', 'sir'}
        if (
            len(lemma) <= 3
            and 'PronunciationGuessed' in attrs
            and lemma.lower() not in PRONUNCIATION_GUESSED_ALLOWLIST
        ):
            continue

        # Skip dubious nouns/interjections that cause false negatives by accepting
        # fragment-inflections of misspelled words. These stems are either very rare,
        # not standard Turkish, or their morphological forms collide with common typos.
        FALSE_NEGATIVE_STEMS = {
            # Single/two-letter nouns that over-generate (caught by PronunciationGuessed
            # filter above for most, but these are in zemberek as normal entries)
            'ü',
            # 'bi' in zemberek as element Bismuth (no PronunciationGuessed) but causes
            # 'bideki' and similar to be accepted as misspellings of 'bindeki'
            'bi',
            # Short interjections being over-inflected  
            'hu', 'ole', 'be',
            # Dubious nouns whose inflected forms match misspellings
            'enç', 'havşa',
            'ikil', 'gelimli', 'cümlesi',
            # 'urmak' registered as Noun (it is a verb root, not a standalone noun)
            'urmak',
            # 'elmek' as Noun (it is a verb 'elmek' meaning to filter — but causes
            # 'elmeye' to be accepted, masking a misspelling of 'gelmeye')
            # 'elmek',
            # Stems causing V2 false negatives
            'pur', 'aysal', 'sahin', 'dölenme', 'çet', 'dölenmek',
        }
        if lemma.lower() in FALSE_NEGATIVE_STEMS and lemma != 'Bi':
            continue
            
        # Irregular word 'su' handling
        if lemma == 'su':
            dic_entries.append("su/3")
            dic_entries.append("suyu/3")
            dic_entries.append("suyun")
            dic_entries.append("suyunun")
            dic_entries.append("suya")
            dic_entries.append("suyu")
            dic_entries.append("suyunda")
            dic_entries.append("suyundan")
            dic_entries.append("suyuna")
            dic_entries.append("suyunu")
            dic_entries.append("suyuyla")
            dic_entries.append("sular/1")
            continue
 
        # Force common abbreviations to lowercase for optimal Hunspell case matching
        common_abbrevs = {'km', 'abd', 'örn', 'örn.', 'dr', 'dna', 'prof', 'x', 'mö', 'ms', 'sf', 'cm', 'kg', 'vb', 'bkz', 'm', 'g', 'b', 'mm', 'ml', 'gps', 'uuı', 'uv', 'bbc', 'vr', 'dr', 'eeg', 'yz', 'sscb', 'esa', 'rfid', 'dehb', 'mit', 'ngc', 'hiv', 'sls', 'atp', 'cern', 'iq', 'vb.', 't.c.'}
        if lemma.lower() in common_abbrevs:
            lemma = lemma.lower()
            
        noun_endings = (
            'parmak', 'ırmak', 'ekmek', 'yemek', 'çakmak', 'tokmak', 'yaşmak', 
            'kaymak', 'ilmek', 'basamak', 'mercimek', 'damak', 'yumak', 'oymak', 
            'yamak', 'hamak', 'sumak', 'kaçamak', 'kuymak', 'ramak', 'somak', 'tomak', 'emek'
        )
        if lemma.endswith(('mak', 'mek')) and (pos != 'Noun' or not lemma.endswith(noun_endings) or (lemma.endswith(('ilmek', 'inmek', 'ilmak', 'inmak', 'tırmak', 'tirmek', 'ırmak', 'irmek')) and lemma not in ['ilmek', 'ırmak'])):
            pos = 'Verb'
            
        # Force Noun POS and Voicing for any lemma ending in lık/lik/luk/lük
        if lemma.endswith(('lık', 'lik', 'luk', 'lük')):
            pos = 'Noun'
            attrs.add('Voicing')
            if 'NoVoicing' in attrs:
                attrs.discard('NoVoicing')
            if 'LastVowelDrop' in attrs:
                attrs.discard('LastVowelDrop')
            
        # Force Noun POS for any lemma ending in ıcı/ici/ucu/ücü (Deverbal Agent Nouns)
        if lemma.endswith(('ıcı', 'ici', 'ucu', 'ücü')):
            pos = 'Noun'
            
        if lemma == 'sahi':
            pos = 'Adverb'
            
        # Force Noun POS for any lemma ending in ış/iş/uş/üş that does not end in mak/mek (Deverbal Action Nouns)
        if lemma.endswith(('ış', 'iş', 'uş', 'üş')) and not lemma.endswith(('mak', 'mek')):
            pos = 'Noun'
            
        # Determine vowel harmony
        back = is_back_vowel(lemma)
        if lemma.lower() in ('vb.', 't.c.'):
            back = False
        if lemma.lower() in ('online', 'offline', 'server', 'wifi', 'wi-fi', 'wi', 'fi'):
            back = True
        # A few Arabic borrowings that Zemberek tags as inverse-harmony actually
        # take back suffixes in standard Turkish (TDK): emlak -> "emlakçı",
        # istihraç -> "maden istihracı". Force back harmony for them, and mark
        # emlak NoVoicing (it keeps the final k: "emlaka", "emlakın").
        if lemma.lower() in ('emlak', 'istihraç'):
            attrs.discard('InverseHarmony')
            attrs.discard('LastVowelFrontal')
            attrs.discard('FrontVowelHarmony')
            if lemma.lower() == 'emlak':
                attrs.add('NoVoicing')

        # Check Zemberek vowel exceptions
        if pos != 'Verb' and not lemma.endswith(('leşmek', 'laşmak', 'leşme', 'laşma', 'lik', 'lık', 'luk', 'lük', 'ci', 'cı', 'cu', 'cü', 'cilik', 'cılık', 'suz', 'süz', 'siz', 'suzluk', 'süzlük', 'sizlik')):
            if 'LastVowelFrontal' in attrs or 'FrontVowelHarmony' in attrs or 'InverseHarmony' in attrs:
                back = False
            
        # Inverse harmony overrides
        inverse_harmony_words = {'kalp', 'saat', 'harf', 'rol', 'alkol', 'hâl', 'hal', 'metal', 'normal', 'ideal', 'gol', 'kontrol', 'petrol', 'sembol', 'şefkat', 'dikkat', 'polifenol', 'flavanol', 'kortizol', 'istirahat'}
        if lemma.lower() in inverse_harmony_words or (pos != 'Verb' and (lemma.lower().endswith('âl') or lemma.lower().endswith('ûl'))):
            back = False

        # Inverse-harmony stems keep a back last vowel but take front suffixes.
        # The -lI derivation suffix is chosen by orthographic conditions, so for
        # these stems the regular LI block only yields the back form ("kontrollu",
        # not "kontrollü"). Mark them with numeric flag 91, which migrate_dictionary
        # expands to the front-only LF derivation flag (see gen_deriv_li2).
        inverse_harmony = (not back) and (get_last_vowel(lemma) or '') in 'aıouâû'

        vowel_end = ends_with_vowel(lemma)
        if lemma.lower() in ('vb.', 't.c.'):
            vowel_end = True
        if lemma.lower() in ('online', 'offline', 'wifi', 'wi-fi', 'wi', 'fi'):
            vowel_end = False
        
        # Check voicing attributes
        voicing = False
        if lemma[-1] in 'pçtkg':
            # Count vowels to check if multi-syllable
            all_vowel_chars = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
            num_vowels = sum(1 for c in lemma if c in all_vowel_chars)
            # Voicing applies when explicitly marked (Voicing/VoicingOpt/
            # VoicingSelf), to multi-syllable stems, or to a few manual
            # exceptions. Inverse-harmony borrowings (Arabic -at/-ak/-kat and
            # friends) keep their final consonant even when polysyllabic
            # (emlak -> emlaki, istirahat -> istirahati, idrak -> idraki), so
            # the multi-syllable heuristic is skipped for them; only stems with
            # an explicit Voicing attribute (kalp -> kalbi, harp -> harbi,
            # vaat -> vaadi) voice.
            if 'Voicing' in attrs or 'VoicingOpt' in attrs or 'VoicingSelf' in attrs or (not inverse_harmony and num_vowels >= 2) or lemma in ['teleskop', 'radyoteleskop', 'asteroit', 'eşlik', 'karbondioksit']:
                # Exclude explicitly marked NoVoicing and a few manual exceptions
                if ('NoVoicing' not in attrs or lemma in ['teleskop', 'radyoteleskop', 'eşlik', 'karbondioksit']) and lemma not in ['dikkat', 'sepet', 'paket', 'bilet', 'kaset', 'anket', 'davet', 'menfaat']:
                    voicing = True
        
        voicing_map[lemma.lower()] = voicing
        # Check vowel drop attributes
        if lemma in ['ağız', 'zehir']:
            attrs.add('LastVowelDrop')
        is_cik_ending = lemma.endswith(('cık', 'cik', 'cuk', 'cük', 'çık', 'çik', 'çuk', 'çük'))
        vowel_drop = 'LastVowelDrop' in attrs and not vowel_end and not is_cik_ending
        
        # Assign Flag
        flag = None
        if lemma == 'birbiri':
            flag = "14"
        elif pos in ['Noun', 'Adjective', 'Adverb', 'Numeral', 'Pronoun', 'Conjunction', 'Interjection', 'Duplicator', 'PostPositive', 'Determiner']:
            is_doubling = 'Doubling' in attrs
            if is_doubling:
                flag = "18" if back else "19"
            elif 'CompoundP3sg' in attrs:
                flag = "13" if back else "14"
            elif vowel_drop:
                flag = "7" if back else "8"
            elif voicing:
                voiced_stem = get_voiced_stem(lemma)
                if voiced_stem and voiced_stem != lemma:
                    flag = "5" if back else "6"
                else:
                    voicing = False
                    if vowel_end:
                        flag = "3" if back else "4"
                    else:
                        flag = "1" if back else "2"
            else:
                if vowel_end:
                    flag = "3" if back else "4"
                else:
                    flag = "1" if back else "2"
        elif pos == 'Verb':
            voicing = 'Voicing' in attrs
            # Determine if stem ends in a vowel before stripping mak/mek
            root = lemma[:-3] if lemma.endswith(('mak', 'mek')) else lemma
            vowel_end = ends_with_vowel(root)
            
            # Voicing only applies if the root ends in a voicing consonant
            is_voicing_stem = voicing and len(root) > 0 and root[-1] in 'pçtk'
            
            if lemma in ['demek', 'yemek']:
                flag = "17"
            elif is_voicing_stem:
                flag = "15" if back else "16"
            elif vowel_end:
                flag = "11" if back else "12"
            else:
                all_vowels = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
                num_vowels = sum(1 for c in root if c in all_vowels)
                aorist_i_exceptions = {
                    'al', 'bil', 'bul', 'dur', 'gel', 'gör', 'kal', 'ol', 'öl', 'san', 'var', 'ver', 'vur', 'yen'
                }
                
                is_aorist_i = 'Aorist_I' in attrs or (num_vowels > 1) or (root in aorist_i_exceptions)
                is_aorist_a = 'Aorist_A' in attrs or (num_vowels == 1 and root not in aorist_i_exceptions)
                
                if is_aorist_i and not is_aorist_a:
                    flag = "21" if back else "23" # wi or wj
                elif is_aorist_a and not is_aorist_i:
                    flag = "20" if back else "22" # wa or we
                else:
                    flag = "9" if back else "10"
        elif pos == 'Question':
            flag = "3" if back else "4"
            
        if flag:
            # Determine if last vowel is rounded
            target_word = lemma
            if pos == 'Verb':
                target_word = lemma[:-3] if lemma.endswith(('mak', 'mek')) else lemma
            
            # For vowel-ending verb stems, we check the vowel before the final vowel to determine rounding
            if pos == 'Verb' and ends_with_vowel(target_word) and len(target_word) > 1:
                stem_before_vowel = target_word[:-1]
                last_v = get_last_vowel(stem_before_vowel)
                if not last_v:
                    last_v = get_last_vowel(target_word)
            else:
                last_v = get_last_vowel(target_word)
                
            is_rounded = last_v in 'oöuüû' if last_v else False
            
            if flag in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "18", "19"] and is_rounded:
                flag = str(int(flag) + 100)
                
            PREFIXABLE_STEMS = {
                'saniye', 'dakika', 'saat', 'gün', 'yıl', 'bayt', 'bit', 'gram', 'metre', 'volt', 'amper',
                'hertz', 'litre', 'watt', 'vat', 'piksel', 'kalori', 'madde', 'parçacık', 'aktif', 'kontrol',
                'virüs', 'saldırı', 'güvenlik', 'teknoloji', 'bilim', 'bilimci', 'yönelim', 'tür',
                'hücre', 'dalga', 'işlemci', 'çip', 'yapı', 'plastik', 'baskı', 'alerjen', 'inflamatuvar',
                'enflamatuvar', 'depresan', 'immün', 'dejeneratif', 'baskılayıcı', 'yazıcı', 'oksidan', 'transmiter', 'transmitter',
                'kütle', 'mikrobiyal'
            }
            if lemma.lower() in PREFIXABLE_STEMS:
                flag = f"{flag},90"
            if inverse_harmony:
                flag = f"{flag},91"
                
            dic_entries.append(f"{lemma}/{flag}")
            if voicing and pos != 'Verb':
                voiced_stem = get_voiced_stem(lemma)
                if voiced_stem and voiced_stem != lemma:
                    dic_entries.append(f"{voiced_stem}/{flag},NE,only_vowel")
        else:
            dic_entries.append(lemma)
            
    print(f"Mapped {len(dic_entries)} dictionary entries.")

    # -----------------------------------------------------------------------
    # Proper-noun apostrophe-suffix flag injection
    # -----------------------------------------------------------------------
    # The proper noun flags (pBN/pBL/pBR … pFN/pFL …) are defined in
    # generate_grammar_rules.py but were never referenced in the .dic.
    # We inject them here by appending the correct family chain to every
    # entry that represents a proper noun stored in lowercase.
    #
    # Family selection is based on the last vowel of the lemma:
    #   a / ı  ->  pB  (back-unrounded:  'ın, 'da, 'dan, 'a  …)
    #   o / u  ->  pO  (back-rounded:    'un, 'da, 'dan, 'a  …)
    #   e / i  ->  pF  (front-unrounded: 'in, 'de, 'den, 'e  …)
    #   ö / ü  ->  pU  (front-rounded:   'ün, 'de, 'den, 'e  …)
    # No vowel (e.g. 'mm') defaults to back-unrounded (pB).
    #
    # Each family exposes 8 sub-flags: N L R Y A I P C
    # (genitive, locative, ablative, dative, accusative, instrumental,
    #  3sg-possessive, copula)
    PROPER_HARMONY = {
        'a': 'pB', 'ı': 'pB',
        'o': 'pO', 'u': 'pO',
        'e': 'pF', 'i': 'pF',
        'ö': 'pU', 'ü': 'pU',
    }
    PROPER_SUB_FLAGS = list('NLRYAIPC')

    # Map of lemma -> proper-noun flag prefix (overrides auto-detection)
    # Add entries here whenever a word needs an explicit override.
    PROPER_NOUN_OVERRIDES: dict[str, str] = {
        # --- Back-unrounded (a/ı) ---
        'ankara':      'pB',
        'diyarbakır':  'pB',
        'yunanistan':  'pB',
        'havalimanı':  'pB',
        'havaalanı':   'pB',
        'cumhurbaşkanı': 'pB',
        'adnan':       'pB',
        'esenboğa':    'pB',
        'sabiha':      'pB',
        'irlanda':     'pB',
        'izlanda':     'pB',
        'iskoçya':     'pB',
        'ocak':        'pB',
        'şubat':       'pB',
        'mart':        'pB',
        'nisan':       'pB',
        'mayıs':       'pB',
        'haziran':     'pB',
        'kasım':       'pB',
        'aralık':      'pB',
        'bakanlık':    'pB',
        'bakanlığı':   'pB',
        'başkanlık':   'pB',
        'başkanlığı':  'pB',
        'kaymakamlık': 'pB',
        'kaymakamlığı':'pB',
        'vakıf':       'pB',
        'vakfı':       'pB',
        'oda':         'pB',
        'odası':       'pB',
        'saray':       'pB',
        'sarayı':      'pB',
        'sokak':       'pB',
        'sokağı':      'pB',
        'meydan':      'pB',
        'meydanı':     'pB',
        'park':        'pB',
        'parkı':       'pB',
        'dağ':         'pB',
        'dağı':        'pB',
        'ada':         'pB',
        'adası':       'pB',
        'almanya':     'pB',
        'fransa':      'pB',
        'italya':      'pB',
        'ispanya':     'pB',
        'japonya':     'pB',
        'rusya':       'pB',
        'brezilya':    'pB',
        'meksika':     'pB',
        'hollanda':    'pB',
        'belçika':     'pB',
        'avusturya':   'pB',
        'hindistan':   'pB',
        'avustralya':  'pB',
        'kanada':      'pB',
        'danimarka':   'pB',
        'finlandiya':  'pB',
        'polonya':     'pB',
        'romanya':     'pB',
        'bulgaristan': 'pB',
        'sırbistan':   'pB',
        'hırvatistan': 'pB',
        'macaristan':  'pB',
        'slovakya':    'pB',
        'çekya':       'pB',
        'ukrayna':     'pB',
        'gürcistan':   'pB',
        'ermenistan':  'pB',
        'azerbaycan':  'pB',
        'kazakistan':  'pB',
        'özbekistan':  'pB',
        'irak':        'pB',
        'iran':        'pB',
        'mısır':       'pB',
        'fas':         'pB',
        'kenya':       'pB',
        'nijerya':     'pB',
        'etyopya':     'pB',
        'etiopya':     'pB',
        'antalya':     'pB',
        'bursa':       'pB',
        'adana':       'pB',
        'konya':       'pB',
        'adapazarı':   'pB',
        'malatya':     'pB',
        'van':         'pB',
        'batman':      'pB',
        'şanlıurfa':   'pB',
        'hatay':       'pB',
        'manisa':      'pB',
        'tekirdağ':    'pB',
        'muğla':       'pB',
        'kahramanmaraş': 'pB',
        'londra':      'pB',
        'moskova':     'pB',
        'roma':        'pB',
        'amsterdam':   'pB',
        'viyana':      'pB',
        'atina':       'pB',
        'kopenhag':    'pB',
        'varşova':     'pB',
        'prag':        'pB',
        'belgrad':     'pB',
        'sofya':       'pB',
        'new york':    'pB',
        'newyork':     'pB',

        # --- Back-rounded (o/u) ---
        'istanbul':    'pO',
        'temmuz':      'pO',
        'ağustos':     'pO',
        'okul':        'pO',
        'okulu':       'pO',
        'tiyatro':     'pO',
        'tiyatrosu':   'pO',
        'okyanus':     'pO',
        'okyanusu':    'pO',
        'anadolu':     'pO',
        'trabzon':     'pO',
        'ordu':        'pO',
        'samsun':      'pO',
        'erzurum':     'pO',
        'tunus':       'pO',
        'lizbon':      'pO',
        'stockholm':   'pO',
        'oslo':        'pO',
        'tokyo':       'pO',
        'seul':        'pO',
        'washington':  'pO',
        'toronto':     'pO',

        # --- Front-unrounded (e/i) ---
        'türkiye':     'pF',
        'şii':         'pF',
        'galler':      'pF',
        'isviçre':     'pF',
        'ekim':        'pF',
        'üniversite':  'pF',
        'üniversitesi':'pF',
        'fakülte':     'pF',
        'fakültesi':   'pF',
        'lise':        'pF',
        'lisesi':      'pF',
        'kolej':       'pF',
        'koleji':      'pF',
        'hastane':     'pF',
        'hastanesi':   'pF',
        'belediye':    'pF',
        'belediyesi':  'pF',
        'valilik':     'pF',
        'valiliği':    'pF',
        'dernek':      'pF',
        'derneği':     'pF',
        'birlik':      'pF',
        'birliği':     'pF',
        'müze':        'pF',
        'müzesi':      'pF',
        'kütüphane':   'pF',
        'kütüphanesi': 'pF',
        'cadde':       'pF',
        'caddesi':     'pF',
        'nehir':       'pF',
        'nehri':       'pF',
        'deniz':       'pF',
        'denizi':      'pF',
        'körfez':      'pF',
        'körfezi':     'pF',
        'izmir':       'pF',
        'edirne':      'pF',
        'ingiltere':   'pF',
        'yandex':      'pF',
        'maps':        'pF',
        'navi':        'pF',
        'gökçen':      'pF',
        'menderes':    'pF',
        'merkez':      'pF',
        'sahne':       'pF',
        'merkezi':     'pF',
        'sahnesi':     'pF',
        'portekiz':    'pF',
        'çin':         'pF',
        'arjantin':    'pF',
        'norveç':      'pF',
        'isveç':       'pF',
        'suriye':      'pF',
        'cezayir':     'pF',
        'gaziantep':   'pF',
        'kayseri':     'pF',
        'mersin':      'pF',
        'eskişehir':   'pF',
        'denizli':     'pF',
        'kocaeli':     'pF',
        'balıkesir':   'pF',
        'berlin':      'pF',
        'paris':       'pF',
        'madrid':      'pF',
        'brüksel':     'pF',
        'helsinki':    'pF',
        'budapeşte':   'pF',
        'bükreş':      'pF',
        'kiev':        'pF',
        'tiflis':      'pF',
        'taşkent':     'pF',
        'pekin':       'pF',
        'mumbai':      'pF',
        'dubai':       'pF',
        'kahire':      'pF',
        'tl':          'pF',
        'kemal':       'pF',

        # --- Front-rounded (ö/ü) ---
        'bakü':        'pU',
        'atatürk':     'pU',
        'eylül':       'pU',
        'enstitü':     'pU',
        'enstitüsü':   'pU',
        'müdürlük':    'pU',
        'müdürlüğü':   'pU',
        'kulüp':       'pU',
        'kulübü':      'pU',
        'köprü':       'pU',
        'köprüsü':     'pU',
        'göl':         'pU',
        'gölü':        'pU',

        # Abbreviations/units: no vowel -> back-unrounded by convention
        'mm':        'pB',
        'cm':        'pB',
        'km':        'pF',  # Pronounced 'kay-me' / 'kilometre' -> front vowel harmony
        'kg':        'pB',
        'abd':       'pF',  # 'a-be-de' -> front vowel harmony
        'dna':       'pB',  # 'de-ne-a' -> back vowel harmony
        'sibirya':   'pB',
        'himalayalar': 'pB',
        'dünya':     'pB',
        'zelanda':   'pB',
        'alaska':    'pB',
        'atlantik':  'pF',
        'paralimpik': 'pF',
        'seddi':     'pF',
        'kutbu':     'pO',
        'dağları':   'pB',
        'bahamalar': 'pB',
        'neandertal': 'pF',
        'pers':      'pF',
        'burnu':     'pO',
        'üssü':      'pU',
        'computer':  'pB',
        'amerika birleşik devletleri': 'pF',
        'devletleri': 'pF',
        'ml': 'pF',
        # Tech words harmony overrides
        'online':    'pB',
        'offline':   'pB',
        'server':    'pB',
        'chat':      'pF',
        'wifi':      'pB',
        'wi-fi':     'pB',
        'wi':        'pB',
        'fi':        'pB',
    }

    # Collect all nouns from lexicon to apply proper noun suffix + KC rules
    noun_lemmas = set()
    for item in lexicon:
        if item.get('pos') == 'Noun':
            noun_lemmas.add(item['lemma'].replace('I', 'ı').replace('İ', 'i').lower())

    # Every lemma that also exists as an ordinary (non-proper) word, across all
    # parts of speech. An uppercase abbreviation may case-fold onto a real
    # lowercase word (AKUT/akut "acute", RAM/ram, FM/fm, SEK/sek); without this
    # the lowercase form is silently replaced by the abbreviation and stops
    # being recognised. noun_lemmas alone misses Adjective/Adverb/Interjection.
    common_lemmas = set()
    for item in lexicon:
        if item.get('pos') != 'ProperNoun' and item.get('lemma'):
            common_lemmas.add(item['lemma'].replace('I', 'ı').replace('İ', 'i').lower())

    # Words that should get proper-noun suffix flags.
    proper_nouns_to_flag: set[str] = set(PROPER_NOUN_OVERRIDES.keys())
    proper_nouns_attrs_map: dict[str, set] = {}
    for item in lexicon:
        if item.get('pos') == 'ProperNoun':
            lk = item['lemma'].replace('I', 'ı').replace('İ', 'i').lower()
            proper_nouns_to_flag.add(lk)
            proper_nouns_attrs_map[lk] = set(item.get('attributes', []))

    for item in custom_entries:
        if isinstance(item, dict) and item.get('pos') == 'ProperNoun':
            lk = item['lemma'].replace('I', 'ı').replace('İ', 'i').lower()
            proper_nouns_to_flag.add(lk)
            proper_nouns_attrs_map[lk] = set(item.get('attributes', []))

    # Remove proper nouns from noun_lemmas to prevent them from being treated as common nouns
    # noun_lemmas = noun_lemmas - proper_nouns_to_flag

    def _proper_flag_for(lemma_lower: str, attrs: set = None) -> str:
        if attrs and 'InverseHarmony' in attrs:
            return 'pF'
        if lemma_lower in PROPER_NOUN_OVERRIDES:
            return PROPER_NOUN_OVERRIDES[lemma_lower]
        # Turkish consonant-only abbreviations (e.g. TDK, TBMM, TRT, SGK, BDDK, THY, TSK, CHP, MHP, AKP, MİT, LGS, YKS)
        has_vowels = any(c in 'aeıioöuüâîû' for c in lemma_lower)
        if not has_vowels:
            return 'pF'  # Turkish letters are read with 'e' (te-de-ke, se-ge-ke, te-re-te, etc.)
        lv = get_last_vowel(lemma_lower)
        return PROPER_HARMONY.get(lv, 'pB')  # default back-unrounded

    # Rebuild dic_entries, enforcing capitalization with KEEPCASE (KC)
    new_dic_entries = []
    seen_overrides = set()
    
    # Derived proper noun patterns that MUST NOT take apostrophes (TDK rule: yapım eki almış özel adlara kesme konmaz)
    derived_no_apostrophe_suffixes = ('ce', 'ca', 'çe', 'ça', 'lı', 'li', 'lu', 'lü', 'lık', 'lik', 'luk', 'lük')
    
    for entry in dic_entries:
        if not entry or not entry.strip():
            continue
        if '/' in entry:
            lemma_part, flags_part = entry.split('/', 1)
        else:
            lemma_part, flags_part = entry, ''

        if not lemma_part or not lemma_part.strip():
            continue

        if 'only_vowel' in flags_part:
            new_dic_entries.append(entry)
            continue

        lkey = lemma_part.lower()

        if lkey == 't.c.':
            new_dic_entries.append(f"T.C./{flags_part},KC" if flags_part else "T.C./KC")
            continue

        # Case 1: Word is a proper noun (e.g. Ankara, TDK, Atatürk, or overrides like Temmuz, İrlanda)
        if lkey in proper_nouns_to_flag:
            is_derived_proper = lkey.endswith(derived_no_apostrophe_suffixes) and lkey not in PROPER_NOUN_OVERRIDES
            if is_derived_proper:
                # Derived proper noun (e.g. Türkçe, Ankaralı, Türklük): takes standard case flags WITHOUT apostrophes
                cap_lemma = capitalize_word(lkey, lkey)
                new_entry = f"{cap_lemma}/{flags_part},KC" if flags_part else f"{cap_lemma}/KC"
                new_dic_entries.append(new_entry)
            else:
                item_attrs = proper_nouns_attrs_map.get(lkey, set())
                pfx = _proper_flag_for(lkey, item_attrs)
                proper_flags = ','.join(f'{pfx}{s}' for s in PROPER_SUB_FLAGS)
                # For lowercase abbreviations/units (like km, cm, mm, kg, gr), keep them lowercase and add proper noun flags
                if lkey in {'km', 'cm', 'mm', 'kg', 'gr'}:
                    new_entry = f"{lkey}/{proper_flags}"
                    new_dic_entries.append(new_entry)
                else:
                    cap_lemma = capitalize_word(lkey, lkey)
                    # Rebuild entry as capitalized with proper noun flags
                    if flags_part:
                        new_entry = f"{cap_lemma}/{flags_part},{proper_flags}"
                    else:
                        new_entry = f"{cap_lemma}/{proper_flags}"
                    new_dic_entries.append(new_entry)
            
            if lkey in PROPER_NOUN_OVERRIDES:
                seen_overrides.add(lkey)
            
            # If it also functions as a common word (e.g. Temmuz, akut, ram),
            # keep the lowercase entry alongside the proper-noun one.
            if lkey in common_lemmas:
                if lkey in {'km', 'cm', 'mm', 'kg', 'gr', 'şii'}:
                    pass
                else:
                    new_dic_entries.append(f"{lkey}/{flags_part}" if flags_part else lkey)

        # Case 2: Word is a common noun (but not explicitly tagged as proper noun/override)
        elif lkey in noun_lemmas:
            # Attach proper noun flags directly to the lowercase entry (Alternative 1)
            item_attrs = proper_nouns_attrs_map.get(lkey, set())
            pfx = _proper_flag_for(lkey, item_attrs)
            proper_flags = ','.join(f'{pfx}{s}' for s in PROPER_SUB_FLAGS)
            
            if flags_part:
                new_dic_entries.append(f"{lkey}/{flags_part},{proper_flags}")
            else:
                new_dic_entries.append(f"{lkey}/{proper_flags}")

        # Case 3: Other POS (verbs, adjectives, etc.) — leave as-is
        else:
            new_dic_entries.append(entry)

    # Inject missing overrides directly as capitalized stems with KC
    for key, pfx in PROPER_NOUN_OVERRIDES.items():
        if key not in seen_overrides:
            extra = ','.join(f'{pfx}{s}' for s in PROPER_SUB_FLAGS)
            cap_key = capitalize_word(key, key)
            new_dic_entries.append(f"{cap_key}/{extra},KC")

    dic_entries = new_dic_entries
    print(f"Injected proper-noun flags into {sum(1 for e in dic_entries if any(f'p{x}N' in e for x in 'BOFU'))} entries.")

    print("Writing tr.dic...")
    with open(os.path.join(base_dir, 'tr.dic'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"{len(dic_entries)}\n")
        for entry in dic_entries:
            f.write(f"{entry}\n")
            
    # Write tr.aff by calling our generator script
    print("Calling generate_grammar_rules.py to generate baseline rules...")
    from generate_grammar_rules import generate_grammar
    generate_grammar()
    
    # Now remap tr.aff in-place to FLAG UTF-8
    print("Remapping rules to FLAG UTF-8 and writing to tr.aff...")
    with open(os.path.join(base_dir, 'tr.aff'), 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = content.replace("FLAG long", "FLAG UTF-8")
    if "NEEDAFFIX NE" in content:
        content = content.replace("NEEDAFFIX NE", f"NEEDAFFIX {LONG_TO_UTF8['NE']}")
    if "KEEPCASE KC" in content:
        content = content.replace("KEEPCASE KC", f"KEEPCASE {LONG_TO_UTF8['KC']}")
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith('#'):
            new_lines.append(line)
            continue
        parts = line.split()
        if len(parts) == 2 and parts[0] == 'NOSUGGEST':
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
            new_lines.append(" ".join(parts))
        elif len(parts) >= 4 and parts[0] in ('SFX', 'PFX') and parts[2] in ('Y', 'N'):
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
            new_lines.append(" ".join(parts))
        elif len(parts) >= 2 and parts[0] in ('SFX', 'PFX'):
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
            if len(parts) >= 4:
                add_field = parts[3]
                if '/' in add_field:
                    prefix_str, flags_str = add_field.split('/', 1)
                    remapped_flags = remap_flag_string(flags_str)
                    parts[3] = f"{prefix_str}/{remapped_flags}"
            new_lines.append(" ".join(parts))
        else:
            new_lines.append(line)
            
    # Separate header lines from SFX/PFX blocks in tr.aff and sort SFX/PFX blocks alphabetically
    header_lines = []
    sfx_blocks = {}  # flag -> list of lines
    curr_flag = None
    for line in new_lines:
        line_strip = line.strip()
        if len(line_strip.split()) >= 2 and line_strip.split()[0] in ('SFX', 'PFX'):
            flag = line_strip.split()[1]
            curr_flag = flag
            if curr_flag not in sfx_blocks:
                sfx_blocks[curr_flag] = []
            sfx_blocks[curr_flag].append(line)
        elif curr_flag is not None and (not line_strip or line_strip.startswith('#')):
            # trailing comments/blank lines end the block
            curr_flag = None
            header_lines.append(line)
        elif curr_flag is not None:
            sfx_blocks[curr_flag].append(line)
        else:
            header_lines.append(line)

    # Drop exactly-duplicated rules within each block. Hunspell applies the
    # first match, so a byte-identical repeat is dead weight — it only inflates
    # the file and the load-time rule table. The block header declares its rule
    # count, so it has to be rewritten to match or Hunspell misparses the block.
    _aff_dropped = 0
    for flag, block in sfx_blocks.items():
        header, rules = block[0], block[1:]
        seen = set()
        kept = []
        for r in rules:
            key = r.strip()
            if key in seen:
                _aff_dropped += 1
                continue
            seen.add(key)
            kept.append(r)
        parts = header.split()
        if len(parts) >= 4 and parts[2] in ('Y', 'N'):
            parts[3] = str(len(kept))
            header = " ".join(parts)
        sfx_blocks[flag] = [header] + kept

    if _aff_dropped:
        print(f"Removed {_aff_dropped:,} duplicate affix rules.")

    sorted_aff_content = "\n".join(header_lines).rstrip() + "\n\n"
    for flag in sorted(sfx_blocks.keys()):
        sorted_aff_content += "\n".join(sfx_blocks[flag]) + "\n\n"

    with open(os.path.join(base_dir, 'tr.aff'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(sorted_aff_content.strip() + "\n")

    # Remap tr.dic in-place: convert numeric flags + 3-char proper-noun flags to UTF-8
    print("Remapping tr.dic to FLAG UTF-8...")
    import sys
    sys.path.insert(0, base_dir)
    from tools.migrate_dictionary import migrate_line as _migrate_line
    with open(os.path.join(base_dir, 'tr.dic'), 'r', encoding='utf-8') as f:
        dic_raw_lines = f.readlines()
    dic_count_str = dic_raw_lines[0].strip()
    dic_data = dic_raw_lines[1:]
    dic_out = []
    dic_migrated = 0
    for _i, _line in enumerate(dic_data, start=2):
        _ls = _line.rstrip()
        if not _ls or _ls.startswith('#'):
            continue
        if '/' not in _ls:
            dic_out.append(_ls + '\n')
            dic_migrated += 1
            continue
        _word, _flag_part = _ls.split('/', 1)
        _parts = _flag_part.split(',')
        _only_vowel = 'only_vowel' in _parts
        _parts = [p for p in _parts if p != 'only_vowel']
        _numeric = [p.strip() for p in _parts if not (p.strip().startswith('p') and len(p.strip()) == 3)]
        _proper  = [p.strip() for p in _parts if p.strip().startswith('p') and len(p.strip()) == 3]
        if _numeric:
            _fake = _word + '/' + ','.join(_numeric)
            _mig, _ = _migrate_line(_fake, _i, set(), only_vowel=_only_vowel)
            if _mig and '/' in _mig:
                _w2, _fc = _mig.split('/', 1)
                _utf8 = remap_flag_string(_fc)
            else:
                _w2, _utf8 = _word, ''
        else:
            _w2, _utf8 = _word, ''
        if _proper:
            _utf8 += ''.join(LONG_TO_UTF8[p] for p in _proper if p in LONG_TO_UTF8)
        dic_out.append((_w2 + '/' + _utf8 if _utf8 else _w2) + '\n')
        dic_migrated += 1

    # Drop byte-identical duplicate entries. These come from lemmas that appear
    # more than once in the source lexicon under different POS (e.g. 'rate' as
    # both Noun and Adjective) but map to the same stem class and flag chain.
    # Entries for the same word with *different* flags are kept: Hunspell treats
    # them as homonyms and each contributes its own paradigm.
    _seen_entries = set()
    _deduped = []
    for _e in dic_out:
        if _e in _seen_entries:
            continue
        _seen_entries.add(_e)
        _deduped.append(_e)
    _dic_dropped = len(dic_out) - len(_deduped)
    dic_out = _deduped
    dic_migrated = len(dic_out)
    if _dic_dropped:
        print(f"Removed {_dic_dropped:,} duplicate dictionary entries.")

    # Sort tr.dic entries alphabetically for easier navigation
    dic_out.sort(key=lambda s: (s.split('/')[0].lower(), s))

    with open(os.path.join(base_dir, 'tr.dic'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(str(dic_migrated) + '\n')
        f.writelines(dic_out)
    print(f"tr.dic remapped: {dic_migrated} entries.")

    print("Compile complete!")

    # Validate the pair we just wrote. A build that produced a broken or
    # incomplete dictionary must not report success.
    print("\nValidating output...")
    from validate_build import validate
    errors, warnings = validate(os.path.join(base_dir, 'tr.dic'), os.path.join(base_dir, 'tr.aff'))
    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR:   {e}")
    if errors:
        raise SystemExit(
            f"\nBuild produced an invalid dictionary: {len(errors)} error(s). "
            f"tr.dic/tr.aff should not be shipped."
        )
    print(f"Validation passed ({len(warnings)} warning(s)).")

if __name__ == "__main__":
    compile_dictionary()
