import csv
import os
import random
import re

# ---------------------------------------------------------------------------
# Base de dados (resultado do scraper)
# ---------------------------------------------------------------------------
_DIR = os.path.dirname(__file__)
_SOURCE_CSV = os.path.join(_DIR, "resultado_scraper.csv")

EDITION_CODE_TO_NAME = {
    "UNL": "Unleashed",
    "SFD": "Spiritforged",
    "OGN": "Origins",
}

EDITION_ALIAS_TO_CODE = {
    "UNL": "UNL",
    "UNLEASHED": "UNL",
    "SFD": "SFD",
    "SPIRITFORGED": "SFD",
    "OGN": "OGN",
    "ORIGINS": "OGN",
}

PRODUCT_RULES = {
    "booster_avulso": {
        "boosters": 1,
        "allowed_editions": {"UNL", "SFD", "OGN"},
        "mini_deck": False,
    },
    "pre_kit": {
        "boosters": 5,
        "allowed_editions": {"UNL", "SFD"},
        "mini_deck": True,
    },
    "boosterbox": {
        "boosters": 24,
        "allowed_editions": {"UNL", "SFD", "OGN"},
        "mini_deck": False,
    },
    "vault": {
        "boosters": 6,
        "allowed_editions": {"UNL"},
        "mini_deck": False,
    },
}

# Exemplo placeholder para o mini-deck do pré-kit.
# Quando os nomes reais forem conhecidos, basta substituir estas listas.
MINI_DECK_OPTIONS = {
    "UNL": [
        "Mini Deck Exemplo 1",
        "Mini Deck Exemplo 2",
        "Mini Deck Exemplo 3",
        "Mini Deck Exemplo 4",
        "Mini Deck Exemplo 5",
        "Mini Deck Exemplo 6",
    ],
    "SFD": [
        "Mini Deck Exemplo 1",
        "Mini Deck Exemplo 2",
        "Mini Deck Exemplo 3",
        "Mini Deck Exemplo 4",
        "Mini Deck Exemplo 5",
        "Mini Deck Exemplo 6",
    ],
}

_BASE_POOL_NAMES = ["Common", "Uncommon", "Rare", "Epic", "Overnumbered", "Alt", "Signed"]
_CARD_POOLS: dict[str, dict[str, list[dict]]] = {}


# ---------------------------------------------------------------------------
# Normalização / parsing
# ---------------------------------------------------------------------------
def _parse_price(value: str) -> float | None:
    v = (value or "").strip()
    if not v:
        return None
    v = v.replace("R$", "").replace(" ", "")
    v = v.replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def _format_currency(value: float | None) -> str:
    if value is None:
        return "-"
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def _normalize_product_key(product_name: str) -> str:
    normalized = (product_name or "").strip().lower().replace("-", "_").replace(" ", "_")
    normalized = normalized.replace("__", "_")
    aliases = {
        "booster_avulso": "booster_avulso",
        "booster_avulsos": "booster_avulso",
        "booster_avulso_": "booster_avulso",
        "boosters_avulsos": "booster_avulso",
        "booster": "booster_avulso",
        "prekit": "pre_kit",
        "pre_kit": "pre_kit",
        "pre_kit_": "pre_kit",
        "booster_box": "boosterbox",
        "boosterbox": "boosterbox",
        "vault": "vault",
    }
    return aliases.get(normalized, normalized)


def _normalize_item_name(item_name: str) -> str:
    name = (item_name or "item").strip().lower().replace(" ", "_")
    safe = "".join(ch for ch in name if ch.isalnum() or ch in {"_", "-"})
    return safe or "item"


def _normalize_edition_code(value: str) -> str:
    token = (value or "").strip().upper().replace(" ", "").replace("-", "")
    return EDITION_ALIAS_TO_CODE.get(token, "")


def _edition_name_from_code(code: str) -> str:
    return EDITION_CODE_TO_NAME.get(code, code)


