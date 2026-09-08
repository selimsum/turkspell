# -*- coding: utf-8 -*-
"""
Curate and maintain lexicons/custom_names.json.
Retains strictly:
1. World country names (in Turkish)
2. City names: Turkish 81 provinces + major districts + world capitals & major cities
3. Popular brand names (global & Turkish)

Purges all personal given/surnames, OCR noise, casing errors (e.g. COCUKLARI, Cagatay),
inflections, and non-proper nouns.
"""

import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\gemini\turkspell")
NAMES_PATH = BASE_DIR / "lexicons" / "custom_names.json"
BACKUP_PATH = BASE_DIR / "lexicons" / "custom_names.json.bak"

# ---------------------------------------------------------------------------
# 1. COUNTRIES (World sovereign nations, territories, and common Turkish forms)
# ---------------------------------------------------------------------------
COUNTRIES = [
    "Afganistan", "Almanya", "Amerika", "Amerika Birleşik Devletleri", "Andorra",
    "Angola", "Antigua ve Barbuda", "Arjantin", "Arnavutluk", "Avustralya",
    "Avusturya", "Azerbaycan", "Bahamalar", "Bahreyn", "Bangladeş",
    "Barbados", "Batı Sahra", "Belarus", "Belçika", "Belize",
    "Benin", "Bhutan", "Birleşik Arap Emirlikleri", "Birleşik Krallık", "Bolivya",
    "Bosna-Hersek", "Botsvana", "Brezilya", "Brunei", "Bulgaristan",
    "Burkina Faso", "Burundi", "Cezayir", "Cibuti", "Çad",
    "Çek Cumhuriyeti", "Çekya", "Çin", "Danimarka", "Doğu Timor",
    "Dominik Cumhuriyeti", "Dominika", "Ekvador", "Ekvator Ginesi", "El Salvador",
    "Endonezya", "Eritre", "Ermenistan", "Estonya", "Esvatini",
    "Etiyopya", "Fas", "Fiji", "Fildişi Sahili", "Filipinler",
    "Filistin", "Finlandiya", "Fransa", "Gabon", "Galler",
    "Gambiya", "Gana", "Gine", "Gine-Bissau", "Grenada",
    "Grönland", "Guatemala", "Guyana", "Güney Afrika", "Güney Kore",
    "Güney Kıbrıs", "Güney Sudan", "Gürcistan", "Haiti", "Hırvatistan",
    "Hindistan", "Hollanda", "Honduras", "Irak", "İran",
    "İrlanda", "İskoçya", "İspanya", "İsrail", "İsveç",
    "İsviçre", "İtalya", "İzlanda", "Jamaika", "Japonya",
    "Kamboçya", "Kamerun", "Kanada", "Karadağ", "Katar",
    "Kazakistan", "Kenya", "Kırgızistan", "Kıbrıs", "Kiribati",
    "Kolombiya", "Komorlar", "Kongo", "Kosova", "Kosta Rika",
    "Kuveyt", "Kuzey İrlanda", "Kuzey Kore", "Kuzey Makedonya", "Küba",
    "Laos", "Letonya", "Liberya", "Libya", "Lihtenştayn",
    "Litvanya", "Lübnan", "Lüksemburg", "Macaristan", "Madagaskar",
    "Malavi", "Malezya", "Maldivler", "Mali", "Malta",
    "Marshall Adaları", "Mauritius", "Meksika", "Mikronezya", "Mısır",
    "Moğolistan", "Moldova", "Monako", "Moritanya", "Mozambik",
    "Myanmar", "Namibya", "Nauru", "Nepal", "Nijer",
    "Nijerya", "Nikaragua", "Norveç", "Orta Afrika Cumhuriyeti", "Özbekistan",
    "Pakistan", "Palau", "Panama", "Papua Yeni Gine", "Paraguay",
    "Peru", "Polonya", "Portekiz", "Romanya", "Ruanda",
    "Rusya", "Saint Kitts ve Nevis", "Saint Lucia", "Saint Vincent ve Grenadinler", "Samoa",
    "San Marino", "Sao Tome ve Principe", "Senegal", "Seyşeller", "Sırbistan",
    "Sierra Leone", "Singapur", "Slovakya", "Slovenya", "Solomon Adaları",
    "Somali", "Sri Lanka", "Sudan", "Surinam", "Suriye",
    "Suudi Arabistan", "Şili", "Tacikistan", "Tanzanya", "Tayland",
    "Tayvan", "Togo", "Tonga", "Trinidad ve Tobago", "Tunus",
    "Tuvalu", "Türkiye", "Türkmenistan", "Uganda", "Ukrayna",
    "Umman", "Uruguay", "Ürdün", "Vanuatu", "Vatikan",
    "Venezuela", "Vietnam", "Yemen", "Yeni Zelanda", "Yeşil Burun Adaları",
    "Yunanistan", "Zambiya", "Zimbabve"
]

