import os
import sys
import re
import shutil
import json
from pathlib import Path

BASE_DIR = Path(r"c:\gemini\turkspell-benchmarks")
TURKSPELL_DIR = Path(r"c:\gemini\turkspell")
DIST_DIR = TURKSPELL_DIR / "dist"

TDK_PATH = TURKSPELL_DIR / "raw_data" / "tdk_words.txt"
DD_PATH = TURKSPELL_DIR / "raw_data" / "dil_dernegi_words.txt"
CUSTOM_ABBREV_PATH = TURKSPELL_DIR / "lexicons" / "custom_abbreviations.json"
CUSTOM_NAMES_PATH = TURKSPELL_DIR / "lexicons" / "custom_names.json"

AFF_SRC = TURKSPELL_DIR / "tr.aff"
DIC_SRC = TURKSPELL_DIR / "tr.dic"

sys.path.insert(0, str(TURKSPELL_DIR / "build"))
from utf8_flag_mapping import UTF8_TO_LONG, LONG_TO_UTF8, remap_flag_string, remap_flag_string

vowels = "AEIOUaeiouÂÎÖÛÜâîöûüİı"
consonant_cond = "[^AEIOUaeiouÂÎÖÛÜâîöûüİı]"

DEAD_FLAG_CHARS = {LONG_TO_UTF8[f] for f in ['G2', 'NX', 'Vb', 'Vf'] if f in LONG_TO_UTF8}
PROPER_SUB_UTF8 = {k for k, v in UTF8_TO_LONG.items() if v.startswith("p") and len(v) == 3}

EXTRA_REP_RULES = [
    # Keyboard & affix boundary substitutions (m/n, j/d, z/a)
    "REP dem den",
    "REP dam dan",
    "REP dej den",
    "REP daj dan",
    "REP tem ten",
    "REP tam tan",
    "REP rim rin",
    "REP larz lara",
    "REP lerz lere",
    "REP lardan lardan",
    # Circumflex canonical rules
    "REP sükut sükût",
    "REP mahkum mahkûm",
    "REP mefkure mefkûre",
    "REP rüku rükû",
    "REP sükun sükûn",
    "REP sükunet sükûnet",
    "REP sükunetli sükûnetli",
    "REP sükunetle sükûnetle",
    "REP sükuti sükûti",
    "REP yekun yekûn",
    "REP kain kâin",
    "REP kufi kûfi",
    "REP meskun meskûn",
    "REP meşkur meşkûr",
    "REP celali celâli",
    "REP eflani eflâni",
    "REP batıniye bâtıniye",
    "REP ademcilik âdemcilik",
    "REP maniasız mâniasız",
    "REP harcıalem harcıâlem",
    "REP mahkumane mahkûmane",
    "REP mahkuk mahkûk",
    "REP mahkumiyet mahkûmiyet",
    "REP hilali hilalî",
    "REP muhammedi muhammedî",
    "REP misakımilli misakımillî",
    "REP elazig Elâzığ",
    "REP ruku rükû",
    "REP gayrimeskun gayrimeskûn",
    "REP asikar aşikâr",
    "REP ahkam ahkâm",
    "REP baskatip başkâtip",
    "REP basmekan başmekân",
    "REP agah agâh",
    "REP aliyyulala aliyyülâlâ",
    "REP aliyyülala aliyyülâlâ",
    # Common orthographic & consonant error corrections
    "REP klavuz kılavuz",
    "REP traş tıraş",
    "REP ünvan unvan",
    "REP tesbih tespih",
    "REP sayili sayılı",
    "REP numarali numaralı",
    "REP buradasiniz buradasınız",
    "REP büyüksehir büyükşehir",
    "REP herkez herkes",
    "REP herkeze herkese",
    "REP herkezin herkesin",
    "REP kiprik kirpik",
    "REP eşki ekşi",
    "REP kirbit kibrit",
    "REP şarz şarj",
    "REP şarzı şarjı",
    "REP şarzda şarjda",
    "REP egsoz egzoz",
    "REP eksoz egzoz",
    "REP tabildot tabldot",
    "REP muhattap muhatap",
    "REP kareografi koreografi",
    # Circumflex canonical inflections
    "REP imkani imkânı",
    "REP imkan imkân",
    "REP imkanlar imkânlar",
    "REP imkanları imkânları",
    "REP imkansız imkânsız",
    "REP mekani mekânı",
    "REP mekanlar mekânlar",
    "REP mekanları mekânları",
    "REP hikayesi hikâyesi",
    "REP hikayeler hikâyeler",
    "REP hikayeleri hikâyeleri",
    "REP şikayeti şikâyeti",
    "REP şikayetçi şikâyetçi",
    "REP şikayetler şikâyetler",
    "REP zekası zekâsı",
    "REP zekalı zekâlı",
    "REP rüzgarı rüzgârı",
    "REP rüzgarlar rüzgârlar",
    "REP rüzgarlı rüzgârlı",
    "REP kağıt kâğıt",
    "REP kağıdı kâğıdı",
    "REP kağıtlar kâğıtlar",
    "REP dükkan dükkân",
    "REP dükkanı dükkânı",
    "REP dükkanlar dükkânlar",
    "REP ahlak ahlâk",
    "REP ahlakı ahlâkı",
    "REP ahlaklı ahlâklı",
    # Compound & separate word rules
    "REP yanısıra yanı_sıra",
    "REP peşisıra peşi_sıra",
    "REP ardısıra ardı_sıra",
    "REP farketmek fark_etmek",
    "REP terketmek terk_etmek",
    "REP ayırdetmek ayırt_etmek",
    "REP haketmek hak_etmek",
    "REP yokolmak yok_olmak",
    "REP varolmak var_olmak",
    "REP sağol sağ_ol",
    "REP hoşçakal hoşça_kal",
    "REP hoşgeldin hoş_geldin",
    "REP hoşgeldiniz hoş_geldiniz",
    "REP herşey her_şey",
    "REP birşey bir_şey",
    "REP hiçbirşey hiçbir_şey",
    "REP icatı icadı"
]