def _strip_edition_suffix(rarity_text: str) -> tuple[str, str]:
    text = (rarity_text or "").strip()
    match = re.search(r"\(([^()]+)\)\s*$", text)
    if not match:
        return text, ""

    suffix = match.group(1).strip()
    code = _normalize_edition_code(suffix)
    cleaned = text[: match.start()].strip()
    return cleaned, code or suffix.upper()


def _normalize_special_rarity(rarity_text: str, card_name: str) -> str:
    rarity = (rarity_text or "").strip()
    rarity_low = rarity.lower()

    if rarity_low.startswith("showcase"):
        if "signature" in rarity_low:
            return "Signature"
        if "overnumbered" in rarity_low:
            return "Overnumbered"
        if "alternate art" in rarity_low or "alternative art" in rarity_low:
            return "Alternative Art"

        name_low = (card_name or "").lower()
        if "overnumbered" in name_low:
            return "Overnumbered"
        if "signature" in name_low:
            return "Signature"
        return "Alternative Art"

    if rarity_low.startswith("alternate art"):
        return "Alternative Art"

    return rarity


def _base_rarity(rarity_text: str) -> str:
    rarity = (rarity_text or "").strip().lower()
    if rarity.startswith("common"):
        return "Common"
    if rarity.startswith("uncommon"):
        return "Uncommon"
    if rarity.startswith("rare"):
        return "Rare"
    if rarity.startswith("epic"):
        return "Epic"
    if rarity.startswith("overnumbered"):
        return "Overnumbered"
    if rarity.startswith("signature"):
        return "Signed"
    if rarity.startswith("alternative art") or rarity.startswith("alternate art"):
        return "Alt"
    return ""


# ---------------------------------------------------------------------------
# Leitura e agrupamento do CSV
# ---------------------------------------------------------------------------
def _parse_source_row(row: list[str]) -> dict | None:
    if not row:
        return None

    first = row[0].strip().lower()
    if first in {"nome", "booster", "carta"}:
        return None

    while len(row) < 10:
        row.append("")

    nome = row[0].strip()
    cor = row[1].strip()

    if _normalize_edition_code(row[2]):
        edition_code = _normalize_edition_code(row[2])
        raridade_raw = row[3].strip()
        price_start = 4
    else:
        edition_code = ""
        raridade_raw = row[2].strip()
        price_start = 3

    raridade_clean, edition_from_rarity = _strip_edition_suffix(raridade_raw)
    edition_code = edition_code or edition_from_rarity or "UNL"
    edition_name = _edition_name_from_code(edition_code)
    raridade_clean = _normalize_special_rarity(raridade_clean, nome)

    menor_normal = _parse_price(row[price_start])
    medio_normal = _parse_price(row[price_start + 1])
    maior_normal = _parse_price(row[price_start + 2])
    menor_foil = _parse_price(row[price_start + 3])
    medio_foil = _parse_price(row[price_start + 4])
    maior_foil = _parse_price(row[price_start + 5])

    if not nome or not raridade_clean:
        return None

    base = _base_rarity(raridade_clean)
    if not base:
        return None

    name_low = nome.lower()
    rarity_low = raridade_clean.lower()
    is_alt = "alternate art" in name_low or "alternate art" in rarity_low or "alternative art" in rarity_low
    is_signature = "signature" in name_low or "signature" in rarity_low
    is_overnumbered = "overnumbered" in name_low or "overnumbered" in rarity_low

    return {
        "nome": nome,
        "cor": cor,
        "edition_code": edition_code,
        "edition_name": edition_name,
        "raridade": raridade_clean,
        "base": base,
        "is_alt": is_alt,
        "is_signature": is_signature,
        "is_overnumbered": is_overnumbered,
        "menor_normal": menor_normal,
        "medio_normal": medio_normal,
        "maior_normal": maior_normal,
        "menor_foil": menor_foil,
        "medio_foil": medio_foil,
        "maior_foil": maior_foil,
    }