# ---------------------------------------------------------------------------
# 2. TURKISH CITIES (All 81 provinces + major districts & metropolitan areas)
# ---------------------------------------------------------------------------
TURKISH_PROVINCES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray",
    "Amasya", "Ankara", "Antalya", "Ardahan", "Artvin",
    "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt",
    "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur",
    "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
    "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan",
    "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane",
    "Hakkâri", "Hakkari", "Hatay", "Iğdır", "Isparta",
    "İstanbul", "İzmir", "Kahramanmaraş", "Karabük", "Karaman",
    "Kars", "Kastamonu", "Kayseri", "Kırıkkale", "Kırklareli",
    "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya",
    "Malatya", "Manisa", "Mardin", "Mersin", "Muğla",
    "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye",
    "Rize", "Sakarya", "Samsun", "Siirt", "Sinop",
    "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat",
    "Trabzon", "Tunceli", "Uşak", "Van", "Yalova",
    "Yozgat", "Zonguldak"
]

TURKISH_DISTRICTS = [
    "Adalar", "Akçaabat", "Akçakoca", "Akhisar", "Alanya",
    "Aliağa", "Altınordu", "Altındağ", "Amasra", "Anamur",
    "Antakya", "Araklı", "Ardeşen", "Arnavutköy", "Ataşehir",
    "Atakum", "Avcılar", "Ayvalık", "Bafra", "Bağcılar",
    "Bahçelievler", "Bakırköy", "Bandırma", "Başakşehir", "Beşiktaş",
    "Beykoz", "Beylikdüzü", "Beyoğlu", "Beypazarı", "Biga",
    "Birecik", "Bodrum", "Bornova", "Bozüyük", "Buca",
    "Bulancak", "Burhaniye", "Büyükçekmece", "Ceyhan", "Cizre",
    "Çamlıhemşin", "Çankaya", "Çarşamba", "Çaycuma", "Çayeli",
    "Çekmeköy", "Çerkezköy", "Çeşme", "Çiğli", "Çorlu",
    "Dalaman", "Darıca", "Datça", "Develi", "Didim",
    "Doğubayazıt", "Dörtyol", "Edremit", "Elbistan", "Elmadağ",
    "Erbaa", "Erciş", "Erdemli", "Ereğli", "Esenler",
    "Esenyurt", "Espiye", "Etimesgut", "Eyüpsultan", "Fatih",
    "Fatsa", "Fethiye", "Foça", "Gaziemir", "Gazipaşa",
    "Gaziosmanpaşa", "Gebze", "Gelibolu", "Gemlik", "Gerede",
    "Geyve", "Gölbaşı", "Gölcük", "Gönen", "Görele",
    "Güngören", "Hendek", "Hopa", "Ilgaz", "İnegöl",
    "İpsala", "İskenderun", "İznik", "Kadıköy", "Kağıthane",
    "Kahta", "Kalkan", "Karamürsel", "Karadeniz Ereğli", "Karataş",
    "Kartal", "Karşıyaka", "Kaş", "Kavacık", "Kemer",
    "Kepez", "Keşan", "Kızılcahamam", "Kızıltepe", "Kireçburnu",
    "Konak", "Kozan", "Körfez", "Köyceğiz", "Kumluca",
    "Kuşadası", "Küçükçekmece", "Lapseki", "Lüleburgaz", "Maltepe",
    "Mamak", "Manavgat", "Marmaraereğlisi", "Marmaris", "Melikgazi",
    "Menemen", "Merzifon", "Midyat", "Milas", "Mudanya",
    "Muratpaşa", "Mustafakemalpaşa", "Nazilli", "Niksar", "Nilüfer",
    "Nizip", "Nusaybin", "Of", "Ortaca", "Osmangazi",
    "Ödemiş", "Pamukkale", "Pendik", "Polatlı", "Reyhanlı",
    "Safranbolu", "Salihli", "Samandağ", "Sancaktepe", "Sandıklı",
    "Sapanca", "Sarıyer", "Seferihisar", "Selçuk", "Serik",
    "Seyhan", "Silifke", "Silivri", "Silopi", "Simav",
    "Siverek", "Soma", "Söke", "Sultanbeyli", "Sultangazi",
    "Sungurlu", "Sürmene", "Şahinbey", "Şehitkamil", "Şile",
    "Şişli", "Tarsus", "Tatvan", "Tavşanlı", "Tekkeköy",
    "Terme", "Tire", "Tirebolu", "Torbalı", "Tosya",
    "Turhal", "Tuzla", "Urla", "Uzunköprü", "Ümraniye",
    "Ünye", "Üsküdar", "Vakfıkebir", "Vezirköprü", "Viranşehir",
    "Yalvaç", "Yenimahalle", "Yerköy", "Yıldırım", "Yomra",
    "Yüksekova", "Zeytinburnu", "Zile"
]

