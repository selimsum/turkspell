import json
import re
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

def is_back_vowel(word):
    lv = get_last_vowel(word)
    if lv is None:
        return True # Default fallback
    return lv in 'aıouâû'

def ends_with_vowel(word):
    all_vowel_chars = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
    return len(word) > 0 and word[-1] in all_vowel_chars

def compile_dictionary():
    print("Reading zemberek_lexicon.json...")
    with open('zemberek_lexicon.json', 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
        
    print(f"Loaded {len(lexicon)} entries from lexicon.")
    
    # Inject custom entries to resolve undetected words
    custom_entries = [
        {'lemma': 'Atatürk', 'pos': 'Noun', 'attributes': ['NoVoicing']},
        {'lemma': 'gezinge', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kafatası', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'kolonileşmek', 'pos': 'Verb', 'attributes': []},
        {'lemma': 'moderatör', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'moralsizlik', 'pos': 'Noun', 'attributes': ['Voicing']},
        {'lemma': 'yıldızlararası', 'pos': 'Noun', 'attributes': ['CompoundP3sg']},
        {'lemma': 'ötegezegen', 'pos': 'Noun', 'attributes': []},
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
        {'lemma': 'adeta', 'pos': 'Noun', 'attributes': []},
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
        {'lemma': 'fedakarlık', 'pos': 'Noun', 'attributes': ['Voicing']},
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
        {'lemma': 'güzergah', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'harekat', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'sahtekar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'tövbekar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'şehriyar', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'kanunusani', 'pos': 'Noun', 'attributes': []},
        {'lemma': 'katibiadil', 'pos': 'Noun', 'attributes': []},
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
        {'lemma': 'resmileşmek', 'pos': 'Verb', 'attributes': []},
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
        {'lemma': 'hakimiyet', 'pos': 'Noun', 'attributes': []},
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
        {'lemma': 'mahkumiyet', 'pos': 'Noun', 'attributes': []},
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
        {'lemma': 'saat', 'pos': 'Noun', 'attributes': []},
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
    ]
    # Load dynamically parsed candidates from OSCAR/Corpus pipeline if available
    import os
    oscar_path = 'oscar_parsed_candidates.json'
    if os.path.exists(oscar_path):
        try:
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
        except Exception as e:
            print(f"Warning: Failed to load {oscar_path}: {e}")

    # Load dynamically harvested undetected words if they exist
    harvested_path = 'harvested_words.json'
    if os.path.exists(harvested_path):
        try:
            with open(harvested_path, 'r', encoding='utf-8') as f:
                harvested_list = json.load(f)
            for w in harvested_list:
                # Add as standard Noun entry
                custom_entries.append({
                    'lemma': w,
                    'pos': 'Noun',
                    'attributes': []
                })
            print(f"Loaded {len(harvested_list)} harvested words from {harvested_path}.")
        except Exception as e:
            print(f"Warning: Failed to load harvested words: {e}")

    lexicon.extend(custom_entries)
    
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
    
    # Create a mapping of custom lemmas to their custom pos and attributes
    custom_map = {e['lemma'].lower(): e for e in custom_entries}
    
    for item in lexicon:
        orig_lemma = item['lemma']
        if orig_lemma == 'Atatürk':
            lemma = 'Atatürk'
        else:
            lemma = orig_lemma.replace('I', 'ı').replace('İ', 'i').lower()
            
        if 'kağıt' in lemma:
            lemma = lemma.replace('kağıt', 'kâğıt')
        
        # Override with custom entry if present
        if lemma.lower() in custom_map:
            pos = custom_map[lemma.lower()]['pos']
            attrs = set(custom_map[lemma.lower()]['attributes'])
        else:
            pos = item['pos']
            attrs = set(item['attributes'])
        
        # Skip abbreviations, punctuation, or single-character noise
        if not lemma or len(lemma) == 0:
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
        common_abbrevs = {'km', 'abd', 'örn', 'dr', 'dna', 'prof', 'x', 'mö', 'ms', 'sf', 'cm', 'kg', 'vb', 'bkz', 'm', 'g', 'b', 'mm', 'gps', 'uuı', 'uv', 'bbc', 'vr', 'dr', 'eeg', 'yz', 'sscb', 'esa', 'rfid', 'dehb', 'mit', 'ngc', 'hiv', 'sls', 'atp', 'cern', 'iq'}
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
            
        # Force Noun POS for any lemma ending in ış/iş/uş/üş that does not end in mak/mek (Deverbal Action Nouns)
        if lemma.endswith(('ış', 'iş', 'uş', 'üş')) and not lemma.endswith(('mak', 'mek')):
            pos = 'Noun'
            
        # Determine vowel harmony
        back = is_back_vowel(lemma)
        # Check Zemberek vowel exceptions
        if pos != 'Verb' and not lemma.endswith(('leşmek', 'laşmak', 'leşme', 'laşma', 'lik', 'lık', 'luk', 'lük', 'ci', 'cı', 'cu', 'cü', 'cilik', 'cılık', 'suz', 'süz', 'siz', 'suzluk', 'süzlük', 'sizlik')):
            if 'LastVowelFrontal' in attrs or 'FrontVowelHarmony' in attrs or 'InverseHarmony' in attrs:
                back = not back
            
        # Inverse harmony overrides
        inverse_harmony_words = {'kalp', 'saat', 'harf', 'rol', 'alkol', 'hâl', 'hal', 'metal', 'normal', 'ideal', 'gol', 'kontrol', 'petrol', 'seans', 'sembol', 'şefkat', 'dikkat', 'polifenol', 'flavanol', 'kortizol', 'istirahat'}
        if lemma.lower() in inverse_harmony_words or (pos != 'Verb' and (lemma.lower().endswith('âl') or lemma.lower().endswith('ûl'))):
            back = False

        vowel_end = ends_with_vowel(lemma)
        
        # Check voicing attributes
        voicing = False
        if lemma[-1] in 'pçtkg':
            # Count vowels to check if multi-syllable
            all_vowel_chars = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
            num_vowels = sum(1 for c in lemma if c in all_vowel_chars)
            # Voicing applies by default to multi-syllable nouns, or if explicitly marked/exception
            if 'Voicing' in attrs or 'VoicingOpt' in attrs or 'VoicingSelf' in attrs or num_vowels >= 2 or lemma in ['teleskop', 'radyoteleskop', 'asteroit', 'eşlik', 'karbondioksit']:
                # Exclude explicitly marked NoVoicing and a few manual exceptions
                if ('NoVoicing' not in attrs or lemma in ['teleskop', 'radyoteleskop', 'eşlik', 'karbondioksit']) and lemma not in ['dikkat', 'sepet', 'paket', 'bilet', 'kaset', 'anket', 'davet']:
                    voicing = True
                
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
                flag = "5" if back else "6"
            elif vowel_end:
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
                
            dic_entries.append(f"{lemma}/{flag}")
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
        # Back-unrounded (a/ı): last vowel is a or ı
        'ankara':    'pB',
        'atatürk':   'pB',
        'diyarbakır': 'pB',
        # Back-rounded (o/u): last vowel is o or u
        'istanbul':  'pO',   # last vowel 'u' -> back-rounded: İstanbul'un, İstanbul'da
        'anadolu':   'pO',   # last vowel 'u' -> back-rounded: Anadolu'nun
        'trabzon':   'pO',
        'ordu':      'pO',
        # Front-unrounded (e/i): last vowel is e or i
        'türkiye':   'pF',
        'izmir':     'pF',
        'edirne':    'pF',
        # Abbreviations/units: no vowel -> back-unrounded by convention
        'mm':        'pB',
        'cm':        'pB',
        'km':        'pB',
        'kg':        'pB',
    }

    # Words that should get proper-noun suffix flags.
    # Includes all entries from PROPER_NOUN_OVERRIDES plus any zemberek entry
    # tagged as ProperNoun.
    proper_nouns_to_flag: set[str] = set(PROPER_NOUN_OVERRIDES.keys())
    for item in lexicon:
        if item.get('pos') == 'ProperNoun':
            proper_nouns_to_flag.add(item['lemma'].replace('I', 'ı').replace('İ', 'i').lower())

    def _proper_flag_for(lemma_lower: str) -> str:
        if lemma_lower in PROPER_NOUN_OVERRIDES:
            return PROPER_NOUN_OVERRIDES[lemma_lower]
        lv = get_last_vowel(lemma_lower)
        return PROPER_HARMONY.get(lv, 'pB')  # default back-unrounded

    # Rebuild dic_entries, appending proper-noun flags where needed
    new_dic_entries = []
    for entry in dic_entries:
        if '/' in entry:
            lemma_part, flags_part = entry.split('/', 1)
        else:
            lemma_part, flags_part = entry, ''

        lkey = lemma_part.lower()
        if lkey in proper_nouns_to_flag:
            pfx = _proper_flag_for(lkey)
            extra = ','.join(f'{pfx}{s}' for s in PROPER_SUB_FLAGS)
            if flags_part:
                entry = f"{lemma_part}/{flags_part},{extra}"
            else:
                entry = f"{lemma_part}/{extra}"

        new_dic_entries.append(entry)

    dic_entries = new_dic_entries
    print(f"Injected proper-noun flags into {sum(1 for e in dic_entries if any(f'p{x}N' in e for x in 'BOFU'))} entries.")

    print("Writing tr.dic...")
    with open('tr.dic', 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"{len(dic_entries)}\n")
        for entry in dic_entries:
            f.write(f"{entry}\n")
            
    # Write tr.aff by calling our generator script
    print("Calling generate_grammar_rules.py to generate baseline rules...")
    try:
        from generate_grammar_rules import generate_grammar
        generate_grammar()
        
        # Now remap tr.aff in-place to FLAG UTF-8
        print("Remapping rules to FLAG UTF-8 and writing to tr.aff...")
        with open('tr.aff', 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = content.replace("FLAG long", "FLAG UTF-8")
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
                
        with open('tr.aff', 'w', encoding='utf-8', newline='\n') as f:
            f.write("\n".join(new_lines))

        # Remap tr.dic in-place: convert numeric flags + 3-char proper-noun flags to UTF-8
        print("Remapping tr.dic to FLAG UTF-8...")
        from migrate_dictionary import migrate_line as _migrate_line
        with open('tr.dic', 'r', encoding='utf-8') as f:
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
            _numeric = [p.strip() for p in _parts if not (p.strip().startswith('p') and len(p.strip()) == 3)]
            _proper  = [p.strip() for p in _parts if p.strip().startswith('p') and len(p.strip()) == 3]
            if _numeric:
                _fake = _word + '/' + ','.join(_numeric)
                _mig, _ = _migrate_line(_fake, _i, set())
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
        with open('tr.dic', 'w', encoding='utf-8', newline='\n') as f:
            f.write(str(dic_migrated) + '\n')
            f.writelines(dic_out)
        print(f"tr.dic remapped: {dic_migrated} entries.")

    except Exception as e:
        print(f"Error compiling/remapping grammar generator: {e}")

        
    print("Compile complete!")

if __name__ == "__main__":
    compile_dictionary()