def _build_card_pools() -> None:
    if _CARD_POOLS:
        return

    with open(_SOURCE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            parsed = _parse_source_row(row)
            if parsed is None:
                continue

            edition_code = parsed["edition_code"]
            edition_pools = _CARD_POOLS.setdefault(
                edition_code,
                {pool_name: [] for pool_name in _BASE_POOL_NAMES},
            )

            base = parsed["base"]
            edition_pools[base].append(parsed)

            if base == "Overnumbered":
                # Overnumbered permanece apenas no próprio pool.
                pass
            elif base in {"Rare", "Epic"}:
                if parsed["is_alt"]:
                    edition_pools["Alt"].append(parsed)
                if parsed["is_signature"]:
                    edition_pools["Signed"].append(parsed)


# ---------------------------------------------------------------------------
# Pools / sorteios
# ---------------------------------------------------------------------------
def _pool_search_order(slot_rarity: str) -> list[str]:
    slot = slot_rarity.replace(" Foil", "")
    if slot == "Signed":
        order = ["Signed", "Overnumbered", "Alt", "Epic", "Rare"]
    elif slot == "Overnumbered":
        order = ["Overnumbered", "Signed", "Alt", "Epic", "Rare"]
    elif slot == "Alt":
        order = ["Alt", "Overnumbered", "Epic", "Rare"]
    elif slot == "Epic":
        order = ["Epic", "Rare"]
    elif slot == "Rare":
        order = ["Rare"]
    elif slot == "Uncommon":
        order = ["Uncommon"]
    elif slot == "Common":
        order = ["Common"]
    else:
        order = [slot]

    if slot_rarity.endswith("Foil"):
        order.extend(["Uncommon", "Common"])
    return order


def _get_card(edition_code: str, rarity: str) -> tuple[str, str, str, float | None, float | None, float | None]:
    """Sorteia uma carta da raridade informada, dentro da edição pedida."""
    if rarity == "Token/Rune":
        return "Token/Rune", "Token/Rune", "", None, None, None

    _build_card_pools()
    edition_pools = _CARD_POOLS.get(edition_code)
    if not edition_pools:
        raise ValueError(f"Sem cartas carregadas para a edição {edition_code}.")

    pool = []
    for key in _pool_search_order(rarity):
        candidates = edition_pools.get(key, [])
        if candidates:
            pool = candidates
            break

    if not pool:
        raise ValueError(f"Sem cartas disponíveis para a raridade '{rarity}' na edição {edition_code}.")

    card = random.choice(pool)
    if rarity.endswith("Foil"):
        menor = card["menor_foil"] if card["menor_foil"] is not None else card["menor_normal"]
        medio = card["medio_foil"] if card["medio_foil"] is not None else card["medio_normal"]
        maior = card["maior_foil"] if card["maior_foil"] is not None else card["maior_normal"]
    else:
        menor = card["menor_normal"]
        medio = card["medio_normal"]
        maior = card["maior_normal"]

    return card["raridade"], card["nome"], card["cor"], menor, medio, maior


def _effective_prices(
    rarity: str,
    menor: float | None,
    medio: float | None,
    maior: float | None,
) -> tuple[float | None, float | None, float | None]:
    """Para foil ate raro, considera venda pelo maior preco tambem no calculo de menor."""
    foil_ate_raro = {"Common Foil", "Uncommon Foil", "Rare Foil"}
    if rarity in foil_ate_raro:
        medio_efetivo = medio if medio is not None else maior
        return maior, medio_efetivo, maior
    return menor, medio, maior


# ---------------------------------------------------------------------------
# Probabilidades mantidas
# ---------------------------------------------------------------------------
_RARE_SLOT_THRESHOLDS = [
    (1 / 1440, "Signed"),
    (1 / 1440 + 1 / 144, "Overnumbered"),
    (1 / 1440 + 1 / 144 + 1 / 24, "Alt"),
    (1 / 1440 + 1 / 144 + 1 / 24 + 1 / 8, "Epic"),
]

_FOIL_THRESHOLDS = [
    (0.002, "Signed Foil"),
    (0.010, "Overnumbered Foil"),
    (0.030, "Alt Foil"),
    (0.100, "Epic Foil"),
    (0.300, "Rare Foil"),
    (0.550, "Uncommon Foil"),
]


def _roll_rare_or_better() -> str:
    r = random.random()
    for threshold, rarity in _RARE_SLOT_THRESHOLDS:
        if r < threshold:
            return rarity
    return "Rare"


def _roll_foil() -> str:
    r = random.random()
    for threshold, rarity in _FOIL_THRESHOLDS:
        if r < threshold:
            return rarity
    return "Common Foil"


def _classify_highlights(card_name: str, card_color: str, card_rarity: str) -> dict[str, int]:
    name_low = (card_name or "").lower()
    color_low = (card_color or "").lower()
    rarity_low = (card_rarity or "").lower()

    return {
        "legends": 1 if color_low == "legend" else 0,
        "signature_spells": 1 if color_low == "signature spell" else 0,
        "overnumbered": 1 if "overnumbered" in rarity_low or "overnumbered" in name_low else 0,
        "signature": 1 if "signature" in rarity_low or "signature" in name_low else 0,
        "alternative_art": 1 if "alternative art" in rarity_low or "alternate art" in rarity_low or "alternate art" in name_low else 0,
    }


# ---------------------------------------------------------------------------
# Simulação base de boosters
# ---------------------------------------------------------------------------
def simulate_pack(edition_code: str = "UNL") -> list[tuple[str, str, str, str, float | None, float | None, float | None]]:
    """Simula um booster individual e retorna as cartas sorteadas."""
    cards: list[tuple[str, str, str, str, float | None, float | None, float | None]] = []

    for _ in range(7):
        card_rarity, name, color, menor, medio, maior = _get_card(edition_code, "Common")
        cards.append(("Common", card_rarity, color, name, menor, medio, maior))

    for _ in range(3):
        card_rarity, name, color, menor, medio, maior = _get_card(edition_code, "Uncommon")
        cards.append(("Uncommon", card_rarity, color, name, menor, medio, maior))

    for _ in range(2):
        slot = _roll_rare_or_better()
        card_rarity, name, color, menor, medio, maior = _get_card(edition_code, slot)
        cards.append((slot, card_rarity, color, name, menor, medio, maior))

    foil_slot = _roll_foil()
    card_rarity, name, color, menor, medio, maior = _get_card(edition_code, foil_slot)
    cards.append((foil_slot, card_rarity, color, name, menor, medio, maior))
    cards.append(("Token/Rune", "Token/Rune", "", "Token/Rune", None, None, None))

    return cards


# ---------------------------------------------------------------------------
# Saída / pastas
# ---------------------------------------------------------------------------
def _create_opened_item_folder(item_name: str) -> str:
    base_name = _normalize_item_name(item_name)
    i = 1
    while True:
        candidate = os.path.join(_DIR, f"{base_name}{i}")
        if not os.path.exists(candidate):
            os.makedirs(candidate, exist_ok=True)
            return candidate
        i += 1


def _create_unit_folder(product_folder: str, unit_number: int) -> str:
    unit_folder = os.path.join(product_folder, f"unidade_{unit_number:03d}")
    os.makedirs(unit_folder, exist_ok=True)
    return unit_folder


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
def _validate_product_edition(product_key: str, edition_code: str) -> None:
    product = PRODUCT_RULES.get(product_key)
    if product is None:
        raise ValueError(f"Produto desconhecido: {product_key}")
    if edition_code not in product["allowed_editions"]:
        raise ValueError(f"O produto '{product_key}' nao suporta a edicao {edition_code}.")


def _roll_mini_deck(edition_code: str) -> str:
    options = MINI_DECK_OPTIONS.get(edition_code)
    if not options:
        raise ValueError(f"Sem opcoes de mini-deck para a edicao {edition_code}.")
    return random.choice(options)


def _write_booster_file(
    booster_path: str,
    product_key: str,
    unit_number: int,
    booster_number: int,
    edition_name: str,
    edition_code: str,
    cards: list[tuple[str, str, str, str, float | None, float | None, float | None]],
) -> tuple[float, float, float, dict[str, int], dict[str, list[dict] | dict | None]]:
    booster_total_menor = 0.0
    booster_total_medio = 0.0
    booster_total_maior = 0.0
    booster_counts = {
        "legends": 0,
        "signature_spells": 0,
        "overnumbered": 0,
        "signature": 0,
        "alternative_art": 0,
    }
    booster_details = {
        "legends": [],
        "signature_spells": [],
        "champions": [],
        "most_expensive_card": None,
    }

    with open(booster_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "produto",
            "unidade",
            "booster",
            "carta",
            "slot_raridade",
            "edicao",
            "raridade_carta",
            "cor",
            "nome",
            "menor",
            "medio",
            "maior",
        ])

        for card_number, (slot_rarity, card_rarity, color, name, menor, medio, maior) in enumerate(cards, start=1):
            menor_calc, medio_calc, maior_calc = _effective_prices(slot_rarity, menor, medio, maior)
            highlights = _classify_highlights(name, color, card_rarity)
            for key, value in highlights.items():
                booster_counts[key] += value

            card_info = {
                "unidade": unit_number,
                "booster": booster_number,
                "carta": card_number,
                "nome": name,
                "raridade": card_rarity,
                "cor": color,
                "menor": menor_calc,
                "medio": medio_calc,
                "maior": maior_calc,
            }

            if color == "Legend":
                booster_details["legends"].append(card_info)
            if color == "Signature Spell":
                booster_details["signature_spells"].append(card_info)
            if card_rarity in {"Rare", "Epic"} and " - " in name:
                booster_details["champions"].append(card_info)

            current_max = booster_details["most_expensive_card"]
            if current_max is None or (maior_calc or 0.0) > (current_max["maior"] or 0.0):
                booster_details["most_expensive_card"] = card_info

            row = [
                product_key,
                unit_number,
                booster_number,
                card_number,
                slot_rarity,
                edition_name,
                card_rarity,
                color,
                name,
                menor_calc if menor_calc is not None else "",
                medio_calc if medio_calc is not None else "",
                maior_calc if maior_calc is not None else "",
            ]
            writer.writerow(row)

            booster_total_menor += menor_calc or 0.0
            booster_total_medio += medio_calc or 0.0
            booster_total_maior += maior_calc or 0.0

    return booster_total_menor, booster_total_medio, booster_total_maior, booster_counts, booster_details