# ---------------------------------------------------------------------------
# 3. WORLD CITIES (Capitals and prominent global metropolitan centers)
# ---------------------------------------------------------------------------
WORLD_CITIES = [
    "Abu Dabi", "Abuja", "Akra", "Almatı", "Amman", "Amsterdam",
    "Anvers", "Aşkabat", "Astana", "Asuncion", "Atina", "Auckland",
    "Bağdat", "Bakü", "Bangkok", "Banja Luka", "Barselona", "Basel",
    "Batum", "Beyrut", "Pekin", "Belgrad", "Berlin", "Bern",
    "Bişkek", "Bogota", "Bordeaux", "Boston", "Bratislava", "Brazzavil",
    "Brisbane", "Brüksel", "Budapeşte", "Buenos Aires", "Bükreş",
    "Bursa", "Cakarta", "Calgary", "Canberra", "Cape Town", "Caracas",
    "Cenevre", "Cezayir", "Chicago", "Cidde", "Dakar", "Dallas",
    "Şam", "Darüsselam", "Delhi", "Denver", "Detroit", "Doha",
    "Dresden", "Dubai", "Dublin", "Dubrovnik", "Duşanbe", "Düsseldorf",
    "Edinburgh", "Edmonton", "Erevan", "Erivan", "Frankfurt", "Gaza",
    "Gazze", "Gdansk", "Gence", "Gize", "Glasgow",
    "Göteborg", "Hamburg", "Hannover", "Hanoi", "Harkiv", "Hartum",
    "Havana", "Helsinki", "Hiroşima", "Ho Chi Minh", "Hong Kong", "Houston",
    "Hyderabad", "İslamabad", "İsfahan", "İskenderiye", "Jaipur", "Kabil",
    "Kahire", "Kalküta", "Karaçi", "Kazablanka", "Kazan", "Kiev",
    "Kigali", "Köln", "Kopenhag", "Krakow", "Kuala Lumpur", "Kudüs",
    "Kuveyt", "Kyoto", "Lagos", "Lahor", "Larnaka", "Las Vegas",
    "Leipzig", "Lille", "Lima", "Limassol", "Lizbon", "Ljubljana",
    "Lodz", "Londra", "Los Angeles", "Lozan", "Lüksemburg", "Lviv",
    "Lyon", "Madrid", "Malakka", "Málaga", "Managua", "Manama",
    "Manchester", "Manila", "Marakeş", "Marseille", "Maskat", "Medellin",
    "Medine", "Mekke", "Melbourne", "Meksiko", "Miami", "Milano",
    "Minsk", "Mogadişu", "Mombasa", "Monako", "Montevideo", "Montreal",
    "Moskova", "Mostar", "Mumbai", "Münih", "Nagasaki", "Nagoya",
    "Nairobi", "Napoli", "New York", "Nice", "Nikosia", "Novosibirsk",
    "Nürnberg", "Odesa", "Ohrid", "Ohri", "Osaka", "Oslo", "Ottawa",
    "Oxford", "Palermo", "Paris", "Pattaya", "Perth",
    "Philadelphia", "Phnom Penh", "Phuket", "Pisa", "Podgorica", "Porto",
    "Prag", "Pretoria", "Priştine", "Prizren", "Pusan", "Quebec",
    "Quito", "Rabat", "Reykjavik", "Riyad", "Rio de Janeiro", "Roma",
    "Rotterdam", "Salzburg", "Samara", "San Diego", "San Francisco",
    "San Jose", "Sankt-Peterburg", "Santiago", "Saraybosna", "Seattle",
    "Semerkant", "Seul", "Sevilla", "Sidney", "Singapur", "Sofya",
    "Split", "St. Louis", "Stockholm", "Strazburg", "Stuttgart", "Suva",
    "Şanghay", "Şarika", "Şenzen", "Tahran", "Taipei", "Tallinn",
    "Tanca", "Taşkent", "Tbilisi", "Tiflis", "Tegucigalpa", "Tel Aviv",
    "Tiran", "Tokyo", "Toronto", "Trablus", "Trablusşam", "Túnez",
    "Tunus", "Torino", "Ulan Batur", "Üsküp", "Valensiya", "Valletta",
    "Vancouver", "Varşova", "Venedik", "Victoria", "Viyana", "Vilnius",
    "Vladivostok", "Washington", "Wellington", "Winnipeg", "Wrocław",
    "Yafa", "Yangon", "Yekaterinburg", "Yokohama", "Zagreb",
    "Zürih"
]