MANDATORY_HATTED_WORDS = {
    "sükût": "sükut",
    "mahkûm": "mahkum",
    "mefkûre": "mefkure",
    "rükû": "rüku",
    "sükûn": "sükun",
    "sükûnet": "sükunet",
    "sükunetli": "sükunetli",
    "sükunetle": "sükunetle",
    "sükûti": "sükuti",
    "yekûn": "yekun",
    "kâin": "kain",
    "kûfi": "kufi",
    "meskûn": "meskun",
    "meşkûr": "meşkur",
    "harcıâlem": "harcıalem",
    "eflâni": "eflani",
    "celâli": "celali",
    "bâtıniye": "batıniye",
    "âdemcilik": "ademcilik",
    "mâniasız": "maniasız",
    "mahkûmane": "mahkumane",
    "mahkûk": "mahkuk",
    "mahkûmiyet": "mahkumiyet",
    "hilalî": "hilali",
    "muhammedî": "muhammedi",
    "misakımillî": "misakımilli",
    # Mandatory hatted words where unhatted forms are illegal in both TDK and DD
    "topyekûn": "topyekun",
    "âlemşümul": "alemşümul",
    "âlemşümullük": "alemşümullük",
    "âdemci": "ademci",
    "âcizlik": "acizlik",
    "hâkimlik": "hakimlik",
    "âlimlik": "alimlik",
    "aliyyülâlâ": "aliyyülala",
    "âmâlık": "amalık",
    "âşıkane": "aşıkane",
    "âşıklı": "aşıklı",
    "âşıklık": "aşıklık",
    "âşıktaş": "aşıktaş",
    "bâtıni": "batıni",
    "beniâdem": "beniadem",
    "dâhiyane": "dahiyane",
    "gülgûn": "gülgun",
    "günâşık": "günaşık",
    "hakkısükût": "hakkısükut",
    "hâlsizleşmek": "halsizleşmek",
    "hayâsız": "hayasız",
    "hayâsızca": "hayasızca",
    "hemhâllik": "hemhallik",
    "kârsızca": "karsızca",
    "melekût": "melekut",
    "meşkûk": "meşkuk",
    "vârislik": "varislik",
    "yâran": "yaran",
    "Elâzığlılık": "Elazığlılık"
}

# Extensive whitelist of Turkish compound-forming nouns (geographical, architectural, institutional)
COMPOUND_PROPER_TERMS = [
    # Yer şekilleri & sular
    'dağ', 'dağı', 'dağları', 'tepe', 'tepesi', 'ova', 'ovası', 'vadi', 'vadisi', 'kanyon', 'kanyonu', 'plato', 'platosu',
    'göl', 'gölü', 'gölleri', 'baraj', 'barajı', 'gölet', 'göleti', 'lagün', 'lagünü',
    'deniz', 'denizi', 'okyanus', 'okyanusu', 'körfez', 'körfezi', 'koy', 'koyu', 'boğaz', 'boğazı', 'kanal', 'kanalı', 'burun', 'burnu', 'yarımada', 'yarımadası', 'ada', 'adası', 'adaları',
    'nehir', 'nehri', 'ırmak', 'ırmağı', 'çay', 'çayı', 'dere', 'deresi', 'şelale', 'şelalesi', 'geçit', 'geçidi',
    # Yapılar
    'saray', 'sarayı', 'köşk', 'köşkü', 'konak', 'konağı', 'kasır', 'kasrı', 'han', 'hanı', 'kervansaray', 'kervansarayı', 'hamam', 'hamamı',
    'kale', 'kalesi', 'hisar', 'hisarı', 'sur', 'surları', 'kule', 'kulesi', 'burç', 'burcu',
    'köprü', 'köprüsü', 'viyadük', 'viyadüğü', 'tünel', 'tüneli', 'anıt', 'anıtı', 'abide', 'abidesi', 'heykel', 'heykeli',
    'cami', 'camisi', 'camii', 'mescit', 'mescidi', 'kilise', 'kilisesi', 'havra', 'havrası', 'sinagog', 'sinagogu', 'türbe', 'türbesi', 'manastır', 'manastırı', 'medrese', 'medresesi', 'külliye', 'külliyesi', 'tekke', 'tekkesi', 'zaviye', 'zaviyesi', 'mezarlık', 'mezarlığı', 'şehitlik', 'şehitliği',
    'gar', 'garı', 'istasyon', 'istasyonu', 'liman', 'limanı', 'iskele', 'iskelesi', 'terminal', 'terminali', 'otogar', 'otogarı',
    'park', 'parkı', 'bahçe', 'bahçesi', 'koru', 'korusu', 'orman', 'ormanı', 'yayla', 'yaylası',
    'stadyum', 'stadyumu', 'stad', 'stadı', 'salon', 'salonu', 'hipodrom', 'hipodromu', 'havuz', 'havuzu', 'pist', 'pisti', 'tesis', 'tesisi', 'tesisleri',
    # Kentsel
    'mahalle', 'mahallesi', 'meydan', 'meydanı', 'bulvar', 'bulvarı', 'cadde', 'caddesi', 'sokak', 'sokağı', 'yokuş', 'yokuşu', 'çıkmaz', 'çıkmazı', 'kavşak', 'kavşağı',
    # Kurumsal
    'meclis', 'meclisi', 'bakanlık', 'bakanlığı', 'başkanlık', 'başkanlığı', 'müsteşarlık', 'müsteşarlığı', 'müdürlük', 'müdürlüğü', 'daire', 'dairesi', 'valilik', 'valiliği', 'kaymakamlık', 'kaymakamlığı', 'belediye', 'belediyesi', 'muhtarlık', 'muhtarlığı',
    'mahkeme', 'mahkemesi', 'savcılık', 'savcılığı', 'başsavcılık', 'başsavcılığı', 'baro', 'barosu',
    'üniversite', 'üniversitesi', 'fakülte', 'fakültesi', 'enstitü', 'enstitüsü', 'yüksekokul', 'yüksekokulu', 'okul', 'okulu', 'lise', 'lisesi', 'kolej', 'koleji', 'akademi', 'akademisi', 'dershane', 'dershanesi', 'anaokulu', 'ilkokul', 'ilkokulu', 'ortaokul', 'ortaokulu', 'rasathane', 'rasathanesi',
    'hastane', 'hastanesi', 'dispanser', 'dispanseri', 'poliklinik', 'polikliniği', 'ocak', 'ocağı', 'klinik', 'kliniği',
    'dernek', 'derneği', 'vakıf', 'vakfı', 'birlik', 'birliği', 'federasyon', 'federasyonu', 'konfederasyon', 'konfederasyonu', 'oda', 'odası', 'borsa', 'borsası', 'sendika', 'sendikası', 'kooperatif', 'kooperatifi', 'kulüp', 'kulübü', 'cemiyet', 'cemiyeti', 'komisyon', 'komisyonu', 'kurul', 'kurulu', 'ajans', 'ajansı', 'banka', 'bankası', 'merkez', 'merkezi', 'laboratuvar', 'laboratuvarı', 'kütüphane', 'kütüphanesi', 'müze', 'müzesi', 'tiyatro', 'tiyatrosu', 'opera', 'operası', 'bale', 'balesi', 'orkestra', 'orkestrası'
]
COMPOUND_SET = set(COMPOUND_PROPER_TERMS)