def _format_summary_card(card: dict) -> str:
    return (
        f"- U{card['unidade']:03d} B{card['booster']:03d} C{card['carta']:02d}: "
        f"{card['nome']} | {card['raridade']} | {card['cor']} | "
        f"Menor={_format_currency(card['menor'])} | "
        f"Medio={_format_currency(card['medio'])} | "
        f"Maior={_format_currency(card['maior'])}"
    )


def _write_text_summary(
    summary_path: str,
    product_key: str,
    edition_name: str,
    quantity: int,
    boosters_por_produto: int,
    mini_decks: list[str],
    total_menor: float,
    total_medio: float,
    total_maior: float,
    most_expensive_card: dict | None,
    legends: list[dict],
    signature_spells: list[dict],
    champions: list[dict],
) -> None:
    lines = [
        f"Produto: {product_key}",
        f"Edicao: {edition_name}",
        f"Quantidade de unidades: {quantity}",
        f"Boosters por unidade: {boosters_por_produto}",
        f"Preco menor somado: {_format_currency(total_menor)}",
        f"Preco medio somado: {_format_currency(total_medio)}",
        f"Preco maior somado: {_format_currency(total_maior)}",
    ]

    if mini_decks:
        lines.append("Mini-decks sorteados:")
        for index, mini_deck in enumerate(mini_decks, start=1):
            lines.append(f"- Unidade {index:03d}: {mini_deck}")

    lines.append("Carta mais cara:")
    lines.append(_format_summary_card(most_expensive_card) if most_expensive_card else "- Nenhuma")

    sections = [
        ("Signature Spells:", signature_spells),
        ("Legends:", legends),
        ("Champions:", champions),
    ]
    for title, cards in sections:
        lines.append(title)
        if cards:
            for card in cards:
                lines.append(_format_summary_card(card))
        else:
            lines.append("- Nenhuma")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def simulate_product(
    product_name: str,
    edition: str,
    quantity: int = 1,
    opened_item_name: str | None = None,
    output_file: str | None = None,
) -> tuple[float, float, float]:
    """Simula um produto (pre-kit, boosterbox ou vault) de uma edição específica."""
    if quantity <= 0:
        raise ValueError("quantity deve ser maior que zero.")

    product_key = _normalize_product_key(product_name)
    edition_code = _normalize_edition_code(edition)
    if not edition_code:
        raise ValueError(f"Edicao invalida: {edition}")

    _validate_product_edition(product_key, edition_code)
    _build_card_pools()

    edition_name = _edition_name_from_code(edition_code)
    if edition_code not in _CARD_POOLS:
        raise ValueError(f"Nao ha cartas carregadas para a edicao {edition_code}.")

    if opened_item_name:
        folder_base = _normalize_item_name(opened_item_name)
    else:
        folder_base = f"{product_key}_{edition_code.lower()}"

    product_folder = _create_opened_item_folder(folder_base)

    summary_path = os.path.join(product_folder, f"resumo_{product_key}_{edition_code.lower()}.txt")

    total_menor = 0.0
    total_medio = 0.0
    total_maior = 0.0
    boosters_por_produto = PRODUCT_RULES[product_key]["boosters"]
    tem_mini_deck = PRODUCT_RULES[product_key]["mini_deck"]
    usar_subpasta_unidade = quantity > 1
    legends: list[dict] = []
    signature_spells: list[dict] = []
    champions: list[dict] = []
    mini_decks: list[str] = []
    most_expensive_card: dict | None = None

    for unit_number in range(1, quantity + 1):
        if usar_subpasta_unidade:
            unit_folder = _create_unit_folder(product_folder, unit_number)
        else:
            unit_folder = product_folder
        mini_deck_choice = _roll_mini_deck(edition_code) if tem_mini_deck else ""
        if mini_deck_choice:
            mini_decks.append(mini_deck_choice)

        for booster_number in range(1, boosters_por_produto + 1):
            booster_path = os.path.join(unit_folder, f"booster_{booster_number:03d}.csv")
            cards = simulate_pack(edition_code)
            booster_total_menor, booster_total_medio, booster_total_maior, _, booster_details = _write_booster_file(
                booster_path,
                product_key,
                unit_number,
                booster_number,
                edition_name,
                edition_code,
                cards,
            )

            total_menor += booster_total_menor
            total_medio += booster_total_medio
            total_maior += booster_total_maior
            legends.extend(booster_details["legends"])
            signature_spells.extend(booster_details["signature_spells"])
            champions.extend(booster_details["champions"])

            candidate = booster_details["most_expensive_card"]
            if candidate is not None and (
                most_expensive_card is None or (candidate["maior"] or 0.0) > (most_expensive_card["maior"] or 0.0)
            ):
                most_expensive_card = candidate

    _write_text_summary(
        summary_path,
        product_key,
        edition_name,
        quantity,
        boosters_por_produto,
        mini_decks,
        total_menor,
        total_medio,
        total_maior,
        most_expensive_card,
        legends,
        signature_spells,
        champions,
    )

    print(f"Pasta do produto: {product_folder}")
    print(f"Resumo do produto: {summary_path}")
    print(f"Total menor: {_format_currency(total_menor)}")
    print(f"Total medio: {_format_currency(total_medio)}")
    print(f"Total maior: {_format_currency(total_maior)}")

    return total_menor, total_medio, total_maior