# ---------------------------------------------------------------------------
# 4. GLOBAL POPULAR BRANDS
# ---------------------------------------------------------------------------
GLOBAL_BRANDS = [
    # Tech & Software
    "Apple", "Microsoft", "Google", "Amazon", "Meta", "Facebook", "Instagram",
    "WhatsApp", "Twitter", "TikTok", "YouTube", "Netflix", "Spotify",
    "LinkedIn", "Telegram", "Reddit", "Pinterest", "Twitch", "Discord",
    "Snapchat", "Skype", "Zoom", "Uber", "Airbnb", "Tinder", "Shazam",
    "GitHub", "GitLab", "OpenAI", "ChatGPT", "Claude", "Gemini",
    "Android", "iOS", "Windows", "Linux", "Ubuntu", "Debian", "macOS",
    "Chrome", "Firefox", "Safari", "Edge", "Opera", "Adobe", "Photoshop",
    "Illustrator", "Premiere", "InDesign", "AutoCAD", "Figma", "Canva",
    "Notion", "Slack", "Trello", "Jira", "Asana", "Dropbox", "OneDrive",
    "iCloud", "Gmail", "Outlook", "Yahoo", "Hotmail", "Yandex", "Baidu",
    "Tencent", "WeChat", "Alibaba", "AliExpress", "AWS", "Azure",
    "Cloudflare", "Oracle", "SAP", "Salesforce", "IBM", "Cisco", "VMware",
    "Docker", "Kubernetes", "Nvidia", "GeForce", "Intel", "AMD", "Ryzen",
    "Radeon", "Qualcomm", "Snapdragon", "MediaTek", "TSMC", "Foxconn",
    "Sony", "PlayStation", "Nintendo", "Xbox", "Sega", "Atari", "Capcom",
    "Konami", "Ubisoft", "Blizzard", "Activision", "Riot Games", "Epic Games",
    "Steam", "Valve", "Bethesda", "Rockstar Games", "Roblox",
    # Hardware & Electronics
    "Samsung", "LG", "Panasonic", "Philips", "Siemens", "Bosch", "Braun",
    "Dyson", "Electrolux", "Whirlpool", "Miele", "Xiaomi", "Huawei",
    "Honor", "Oppo", "Vivo", "Realme", "OnePlus", "Motorola", "Nokia",
    "Lenovo", "Asus", "Acer", "Dell", "HP", "Alienware", "MSI", "Razer",
    "Corsair", "Logitech", "SteelSeries", "Kingston", "SanDisk",
    "Western Digital", "Seagate", "Crucial", "Gigabyte", "ASRock", "Zotac",
    "BenQ", "ViewSonic", "AOC", "Canon", "Nikon", "Fujifilm", "Olympus",
    "Leica", "Hasselblad", "GoPro", "DJI", "Bose", "Sennheiser", "JBL",
    "Harman Kardon", "Bang & Olufsen", "Marshall", "Beats", "Shure",
    "Pioneer", "Denon", "Yamaha", "Roland", "Casio", "Korg",
    # Automotive
    "BMW", "Mercedes", "Mercedes-Benz", "Audi", "Volkswagen", "Porsche",
    "Opel", "Ford", "Chevrolet", "Cadillac", "GMC", "Dodge", "Chrysler",
    "Jeep", "Ram", "Lincoln", "Tesla", "Toyota", "Lexus", "Honda",
    "Acura", "Nissan", "Infiniti", "Mazda", "Subaru", "Mitsubishi",
    "Suzuki", "Isuzu", "Hyundai", "Kia", "Genesis", "Renault", "Peugeot",
    "Citroën", "DS", "Dacia", "Fiat", "Alfa Romeo", "Maserati", "Ferrari",
    "Lamborghini", "Lancia", "Abarth", "Iveco", "Volvo", "Scania", "Saab",
    "Koenigsegg", "Skoda", "Seat", "Cupra", "Land Rover", "Range Rover",
    "Jaguar", "Mini", "Aston Martin", "Bentley", "Rolls-Royce", "McLaren",
    "Lotus", "Bugatti", "BYD", "Chery", "Geely", "MG",
    # Fashion & Luxury & Footwear
    "Nike", "Adidas", "Puma", "Reebok", "Under Armour", "New Balance",
    "Asics", "Converse", "Vans", "Skechers", "Fila", "Champion",
    "Columbia", "The North Face", "Patagonia", "Salomon", "Timberland",
    "Dr. Martens", "Birkenstock", "Crocs", "Ugg", "Zara", "H&M", "Mango",
    "Bershka", "Pull&Bear", "Stradivarius", "Massimo Dutti", "Oysho",
    "Cos", "Uniqlo", "Gap", "Levi's", "Wrangler", "Lee", "Diesel",
    "Calvin Klein", "Tommy Hilfiger", "Ralph Lauren", "Lacoste", "Gant",
    "Fred Perry", "Barbour", "Benetton", "Guess", "Michael Kors", "Coach",
    "Gucci", "Prada", "Miu Miu", "Louis Vuitton", "Dior", "Chanel",
    "Hermès", "Saint Laurent", "Balenciaga", "Bottega Veneta", "Celine",
    "Fendi", "Givenchy", "Valentino", "Burberry", "Versace",
    "Dolce & Gabbana", "Armani", "Emporio Armani", "Hugo Boss", "Boss",
    "Kenzo", "Off-White", "Moncler", "Tom Ford", "Rolex", "Omega",
    "Breitling", "TAG Heuer", "Cartier", "Patek Philippe", "Audemars Piguet",
    "IWC", "Hublot", "Tissot", "Swatch", "Seiko", "Citizen", "G-Shock",
    "Fossil", "Ray-Ban", "Oakley", "Persol", "Pandora", "Swarovski",
    "Tiffany", "Bulgari",
    # Beauty & Cosmetics
    "L'Oréal", "Maybelline", "Garnier", "Lancôme", "Kiehl's", "Estée Lauder",
    "Clinique", "MAC", "Bobbi Brown", "La Mer", "NARS", "Shiseido",
    "Clarins", "Sephora", "Nivea", "Dove", "Rexona", "Axe", "Lux",
    "Palmolive", "Colgate", "Sensodyne", "Oral-B", "Gillette",
    "Head & Shoulders", "Pantene", "Always", "Kotex", "Durex", "Neutrogena",
    "Listerine", "Bioderma", "La Roche-Posay", "Vichy", "CeraVe", "Avène",
    # Food & Beverage
    "Coca-Cola", "Coke", "Fanta", "Sprite", "Schweppes", "Cappy", "Fuze Tea",
    "Monster", "Burn", "Pepsi", "7Up", "Mirinda", "Mountain Dew", "Lipton",
    "Tropicana", "Red Bull", "Nescafé", "Nespresso", "Starbucks",
    "Costa Coffee", "Lavazza", "Illy", "Tchibo", "Jacobs", "McDonald's",
    "Burger King", "KFC", "Subway", "Domino's", "Pizza Hut", "Papa John's",
    "Little Caesars", "Wendy's", "Taco Bell", "Dunkin'", "Krispy Kreme",
    "Nestlé", "KitKat", "Smarties", "Danone", "Activia", "Ferrero",
    "Nutella", "Kinder", "Tic Tac", "Raffaello", "Mars", "Snickers",
    "Twix", "Bounty", "Milky Way", "M&M's", "Skittles", "Orbit",
    "Mondelez", "Oreo", "Milka", "Toblerone", "Cadbury", "Tuc", "Ritz",
    "Haribo", "Chupa Chups", "Mentos", "Lindt", "Godiva", "Ritter Sport",
    "Barilla", "Knorr", "Hellmann's", "Heinz", "Tabasco", "Calvé",
    "Lay's", "Doritos", "Ruffles", "Cheetos", "Pringles", "Kellogg's",
    "Corn Flakes", "Heineken", "Carlsberg", "Budweiser", "Corona",
    "Stella Artois", "Guinness", "Tuborg", "Amstel", "Peroni", "Efes",
    "Johnnie Walker", "Chivas Regal", "Jack Daniel's", "Jameson",
    "Smirnoff", "Absolut", "Bacardi", "Captain Morgan", "Baileys",
    "Jägermeister", "Campari", "Martini",
    # Retail & Home & Transport & Finance
    "Ikea", "Jysk", "Bauhaus", "Leroy Merlin", "Decathlon", "Foot Locker",
    "Carrefour", "Metro", "Costco", "Walmart", "Target", "Best Buy",
    "Harrods", "Marks & Spencer", "Primark", "DHL", "FedEx", "UPS",
    "Booking.com", "TripAdvisor", "Expedia", "Skyscanner", "Hertz",
    "Avis", "Sixt", "Budget", "Visa", "Mastercard", "Maestro",
    "American Express", "Amex", "PayPal", "Western Union", "Revolut",
    "Wise", "Stripe", "HSBC", "Citibank", "BNP Paribas", "Deutsche Bank",
    "Disney", "Warner Bros", "Universal", "Marvel", "HBO", "CNN", "BBC", "Reuters"
]