LEGITIMATE_MISSED_WORDS = [
    # Ince 'l' and borrowing vowel harmony inflections
    "golü", "golüydü", "gollere", "golümüz",
    "rolü", "rolümüz", "rolleri",
    "ihtilaller", "ihtilallerde", "ihtilallere",
    "mamulü", "mamulünü", "mamulleri",
    "karambolü", "karambolüne",
    "kontrolü", "kontrolünüze", "kontrolleri",
    "kolonizasyon", "kolonizasyonu",
    # Internal vowel drop & inflection chains
    "emrinde", "emrindeymiş",
    "zehrin",
    "köprüaltı",
    "feyzli",
    "tilavet", "tilaveti",
    "rehneden",
    "külhanbey",
    # Legitimate Turkish derivations & inflections
    "fiyatlama", "fiyatlamasında", "fiyatlamalar",
    "tanınırlık", "tanınırlığının",
    "tanırı", "tanırının",
    "işleticilik", "işleticiliği",
    "dilsizleşme",
    "zararlandırma",
    "edilemezlik", "edilemezliği",
    "geçirmezlik",
    "hayaletimsi",
    "menekşemsi",
    "paranoyaklaşmış",
    "politikasızlık", "politikasızlığın",
    "şikayetname", "şikayetnamede",
    "şümul", "şümulünden",
    "mağdure", "mağdurelerle",
    "ardındayken",
    "ferdileştirilerek",
    "yaptıklarındır",
    "kimliklendirilecek",
    "sivilcelenmeler",
    "siyasileştirilemez",
    "sorunsallaştırdığı",
    "tarikatlaşma",
    "taşeronlaştırmanın",
    "temyizen",
    "terörize",
    "ucumuzu",
    "velayete",
    "yuhla",
    "kargolanıp",
    "mahsuplaşmak",
    "metalaşması",
    "sümeroloji", "sumeroloji",
    "süreklenen",
    "çerli",
    "sağınç",
    "müdebber",
    "derdirten",
    "şarlarını",
    "haylicesi",
    "garipçenin",
    "entelejansiyasını",
    "istimlâkten",
    # Official TDK Circumflex entries
    "hâlet", "hâletiruhiye", "merkûp", "vâkıâ", "arzuhâl", "arzuhâlci",
    "mahkûmane", "lâm", "merzengûş", "gayrimeskûn", "şûra",
    "elâzığlı", "hâlsizleşmek", "hâllenme", "âlemcilik",
    "dâhil", "dâhilen", "dâhiliye", "dâhiliyeci",
    "bâtın", "bâtıni", "bâtıniye",
    "herhâlde", "hâlde", "hâlen", "hâlihazır", "hâlihazırda", "hâlinde",
    "hâlleşme", "hâlleşmek", "hâlli", "hâllilik", "hâlsizleşme", "hâlükârda",
    "ibretiâlem", "sâdır", "vâkıflık", "âlimane", "âlâsı",
    "arzuhâlcilik", "hikâyesi", "kabîlden", "ilahî", "leylâ", "kâhyası", "âdetgörmezlik",
    # Valid passive verb derivations
    "uçulmak/≞⊅", "uçularak",
    # TDK loanword adjective
    "total",
    # Added legitimate stems
    "hasılat", "ihlalci"
]


HEAD_FLAG_OVERRIDES = {
    # değil: copular/predicate flags
    "değil": remap_flag_string("A3 CI CK DE DL DT F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 Y2 cl".replace(" ", "")),
    # ait: copular/predicate flags
    "ait": remap_flag_string("A3 CI CK DE DL DT F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 Y2 cl".replace(" ", "")),
    # felaket: unvoiced front noun (F1, no voicing V3)
    "felaket": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 SL Y2 cl CI LI LK SZ".replace(" ", "")),
    # stok: unvoiced back rounded noun (B2, no voicing V2)
    "stok": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1".replace(" ", "")),
    # ilmek: both noun and verb flags
    "ilmek": remap_flag_string("CI CK DE I2 L2 LI LK PF Q2 R2 SL SZ cl F1 A3 N3 P3 P7 PP PU PW Y2 VF wj".replace(" ", "")),
    # adem: yokluk (no CI flag, preventing illegal *ademci / *Ademci while preserving legit cases)
    "adem": remap_flag_string("A3 CK F1 I2 L2 LK N3 P3 P7 PF PP PU PW Q2 R2 SZ Y2 cl".replace(" ", "")),
    # aciz: unhatted (no LK flag, so unhatted *acizlik cannot be generated; only âcizlik exists)
    "aciz": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 SZ Y2 cl".replace(" ", "")),
    # hakim: unhatted bilge/hekim (no LK flag, so *hakimlik cannot be generated; only hâkimlik exists)
    "hakim": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 SZ Y2 cl".replace(" ", "")),
    # teşkilat: unvoiced back noun (A1, B1, N1, P1, etc. instead of verb flags V1)
    "teşkilat": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    # nezt: huzur/kat/yan (nezdinde, nezdindeki)
    "nezt": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 Y2 cl KI".replace(" ", "")),
    # nezdinde: (nezdindeki, nezdindekiler)
    "nezdinde": remap_flag_string("CI CK F3 L2 P3 P7 PF PP PU PW Q2 R2 a3 cl i2 n3 y2 KI".replace(" ", "")),
    # despot: unvoiced back rounded noun (B2, no voicing V2)
    "despot": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1 DL DT DE".replace(" ", "")),
    # ihlalci: front vowel unrounded noun (F3)
    "ihlalci": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl LI LK SZ CI CK SL DL DT DE".replace(" ", "")),
}

# Standard regular non-voicing inflection flags
BACK_UNVOICED_FLAGS = remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", ""))
FRONT_UNVOICED_FLAGS = remap_flag_string("A3 CI CK DE F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl".replace(" ", ""))