# ---------------------------------------------------------------------------
# Compatibilidade com a API antiga
# ---------------------------------------------------------------------------
def simulate_boosters(
    quantity: int,
    output_file: str = "resultado_boosters.csv",
    opened_item_name: str = "booster_box",
    edition: str = "UNL",
) -> tuple[float, float, float]:
    product_key = _normalize_product_key(opened_item_name)
    if product_key not in PRODUCT_RULES:
        product_key = "boosterbox"
    return simulate_product(
        product_key,
        edition,
        quantity=quantity,
        opened_item_name=opened_item_name,
        output_file=output_file,
    )


def simular_varias_caixas(n: int) -> None:
    """Mantido por compatibilidade; simula 24 boosters por caixa na edicao UNL."""
    if n <= 0:
        raise ValueError("n deve ser maior que zero.")

    soma_menor = 0.0
    soma_medio = 0.0
    soma_maior = 0.0
    pad = len(str(n))

    for i in range(1, n + 1):
        total_menor = 0.0
        total_medio = 0.0
        total_maior = 0.0
        for _ in range(24):
            for slot_rarity, _, _, _, menor, medio, maior in simulate_pack("UNL"):
                menor_calc, medio_calc, maior_calc = _effective_prices(slot_rarity, menor, medio, maior)
                total_menor += menor_calc or 0.0
                total_medio += medio_calc or 0.0
                total_maior += maior_calc or 0.0
        soma_menor += total_menor
        soma_medio += total_medio
        soma_maior += total_maior
        print(
            f"  Caixa {i:{pad}}: Menor={_format_currency(total_menor)}  "
            f"Medio={_format_currency(total_medio)}  Maior={_format_currency(total_maior)}"
        )

    media_menor = soma_menor / n
    media_medio = soma_medio / n
    media_maior = soma_maior / n
    print(f"\n{'-' * 50}")
    print(f"Media de {n} caixa(s) (24 boosters cada):")
    print(f"  Menor: {_format_currency(media_menor)}")
    print(f"  Medio: {_format_currency(media_medio)}")
    print(f"  Maior: {_format_currency(media_maior)}")