# ---------------------------------------------------------------------------
# 5. TURKISH POPULAR BRANDS
# ---------------------------------------------------------------------------
TURKISH_BRANDS = [
    # E-Commerce & Apps & Tech
    "Turkcell", "Vodafone", "Türk Telekom", "TurkNet", "Millenicom", "Netmaster",
    "Kablonet", "TTNET", "Trendyol", "Hepsiburada", "Getir", "Yemeksepeti",
    "Sahibinden", "N11", "ÇiçekSepeti", "Morhipo", "Dolap", "Gardrops",
    "Letgo", "Modanisa", "Sefamerve", "Kitapyurdu", "D&R", "İdefix",
    "BKM Kitap", "Enpara", "Papara", "Tosla", "Pokus", "Hadi", "İyziCo",
    "Paycell", "FastPay", "BtcTurk", "Paribu", "Bitexen", "Midas",
    "Insider", "Peak Games", "Dream Games", "TaleWorlds", "Gram Games",
    "Onedio", "Webtekno", "ShiftDelete", "DonanımHaber", "Ekşi Sözlük",
    # Appliances & Manufacturing
    "Arçelik", "Beko", "Vestel", "Profilo", "Altus", "Regal", "Simfer",
    "Kumtel", "Luxell", "Silverline", "Arnica", "Arzum", "Korkmaz",
    "Fakir", "Sinbo", "King", "Schafer", "Karaca", "Emsan", "Jumbo",
    "Hisar", "Nehir", "Güral", "Kütahya Porselen", "Porland", "Paşabahçe",
    "Nude", "Lav", "Borcam",
    # Food & Beverage & Supermarkets
    "Ülker", "Eti", "Şölen", "Torku", "Tadelle", "Sarelle", "Sagra",
    "Fiskobirlik", "Bifa", "Kent", "Olips", "Jelibon", "Tofita", "Falım",
    "Tipitip", "First", "Vivident", "Sütaş", "Pınar", "İçim", "SEK",
    "Yörsan", "Eker", "Dost", "Aynes", "Kaanlar", "Muratbey", "Tahsildaroğlu",
    "Bahçıvan", "Kebir", "Ekici", "Teksüt", "Marmarabirlik", "Tariş",
    "Komili", "Yudum", "Kristal", "Orkide", "Biryağ", "Olin", "Kırlangıç",
    "Banvit", "Şenpiliç", "Beypiliç", "Gedik", "Erpiliç", "Keskinoğlu",
    "Lezita", "Hastavuk", "Aytaç", "Maret", "Namet", "Danet", "Polonez",
    "Cumhuriyet Sucukları", "Şahin Sucukları", "Apikoğlu", "Tat", "Tukaş",
    "Dardanel", "Burcu", "Penguen", "Berrak", "Kemal Kükrer", "Bağdat Baharat",
    "Arifoğlu", "Doğuş Çay", "Çaykur", "Ofçay", "Tirebolu 42", "Doğadan",
    "Mehmet Efendi", "Kurukahveci Mehmet Efendi", "Kocatepe", "Kahve Dünyası",
    "Espressolab", "Hafız Mustafa", "Koska", "Hacı Bekir", "Güllüoğlu",
    "Karaköy Güllüoğlu", "Faruk Güllüoğlu", "Seyidoğlu", "Mado", "Özsüt",
    "Saray Muhallebicisi", "Pelit", "Divan", "Emirgan Sütiş",
    "Bolulu Hasan Usta", "Simit Sarayı", "Baydöner", "HD İskender",
    "Köfteci Yusuf", "Köfteci Ramiz", "Tavuk Dünyası", "Dürümle",
    "Komagene", "Oses", "Battalbey", "Big Chefs", "Midpoint", "Cookshop",
    "Happy Moon's", "Huqqa", "Nusr-Et", "Günaydın", "Kaşıbeyaz", "Develi",
    "Uludağ Gazozu", "Beypazarı", "Kızılay", "Sarıkız", "Erikli", "Hayat Su",
    "Damla Su", "Pınar Su", "Sırma", "Saka", "Taşkesti", "Abant Su",
    "Buzdağı", "Hamidiye", "Efes Pilsen", "Bomonti", "Yeni Rakı",
    "Tekirdağ Rakısı", "Kulüp Rakısı", "Altınbaş", "Beylerbeyi", "Efe Rakı",
    "Kayra", "Doluca", "Kavaklıdere", "Pamukkale Şarapları", "Sevilen",
    "Suvla", "Diren", "Corvus", "Chamlija", "Büyülübağ", "Turasan",
    "Migros", "Macrocenter", "BİM", "A101", "Şok", "CarrefourSA",
    "Bizim Toptan", "File", "Hakmar", "Happy Center", "Onur Market",
    "Kim Market", "Pehlivanoğlu", "Tekzen", "Koçtaş", "Vatan Bilgisayar",
    "MediaMarkt", "Teknosa", "İtopya", "Sinerji", "İncehesap",
    # Fashion & Retail
    "LC Waikiki", "LCW", "DeFacto", "Koton", "Mavi", "Flo", "Vakko",
    "Sarar", "Kiğılı", "Ramsey", "Beymen", "Network", "Divarese",
    "İpekyol", "Twist", "Machka", "Yargıcı", "D'S Damat", "Altınyıldız",
    "Colin's", "LTB", "Loft", "Mudo", "Boyner", "YKM", "Çetinkaya",
    "Greyder", "Derimod", "Kemal Tanca", "İnci", "Hotiç", "Elle",
    "Bambi", "Polaris", "Kinetix", "Lumberjack", "Muya", "Ceyo", "Gezer",
    "Penti", "Suwen", "Dagi", "Kom", "Yeni İnci", "English Home",
    "Madame Coco", "Linens", "Özdilek", "Taç", "Yataş", "Enza Home",
    "Doğtaş", "Kelebek", "Bellona", "İstikbal", "Mondi", "Kilim Mobilya",
    "İdaş", "İşbir Yatak", "Vivense",
    # Automotive & Petroleum & Industry & Defense
    "TOGG", "Tofaş", "Oyak Renault", "Ford Otosan", "BMC", "Otokar",
    "Karsan", "Temsa", "Anadolu Isuzu", "TürkTraktör", "Tümosan",
    "Petlas", "Lassa", "Brisa", "Mutlu Akü", "İnci Akü", "Yiğit Akü",
    "Tüpraş", "Petkim", "Petrol Ofisi", "Opet", "Sunpet", "Aytemiz",
    "Alpet", "Moil", "TP", "Türkiye Petrolleri", "Shell", "BP", "Total",
    "Aselsan", "Havelsan", "Roketsan", "TUSAŞ", "TAI", "TEI", "Baykar",
    "STM", "FNSS", "Meteksan", "Katmerciler", "Canik", "Sarsılmaz",
    "MKE", "Şişecam", "Erdemir", "İsdemir", "Kardemir", "İçdaş",
    "Tosyalı", "Borusan", "Çimsa", "Akçansa", "Enka", "Tekfen",
    "Rönesans", "Limak", "Cengiz", "Kolin", "Kalyon", "Çalık", "Kibar",
    "Sanko", "Gama", "Alarko", "Nurol", "Yapı Merkezi", "STFA", "TOKİ",
    "Emlak Konut", "Koç", "Sabancı", "Eczacıbaşı", "Zorlu", "Doğuş Grubu",
    # Banks & Insurance
    "İş Bankası", "Türkiye İş Bankası", "Garanti", "Garanti BBVA", "Akbank",
    "Yapı Kredi", "Ziraat Bankası", "Ziraat", "Halkbank", "VakıfBank",
    "QNB", "QNB Finansbank", "TEB", "DenizBank", "Şekerbank", "Fibabanka",
    "Odeabank", "Burgan Bank", "ICBC", "Aktif Bank", "Albaraka",
    "Albaraka Türk", "Kuveyt Türk", "Türkiye Finans", "Emlak Katılım",
    "Vakıf Katılım", "Ziraat Katılım", "Allianz", "Aksigorta",
    "Anadolu Sigorta", "Türkiye Sigorta", "Borsa İstanbul", "BIST",
    # Airlines & Travel & Media
    "THY", "Türk Hava Yolları", "Turkish Airlines", "Pegasus", "SunExpress",
    "AJet", "AnadoluJet", "Corendon", "Yurtiçi Kargo", "Aras Kargo",
    "MNG Kargo", "Sürat Kargo", "PTT Kargo", "Kolay Gelsin", "HepsiJet",
    "Trendyol Express", "Kamil Koç", "Pamukkale", "Metro Turizm", "Varan",
    "Nilüfer", "Ulusoy", "Martı", "BinBin", "Hop", "TRT", "ATV", "Kanal D",
    "Star TV", "Show TV", "Fox TV", "NOW", "TV8", "Haber Global",
    "Habertürk", "NTV", "CNN Türk", "A Haber", "Sözcü TV", "Digiturk",
    "Tivibu", "TV+", "BluTV", "Exxen", "Gain", "Tabii", "Hürriyet",
    "Milliyet", "Sabah", "Sözcü", "Cumhuriyet", "Posta", "Akşam",
    "Yeni Şafak", "BirGün", "Anadolu Ajansı", "İHA", "DHA"
]