# Stems attested in corpus as non-voicing that erroneously had V1/V3 or missing nominal flags
BACK_NOVOICING_STEMS = [
    "imalat", "tahsilat", "harekat", "tatbikat", "tadilat", "salat", "bürokrat",
    "kâinat", "belagat", "boydak", "istihbarat", "muamelat", "müfredat",
    "mefruşat", "nebatat", "haşarat", "barikat", "nasihat", "kabahat", "mükafat",
    "pasaport", "rahat", "bask", "mark", "bank", "fırsat", "ark", "park", "şok",
    "hasılat"
]

# Front-vowel non-voicing stems (including Arabic/Persian loanwords ending in -at and -al taking front harmony)
FRONT_NOVOICING_STEMS = [
    "seyahat", "hakikat", "cemaat", "menfaat", "sadakat", "dikkat", "şefkat",
    "ihtimal", "hilal", "helal", "hayal", "ithal", "ihlal", "işgal", "ihmal",
    "zeval", "intikal", "infial", "istiklal", "santral", "moral",
    "cennet", "beraat", "akıbet", "aktivist", "ahret", "adalat", "dakik",
    "politik", "antik", "melik", "malik", "patik", "vilayet", "bereket",
    "dehşet", "edremit", "ehlisünnet", "elbet", "ensefalit", "eternit",
    "faset", "brifing", "damping", "doping", "bumerang", "aysberg",
    "dramaturg", "andezit", "babet", "bangkok", "beyrut", "dargeçit",
    "derik", "doğubeyazıt", "ehlibeyt", "çöp", "met", "çet",
    "arktik"
]

for _w in BACK_NOVOICING_STEMS:
    if _w not in HEAD_FLAG_OVERRIDES:
        HEAD_FLAG_OVERRIDES[_w] = BACK_UNVOICED_FLAGS
for _w in FRONT_NOVOICING_STEMS:
    if _w not in HEAD_FLAG_OVERRIDES:
        HEAD_FLAG_OVERRIDES[_w] = FRONT_UNVOICED_FLAGS

_voicing_table = {"p": "b", "ç": "c", "t": "d", "k": "ğ", "g": "ğ"}
PURGE_VIRTUAL_STEMS = {"felaked", "stoğ"}
for _w in BACK_NOVOICING_STEMS + FRONT_NOVOICING_STEMS:
    if _w and _w[-1] in _voicing_table:
        PURGE_VIRTUAL_STEMS.add(_w[:-1] + _voicing_table[_w[-1]])

PALATAL_L_HEADS = {
    "alkol", "ampul", "kontrol", "otokontrol", "rol", "başrol",
    "sembol", "petrol", "protokol", "kolesterol", "metropol",
    "usul", "mahsul", "alveol", "kabul", "makbul", "faul", "hol"
}
# Pure palatal l flags: front rounded vowels, NO regular back-vowel SZ/CI, includes R2 (ablative -den), I2 (-le), PQ (-ümüz), PZ (-ünüz)
PALATAL_L_FLAGS = remap_flag_string("A4 N4 PV P8 Y2 L2 R2 I2 PQ PZ CK cl LF LSZ LFK LCI PF".replace(" ", ""))

VIRTUAL_STEMS = [
    # ard (art -> ard-ı, ard-ı-n-da, ard-ı-n-dan, ard-ı-n-a)
    "ard/X∀∫∲∶∼∽≂≣",
    # icad (icat -> icad-ı, icad-ı-n-da, icad-ı-n-dan, icad-ı-n-ı)
    "icad/X∀∫∲∶∼∽≂≣",
    # kab (kap -> kab-ı, kab-ı-n-da, kab-ı-n-dan, kab-ı-n-ı)
    "kab/X∀∫∲∶∼∽≂≣",
    # kayd (kayıt -> kayd-ı, kayd-ı-n-da, kayd-ı-n-dan, kayd-ı-n-ı)
    "kayd/X∀∫∲∶∼∽≂≣",
    # lob (lop -> lob-u, lob-u-n-da, lob-u-n-dan, lob-lar, lob-lar-da)
    "lob/X∁∬∳∷∾≁≃≕≣" + remap_flag_string("I1 L1 PB Q1 R1 SZ".replace(" ", "")),
    # ilmeğ (ilmek -> ilmeğ-i, ilmeğ-i-n-e, ilmeğ-i-m)
    "ilmeğ/X∂∭∴∸∿≄≆≤≽",
    # serçeparmağ (serçeparmak -> serçeparmağ-a, serçeparmağ-ı)
    "serçeparmağ/X∀∫∲∶∼∽≂≕≣",
    # Short nouns with stem voicing:
    # tat (tat -> tad-ı, tad-ı-n-da, tad-ı-n-dan, tad-ı-n-ı, tad-a, tad-ı-m, tad-ı-n)
    "tad/X∀∫∲∶∼∽≂≕≣",
    # uç (uç -> uc-u, uc-u-n-da, uc-u-n-dan, uc-u-n-u, uc-a, uc-u-m, uc-u-n)
    "uc/X∁∬∳∷∾≁≃≕≣",
    # cep (cep -> ceb-i, ceb-i-n-de, ceb-i-n-den, ceb-i-n-i, ceb-e, ceb-i-m, ceb-i-n)
    "ceb/X∂∭∴∸∿≄≆≤≽",
    # gök (gök -> göğ-ü, göğ-ü-n-de, göğ-ü-n-den, göğ-ü-n-ü, göğ-e, göğ-ü-m, göğ-ü-n)
    "göğ/X∃∮∵∹≀≅≈≤≽",
    # öç (öç -> öc-ü, öc-ü-n-de, öc-ü-n-den, öc-ü-n-ü, öc-e, öc-ü-m, öc-ü-n)
    "öc/X∃∮∵∹≀≅≈≤≽",
    # but (but -> bud-u, bud-u-n-da, bud-u-n-dan, bud-u-n-u, bud-a, bud-u-m, bud-u-n)
    "bud/X∁∬∳∷∾≁≃≕≣",
    # ut (ut -> ud-u, ud-u-n-da, ud-u-n-dan, ud-u-n-u, ud-a, ud-u-m, ud-u-n)
    "ud/X∁∬∳∷∾≁≃≕≣",
    # kulp (kulp -> kulb-u, kulb-u-n-da, kulb-u-n-dan, kulb-u-n-u, kulb-a, kulb-u-m)
    "kulb/X∁∬∳∷∾≁≃≕≣",
    # ceht (ceht -> cehd-i, cehd-i-n-de, cehd-i-n-den, cehd-i-n-i, cehd-e, cehd-i-m)
    "cehd/X∂∭∴∸∿≄≆≤≽",
    # bloğ (blok -> bloğ-u, bloğ-u-n-da, bloğ-u-n-dan, bloğ-u-n-u, bloğ-a, bloğ-u-m, bloğ-u-n, bloğ-u-muz, bloğ-u-nuz)
    "bloğ/X∁∬∳∷∾≁≃≕≣",
    # tedariğ (tedarik -> tedariğ-i, tedariğ-i-n-de, tedariğ-i-n-den, tedariğ-i-n-i, tedariğ-e, tedariğ-i-m, tedariğ-i-n)
    "tedariğ/X∂∭∴∸∿≄≆≤≽",
]

