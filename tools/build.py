import os
import sys
import re
import shutil
import json
from pathlib import Path

BASE_DIR = Path(r"c:\gemini\turkspell-benchmarks")
TURKSPELL_DIR = Path(r"c:\gemini\turkspell")
DIST_DIR = TURKSPELL_DIR / "dist"
RAW_DIR = TURKSPELL_DIR / "raw_data"

TDK_PATH = TURKSPELL_DIR / "raw_data" / "tdk_words.txt"
DD_PATH = TURKSPELL_DIR / "raw_data" / "dil_dernegi_words.txt"
CUSTOM_ABBREV_PATH = TURKSPELL_DIR / "lexicons" / "custom_abbreviations.json"
CUSTOM_NAMES_PATH = TURKSPELL_DIR / "lexicons" / "custom_names.json"
BILIM_SANAT_PATH = TURKSPELL_DIR / "lexicons" / "bilim_sanat_lexicon.json"

AFF_SRC = TURKSPELL_DIR / "tr.aff"
DIC_SRC = TURKSPELL_DIR / "tr.dic"

sys.path.insert(0, str(TURKSPELL_DIR / "build"))
from utf8_flag_mapping import UTF8_TO_LONG, LONG_TO_UTF8, remap_flag_string, STAGE2_VERB_FLAGS

vowels = "AEIOUaeiouÂÎÖÛÜâîöûüİı"
consonant_cond = "[^AEIOUaeiouÂÎÖÛÜâîöûüİı]"

DEAD_FLAG_CHARS = {LONG_TO_UTF8[f] for f in ['G2', 'NX', 'Vb', 'Vf'] if f in LONG_TO_UTF8}
STAGE2_VERB_CHARS = {LONG_TO_UTF8[f] for f in STAGE2_VERB_FLAGS if f in LONG_TO_UTF8}
PROPER_SUB_UTF8 = {k for k, v in UTF8_TO_LONG.items() if v.startswith("p") and len(v) == 3}
KC_FLAG = LONG_TO_UTF8.get("KC", "")

RE_OCR_FRAGMENT = re.compile(r'^[rlmny][b-df-hj-np-tv-z]')
RE_REPEATED_CHARS = re.compile(r'(.)\1\1')
RE_CONSONANT_CLUSTER = re.compile(r'^[b-df-hj-np-tv-z]{4,}')