# ---------------------------------------------------------------------------
# Specific POS & Attribute Mapping
# ---------------------------------------------------------------------------
ATTR_OVERRIDES = {
    # InverseHarmony (foreign loanwords / thin-l stems requiring front vowel suffixes: Apple'a, Google'a, etc.)
    "Apple": ["InverseHarmony"],
    "Google": ["InverseHarmony"],
    "Intel": ["InverseHarmony"],
    "Dell": ["InverseHarmony"],
    "Chanel": ["InverseHarmony"],
    "Oracle": ["InverseHarmony"],
    "Renault": ["InverseHarmony"],
    "Vestel": ["InverseHarmony"],
    "Turkcell": ["InverseHarmony"],
    "L'Oréal": ["InverseHarmony"],
    "Pilsen": ["InverseHarmony"],

    # NoVoicing (proper stems ending in voiceless stops)
    "Akbank": ["NoVoicing"],
    "AnadoluJet": ["NoVoicing"],
    "Arçelik": ["NoVoicing"],
    "BtcTurk": ["NoVoicing"],
    "ChatGPT": ["NoVoicing"],
    "Chrome": ["NoVoicing"],
    "DenizBank": ["NoVoicing"],
    "Facebook": ["NoVoicing"],
    "Fiat": ["NoVoicing"],
    "Finansbank": ["NoVoicing"],
    "Firefox": ["NoVoicing"],
    "Halkbank": ["NoVoicing"],
    "Koç": ["NoVoicing"],
    "Kuveyt Türk": ["NoVoicing"],
    "Microsoft": ["NoVoicing"],
    "Netflix": ["NoVoicing"],
    "Nike": ["NoVoicing"],
    "Panasonic": ["NoVoicing"],
    "TikTok": ["NoVoicing"],
    "TurkNet": ["NoVoicing"],
    "VakıfBank": ["NoVoicing"],
    "WhatsApp": ["NoVoicing"],
    "Yandex": ["NoVoicing"],
    "YouTube": ["NoVoicing"],
    "Ziraat": ["NoVoicing"],
    "Şok": ["NoVoicing"],
}

