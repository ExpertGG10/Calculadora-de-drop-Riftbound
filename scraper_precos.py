import csv
import os
import re
import pyautogui as pag
import pyperclip as ppc

from rpa_base import (
    aguardar,
    aguardar_inicio_processo,
    pressionar_tab,
    pressionar_atalho,
    PararExecucao,
)

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
ARQUIVO_SAIDA = os.path.join(os.path.dirname(__file__), "resultado_scraper.csv")
COLUNAS = [
    "Nome",
    "Cor",
    "Edição",
    "Raridade",
    "Menor Preço Normal",
    "Preço Médio Normal",
    "Maior Preço Normal",
    "Menor Preço Foil",
    "Preço Médio Foil",
    "Maior Preço Foil",
]
EDICAO_CODIGO_PARA_NOME = {
    "UNL": "Unleashed",
    "SFD": "Spiritforged",
    "OGN": "Origins",
}
QUANTIDADE_CARTAS = 100  # ajuste conforme necessário
ABAS_POR_LOTE = 8     # quantas cartas abrir por vez com Ctrl+Enter
TABS_ATE_PRIMEIRO_CARD = 37  # ajuste inicial para focar no primeiro card da lista
PASSO_TAB_ENTRE_CARDS = 4  # tabs entre um card e outro na listagem
TENTATIVAS_LEITURA_ABA = 4
INTERVALO_TENTATIVAS_LEITURA = 1.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _inicializar_csv():
    """Cria o CSV de saída com cabeçalho se ainda não existir."""
    if not os.path.exists(ARQUIVO_SAIDA):
        with open(ARQUIVO_SAIDA, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUNAS)
            writer.writeheader()


def _salvar_linha(dados: dict):
    """Acrescenta uma linha ao CSV de saída."""
    with open(ARQUIVO_SAIDA, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS)
        writer.writerow(dados)


def _capturar_conteudo() -> str:
    """Seleciona tudo (Ctrl+A), copia (Ctrl+C) e retorna o texto da área de transferência."""
    pag.hotkey("ctrl", "a")
    aguardar(0.3)
    pag.hotkey("ctrl", "c")
    aguardar(0.5)
    return ppc.paste()


def _separar_raridade_e_edicao(raridade: str) -> tuple[str, str]:
    """Separa a raridade da edição no sufixo final, por exemplo 'Common (UNL)'."""
    texto = (raridade or "").strip()
    match = re.search(r"\(([^()]+)\)\s*$", texto)
    if not match:
        return texto, ""

    codigo = match.group(1).strip().upper()
    raridade_limpa = texto[: match.start()].strip()
    edicao = EDICAO_CODIGO_PARA_NOME.get(codigo, codigo)
    return raridade_limpa, edicao


def _normalizar_raridade_showcase(raridade: str, nome: str) -> str:
    """Converte raridade Showcase para Overnumbered, Signature ou Alternative Art."""
    if not raridade.lower().startswith("showcase"):
        return raridade

    nome_lower = nome.lower()
    if "overnumbered" in nome_lower:
        return "Overnumbered"
    elif "signature" in nome_lower:
        return "Signature"
    else:
        return "Alternative Art"


def _interpretar_resposta(conteudo: str) -> dict | None:
    """
    Interpreta o texto copiado (Ctrl+A → Ctrl+C) da página de um card e extrai:
    nome, cor, raridade e preços (menor/médio/maior) para Normal e Foil.
    """
    linhas = [l.strip() for l in conteudo.splitlines()]
    linhas = [l for l in linhas if l]  # remove linhas vazias

    # ── Nome ─────────────────────────────────────────────────────────────────
    # O nome aparece na linha imediatamente anterior a "Acompanhar este card"
    nome = ""
    for i, linha in enumerate(linhas):
        if linha == "Acompanhar este card" and i > 0:
            nome = linhas[i - 1]
            break

    # ── Raridade ─────────────────────────────────────────────────────────────
    # Linha imediatamente após "Raridade"
    raridade = ""
    for i, linha in enumerate(linhas):
        if linha == "Raridade" and i + 1 < len(linhas):
            raridade = linhas[i + 1]
            break

    raridade, edicao = _separar_raridade_e_edicao(raridade)
    raridade = _normalizar_raridade_showcase(raridade, nome)

    # ── Cor ──────────────────────────────────────────────────────────────────
    # Linha imediatamente após "Cor"; se ausente, infere pelo tipo de raridade.
    cor = ""
    for i, linha in enumerate(linhas):
        if linha == "Cor" and i + 1 < len(linhas):
            cor = linhas[i + 1]
            break

    if not cor:
        raridade_lower = raridade.lower()
        if raridade_lower.startswith("common"):
            cor = "Token/Energia"
        elif raridade_lower.startswith("uncommon"):
            cor = "Battlefield"
        elif raridade_lower.startswith("rare"):
            cor = "Legend"
        elif raridade_lower.startswith("epic"):
            cor = "Signature Spell"
        elif raridade_lower in {"overnumbered", "signature", "alternative art", "alternate art"}:
            cor = "Legend"

    # ── Preços Normal ─────────────────────────────────────────────────────────
    # Bloco marcado por linha "N" seguida de linha "Normal"; as 3 próximas são
    # menor, médio e maior preço respectivamente.
    menor_normal = preco_medio_normal = maior_normal = ""
    for i, linha in enumerate(linhas):
        if linha == "N" and i + 1 < len(linhas) and linhas[i + 1] == "Normal":
            precos = linhas[i + 2 : i + 5]
            if len(precos) == 3:
                menor_normal, preco_medio_normal, maior_normal = precos
            break

    # ── Preços Foil ───────────────────────────────────────────────────────────
    # Bloco marcado por linha "F" seguida de linha "Foil"; as 3 próximas são
    # menor, médio e maior preço respectivamente.
    menor_foil = preco_medio_foil = maior_foil = ""
    for i, linha in enumerate(linhas):
        if linha == "F" and i + 1 < len(linhas) and linhas[i + 1] == "Foil":
            precos = linhas[i + 2 : i + 5]
            if len(precos) == 3:
                menor_foil, preco_medio_foil, maior_foil = precos
            break

    # Considera valido apenas se encontrar estrutura minima de carta.
    if not nome or not raridade:
        return None
    if not (menor_normal and preco_medio_normal and maior_normal):
        return None

    return {
        "Nome": nome,
        "Cor": cor,
        "Edição": edicao,
        "Raridade": raridade,
        "Menor Preço Normal": menor_normal,
        "Preço Médio Normal": preco_medio_normal,
        "Maior Preço Normal": maior_normal,
        "Menor Preço Foil": menor_foil,
        "Preço Médio Foil": preco_medio_foil,
        "Maior Preço Foil": maior_foil,
    }