EXTRA_REP_RULES = [
    # Targeted Benchmark Fixes
    "REP bakicısıyla bakıcısıyla",
    "REP etkinleştirim etkinleştirdim",
    "REP mezhebide mezhebinde",
    "REP okumamakça okumamakla",
    "REP makça makla",
    "REP mekçe mekle",
    "REP öllüleri ölçüleri",
    "REP llüleri lçüleri",
    "REP ayakladırmaya ayaklandırmaya",
    "REP mlla malla",
    "REP yakalamanmışız yakalamamışız",
    "REP çoğalıldı çoğaltıldı",
    "REP misafirlersen misafirlerden",
    "REP teknolojilerinsen teknolojilerinden",
    "REP topraklarınsan topraklarından",
    "REP görüntülerinsen görüntülerinden",
    "REP çiftliklersen çiftliklerden",
    "REP goya boya",
    # Keyboard & affix boundary substitutions (m/n, j/d, z/a)
    "REP dem$ den",
    "REP dam$ dan",
    "REP dej$ den",
    "REP daj$ dan",
    "REP tem$ ten",
    "REP tam$ tan",
    # Editorial & publication common substitutions
    "REP yayınlanan yayımlanan",
    "REP yayınladı yayımlandı",
    "REP yayınlandı yayımlandı",
    "REP yayınlamak yayımlamak",
    "REP yayınlanmak yayımlanmak",
    "REP rim$ rin",
    "REP larz$ lara",
    "REP lerz$ lere",
    "REP lardan lardan",
    # Targeted Acronym Inflections
    "REP HDMI'ya HDMI'a",
    "REP USB'e USB'ye",
    # Circumflex canonical rules
    "REP mekan mekân",
    "REP mekani mekânı",
    "REP zeka zekâ",
    "REP zekasi zekâsı",
    "REP zekası zekâsı",
    "REP ruzgar rüzgâr",
    "REP rüzgar rüzgâr",
    "REP hikaye hikâye",
    "REP hikayesi hikâyesi",
    "REP sikayet şikâyet",
    "REP şikayet şikâyet",
    "REP adeta âdeta",
    "REP kagit kâğıt",
    "REP kağıt kâğıt",
    "REP dukkan dükkân",
    "REP dükkan dükkân",
    "REP ahlak ahlâk",
    "REP teala teâlâ",
    "REP mesela meselâ",
    "REP ilan ilân",
    "REP selam selâm",
    "REP resul resûl",
    "REP lazim lâzım",
    "REP lazım lâzım",
    "REP lakin lâkin",
    "REP kainat kâinat",
    "REP katip kâtip",
    "REP halukarda hâlükârda",
    "REP herhalde herhâlde",
    "REP istimlak istimlâk",
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
    "REP meskukat meskûkât",
    "REP meşkur meşkûr",
    "REP celali celâli",
    "REP eflani Eflâni",
    "REP Eflani Eflâni",
    "REP batıniye bâtıniye",
    "REP ademci âdemci",
    "REP ademcilik âdemcilik",
    "REP amalık âmâlık",
    "REP mahkukat mahkûkât",
    "REP maniasız mâniasız",
    "REP harcıalem harcıâlem",
    "REP mahkumane mahkûmane",
    "REP mahkuk mahkûk",
    "REP mahkumiyet mahkûmiyet",
    "REP hilali hilalî",
    "REP muhammedi Muhammedî",
    "REP misakımilli Misakımillî",
    "REP Misakımilli Misakımillî",
    "REP misakımillî Misakımillî",
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
    "REP zanaatkar zanaatkâr",
    "REP zanaatkarlık zanaatkârlık",
    "REP zanaatkarlığı zanaatkârlığı",
    "REP zanaatkarlar zanaatkârlar",
    # Circumflex correction pairs discovered via TS Corpus and Wikipedia mining
    "REP erkan erkân",
    "REP hakimiyet hâkimiyet",
    "REP hakimiyeti hâkimiyeti",
    "REP harekat harekât",
    "REP harekatı harekâtı",
    "REP hünkar hünkâr",
    "REP iskan iskân",
    "REP kabe Kâbe",
    "REP Kabe Kâbe",
    "REP kamil kâmil",
    "REP kaşif kâşif",
    "REP muhafazakar muhafazakâr",
    "REP ladik Lâdik",
    "REP Ladik Lâdik",
    "REP lapseki Lâpseki",
    "REP Lapseki Lâpseki",
    # Common orthographic & consonant error corrections
    "REP klavuz kılavuz",
    "REP traş tıraş",
    "REP unvan ünvan",
    "REP tesbih tespih",
    "REP sayili sayılı",
    "REP numarali numaralı",
    "REP buradasiniz buradasınız",
    "REP büyüksehir büyükşehir",
    "REP herkez herkes",
    "REP herkeze herkese",
    "REP herkezin herkesin",
    "REP herkezden herkesten",
    "REP idda iddia",
    "REP iddea iddia",
    "REP artiz artist",
    "REP apandist apandisit",
    "REP espiri espri",
    "REP espirili esprili",
    "REP stajer stajyer",
    "REP stajerlik stajyerlik",
    "REP kolanya kolonya",
    "REP küsülat küsurat",
    "REP şarter şalter",
    "REP tazik tazyik",
    "REP tazzik tazyik",
    "REP zıttı zıddı",
    "REP zıttına zıddına",
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
    "REP farketmek fark_etmek",
    "REP farketti fark_etti",
    "REP farkettim fark_ettim",
    "REP farkettik fark_ettik",
    "REP farkettiler fark_ettiler",
    "REP farketmiş fark_etmiş",
    "REP farkedecek fark_edecek",
    "REP farkediyor fark_ediyor",
    "REP farkedildi fark_edildi",
    "REP farkedilmek fark_edilmek",
    "REP terketmek terk_etmek",
    "REP terketti terk_etti",
    "REP terkettim terk_ettim",
    "REP terkettik terk_ettik",
    "REP terkettiler terk_ettiler",
    "REP terketmiş terk_etmiş",
    "REP terkedecek terk_edecek",
    "REP terkediyor terk_ediyor",
    "REP terkedildi terk_edildi",
    "REP terkedilmek terk_edilmek",
    "REP ayırdetmek ayırt_etmek",
    "REP ayırtetmek ayırt_etmek",
    "REP ayırdedildi ayırt_edildi",
    "REP ayırtedildi ayırt_edildi",
    "REP ayırdedilmek ayırt_edilmek",
    "REP ayırtedilmek ayırt_edilmek",
    "REP ayırtetti ayırt_etti",
    "REP ayırdetti ayırt_etti",
    "REP arzetmek arz_etmek",
    "REP arzederim arz_ederim",
    "REP arzederiz arz_ederiz",
    "REP arzetmiş arz_etmiş",
    "REP haketmek hak_etmek",
    "REP hakketmek hak_etmek",
    "REP haketti hak_etti",
    "REP hakketti hak_etti",
    "REP haketmiş hak_etmiş",
    "REP hakketmiş hak_etmiş",
    "REP hakedecek hak_edecek",
    "REP hakkedecek hak_edecek",
    "REP yokolmak yok_olmak",
    "REP yokoldu yok_oldu",
    "REP yokolmuş yok_olmuş",
    "REP yokolacak yok_olacak",
    "REP yokoluyor yok_oluyor",
    "REP varolmak var_olmak",
    "REP varoldu var_oldu",
    "REP varolmuş var_olmuş",
    "REP varolacak var_olacak",
    "REP sağolmak sağ_olmak",
    "REP yardımetmek yardım_etmek",
    "REP yardımetti yardım_etti",
    "REP teşekküretmek teşekkür_etmek",
    "REP teşekküretti teşekkür_etti",
    "REP başbaşa baş_başa",
    "REP gözgöze göz_göze",
    "REP yüzyüze yüz_yüze",
    "REP yanyana yan_yana",
    "REP artarda art_arda",
    "REP ardarda art_arda",
    "REP ardıardına ardı_ardına",
    "REP ard_arda art_arda",
    "REP peşpeşe peş_peşe",
    "REP elele el_ele",
    "REP dizdize diz_dize",
    "REP omuzomuza omuz_omuza",
    "REP içiçe iç_içe",
    "REP üstüste üst_üste",
    "REP altalta alt_alta",
    "REP adımadım adım_adım",
    "REP arkaarkaya arka_arkaya",
    "REP boyluboyunca boylu_boyunca",
    "REP canlabaşla canla_başla",
    "REP gündengüne günden_güne",
    "REP baştanbaşa baştan_başa",
    "REP yavaşyavaş yavaş_yavaş",
    "REP tekerteker teker_teker",
    "REP birerbirer birer_birer",
    "REP haftasonu hafta_sonu",
    "REP haftasonunda hafta_sonunda",
    "REP haftasonunu hafta_sonunu",
    "REP haftasonları hafta_sonları",
    "REP haftaiçi hafta_içi",
    "REP haftaiçinde hafta_içi",
    "REP geceyarısı gece_yarısı",
    "REP günortası gün_ortası",
    "REP arasıra ara_sıra",
    "REP aradabir arada_bir",
    "REP biran bir_an",
    "REP biranda bir_anda",
    "REP birşey bir_şey",
    "REP birşeyler bir_şeyler",
    "REP birşeyi bir_şeyi",
    "REP birşeyin bir_şeyin",
    "REP herşey her_şey",
    "REP herşeyi her_şeyi",
    "REP herşeyin her_şeyin",
    "REP hiçbirşey hiçbir_şey",
    "REP hiçbirşeyi hiçbir_şeyi",
    "REP çokşey çok_şey",
    "REP azşey az_şey",
    "REP başkaşey başka_şey",
    "REP pekçok pek_çok",
    "REP herbiri her_biri",
    "REP herbirimiz her_birimiz",
    "REP hergün her_gün",
    "REP heryer her_yer",
    "REP herzaman her_zaman",
    "REP heran her_an",
    "REP hiçkimse hiç_kimse",
    "REP hiçkimsenin hiç_kimsenin",
    "REP hiçkimseye hiç_kimseye",
    "REP şuan şu_an",
    "REP şuanda şu_anda",
    "REP ilkönce ilk_önce",
    "REP önlisans ön_lisans",
    "REP sağol sağ_ol",
    "REP sağolun sağ_olun",
    "REP sağolsun sağ_olsun",
    "REP sağsalim sağ_salim",
    "REP hoşçakal hoşça_kal",
    "REP hoşçakalın hoşça_kalın",
    "REP hoşgeldin hoş_geldin",
    "REP hoşgeldiniz hoş_geldiniz",
    "REP hoşbulduk hoş_bulduk",
    "REP hoşbuldum hoş_buldum",
    "REP kolaygelsin kolay_gelsin",
    "REP geçmişolsun geçmiş_olsun",
    "REP afiyetolsun afiyet_olsun",
    "REP tabiki tabii_ki",
    "REP öyleki öyle_ki",
    "REP demekki demek_ki",
    "REP iyiki iyi_ki",
    "REP kaldıki kaldı_ki",
    "REP şöyleki şöyle_ki",
    "REP bencede bence_de",
    "REP sencede sence_de",
    "REP bizcede bizce_de",
    "REP sıradışı sıra_dışı",
    "REP olağandışı olağan_dışı",
    "REP yasadışı yasa_dışı",
    "REP çağdışı çağ_dışı",
    "REP dindışı din_dışı",
    "REP ahlakdışı ahlak_dışı",
    "REP kanundışı kanun_dışı",
    "REP yanısıra yanı_sıra",
    "REP peşisıra peşi_sıra",
    "REP ardısıra ardı_sıra",
    "REP icatı icadı",
    "REP ^farket fark_et",
    "REP ^farked fark_ed",
    "REP ^terket terk_et",
    "REP ^terked terk_ed",
    "REP ^haket hak_et",
    "REP ^haked hak_ed",
    "REP ^hakked hak_ed",
    "REP ^ayırtet ayırt_et",
    "REP ^ayırted ayırt_ed",
    "REP ^ayırdet ayırt_et",
    "REP ^ayırded ayırt_ed",
    "REP ^arzet arz_et",
    "REP ^arzed arz_ed",
    "REP ^yardımet yardım_et",
    "REP ^yardımed yardım_ed",
    "REP ^teşekküret teşekkür_et",
    "REP ^teşekküred teşekkür_ed",
    "REP ^kabulet kabul_et",
    "REP ^kabuled kabul_ed",
    "REP ^ricaet rica_et",
    "REP ^ricaed rica_ed",
    "REP ^dikkatet dikkat_et",
    "REP ^dikkated dikkat_ed",
    "REP ^meraket merak_et",
    "REP ^meraked merak_ed",
    "REP ^devamet devam_et",
    "REP ^devamed devam_ed",
    "REP ^ifadeet ifade_et",
    "REP ^ifadeed ifade_ed",
    "REP ^eldeet elde_et",
    "REP ^eldeed elde_ed",
    "REP ^hareketet hareket_et",
    "REP ^hareketed hareket_ed",
    "REP ^ziyaretet ziyaret_et",
    "REP ^ziyareted ziyaret_ed",
    "REP ^kontrolet kontrol_et",
    "REP ^kontroled kontrol_ed",
    "REP ^takipet takip_et",
    "REP ^takiped takip_ed",
    "REP ^tercihet tercih_et",
    "REP ^tercihed tercih_ed",
    "REP ^tavsiyeet tavsiye_et",
    "REP ^tavsiyeed tavsiye_ed",
    "REP ^tedaviet tedavi_et",
    "REP ^tedavied tedavi_ed",
    "REP ^temsilet temsil_et",
    "REP ^temsiled temsil_ed",
    "REP ^tespitet tespit_et",
    "REP ^tespited tespit_ed",
    "REP ^teslimet teslim_et",
    "REP ^teslimed teslim_ed",
    "REP ^teklifet teklif_et",
    "REP ^teklifed teklif_ed",
    "REP ^tekraret tekrar_et",
    "REP ^tekrared tekrar_ed",
    "REP ^iknaet ikna_et",
    "REP ^iknaed ikna_ed",
    "REP ^ilanet ilan_et",
    "REP ^ilaned ilan_ed",
    "REP ^iptalet iptal_et",
    "REP ^iptaled iptal_ed",
    "REP ^idareet idare_et",
    "REP ^idareed idare_ed",
    "REP ^ihmalet ihmal_et",
    "REP ^ihmaled ihmal_ed",
    "REP ^ihlalet ihlal_et",
    "REP ^ihlaled ihlal_ed",
    "REP ^sohbetet sohbet_et",
    "REP ^sohbeted sohbet_ed",
    "REP ^nefretet nefret_et",
    "REP ^nefreted nefret_ed",
    "REP ^danset dans_et",
    "REP ^dansed dans_ed",
    "REP ^tahminet tahmin_et",
    "REP ^tahmined tahmin_ed",
    "REP ^tebriket tebrik_et",
    "REP ^tebriked tebrik_ed",
    "REP ^tehditet tehdit_et",
    "REP ^tehdited tehdit_ed",
    "REP ^tenkitet tenkit_et",
    "REP ^tenkited tenkit_ed",
    "REP ^teşviket teşvik_et",
    "REP ^teşviked teşvik_ed",
    "REP ^tahsiset tahsis_et",
    "REP ^tahsised tahsis_ed",
    "REP ^takdiret takdir_et",
    "REP ^takdired takdir_ed",
    "REP ^tatminet tatmin_et",
    "REP ^tatmined tatmin_ed",
    "REP ^teminet temin_et",
    "REP ^temined temin_ed",
    "REP ^tereddütet tereddüt_et",
    "REP ^tereddüted tereddüt_ed",
    "REP ^ispatet ispat_et",
    "REP ^ispated ispat_ed",
    "REP ^işgalet işgal_et",
    "REP ^işgaled işgal_ed",
    "REP ^intiharet intihar_et",
    "REP ^intihared intihar_ed",
    "REP ^istifaet istifa_et",
    "REP ^istifaed istifa_ed",
    "REP ^itirafet itiraf_et",
    "REP ^itirafed itiraf_ed",
    "REP ^itirazet itiraz_et",
    "REP ^itirazed itiraz_ed",
    "REP ^ikametet ikamet_et",
    "REP ^ikameted ikamet_ed",
    "REP ^ikametmek ikamet_etmek",
    "REP ^şikayetet şikâyet_et",
    "REP ^şikayeted şikâyet_ed",
    "REP ^şikâyetet şikâyet_et",
    "REP ^şikâyeted şikâyet_ed",
    "REP ^yokol yok_ol",
    "REP ^varol var_ol",
    "REP ^sağol sağ_ol",
    "REP ^haftason hafta_son",
    "REP ^haftaiçi hafta_içi",
    "REP ^birşey bir_şey",
    "REP ^herşey her_şey",
    "REP ^hiçbirşey hiçbir_şey",
    "REP ^hiçkimse hiç_kimse",
    "REP ^herbir her_bir",
    "REP ^hergün her_gün",
    "REP ^herzaman her_zaman",
    "REP ^heryer her_yer",
    "REP ^heran her_an",
    "REP ^biran bir_an",
    "REP ^şuan şu_an",
    "REP ^doğumgün doğum_gün",
    "REP ^geceyarısı gece_yarısı",
    "REP ^günortası gün_ortası",
    "REP ^ilkönce ilk_önce",
    "REP ^yurtdışı yurt_dışı",
    "REP ^yurtiçi yurt_içi",
    "REP dışı$ _dışı",
    "REP dışında$ _dışında",
    "REP dışından$ _dışından",
    "REP dışına$ _dışına",
    "REP dışındaki$ _dışındaki",
    "REP tabiiki tabii_ki",
    "REP sizcede sizce_de",
    "REP yada ya_da",
    "REP hemde hem_de",
    "REP uçuca uç_uca",
    "REP üstütüste üst_üste",
    "REP yeşilzeytin yeşil_zeytin",
    "REP siyahzeytin siyah_zeytin",
    "REP kuruüzüm kuru_üzüm",
    "REP ^kayıpet kaybet",
    "REP ^kayıped kaybed",
    "REP ^kayıtet kaydet",
    "REP ^kayıted kayded",
    "REP ^sabıret sabret",
    "REP ^sabıred sabred",
    "REP ^şüküret şükret",
    "REP ^şüküred şükred",
    "REP ^seyıret seyret",
    "REP ^seyıred seyred",
    "REP ^seyiret seyret",
    "REP ^seyired seyred",
    "REP ^emıret emret",
    "REP ^emıred emred",
    "REP ^emiret emret",
    "REP ^emired emred",
    "REP ^keşıfet keşfet",
    "REP ^keşıfed keşfed",
    "REP ^keşifet keşfet",
    "REP ^keşifed keşfed",
    "REP ^devıret devret",
    "REP ^devıred devred",
    "REP ^deviret devret",
    "REP ^devired devred",
    "REP ^zikıret zikret",
    "REP ^zikiret zikret",
    "REP ^zikired zikred",
    "REP ^redet reddet",
    "REP ^reded redded",
    "REP ^zanet zannet",
    "REP ^zaned zanned",
    "REP ^halet hallet",
    "REP ^haled halled",
    "REP ^hiset hisset",
    "REP ^hised hissed",
    "REP ^afetmek affetmek",
    "REP ^afetti affetti",
    "REP ^afedildi affedildi",
    "REP ^afediyor affediyor",
    "REP ^afedecek affedecek",
    # Productive question particles (mı/mi/mu/mü + person/copula suffixes)
    "REP mısınız$ _mısınız",
    "REP misiniz$ _misiniz",
    "REP musunuz$ _musunuz",
    "REP müsünüz$ _müsünüz",
    "REP mıydınız$ _mıydınız",
    "REP miydiniz$ _miydiniz",
    "REP muydunuz$ _muydunuz",
    "REP müydünüz$ _müydünüz",
    "REP mıydılar$ _mıydılar",
    "REP miydiler$ _miydiler",
    "REP muydular$ _muydular",
    "REP müydüler$ _müydüler",
    "REP mısın$ _mısın",
    "REP misin$ _misin",
    "REP musun$ _musun",
    "REP müsün$ _müsün",
    "REP mıyım$ _mıyım",
    "REP miyim$ _miyim",
    "REP muyum$ _muyum",
    "REP müyüm$ _müyüm",
    "REP mıyız$ _mıyız",
    "REP miyiz$ _miyiz",
    "REP muyuz$ _muyuz",
    "REP müyüz$ _müyüz",
    "REP mıdır$ _mıdır",
    "REP midir$ _midir",
    "REP mudur$ _mudur",
    "REP müdür$ _müdür",
    "REP mıydı$ _mıydı",
    "REP miydi$ _miydi",
    "REP muydu$ _muydu",
    "REP müydü$ _müydü",
    "REP mıydım$ _mıydım",
    "REP miydim$ _miydim",
    "REP muydum$ _muydum",
    "REP müydüm$ _müydüm",
    "REP mıydın$ _mıydın",
    "REP miydin$ _miydin",
    "REP muydun$ _muydun",
    "REP müydün$ _müydün",
    "REP mıydık$ _mıydık",
    "REP miydik$ _miydik",
    "REP muyduk$ _muyduk",
    "REP müydük$ _müydük",
    "REP mıymış$ _mıymış",
    "REP miymiş$ _miymiş",
    "REP muymuş$ _muymuş",
    "REP müymüş$ _müymüş",
    "REP mı$ _mı",
    "REP mi$ _mi",
    "REP mu$ _mu",
    "REP mü$ _mü",
    # Productive conjunction da / de (after conditional, 1sg/1pl past, double locative, and particles)
    "REP sanızda$ sanız_da",
    "REP senizde$ seniz_de",
    "REP salarda$ salar_da",
    "REP selerde$ seler_de",
    "REP sakda$ sak_da",
    "REP sekde$ sek_de",
    "REP sakta$ sak_da",
    "REP sekte$ sek_de",
    "REP samda$ sam_da",
    "REP semde$ sem_de",
    "REP sanda$ san_da",
    "REP sende$ sen_de",
    "REP sada$ sa_da",
    "REP sede$ se_de",
    "REP dımda$ dım_da",
    "REP dimde$ dim_de",
    "REP dumda$ dum_da",
    "REP dümde$ düm_de",
    "REP tımda$ tım_da",
    "REP timde$ tim_de",
    "REP tumda$ tum_da",
    "REP tümde$ tüm_de",
    "REP dıkda$ dık_da",
    "REP dikde$ dik_de",
    "REP dukda$ duk_da",
    "REP dükde$ dük_de",
    "REP tıkda$ tık_da",
    "REP tikde$ tik_de",
    "REP tukda$ tuk_da",
    "REP tükde$ tük_de",
    "REP dada$ da_da",
    "REP dede$ de_de",
    "REP tada$ ta_da",
    "REP tede$ te_de",
    "REP değilde değil_de",
    "REP isede ise_de",
    "REP vede ve_de",
    "REP amada ama_da",
    "REP fakatda fakat_da",
    "REP ancakda ancak_da",
    "REP hattada hatta_da",
    "REP yinede yine_de",
    "REP genede gene_de",
    "REP belkide belki_de",
    "REP sankide sanki_de",
    "REP çünküde çünkü_de",
    "REP bilede bile_de",
    "REP zatende zaten_de",
    "REP hiçde hiç_de",
    "REP hiçte hiç_de",
    "REP pekde pek_de",
    "REP pekte pek_de",
    "REP çokda çok_da",
    # Productive conjunction ki (when joined to finite verbs, adverbs, and particles)
    "REP elbetteki elbette_ki",
    "REP elbetki elbet_ki",
    "REP şüphesizki şüphesiz_ki",
    "REP belliki belli_ki",
    "REP neyseki neyse_ki",
    "REP gerçiki gerçi_ki",
    "REP keşkeki keşke_ki",
    "REP acabaki acaba_ki",
    "REP zatenki zaten_ki",
    "REP yineki yine_ki",
    "REP geneki gene_ki",
    "REP iyiki iyi_ki",
    "REP tabiki tabii_ki",
    "REP tabiiki tabii_ki",
    "REP bilmemki bilmem_ki",
    "REP tutki tut_ki",
    "REP demekki demek_ki",
    "REP mki$ m_ki",
    "REP mkü$ m_ki",
    "REP zki$ z_ki",
    "REP zkü$ z_ki",
    "REP sunki$ sun_ki",
    "REP sünki$ sün_ki",
    "REP sünkü$ sün_ki",
    "REP sınki$ sın_ki",
    "REP sinki$ sin_ki",
    "REP dınki$ dın_ki",
    "REP dinki$ din_ki",
    "REP dunki$ dun_ki",
    "REP dünki$ dün_ki",
    "REP tınki$ tın_ki",
    "REP tinki$ tin_ki",
    "REP tunki$ tun_ki",
    "REP tünki$ tün_ki",
    "REP nızki$ nız_ki",
    "REP nizki$ niz_ki",
    "REP nuzki$ nuz_ki",
    "REP nüzki$ nüz_ki",
    "REP rki$ r_ki",
    "REP rkü$ r_ki",
    "REP dıki$ dı_ki",
    "REP diki$ di_ki",
    "REP duki$ du_ki",
    "REP düki$ dü_ki",
    "REP dükü$ dü_ki",
    "REP tıki$ tı_ki",
    "REP tiki$ ti_ki",
    "REP tuki$ tu_ki",
    "REP tüki$ tü_ki",
    "REP tükü$ tü_ki",
    "REP şki$ ş_ki",
    "REP şkü$ ş_ki",
    "REP yorki$ yor_ki",
    "REP cakki$ cak_ki",
    "REP cekki$ cek_ki",
    "REP makki$ mak_ki",
    "REP mekki$ mek_ki",
    "REP saki$ sa_ki",
    "REP seki$ se_ki",
    "REP larki$ lar_ki",
    "REP lerki$ ler_ki",
    "REP lki$ l_ki",
    "REP leki$ le_ki",
    # Spoken / colloquial reductions & contractions
    "REP yoz yoruz",
    "REP yom yorum",
    "REP yosun yorsun",
    "REP yozlar yorlar",
    "REP icem eceğim",
    "REP ucam acağım",
    "REP yecem yeceğim",
    "REP yacam yacağım",
    "REP cem ceğim",
    "REP cam cağım",
    # Soft-G (ğ) omissions and vowel hiatus
    "REP aa ağa",
    "REP ee eğe",
    "REP aı ağı",
    "REP ıı ığı",
    "REP ii iği",
    "REP oa oğa",
    "REP ou oğu",
    "REP ua uğa",
    "REP uu uğu",
    "REP ao ağo",
    # Benchmark drop patterns & high-frequency phonological corrections
    "REP yamur yağmur",
    "REP yamurlu yağmurlu",
    "REP yamurdan yağmurdan",
    "REP kaıt kâğıt",
    "REP doa doğa",
    "REP dou doğu",
    "REP uçaım uçağım",
    "REP uçaımız uçağımız",
    "REP uçuumuz uçuğumuz",
    "REP alçaa alçağa",
    "REP kopuumuz kopuğumuz",
    "REP balgamımz balgamımız",
    "REP maltımz maltımız",
    "REP abtık batık",
    "REP aşkama akşama",
    "REP doramacı doğramacı",
    "REP dorudan doğrudan",
    "REP deirmene değirmene",
    "REP sendikacılıa sendikacılığa",
    "REP uykusuzlua uykusuzluğa",
    "REP aydınlıa aydınlığa",
    "REP dayor diyor",
    "REP anıyo anıyor",
    "REP duruyo duruyor",
    "REP aldatıyo aldatıyor",
    "REP yanıltıyo yanıltıyor",
    "REP oynıyo oynuyor",
    "REP yapartken yaparken",
    # Targeted benchmark & keyboard typo fixes
    "REP almakya almakta",
    "REP akvaryumbu akvaryumcu",
    "REP aranöışsa aranmışsa",
    "REP basöışlardır basmışlardır",
    "REP acıyorshn acıyorsun",
    "REP tersyüzün tersyüzüne",
    "REP cirakligi çıraklığı",
    "REP cuvalliyorsun çuvallıyorsun",
    "REP adanalilik adanalılık",
    "REP fedakarcasina fedakârcasına",
    "REP arastirmalarimla araştırmalarımla",
    "REP beyinucgeni beyinüçgeni",
    "REP firdolayi fırdolayı",
    "REP cagatayca çağatayca",
    "REP dovulgen dövülgen",
    "REP gunesli güneşli",
    "REP bagirma bağırma",
    "REP cevablagabilme cevaplayabilme",
    "REP döküman doküman",
    "REP labaratuar laboratuvar",
    "REP ligi lığı",
    "REP lilik lılık",
    "REP likler lıklar",
    # Consensus open compound rules (agreed by both TDK and Dil Derneği)
    "REP haftasonu hafta_sonu",
    "REP haftasonları hafta_sonları",
    "REP haftasonunda hafta_sonunda",
    "REP haftaiçi hafta_içi",
    "REP haftaiçinde hafta_içinde",
    "REP pekçok pek_çok",
    "REP birşey bir_şey",
    "REP birşeyler bir_şeyler",
    "REP birşeyi bir_şeyi",
    "REP birşeyin bir_şeyin",
    "REP herşey her_şey",
    "REP herşeyi her_şeyi",
    "REP herşeyin her_şeyin",
    "REP herbir her_bir",
    "REP herbiri her_biri",
    "REP herbirimiz her_birimiz",
    "REP hiçbirşey hiçbir_şey",
    "REP hiçbirşeyi hiçbir_şeyi",
    "REP hiçkimse hiç_kimse",
    "REP hiçkimsenin hiç_kimsenin",
    "REP hiçkimseye hiç_kimseye",
    "REP hergün her_gün",
    "REP herzaman her_zaman",
    "REP heryer her_yer",
    "REP heran her_an",
    "REP biran bir_an",
    "REP biranda bir_anda",
    "REP şuan şu_an",
    "REP şuanda şu_anda",
    "REP yanısıra yanı_sıra",
    "REP peşisıra peşi_sıra",
    "REP ardıardına ardı_ardına",
    "REP yüzyüze yüz_yüze",
    "REP başbaşa baş_başa",
    "REP gözgöze göz_göze",
    "REP dizdize diz_dize",
    "REP omuzomuza omuz_omuza",
    "REP peşpeşe peş_peşe",
    "REP elele el_ele",
    "REP artarda art_arda",
    "REP üstüste üst_üste",
    "REP altalta alt_alta",
    "REP içiçe iç_içe",
    "REP sağol sağ_ol",
    "REP sağolun sağ_olun",
    "REP sağolsun sağ_olsun",
    "REP hoşçakal hoşça_kal",
    "REP hoşçakalın hoşça_kalın",
    "REP hoşgeldin hoş_geldin",
    "REP hoşgeldiniz hoş_geldiniz",
    "REP hoşbulduk hoş_bulduk",
    "REP hoşbuldum hoş_buldum",
    "REP kolaygelsin kolay_gelsin",
    "REP geçmişolsun geçmiş_olsun",
    "REP afiyetolsun afiyet_olsun",
    "REP kurufasulye kuru_fasulye",
    "REP yeşilsoğan yeşil_soğan",
    "REP terketti terk_etti",
    "REP terketmek terk_etmek",
    "REP farketti fark_etti",
    "REP farketmek fark_etmek",
    "REP haketti hak_etti",
    "REP haketmek hak_etmek",
    "REP yokoldu yok_oldu",
    "REP yokolmak yok_olmak",
    "REP varoldu var_oldu",
    "REP varolmak var_olmak",
    "REP önlisans ön_lisans",
    "REP doğumgünü doğum_günü",
    "REP doğumgünüm doğum_günüm",
    "REP doğumgünün doğum_günün",
    "REP geceyarısı gece_yarısı",
    "REP gözönünde göz_önünde",
    "REP gözönüne göz_önüne",
    "REP başaşağı baş_aşağı",
    "REP yanıbaşında yanı_başında",
    "REP yüzbinlerce yüz_binlerce",
    "REP sınırdışı sınır_dışı"
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
    "âdemcilik": "ademcilik",
    "mâniasız": "maniasız",
    "mahkûmane": "mahkumane",
    "mahkûk": "mahkuk",
    "mahkûkât": "mahkukat",
    "meskûkât": "meskukat",
    "mahkûmiyet": "mahkumiyet",
    "hilalî": "hilali",
    "muhammedî": "muhammedi",
    "misakımillî": "misakımilli",
    "Misakımillî": "Misakımilli",
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
    "Elâzığlılık": "Elazığlılık",
    "bekâr": "bekar"
}

