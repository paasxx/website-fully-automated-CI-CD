from typing import Optional

# (name, hex_color, keywords)
# All keywords lowercase — description is lowercased before matching, so case is irrelevant.
# Order matters: first match wins. "Other" must be last (no keywords = never matches, is the fallback).
# This list is the single source of truth for default category names + colors:
# default_categories() derives the per-user seed from it, and categorize() matches against it.
CATEGORY_RULES = [
    ("Food", "#ef5350", [
        # Delivery / apps
        "ifood", "rappi", "ze delivery", "daki",
        # Fast food / chains — PT + EN
        "mcdonalds", "mc donald", "burger king", "subway", "outback", "coco bambu",
        "giraffas", "madero", "jeronimo", "bob's", "bobs", "five guys", "shake shack",
        "kfc", "taco bell", "chipotle", "chili's", "chilis",
        # Cafés / cafeterias
        "starbucks", "dunkin", "padaria", "bakery", "cafe", "coffee", "cafeteria",
        # Restaurantes / genérico — PT + EN
        "restaurante", "restaurant", "pizzaria", "pizza", "sushi", "churrascaria",
        "lanchonete", "bistro", "grill", "kitchen", "eatery", "dining",
        "acai", "sorvete", "gelato", "ice cream",
        # Mercados / supermercados
        "supermercado", "supermarket", "pao de acucar", "extra", "carrefour",
        "atacadao", "assai", "hortifruti", "mercado", "grocery", "whole foods",
        "trader joe", "costco", "walmart", "sams club", "aldi", "lidl",
        "hirota", "big mais", "primicia", "paes e doces", "giroil",
    ]),
    ("Transport", "#42a5f5", [
        # Ride-hailing
        "uber", "99app", "99 taxi", "99taxi", "cabify", "indriver", "lyft",
        # Combustível / postos
        "shell", "posto ", "combustivel", "gasolina", "etanol", "fuel", "gas station",
        "ipiranga", "br distribuidora", "ale", "petrobras dist",
        # Estacionamento / pedágio
        "estacionamento", "parking", "pedagio", "toll", "semparar", "veloe", "conectcar",
        # Transporte público
        "bilhete unico", "metro", "onibus", "sptrans", "brt", "transit", "subway pass",
        # Manutenção veicular
        "mecanica", "oficina", "borracharia", "autopeca", "auto peca", "lubrificante",
        "revisao", "funilaria", "ruella",
        # Outros
        "buser", "uber eats",  # Uber Eats cai aqui só se não houver match em Alimentação antes
    ]),
    ("Health", "#66bb6a", [
        # Farmácias
        "farmacia", "pharmacy", "drugstore", "drogasil", "droga raia", "ultrafarma",
        "drogaria", "pague menos", "raia", "pacheco", "cvs", "walgreens", "boots",
        # Médico / clínicas
        "hospital", "clinica", "clinic", "dentista", "dentist", "medico", "doctor",
        "laboratorio", "laboratory", "lab ", "exame", "exam", "checkup",
        # Planos de saúde
        "unimed", "amil", "bradesco saude", "sulamerica", "hapvida", "notredame",
        "health insurance", "dental plan",
        # Fitness / bem-estar
        "gympass", "smart fit", "academia", "wellhub", "bluefit", "bio ritmo",
        "gym", "fitness", "wellness", "yoga", "pilates",
        # Ótica / veterinário / vacinação
        "otica", "oticas", "optica", "oculos", "lentes", "zerezes",
        "veterinario", "vet ", "hosp vet", "petshop", "pet shop", "vitalpet",
        "imunizacao", "vacina", "tech immune",
    ]),
    ("Entertainment", "#ab47bc", [
        # Streaming — video
        "netflix", "amazon prime", "disney", "hbo max", "hbo ", "apple tv",
        "paramount", "globoplay", "telecine", "crunchyroll", "mubi", "hulu",
        # Streaming — música
        "spotify", "apple music", "deezer", "tidal", "youtube music", "amazon music",
        # Games
        "steam", "playstation", "xbox", "nintendo", "ea play", "epic games",
        "battle.net", "gog ", "humble bundle", "nuuvem",
        # Social / video
        "youtube", "twitch",
        # Cinema / shows / eventos
        "cinema", "cinemark", "kinoplex", "uci cinema", "teatro", "theater",
        "ingresso", "ticket", "ticketmaster", "sympla", "eventbrite", "livenation",
        "show ", "concert", "festival",
    ]),
    ("Shopping", "#ffa726", [
        # Marketplaces
        "amazon", "mercado livre", "shopee", "americanas", "casas bahia",
        "magazine luiza", "magalu", "submarino", "aliexpress", "ali express",
        "ali-express", "shein", "wish ", "ebay", "etsy", "enjoei",
        "olx", "casar.com", "panini",
        # Moda
        "zara", "riachuelo", "renner", "c&a", "hering", "marisa", "lupo",
        "h&m", "uniqlo", "gap ", "forever21", "farm ", "reserva", "aramis",
        # Esporte / eletrônicos
        "centauro", "decathlon", "netshoes", "kabum", "ka bu m", "terabyte", "pichau",
        "best buy", "apple store", "samsung store",
        # Shopping (genérico — pega "CP PARC SHOPPING INTER" e similares)
        "shopping",
        # Genérico
        "store", "shop ", "loja", "outlet",
    ]),
    ("Housing", "#78909c", [
        # Aluguel / condomínio
        "aluguel", "rent", "condominio", "iptu", "taxa condominial",
        # Utilities — PT
        "enel ", "sabesp", "cedae", "copasa", "comgas", "embasa", "caema",
        "energia eletrica", "conta de luz", "conta de agua", "gas encanado",
        # Utilities — EN
        "electricity", "water bill", "gas bill", "utility", "utilities",
        # Internet / TV cabo
        "net ", "claro net", "sky ", "oi fibra", "vivo fibra", "cable", "broadband",
    ]),
    ("Services", "#26c6da", [
        # Telefonia / internet
        "claro ", "vivo ", "tim ", "oi ", "giga ", "nextel",
        "at&t", "verizon", "t-mobile", "vodafone", "orange",
        # Cloud / software
        "google one", "icloud", "dropbox", "microsoft 365", "adobe", "notion",
        "figma", "canva", "1password", "nordvpn", "expressvpn",
        "claude", "anthropic", "tradingview",
        # Tarifas bancárias
        "tarifa", "anuidade", "taxa ", "juros", "bank fee", "monthly fee",
        "service fee", "maintenance fee",
        # Seguros
        "seguro", "porto seguro", "bb seguro", "tokio marine", "zurich",
        "insurance", "assurance",
    ]),
    ("Education", "#8d6e63", [
        # Plataformas — PT
        "udemy", "coursera", "alura", "descomplica", "rocketseat", "dio ",
        "hotmart", "eduzz", "kiwify",
        # Plataformas — EN
        "skillshare", "pluralsight", "linkedin learning", "masterclass",
        "khan academy", "duolingo", "babbel",
        # Instituições
        "escola", "school", "faculdade", "college", "universidade", "university",
        "curso", "course", "treinamento", "training", "workshop",
        # Livros / conteúdo
        "livraria", "bookstore", "amazon kindle", "kindle", "saraiva", "cultura",
        "barnes", "book ", "estante v", "estante virtual",
    ]),
    ("Travel", "#5c6bc0", [
        # Hospedagem
        "airbnb", "booking", "hotel", "pousada", "hostel", "resort",
        "trivago", "decolar", "hotels.com", "expedia", "vrbo",
        # Aéreo
        "latam", "gol ", "azul ", "american airlines", "tap ", "copa airlines",
        "delta", "united", "british airways", "emirates", "lufthansa", "iberia",
        "airline", "airfare", "flight",
        # Aeroporto / viagem
        "aeroporto", "airport", "passagem", "travel", "viagem", "cruise", "navio",
    ]),
    ("Other", "#757575", []),
]

# Name of the fallback category. It is protected (locked) on the frontend and in the
# delete view: deleted categories reassign their transactions to it, so it must always exist.
FALLBACK_CATEGORY = "Other"


def default_categories():
    """
    (name, color) pairs used to seed a new user's categories on registration.
    Derived from CATEGORY_RULES so there is a single source of truth for names/colors.
    """
    return [(name, color) for name, color, _ in CATEGORY_RULES]


def categorize(description: str, categories: dict) -> Optional[object]:
    """
    Match description against keyword rules and return the corresponding Category instance.
    `categories` must be a dict mapping category name → Category model instance.
    Returns the "Other" category when no keyword matches, or None if "Other" is not seeded.
    """
    desc_lower = description.lower()
    for name, _, keywords in CATEGORY_RULES:
        if keywords and any(kw in desc_lower for kw in keywords):
            return categories.get(name)
    return categories.get(FALLBACK_CATEGORY)