# Explicit blacklist of noisy strings to guarantee they never enter
EXPLICIT_BLACKLIST = {
    "COCUKLARI", "COCUKLAR", "Cagatay", "Goya", "Orban", "Lele", "Sylvia",
    "Gillars", "Bauer", "Schweitzer", "Fyodorov", "Corrigan", "Legolas",
    "Leia", "Lennon", "Rutkay", "Gulten", "Ildiz", "DINCER", "BAHCESEHIR",
    "HINDISTAN", "ZIRAAT", "IADELERI", "IDARESI", "MEKANA", "BAHSI",
    "ZASYON", "UKUROVA", "NADOLU", "UHALEFET", "ZIL", "CABRIO", "Pazu",
    "Linoleik", "Nöroblastom", "Legionella", "Leishmania"
}


def build_curated_names():
    all_names = set()
    all_names.update(COUNTRIES)
    all_names.update(TURKISH_PROVINCES)
    all_names.update(TURKISH_DISTRICTS)
    all_names.update(WORLD_CITIES)
    all_names.update(GLOBAL_BRANDS)
    all_names.update(TURKISH_BRANDS)

    # Filter out blacklisted or empty
    cleaned_entries = []
    seen = set()

    for name in sorted(all_names):
        name = name.strip()
        if not name or name in EXPLICIT_BLACKLIST or name in seen:
            continue
        seen.add(name)

        attrs = ATTR_OVERRIDES.get(name, [])
        cleaned_entries.append({
            "lemma": name,
            "pos": "ProperNoun",
            "attributes": attrs
        })

    # Sort deterministically by lemma
    cleaned_entries.sort(key=lambda x: x["lemma"])
    return cleaned_entries


def main():
    entries = build_curated_names()
    print(f"Generated {len(entries)} curated proper nouns (countries, cities, popular brands).")

    # Verify no blacklisted items present
    lemmas = {e["lemma"] for e in entries}
    for b in EXPLICIT_BLACKLIST:
        assert b not in lemmas, f"Blacklisted item leaked: {b}"

    # Verify key samples present
    assert "Türkiye" in lemmas
    assert "Almanya" in lemmas
    assert "Ankara" in lemmas
    assert "İstanbul" in lemmas
    assert "Londra" in lemmas
    assert "Apple" in lemmas
    assert "Google" in lemmas
    assert "Arçelik" in lemmas
    assert "Trendyol" in lemmas
    assert "BİM" in lemmas

    # Ensure backup exists
    if not BACKUP_PATH.exists() and NAMES_PATH.exists():
        import shutil
        shutil.copyfile(NAMES_PATH, BACKUP_PATH)
        print(f"Created backup at {BACKUP_PATH}")

    # Write out clean lexicon
    with open(NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Successfully wrote {len(entries)} entries to {NAMES_PATH}")


if __name__ == "__main__":
    main()