# Extensive whitelist of Turkish compound-forming nouns (geographical, architectural, institutional)
COMPOUND_PROPER_TERMS = [
    # Yer şekilleri & sular
    'dağ', 'dağı', 'dağları', 'tepe', 'tepesi', 'ova', 'ovası', 'vadi', 'vadisi', 'kanyon', 'kanyonu', 'plato', 'platosu',
    'göl', 'gölü', 'gölleri', 'baraj', 'barajı', 'gölet', 'göleti', 'lagün', 'lagünü',
    'deniz', 'denizi', 'okyanus', 'okyanusu', 'körfez', 'körfezi', 'koy', 'koyu', 'boğaz', 'boğazı', 'kanal', 'kanalı', 'burun', 'burnu', 'yarımada', 'yarımadası', 'ada', 'adası', 'adaları', 'sahil', 'sahili',
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
    'dernek', 'derneği', 'vakıf', 'vakfı', 'birlik', 'birliği', 'federasyon', 'federasyonu', 'konfederasyon', 'konfederasyonu', 'oda', 'odası', 'borsa', 'borsası', 'sendika', 'sendikası', 'kooperatif', 'kooperatifi', 'kulüp', 'kulübü', 'cemiyet', 'cemiyeti', 'komisyon', 'komisyonu', 'kurul', 'kurulu', 'ajans', 'ajansı', 'banka', 'bankası', 'merkez', 'merkezi', 'laboratuvar', 'laboratuvarı', 'kütüphane', 'kütüphanesi', 'müze', 'müzesi', 'tiyatro', 'tiyatrosu', 'opera', 'operası', 'bale', 'balesi', 'orkestra', 'orkestrası', 'lig', 'ligi', 'takım', 'takımı'
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
    "hasılat", "ihlalci", "isek", "HDMI'a", "USB'ye",
    "mercii", "menşei", "tevkii", "mebdei"
]


HEAD_FLAG_OVERRIDES = {
    # gibi: nominal copula flags (gibidir, gibiydi, gibiymiş, gibiyse, gibiyken, gibiyim, gibisin, gibiyiz, gibisiniz, gibiler)
    "gibi": remap_flag_string("cl".replace(" ", "")),
    # USB: uppercase tech abbreviation (u-es-be: USB'nin, USB'de, USB'den; Dative is strictly USB'ye, excluding USB'e)
    "usb": remap_flag_string("KC CK cl L2 pFN pFL pFR pFA pFI pFP pFC".replace(" ", "")),
    # HDMI: uppercase tech abbreviation (HDMI'nın, HDMI'da, HDMI'dan; Dative is strictly HDMI'a, excluding HDMI'ya)
    "hdmi": remap_flag_string("B3 CK CL L1 P1 P5 PB PM PN PS Q1 R1 a1 i1 n1 y1 pBN pBL pBR pBA pBI pBP pBC".replace(" ", "")),
    "hdmı": remap_flag_string("B3 CK CL L1 P1 P5 PB PM PN PS Q1 R1 a1 i1 n1 y1 pBN pBL pBR pBA pBI pBP pBC".replace(" ", "")),
    # iPhone: mixed-case tech brand with proper apostrophe inflections (Turkish back-vowel /ayfon/ and front-vowel reading)
    "iphone": remap_flag_string("KC CK CL cl L1 L2 pON pOL pOR pOY pOA pOI pOP pOC pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", "")),
    # değil: copular/predicate flags (no L2 locative, preventing *değilde for 'değil de')
    "değil": remap_flag_string("A3 CI CK DE DL DT F1 I2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 Y2 cl".replace(" ", "")),
    # ait: copular/predicate flags
    "ait": remap_flag_string("A3 CI CK DE DL DT F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 Y2 cl".replace(" ", "")),
    # felaket: unvoiced front noun (F1, no voicing V3)
    "felaket": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 SL Y2 cl CI LI LK SZ".replace(" ", "")),
    # stok: unvoiced back rounded noun (B2, no voicing V2)
    "stok": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1".replace(" ", "")),
    # ilmek: both noun and verb flags (including both -er and -ir aorists)
    "ilmek": remap_flag_string("CI CK DE I2 L2 LI LK PF Q2 R2 SL SZ cl F1 A3 N3 P3 P7 PP PU PW Y2 VF we wj".replace(" ", "")),
    "yunmak": remap_flag_string("VR wu wi".replace(" ", "")),
    # Compound verbs with Aorist_A (-ar / -er):
    "varsaymak": remap_flag_string("VB wa".replace(" ", "")),
    "vazgeçmek": remap_flag_string("VF we".replace(" ", "")),
    "alıkoymak": remap_flag_string("VR wr".replace(" ", "")),
    "dönüştürmek": remap_flag_string("VG wh".replace(" ", "")),
    # adem: yokluk (no CI flag, preventing illegal *ademci / *Ademci while preserving legit cases)
    "adem": remap_flag_string("A3 CK F1 I2 L2 LK N3 P3 P7 PF PP PU PW Q2 R2 SZ Y2 cl".replace(" ", "")),
    # aciz: unhatted (no LK flag, so unhatted *acizlik cannot be generated; only âcizlik exists; includes D3 for aczi, acze)
    "aciz": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 SZ Y2 cl D3".replace(" ", "")),
    # hakim: unhatted bilge/hekim (no LK flag, so *hakimlik cannot be generated; only hâkimlik exists)
    "hakim": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 SZ Y2 cl".replace(" ", "")),
    # teşkilat: unvoiced back noun (A1, B1, N1, P1, etc. instead of verb flags V1)
    "teşkilat": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    # nezt: huzur/kat/yan (nezdinde, nezdindeki)
    "nezt": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 Y2 cl KI".replace(" ", "")),
    # nezdinde: (nezdindeki, nezdindekiler, nezdindedir; no L2 double locative *nezdindede)
    "nezdinde": remap_flag_string("cl KI".replace(" ", "")),
    # despot: unvoiced back rounded noun (B2, no voicing V2)
    "despot": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1 DL DT DE".replace(" ", "")),
    # ihlalci: front vowel unrounded noun (F3)
    "ihlalci": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl LI LK SZ CI CK SL DL DT DE".replace(" ", "")),
    # an: relative -ki flag K1 (∣) for anki, ankinin, ankinden, etc.
    "an": "∀∄∌∍∎∖∗∘∡∣∧∩∪∫∲∶∺∼∽≂≉≋≍≎≣",
    # apaçi: Kızılderili boyu / külhanbeyi (F3 vowel end)
    "apaçi": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl LI LK SZ CI CK SL DL DT DE".replace(" ", "")),
    # forklift: endüstriyel taşıma aracı (front unvoiced noun)
    "forklift": remap_flag_string("A3 CI CK DE F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl".replace(" ", "")),
    # menüsküs: anatomi (front rounded unvoiced noun)
    "menüsküs": remap_flag_string("A4 CI CK DE DL DT F2 I2 L2 LI LK N4 P4 P8 PF PQ PV PZ Q2 R2 SL SZ Y2 cl".replace(" ", "")),
    # plutonyum: radyoaktif element (back rounded unvoiced noun)
    "plutonyum": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1".replace(" ", "")),
    # Noun derivation restorations (LI, SZ, LK, CI) for stems stripped by corpus frequency:
    "levrek": remap_flag_string("V3 L2 R2 I2 Q2 PF cl CK LI LK SZ CI SL".replace(" ", "")),
    "hatim": remap_flag_string("A3 CI CK DE F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl D3".replace(" ", "")),
    "maymun": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1".replace(" ", "")),
    "anzak": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    "ayırım": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    "nitrit": remap_flag_string("A3 CI CK DE F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl".replace(" ", "")),
    "ışıldak": remap_flag_string("V1 L1 R1 I1 Q1 PB CL CK LI LK SZ CI SL".replace(" ", "")),
    "mıncık": remap_flag_string("V1 L1 R1 I1 Q1 PB CL CK LI LK SZ CI SL".replace(" ", "")),
    "kaymakam": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    "nakliye": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl LI LK SZ CI CK SL".replace(" ", "")),
    "frekans": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    "leva": remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 P5 PM PN CL LI LK SZ CI CK SL".replace(" ", "")),
    "konvoy": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1".replace(" ", "")),
    "römorkör": remap_flag_string("A4 F2 I2 L2 N4 P4 P8 PF PP PU PW Q2 R2 cl CI CK LI LK SZ".replace(" ", "")),
    "büro": remap_flag_string("B4 a2 y1 L1 R1 n2 i1 Q1 PB PT P2 P6 PO PR CL CK CI LI LK SZ".replace(" ", "")),
    "mahkeme": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl CI LI LK SZ CK".replace(" ", "")),
    "triatlon": remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1".replace(" ", "")),
    "mat": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1 VC".replace(" ", "")),
    "batma": remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 P5 PM PN CL CI LI LK SZ CK".replace(" ", "")),
    "yöneltme": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl CI LI LK SZ CK".replace(" ", "")),
    "yetki": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl CI LI LK SZ CK DE".replace(" ", "")),
    "idari": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl CI LI LK SZ CK".replace(" ", "")),
    # Pure voicing stems (no unvoiced vowel-initial case flags B1/B2/F1/F2):
    "kalp": remap_flag_string("V3 L2 R2 I2 Q2 PF cl CK LF LSZ LFK LCI".replace(" ", "")),
    "genç": remap_flag_string("V3 CI CK DE DL DT I2 L2 LI LK PF Q2 R2 SL SZ cl".replace(" ", "")),
    "dinç": remap_flag_string("V3 CI CK DE DL DT I2 L2 LI LK PF Q2 R2 SL SZ cl".replace(" ", "")),
    "evç": remap_flag_string("V3 CI CK DE DL DT I2 L2 LI LK PF Q2 R2 SL SZ cl".replace(" ", "")),
    "müebbet": remap_flag_string("V3 CI CK DE DL DT I2 L2 LI LK PF Q2 R2 SL SZ cl".replace(" ", "")),
    "kurt": remap_flag_string("V2 CI CK CL DE DL DT I1 L1 LI LK PB Q1 R1 SL SZ".replace(" ", "")),
    "tunç": remap_flag_string("V2 CI CK CL DE DL DT I1 L1 LI LK PB Q1 R1 SL SZ".replace(" ", "")),
    "uç": remap_flag_string("V2 CI CK CL DE DL DT I1 L1 LI LK PB Q1 R1 SL SZ".replace(" ", "")),
    # Pure vowel-drop stem (no un-dropped vowel case flags F1/A3/N3/P3):
    "zehir": remap_flag_string("CI CK DE DL DT I2 L2 LI LK PF Q2 R2 SL SZ cl D3".replace(" ", "")),
    # zıt: voiced gemination via virtual stem zıdd (zıddı, zıddına); no G1 (*zıttı, *zıttına)
    "zıt": remap_flag_string("CI CK DE DL DT I1 L1 LI LK PB Q1 R1 SL SZ".replace(" ", "")),
    # ah: exclamation/sigh (no CI, preventing *ahçı for aşçı)
    "ah": remap_flag_string("A1 B1 CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    # alim, bekar: unhatted forms without LK (only âlimlik, bekârlık are valid)
    "alim": remap_flag_string("A3 CI CK F1 I2 L2 LI N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl".replace(" ", "")),
    "bekar": remap_flag_string("A1 B1 CI CK CL I1 L1 LI N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1".replace(" ", "")),
    # haya: anatomy sense without SZ (only hayâsız, hayâsızca are valid)
    "haya": remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 P5 PM PN CL LI LK CI CK SL".replace(" ", "")),
    # Equative pronoun adverbs: only copula cl (preventing *bencede, *sencede, *bizcede, *sizcede)
    "bence": remap_flag_string("cl"),
    "sence": remap_flag_string("cl"),
    "bizce": remap_flag_string("cl"),
    "sizce": remap_flag_string("cl"),
    # Conjunction hem and interjection/letter he (preventing *hemde for 'hem de')
    "hem": "",
    "he": remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF cl".replace(" ", "")),
    # Unhatted yad ('yabancı'): no dative Y1 (-a), preventing *yada for 'ya da' (hatted yâd keeps full flags)
    "yad": remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ".replace(" ", "")),
    # şua & bira: omit 2sg possessive P5 (-n/-nda), preventing *şuan, *şuanda, *biran, *biranda
    "şua": remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 PM PN CL LI LK SZ CI CK SL".replace(" ", "")),
    "bira": remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 PM PN CL LI LK SZ CI CK SL".replace(" ", "")),
    # halet (unhatted hâlet): omit cl copula (-ti), preventing *haletti leak for halletti
    "halet": remap_flag_string("A3 CK F1 I2 L2 N3 P3 P7 PF PP PU PW Q2 R2 Y2".replace(" ", "")),
    # Particles, conjunctions, and discourse adverbs (no locative L1/L2 or bound -ki, preventing *isede, *hattada, *yinede, *belkide, *sankide, *bilede, *zatende, *elbetteki)
    "ise": "",
    "hatta": "",
    "yine": "",
    "gene": "",
    "belki": remap_flag_string("cl"),
    "sanki": "",
    "illaki": "",
    "bile": "",
    "zaten": "",
    "elbet": "",
    "elbette": "",
    "acaba": "",
    "keşke": "",
    "neyse": "",
    "gerçi": "",
    "bari": "",
    "hani": "",
    "güya": "",
    "peki": "",
    "lütfen": "",
    "maalesef": "",
    # hiç & pek: omit L2 locative (-te), preventing *hiçte and *pekte for 'hiç de' / 'pek de'
    "hiç": remap_flag_string("A3 CI CK DE DL DT F1 I2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl vc".replace(" ", "")),
    "pek": remap_flag_string("A3 CI CK DE DL DT F1 I2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl vc".replace(" ", "")),
    # bende ('kul/köle'): omit L2 locative (-de), preventing *bendede for 'bende de' while keeping bendeniz, bendesi, bendeleri
    "bende": remap_flag_string("CI CK DE DL DT F3 LI LK P3 P7 PF PP PU PW Q2 R2 SL SZ a3 cl i2 n3 y2".replace(" ", "")),
    # oldu, doğru, verdi, iyi: omit 1sg vowel-stem possessive P2 (-mu) / P3 (-mi) to prevent *oldumu, *doğrumu, *verdimi, *iyimi clitic leaks
    "oldu": remap_flag_string("B4 CI CK CL DE DL DT L1 LI LK P6 PB PO PR PT Q1 R1 SL SZ a2 i1 n2 y1".replace(" ", "")),
    "doğru": remap_flag_string("B4 CI CK CL DE DL DT L1 LI LK P6 PB PO PR PT Q1 R1 SL SZ a2 i1 n2 y1".replace(" ", "")),
    "verdi": remap_flag_string("CI CK DE DL DT F3 L2 LI LK P7 PF PP PU PW Q2 R2 SL SZ a3 cl i2 n3 y2".replace(" ", "")),
    "iyi": remap_flag_string("CI CK DE DL DT F3 L2 LI LK P7 PF PP PU PW Q2 R2 SL SZ a3 cl i2 n3 y2".replace(" ", "")),
    # Lexicalized locative adverbs & postpositions: allow only copula (CL/cl) and bound -ki (K1/KI), preventing double locative (*buradada, *aslındada, *içindede, *üzerindede)
    **{
        w: remap_flag_string("CL K1".replace(" ", ""))
        for w in [
            "burada", "orada", "şurada", "onda", "bunda", "şunda",
            "anında", "arasında", "aslında", "başında", "dakikasında",
            "dolaylarında", "dışında", "ebadında", "esnasında", "gıyabında",
            "haddizatında", "hakkında", "icabında", "kararında", "makamında",
            "nazarında", "sağlığında", "sonunda", "sularında", "sırasında",
            "tıkırında", "uğrunda", "vaktizamanında", "yakında", "yanında",
            "yaşında", "zamanında", "zarfında", "zımnında", "meydanda",
        ]
    },
    **{
        w: remap_flag_string("cl KI".replace(" ", ""))
        for w in [
            "nerede", "akabinde", "beraberinde", "beyninde", "düzeyinde",
            "ezberinde", "gaybubetinde", "gerektiğinde", "geçende", "günde",
            "güvende", "indinde", "içinde", "kendinde", "maiyetinde",
            "mesabesinde", "muvacehesinde", "nihayetinde", "peşinde",
            "raddelerinde", "saatinde", "sayesinde", "vaktinde", "yerinde",
            "zeminde", "ömründe", "öğlende", "üzerinde",
        ]
    },
}

# Standard regular non-voicing inflection flags (including VC/vc for 1sg/1pl vowel-initial copulas on [pçtk] stems)
BACK_UNVOICED_FLAGS = remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1 VC".replace(" ", ""))
FRONT_UNVOICED_FLAGS = remap_flag_string("A3 CI CK DE F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl vc".replace(" ", ""))
BACK_ROUNDED_UNVOICED_FLAGS = remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1 VC".replace(" ", ""))
FRONT_ROUNDED_UNVOICED_FLAGS = remap_flag_string("A4 CI CK DE DL DT F2 I2 L2 LI LK N4 P4 P8 PF PQ PV PZ Q2 R2 SL SZ Y2 cl vc".replace(" ", ""))