def _posicionar_no_primeiro_card_lista():
    """Posiciona o foco no primeiro card da listagem usando tabulação inicial."""
    pressionar_tab(TABS_ATE_PRIMEIRO_CARD)
    aguardar(0.3)


def _limpar_clipboard():
    ppc.copy("")


def _foco_atual_e_carta() -> bool:
    """Sonda o foco na listagem: 2 tabs + Ctrl+C deve copiar '1'."""
    _limpar_clipboard()
    pressionar_tab(2)
    aguardar(0.2)
    pag.hotkey("ctrl", "c")
    aguardar(0.3)
    valor = ppc.paste().strip()
    pressionar_tab(-2)
    aguardar(0.2)
    return valor == "1"


def _abrir_cartas_em_abas_sem_limite() -> int:
    """Abre cartas em segundo plano até encontrar um item que não é carta."""
    abertas = 0
    primeira = True
    while True:
        if not primeira:
            pressionar_tab(PASSO_TAB_ENTRE_CARDS)
            aguardar(0.2)
        else:
            primeira = False

        if not _foco_atual_e_carta():
            break

        pressionar_atalho("ctrl", "enter")
        aguardar(0.5)
        abertas += 1
    return abertas


def _ir_para_ultima_aba():
    """Vai para a ultima aba do navegador."""
    pressionar_atalho("ctrl", "9")
    aguardar(1.0)


def _processar_aba_atual() -> bool:
    """Captura, interpreta e salva apenas se a aba for uma carta valida."""
    for tentativa in range(TENTATIVAS_LEITURA_ABA):
        conteudo = _capturar_conteudo()
        dados = _interpretar_resposta(conteudo)
        if dados is not None:
            _salvar_linha(dados)
            return True

        if tentativa < TENTATIVAS_LEITURA_ABA - 1:
            aguardar(INTERVALO_TENTATIVAS_LEITURA)

    return False


def _processar_abas_abertas(quantidade: int):
    """Processa e fecha abas em sequencia; ao fechar, o navegador vai para a anterior."""
    salvas = 0
    for _ in range(quantidade):
        if _processar_aba_atual():
            salvas += 1
        pressionar_atalho("ctrl", "w")
        aguardar(0.7)
    return salvas


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------
def processar_cartas_em_lotes():
    """Abre cartas em abas até encontrar uma não-carta, processa cada aba e para ao encontrar uma não-carta na leitura."""
    _posicionar_no_primeiro_card_lista()
    abertas = _abrir_cartas_em_abas_sem_limite()
    if abertas == 0:
        return

    # Guarda o total correto de abas abertas para percorrer todas na leitura.
    total_abas_para_ler = abertas
    _ir_para_ultima_aba()
    for _ in range(total_abas_para_ler):
        # Se a aba atual não for carta, apenas ignora e segue para a próxima.
        _processar_aba_atual()
        pressionar_atalho("ctrl", "w")
        aguardar(0.7)


def main():
    _inicializar_csv()

    aguardar_inicio_processo()

    try:
        processar_cartas_em_lotes()
    except PararExecucao:
        print("Execução interrompida pelo usuário.")


if __name__ == "__main__":
    main()