def _ask_choice(prompt: str, options: list[tuple[str, str]]) -> str:
    while True:
        print(prompt)
        for index, (_, label) in enumerate(options, start=1):
            print(f"{index}. {label}")
        answer = input("> ").strip()
        if answer.isdigit():
            selected = int(answer)
            if 1 <= selected <= len(options):
                return options[selected - 1][0]
        print("Opcao invalida. Tente novamente.\n")


def _ask_positive_int(prompt: str, default: int = 1) -> int:
    while True:
        answer = input(f"{prompt} [{default}]: ").strip()
        if not answer:
            return default
        if answer.isdigit() and int(answer) > 0:
            return int(answer)
        print("Informe um numero inteiro maior que zero.\n")


def _suggest_item_name(product_key: str) -> str:
    suggestions = {
        "booster_avulso": "booster_avulso_",
        "pre_kit": "pre-kit_",
        "boosterbox": "booster_box",
        "vault": "vault_",
    }
    return suggestions.get(product_key, "produto_")


def run_cli() -> None:
    print("Simulador de produtos\n")

    product_key = _ask_choice(
        "Escolha o produto:",
        [
            ("booster_avulso", "Booster Avulso"),
            ("pre_kit", "Pre-Kit"),
            ("boosterbox", "Booster Box"),
            ("vault", "Vault"),
        ],
    )

    allowed_editions = sorted(PRODUCT_RULES[product_key]["allowed_editions"])
    edition_key = _ask_choice(
        "Escolha a edicao:",
        [(code, f"{code} - {_edition_name_from_code(code)}") for code in allowed_editions],
    )

    quantity = _ask_positive_int("Quantidade de unidades", 1)
    default_name = _suggest_item_name(product_key)
    opened_item_name = input(f"Nome base da pasta [{default_name}]: ").strip() or default_name

    print("\nExecutando simulacao...\n")
    simulate_product(
        product_key,
        edition_key,
        quantity=quantity,
        opened_item_name=opened_item_name,
    )


if __name__ == "__main__":
    run_cli()