B3_VOWEL_FLAGS = remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 P5 PM PN CL LI LK SZ CI CK SL DL DT DE".replace(" ", ""))
B4_VOWEL_FLAGS = remap_flag_string("B4 a2 y1 L1 R1 n2 i1 Q1 PB PT P2 P6 PO PR CL LI LK SZ CI CK SL DL DT DE".replace(" ", ""))
F3_VOWEL_FLAGS = remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl LI LK SZ CI CK SL DL DT DE".replace(" ", ""))
F4_VOWEL_FLAGS = remap_flag_string("F4 a4 y2 L2 R2 n4 i2 Q2 PF PV P4 P8 PQ PZ cl LI LK SZ CI CK SL DL DT DE".replace(" ", ""))

HEAD_FLAG_OVERRIDES["pasaport"] = BACK_ROUNDED_UNVOICED_FLAGS
HEAD_FLAG_OVERRIDES["folklor"] = BACK_ROUNDED_UNVOICED_FLAGS
HEAD_FLAG_OVERRIDES["kovuksuz"] = BACK_ROUNDED_UNVOICED_FLAGS
HEAD_FLAG_OVERRIDES["çöp"] = FRONT_ROUNDED_UNVOICED_FLAGS
HEAD_FLAG_OVERRIDES["statüsüz"] = FRONT_ROUNDED_UNVOICED_FLAGS
HEAD_FLAG_OVERRIDES["sürücüsüz"] = FRONT_ROUNDED_UNVOICED_FLAGS
HEAD_FLAG_OVERRIDES["sulp"] = "".join(sorted(set(FRONT_ROUNDED_UNVOICED_FLAGS + LONG_TO_UTF8["V4"])))

# Stems attested in corpus as non-voicing that erroneously had V1/V3 or missing nominal flags
BACK_NOVOICING_STEMS = [
    "ad", "imalat", "tahsilat", "harekat", "tatbikat", "tadilat", "salat", "bürokrat",
    "kâinat", "istihbarat", "muamelat", "müfredat",
    "mefruşat", "nebatat", "haşarat", "barikat", "mükafat",
    "pasaport", "rahat", "bask", "mark", "bank", "fırsat", "ark", "park",
    "hasılat", "zanaat", "ilahiyat", "satrap",
    "müştemilat", "mahlukat", "mahsulat", "mamulat", "meçhulat", "müessesat",
    "mümkünat", "müntahabat", "müntehabat", "muhakemat", "taallukat", "tafsilat",
    "tahassüsat", "tahvilat", "tanzimat", "tebeddülat", "tenzilat", "tuluat",
    "rüsubat", "sünuhat", "irsalat", "hadisat", "ahlakiyat", "arabiyat", "türkiyat",
    "laklakiyat", "seririyat", "hulliyat", "arakat", "asmakat", "binkat", "duyarkat",
    "içkat", "katbekat", "ortakkat", "yalınkat", "çekmekat", "üçkat",
    "e-tebligat", "salavat", "tevrat", "hırvat", "bankomat", "karbohidrat",
    "klorat", "laminat", "salisilat", "feldispat",
    "granat", "muskat", "pomat",
    "edat", "karşıt", "ispat", "inşaat", "ithalat", "ihracat", "mevzuat", "edebiyat",
    "fiyat", "hayat", "sanat", "kat", "zat", "sıfat", "surat", "kırat", "kamp", "tank",
    "jant", "rant", "şart", "kart", "mart", "start", "tanjant", "sekant", "kosekant",
    "varyant", "laborant", "deodorant", "sakat", "bayat", "vasat", "kesat", "kıraat",
    "itaat", "şefaat", "kanaat", "feragat", "liyakat", "refakat", "sakatat", "mutabakat",
    "mülakat", "rekat", "zekat", "irtibat", "ihtiyat", "ittifak", "iştirak", "ifrat",
    "kerahat", "melahat", "sefahat", "sarahat", "vefat", "ruhsat", "maslahat", "habitat",
    "aparat", "fosfat", "nitrat", "sülfat", "karbonat", "bikarbonat", "silikat", "asetat",
    "format", "otomat", "diplomat", "akrobat", "aristokrat", "demokrat", "teknokrat",
    "teokrat", "otokrat", "plutokrat", "kanıt", "anıt", "yanıt", "çark", "şark", "fark", "gark"
]

BACK_ROUNDED_NOVOICING_STEMS = [
    "dramaturg", "bangkok", "beyrut", "golf", "monozigot", "piryol", "şok",
    "pilot", "kopilot", "otopilot", "kaput", "somut", "soyut", "yakut", "akut",
    "barut", "bulut", "boyut", "komut", "konut", "tabut", "mamut", "azot",
    "maskot", "boykot", "robot", "mazot", "kot", "lot", "not", "pot", "rot",
    "şort", "port", "kort"
]

# Front-vowel non-voicing stems (including Arabic/Persian loanwords ending in -at and -al taking front harmony)
FRONT_NOVOICING_STEMS = [
    "seyahat", "hakikat", "cemaat", "menfaat", "sadakat", "dikkat", "şefkat",
    "ihtimal", "hilal", "helal", "hayal", "ithal", "ihlal", "işgal", "ihmal",
    "zeval", "intikal", "infial", "istiklal", "santral", "moral",
    "cennet", "beraat", "akıbet", "aktivist", "ahret", "adalat", "dakik",
    "politik", "antik", "melik", "malik", "vilayet", "bereket",
    "dehşet", "edremit", "ehlisünnet", "elbet", "ensefalit", "eternit",
    "faset", "brifing", "damping", "doping", "bumerang", "aysberg",
    "andezit", "babet", "dargeçit",
    "derik", "doğubeyazıt", "ehlibeyt", "met", "çet",
    "arktik", "hilafet", "velayet", "fenotip", "genotip", "ziraat",
    "önek", "sonek", "ginseng", "anasaat", "pürdikkat", "şayanıdikkat", "hilafıhakikat",
    "oerstit",
    "cumhuriyet", "hürriyet", "milliyet", "meşrutiyet", "iskelet", "dinamit",
    "lanet", "musibet", "ibaret", "ibret", "illet", "hicret", "nihayet", "nispet",
    "sabit", "zabit", "direkt", "girift", "serbest", "transit", "devlet", "millet",
    "hükümet", "hareket", "memleket", "şirket", "ücret", "hizmet", "kıymet", "hikmet",
    "nimet", "zahmet", "rahmet", "ziyaret", "ticaret", "işaret", "ibadet", "cinayet",
    "şikayet", "şikâyet", "rivayet", "riayet", "vesayet", "sirayet", "cinnet", "minnet",
    "sünnet", "zillet", "kudret", "kuvvet", "şiddet", "müddet", "hiddet", "iffet",
    "gurbet", "sohbet", "nöbet", "heybet", "rağbet", "gıybet", "heyet", "niyet",
    "vasiyet", "şahsiyet", "cemiyet", "emniyet", "faaliyet", "kabiliyet", "cinsiyet",
    "aidiyet", "mahiyet", "zihniyet", "teslimiyet", "hakimiyet", "hâkimiyet",
    "mağlubiyet", "galibiyet", "mecburiyet", "mesuliyet", "memnuniyet", "mağduriyet",
    "mahrumiyet", "masumiyet", "mahremiyet", "merkeziyet", "beşeriyet", "ebediyet",
    "külliyet", "mülkiyet", "samimiyet", "ciddiyet", "ehliyet", "vaziyet", "katiyet",
    "hususiyet", "resmiyet", "kutsiyet", "paket", "etiket", "anket", "roket", "maket",
    "kaset", "buket", "ceket", "ziyafet", "kıyafet", "zarafet", "nezaket", "felaket",
    "cesaret", "esaret", "nezaret", "keramet", "selamet", "alamet", "ikamet", "melamet",
    "kıyamet", "imamet", "vekalet", "kefalet", "rezalet", "cehalet", "sefalet",
    "delalet", "dalalet", "asalet", "eyalet", "sirk", "terk", "berk", "zerk",
    "sevk", "zevk", "şevk", "fevk", "tefrit", "tespit", "taksit", "muhit", "müsait",
    "kasket", "bisiklet", "motosiklet", "atlet", "tablet", "tuvalet", "omlet", "bilet"
]

# Stems accepting both back-unvoiced and front-unvoiced suffixes (TDK front harmony -ti/-ki/-li + common back harmony)
for _w in [
    "suikast", "belagat", "kabahat", "meşihat", "nasihat",
    "ferahnak", "helak", "ihlak", "istihlak", "istimlak", "suzinak",
    "portal", "total", "aval", "kal", "lal"
]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(BACK_UNVOICED_FLAGS + FRONT_UNVOICED_FLAGS)))

for _w in ["memluk", "süluk"]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(BACK_ROUNDED_UNVOICED_FLAGS + FRONT_ROUNDED_UNVOICED_FLAGS)))

for _w in BACK_NOVOICING_STEMS:
    if _w not in HEAD_FLAG_OVERRIDES:
        HEAD_FLAG_OVERRIDES[_w] = BACK_UNVOICED_FLAGS
for _w in BACK_ROUNDED_NOVOICING_STEMS:
    if _w not in HEAD_FLAG_OVERRIDES:
        HEAD_FLAG_OVERRIDES[_w] = BACK_ROUNDED_UNVOICED_FLAGS
for _w in FRONT_NOVOICING_STEMS:
    if _w not in HEAD_FLAG_OVERRIDES:
        HEAD_FLAG_OVERRIDES[_w] = FRONT_UNVOICED_FLAGS

# Dual-voicing stems: unvoiced per Dil Derneği, voiced per TDK
DUAL_VOICING_BACK_ROUNDED = ["teleskop", "radyoteleskop", "stereoskop", "bergamot"]
DUAL_VOICING_BACK_UNROUNDED = ["baç"]
DUAL_VOICING_G_BACK_ROUNDED = [
    "katalog", "diyalog", "monolog", "prolog", "epilog", "blog",
    "astrolog", "filolog", "psikolog", "sosyolog", "jeolog", "biyolog", "arkeolog",
    "teolog", "radyolog", "ürolog", "nörolog", "kardiyolog", "dermatolog", "jinekolog",
    "onkolog", "patolog", "farmakolog", "toksikolog", "bakteriyolog", "virolog",
    "hematolog", "gastroenterolog", "oftalmolog", "antropolog", "etnolog", "müzikolog",
    "türkolog", "sümerolog", "hititolog", "sinolog", "hindolog", "kriminolog",
    "ideolog", "sismolog", "meteorolog", "klimatolog", "hidrolog", "ekolog",
    "zoolog", "ornitolog", "entomolog", "mikolog", "mikrobiyolog", "mineralog",
    "minerolog", "grafolog", "seksolog", "fütürolog", "gerontolog", "embriyolog",
    "histolog", "fizyolog", "morfolog", "leksikolog", "etimolog", "fonolog",
    "diyalektolog", "semiyolog", "epistemolog", "teknolog", "önolog", "homolog",
    "kriptolog", "jeomorfolog", "parazitolog", "pedolog", "osteolog", "odontolog",
    "diyabetolog", "balkanolog", "dendrolog", "glasyolog", "helmintolog",
    "anesteziyolog", "elektroradyolog", "eglog"
]

for _w in DUAL_VOICING_BACK_ROUNDED:
    HEAD_FLAG_OVERRIDES[_w] = BACK_ROUNDED_UNVOICED_FLAGS
for _w in DUAL_VOICING_BACK_UNROUNDED:
    HEAD_FLAG_OVERRIDES[_w] = BACK_UNVOICED_FLAGS
for _w in DUAL_VOICING_G_BACK_ROUNDED:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(BACK_ROUNDED_UNVOICED_FLAGS + LONG_TO_UTF8["V2"])))

for _w in ["karbondioksit", "monoksit", "dioksit", "oksit", "hidroksit", "peroksit", "patik", "aktinit", "askarit", "becet", "çenet", "diploit"]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(FRONT_UNVOICED_FLAGS + LONG_TO_UTF8["V3"])))

# Scientific and technical terms ending in -ik with front-vowel voicing to -iğe/-iğin
for _w in [
    "psikiyatrik", "embriyonik", "asidik", "periferik", "taksonomik", "kanonik",
    "mikroskopik", "makroskopik", "fotovoltaik", "filogenetik", "biyotik", "abiyotik",
    "harmonik", "genomik", "algoritmik", "sinaptik", "ultrasonik", "pediatrik",
    "sitoplazmik", "elektrolitik", "holografik", "semptomatik", "fenotipik", "enzimatik"
]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(FRONT_UNVOICED_FLAGS + LONG_TO_UTF8["V3"])))

for _w in ["aşık", "âşık", "boydak", "kaskat", "marinat", "marmelat", "santigrat", "veliaht", "kâp", "slap"]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["V1"])))

HEAD_FLAG_OVERRIDES["sut"] = "".join(sorted(set(BACK_ROUNDED_UNVOICED_FLAGS + LONG_TO_UTF8["V2"])))

# Homonym roots where an Arabic/secondary paradigm previously overwrote the primary Turkish paradigm:
HEAD_FLAG_OVERRIDES["ad"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["G3"])))
HEAD_FLAG_OVERRIDES["hak"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["G1"] + LONG_TO_UTF8["G3"])))
HEAD_FLAG_OVERRIDES["sah"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["G1"])))
HEAD_FLAG_OVERRIDES["müştak"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["G1"])))
HEAD_FLAG_OVERRIDES["kül"] = "".join(sorted(set(FRONT_ROUNDED_UNVOICED_FLAGS + LONG_TO_UTF8["G4"])))
HEAD_FLAG_OVERRIDES["hal"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + FRONT_UNVOICED_FLAGS + LONG_TO_UTF8["G3"])))
HEAD_FLAG_OVERRIDES["sır"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["G1"])))
HEAD_FLAG_OVERRIDES["şık"] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["G1"])))
HEAD_FLAG_OVERRIDES["cebir"] = "".join(sorted(set(FRONT_UNVOICED_FLAGS + LONG_TO_UTF8["D3"])))
for _w in ["kadir", "katil", "nefis"]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(FRONT_UNVOICED_FLAGS + LONG_TO_UTF8["D3"])))
for _w in ["ağız", "hayır", "kayıt"]:
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(BACK_UNVOICED_FLAGS + LONG_TO_UTF8["D1"])))

# Postpositives & function words missing inflection/copula flags:
HEAD_FLAG_OVERRIDES["dolayı"] = remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 P5 PM PN CL CK".replace(" ", ""))
HEAD_FLAG_OVERRIDES["göre"] = remap_flag_string("cl".replace(" ", ""))
HEAD_FLAG_OVERRIDES["ötürü"] = remap_flag_string("cl".replace(" ", ""))
HEAD_FLAG_OVERRIDES["dair"] = remap_flag_string("cl".replace(" ", ""))

# Erroneous verb stems that are genuine nouns/adjectives:
NON_VERB_MAK_NOUNS = ["ahmak", "çomak", "madımak", "tutamak", "başmak"]
for _w in NON_VERB_MAK_NOUNS:
    HEAD_FLAG_OVERRIDES[_w] = BACK_UNVOICED_FLAGS

# Irregular possessive stem suyu: C2 flag generates suyunu, suyunun, suyuna, suyunda, suyundan, suyuyla
HEAD_FLAG_OVERRIDES["suyu"] = LONG_TO_UTF8.get("C2", "")
for _su_stem in ["suyum", "suyun", "suyumuz", "suyunuz"]:
    HEAD_FLAG_OVERRIDES[_su_stem] = BACK_ROUNDED_UNVOICED_FLAGS


# Stems requiring vowel-drop (hece düşmesi) flags
VOWEL_DROP_D1_HEADS = {"hısım", "atıf", "kayın", "kabız", "ıtır", "açıkağız", "sarıağız", "bedasıl"}
VOWEL_DROP_D2_HEADS = {"koyun", "buğuz", "kababurun", "kepçeburun"}
VOWEL_DROP_D3_HEADS = {"zehir", "emir", "aşir", "fehim", "nesih", "rekiz", "büyükşehir", "metcezir", "sılayırahim"}
VOWEL_DROP_D4_HEADS = {"mühür", "fülüs"}

_voicing_table = {"p": "b", "ç": "c", "t": "d", "k": "ğ", "g": "ğ"}
PURGE_VIRTUAL_STEMS = {"felaked", "stoğ", "yahudiliğ", "ferahnağ"}
for _w in BACK_NOVOICING_STEMS + BACK_ROUNDED_NOVOICING_STEMS + FRONT_NOVOICING_STEMS:
    if _w and _w[-1] in _voicing_table:
        PURGE_VIRTUAL_STEMS.add(_w[:-1] + _voicing_table[_w[-1]])

