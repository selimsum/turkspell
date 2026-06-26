import os

def generate_grammar():
    # Headers
    content = """# Türkçe Yazım Denetimi Sözlüğü - Üretilmiş Affix Rules
SET UTF-8
FLAG num
LANG tr

# Suggestion parameters
TRY aıeiouödgbsnrlhmyçtzkşvğpcfjAIEİOUÖDGBSNRLHMYÇTZKŞVĞPCFJ
KEY qwertyuıopğü|asdfghjklşi|zxcvbnmçö|fgğıodrnhpqw|uıevazyktsx|jövcçzsb
MAP 9
MAP aâAÂ
MAP uûUÛ
MAP iîİÎ
MAP cçCÇ
MAP gğGĞ
MAP sşSŞ
MAP oöOÖ
MAP uüUÜ
MAP ıiIİ
MAXDIFF 2

REP 28
REP a â
REP â a
REP u û
REP û u
REP i î
REP î i
REP c ç
REP ç c
REP g ğ
REP ğ g
REP s ş
REP ş s
REP o ö
REP ö o
REP u ü
REP ü u
REP ı i
REP i ı
REP sh ş
REP ch ç
REP gh ğ
REP ss ş
REP dd t
REP tt d
REP bb p
REP pp b
REP cc c
REP kk g
"""

    # Vowel/Consonant copula templates
    COPULAS_VOWEL = ["ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr", "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr", "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr", "yIm", "sIn", "yIz", "sInIz", "lAr", "dIr", "dIrlAr", "lArdIr", "yken", "ydIlArdI", "ymIşlArdI", "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr"]
    COPULAS_CONS = [
        "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
        "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
        "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
        "Im", "sIn", "Iz", "sInIz", "lAr", "dIr", "tIr", "dIrlAr", "tIrlAr", "lArdIr", "ken",
        "dIlArdI", "tIlArdI", "mIşlArdI", "ImdIr", "sIndIr", "IzdIr", "sInIzdIr"
    ]

    # Vowel Harmony Simulator for Noun Copulas and Verbs
    def append_suffix_harmonized(stem, template):
        unvoiced_chars = set('pçtksşhf')
        vowels = set('aeıioöuüâîû')
        
        def get_last_vowel(s):
            for ch in reversed(s):
                if ch in vowels:
                    return ch.lower()
            return 'a' # default fallback
            
        res = list(stem)
        for i, char in enumerate(template):
            last_v = get_last_vowel(''.join(res))
            last_c = res[-1] if res else ''
            
            if char in 'AIU' and last_c in vowels:
                is_pres_cont = (char == 'I' and template[i:i+4] == 'Iyor')
                if not is_pres_cont:
                    res.append('y')
                    last_c = 'y'
                
            if char == 'A':
                res.append('a' if last_v in 'aıouâû' else 'e')
            elif char == 'I':
                if last_v in 'aıâ':
                    res.append('ı')
                elif last_v in 'eiî':
                    res.append('i')
                elif last_v in 'ouû':
                    res.append('u')
                else:
                    res.append('ü')
            elif char == 'U':
                res.append('u' if last_v in 'aıouâû' else 'ü')
            elif char == 'D':
                res.append('t' if last_c in unvoiced_chars else 'd')
            elif char == 'C':
                res.append('ç' if last_c in unvoiced_chars else 'c')
            else:
                res.append(char)
                
        return ''.join(res)[len(stem):]

    def get_noun_continuation_flag(resolved_sfx):
        vowels = 'aeıioöuüâîû'
        last_v = None
        for ch in reversed(resolved_sfx):
            if ch in vowels:
                last_v = ch.lower()
                break
        if not last_v:
            return ""
            
        is_back = last_v in 'aıouâû'
        is_rounded = last_v in 'oöuüû'
        last_char = resolved_sfx[-1]
        
        if last_char in 'aeıioöuü':
            if is_back:
                return "183" if is_rounded else "83"
            else:
                return "184" if is_rounded else "84"
        elif last_char == 'k':
            if is_back:
                return "185" if is_rounded else "85"
            else:
                return "186" if is_rounded else "86"
        else:
            if is_back:
                return "181" if is_rounded else "81"
            else:
                return "182" if is_rounded else "82"

    # Helper function to generate combinations for a noun paradigm (two-fold)
    def generate_noun_sfx(flag, back_vowel, vowel_end, rounded, voicing=False, vowel_drop=False, doubling=False):
        # Determine sim stems to cover rounded/unrounded/voiced/unvoiced harmony
        if vowel_end:
            if rounded:
                stems = ["kutu"] if back_vowel else ["ütü"]
            else:
                stems = ["oda"] if back_vowel else ["kedi"]
        else:
            if rounded:
                stems = ["uç", "bul"] if back_vowel else ["düş", "gör"]
            else:
                stems = ["yap", "kal"] if back_vowel else ["git", "gel"]

        def append_noun_rule(lines, flag, suffix, cont_flag=None):
            if not suffix:
                return
            starts_unvoiced = suffix[0] in 'tç'
            starts_voiced = suffix[0] in 'dc'
            
            add_part = f"{suffix}/{cont_flag}" if cont_flag else suffix
            
            if starts_unvoiced:
                lines.append(f"SFX {flag} 0 {add_part} [çfhkpsşt]")
            elif starts_voiced:
                lines.append(f"SFX {flag} 0 {add_part} [^çfhkpsşt]")
            else:
                lines.append(f"SFX {flag} 0 {add_part} .")

        rules = []
        is_first_fold = flag not in [81, 82, 83, 84, 85, 86, 181, 182, 183, 184, 185, 186]

        if is_first_fold:
            # First Fold: Derivational suffixes and Plurals
            # Restrict derivational suffixes to keep tr.aff under 10MB
            if flag in [1, 2, 3, 4, 101, 102, 103, 104]:
                derivs = ["", "lI", "sIz", "lIk", "cIk", "cIm", "CI"]
            elif flag in [5, 6, 105, 106]:
                derivs = ["", "lI", "sIz", "lIk", "CI"]
            else:
                derivs = [""]
            
            plurals = ["", "lAr"]
            
            for deriv in derivs:
                for pl in plurals:
                    if deriv == "" and pl == "":
                        continue  # Empty suffix is skipped in first fold (handled directly by assigning second-fold flag to stem)
                    
                    for sim_stem in stems:
                        base_template = deriv + pl
                        base_sfx = append_suffix_harmonized(sim_stem, base_template)
                        if base_sfx:
                            cont_flag = get_noun_continuation_flag(base_sfx)
                            rules.append((base_sfx, cont_flag))
        else:
            # Second Fold: Possessives, Cases, Relatives, Copulas
            derivs = [""]
            plurals = [""]
            
            for deriv in derivs:
                current_vowel_end = vowel_end
                
                if current_vowel_end:
                    possessives = ["", "m", "n", "sI", "mIz", "nIz", "lArI"]
                else:
                    possessives = ["", "Im", "In", "I", "ImIz", "InIz", "lArI"]
                
                for sim_stem in stems:
                    for poss in possessives:
                        actual_poss = poss
                        # 3rd person possessives end in vowel, and take buffer 'n' before cases
                        is_3rd_person = actual_poss in ['I', 'sI', 'lArI']

                        # Case templates
                        if is_3rd_person:
                            cases = ['', 'nA', 'nI', 'ndA', 'ndAn', 'nIn', 'ylA', 'ncA']
                        else:
                            if (actual_poss or not current_vowel_end):
                                cases = ['', 'A', 'I', 'DA', 'DAn', 'In', 'lA', 'CA']
                            else:
                                cases = ['', 'yA', 'yI', 'DA', 'DAn', 'nIn', 'ylA', 'CA']

                        for case in cases:
                            starts_with_vowel = False
                            if actual_poss in ['Im', 'In', 'I', 'ImIz', 'InIz']:
                                starts_with_vowel = True
                            elif not actual_poss and case in ['A', 'I']:
                                starts_with_vowel = True

                            base_template = actual_poss + case
                            base_sfx = append_suffix_harmonized(sim_stem, base_template)
                            if base_sfx:
                                rules.append(base_sfx)

                            # Determine if resolved base suffix ends in a vowel
                            ends_in_v = False
                            if base_sfx:
                                ends_in_v = base_sfx[-1] in 'aeıioöuü'
                            else:
                                ends_in_v = current_vowel_end

                            # 1. Append copulas
                            cop_templates = COPULAS_VOWEL if ends_in_v else COPULAS_CONS
                            for cop_temp in cop_templates:
                                resolved_cop = append_suffix_harmonized(sim_stem + base_sfx, cop_temp)
                                rules.append(base_sfx + resolved_cop)

                            # 2. Append relative -ki suffixes
                            is_locative_or_genitive = case in ['DA', 'DAn', 'In', 'nIn', 'ndA', 'ndAn']
                            if is_locative_or_genitive and base_sfx:
                                loc_ki = base_sfx + 'ki'
                                rules.append(loc_ki)
                                
                                ki_suffixes = [
                                     'ler', 'lerin', 'lere', 'lerde', 'lerden', 'lerle', 'lerce',
                                     'leri', 'lerini', 'lerine', 'lerinde', 'lerinden', 'leriyle', 'lerinin',
                                     'leriyse', 'leridir', 'leriymiş', 'leriydi', 'leriyse',
                                     'ni', 'ne', 'nde', 'nden', 'nin', 'yle', 'yse', 'dir', 'ymiş', 'ydi', 'ydim', 'ydin'
                                ]
                                for ki_sfx in ki_suffixes:
                                    rules.append(loc_ki + ki_sfx)
                                    
                            # 3. Append adverbial -yken to locative cases
                            if case in ['DA', 'ndA'] and base_sfx:
                                rules.append(base_sfx + 'yken')

        # Formatting lines
        lines = ["HEADER_PLACEHOLDER"]

        if is_first_fold:
            # Deduplicate first-fold rules
            seen = set()
            unique_rules = []
            for base_sfx, cont_flag in rules:
                key = (base_sfx, cont_flag)
                if key not in seen:
                    seen.add(key)
                    unique_rules.append(key)
            
            for base_sfx, cont_flag in unique_rules:
                append_noun_rule(lines, flag, base_sfx, cont_flag)
                
            # Generate first-fold strip-add rules for voicing, vowel drop, or doubling
            if rounded:
                target_sfx_flag = "181" if back_vowel else "182"
            else:
                target_sfx_flag = "81" if back_vowel else "82"
                
            if voicing:
                voicing_pairs = [('p', 'b'), ('ç', 'c'), ('t', 'd'), ('k', 'ğ'), ('g', 'ğ')]
                for unv, vc in voicing_pairs:
                    lines.append(f"SFX {flag} {unv} {vc}/{target_sfx_flag} {unv}")
            elif vowel_drop:
                if back_vowel:
                    endings = ['ıl', 'ım', 'ın', 'ır', 'ıs', 'ız', 'ul', 'um', 'un', 'ur', 'us', 'uz', 'ıf', 'ıh', 'ık', 'ıp', 'ıt', 'uf', 'uh', 'uk', 'up', 'ut', 'uv']
                else:
                    endings = ['il', 'im', 'in', 'iş', 'ir', 'is', 'iz', 'ül', 'üm', 'ün', 'ür', 'üs', 'üz', 'if', 'ih', 'ik', 'ip', 'it', 'üf', 'üh', 'ük', 'üp', 'üt', 'üv']
                
                for end in endings:
                    strip_str = end
                    add_char = end[1]
                    lines.append(f"SFX {flag} {strip_str} {add_char}/{target_sfx_flag} {strip_str}")
            elif doubling:
                doubling_pairs = [
                    ('p', 'bb'), ('t', 'dd'), ('t', 'tt'), ('k', 'kk'), ('s', 'ss'),
                    ('r', 'rr'), ('m', 'mm'), ('n', 'nn'), ('l', 'll'), ('z', 'zz')
                ]
                for unv, db in doubling_pairs:
                    lines.append(f"SFX {flag} {unv} {db}/{target_sfx_flag} {unv}")
        else:
            # Deduplicate second-fold rules
            seen = set()
            unique_rules = []
            for r in rules:
                if r not in seen:
                    seen.add(r)
                    unique_rules.append(r)
            
            for suffix in unique_rules:
                if voicing:
                    # Voicing paradigm for all p, ç, t, k, g consonants
                    voicing_pairs = [('p', 'b'), ('ç', 'c'), ('t', 'd'), ('k', 'ğ'), ('g', 'ğ')]
                    starts_with_vowel = suffix[0] in 'aeıioöuü'
                    if starts_with_vowel:
                        # Non-voicing fallback
                        append_noun_rule(lines, flag, suffix)
                        # Voicing rules
                        for unv, vc in voicing_pairs:
                            lines.append(f"SFX {flag} {unv} {vc}{suffix} {unv}")
                    else:
                        append_noun_rule(lines, flag, suffix)
                elif vowel_drop:
                    # Vowel drop paradigm for all possible 2-letter back/front vowel-drop endings
                    starts_with_vowel = suffix[0] in 'aeıioöuü'
                    if starts_with_vowel:
                        if back_vowel:
                            endings = ['ıl', 'ım', 'ın', 'ır', 'ıs', 'ız', 'ul', 'um', 'un', 'ur', 'us', 'uz', 'ıf', 'ıh', 'ık', 'ıp', 'ıt', 'uf', 'uh', 'uk', 'up', 'ut', 'uv']
                        else:
                            endings = ['il', 'im', 'in', 'iş', 'ir', 'is', 'iz', 'ül', 'üm', 'ün', 'ür', 'üs', 'üz', 'if', 'ih', 'ik', 'ip', 'it', 'üf', 'üh', 'ük', 'üp', 'üt', 'üv']
                        
                        voicing_map = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'ğ'}
                        
                        for end in endings:
                            strip_suffix = end
                            add_char = end[1]
                            lines.append(f"SFX {flag} {strip_suffix} {add_char}{suffix} {strip_suffix}")
                            
                            if add_char in voicing_map:
                                voiced_char = voicing_map[add_char]
                                lines.append(f"SFX {flag} {strip_suffix} {voiced_char}{suffix} {strip_suffix}")
                    else:
                        append_noun_rule(lines, flag, suffix)
                elif doubling:
                    starts_with_vowel = suffix[0] in 'aeıioöuü'
                    if starts_with_vowel:
                        append_noun_rule(lines, flag, suffix)
                        doubling_pairs = [
                            ('p', 'bb'), ('t', 'dd'), ('t', 'tt'), ('k', 'kk'), ('s', 'ss'),
                            ('r', 'rr'), ('m', 'mm'), ('n', 'nn'), ('l', 'll'), ('z', 'zz')
                        ]
                        for unv, db in doubling_pairs:
                            lines.append(f"SFX {flag} {unv} {db}{suffix} {unv}")
                    else:
                        append_noun_rule(lines, flag, suffix)
                else:
                    append_noun_rule(lines, flag, suffix)

        # Clean duplicates in lines just in case voicing/vowel drop generated duplicates
        seen_lines = set()
        final_lines = []
        for l in lines:
            if l not in seen_lines:
                seen_lines.add(l)
                final_lines.append(l)
                
        # Update rule count in header line
        final_lines[0] = f"SFX {flag} Y {len(final_lines) - 1}"
        return '\n'.join(final_lines)

    # Generate all verb suffixes for a given paradigm
    def generate_verb_suffixes(back_vowel, vowel_stem, rounded):
        # We will simulate to cover all 4-way vowel harmony and voiced/unvoiced variants
        if vowel_stem:
            if rounded:
                stems = ["oku"] if back_vowel else ["söyl"]
            else:
                stems = ["ar"] if back_vowel else ["bekl"]
        else:
            if rounded:
                stems = ["uç", "bul"] if back_vowel else ["düş", "gör"]
            else:
                stems = ["yap", "kal"] if back_vowel else ["git", "gel"]
        
        # We now strip mak/mek for vowel stems too,
        TAM = [
            # Bare verb stem (imperative 2nd sg)
            "",
            # Past
            "DI", "DIm", "DIn", "DIk", "DInIz", "DIlAr",
            # Narrative
            "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr", "mIştIr", "mIşlArdIr",
            "mIşImdIr", "mIşsIndIr", "mIşIzdIr", "mIşsInIzdIr",
            "mIşlArdI", "mIşlArdIm", "mIşlArdIn", "mIşlArdIk", "mIşlArdInIz", "mIşlArdIlAr", # Narrative past plural copulas
            # Present Continuous
            "Iyor", "Iyorum", "Iyorsun", "Iyoruz", "Iyorsunuz", "IyorlAr", "Iyordur", "IyorlArmIş",
            "IyorumdIr", "IyorsundIr", "IyoruzdIr", "IyorsunuzdIr", "IyorlArdIr", # Assertive copulas
            "Iyorken", # Adverbial -yken
            # Present Continuous Past (Hikaye)
            "Iyordu", "Iyordum", "Iyordun", "Iyorduk", "Iyordunuz", "IyordulAr", "IyorlArdI",
            # Present Continuous Narrative (Rivayet)
            "Iyormuş", "Iyormuşum", "Iyormuşsun", "Iyormuşuz", "Iyormuşsunuz", "IyormuşlAr",
            # Present Continuous Conditional (Şart)
            "IyorsA", "IyorsAm", "IyorsAn", "IyorsAk", "IyorsAnIz", "IyorsAlAr", "IyorlArsA",
            # Future
            "AcAk", "AcAksIn", "AcAksInIz", "AcAklAr", "AcAktIr", "AcAklArmIş", "AcAğIm", "AcAğIz",
            "AcAğImdIr", "AcAksIndIr", "AcAğIzdIr", "AcAksInIzdIr", "AcAklArdIr", # Assertive copulas
            "AcAkken", # Adverbial -yken
            # Future Past
            "AcAktI", "AcAktIm", "AcAktIn", "AcAktIk", "AcAktInIz", "AcAktIlAr", "AcAklArdI",
            # Future Narrative
            "AcAkmIş", "AcAkmIşIm", "AcAkmIşsIn", "AcAkmIşUz", "AcAkmIşsInIz", "AcAkmIşlAr",
            # Future Conditional
            "AcAksA", "AcAksAm", "AcAksAn", "AcAksAk", "AcAksAnIz", "AcAksAlAr", "AcAklArsA",
            # Aorist
            "Ar", "ArIm", "ArsIn", "ArIz", "ArsInIz", "ArlAr", "ArlArmIş",
            "Ir", "IrIm", "IrsIn", "IrIz", "IrsInIz", "IrlAr", "IrlArmIş",
            "ArImdIr", "ArsIndIr", "ArIzdIr", "ArsInIzdIr", "ArlArdIr", # Assertive copulas
            "IrImdIr", "IrsIndIr", "IrIzdIr", "IrsInIzdIr", "IrlArdIr",
            # Aorist Past
            "ArdI", "ArdIm", "ArdIn", "ArdIk", "ArdInIz", "ArdIlAr",
            "IrdI", "IrdIm", "IrdIn", "IrdIk", "IrdInIz", "IrdIlAr",
            "ArlArdI", "IrlArdI", "yAbilIrlArdI", "AbilIrlArdI", # Aorist past plural copulas
            # Aorist Narrative
            "ArmIş", "ArmIşIm", "ArmIşsIn", "ArmIşIz", "ArmIşsInIz", "ArmIşlAr",
            "IrmIş", "IrmIşIm", "IrmIşsIn", "IrmIşIz", "IrmIşsInIz", "IrmIşlAr",
            # Aorist Conditional
            "ArsA", "ArsAm", "ArsAn", "ArsAk", "ArsAnIz", "ArsAlAr", "ArlArsA",
            "IrsA", "IrsAm", "IrsAn", "IrsAk", "IrsAnIz", "IrsAlAr", "IrlArsA",
            # Past Conditional (olduysa)
            "DIysA", "DIysAm", "DIysAn", "DIysAk", "DIysAnIz", "DIysAlAr", "DIlArsA",
            # Narrative Past (Pluperfect)
            "mIştI", "mIştIm", "mIştIn", "mIştIk", "mIştInIz", "mIştIlAr",
            # Narrative Conditional
            "mIşsA", "mIşsAm", "mIşsAn", "mIşsAk", "mIşsAnIz", "mIşsAlAr", "mIşlArsA",
            # Necessity
            "mAlI", "mAlIyIm", "mAlIsIn", "mAlIyIz", "mAlIsInIz", "mAlIlAr", "mAlIdIr", "mAlIlArdIr", "mAlIdIrlAr",
            "mAlIyImdIr", "mAlIsIndIr", "mAlIyIzdIr", "mAlIsInIzdIr", "mAlIlArdIr", # Assertive copulas
            "mAlIyken", "ArlArken", "IrlArken", # Adverbial -yken
            # Necessity Past
            "mAlIydI", "mAlIydIm", "mAlIydIn", "mAlIydIk", "mAlIydInIz", "mAlIydIlAr",
            # Necessity Conditional
            "mAlIysA", "mAlIysAm", "mAlIysAn", "mAlIysAk", "mAlIysAnIz", "mAlIyslAr", "mAlIlArsA",
            # Necessity Narrative / Plural Copulas
            "mAlIymIş", "mAlIymIşIm", "mAlIymIşsIn", "mAlIymIşIz", "mAlIymIşsInIz", "mAlIymIşlAr", "mAlIlArmIş", "mAlIlArdI",
            # Conditional
            "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
            # Conditional Past (Hikaye)
            "sAydI", "sAydIm", "sAydIn", "sAydIk", "sAydInIz", "sAydIlAr", "sAnA", "sAnIzA", "sAlArdI", "ysAlArdI",
            # Adverbial -casına
            "cAsInA", "ArCAsInA", "IrCAsInA", "yArAkCAsInA", "mIşCAsInA",
            # Capability Aorist (y-buffered and y-less)
            "yAbilIr", "yAbilIrIm", "yAbilIrsIn", "yAbilIrIz", "yAbilIrsInIz", "yAbilIrlAr",
            "AbilIr", "AbilIrIm", "AbilIrsIn", "AbilIrIz", "AbilIrsInIz", "AbilIrlAr",
            "yAbilIrImdIr", "yAbilIrsIndIr", "yAbilIrIzdIr", "yAbilIrsInIzdIr", "yAbilIrlArdIr", # Assertive copulas
            "AbilIrImdIr", "AbilIrsIndIr", "AbilIrIzdIr", "AbilIrsInIzdIr", "AbilIrlArdIr",
            "yAbilIrken", "AbilIrken", # Adverbial -yken
            # Capability Aorist Conditional
            "yAbilIrsA", "yAbilIrsAm", "yAbilIrsAn", "yAbilIrsAk", "yAbilIrsAnIz", "yAbilIrsAlAr", "yAbilIrlArsA",
            "AbilIrsA", "AbilIrsAm", "AbilIrsAn", "AbilIrsAk", "AbilIrsAnIz", "AbilIrsAlAr", "AbilIrlArsA",
            # Conditional Narrative
            "sAymIş", "sAymIşIm", "sAymIşsIn", "sAymIşIz", "sAymIşsInIz", "sAymIşlAr",
            # Capability Past
            "yAbildI", "yAbildIm", "yAbildIn", "yAbildIk", "yAbildInIz", "yAbildIlAr",
            "AbildI", "AbildIm", "AbildIn", "AbildIk", "AbildInIz", "AbildIlAr",
            # Capability Future
            "yAbilAcAk", "yAbilAcAklAr", "yAbilAcAğImdIr", "yAbilAcAksIndIr", "yAbilAcAğIzdIr", "yAbilAcAksInIzdIr", "yAbilAcAklArdIr",
            "AbilAcAk", "AbilAcAklAr", "AbilAcAğImdIr", "AbilAcAksIndIr", "AbilAcAğIzdIr", "AbilAcAksInIzdIr", "AbilAcAklArdIr",
            "yAbilAcAkken", "AbilAcAkken", # Adverbial -yken
            # Capability Present Continuous
            "yAbiliyor", "yAbiliyorum", "yAbiliyorsun", "yAbiliyoruz", "yAbiliyorsunuz", "yAbiliyorlAr", "yAbiliyorlArdIr", "yAbiliyorlArsA", "yAbilirlAr",
            "yAbiliyorumdIr", "yAbiliyorsundIr", "yAbiliyoruzdIr", "yAbiliyorsunuzdIr", "yAbiliyorlArdIr",
            "Abiliyor", "Abiliyorum", "Abiliyorsun", "Abiliyoruz", "Abiliyorsunuz", "AbiliyorlAr", "AbiliyorlArdIr", "AbiliyorlArsA", "AbilirlAr",
            "AbiliyorumdIr", "AbiliyorsundIr", "AbiliyoruzdIr", "AbiliyorsunuzdIr", "AbiliyorlArdIr",
            "yAbiliyorken", "Abiliyorken", # Adverbial -yken
            # Capability Conditional
            "yAbilsA", "yAbilsAm", "yAbilsAn", "yAbilsAk", "yAbilsAnIz", "yAbilsAlAr",
            "AbilsA", "AbilsAm", "AbilsAn", "AbilsAk", "AbilsAnIz", "AbilsAlAr",
            # Capability Conditional Past
            "AbilsAydI", "AbilsAydIm", "AbilsAydIn", "AbilsAydIk", "AbilsAydInIz", "AbilsAlArdI",
            "yAbilsAydI", "yAbilsAydIm", "yAbilsAydIn", "yAbilsAydIk", "yAbilsAydInIz", "yAbilsAlArdI",
            # Capability Optative
            "AbilsIn", "yAbilsIn", "AbilAlIm", "yAbilAlIm", "AbilAyIm", "yAbilAyIm", "AbilsInlAr", "yAbilsInlAr", "AbilIn", "yAbilIn", "AbilInIz", "yAbilInIz",
            # Capability Past Aorist
            "yAbilIrdI", "yAbilIrdIm", "yAbilIrdIn", "yAbilIrdIk", "yAbilIrdInIz", "yAbilIrdIlAr",
            "AbilIrdI", "AbilIrdIm", "AbilIrdIn", "AbilIrdIk", "AbilIrdInIz", "AbilIrdIlAr",
            # Capability Present Continuous Past
            "yAbiliyordu", "yAbiliyordum", "yAbiliyordun", "yAbiliyorduk", "yAbiliyordunuz", "yAbiliyorlArdI",
            "Abiliyordu", "Abiliyordum", "Abiliyordun", "Abiliyorduk", "Abiliyordunuz", "AbiliyorlArdI",
            # Optative/Imperative
            "yAyIm", "yAlIm", "AyIm", "AlIm", "sIn", "sInlAr", "In", "InIz",
            "A", "yA", "AsIn", "yAsIn", "AsInIz", "yAsInIz", "AlAr", "yAlAr",
            # Positive Progressive Tense (-maktA)
            "mAktA", "mAktAyIm", "mAktAsIn", "mAktAyIz", "mAktAsInIz", "mAktAlAr", "mAktAdIr", "mAktAdIrlAr", "mAktAlArdIr",
            "mAktAydI", "mAktAydIm", "mAktAydIn", "mAktAydIk", "mAktAydInIz", "mAktAydIlAr",
            "mAktAymIş", "mAktAymIşIm", "mAktAymIşsIn", "mAktAymIşIz", "mAktAymIşsInIz", "mAktAymIşlAr",
            "mAktAysA", "mAktAysAm", "mAktAysAn", "mAktAysAk", "mAktAysAnIz", "mAktAyslAr", "mAktAlArsA",
            "mAktAyken", "mAktAnsA"
        ]
        
        # Add aorist for vowel stems if vowel_stem is True
        if vowel_stem:
            aorist_vowel = [
                "r", "rIm", "rsIn", "rIz", "rsInIz", "rlAr",
                "rdI", "rdIm", "rdIn", "rdIk", "rdInIz", "rdIlAr",
                "rmIş", "rmIşIm", "rmIşsIn", "rmIşIz", "rmIşsInIz", "rmIşlAr",
                "rsA", "rsAm", "rsAn", "rsAk", "rsAnIz", "rsAlAr", "rlArsA", "rsAlAr", "rlArmIş", "rlArdI",
                "rken", "rcAsInA", "rCAsInA", "rlArken"
            ]
            TAM = TAM + aorist_vowel
        
        # Negatives
        NEG_TAM = [
            "mADI", "mADIm", "mADIn", "mADIk", "mADInIz", "mADIlAr",
            "mADIysA", "mADIysAm", "mADIysAn", "mADIysAk", "mADIysAnIz", "mADIysAlAr", "mADIlArsA",
            "mAmIş", "mAmIşIm", "mAmIşsIn", "mAmIşIz", "mAmIşsInIz", "mAmIşlAr", "mAmIştIr",
            "mAmIşImdIr", "mAmIşsIndIr", "mAmIşIzdIr", "mAmIşsInIzdIr",
            "mAmIşlArdI", "mAmIşlArdIm", "mAmIşlArdIn", "mAmIşlArdIk", "mAmIşlArdInIz", "mAmIşlArdIlAr", # Negative narrative past plurals
            "mIyor", "mIyorum", "mIyorsun", "mIyoruz", "mIyorsunuz", "mIyorlAr", "mIyordur", "mIyorlArmIş",
            "mIyorumdIr", "mIyorsundIr", "mIyoruzdIr", "mIyorsunuzdIr", "mIyorlArdIr", # Assertive copula
            "mIyorken", # Adverbial
            # Present Continuous Past
            "mIyordu", "mIyordum", "mIyordun", "mIyorduk", "mIyordunuz", "mIyorlArdI",
            # Present Continuous Narrative
            "mIyormuş", "mIyormuşum", "mIyormuşsun", "mIyormuşuz", "mIyormuşsunuz", "mIyormuşlAr",
            # Present Continuous Conditional
            "mIyorsA", "mIyorsAm", "mIyorsAn", "mIyorsAk", "mIyorsAnIz", "mIyorsAlAr", "mIyorlArsA",
            "mAyAcAk", "mAyAcAksIn", "mAyAcAksInIz", "mAyAcAklAr", "mAyAcAktIr",
            "mAyAcAğImdIr", "mAyAcAksIndIr", "mAyAcAğIzdIr", "mAyAcAksInIzdIr", "mAyAcAklArdIr", # Assertive copulas
            "mAyAcAkken", # Adverbial
            "mAyAcAğIm", "mAyAcAğIz",
            # Future Past
            "mAyAcAktI", "mAyAcAktIm", "mAyAcAktIn", "mAyAcAktIk", "mAyAcAktInIz", "mAyAcAktIlAr",
            # Future Narrative
            "mAyAcAkmIş", "mAyAcAkmIşIm", "mAyAcAkmIşsIn", "mAyAcAkmIşIz", "mAyAcAkmIşsInIz", "mAyAcAkmIşlAr",
            # Future Conditional
            "mAyAcAksA", "mAyAcAksAm", "mAyAcAksAn", "mAyAcAksAk", "mAyAcAksAnIz", "mAyAcAksAlAr", "mAyAcAklArsA",
            "mAm", "mAzsIn", "mAz", "mAyIz", "mAzsInIz", "mAzlAr", "mAztIr",
            "mAmdIr", "mAzsIndIr", "mAzdIr", "mAyIzdIr", "mAzsInIzdIr", "mAzlArdIr", # Assertive copulas
            # Aorist Past
            "mAzdI", "mAzdIm", "mAzdIn", "mAzdIk", "mAzdInIz", "mAzdIlAr",
            "mAzlArdI", "mAyAbilIrlArdI", "AmAzlArdI", # Negative aorist past plurals
            # Aorist Narrative
            "mAzmIş", "mAzmIşIm", "mAzmIşsIn", "mAzmIşIz", "mAzmIşsInIz", "mAzmIşlAr",
            # Aorist Conditional
            "mAzsA", "mAzsAm", "mAzsAn", "mAzsAk", "mAzsAnIz", "mAzsAlAr", "mAzlArsA",
            # Narrative Past
            "mAmIştI", "mAmIştIm", "mAmIştIn", "mAmIştIk", "mAmIştInIz", "mAmIştIlAr",
            # Narrative Conditional
            "mAmIşsA", "mAmIşsAm", "mAmIşsAn", "mAmIşsAk", "mAmIşsAnIz", "mAmIşsAlAr", "mAmIşlArsA",
            # Necessity
            "mAmAlI", "mAmAlIyIm", "mAmAlIsIn", "mAmAlIyIz", "mAmAlIsInIz", "mAmAlIlAr", "mAmAlIdIr", "mAmAlIlArdIr",
            "mAmAlIyImdIr", "mAmAlIsIndIr", "mAmAlIyIzdIr", "mAmAlIsInIzdIr", "mAmAlIlArdIr", # Assertive copulas
            "mAmAlIyken", "mAzlArken", # Adverbial
            # Necessity Past
            "mAmAlIydI", "mAmAlIydIm", "mAmAlIydIn", "mAmAlIydIk", "mAmAlIydInIz", "mAmAlIydIlAr",
            # Necessity Conditional
            "mAmAlIysA", "mAmAlIysAm", "mAmAlIysAn", "mAmAlIysAk", "mAmAlIysAnIz", "mAmAlIyslAr", "mAmAlIlArsA",
            # Conditional
            "mAsA", "mAsAm", "mAsAn", "mAsAk", "mAsAnIz", "mAsAlAr",
            "AmAsA", "AmAsAm", "AmAsAn", "AmAsAk", "AmAsAnIz", "AmAsAlAr", "AmAsAlArdI",
            "yAmAsA", "yAmAsAm", "yAmAsAn", "yAmAsAk", "yAmAsAnIz", "yAmAsAlAr", "yAmAsAlArdI",
            "AmAsAydI", "AmAsAydIm", "AmAsAydIn", "AmAsAydIk", "AmAsAydInIz", "AmAsAydIlAr",
            "yAmAsAydI", "yAmAsAydIm", "yAmAsAydIn", "yAmAsAydIk", "yAmAsAydInIz", "yAmAsAydIlAr",
            # Conditional Past Neg
            "mAsAydI", "mAsAydIm", "mAsAydIn", "mAsAydIk", "mAsAydInIz", "mAsAydIlAr", "mAsAnA", "mAsAnIzA", "mAsAlArdI",
            # Negative Progressive Tense (-memekte)
            "mAmAktA", "mAmAktAyIm", "mAmAktAsIn", "mAmAktAyIz", "mAmAktAsInIz", "mAmAktAlAr", "mAmAktAdIr", "mAmAktAdIrlAr", "mAmAktAlArdIr",
            "mAmAktAydI", "mAmAktAydIm", "mAmAktAydIn", "mAmAktAydIk", "mAmAktAydInIz", "mAmAktAydIlAr",
            "mAmAktAymIş", "mAmAktAymIşIm", "mAmAktAymIşsIn", "mAmAktAymIşIz", "mAmAktAymIşsInIz", "mAmAktAymIşlAr",
            "mAmAktAysA", "mAmAktAysAm", "mAmAktAysAn", "mAmAktAysAk", "mAmAktAysAnIz", "mAmAktAyslAr", "mAmAktAlArsA",
            "mAmAktAyken", "mAmAktAnsA",
            # Capability Negatives (Present Continuous)
            "yAmIyor", "yAmIyorum", "yAmIyorsun", "yAmIyoruz", "yAmIyorsunuz", "yAmIyorlAr", "yAmIyorlArdI", "yAmIyordur", "yAmIyordu",
            "yAmIyorumdIr", "yAmIyorsundIr", "yAmIyoruzdIr", "yAmIyorsunuzdIr", "yAmIyorlArdIr", # Assertive copulas
            "yAmIyorken", # Adverbial
            "AmIyor", "AmIyorum", "AmIyorsun", "AmIyoruz", "AmIyorsunuz", "AmIyorlAr", "AmIyorlArdI", "AmIyordur", "AmIyordu",
            "AmIyorumdIr", "AmIyorsundIr", "AmIyoruzdIr", "AmIyorsunuzdIr", "AmIyorlArdIr", # Assertive copulas
            "AmIyorken", # Adverbial
            # Capability Negatives (Continuous Past)
            "AmIyordum", "AmIyordun", "AmIyorduk", "AmIyordunuz",
            "yAmIyordum", "yAmIyordun", "yAmIyorduk", "yAmIyordunuz",
            # Capability Negatives (Continuous Conditional)
            "AmIyorsAm", "AmIyorsAn", "AmIyorsA", "AmIyorsAk", "AmIyorsAnIz", "AmIyorsAlAr", "AmIyorlArsA",
            "yAmIyorsAm", "yAmIyorsAn", "yAmIyorsA", "yAmIyorsAk", "yAmIyorsAnIz", "yAmIyorsAlAr", "yAmIyorlArsA",
            # Capability Negatives (Continuous Narrative)
            "AmIyormuşum", "AmIyormuşsun", "AmIyormuş", "AmIyormuşuz", "AmIyormuşsunuz", "AmIyormuşlAr", "AmIyorlArmIş",
            "yAmIyormuşum", "yAmIyormuşsun", "yAmIyormuş", "yAmIyormuşuz", "yAmIyormuşsunuz", "yAmIyormuşlAr", "yAmIyorlArmIş",
            # Capability Negatives (Aorist etc.)
            "yAmAz", "yAmAzsIn", "yAmAzsInIz", "yAmAzlAr", "yAmAm", "yAmAyIz", "yAmAzlArdI", "yAmAzlArmIş",
            "yAmAmdIr", "yAmAzsIndIr", "yAmAzdIr", "yAmAyIzdIr", "yAmAzsInIzdIr", "yAmAzlArdIr", # Assertive copulas
            "yAmAzdI", "yAmAzdIm", "yAmAzdIn", "yAmAzdIk", "yAmAzdInIz", "yAmAzdIlAr",
            "yAmAzmIş", "yAmAzmIşIm", "yAmAzmIşsIn", "yAmAzmIşIz", "yAmAzmIşsInIz", "yAmAzmIşlAr",
            "yAmAzsA", "yAmAzsAm", "yAmAzsAn", "yAmAzsAk", "yAmAzsAnIz", "yAmAzsAlAr",
            "yAmAdI", "yAmADIm", "yAmADIn", "yAmADIk", "yAmADIlAr", "yAmADIlArsA", "yAmADIysA", "yAmADInIz",
            "yAmAyAcAk", "yAmAyAcAklAr", "yAmAyAcAğImdIr", "yAmAyAcAksIndIr", "yAmAyAcAğIzdIr", "yAmAyAcAksInIzdIr", "yAmAyAcAklArdIr", # Assertive copulas
            "yAmAyAcAkken", # Adverbial
            "yAmAyAcAktI", "yAmAyAcAğIm", "yAmAyAcAğIz",
            "AmAz", "AmAzsIn", "AmAzsInIz", "AmAzlAr", "AmAm", "AmAyIz", "AmAzlArdI", "AmAzlArmIş",
            "AmAmdIr", "AmAzsIndIr", "AmAzdIr", "AmAyIzdIr", "AmAzsInIzdIr", "AmAzlArdIr", # Assertive copulas
            "AmAzdI", "AmAzdIm", "AmAzdIn", "AmAzdIk", "AmAzdInIz", "AmAzdIlAr",
            "AmAzmIş", "AmAzmIşIm", "AmAzmIşsIn", "AmAzmIşIz", "AmAzmIşsInIz", "AmAzmIşlAr",
            "AmAzsA", "AmAzsAm", "AmAzsAn", "AmAzsAk", "AmAzsAnIz", "AmAzsAlAr",
            "AmAdI", "AmADIm", "AmADIn", "AmADIk", "AmADIlAr", "AmADIlArsA", "AmADIysA", "AmADInIz",
            "AmAyAcAk", "AmAyAcAklAr", "AmAyAcAğImdIr", "AmAyAcAksIndIr", "AmAyAcAğIzdIr", "AmAyAcAksInIzdIr", "AmAyAcAklArdIr", # Assertive copulas
            "AmAyAcAkken", # Adverbial
            "AmAyAcAktI", "AmAyAcAğIm", "AmAyAcAğIz",
            # Capability Negatives (Narrative past mIş)
            "AmAmIş", "AmAmIşIm", "AmAmIşsIn", "AmAmIşIz", "AmAmIşsInIz", "AmAmIşlAr", "AmAmIştIr",
            "AmAmIşImdIr", "AmAmIşsIndIr", "AmAmIşIzdIr", "AmAmIşsInIzdIr",
            "AmAmIşlArdI", "AmAmIşsA", "AmAmIşsAm", "AmAmIşsAn", "AmAmIşsAk", "AmAmIşsAnIz", "AmAmIşsAlAr", "AmAmIşlArsA",
            "yAmAmIş", "yAmAmIşIm", "yAmAmIşsIn", "yAmAmIşIz", "yAmAmIşsInIz", "yAmAmIşlAr", "yAmAmIştIr",
            "yAmAmIşImdIr", "yAmAmIşsIndIr", "yAmAmIşIzdIr", "yAmAmIşsInIzdIr",
            "yAmAmIşlArdI", "yAmAmIşsA", "yAmAmIşsAm", "yAmAmIşsAn", "yAmAmIşsAk", "yAmAmIşsAnIz", "yAmAmIşsAlAr", "yAmAmIşlArsA",
            # Conditional Narrative Negatives
            "mAsAymIş", "mAsAymIşIm", "mAsAymIşsIn", "mAsAymIşIz", "mAsAymIşsInIz", "mAsAymIşlAr",
            # Capability Negatives (Probability/Possibility)
            "AmAyAbilIr", "yAmAyAbilIr", "AmAyAbilIrlAr", "yAmAyAbilIrlAr",
            "AmAyAbilIrIm", "AmAyAbilIrsIn", "AmAyAbilIrIz", "AmAyAbilIrsInIz",
            "yAmAyAbilIrIm", "yAmAyAbilIrsIn", "yAmAyAbilIrIz", "yAmAyAbilIrsInIz",
            "AmAyAbilIrImdIr", "AmAyAbilIrsIndIr", "AmAyAbilIrIzdIr", "AmAyAbilIrsInIzdIr",
            "yAmAyAbilIrImdIr", "yAmAyAbilIrsIndIr", "yAmAyAbilIrIzdIr", "yAmAyAbilIrsInIzdIr",
            # Capability Negatives (Probability Past/Narrative/Conditional)
            "AmAyAbilIrdI", "AmAyAbilIrdIm", "AmAyAbilIrdIn", "AmAyAbilIrdIk", "AmAyAbilIrdInIz", "AmAyAbilIrlArdI",
            "yAmAyAbilIrdI", "yAmAyAbilIrdIm", "yAmAyAbilIrdIn", "yAmAyAbilIrdIk", "yAmAyAbilIrdInIz", "yAmAyAbilIrlArdI",
            "AmAyAbilIrmIş", "yAmAyAbilIrmIş", "AmAyAbilIrsA", "yAmAyAbilIrsA",
            "AmAyAbildI", "yAmAyAbildI", "AmAyAbilsA", "yAmAyAbilsA",
            "AmAyAbiliyor", "yAmAyAbiliyor", "AmAyAbiliyorum", "yAmAyAbiliyorum", "AmAyAbiliyorsun", "yAmAyAbiliyorsun", "AmAyAbiliyoruz", "yAmAyAbiliyoruz", "AmAyAbiliyorsunuz", "yAmAyAbiliyorsunuz", "AmAyAbiliyorlAr", "yAmAyAbiliyorlAr", "AmAyAbiliyordu", "yAmAyAbiliyordu", "AmAyAbiliyormuş", "yAmAyAbiliyormuş", "AmAyAbiliyorsa", "yAmAyAbiliyorsa",
            "mAyAbilIr", "mAyAbilIrlAr",
            "mAyAbilIrIm", "mAyAbilIrsIn", "mAyAbilIrIz", "mAyAbilIrsInIz",
            "mAyAbildI", "mAyAbilsA",
            "mAyAbiliyor", "mAyAbiliyorum", "mAyAbiliyorsun", "mAyAbiliyoruz", "mAyAbiliyorsunuz", "mAyAbiliyorlAr", "mAyAbiliyordu", "mAyAbiliyormuş", "mAyAbiliyorsa",
            "mAyAbilIrdI", "mAyAbilIrdIm", "mAyAbilIrdIn", "mAyAbilIrdIk", "mAyAbilIrdInIz", "mAyAbilIrlArdI",
            "mAyAbilIrmIş", "mAyAbilIrsA",
            # Capability Negatives Optative/Imperative
            "AmA", "yAmA", "AmAyAyIm", "yAmAyAyIm", "AmAyAlIm", "yAmAyAlIm", "AmAsIn", "yAmAsIn", "AmAsInlAr", "yAmAsInlAr", "AmAyIn", "yAmAyIn", "AmAyInIz", "yAmAyInIz",
            # Adverbial -ken on Capability Negatives
            "AmAzken", "yAmAzken",
            # Negative Optative/Imperative
            "mAyAyIm", "mAyAlIm", "mAsIn", "mAsInlAr", "mAyIn", "mAyInIz"
        ]
        
        def get_continuation_flag(resolved_sfx):
            vowels = 'aeıioöuüâîû'
            last_v = None
            for ch in reversed(resolved_sfx):
                if ch in vowels:
                    last_v = ch.lower()
                    break
            if not last_v:
                return ""
                
            is_back = last_v in 'aıouâû'
            is_rounded = last_v in 'oöuüû'
            last_char = resolved_sfx[-1]
            
            if resolved_sfx.endswith(('mak', 'mek')):
                # 'mak' / 'mek' are non-voicing, so they point to 81/82
                return "81" if is_back else "82"
                
            if last_char in 'aeıioöuü':
                if is_back:
                    return "183" if is_rounded else "83"
                else:
                    return "184" if is_rounded else "84"
            elif last_char == 'k':
                if is_back:
                    return "185" if is_rounded else "85"
                else:
                    return "186" if is_rounded else "86"
            else:
                if is_back:
                    return "181" if is_rounded else "81"
                else:
                    return "182" if is_rounded else "82"

        def generate_base_nominal_suffixes(back_vowel, rounded):
            verb_prefixes = [
                "", "Il", "n", "In",
                "DIr", "t", "tDIr", "Ir", "tIr",
                "tIl", "DIrIl", "IrIl"
            ]
            tam_prefixes = [
                "", "mA", "Abil", "yAbil", "AmA", "yAmA", "mAyAbil", "AmAyAbil", "yAmAyAbil"
            ]
            nominal_templates = [
                "mAk", "mA", "IcI", "Iş", "DIk", "AcAk", "An", "mIş", "mIşlIk", "mAz", "AbilIrlIk", "AsI"
            ]
            gerund_templates = [
                "ArAk", "Ip", "IncA", "mAdAn", "DIkçA", "mAksIzIn", "AmAdAn",
                "IncAyA", "mAyIncAyA",
                "Arken", "Irken", "Acakken", "mAzken", "AlI"
            ]
            
            sim_stem = "bul" if back_vowel else "gör"
            if not rounded:
                sim_stem = "kal" if back_vowel else "gel"
                
            resolved_rules = []
            
            for vp in verb_prefixes:
                for tp in tam_prefixes:
                    if vp and (tp in ["mAyAbil", "yAbil", "AmAyAbil", "yAmAyAbil"]):
                        if vp not in ["Il", "n", "DIr", "t"]:
                            continue
                    prefix_temp = vp + tp
                    for nt in nominal_templates:
                        # Singular version
                        template = prefix_temp + nt
                        resolved = append_suffix_harmonized(sim_stem, template)
                        if resolved:
                            flag = get_continuation_flag(resolved)
                            if flag:
                                resolved_rules.append(f"{template}/{flag}")
                                resolved_rules.append(template)
                            else:
                                resolved_rules.append(template)
                                
                        # Plural version
                        template_pl = prefix_temp + nt + "lAr"
                        resolved_pl = append_suffix_harmonized(sim_stem, template_pl)
                        if resolved_pl:
                            flag_pl = get_continuation_flag(resolved_pl)
                            if flag_pl:
                                resolved_rules.append(f"{template_pl}/{flag_pl}")
                                resolved_rules.append(template_pl)
                            else:
                                resolved_rules.append(template_pl)
                                
                    for gt in gerund_templates:
                        template = prefix_temp + gt
                        resolved = append_suffix_harmonized(sim_stem, template)
                        if resolved:
                            resolved_rules.append(template)
                            
            return sorted(list(set(resolved_rules)))

        # Get base nominal suffixes using twofold stripping continuation flags
        nominal_suffixes = generate_base_nominal_suffixes(back_vowel, rounded)
        
        # Prepend passive/causative prefixes to TAM and NEG_TAM for prefixed tenses
        verb_prefixes = [
            "Il", "n", "In",
            "dIr", "t", "tDIr", "Ir", "tIr",
            "tIl", "dIrIl", "IrIl"
        ]
        prefixed_tam = []
        for pref in verb_prefixes:
            for temp in TAM + NEG_TAM:
                prefixed_tam.append(pref + temp)
                
        # Combine everything
        all_templates = TAM + NEG_TAM + prefixed_tam + nominal_suffixes
        
        # Resolve all templates using harmony simulator
        resolved_suffixes = []
        for sim_stem in stems:
            for template in all_templates:
                if "/" in template:
                    base_temp, flag_part = template.split("/")
                    resolved = append_suffix_harmonized(sim_stem, base_temp)
                    resolved_suffixes.append(f"{resolved}/{flag_part}")
                else:
                    resolved = append_suffix_harmonized(sim_stem, template)
                    resolved_suffixes.append(resolved)
        # Unique and sorted
        return sorted(list(set(resolved_suffixes)))

    # Format verb rules for output
    def format_verb_rules(flag, strip_ending, suffixes, is_voicing=False, is_narrowing=False, is_vowel_stem=False):
        unvoiced_chars = 'çfhkpsşt'
        voiced_chars = 'abcdeğgıijklmnoöprtuüvyzâîû'
        
        # Count number of rules
        num_rules = 0
        rule_lines = []
        
        for suffix in suffixes:
            if not suffix:
                if is_vowel_stem:
                    if flag in [11, 111]:
                        rule_lines.append(f"SFX {flag} mak 0 .")
                        num_rules += 1
                    else:
                        rule_lines.append(f"SFX {flag} mek 0 .")
                        num_rules += 1
                else:
                    rule_lines.append(f"SFX {flag} {strip_ending} 0 .")
                    num_rules += 1
                continue
                
            # If the suffix starts with 'd', generate both 'd' and 't' variants with matches
            if not is_narrowing and not is_voicing and not is_vowel_stem and (suffix[0] in 'tçdc'):
                starts_unvoiced = suffix[0] in 'tç'
                starts_voiced = suffix[0] in 'dc'
                if starts_unvoiced:
                    rule_lines.append(f"SFX {flag} {strip_ending} {suffix} [çfhkpsşt]{strip_ending}")
                    num_rules += 1
                elif starts_voiced:
                    rule_lines.append(f"SFX {flag} {strip_ending} {suffix} [^çfhkpsşt]{strip_ending}")
                    num_rules += 1
            elif is_vowel_stem:
                # Vowel stems: aramak, beklemek, okumak, büyümek, erimek etc.
                # Positive present continuous starts with ı/i/u/ü + yor (e.g., ıyor, iyor, uyor, üyor).
                # These trigger vowel narrowing of the stem.
                is_pres_cont = suffix[0] in 'ıiuü' and len(suffix) > 2 and suffix[1:3] == 'yo'
                if is_pres_cont:
                    if flag in [11, 111]:
                        # Back: aramak -> arıyor, taşımak -> taşıyor, okumak -> okuyor
                        # We narrow ıyor/uyor depending on the stem vowel
                        first_char = suffix[0]
                        # For amak -> ıyor
                        rule_lines.append(f"SFX {flag} amak {suffix} amak")
                        # For ımak -> ıyor
                        rule_lines.append(f"SFX {flag} ımak {suffix} ımak")
                        # For umak -> uyor
                        u_suffix = 'u' + suffix[1:]
                        rule_lines.append(f"SFX {flag} umak {u_suffix} umak")
                        num_rules += 3
                    else:
                        # Front: beklemek -> bekliyor, erimek -> eriyor, büyümek -> büyüyor
                        # For emek -> iyor
                        rule_lines.append(f"SFX {flag} emek {suffix} emek")
                        # For imek -> iyor
                        rule_lines.append(f"SFX {flag} imek {suffix} imek")
                        # For ümek -> üyor
                        ü_suffix = 'ü' + suffix[1:]
                        rule_lines.append(f"SFX {flag} ümek {ü_suffix} ümek")
                        num_rules += 3
                else:
                    # All other suffixes
                    starts_with_v = suffix[0].lower() in 'aeıioöuü'
                    resolved_suffix = 'y' + suffix if starts_with_v else suffix
                    
                    def harmonize_suffix(sfx, back, initial_rounded):
                        res = []
                        current_rounded = initial_rounded
                        for c in sfx:
                            if c in 'ıi':
                                if current_rounded:
                                    res.append('u' if back else 'ü')
                                else:
                                    res.append(c)
                            elif c in 'uü':
                                if current_rounded:
                                    res.append(c)
                                else:
                                    res.append('ı' if back else 'i')
                            elif c in 'aeoö':
                                res.append(c)
                                current_rounded = c in 'oö'
                            else:
                                res.append(c)
                        return ''.join(res)
                        
                    def is_suffix_rounded(sfx_str):
                        for ch in reversed(sfx_str):
                            if ch in 'aeıioöuüâîû':
                                return ch.lower() in 'oöuüû'
                        return False

                    def adjust_flag(resolved_sfx):
                        if '/' in resolved_sfx:
                            base, fl = resolved_sfx.split('/')
                            if fl.isdigit():
                                fl_num = int(fl)
                                is_rnd = is_suffix_rounded(base)
                                if is_rnd:
                                    if 1 <= fl_num <= 8:
                                        fl_num += 100
                                else:
                                    if 101 <= fl_num <= 108:
                                        fl_num -= 100
                                return f"{base}/{fl_num}"
                        return resolved_sfx

                    def unround_suffix(sfx, back):
                        res = harmonize_suffix(sfx, back, False)
                        return adjust_flag(res)
                        
                    def round_suffix(sfx, back):
                        res = harmonize_suffix(sfx, back, True)
                        return adjust_flag(res)
                    
                    if flag in [11, 111, 12, 112]:
                        if flag in [11, 111]:
                            # Back: aramak (amak), okumak (umak)
                            unrounded_sfx = unround_suffix(resolved_suffix, back=True)
                            rule_lines.append(f"SFX {flag} amak a{unrounded_sfx} amak")
                            rule_lines.append(f"SFX {flag} ımak ı{unrounded_sfx} ımak")
                            
                            rounded_sfx = round_suffix(resolved_suffix, back=True)
                            rule_lines.append(f"SFX {flag} umak u{rounded_sfx} umak")
                            num_rules += 3
                        else:
                            # Front: beklemek (emek), erimek (imek), büyümek (ümek)
                            unrounded_sfx = unround_suffix(resolved_suffix, back=False)
                            rule_lines.append(f"SFX {flag} emek e{unrounded_sfx} emek")
                            rule_lines.append(f"SFX {flag} imek i{unrounded_sfx} imek")
                            
                            rounded_sfx = round_suffix(resolved_suffix, back=False)
                            rule_lines.append(f"SFX {flag} ümek ü{rounded_sfx} ümek")
                            num_rules += 3
                    else:
                        rule_lines.append(f"SFX {flag} {strip_ending} {resolved_suffix} .")
                        num_rules += 1
            elif is_voicing:
                # Voicing verbs: gitmek, etmek, tatmak, gütmek
                # Suffixes starting with 'd' MUST become 't' suffixes!
                if suffix.startswith('d'):
                    t_suffix = 't' + suffix[1:]
                    rule_lines.append(f"SFX {flag} {strip_ending} {t_suffix} {strip_ending}")
                    num_rules += 1
                else:
                    # If suffix starts with a vowel (or y + vowel)
                    starts_with_vowel = suffix[0].lower() in 'aeıioöuü' or (suffix.startswith('y') and len(suffix) > 1 and suffix[1].lower() in 'aeıioöuü')
                    if starts_with_vowel:
                        # Strip 'tmek' or 'tmak' and add 'd' + suffix
                        voicing_strip = 't' + strip_ending
                        voiced_addition = 'd' + suffix
                        rule_lines.append(f"SFX {flag} {voicing_strip} {voiced_addition} {voicing_strip}")
                        num_rules += 1
                    else:
                        # Strip 'mek'/'mak' and add suffix (keeps 't')
                        rule_lines.append(f"SFX {flag} {strip_ending} {suffix} {strip_ending}")
                        num_rules += 1
            elif is_narrowing:
                # Narrowing verbs: demek, yemek
                # Suffixes starting with 'e' (like en, erek, ecek) take buffer y and narrow e->i (so we add i + y + suffix)
                # Suffixes starting with 'i':
                #   - 'iyor' narrows e->i directly without buffer y (so we add suffix)
                #   - 'ip' and 'ince' can narrow to i and take buffer y (add i + y + suffix), or keep e and take buffer y (add e + y + suffix)
                if suffix.startswith('er') and suffix != 'erek':
                    # Aorist: Ar -> er. de + r -> der.
                    addition = 'r' + suffix[2:]
                    rule_lines.append(f"SFX {flag} mek {addition} demek")
                    rule_lines.append(f"SFX {flag} mek {addition} yemek")
                    num_rules += 2
                elif suffix[0] == 'e':
                    addition = 'iy' + suffix
                    rule_lines.append(f"SFX {flag} emek {addition} demek")
                    rule_lines.append(f"SFX {flag} emek {addition} yemek")
                    num_rules += 2
                elif suffix.startswith('iyor'):
                    addition = suffix
                    rule_lines.append(f"SFX {flag} emek {addition} demek")
                    rule_lines.append(f"SFX {flag} emek {addition} yemek")
                    num_rules += 2
                elif suffix[0] == 'i':
                    addition_i = 'iy' + suffix
                    addition_e = 'ey' + suffix[1:]
                    rule_lines.append(f"SFX {flag} emek {addition_i} demek")
                    rule_lines.append(f"SFX {flag} emek {addition_e} demek")
                    rule_lines.append(f"SFX {flag} emek {addition_i} yemek")
                    num_rules += 3
                else:
                    # Consonant suffixes: keep 'e' by stripping 'mek'
                    rule_lines.append(f"SFX {flag} mek {suffix} demek")
                    rule_lines.append(f"SFX {flag} mek {suffix} yemek")
                    num_rules += 2
            else:
                rule_lines.append(f"SFX {flag} {strip_ending} {suffix} .")
                num_rules += 1
                
        header_line = f"SFX {flag} Y {num_rules}"
        return header_line + '\n' + '\n'.join(rule_lines)

    # 1. Generate noun paradigms (1 to 8)
    print("Generating Noun Paradigm 1 (Back Consonant)...")
    content += "\n# PARADIGM 1: BACK CONSONANT (UNROUNDED)\n" + generate_noun_sfx(1, back_vowel=True, vowel_end=False, rounded=False) + "\n"
    content += "\n# PARADIGM 101: BACK CONSONANT (ROUNDED)\n" + generate_noun_sfx(101, back_vowel=True, vowel_end=False, rounded=True) + "\n"
    
    print("Generating Noun Paradigm 2 (Front Consonant)...")
    content += "\n# PARADIGM 2: FRONT CONSONANT (UNROUNDED)\n" + generate_noun_sfx(2, back_vowel=False, vowel_end=False, rounded=False) + "\n"
    content += "\n# PARADIGM 102: FRONT CONSONANT (ROUNDED)\n" + generate_noun_sfx(102, back_vowel=False, vowel_end=False, rounded=True) + "\n"
    
    print("Generating Noun Paradigm 3 (Back Vowel)...")
    content += "\n# PARADIGM 3: BACK VOWEL (UNROUNDED)\n" + generate_noun_sfx(3, back_vowel=True, vowel_end=True, rounded=False) + "\n"
    content += "\n# PARADIGM 103: BACK VOWEL (ROUNDED)\n" + generate_noun_sfx(103, back_vowel=True, vowel_end=True, rounded=True) + "\n"
    
    print("Generating Noun Paradigm 4 (Front Vowel)...")
    content += "\n# PARADIGM 4: FRONT VOWEL (UNROUNDED)\n" + generate_noun_sfx(4, back_vowel=False, vowel_end=True, rounded=False) + "\n"
    content += "\n# PARADIGM 104: FRONT VOWEL (ROUNDED)\n" + generate_noun_sfx(104, back_vowel=False, vowel_end=True, rounded=True) + "\n"
    
    print("Generating Noun Paradigm 5 (Back Voicing)...")
    content += "\n# PARADIGM 5: BACK VOICING (UNROUNDED)\n" + generate_noun_sfx(5, back_vowel=True, vowel_end=False, rounded=False, voicing=True) + "\n"
    content += "\n# PARADIGM 105: BACK VOICING (ROUNDED)\n" + generate_noun_sfx(105, back_vowel=True, vowel_end=False, rounded=True, voicing=True) + "\n"
    
    print("Generating Noun Paradigm 6 (Front Voicing)...")
    content += "\n# PARADIGM 6: FRONT VOICING (UNROUNDED)\n" + generate_noun_sfx(6, back_vowel=False, vowel_end=False, rounded=False, voicing=True) + "\n"
    content += "\n# PARADIGM 106: FRONT VOICING (ROUNDED)\n" + generate_noun_sfx(106, back_vowel=False, vowel_end=False, rounded=True, voicing=True) + "\n"
    
    print("Generating Noun Paradigm 7 (Back Vowel Drop)...")
    content += "\n# PARADIGM 7: BACK VOWEL DROP (UNROUNDED)\n" + generate_noun_sfx(7, back_vowel=True, vowel_end=False, rounded=False, vowel_drop=True) + "\n"
    content += "\n# PARADIGM 107: BACK VOWEL DROP (ROUNDED)\n" + generate_noun_sfx(107, back_vowel=True, vowel_end=False, rounded=True, vowel_drop=True) + "\n"
    
    print("Generating Noun Paradigm 8 (Front Vowel Drop)...")
    content += "\n# PARADIGM 8: FRONT VOWEL DROP (UNROUNDED)\n" + generate_noun_sfx(8, back_vowel=False, vowel_end=False, rounded=False, vowel_drop=True) + "\n"
    content += "\n# PARADIGM 108: FRONT VOWEL DROP (ROUNDED)\n" + generate_noun_sfx(108, back_vowel=False, vowel_end=False, rounded=True, vowel_drop=True) + "\n"

    # 1b. Generate second-fold noun paradigms (81 to 84)
    print("Generating Second-Fold Noun Paradigm 81...")
    content += "\n# SECOND-FOLD PARADIGM 81: BACK CONSONANT (UNROUNDED)\n" + generate_noun_sfx(81, back_vowel=True, vowel_end=False, rounded=False) + "\n"
    content += "\n# SECOND-FOLD PARADIGM 181: BACK CONSONANT (ROUNDED)\n" + generate_noun_sfx(181, back_vowel=True, vowel_end=False, rounded=True) + "\n"
    
    print("Generating Second-Fold Noun Paradigm 82...")
    content += "\n# SECOND-FOLD PARADIGM 82: FRONT CONSONANT (UNROUNDED)\n" + generate_noun_sfx(82, back_vowel=False, vowel_end=False, rounded=False) + "\n"
    content += "\n# SECOND-FOLD PARADIGM 182: FRONT CONSONANT (ROUNDED)\n" + generate_noun_sfx(182, back_vowel=False, vowel_end=False, rounded=True) + "\n"
    
    print("Generating Second-Fold Noun Paradigm 83...")
    content += "\n# SECOND-FOLD PARADIGM 83: BACK VOWEL (UNROUNDED)\n" + generate_noun_sfx(83, back_vowel=True, vowel_end=True, rounded=False) + "\n"
    content += "\n# SECOND-FOLD PARADIGM 183: BACK VOWEL (ROUNDED)\n" + generate_noun_sfx(183, back_vowel=True, vowel_end=True, rounded=True) + "\n"
    
    print("Generating Second-Fold Noun Paradigm 84...")
    content += "\n# SECOND-FOLD PARADIGM 84: FRONT VOWEL (UNROUNDED)\n" + generate_noun_sfx(84, back_vowel=False, vowel_end=True, rounded=False) + "\n"
    content += "\n# SECOND-FOLD PARADIGM 184: FRONT VOWEL (ROUNDED)\n" + generate_noun_sfx(184, back_vowel=False, vowel_end=True, rounded=True) + "\n"

    print("Generating Second-Fold Noun Paradigm 85...")
    content += "\n# SECOND-FOLD PARADIGM 85: BACK VOICING (UNROUNDED)\n" + generate_noun_sfx(85, back_vowel=True, vowel_end=False, rounded=False, voicing=True) + "\n"
    content += "\n# SECOND-FOLD PARADIGM 185: BACK VOICING (ROUNDED)\n" + generate_noun_sfx(185, back_vowel=True, vowel_end=False, rounded=True, voicing=True) + "\n"
    
    print("Generating Second-Fold Noun Paradigm 86...")
    content += "\n# SECOND-FOLD PARADIGM 86: FRONT VOICING (UNROUNDED)\n" + generate_noun_sfx(86, back_vowel=False, vowel_end=False, rounded=False, voicing=True) + "\n"
    content += "\n# SECOND-FOLD PARADIGM 186: FRONT VOICING (ROUNDED)\n" + generate_noun_sfx(186, back_vowel=False, vowel_end=False, rounded=True, voicing=True) + "\n"

    # 2. Verb paradigms (9 to 12, 15, 16)
    print("Generating Verb Paradigm 9 (Back Consonant)...")
    back_suffixes_cons_unr = generate_verb_suffixes(back_vowel=True, vowel_stem=False, rounded=False)
    back_suffixes_cons_rnd = generate_verb_suffixes(back_vowel=True, vowel_stem=False, rounded=True)
    content += "\n# PARADIGM 9: BACK CONSONANT VERBS (UNROUNDED)\n" + format_verb_rules(9, 'mak', back_suffixes_cons_unr) + "\n"
    content += "\n# PARADIGM 109: BACK CONSONANT VERBS (ROUNDED)\n" + format_verb_rules(109, 'mak', back_suffixes_cons_rnd) + "\n"
    
    print("Generating Verb Paradigm 10 (Front Consonant)...")
    front_suffixes_cons_unr = generate_verb_suffixes(back_vowel=False, vowel_stem=False, rounded=False)
    front_suffixes_cons_rnd = generate_verb_suffixes(back_vowel=False, vowel_stem=False, rounded=True)
    content += "\n# PARADIGM 10: FRONT CONSONANT VERBS (UNROUNDED)\n" + format_verb_rules(10, 'mek', front_suffixes_cons_unr) + "\n"
    content += "\n# PARADIGM 110: FRONT CONSONANT VERBS (ROUNDED)\n" + format_verb_rules(110, 'mek', front_suffixes_cons_rnd) + "\n"
    
    print("Generating Verb Paradigm 11 (Back Vowel)...")
    back_suffixes_vowel_unr = generate_verb_suffixes(back_vowel=True, vowel_stem=True, rounded=False)
    back_suffixes_vowel_rnd = generate_verb_suffixes(back_vowel=True, vowel_stem=True, rounded=True)
    content += "\n# PARADIGM 11: BACK VOWEL VERBS (UNROUNDED)\n" + format_verb_rules(11, 'mak', back_suffixes_vowel_unr, is_vowel_stem=True) + "\n"
    content += "\n# PARADIGM 111: BACK VOWEL VERBS (ROUNDED)\n" + format_verb_rules(111, 'mak', back_suffixes_vowel_rnd, is_vowel_stem=True) + "\n"
    
    print("Generating Verb Paradigm 12 (Front Vowel)...")
    front_suffixes_vowel_unr = generate_verb_suffixes(back_vowel=False, vowel_stem=True, rounded=False)
    front_suffixes_vowel_rnd = generate_verb_suffixes(back_vowel=False, vowel_stem=True, rounded=True)
    content += "\n# PARADIGM 12: FRONT VOWEL VERBS (UNROUNDED)\n" + format_verb_rules(12, 'mek', front_suffixes_vowel_unr, is_vowel_stem=True) + "\n"
    content += "\n# PARADIGM 112: FRONT VOWEL VERBS (ROUNDED)\n" + format_verb_rules(112, 'mek', front_suffixes_vowel_rnd, is_vowel_stem=True) + "\n"
    
    print("Generating Verb Paradigm 15 (Back Voicing)...")
    content += "\n# PARADIGM 15: BACK VOICING VERBS (UNROUNDED)\n" + format_verb_rules(15, 'mak', back_suffixes_cons_unr, is_voicing=True) + "\n"
    content += "\n# PARADIGM 115: BACK VOICING VERBS (ROUNDED)\n" + format_verb_rules(115, 'mak', back_suffixes_cons_rnd, is_voicing=True) + "\n"
    
    print("Generating Verb Paradigm 16 (Front Voicing)...")
    content += "\n# PARADIGM 16: FRONT VOICING VERBS (UNROUNDED)\n" + format_verb_rules(16, 'mek', front_suffixes_cons_unr, is_voicing=True) + "\n"
    content += "\n# PARADIGM 116: FRONT VOICING VERBS (ROUNDED)\n" + format_verb_rules(116, 'mek', front_suffixes_cons_rnd, is_voicing=True) + "\n"
    
    print("Generating Verb Paradigm 17 (Narrowing)...")
    content += "\n# PARADIGM 17: NARROWING VERBS\n" + format_verb_rules(17, 'mek', front_suffixes_cons_unr, is_narrowing=True) + "\n"

    # Paradigm 13 & 14 (Compounds)
    def generate_compound_sfx(flag, back_vowel):
        lines = []
        ki_suffixes = [
            'ler', 'leri', 'lerini', 'lerine', 'lerinde', 'lerinden', 'leriyle', 'lerinin',
            'leriyse', 'leridir', 'leriymiş', 'leriydi', 'leriyse',
            'ni', 'ne', 'nde', 'nden', 'nin', 'yle', 'yse', 'dir', 'ymiş', 'ydi', 'ydim', 'ydin'
        ]
        
        if back_vowel:
            # Helper to generate case/ki rules
            def get_non_strip_rules(ending, acc, gen):
                rules = []
                for suffix in ['nda', 'ndan', 'na', acc, gen, 'yla']:
                    rules.append(("0", suffix))
                    if suffix in ['nda', gen]:
                        loc_ki = suffix + 'ki'
                        rules.append(("0", loc_ki))
                        for ki_sfx in ki_suffixes:
                            rules.append(("0", loc_ki + ki_sfx))
                # Add vowel copulas directly to the compound base
                stem_for_harmony = "kutu" if ending == 'u' else "oda"
                for cop_temp in COPULAS_VOWEL:
                    resolved_cop = append_suffix_harmonized(stem_for_harmony, cop_temp)
                    rules.append(("0", resolved_cop))
                return rules

            rules_ı = get_non_strip_rules('ı', 'nı', 'nın')
            for strip, add in rules_ı:
                lines.append(f"SFX {flag} {strip} {add} ı")
                
            rules_u = get_non_strip_rules('u', 'nu', 'nun')
            for strip, add in rules_u:
                lines.append(f"SFX {flag} {strip} {add} u")

            plural_suffixes = ['ları', 'larında', 'larından', 'larına', 'larını', 'larının', 'larıyla']
            if flag == 113:
                extra_possessives_back = [
                    'm', 'ma', 'mı', 'mda', 'mdan', 'mın', 'mla', 'mdadır', 'mken',
                    'n', 'na', 'nı', 'nda', 'ndan', 'nın', 'nla', 'ndadır', 'nken',
                    'mız', 'mıza', 'mızı', 'mızda', 'mızdan', 'mızın', 'mızla', 'mızdir', 'mızken',
                    'nız', 'nıza', 'nızı', 'nızda', 'nızdan', 'nızın', 'nızla', 'nızdır', 'nızken',
                    'um', 'uma', 'umu', 'umda', 'umdan', 'umın', 'umla', 'umdır', 'umken',
                    'un', 'una', 'unu', 'unda', 'undan', 'unun', 'unla', 'undır', 'unken',
                    'umuz', 'umuza', 'umuzu', 'umuzda', 'umuzdan', 'umuzun', 'umuzla', 'umuzdır', 'umuzken',
                    'unuz', 'unuza', 'unuzu', 'unuzda', 'unuzdan', 'unuzın', 'unuzla', 'unuzdır', 'unuzken'
                ]
            else:
                extra_possessives_back = [
                    'm', 'ma', 'mı', 'mda', 'mdan', 'mın', 'mla', 'mdadır', 'mken',
                    'n', 'na', 'nı', 'nda', 'ndan', 'nın', 'nla', 'ndadır', 'nken',
                    'mız', 'mıza', 'mızı', 'mızda', 'mızdan', 'mızın', 'mızla', 'mızdır', 'mızken',
                    'nız', 'nıza', 'nızı', 'nızda', 'nızdan', 'nızın', 'nızla', 'nızdır', 'nızken',
                    'ım', 'ıma', 'ımı', 'ımda', 'ımdan', 'ımın', 'ımla', 'ımdır', 'ımken',
                    'ın', 'ına', 'ını', 'ında', 'ından', 'ının', 'ınla', 'ındır', 'ınken',
                    'ımız', 'ımıza', 'ımızı', 'ımızda', 'ımızdan', 'ımızın', 'ımızla', 'ımızdır', 'ımızken',
                    'ınız', 'ınıza', 'ınızı', 'ınızda', 'ınızdan', 'ınızın', 'ınızla', 'ınızdır', 'ınızken'
                ]
            plural_possessives_back = [
                'larımız', 'larımıza', 'larımızı', 'larımızda', 'larımızdan', 'larımızın', 'larımızla', 'larımızdır',
                'larınız', 'larınıza', 'larınızı', 'larınızda', 'larınızdan', 'larınızın', 'larınızla', 'larınızdır'
            ]
            extended_plural_suffixes = list(plural_suffixes) + extra_possessives_back + plural_possessives_back
            
            # Generate relative -ki suffixes for all locative/genitive possessives
            ki_targets = [ps for ps in extended_plural_suffixes if ps.endswith(('da', 'de', 'ın', 'in', 'un', 'ün'))]
            for ps in ki_targets:
                loc_ki = ps + 'ki'
                extended_plural_suffixes.append(loc_ki)
                for ki_sfx in ki_suffixes:
                    extended_plural_suffixes.append(loc_ki + ki_sfx)

            strip_configs = [
                ('sı', 'sı'),
                ('su', 'su'),
                ('ğu', 'ğu'),
                ('ğı', 'ğı'),
                ('cu', 'cu'),
                ('cı', 'cı'),
                ('bı', 'bı'),
                ('bu', 'bu'),
                ('ı', 'tası'),
                ('ı', '[^sğcb]ı'),
                ('u', '[^sğcb]u'),
            ]
            
            for strip, cond in strip_configs:
                for ps in extended_plural_suffixes:
                    if 'ğu' in strip or 'ğı' in strip:
                        add_ps = 'ğ' + ps if ps and ps[0] in 'aeıioöuü' else 'k' + ps
                    elif 'cu' in strip or 'cı' in strip:
                        add_ps = 'c' + ps if ps and ps[0] in 'aeıioöuü' else 'ç' + ps
                    elif 'bı' in strip or 'bu' in strip:
                        add_ps = 'b' + ps if ps and ps[0] in 'aeıioöuü' else 'p' + ps
                    else:
                        add_ps = ps
                    lines.append(f"SFX {flag} {strip} {add_ps} {cond}")

        else:
            def get_non_strip_rules_front(ending, acc, gen):
                rules = []
                for suffix in ['nde', 'nden', 'ne', acc, gen, 'yle']:
                    rules.append(("0", suffix))
                    if suffix in ['nde', gen]:
                        loc_ki = suffix + 'ki'
                        rules.append(("0", loc_ki))
                        for ki_sfx in ki_suffixes:
                            rules.append(("0", loc_ki + ki_sfx))
                # Add vowel copulas directly to the compound base
                stem_for_harmony = "ütü" if ending == 'ü' else "kedi"
                for cop_temp in COPULAS_VOWEL:
                    resolved_cop = append_suffix_harmonized(stem_for_harmony, cop_temp)
                    rules.append(("0", resolved_cop))
                return rules

            rules_i = get_non_strip_rules_front('i', 'ni', 'nin')
            for strip, add in rules_i:
                lines.append(f"SFX {flag} {strip} {add} i")
                
            rules_ü = get_non_strip_rules_front('ü', 'nü', 'nün')
            for strip, add in rules_ü:
                lines.append(f"SFX {flag} {strip} {add} ü")

            plural_suffixes = ['leri', 'lerinde', 'lerinden', 'lerine', 'lerini', 'lerinin', 'leriyle']
            if flag == 114:
                extra_possessives_front = [
                    'm', 'me', 'mi', 'mde', 'mden', 'min', 'mle', 'mdedir', 'mken',
                    'n', 'ne', 'ni', 'nde', 'nden', 'nin', 'nle', 'ndedir', 'nken',
                    'miz', 'mize', 'mizi', 'mizde', 'mizden', 'mizin', 'mizle', 'mizdir', 'mizken',
                    'niz', 'nize', 'nizi', 'nizde', 'nizden', 'nizin', 'nizle', 'nizdir', 'nizken',
                    'üm', 'üme', 'ümü', 'ümde', 'ümden', 'ümün', 'ümle', 'ümdir', 'ümken',
                    'ün', 'üne', 'ünü', 'ünde', 'ünden', 'ünün', 'ünle', 'ündir', 'ünken',
                    'ümüz', 'ümüze', 'ümüzü', 'ümüzde', 'ümüzden', 'ümüzün', 'ümüzle', 'ümüzdir', 'ümüzken',
                    'ünüz', 'ünüze', 'ünüzü', 'ünüzde', 'ünüzden', 'ünüzün', 'ünüzle', 'ünüzdir', 'ünüzken'
                ]
            else:
                extra_possessives_front = [
                    'm', 'me', 'mi', 'mde', 'mden', 'min', 'mle', 'mdedir', 'mken',
                    'n', 'ne', 'ni', 'nde', 'nden', 'nin', 'nle', 'ndedir', 'nken',
                    'miz', 'mize', 'mizi', 'mizde', 'mizden', 'mizin', 'mizle', 'mizdir', 'mizken',
                    'niz', 'nize', 'nizi', 'nizde', 'nizden', 'nizin', 'nizle', 'nizdir', 'nizken',
                    'im', 'ime', 'imi', 'imde', 'imden', 'imin', 'imle', 'imdir', 'imken',
                    'in', 'ine', 'ini', 'inde', 'inden', 'inin', 'inle', 'indir', 'inken',
                    'imiz', 'imize', 'imizi', 'imizde', 'imizden', 'imizin', 'imizle', 'imizdir', 'imizken',
                    'iniz', 'inize', 'inizi', 'inizde', 'inizden', 'inizin', 'inizle', 'inizdir', 'inizken'
                ]
            plural_possessives_front = [
                'lerimiz', 'lerimize', 'lerimizi', 'lerimizde', 'lerimizden', 'lerimizin', 'lerimizle', 'lerimizdir',
                'leriniz', 'lerinize', 'lerinizi', 'lerinizde', 'lerinizden', 'lerinizin', 'lerinizle', 'lerinizdir'
            ]
            extended_plural_suffixes = list(plural_suffixes) + extra_possessives_front + plural_possessives_front
            
            # Generate relative -ki suffixes for all locative/genitive possessives
            ki_targets = [ps for ps in extended_plural_suffixes if ps.endswith(('da', 'de', 'ın', 'in', 'un', 'ün'))]
            for ps in ki_targets:
                loc_ki = ps + 'ki'
                extended_plural_suffixes.append(loc_ki)
                for ki_sfx in ki_suffixes:
                    extended_plural_suffixes.append(loc_ki + ki_sfx)

            strip_configs = [
                ('si', 'si'),
                ('sü', 'sü'),
                ('ği', 'ği'),
                ('ğü', 'ğü'),
                ('ci', 'ci'),
                ('cü', 'cü'),
                ('bi', 'bi'),
                ('bü', 'bü'),
                ('i', '[^sğcb]i'),
                ('ü', '[^sğcb]ü'),
            ]
            
            for strip, cond in strip_configs:
                for ps in extended_plural_suffixes:
                    if 'ği' in strip or 'ğü' in strip:
                        add_ps = 'ğ' + ps if ps and ps[0] in 'aeıioöuü' else 'k' + ps
                    elif 'ci' in strip or 'cü' in strip:
                        add_ps = 'c' + ps if ps and ps[0] in 'aeıioöuü' else 'ç' + ps
                    elif 'bi' in strip or 'bü' in strip:
                        add_ps = 'b' + ps if ps and ps[0] in 'aeıioöuü' else 'p' + ps
                    else:
                        add_ps = ps
                    lines.append(f"SFX {flag} {strip} {add_ps} {cond}")

        seen = set()
        unique_lines = []
        for l in lines:
            if l not in seen:
                seen.add(l)
                unique_lines.append(l)

        header_line = f"SFX {flag} Y {len(unique_lines)}"
        return header_line + '\n' + '\n'.join(unique_lines)

    print("Generating Compound Paradigm 13 (Back)...")
    content += "\n# PARADIGM 13: BACK COMPOUND (UNROUNDED)\n" + generate_compound_sfx(13, back_vowel=True) + "\n"
    content += "\n# PARADIGM 113: BACK COMPOUND (ROUNDED)\n" + generate_compound_sfx(113, back_vowel=True) + "\n"
    
    print("Generating Compound Paradigm 14 (Front)...")
    content += "\n# PARADIGM 14: FRONT COMPOUND (UNROUNDED)\n" + generate_compound_sfx(14, back_vowel=False) + "\n"
    content += "\n# PARADIGM 114: FRONT COMPOUND (ROUNDED)\n" + generate_compound_sfx(114, back_vowel=False) + "\n"

    print("Generating Noun Paradigm 18 (Back Doubling)...")
    content += "\n# PARADIGM 18: BACK DOUBLING (UNROUNDED)\n" + generate_noun_sfx(18, back_vowel=True, vowel_end=False, rounded=False, doubling=True) + "\n"
    content += "\n# PARADIGM 118: BACK DOUBLING (ROUNDED)\n" + generate_noun_sfx(118, back_vowel=True, vowel_end=False, rounded=True, doubling=True) + "\n"
    
    print("Generating Noun Paradigm 19 (Front Doubling)...")
    content += "\n# PARADIGM 19: FRONT DOUBLING (UNROUNDED)\n" + generate_noun_sfx(19, back_vowel=False, vowel_end=False, rounded=False, doubling=True) + "\n"
    content += "\n# PARADIGM 119: FRONT DOUBLING (ROUNDED)\n" + generate_noun_sfx(119, back_vowel=False, vowel_end=False, rounded=True, doubling=True) + "\n"


    print("Generating Prefix Paradigm 90...")
    prefixes = [
        "mili", "mikro", "nano", "piko", "femto", "atto",
        "kilo", "mega", "giga", "tera", "peta", "eksa",
        "anti", "hiper", "siber", "biyo", "oto", "kriyo", "psiko", "makro", "nöro"
    ]
    pfx_rules = [f"PFX 90 Y {len(prefixes)}"]
    for pref in prefixes:
        pfx_rules.append(f"PFX 90 0 {pref} .")
    content += "\n# PREFIX PARADIGM 90: METRIC AND LOAN PREFIXES\n" + "\n".join(pfx_rules) + "\n"

    # Write tr.aff
    print("Writing tr.aff...")
    with open('tr.aff', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    print("Suffix generation complete!")

if __name__ == '__main__':
    generate_grammar()