EXTRA_AUTHORITY_HEADWORDS = [
    # Copula & predicate defective verbs:
    "idi/∴∸≆∻≩",
    "idik",
    "imiş/∂∌∍∖∗∘∙∢∨∩∪∭∴∸∻∿≄≆≊≌≤≩",
    # Cami, Mevki & Sanayi compound & possessive forms (P7 chain -nde, -nden, -ndeki, -nin):
    "camii/∸",
    "Camii/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mevkii/∸",
    "Mevkii/⊘⊙⊚⊛⊜⊝⊞⊟",
    "sanayii/∸",
    "Sanayii/⊘⊙⊚⊛⊜⊝⊞⊟",
    # Authoritative TDK/DD missed common roots:
    "mut/" + remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SZ Y1".replace(" ", "")),
    "ayaklamak/≟",
    # TDK / DD regular derived or compound words
    "çıtır/" + remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SZ Y1".replace(" ", "")),
    "çerçöp/∃∌∍∖√∢∨∩∪∮∵∹∻≀≅≈≊≌≍≎≤≩",
    "serçeparmak/∌∍∎∡∧∩∪∺≉≋≍≎≏≔≾",
    "tutamak/" + remap_flag_string("CI CK CL I1 L1 LI LK PB Q1 R1 SZ V1".replace(" ", "")),
    "sürücüsüz/" + remap_flag_string("CI CK I2 L2 LI LK PF Q2 R2 SL SZ cl F1 A3 N3 P3 P7 PP PU PW Y2".replace(" ", "")),
    "statüsüz/" + remap_flag_string("CI CK I2 L2 LI LK PF Q2 R2 SL SZ cl F1 A3 N3 P3 P7 PP PU PW Y2".replace(" ", "")),
    "kovuksuz/" + remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SZ Y1".replace(" ", "")),
    "temsilen",
    "sanayiinde",
    "buzdağı/∀∈∍∎∡∧∫∲∶∺∼∽≂≉≋≍≣",
    "buzdağ/∁∅∌∍∎∡∧∩∪∬∳∷∺∾≁≃≉≋≍≎≣",
    "gökcismi/∂∊∍∢∨∭∴∸∻∿≄≆≊≌≤≩",
    "gökcisim/∌∍∖∢∨∩∪∻≊≌≍≎≑≩",
    "fas", "go", "hut", "çad",
    # Chemical element symbols & letter names from TDK:
    "ac", "bi", "ca", "cl", "co", "cu", "ga", "li", "lu", "me", "mn", "mo", "n", "na",
    "ni", "pa", "pu", "ra", "rh", "sc", "u", "v", "y", "ö", "ı", "ın", "ır", "ke", "isa"
]

def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()

def tr_title(s: str) -> str:
    if not s: return s
    if s[0] == 'i': return 'İ' + s[1:]
    if s[0] == 'ı': return 'I' + s[1:]
    return s[0].upper() + s[1:]