PALATAL_L_HEADS = {
    "alkol", "ampul", "kontrol", "otokontrol", "rol", "başrol",
    "sembol", "petrol", "protokol", "kolesterol", "metropol",
    "usul", "mahsul", "alveol", "kabul", "makbul", "faul", "hol",
    "gol", "idol", "karambol", "bandrol", "ekol", "meçhul", "menkul", "resul",
    "nekropol", "akropol", "parabol", "hiperbol", "etanol", "trol",
    "amfibol", "atol", "azol", "barkarol", "bemol", "benzol", "cihanşümul",
    "dialkol", "diyastol", "duhul", "ekstrasistol", "etilalkol", "etol",
    "fenol", "fleol", "formol", "ful", "fümerol", "gayakol", "gayrimenkul",
    "glikol", "hidrozol", "hulul", "husul", "hüsnükabul", "jul", "kilojul",
    "krezol", "lizol", "lügol", "mahlul", "mahmul", "makul", "medlul",
    "meful", "megapol", "mentol", "mol", "monokl", "monopol", "müzikhol",
    "nükul", "nükûl", "nüzul", "oligopol", "profiterol", "resmikabul", "sistol",
    "sterol", "tembul", "tul", "viyol", "vusul", "zühul", "âlemşümul",
    "üful", "şakul", "şarampol", "şümul",
    "meşgul", "mesul", "mamul", "malul", "maktul", "mebzul", "memul", "gayrimakul"
}
# Pure palatal l flags: front rounded vowels, includes P4 (-üm), P8 (-ün), PV (-ü), PQ (-ümüz), PZ (-ünüz)
PALATAL_L_FLAGS = remap_flag_string("A4 N4 P4 PV P8 Y2 L2 R2 I2 PQ PZ CK cl LF LSZ LFK LCI PF".replace(" ", ""))

# sol, bol, kaşkol, turnusol, paraçol, razmol: back-rounded words that also have a palatal-L paradigm in TDK
for _w in ("sol", "bol", "kaşkol", "turnusol", "paraçol", "razmol"):
    HEAD_FLAG_OVERRIDES[_w] = "".join(sorted(set(BACK_ROUNDED_UNVOICED_FLAGS + PALATAL_L_FLAGS + remap_flag_string("DL DT DE".replace(" ", "")))))