def load_lexicons():
    print("Loading authority sets & custom lexicons...")
    tdk_words = set()
    with open(TDK_PATH, encoding="utf-8") as f:
        for line in f:
            w = tr_lower(line.strip().split("/")[0])
            if w: tdk_words.add(w)
            
    dd_words = set()
    with open(DD_PATH, encoding="utf-8") as f:
        for line in f:
            w = tr_lower(line.strip().split("/")[0])
            if w: dd_words.add(w)
            
    custom_abbrevs = set()
    custom_abbrevs_orig = set()
    if CUSTOM_ABBREV_PATH.exists():
        with open(CUSTOM_ABBREV_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                lem = item.get("lemma", "")
                if lem:
                    custom_abbrevs.add(tr_lower(lem))
                    custom_abbrevs_orig.add(lem)
                    
    custom_names = set()
    custom_names_orig = set()
    if CUSTOM_NAMES_PATH.exists():
        with open(CUSTOM_NAMES_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                lem = item.get("lemma", "")
                if lem:
                    custom_names.add(tr_lower(lem))
                    custom_names_orig.add(lem)
                    
    print(f"  TDK: {len(tdk_words):,}, DD: {len(dd_words):,}, Abbrevs: {len(custom_abbrevs):,}, Names: {len(custom_names):,}")
    return tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig

def build_hardened_aff(profile="tdk"):
    print(f"Building hardened .aff file for profile [{profile}]...")
    with open(AFF_SRC, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    hardened_lines = []
    fixed_wildcards = 0
    
    # 1. Parse into header and SFX/PFX blocks to drop dead flags and duplicates
    header_lines = []
    sfx_blocks = {}
    curr_flag = None
    
    for line in lines:
        line_s = line.strip()
        parts = line_s.split()
        
        # Check if starting an SFX/PFX block
        if len(parts) >= 4 and parts[0] in ('SFX', 'PFX') and parts[2] in ('Y', 'N'):
            curr_flag = parts[1]
            if curr_flag not in sfx_blocks:
                sfx_blocks[curr_flag] = []
            sfx_blocks[curr_flag].append(line)
        elif curr_flag is not None and len(parts) >= 2 and parts[0] in ('SFX', 'PFX') and parts[1] == curr_flag:
            # Suffix rule within curr_flag block
            # Safely disable ungrammatical / vowel-violating rules
            if line_s.startswith("SFX ≠") and "emek ebilecek" in line_s:
                if len(parts) >= 5: parts[4] = "X"; line = " ".join(parts) + "\n"
            elif line_s == "SFX ≖ emek enr emek": line = "SFX ≖ emek enr X\n"
            elif line_s == "SFX ≟ umak unr umak": line = "SFX ≟ umak unr X\n"
            elif line_s == "SFX ≟ amak atrsanız amak": line = "SFX ≟ amak atrsanız X\n"
            elif line_s in ("SFX ⊁ mek mesü mek", "SFX ≘ mek mesü mek"): line = line.replace("mek\n", "X\n")
            elif line_s.startswith("SFX ≟") and "masunı" in line_s:
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ≔ mak ıldı"): line = "SFX ≔ mak ıldı [^l]mak\n"
            elif line_s.startswith("SFX ⊂ mak ırm"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊁ mek üre"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s in ("SFX ≓ amak adırıp amak", "SFX ≓ ımak ıdırıp ımak"):
                parts = line_s.split(); parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊃ mek irme/"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif len(parts) >= 4 and "/" in parts[3]:
                clean_add, flags = parts[3].split("/", 1)
                if clean_add.endswith("ğ") and "X" not in flags:
                    parts[3] = f"{clean_add}/X{flags}"
                    line = " ".join(parts) + "\n"
            if len(parts) >= 5:
                clean_add = parts[3].split("/")[0]
                if parts[4] == "." and clean_add and clean_add[0] in vowels:
                    parts[4] = consonant_cond
                    line = " ".join(parts) + "\n"
                    fixed_wildcards += 1
            sfx_blocks[curr_flag].append(line)
        elif curr_flag is not None and (not line_s or line_s.startswith('#')):
            curr_flag = None
            header_lines.append(line)
        elif curr_flag is not None:
            sfx_blocks[curr_flag].append(line)
        else:
            header_lines.append(line)
            
    print(f"  Fixed {fixed_wildcards} wildcard rules in .aff")
    
    # 2. Prune dead flag blocks and deduplicate identical rules per block
    pruned_flags = 0
    dropped_rules = 0
    clean_sfx_blocks = {}
    
    for flag, block in sfx_blocks.items():
        if flag in DEAD_FLAG_CHARS:
            pruned_flags += 1
            dropped_rules += len(block) - 1
            continue
            
        header, rules = block[0], block[1:]
        seen = set()
        kept = []
        flag_long = UTF8_TO_LONG.get(flag, flag)
        for r in rules:
            r_strip = r.strip()
            if r_strip in seen:
                dropped_rules += 1
                continue
            parts_r = r_strip.split()
            if len(parts_r) >= 5:
                cond = parts_r[4]
                if flag_long == 'VH' and cond == 'imek':
                    dropped_rules += 1
                    continue
                elif flag_long == 'VS' and cond == 'ımak':
                    dropped_rules += 1
                    continue
                elif flag_long == 'VL' and cond.endswith('tmak'):
                    dropped_rules += 1
                    continue
            seen.add(r_strip)
            kept.append(r)
            
        parts = header.split()
        if len(parts) >= 4 and parts[2] in ('Y', 'N'):
            parts[3] = str(len(kept))
            header = " ".join(parts) + "\n"
            
        # Consolidate VY (demek + yemek) duplicate rules
        if flag_long == 'VY':
            demek_map = {}
            yemek_map = {}
            other_vy = []
            for r in kept:
                parts_r = r.strip().split()
                if len(parts_r) >= 5:
                    strip, add, cond = parts_r[2], parts_r[3], parts_r[4]
                    if cond == 'demek': demek_map[(strip, add)] = r
                    elif cond == 'yemek': yemek_map[(strip, add)] = r
                    else: other_vy.append(r)
                else: other_vy.append(r)
            common_keys = set(demek_map.keys()) & set(yemek_map.keys())
            consolidated_vy = []
            for k in sorted(common_keys):
                strip, add = k
                consolidated_vy.append(f"SFX {flag} {strip} {add} [dy]emek\n")
            for k, r in demek_map.items():
                if k not in common_keys: consolidated_vy.append(r)
            for k, r in yemek_map.items():
                if k not in common_keys: consolidated_vy.append(r)
            consolidated_vy.extend(other_vy)
            parts = header.split()
            parts[3] = str(len(consolidated_vy))
            header = " ".join(parts) + "\n"
            dropped_rules += len(common_keys)
            kept = consolidated_vy

        clean_sfx_blocks[flag] = [header] + kept
        
    print(f"  Pruned {pruned_flags} dead flag blocks, {dropped_rules:,} total duplicate/dead rules.")
    
    # Reassemble aff content
    aff_text = "".join(header_lines).rstrip() + "\n\n"
    for flag in sorted(clean_sfx_blocks.keys()):
        aff_text += "".join(clean_sfx_blocks[flag]) + "\n"
        
    # Enhanced MAP Matrix
    new_map = """MAP 14
MAP aâAÂ
MAP uûUÛ
MAP uüUÜ
MAP iîİÎ
MAP ıiIİ
MAP oöOÖ
MAP eêEÊ
MAP cçCÇ
MAP gğGĞ
MAP sşSŞ
MAP dtDT
MAP bpBP
MAP vwyVWY
MAP '’‘"""
    aff_text = re.sub(r'MAP \d+\n(?:MAP [^\n]+\n)+', new_map + '\n', aff_text, count=1)
    
    # Extra REP rules: clean any leading "REP " prefixes
    clean_extra = []
    for r in EXTRA_REP_RULES:
        rule_str = r.strip()
        while rule_str.startswith("REP "):
            rule_str = rule_str[4:].strip()
        if rule_str:
            clean_extra.append(rule_str)

    if profile == "dd":
        clean_extra.extend([
            "î i",
            "resmî resmi",
            "askerî askeri",
            "dinî dini",
            "millî milli"
        ])
        
    # Extract only genuine replacement pairs from base aff, ignoring digit counts like "1265"
    base_rep = []
    for m in re.findall(r'^REP\s+(.+)$', aff_text, re.MULTILINE):
        rule_str = m.strip()
        while rule_str.startswith("REP "):
            rule_str = rule_str[4:].strip()
        parts = rule_str.split()
        if len(parts) >= 2 and not (len(parts) == 1 and parts[0].isdigit()):
            base_rep.append(rule_str)

    all_rep = list(dict.fromkeys(clean_extra + base_rep))
    rep_block = f"REP {len(all_rep)}\n" + "\n".join(f"REP {r}" for r in all_rep) + "\n"

    # Remove all existing REP lines and replace cleanly after MAXNGRAMSUGS
    aff_text = re.sub(r'^REP.*$\n?', '', aff_text, flags=re.MULTILINE)
    aff_text = re.sub(r'(MAXNGRAMSUGS \d+\n+)', r'\1' + rep_block + '\n', aff_text, count=1)
    
    return aff_text

def build_sanitized_dic(tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig, profile="tdk"):
    print(f"Sanitizing .dic file for profile [{profile}]...")
    
    unhatted_to_purge = {tr_lower(v) for v in MANDATORY_HATTED_WORDS.values()}
    unhat_map = str.maketrans('âîûÂÎÛ', 'aiuAIU')
    for h in tdk_words:
        if any(c in h for c in 'âîû'):
            u = h.translate(unhat_map)
            if u not in dd_words and u not in tdk_words:
                unhatted_to_purge.add(tr_lower(u))
    print(f"  Unhatted clones targeted for purge: {len(unhatted_to_purge)}")

    all_ref = tdk_words | dd_words
    whitelist = (all_ref - unhatted_to_purge) | custom_abbrevs | custom_names | {tr_lower(c) for c in COMPOUND_SET}
    
    BAD_STEMS = {
        "istasyonu", "televizyonu", "dma", "ce", "hum", "a101",
        "dilerini", "bızız", "islaminin",
        "gorkem", "bahce", "cocuk", "catal", "ornek", "gorevli", "bakici",
        "gorev", "ozet", "bahceci", "goren", "gore", "msde", "cocuklar",
        "calon", "keefe", "jfet",
        "mebs", "ornegi", "ıcad", "icad", "ıkisi", "ikisi", "felaked", "stoğ",
        "topyekun", "alemşümul", "alemşümullük", "ademci", "kai", "klavuz"
    }
    
    with open(DIC_SRC, "r", encoding="utf-8") as f:
        f.readline()
        raw_lines = f.readlines()
        
    clean_entries = []
    seen_heads = set()
    
    removed_permutations = 0
    removed_crawler_spam = 0
    removed_unhatted_dups = 0
    removed_bad_stems = 0
    removed_redundant_upper = 0
    cleaned_common_noun_flags = 0
    
    # Pre-scan lowercase heads present in dictionary
    existing_lower_heads = set()
    for line in raw_lines:
        line_clean = line.strip()
        if line_clean:
            h = line_clean.split("/")[0]
            if h.islower():
                existing_lower_heads.add(h)
                
    for line in raw_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        parts = line_clean.split("/")
        head = parts[0]
        flags = parts[1] if len(parts) > 1 else ""
        head_lower = tr_lower(head)
        
        # 1. Purge known bad stems and bogus voiced virtual stems
        if head_lower in PURGE_VIRTUAL_STEMS or head_lower in ("felaked", "stoğ"):
            removed_bad_stems += 1
            continue
        if head_lower in BAD_STEMS and "X" not in flags and not flags.startswith("X"):
            removed_bad_stems += 1
            continue
            
        # 2. Purge unhatted duplicates for mandatory hatted words
        if head in unhatted_to_purge or head_lower in unhatted_to_purge:
            removed_unhatted_dups += 1
            continue
            
        # 3. Whitelist check (protects all custom abbreviations, custom names, compound terms, TDK/DD)
        is_whitelisted = head_lower in whitelist or head in custom_abbrevs_orig or head in custom_names_orig
        
        if not is_whitelisted:
            # 1-3 letter permutation noise not in whitelist
            if len(head) <= 3 and head.isalpha():
                removed_permutations += 1
                continue
            # Chopped OCR fragments
            if head.isalpha() and re.match(r'^[rlmny][b-df-hj-np-tv-z]', head_lower):
                removed_crawler_spam += 1
                continue
            # Crawler spam / repeated clusters
            if re.search(r'(.)\1\1', head) or re.search(r'^[b-df-hj-np-tv-z]{4,}', head_lower):
                removed_crawler_spam += 1
                continue
            if head.islower() and len(head) >= 4:
                if head_lower.startswith("aa") or head_lower.startswith("bb"):
                    removed_crawler_spam += 1
                    continue
                    
        # 4. Common noun vs proper noun compound separation
        is_compound_term = head_lower in COMPOUND_SET
        proper_flags = "".join(c for c in flags if c in PROPER_SUB_UTF8)
        common_flags = "".join(c for c in flags if c not in PROPER_SUB_UTF8)
        
        if head[0].isupper():
            # Check if this capitalized entry is legitimate:
            # - A custom name (e.g. Arc, AMD, HP, LG, Ahmet, İstanbul)
            # - A custom abbreviation (e.g. AA, ABD, ABS)
            # - A compound term (e.g. Dağ, Göl, Vadi, Ova, Köprü, Saray)
            # - Has KEEPCASE (KC) or proper noun flags
            is_legit_upper = (
                head in custom_names_orig
                or head_lower in custom_names
                or head in custom_abbrevs_orig
                or head_lower in custom_abbrevs
                or is_compound_term
                or "KC" in [UTF8_TO_LONG.get(c) for c in flags]
                or len(head) <= 4
                or bool(proper_flags)
            )
            # If it's merely a capitalized clone of a common noun (e.g. Abajur when abajur exists) with no proper flags -> Drop!
            if not is_legit_upper and head_lower in existing_lower_heads:
                removed_redundant_upper += 1
                continue
        else:
            # Lowercase entry:
            if is_compound_term:
                # Lowercase compound term (dağ, vadi, ova): gets ONLY common flags (no apostrophes!)
                flags = common_flags
                # Also ensure the Capitalized compound head exists with proper flags!
                cap_head = tr_title(head)
                if proper_flags and (cap_head, proper_flags) not in seen_heads:
                    seen_heads.add((cap_head, proper_flags))
                    clean_entries.append(f"{cap_head}/{proper_flags}")
            elif head in custom_abbrevs_orig or head_lower in custom_abbrevs:
                # Keep abbreviation as-is
                pass
            elif head in custom_names_orig or head_lower in custom_names:
                # Keep name as-is
                pass
            else:
                # Ordinary common noun (elma, tornavida): strip all proper noun flags!
                if proper_flags:
                    cleaned_common_noun_flags += 1
                    flags = common_flags
                    
        # Morphological flag overrides for core stems:
        if head_lower in HEAD_FLAG_OVERRIDES:
            flags = HEAD_FLAG_OVERRIDES[head_lower]
        elif head_lower in PALATAL_L_HEADS:
            flags = PALATAL_L_FLAGS
        elif head_lower in ("zehir", "emir"):
            d3_flag = LONG_TO_UTF8.get("D3", "")
            if d3_flag and d3_flag not in flags:
                flags += d3_flag

        # Loanwords ending in 'ing' must take front-vowel noun suffixes
        if head.lower().endswith("ing") and ("≑" in flags or not flags):
            flags = flags.replace("≑", "") + "∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪≎∌∍≍⊘⊙⊚⊛⊜⊝⊞⊟"
            
        if profile == "dd" and "î" in head:
            head = head.replace("î", "i")
            
        if profile == "universal" and "î" in head:
            head_unhatted = head.replace("î", "i")
            entry_unhatted = (head_unhatted, flags)
            if entry_unhatted not in seen_heads:
                seen_heads.add(entry_unhatted)
                clean_entries.append(f"{head_unhatted}/{flags}" if flags else head_unhatted)
                
        if len(head) == 1:
            flags = ""
            
        if head == "boyn":
            flags = flags.replace("≕", "")
        elif head == "boyun":
            flags = flags.replace("∓", "")
            
        entry_key = (head, flags)
        if entry_key in seen_heads:
            continue
        seen_heads.add(entry_key)
        clean_entries.append(f"{head}/{flags}" if flags else head)
        
    print(f"  Removed: {removed_permutations} permutation noises, {removed_crawler_spam} crawler spam, {removed_unhatted_dups} unhatted dups, {removed_bad_stems} bad stems.")
    print(f"  Pruned {removed_redundant_upper:,} redundant capitalized duplicates.")
    print(f"  Cleaned proper-noun apostrophe flags from {cleaned_common_noun_flags:,} ordinary common nouns.")
    
    # 5. Inject legitimate missed words & virtual stems & extra authority headwords
    added_legit = 0
    for w in LEGITIMATE_MISSED_WORDS:
        if profile == "dd" and "î" in w:
            w = w.replace("î", "i")
        head_w = w.split("/")[0]
        fl_w = w.split("/")[1] if "/" in w else ""
        if head_w.lower() in HEAD_FLAG_OVERRIDES and not fl_w:
            fl_w = HEAD_FLAG_OVERRIDES[head_w.lower()]
        entry_w = f"{head_w}/{fl_w}" if fl_w else head_w
        if (head_w, "") not in seen_heads and (head_w.lower(), "") not in seen_heads:
            clean_entries.append(entry_w)
            seen_heads.add((head_w, ""))
            added_legit += 1
            
    for w in VIRTUAL_STEMS + EXTRA_AUTHORITY_HEADWORDS:
        clean_entries.append(w)
        added_legit += 1
            
    # 6. Inject all missing custom abbreviations and names from lexicons
    added_abbrevs = 0
    for a in custom_abbrevs_orig:
        if (a, "") not in seen_heads and (a.lower(), "") not in seen_heads:
            clean_entries.append(a)
            seen_heads.add((a, ""))
            added_abbrevs += 1
            
    added_names = 0
    for n in custom_names_orig:
        if (n, "") not in seen_heads and (n.lower(), "") not in seen_heads:
            clean_entries.append(n)
            seen_heads.add((n, ""))
            added_names += 1
            
    print(f"  Injected: {added_legit} legitimate missed words, {added_abbrevs} missing abbrevs, {added_names} missing names.")
    
    # 7. Deduplicate multi-line heads in .dic
    merged_heads = {}
    for entry in clean_entries:
        parts = entry.split("/", 1)
        h = parts[0]
        fl = parts[1] if len(parts) > 1 else ""
        if h not in merged_heads:
            merged_heads[h] = set(fl)
        else:
            merged_heads[h].update(fl)

    deduped_entries = []
    for h in sorted(merged_heads.keys()):
        fl_set = merged_heads[h]
        fl_combined = "".join(sorted(fl_set))
        deduped_entries.append(f"{h}/{fl_combined}" if fl_combined else h)

    print(f"  Clean entries before dedup: {len(clean_entries):,} -> after dedup: {len(deduped_entries):,}")
    return deduped_entries

def compile_v06_gold():
    tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig = load_lexicons()
    
    profiles = ["tdk", "dd", "universal"]
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    for prof in profiles:
        print(f"\n=======================================================")
        print(f"Compiling Turkspell v0.6 Gold - Profile: [{prof.upper()}]")
        print(f"=======================================================")
        
        prof_dir = DIST_DIR / f"turkspell-v0.6-{prof}"
        prof_dir.mkdir(parents=True, exist_ok=True)
        
        # Build aff
        aff_content = build_hardened_aff(profile=prof)
        aff_out = prof_dir / "tr.aff"
        with open(aff_out, "w", encoding="utf-8") as f:
            f.write(aff_content)
            
        # Build dic
        dic_entries = build_sanitized_dic(
            tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig, profile=prof
        )
        dic_out = prof_dir / "tr.dic"
        with open(dic_out, "w", encoding="utf-8") as f:
            f.write(f"{len(dic_entries)}\n")
            for entry in dic_entries:
                f.write(f"{entry}\n")
                
        print(f"Successfully compiled: {prof_dir / 'tr.aff'} and {prof_dir / 'tr.dic'}")
        
    # Deploy flagship Universal profile to repository root
    print("\nDeploying flagship Turkspell v0.6 Gold (Universal) to repository root (c:\\gemini\\turkspell\\tr.*)...")
    shutil.copy2(DIST_DIR / "turkspell-v0.6-universal" / "tr.aff", TURKSPELL_DIR / "tr.aff")
    shutil.copy2(DIST_DIR / "turkspell-v0.6-universal" / "tr.dic", TURKSPELL_DIR / "tr.dic")
    
    # Deploy to Firefox addon
    addon_dict_dir = TURKSPELL_DIR / "firefox-addon" / "dictionaries"
    if addon_dict_dir.exists():
        shutil.copy2(DIST_DIR / "turkspell-v0.6-universal" / "tr.aff", addon_dict_dir / "tr.aff")
        shutil.copy2(DIST_DIR / "turkspell-v0.6-universal" / "tr.dic", addon_dict_dir / "tr.dic")
        
    print("Deployment complete!")

if __name__ == "__main__":
    compile_v06_gold()