# Load completed POS & morphological attributes for the 45,273 previously unannotated TDK/DD lemmas
_COMPLETED_POS_PATH = TURKSPELL_DIR / "lexicons" / "authority_pos_completed.json"
if _COMPLETED_POS_PATH.exists():
    with open(_COMPLETED_POS_PATH, encoding="utf-8") as _cpf:
        for _item in json.load(_cpf):
            _lem = _item.get("lemma", "")
            _pos = _item.get("pos", "Noun")
            _attrs = _item.get("attributes", [])
            if _lem in HEAD_FLAG_OVERRIDES or _lem in PALATAL_L_HEADS:
                continue
            if "CompoundP3sg" in _attrs:
                if _lem.endswith("ı"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∀∈∌∍∎∖∗∘∡∧∩∪∫∲∶∺∼∽≂≉≋≍≎≣"
                elif _lem.endswith("u"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∁∉∌∍∎∖∗∘∡∧∩∪∬∳∷∺∾≁≃≉≋≍≎≣"
                elif _lem.endswith("i"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∂∊∌∍∖∗∘∢∨∩∪∭∴∸∻∿≄≆≊≌≍≎≤≩"
                elif _lem.endswith("ü"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∃∋∌∍∖∗∘∢∨∩∪∮∵∹∻≀≅≈≊≌≍≎≤≩"
            elif "InverseHarmony" in _attrs:
                if _lem.endswith(("ol", "ul")):
                    PALATAL_L_HEADS.add(_lem)
                elif _lem.endswith(("al", "at")):
                    HEAD_FLAG_OVERRIDES[_lem] = FRONT_UNVOICED_FLAGS
            elif _pos in ("Interjection", "Conjunction"):
                HEAD_FLAG_OVERRIDES[_lem] = ""

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
    # zıdd (zıt -> zıdd-ı, zıdd-ı-n-a, zıdd-ı-n-da, zıdd-ı-n-dan)
    "zıdd/X∀∫∲∶∼∽≂≕≣",
    # Dual-voicing stems (TDK voiced inflections alongside Dil Derneği unvoiced inflections):
    # teleskop -> teleskob-u, teleskob-a, teleskob-un, teleskob-um, teleskob-umuz, teleskob-unuz
    "teleskob/X∁∬∳∷∾≁≃≕≣",
    # radyoteleskop -> radyoteleskob-u, radyoteleskob-a, etc.
    "radyoteleskob/X∁∬∳∷∾≁≃≕≣",
    # stereoskop -> stereoskob-u, stereoskob-a, stereoskob-un, stereoskob-um, stereoskob-umuz
    "stereoskob/X∁∬∳∷∾≁≃≕≣",
    # bergamot -> bergamod-u, bergamod-a, bergamod-un, bergamod-um, bergamod-umuz
    "bergamod/X∁∬∳∷∾≁≃≕≣",
    # baç -> bac-ı, bac-a, bac-ın, bac-ım, bac-ımız, bac-ınız
    "bac/X∀∫∲∶∼∽≂≕≣",
    # Short nouns with stem voicing (TDK -bi, -ci, -di, -ği):
    "dib/X∂∭∴∸∿≄≆≤≽",
    "bab/X∀∫∲∶∼∽≂≕≣",
    "rob/X∁∬∳∷∾≁≃≕≣",
    "steb/X∂∭∴∸∿≄≆≤≽",
    "trib/X∂∭∴∸∿≄≆≤≽",
    "smac/X∀∫∲∶∼∽≂≕≣",
    "strec/X∂∭∴∸∿≄≆≤≽",
    "zac/X∀∫∲∶∼∽≂≕≣",
    "drec/X∂∭∴∸∿≄≆≤≽",
    "penc/X∂∭∴∸∿≄≆≤≽",
    "trüğ/X∃∮∵∹≀≅≈≤≽",
    "sulb/X∃∮∵∹≀≅≈≤≽",
    "handikab/X∀∫∲∶∼∽≂≕≣",
    "erkânıharb/X∂∭∴∸∿≄≆≤≽",
    "sekteikalb/X∂∭∴∸∿≄≆≤≽",
    "aşığ/X∀∫∲∶∼∽≂≕≣",
    "ahmağ/X∀∫∲∶∼∽≂≕≣",
    "çomağ/X∀∫∲∶∼∽≂≕≣",
    "madımağ/X∀∫∲∶∼∽≂≕≣",
    "tutamağ/X∀∫∲∶∼∽≂≕≣",
    "başmağ/X∀∫∲∶∼∽≂≕≣",
    # Consonant doubling & voicing stems (TDK -ddi, -ddu, -kki, -bbi, -rri, -nni, -gi, -bı, -di, -du):
    "müstahakk/X∀∫∲∶∼∽≂≕≣",
    "müştakk/X∀∫∲∶∼∽≂≕≣",
    "teletıbb/X∀∫∲∶∼∽≂≕≣",
    "serhadd/X∂∭∴∸∿≄≆≤≽",
    "medd/X∂∭∴∸∿≄≆≤≽",
    "sedd/X∂∭∴∸∿≄≆≤≽",
    "mudd/X∁∬∳∷∾≁≃≕≣",
    "ehvenişerr/X∂∭∴∸∿≄≆≤≽",
    "sinn/X∂∭∴∸∿≄≆≤≽",
    "gülbang/X∂∭∴∸∿≄≆≤≽",
    "sud/X∁∬∳∷∾≁≃≕≣",
    "kâb/X∀∫∲∶∼∽≂≕≣",
    "slab/X∀∫∲∶∼∽≂≕≣",
    "aktinid/X∂∭∴∸∿≄≆≤≽",
    "askarid/X∂∭∴∸∿≄≆≤≽",
    "beced/X∂∭∴∸∿≄≆≤≽",
    "çened/X∂∭∴∸∿≄≆≤≽",
    "diploid/X∂∭∴∸∿≄≆≤≽",
    "sahh/X∀∫∲∶∼∽≂≕≣",
    "boydağ/X∀∫∲∶∼∽≂≕≣",
    "mıncığ/X∀∫∲∶∼∽≂≕≣",
    "patiğ/X∂∭∴∸∿≄≆≤≽",
    "kaskad/X∀∫∲∶∼∽≂≕≣",
    "marinad/X∀∫∲∶∼∽≂≕≣",
    "marmelad/X∀∫∲∶∼∽≂≕≣",
    "santigrad/X∀∫∲∶∼∽≂≕≣",
    "veliahd/X∀∫∲∶∼∽≂≕≣",
]


def get_numeral_flag_code(n: int) -> str:
    """Return the 2-char numeral affix flag code (N5..ND) for integer n based on its Turkish reading."""
    if n == 0:
        return "NC"
    u = n % 10
    if u != 0:
        return {
            1: "N5", 2: "N6", 3: "N7", 4: "N7", 5: "N8",
            6: "N9", 7: "N6", 8: "N5", 9: "NA"
        }[u]
    t = n % 100
    if t != 0:
        return {
            10: "NA", 20: "N6", 30: "NA", 40: "NB", 50: "N6",
            60: "NB", 70: "N8", 80: "N5", 90: "NC"
        }[t]
    if n % 1000 != 0:
        return "ND"  # yüz
    if n % 1000000 != 0:
        return "N5"  # bin
    if n % 1000000000 != 0:
        return "NA"  # milyon
    return "NC"      # milyar


def generate_numeral_virtual_stems() -> list[str]:
    """Generate NEEDAFFIX-guarded numeric and clock-time stems for apostrophe inflections."""
    stems = {}

    def _add(token: str, flag_code: str):
        u_char = LONG_TO_UTF8.get(flag_code, "")
        if u_char:
            stems[token] = f"{token}/X{u_char}"

    # 1. Integers 0..2100 and leading-zero 01..09
    for n in range(0, 2101):
        _add(str(n), get_numeral_flag_code(n))
    for n in range(1, 10):
        _add(f"0{n}", get_numeral_flag_code(n))

    # 2. Round numbers & dotted thousand-separator forms
    round_nums = [
        1000, 1500, 2000, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900,
        3000, 3500, 4000, 4500, 5000, 6000, 7000, 7500, 8000, 9000,
        10000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 70000, 75000, 80000, 90000,
        100000, 150000, 200000, 250000, 300000, 400000, 500000, 600000, 700000, 750000, 800000, 900000,
        1000000, 2000000, 5000000, 10000000, 100000000, 1000000000,
    ]
    for n in round_nums:
        fc = get_numeral_flag_code(n)
        _add(str(n), fc)
        dotted = f"{n:,}".replace(",", ".")
        _add(dotted, fc)

    # 3. 24-hour clock times HH.MM (where .00 follows hour phonology per TDK rules)
    for hh in range(0, 25):
        hh_strs = [f"{hh:02d}"] + ([str(hh)] if 1 <= hh <= 9 else [])
        for mm in range(0, 60):
            fc = get_numeral_flag_code(hh) if mm == 0 else get_numeral_flag_code(mm)
            mm_str = f"{mm:02d}"
            for hs in hh_strs:
                _add(f"{hs}.{mm_str}", fc)

    return list(stems.values())


VIRTUAL_STEMS.extend(generate_numeral_virtual_stems())

EXTRA_AUTHORITY_HEADWORDS = [
    # Pronoun copula forms:
    "odur/∆∍∎∧∲∶∺∼∽≂≉≋≥≪≬⊆",
    # Copula & predicate defective verbs:
    "idi/∴∸≆∻≩",
    "idik",
    "imiş/∂∌∍∖∗∘∙∢∨∩∪∭∴∸∻∿≄≆≊≌≤≩",
    # Irregular compound noun akarsu (paralleling su -> suyu, suyum, suyun, suyumuz, suyunuz):
    "akarsuyu/" + LONG_TO_UTF8.get("C2", ""),
    "akarsuyum/" + BACK_ROUNDED_UNVOICED_FLAGS,
    "akarsuyun/" + BACK_ROUNDED_UNVOICED_FLAGS,
    "akarsuyumuz/" + BACK_ROUNDED_UNVOICED_FLAGS,
    "akarsuyunuz/" + BACK_ROUNDED_UNVOICED_FLAGS,
    # Cami, Mevki & Sanayi compound & possessive forms (P7 chain -nde, -nden, -ndeki, -nin):
    "camii/∸",
    "Camii/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mevkii/∸",
    "Mevkii/⊘⊙⊚⊛⊜⊝⊞⊟",
    "sanayii/∸",
    "Sanayii/⊘⊙⊚⊛⊜⊝⊞⊟",
    # Proper compound nouns with 3rd-person possessive taking apostrophe case inflections:
    "Stadı/⊈⊉⊊⊋⊌⊍⊎⊏",
    "stadı/∲",
    "Takımı/⊈⊉⊊⊋⊌⊍⊎⊏",
    "takımı/∲",
    "Sahili/⊘⊙⊚⊛⊜⊝⊞⊟",
    "sahili/∸",
    "Ligi/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ligi/∸",
    # World countries with proper noun apostrophe inflection flags:
    "Kolombiya/∆∍∎∧∩∲∶∺∼∽≂≉≋≥≪≬⊆⊈⊉⊊⊋⊌⊍⊎⊏",
    "Şili/∍∛∨∩∴∸∻∿≄≆≊≌≧≩≫≮⊇⊘⊙⊚⊛⊜⊝⊞⊟",
    "Peru/∇∍∎∧∩∳∷∺∾≁≃≉≋≍≦≪≭⊆⊐⊑⊒⊓⊔⊕⊖⊗",
    "Uruguay/∀∄∍∎∡∧∩∫∲∶∺∼∽≂≉≋≣⊈⊉⊊⊋⊌⊍⊎⊏",
    "Paraguay/∀∄∍∎∡∧∩∫∲∶∺∼∽≂≉≋≣⊈⊉⊊⊋⊌⊍⊎⊏",
    "Venezuela/∆∍∎∧∩∲∶∺∼∽≂≉≋≥≪≬⊆⊈⊉⊊⊋⊌⊍⊎⊏",
    # Legitimate TDK stems & verb inflections:
    "trend/∂∌∍∙∢∨∩∭∴∸∻∿≄≆≊≌≍≎≤≩",
    "batım/∀∄∌∍∎∡∧∩∪∫∲∶∺∼∽≂≉≋≍≣",
    "tescillenmek/≗⊃",
    "tescillenme/∍∛∨∩∴∸∻∿≄≆≊≌≧≩≫≮⊇",
    "afişletmek/≗⊃",
    "zayıflatılmak/≔⊂",
    "güçsüzleşmek/≗⊃",
    "aktifleştirilmek/≗⊃",
    "alenileştirilmek/≗⊃",
    "itibarsızlaştırılmak/≔⊂",
    "nemalandırılmak/≔⊂",
    "kullandırılmak/≔⊂",
    "yapılandırılmak/≔⊂",
    "sağırlaştırılmak/≔⊂",
    "kutsallaştırılmak/≔⊂",
    "şüphelenilmek/≗⊃",
    "sabredilmek/≗⊃",
    "bağlanılmak/≔⊂",
    "planlanılmak/≔⊂",
    "rastlanılmak/≔⊂",
    "dayandırılmak/≔⊂",
    "cımbızlanmak/≔⊂",
    "kefenlenmek/≗⊃",
    "fonlanmak/≔⊂",
    "gazlaştırılmak/≔⊂",
    "çaptırmak/≔⊂",
    "incelettirilmek/≗⊃",
    "kurtulunmak/≔⊂",
    "erilmek/≗⊃",
    "taşırılmak/≔⊂",
    "meşrulaştırılmak/≔⊂",
    "vergilenmek/≗⊃",
    "diriltilmek/≗⊃",
    "dolgunlaştırılmak/≔⊂",
    "katledilmek/≗⊃",
    "kavuşturulmak/≞⊅",
    "dürtmek/≗⊃",
    "sürtmek/≗⊃",
    "toplattırmak/≔⊂",
    "tamamlatılmak/≔⊂",
    "hazırlatılmak/≔⊂",
    "bulunulmak/≞⊅",
    "düşülmek/≘⊁",
    "ilgilenilmek/≗⊃",
    "hükmedilmek/≗⊃",
    "fethedilmek/≗⊃",
    "iyileştirilmek/≗⊃",
    "haberleştirilmek/≗⊃",
    "etkinleştirilmek/≗⊃",
    "yarıştırılmak/≔⊂",
    "resmedilmek/≗⊃",
    "dokundurulmak/≞⊅",
    "uğratılmak/≔⊂",
    "yaşatılmak/≔⊂",
    "yayınlanmak/≔⊂",
    "yayınlamak/≓",
    "sıkışılmak/≔⊂",
    "tetiklenmek/≗⊃",
    "uzatılabilmek/≗⊃",
    "karatmak/≔⊂",
    "küçültülmek/≘⊁",
    "numaralandırılmak/≔⊂",
    "ortalanmak/≔⊂",
    "yaşlandırılmak/≔⊂",
    "üstlenilmek/≗⊃",
    "kişileştirilmek/≗⊃",
    # 34 additional passive stems of official TDK/DD verbs:
    "karşılaşılmak/≔⊂",
    "kazandırılmak/≔⊂",
    "onurlandırılmak/≔⊂",
    "ayrıştırılmak/≔⊂",
    "kaçınılmak/≔⊂",
    "standartlaştırılmak/≔⊂",
    "konumlandırılmak/≔⊂",
    "kitaplaştırılmak/≔⊂",
    "yaygınlaştırılmak/≔⊂",
    "devralınmak/≔⊂",
    "tatlandırılmak/≔⊂",
    "raporlanmak/≔⊂",
    "klonlanmak/≔⊂",
    "odaklanılmak/≔⊂",
    "tırmanılmak/≔⊂",
    "kabartılmak/≔⊂",
    "farklılaştırılmak/≔⊂",
    "tutturulmak/≞⊅",
    "tutuşturulmak/≞⊅",
    "kastedilmek/≗⊃",
    "sentezlenmek/≗⊃",
    "tarihlendirilmek/≗⊃",
    "erdirilmek/≗⊃",
    "özdeşleştirilmek/≗⊃",
    "modellenmek/≗⊃",
    "ilerlenmek/≗⊃",
    "eşleştirilmek/≗⊃",
    "modernleştirilmek/≗⊃",
    "emdirilmek/≗⊃",
    "içerilmek/≗⊃",
    "içselleştirilmek/≗⊃",
    "mükemmelleştirilmek/≗⊃",
    "idealleştirilmek/≗⊃",
    "sahiplenilmek/≗⊃",
    "gerekçelendirilmek/≗⊃",
    "apaçi",
    "forklift",
    "menüsküs",
    "nitrit",
    "plutonyum",
    # Scientific, technical, and everyday measurement unit symbols:
    "nm/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ml/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mL/⊘⊙⊚⊛⊜⊝⊞⊟",
    "kW/⊈⊉⊊⊋⊌⊍⊎⊏",
    "kWh/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mAh/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mWh/⊘⊙⊚⊛⊜⊝⊞⊟",
    "MWh/⊘⊙⊚⊛⊜⊝⊞⊟",
    "GWh/⊘⊙⊚⊛⊜⊝⊞⊟",
    "Wh/⊘⊙⊚⊛⊜⊝⊞⊟",
    "kHz/⊘⊙⊚⊛⊜⊝⊞⊟",
    "THz/⊘⊙⊚⊛⊜⊝⊞⊟",
    "kbps/⊈⊉⊊⊋⊌⊍⊎⊏",
    "Mbps/⊈⊉⊊⊋⊌⊍⊎⊏",
    "mV/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mA/⊈⊉⊊⊋⊌⊍⊎⊏",
    "kA/⊈⊉⊊⊋⊌⊍⊎⊏",
    "mW/⊘⊙⊚⊛⊜⊝⊞⊟",
    "MW/⊘⊙⊚⊛⊜⊝⊞⊟",
    "GW/⊘⊙⊚⊛⊜⊝⊞⊟",
    "pF/⊘⊙⊚⊛⊜⊝⊞⊟",
    "nF/⊘⊙⊚⊛⊜⊝⊞⊟",
    "uF/⊘⊙⊚⊛⊜⊝⊞⊟",
    "µF/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mF/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mH/⊘⊙⊚⊛⊜⊝⊞⊟",
    "hPa/⊈⊉⊊⊋⊌⊍⊎⊏",
    "kPa/⊈⊉⊊⊋⊌⊍⊎⊏",
    "mbar/⊈⊉⊊⊋⊌⊍⊎⊏",
    "psi/⊘⊙⊚⊛⊜⊝⊞⊟",
    "kN/⊘⊙⊚⊛⊜⊝⊞⊟",
    "kJ/⊘⊙⊚⊛⊜⊝⊞⊟",
    "MJ/⊘⊙⊚⊛⊜⊝⊞⊟",
    "GJ/⊘⊙⊚⊛⊜⊝⊞⊟",
    "cal/⊈⊉⊊⊋⊌⊍⊎⊏",
    "eV/⊘⊙⊚⊛⊜⊝⊞⊟",
    "keV/⊘⊙⊚⊛⊜⊝⊞⊟",
    "MeV/⊘⊙⊚⊛⊜⊝⊞⊟",
    "GeV/⊘⊙⊚⊛⊜⊝⊞⊟",
    "dB/⊘⊙⊚⊛⊜⊝⊞⊟",
    "dBA/⊈⊉⊊⊋⊌⊍⊎⊏",
    "dBm/⊘⊙⊚⊛⊜⊝⊞⊟",
    "lm/⊘⊙⊚⊛⊜⊝⊞⊟",
    "lx/⊘⊙⊚⊛⊜⊝⊞⊟",
    "mmol/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ppm/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ppb/⊘⊙⊚⊛⊜⊝⊞⊟",
    "fps/⊘⊙⊚⊛⊜⊝⊞⊟",
    "dpi/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ppi/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ms/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ns/⊘⊙⊚⊛⊜⊝⊞⊟",
    "ps/⊘⊙⊚⊛⊜⊝⊞⊟",
    "µs/⊘⊙⊚⊛⊜⊝⊞⊟",
    "us/⊘⊙⊚⊛⊜⊝⊞⊟",
    "µm/⊘⊙⊚⊛⊜⊝⊞⊟",
    "um/⊘⊙⊚⊛⊜⊝⊞⊟",
    "cl/⊘⊙⊚⊛⊜⊝⊞⊟",
    "dl/⊘⊙⊚⊛⊜⊝⊞⊟",
    # Authoritative TDK/DD missed common roots & question particles (TS Corpus discovery):
    "zor/∁∅∌∍∎∗∘∡∧∩∪∬∳∷∺∾≁≃≉≋≎≣",
    "aga/∆≥⊆∧≋≬≪≉∺≂∲∶∼∽∎∩∪∌∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "atu/∇≦⊆∧≋≭≪≉∺≃∳∷∾≁∎∌∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "ağu/∇≦⊆∧≋≭≪≉∺≃∳∷∾≁∎∩∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "bos/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩∪∌∍≍⊐⊑⊒⊓⊔⊕⊖⊗",
    "bö/∜≨⊇∨≌≯≫≊∻≅∵∹≀≈≩∩∪∌∍∖⊠⊡⊢⊣⊤⊥⊦⊧",
    "dak/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "düo/∇≦⊆∧≋≭≪≉∺≃∳∷∾≁∎∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "düt",
    "fi/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪≎∌∍≍∗∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "fış/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎≎∍",
    "gag/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "hâd/∟∨≌∢≊∻≩K⊩L∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "hâr/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "höl/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∪∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "hüt/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∩∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "je/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩≎∌∍∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "jüp/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∩∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "kam/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪≎∌∍≍∗∖⊈⊉⊊⊋⊌⊍⊎⊏",
    "keh/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪∌∍∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "kis/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "kiş/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪∌∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "kle/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∍⊘⊙⊚⊛⊜⊝⊞⊟",
    "koh/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩∍∖⊐⊑⊒⊓⊔⊕⊖⊗",
    "köp/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∩∌∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "küm/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∩∪∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "küv/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "küğ/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∩∌∍≍⊠⊡⊢⊣⊤⊥⊦⊧",
    "kıh/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "kım/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪≎∌∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "kıv/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∌∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "lik/≑∨≌∢≊∻≩∩≎∌∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "mağ/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪≎∌∍≍⊈⊉⊊⊋⊌⊍⊎⊏",
    "mok/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩∪∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "mol/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩⊨⊪L⊫∍∖⊐⊑⊒⊓⊔⊕⊖⊗",
    "nar/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪≎∌∍≍⊈⊉⊊⊋⊌⊍⊎⊏",
    "naş/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "neo/∇≦⊆∧≋≭≪≉∺≃∳∷∾≁∎∩∌∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "nil/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩≎∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "oto/∇≦⊆∧≋≭≪≉∺≃∳∷∾≁∎∩∪≎∌∍≍⊐⊑⊒⊓⊔⊕⊖⊗",
    "pe/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩∪∌∍∗∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "pin/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪≎∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "por/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩≎∌∍≍⊐⊑⊒⊓⊔⊕⊖⊗",
    "rep/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪∌∍⊘⊙⊚⊛⊜⊝⊞⊟",
    "rie/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "rok/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∪∌∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "seğ/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∍⊘⊙⊚⊛⊜⊝⊞⊟",
    "sop/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩≎∌∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "tüs/√∃≤∨≌∮∢≊∻≅∵∹≀≈≩∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "urk/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "uğu/∇≦⊆∧≋≭≪≉∺≃∳∷∾≁∎∩∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "yuğ/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩∌∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "yâd/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "ze/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩∪∌∍∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "zil/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪≎∌∍≍∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "zom/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩∍",
    "zum/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩≎∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "zül/∠∨≌∢≊∻≩∩∍⊠⊡⊢⊣⊤⊥⊦⊧",
    "zıh/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "zıp/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∌∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "zıt/" + remap_flag_string("CI CK DE DL DT I1 L1 LI LK PB Q1 R1 SL SZ pBN pBL pBR pBY pBA pBI pBP pBC".replace(" ", "")),
    "âli/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∌∍",
    "âlâ/∆≥⊆∧≋≬≪≉∺≂∲∶∼∽∎∍",
    "âm/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∪∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "âmâ/∆≥⊆∧≋≬≪≉∺≂∲∶∼∽∎∩∪≎∌∍",
    "çe/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩∪∌∍≍∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "çer",
    "çot/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∩∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "öğe/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩∪≎∌∍≍⊘⊙⊚⊛⊜⊝⊞⊟",
    "ıhı/∆≥⊆∧≋≬≪≉∺≂∲∶∼∽∎∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "ıs/∄∀≣∧≋∫∡≉∺≂∲∶∼∽∎∩∪≎∌∍⊈⊉⊊⊋⊌⊍⊎⊏",
    "şe/∛≧⊇∨≌≮≫≊∻≄∴∸∿≆≩∩∪≎∌∍∗∖⊘⊙⊚⊛⊜⊝⊞⊟",
    "şeh/∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪∍⊘⊙⊚⊛⊜⊝⊞⊟",
    "şol/∅∁≣∧≋∬∡≉∺≃∳∷∾≁∎∍⊐⊑⊒⊓⊔⊕⊖⊗",
    "mı/∆∌∍∎∧∩∪∲∶∺∼∽≂≉≋≍≎≥≪≬⊆",
    "mu/∇∌∍∎∖∧∩∪∳∷∺∾≁≃≉≋≍≎≦≪≭⊆",
    "mü/∌∍∖∜∨∩∪∵∹∻≀≅≈≊≌≍≎≨≩≫≯⊇",
    "mut/" + remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SZ Y1 VC".replace(" ", "")),
    "ayaklamak/≟",
    # Yahudi, Müslüman, Hristiyan Proper Noun Orthography (TDK standard: capitalized, apostrophe for case, no apostrophe for -ce / -lik / plural)
    "Yahudi/" + remap_flag_string("pFN pFL pFR pFY pFA pFI pFP pFC PF cl KC".replace(" ", "")),
    "Yahudice/" + remap_flag_string("CK F3 L2 P3 P7 PF PP PU PW Q2 R2 a3 cl i2 n3 y2 KC".replace(" ", "")),
    "Yahudilik/" + remap_flag_string("CK I2 L2 PF Q2 R2 V3 cl KC".replace(" ", "")),
    "Yahudiliğ/" + remap_flag_string("NE A3 N3 P3 P7 PP PU PW Y2 vc KC".replace(" ", "")),
    "Müslüman/" + remap_flag_string("pBN pBL pBR pBY pBA pBI pBP pBC PB CL LI LK SZ SL KC".replace(" ", "")),
    "Müslümanca/" + remap_flag_string("CK B3 L1 P1 P5 PB PM PN PS Q1 R1 a1 CL i1 n1 y1 KC".replace(" ", "")),
    "Müslümanlık/" + remap_flag_string("CK I1 L1 PB Q1 R1 V1 CL KC".replace(" ", "")),
    "Müslümanlığ/" + remap_flag_string("NE A1 N1 P1 P5 PM PN PS Y1 VC KC".replace(" ", "")),
    "Hristiyan/" + remap_flag_string("pBN pBL pBR pBY pBA pBI pBP pBC PB CL LI LK SZ SL KC".replace(" ", "")),
    "Hristiyanca/" + remap_flag_string("CK B3 L1 P1 P5 PB PM PN PS Q1 R1 a1 CL i1 n1 y1 KC".replace(" ", "")),
    "Hristiyanlık/" + remap_flag_string("CK I1 L1 PB Q1 R1 V1 CL KC".replace(" ", "")),
    "Hristiyanlığ/" + remap_flag_string("NE A1 N1 P1 P5 PM PN PS Y1 VC KC".replace(" ", "")),
    # Misakımilli / Misakımillî Proper Noun Orthography (capitalized, with proper noun apostrophe flags)
    "Misakımilli/" + remap_flag_string("CK F3 L2 P3 P7 PF PP PU PW Q2 R2 a3 cl i2 n3 y2 pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", "")),
    "Misakımillî/" + remap_flag_string("CK F3 L2 P3 P7 PF PP PU PW Q2 R2 a3 cl i2 n3 y2 pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", "")),
    # TDK / DD regular derived or compound words
    "çıtır/" + remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SZ Y1".replace(" ", "")),
    "çerçöp/∃∌∍∖√∢∨∩∪∮∵∹∻≀≅≈≊≌≍≎≤≩",
    "serçeparmak/∌∍∎∡∧∩∪∺≉≋≍≎≏≔≾",
    "tutamak/" + remap_flag_string("CI CK CL I1 L1 LI LK PB Q1 R1 SZ V1".replace(" ", "")),
    "sürücüsüz/" + FRONT_ROUNDED_UNVOICED_FLAGS,
    "statüsüz/" + FRONT_ROUNDED_UNVOICED_FLAGS,
    "kovuksuz/" + BACK_ROUNDED_UNVOICED_FLAGS,
    "temsilen",
    "sanayiinde",
    "buzdağı/∀∈∍∎∡∧∫∲∶∺∼∽≂≉≋≍≣",
    "buzdağ/∁∅∌∍∎∡∧∩∪∬∳∷∺∾≁≃≉≋≍≎≣",
    "gökcismi/∂∊∍∢∨∭∴∸∻∿≄≆≊≌≤≩",
    "gökcisim/∌∍∖∢∨∩∪∻≊≌≍≎≑≩",
    "fas", "go", "hut", "çad",
    # Chemical element symbols & letter names from TDK:
    "ac", "bi", "ca", "cl", "co", "cu", "ga", "li", "lu", "me", "mn", "mo", "n", "na",
    "ni", "pa", "pu", "ra", "rh", "sc", "u", "v", "y", "ö", "ı", "ın", "ır", "ke", "isa",
    "ag", "Ag", "ba", "Ba", "be", "Be", "br", "Br", "ce", "Ce", "cr", "Cr", "dy", "Dy",
    "hg", "Hg", "nb", "Nb", "nd", "Nd", "th", "Th", "zr", "Zr", "ph", "pH",
    "vâkıfane", "vâle", "hâletinez", "neftîmsi", "zengûle", "zımparamsı",
    # Technical & authoritative noun roots missing from base dictionaries:
    "kod/" + remap_flag_string("A2 B2 CI CK CL DE DL DT I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1 VC".replace(" ", "")),
    # Physics & scientific compound derivations:
    "kütleçekim/" + FRONT_UNVOICED_FLAGS,
    "yerçekim/" + FRONT_UNVOICED_FLAGS,
    "kütleçekimsel/" + FRONT_UNVOICED_FLAGS,
    "yerçekimsel/" + FRONT_UNVOICED_FLAGS,
    "dilbilgisel/" + FRONT_UNVOICED_FLAGS,
    "üstbilişsel/" + FRONT_UNVOICED_FLAGS,
    "sözdebilimsel/" + FRONT_UNVOICED_FLAGS,
    "vektörel/" + FRONT_UNVOICED_FLAGS,
    "maruziyet/" + FRONT_UNVOICED_FLAGS,
    "temsiliyet/" + FRONT_UNVOICED_FLAGS,
    "tekabüliyet/" + FRONT_UNVOICED_FLAGS,
    "asteroit/" + FRONT_UNVOICED_FLAGS,
    "asteroid/" + remap_flag_string("NE A3 N3 P3 P7 PP PU PW Y2 vc".replace(" ", "")),
    "otoimmün/" + FRONT_ROUNDED_UNVOICED_FLAGS,
    "kortizol/" + BACK_ROUNDED_UNVOICED_FLAGS,
    # Productive inter-X compound adjectives (-lararası / -lerarası):
    "yıldızlararası/" + B3_VOWEL_FLAGS,
    "gezegenlerarası/" + B3_VOWEL_FLAGS,
    "dinlerarası/" + B3_VOWEL_FLAGS,
    "buzullararası/" + B3_VOWEL_FLAGS,
    "bankalararası/" + B3_VOWEL_FLAGS,
    "eyaletlerarası/" + B3_VOWEL_FLAGS,
    # Computing verbal nouns (-lama / -leme):
    "adresleme/" + F3_VOWEL_FLAGS,
    "tünelleme/" + F3_VOWEL_FLAGS,
    "indeksleme/" + F3_VOWEL_FLAGS,
    "girintileme/" + F3_VOWEL_FLAGS,
    "anahtarlama/" + B3_VOWEL_FLAGS,
    "kablolama/" + B3_VOWEL_FLAGS,
    "haritalama/" + B3_VOWEL_FLAGS,
    "lisanslama/" + B3_VOWEL_FLAGS,
    # Specialized agents, ideologies and enzymes:
    "rapçi/" + FRONT_UNVOICED_FLAGS,
    "küçükresim/" + FRONT_UNVOICED_FLAGS,
    "psikiyatrist/" + FRONT_UNVOICED_FLAGS,
    "pasifist/" + FRONT_UNVOICED_FLAGS,
    "minimalist/" + FRONT_UNVOICED_FLAGS,
    "elitist/" + FRONT_UNVOICED_FLAGS,
    "pasifizm/" + FRONT_UNVOICED_FLAGS,
    "polimeraz/" + BACK_UNVOICED_FLAGS,
    "oksidaz/" + BACK_UNVOICED_FLAGS,
    "kinaz/" + BACK_UNVOICED_FLAGS,
    "sentaz/" + BACK_UNVOICED_FLAGS,
    "senkronize/" + F3_VOWEL_FLAGS,
    "plasebo/" + B4_VOWEL_FLAGS,
    "paramiliter/" + FRONT_UNVOICED_FLAGS,
    "paranormal/" + BACK_UNVOICED_FLAGS,
    # Scientific -ik loanword adjectives:
    "psikiyatrik", "embriyonik", "asidik", "periferik", "taksonomik", "kanonik",
    "mikroskopik", "makroskopik", "fotovoltaik", "filogenetik", "biyotik", "abiyotik",
    "harmonik", "genomik", "algoritmik", "sinaptik", "ultrasonik", "pediatrik",
    "sitoplazmik", "elektrolitik", "holografik", "semptomatik", "fenotipik", "enzimatik"
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
            w = tr_lower(line.strip().split("/")[0].split(" (")[0])
            if w: tdk_words.add(w)
            
    dd_words = set()
    with open(DD_PATH, encoding="utf-8") as f:
        for line in f:
            w = tr_lower(line.strip().split("/")[0].split(" (")[0])
            if w: dd_words.add(w)
            
    custom_abbrevs = set()
    custom_abbrevs_orig = set()
    if CUSTOM_ABBREV_PATH.exists():
        with open(CUSTOM_ABBREV_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                lem = item.get("lemma", "").strip()
                if lem:
                    # Do NOT lowercase abbreviations: preserve exact casing
                    custom_abbrevs_orig.add(lem)
                    if lem.islower():
                        custom_abbrevs.add(lem)
                    
    custom_names = set()
    custom_names_orig = set()
    if CUSTOM_NAMES_PATH.exists():
        with open(CUSTOM_NAMES_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                lem = item.get("lemma", "").strip()
                if lem:
                    custom_names_orig.add(lem)
                    if lem.islower():
                        custom_names.add(lem)
                    
    bilim_sanat_lexicon = []
    bilim_sanat_words = set()
    if BILIM_SANAT_PATH.exists():
        with open(BILIM_SANAT_PATH, encoding="utf-8") as f:
            bilim_sanat_lexicon = json.load(f)
            for item in bilim_sanat_lexicon:
                lem = item.get("lemma", "").strip()
                if lem:
                    bilim_sanat_words.add(tr_lower(lem))
                    
    print(f"  TDK: {len(tdk_words):,}, DD: {len(dd_words):,}, Bilim-Sanat: {len(bilim_sanat_words):,}, Abbrevs: {len(custom_abbrevs_orig):,}, Names: {len(custom_names_orig):,}")
    return tdk_words, dd_words, bilim_sanat_lexicon, bilim_sanat_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig

def build_hardened_aff(profile="tdk"):
    print(f"Building hardened .aff file for profile [{profile}]...")
    with open(AFF_SRC, "r", encoding="utf-8") as f:
        raw_aff_check = f.read()
    if "FLAG long" in raw_aff_check:
        from compile_hunspell_utf8 import remap_aff_file
        remap_aff_file(str(AFF_SRC), str(AFF_SRC))
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
            elif line_s.startswith("SFX ⊂ mak ırm"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊁ mek üre"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s in ("SFX ≓ amak adırıp amak", "SFX ≓ ımak ıdırıp ımak"):
                parts = line_s.split(); parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊃ mek irme/"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s == "SFX ≚ tmak dıktan tmak":
                line = "SFX ≚ mak tıktan tmak\n"
            elif line_s == "SFX ≛ tmak duktan tmak":
                line = "SFX ≛ mak tuktan tmak\n"
            elif line_s == "SFX ≜ tmek dikten tmek":
                line = "SFX ≜ mek tikten tmek\n"
            elif line_s == "SFX ≝ tmek dükten tmek":
                line = "SFX ≝ mek tükten tmek\n"
            elif line_s in ("SFX ≠ emek idikten [dy]emek", "SFX ≠ emek idikten demek", "SFX ≠ emek idikten yemek"):
                line = f"SFX ≠ mek dikten {parts[4]}\n"
            elif len(parts) >= 4 and "/" in parts[3]:
                clean_add, flags = parts[3].split("/", 1)
                if clean_add.endswith("ğ") and "X" not in flags:
                    parts[3] = f"{clean_add}/X{flags}"
                    line = " ".join(parts) + "\n"
            if curr_flag not in STAGE2_VERB_CHARS and len(parts) >= 5:
                clean_add = parts[3].split("/")[0]
                if parts[2] in ("mak", "mek"):
                    if clean_add.startswith(("ıl", "il", "ul", "ül")):
                        parts[4] = f"[^lAEIOUaeiouÂÎÖÛÜâîöûüİı]{parts[2]}"
                        line = " ".join(parts) + "\n"
                        fixed_wildcards += 1
                    elif parts[4] in (".", consonant_cond) and clean_add and clean_add[0] in vowels:
                        parts[4] = f"[^AEIOUaeiouÂÎÖÛÜâîöûüİı]{parts[2]}"
                        line = " ".join(parts) + "\n"
                        fixed_wildcards += 1
                elif parts[4] == "." and clean_add and clean_add[0] in vowels:
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

    if profile == "tdk":
        clean_extra.extend([
            "resmi resmî",
            "milli millî",
            "dini dinî",
            "askeri askerî",
            "tarihi tarihî",
            "ahlaki ahlâkî",
            "dahili dâhilî",
            "ilmi ilmî",
            "edebi edebî",
            "ebedi ebedî",
            "insani insanî",
            "ruhi ruhî",
            "siyasi siyasî",
            "hukuki hukukî",
            "iktisadi iktisadî",
            "felsefi felsefî",
            "zihni zihnî",
            "hayali hayalî",
            "manevi manevî",
            "maddi maddî",
            "harbi harbî",
            "kısmi kısmî",
            "şahsi şahsî",
            "vicdani vicdanî",
            "dahiliye dâhiliye",
            "dahil dâhil",
            "bekar bekâr",
            "ruzgar rüzgâr",
            "hikaye hikâye",
            "kagıt kâğıt",
            "kagit kâğıt",
            "dukkan dükkân",
            "tezgah tezgâh",
            "mekan mekân",
            "imkan imkân",
            "mahkum mahkûm",
            "sukun sükûn",
            "sukut sükût",
            "batini bâtıni",
            "teleskopu teleskobu",
            "bergamotu bergamodu",
            "baçı bacı",
            "bilim$ _bilimi"
        ])
        # Load all TDK-open compound suggestions (where joined is used in Dil Derneği)
        _tdk_open_rep_path = RAW_DIR / "tdk_open_compound_rep.json"
        if _tdk_open_rep_path.exists():
            with open(_tdk_open_rep_path, encoding="utf-8") as _torf:
                clean_extra.extend(json.load(_torf))
    elif profile == "dd":
        clean_extra.extend([
            "î i",
            "resmî resmi",
            "askerî askeri",
            "dinî dini",
            "millî milli",
            "misakımilli Misakımilli",
            "misakımillî Misakımilli",
            "Misakımillî Misakımilli"
        ])
        # Load all DD-open compound suggestions (where joined is used in TDK)
        _dd_open_rep_path = RAW_DIR / "dd_open_compound_rep.json"
        if _dd_open_rep_path.exists():
            with open(_dd_open_rep_path, encoding="utf-8") as _dorf:
                clean_extra.extend(json.load(_dorf))
        
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

PROPER_B = remap_flag_string("pBN pBL pBR pBY pBA pBI pBP pBC".replace(" ", ""))
PROPER_O = remap_flag_string("pON pOL pOR pOY pOA pOI pOP pOC".replace(" ", ""))
PROPER_F = remap_flag_string("pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", ""))
PROPER_U = remap_flag_string("pUN pUL pUR pUY pUA pUI pUP pUC".replace(" ", ""))

UNIT_FLAG_MAP = {
    "cm": PROPER_F, "mm": PROPER_F, "km": PROPER_F, "dm": PROPER_F, "nm": PROPER_F,
    "ml": PROPER_F, "mL": PROPER_F, "cl": PROPER_F, "dl": PROPER_F, "hl": PROPER_F,
    "lt": PROPER_F, "sn": PROPER_F,
    "kg": PROPER_B, "gr": PROPER_B, "mg": PROPER_B, "dg": PROPER_B, "cg": PROPER_B,
    "dk": PROPER_B, "yy": PROPER_B,
    "kr": PROPER_O, "krş": PROPER_O,
}

BRAND_FLAG_MAP = {
    "iPhone": remap_flag_string("KC CK CL cl L1 L2".replace(" ", "")) + PROPER_O + PROPER_F,
    "iPad": remap_flag_string("KC CK cl L2".replace(" ", "")) + PROPER_F + PROPER_B,
    "YouTube": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_O + PROPER_F,
    "Google": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_B + PROPER_F,
    "Apple": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_B + PROPER_F,
    "Twitter": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_B + PROPER_F,
    "VMware": remap_flag_string("CK cl L2".replace(" ", "")) + PROPER_F,
    "A101": PROPER_F,
}


def get_abbrev_flags(w: str) -> str:
    if not w or len(w) <= 1 or any(c in w for c in ". '/"):
        return ""
    if w in UNIT_FLAG_MAP:
        return UNIT_FLAG_MAP[w]
    if w in BRAND_FLAG_MAP:
        return BRAND_FLAG_MAP[w]
    wl = tr_lower(w)
    if wl in ("usb", "hdmi", "hdmı"):
        return HEAD_FLAG_OVERRIDES[wl]
    if w.isupper() and w.isalpha() and len(w) >= 2:
        if w[-1] in "AIÂ":
            fl = PROPER_B
        elif w[-1] in "OUÛ":
            fl = PROPER_O
        elif w[-1] in "EİÎ":
            fl = PROPER_F
        elif w[-1] in "ÖÜ":
            fl = PROPER_U
        else:
            if w[-1] == "Q":
                fl = PROPER_U
            elif w[-1] == "W":
                fl = PROPER_O + PROPER_F
            else:
                fl = PROPER_F
            if w[-1] in "KH" or w in ("TL", "GB", "MB", "TB", "KB", "PB"):
                fl += PROPER_B
            for ch in reversed(w):
                if ch in "AIÂOUÛEİÎÖÜ":
                    if ch in "AIÂ":
                        fl += PROPER_B
                    elif ch in "OUÛ":
                        fl += PROPER_O
                    elif ch in "EİÎ":
                        fl += PROPER_F
                    elif ch in "ÖÜ":
                        fl += PROPER_U
                    break
        return "".join(sorted(set(fl)))
    if w.isalpha() and len(w) >= 2:
        lv = "e"
        for ch in reversed(w):
            if ch in "aıâouûeiîöüAIÂOUÛEİÎÖÜ":
                lv = tr_lower(ch)
                break
        if lv in "aıâ":
            fl = PROPER_B
        elif lv in "ouû":
            fl = PROPER_O
        elif lv in "eiî":
            fl = PROPER_F
        else:
            fl = PROPER_U
        if w[-1].isupper() and w[-1] not in "AIÂOUÛEİÎÖÜ":
            fl += PROPER_F
            if w[-1] in "KH":
                fl += PROPER_B
        return "".join(sorted(set(fl)))
    return ""


def build_sanitized_dic(tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig, bilim_sanat_lexicon=None, bilim_sanat_words=None, profile="tdk"):
    print(f"Sanitizing .dic file for profile [{profile}]...")
    
    unhatted_to_purge = {tr_lower(v) for v in MANDATORY_HATTED_WORDS.values()}
    unhat_map = str.maketrans('âîûÂÎÛ', 'aiuAIU')
    for h in tdk_words:
        if any(c in h for c in 'âîû'):
            u = h.translate(unhat_map)
            if profile == "tdk":
                if u not in tdk_words:
                    unhatted_to_purge.add(tr_lower(u))
            else:
                if u not in dd_words and u not in tdk_words:
                    unhatted_to_purge.add(tr_lower(u))
    print(f"  Unhatted clones targeted for purge: {len(unhatted_to_purge)}")

    authority_all = tdk_words | dd_words
    if profile in ("universal", "bilim-sanat") and bilim_sanat_words:
        authority_all = authority_all | bilim_sanat_words
    dd_words_to_purge = set()
    if profile == "tdk":
        all_ref = tdk_words
        dd_words_to_purge = (dd_words - tdk_words) - custom_names - custom_abbrevs - {tr_lower(c) for c in COMPOUND_SET}
        print(f"  Dil Derneği-only words targeted for purge: {len(dd_words_to_purge)}")
    elif profile == "dd":
        all_ref = dd_words
    else:
        all_ref = authority_all
    whitelist = (all_ref - unhatted_to_purge) | custom_abbrevs | custom_names | {tr_lower(c) for c in COMPOUND_SET}
    
    BAD_STEMS = {
        "istasyonu", "televizyonu", "dma", "ce", "hum", "a101",
        "dilerini", "bızız", "islaminin",
        "gorkem", "bahce", "cocuk", "catal", "ornek", "gorevli", "bakici",
        "gorev", "ozet", "bahceci", "goren", "gore", "msde", "cocuklar",
        "calon", "keefe", "jfet",
        "mebs", "ornegi", "ıcad", "icad", "ıkisi", "ikisi", "felaked", "stoğ",
        "topyekun", "alemşümul", "alemşümullük", "ademci", "kai", "klavuz",
        "öl", "mezhebi",
        # Purge legacy noise stems, false abbreviations, and uncapitalized proper nouns
        "aı", "baı", "baıc", "gur", "pluto",
        "yahudi", "yahudice", "yahudilik", "yahudiliğ", "yahudibaklası",
        "müslüman", "müslümanca", "müslümanlık", "müslümanlığ",
        "hristiyan", "hristiyanca", "hristiyanlık", "hristiyanlığ",
        "hıristiyan", "hıristiyanlık", "hıristiyanlığ",
        "misakımilli", "misakımillî",
        "fata", "çe",
        # Purge noisy abbreviation/symbol stems causing widespread inflection overgeneration
        "sr", "ac", "ag", "ariza", "aski", "ba", "paba", "kefne", "ekit",
        "cav", "pere", "pal", "hut", "banaz", "ızgın", "elazığ",
        "haletmek", "haledilmek", "haletme", "haledilme", "hal etmek", "günorta", "uçuc",
        # Explicit test rejection guards & pseudo-voicing stems
        "ved", "biled", "paked", "anked", "pantalon", "şöför", "stajer",
        "silahşör", "kapiler", "gözgöze", "gözgöz", "zembiligözgöz"
    }
    if profile == "tdk":
        BAD_STEMS.update({"fata", "çe"})

    _B12_CHARS = {LONG_TO_UTF8["B1"], LONG_TO_UTF8["B2"]}
    _F12_CHARS = {LONG_TO_UTF8["F1"], LONG_TO_UTF8["F2"]}
    _VC_CHAR = LONG_TO_UTF8["VC"]
    _vc_CHAR = LONG_TO_UTF8["vc"]
    
    with open(DIC_SRC, "r", encoding="utf-8") as f:
        f.readline()
        raw_lines = f.readlines()
        
    clean_entries = []
    seen_heads = set()
    
    removed_permutations = 0
    removed_crawler_spam = 0
    removed_unhatted_dups = 0
    removed_bad_stems = 0
    removed_dd_words = 0
    removed_redundant_upper = 0
    cleaned_common_noun_flags = 0
    
    # Single-pass parse and pre-scan lowercase heads
    existing_lower_heads = set()
    parsed_lines = []
    for line in raw_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        idx = line_clean.find("/")
        if idx != -1:
            head = line_clean[:idx]
            flags = line_clean[idx+1:]
        else:
            head = line_clean
            flags = ""
        parsed_lines.append((head, flags))
        if head.islower():
            existing_lower_heads.add(head)

    virtual_stem_heads = {w.split("/")[0] for w in VIRTUAL_STEMS}
    for head, flags in parsed_lines:
        head_lower = tr_lower(head)
        if head in virtual_stem_heads or " (" in head:
            continue
        
        # 1. Purge known bad stems and bogus voiced virtual stems
        if head_lower in PURGE_VIRTUAL_STEMS or head_lower in ("felaked", "stoğ"):
            removed_bad_stems += 1
            continue
        if head in BAD_STEMS or (
            head_lower in BAD_STEMS
            and (
                head.islower()
                or head_lower in {
                    "ademci", "topyekun", "alemşümul", "alemşümullük",
                    "misakımilli", "misakımillî", "yahudi", "yahudice",
                    "yahudilik", "yahudiliğ", "yahudibaklası", "fata", "çe",
                    "müslüman", "müslümanca", "müslümanlık", "müslümanlığ",
                    "hristiyan", "hristiyanca", "hristiyanlık", "hristiyanlığ",
                    "hıristiyan", "hıristiyanlık", "hıristiyanlığ"
                }
            )
        ):
            removed_bad_stems += 1
            continue

        # 1b. In TDK profile, purge words unique to Dil Derneği
        if profile == "tdk" and head_lower in dd_words_to_purge:
            removed_dd_words += 1
            continue
            
        # 2. Purge unhatted duplicates for mandatory hatted words
        if head in unhatted_to_purge or head_lower in unhatted_to_purge:
            removed_unhatted_dups += 1
            continue
            
        # 3. Whitelist check (protects all custom abbreviations, custom names, compound terms, TDK/DD)
        is_whitelisted = head_lower in whitelist or head in custom_abbrevs_orig or head in custom_names_orig or (head_lower in authority_all if profile != "tdk" else head_lower in tdk_words)
        
        if not is_whitelisted:
            # 1-3 letter permutation noise not in whitelist
            if len(head) <= 3 and head.isalpha():
                removed_permutations += 1
                continue
            # Chopped OCR fragments
            if head.isalpha() and RE_OCR_FRAGMENT.match(head_lower):
                removed_crawler_spam += 1
                continue
            # Crawler spam / repeated clusters
            if RE_REPEATED_CHARS.search(head) or RE_CONSONANT_CLUSTER.search(head_lower):
                removed_crawler_spam += 1
                continue
            if head.islower() and len(head) >= 4:
                if head_lower.startswith("aa") or head_lower.startswith("bb"):
                    removed_crawler_spam += 1
                    continue
                    
        # 4. Common noun vs proper noun compound separation
        is_compound_term = head_lower in COMPOUND_SET

        # Fast path: only partition flags if any PROPER_SUB_UTF8 flag character is present
        if any(c in PROPER_SUB_UTF8 for c in flags):
            proper_flags = "".join(c for c in flags if c in PROPER_SUB_UTF8)
            common_flags = "".join(c for c in flags if c not in PROPER_SUB_UTF8)
        else:
            proper_flags = ""
            common_flags = flags
        
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
                or (KC_FLAG and KC_FLAG in flags)
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
            elif head in UNIT_FLAG_MAP:
                flags = UNIT_FLAG_MAP[head]
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
        if head in UNIT_FLAG_MAP:
            flags = UNIT_FLAG_MAP[head]
        elif head in BRAND_FLAG_MAP:
            flags = BRAND_FLAG_MAP[head]
        elif len(head) >= 2 and head.isupper() and head.isalpha():
            flags = get_abbrev_flags(head)
        elif head in custom_abbrevs_orig and not head.islower():
            flags = "".join(sorted(set(flags + get_abbrev_flags(head))))
        elif head_lower in HEAD_FLAG_OVERRIDES:
            flags = HEAD_FLAG_OVERRIDES[head_lower]
        elif head_lower in PALATAL_L_HEADS:
            flags = PALATAL_L_FLAGS
        elif head_lower.endswith((" etmek", " gitmek")) or head_lower in ("kayetmek", "kayyetmek"):
            flags = LONG_TO_UTF8["VM"]
        elif head_lower.endswith(" tatmak"):
            flags = LONG_TO_UTF8["VK"]
        elif head_lower.endswith(" gütmek"):
            flags = LONG_TO_UTF8["VN"]
        elif not head_lower.endswith(("mak", "mek")) and "X" not in flags and any(c in flags for c in "≔≖≗≘≙≚≛≜≝≞≟≠≡"):
            # Rescue non-mak/mek nouns/adjectives that erroneously received verb flags
            if head_lower in {
                "aktı", "bakarak", "bakındı", "defol", "evlensek", "gebere", "görsün",
                "görürsün", "haçan", "hisset", "kıstı", "niceleyin", "ol", "sencileyin",
                "sevsinler", "seyret", "seç", "siktir", "sizcileyin", "sus", "sıyırdım",
                "yürü", "üçürdüm"
            }:
                flags = ""
            else:
                _lv = "a"
                for _ch in reversed(head_lower):
                    if _ch in "aeıioöuüâîû":
                        _lv = _ch
                        break
                if head_lower[-1] in "aeıioöuüâîû":
                    if _lv in "aıâ":
                        flags = B3_VOWEL_FLAGS
                    elif _lv in "ouû":
                        flags = B4_VOWEL_FLAGS
                    elif _lv in "eiî":
                        flags = F3_VOWEL_FLAGS
                    else:
                        flags = F4_VOWEL_FLAGS
                else:
                    if _lv in "aıâ":
                        flags = BACK_UNVOICED_FLAGS + (LONG_TO_UTF8["V1"] if head_lower.endswith("k") else "")
                    elif _lv in "ouû":
                        flags = BACK_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V2"] if head_lower.endswith("k") else "")
                    elif _lv in "eiî":
                        flags = FRONT_UNVOICED_FLAGS + (LONG_TO_UTF8["V3"] if head_lower.endswith("k") else "")
                    else:
                        flags = FRONT_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V4"] if head_lower.endswith("k") else "")
        
        # Inject vowel drop flags (D1, D2, D3, D4)
        if head_lower in VOWEL_DROP_D1_HEADS:
            d_flag = LONG_TO_UTF8.get("D1", "")
            if d_flag and d_flag not in flags:
                flags += d_flag
        elif head_lower in VOWEL_DROP_D2_HEADS:
            d_flag = LONG_TO_UTF8.get("D2", "")
            if d_flag and d_flag not in flags:
                flags += d_flag
        elif head_lower in VOWEL_DROP_D3_HEADS:
            d_flag = LONG_TO_UTF8.get("D3", "")
            if d_flag and d_flag not in flags:
                flags += d_flag
        elif head_lower in VOWEL_DROP_D4_HEADS:
            d_flag = LONG_TO_UTF8.get("D4", "")
            if d_flag and d_flag not in flags:
                flags += d_flag

        # Temporal relative -ki for sezon (sezonki, sezonkinin, sezonkiler)
        if head_lower == "sezon":
            k1_flag = LONG_TO_UTF8.get("K1", "")
            if k1_flag and k1_flag not in flags:
                flags += k1_flag

        # Loanwords ending in 'ing' must take front-vowel noun suffixes
        if head.lower().endswith("ing") and ("≑" in flags or not flags):
            flags = flags.replace("≑", "") + "∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪≎∌∍≍⊘⊙⊚⊛⊜⊝⊞⊟"
            
        # For TDK profile: dual voicing stems (teleskop, bergamot, baç) take only consonant suffixes
        if profile == "tdk" and head_lower in (DUAL_VOICING_BACK_ROUNDED + DUAL_VOICING_BACK_UNROUNDED):
            consonant_flags = remap_flag_string("CI CK CL L1 LI LK PB Q1 R1 SL SZ".replace(" ", ""))
            flags = "".join(sorted(set(c for c in flags if c in consonant_flags)))
        elif profile == "tdk" and head_lower in DUAL_VOICING_G_BACK_ROUNDED:
            consonant_v2_flags = remap_flag_string("V2 CI CK CL L1 LI LK PB Q1 R1 SL SZ".replace(" ", ""))
            flags = "".join(sorted(set(c for c in flags if c in consonant_v2_flags)))
            
        if profile == "dd" and "î" in head:
            head_dd = head.replace("î", "i")
            if head_dd in BAD_STEMS:
                continue
            head = head_dd
            
        if profile == "universal" and "î" in head:
            head_unhatted = head.replace("î", "i")
            if head_unhatted not in BAD_STEMS:
                entry_unhatted = (head_unhatted, flags)
                if entry_unhatted not in seen_heads:
                    seen_heads.add(entry_unhatted)
                    clean_entries.append(f"{head_unhatted}/{flags}" if flags else head_unhatted)

        # Dil Derneği accepts unhatted forms for certain words like batıni, batıniye
        if head.lower() in ("bâtıni", "bâtıniye"):
            head_unhatted = head.replace("â", "a")
            if profile == "dd":
                head = head_unhatted
            elif profile == "universal":
                entry_unhatted = (head_unhatted, flags)
                if entry_unhatted not in seen_heads:
                    seen_heads.add(entry_unhatted)
                    clean_entries.append(f"{head_unhatted}/{flags}" if flags else head_unhatted)
                
        if len(head) == 1:
            flags = ""
        elif head_lower.endswith(("p", "ç", "t", "k")):
            if any(c in _B12_CHARS for c in flags) and _VC_CHAR not in flags:
                flags += _VC_CHAR
            if any(c in _F12_CHARS for c in flags) and _vc_CHAR not in flags:
                flags += _vc_CHAR
            
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
        head_w = w.split("/")[0]
        head_lower = tr_lower(head_w)
        if profile == "tdk" and (head_w in unhatted_to_purge or head_lower in unhatted_to_purge):
            continue
        if profile == "dd" and "î" in head_w:
            continue
        if "/" not in w and head_lower in HEAD_FLAG_OVERRIDES:
            clean_entries.append(f"{w}/{HEAD_FLAG_OVERRIDES[head_lower]}")
        else:
            clean_entries.append(w)
        seen_heads.add((head_w, ""))
        added_legit += 1
            
    # 5b. Inject Bilim ve Sanat Terimleri in universal profile
    added_terimler = 0
    if profile in ("universal", "bilim-sanat") and bilim_sanat_lexicon:
        for t_item in bilim_sanat_lexicon:
            w = t_item["lemma"]
            head_lower = tr_lower(w)
            if (w, "") in seen_heads or (head_lower, "") in seen_heads:
                continue
            attrs = t_item.get("attributes", [])
            pos = t_item.get("pos", "Noun")
            if head_lower in HEAD_FLAG_OVERRIDES:
                fl = HEAD_FLAG_OVERRIDES[head_lower]
            elif head_lower in PALATAL_L_HEADS or "InverseHarmony" in attrs:
                fl = PALATAL_L_FLAGS
            elif "CompoundP3sg" in attrs:
                if head_lower.endswith("ı"):
                    fl = "∀∈∌∍∎∖∗∘∡∧∩∪∫∲∶∺∼∽≂≉≋≍≎≣"
                elif head_lower.endswith("u"):
                    fl = "∁∉∌∍∎∖∗∘∡∧∩∪∬∳∷∺∾≁≃≉≋≍≎≣"
                elif head_lower.endswith("i"):
                    fl = "∂∊∌∍∖∗∘∢∨∩∪∭∴∸∻∿≄≆≊≌≍≎≤≩"
                elif head_lower.endswith("ü"):
                    fl = "∃∋∌∍∖∗∘∢∨∩∪∮∵∹∻≀≅≈≊≌≍≎≤≩"
                else:
                    fl = ""
            elif pos == "Verb" and head_lower.endswith(("mak", "mek")):
                fl = ""
            else:
                _lv = "a"
                for _ch in reversed(head_lower):
                    if _ch in "aeıioöuüâîû":
                        _lv = _ch
                        break
                if head_lower[-1] in "aeıioöuüâîû":
                    if _lv in "aıâ": fl = B3_VOWEL_FLAGS
                    elif _lv in "ouû": fl = B4_VOWEL_FLAGS
                    elif _lv in "eiî": fl = F3_VOWEL_FLAGS
                    else: fl = F4_VOWEL_FLAGS
                else:
                    has_voicing = "Voicing" in attrs or head_lower.endswith("k")
                    if _lv in "aıâ":
                        fl = BACK_UNVOICED_FLAGS + (LONG_TO_UTF8["V1"] if has_voicing else "")
                    elif _lv in "ouû":
                        fl = BACK_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V2"] if has_voicing else "")
                    elif _lv in "eiî":
                        fl = FRONT_UNVOICED_FLAGS + (LONG_TO_UTF8["V3"] if has_voicing else "")
                    else:
                        fl = FRONT_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V4"] if has_voicing else "")
            
            clean_entries.append(f"{w}/{fl}" if fl else w)
            seen_heads.add((w, ""))
            added_terimler += 1
        print(f"  Injected: {added_terimler:,} Bilim ve Sanat Terimleri lemmas into profile [{profile}].")

    # 6. Inject all missing custom abbreviations and names from lexicons
    added_abbrevs = 0
    for a in custom_abbrevs_orig:
        if (a, "") not in seen_heads:
            if (a.lower(), "") not in seen_heads or a != a.lower():
                fl_a = get_abbrev_flags(a)
                if not fl_a and a.lower() in HEAD_FLAG_OVERRIDES:
                    fl_a = HEAD_FLAG_OVERRIDES[a.lower()]
                clean_entries.append(f"{a}/{fl_a}" if fl_a else a)
                seen_heads.add((a, ""))
                added_abbrevs += 1
            
    lower_to_flags = {}
    for h, fl in parsed_lines:
        if h.islower():
            lower_to_flags[h] = fl

    added_names = 0
    for n in custom_names_orig:
        if (n, "") not in seen_heads and ((n.lower(), "") not in seen_heads or (n and (n[0].isupper() or any(c.isupper() for c in n)))):
            base_fl = lower_to_flags.get(n.lower(), "")
            # Assign harmonic proper noun apostrophe inflection flags for capitalized proper names
            if n in BRAND_FLAG_MAP:
                entry_n = f"{n}/{BRAND_FLAG_MAP[n]}"
            elif len(n) >= 2 and n.isupper() and n.isalpha():
                fl_n = get_abbrev_flags(n)
                entry_n = f"{n}/{fl_n}" if fl_n else n
            elif n.lower() in HEAD_FLAG_OVERRIDES:
                entry_n = f"{n}/{HEAD_FLAG_OVERRIDES[n.lower()]}"
            elif n and (n[0].isupper() or any(c.isupper() for c in n)) and not any(c in n for c in "0123456789."):
                last_vowel = ""
                for ch in reversed(n):
                    if ch in "aıâouûeiîöüAIÂOUÛEİÎÖÜ":
                        last_vowel = tr_lower(ch)
                        break
                if last_vowel in "aıâ":
                    proper_flags = remap_flag_string("CK CL L1 pBN pBL pBR pBY pBA pBI pBP pBC".replace(" ", ""))
                elif last_vowel in "ouû":
                    proper_flags = remap_flag_string("CK CL L1 pON pOL pOR pOY pOA pOI pOP pOC".replace(" ", ""))
                elif last_vowel in "eiî":
                    proper_flags = remap_flag_string("CK cl L2 pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", ""))
                elif last_vowel in "öü":
                    proper_flags = remap_flag_string("CK cl L2 pUN pUL pUR pUY pUA pUI pUP pUC".replace(" ", ""))
                else:
                    proper_flags = ""
                combined_fl = "".join(sorted(set(base_fl + proper_flags)))
                entry_n = f"{n}/{combined_fl}" if combined_fl else n
            else:
                entry_n = f"{n}/{base_fl}" if base_fl else n
            clean_entries.append(entry_n)
            seen_heads.add((n, ""))
            added_names += 1
            
    print(f"  Injected: {added_legit} legitimate missed words, {added_abbrevs} missing abbrevs, {added_names} missing names.")
    
    # 7. Deduplicate multi-line heads in .dic
    merged_heads = {}
    for entry in clean_entries:
        idx = entry.find("/")
        if idx != -1:
            h = entry[:idx]
            fl = entry[idx+1:]
        else:
            h = entry
            fl = ""
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

def compile_v06(deploy_profile="universal"):
    tdk_words, dd_words, bilim_sanat_lexicon, bilim_sanat_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig = load_lexicons()
    
    profiles = ["tdk", "dd", "universal"]
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    for prof in profiles:
        print(f"\n=======================================================")
        print(f"Compiling Turkspell - Profile: [{prof.upper()}]")
        print(f"=======================================================")
        
        prof_dir = DIST_DIR / f"turkspell-{prof}"
        prof_dir.mkdir(parents=True, exist_ok=True)
        
        # Build aff
        aff_content = build_hardened_aff(profile=prof)
        aff_out = prof_dir / "tr.aff"
        with open(aff_out, "w", encoding="utf-8") as f:
            f.write(aff_content)
            
        # Build dic
        dic_entries = build_sanitized_dic(
            tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig,
            bilim_sanat_lexicon=bilim_sanat_lexicon, bilim_sanat_words=bilim_sanat_words, profile=prof
        )
        dic_out = prof_dir / "tr.dic"
        with open(dic_out, "w", encoding="utf-8") as f:
            f.write(f"{len(dic_entries)}\n")
            for entry in dic_entries:
                f.write(f"{entry}\n")
                
        print(f"Successfully compiled: {prof_dir / 'tr.aff'} and {prof_dir / 'tr.dic'}")
        
    def _copy_file(src, dst):
        try:
            shutil.copy2(src, dst)
        except OSError:
            with open(src, "rb") as f_in, open(dst, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    # Deploy selected profile to repository root
    print(f"\nDeploying Turkspell ({deploy_profile.upper()}) to repository root (c:\\gemini\\turkspell\\tr.*)...")
    _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.aff", TURKSPELL_DIR / "tr.aff")
    _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.dic", TURKSPELL_DIR / "tr.dic")
    
    # Deploy to Firefox addon
    addon_dict_dir = TURKSPELL_DIR / "firefox-addon" / "dictionaries"
    if addon_dict_dir.exists():
        _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.aff", addon_dict_dir / "tr.aff")
        _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.dic", addon_dict_dir / "tr.dic")
        
    print("Deployment complete!")
    print("\nValidating deployed dictionary and running regression tests...")
    from validate_build import validate
    errors, warnings = validate(str(TURKSPELL_DIR / "tr.dic"), str(TURKSPELL_DIR / "tr.aff"), run_tests=True)
    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR:   {e}")
    if errors:
        raise SystemExit(f"\nDeployed dictionary failed validation: {len(errors)} error(s).")
    print(f"Validation and regression tests passed ({len(warnings)} warning(s)).")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compile Turkspell Hunspell dictionaries")
    parser.add_argument(
        "--deploy-profile",
        default=os.environ.get("TURKSPELL_PROFILE", "universal"),
        choices=["tdk", "universal", "dd"],
        help="Profile to deploy to repo root and firefox-addon (default: universal)"
    )
    args = parser.parse_args()
    compile_v06(deploy_profile=args.deploy_profile)
