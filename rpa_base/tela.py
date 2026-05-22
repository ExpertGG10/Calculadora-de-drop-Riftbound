import pyautogui as pag
from functools import lru_cache
from pathlib import Path
from PIL import Image

from .espera import aguardar


_RAIZ_PROJETO = Path(__file__).resolve().parent.parent
_TEMPO_ESTIMADO_BUSCA_PIXEL_TELA_INTEIRA = 1.4


def _montar_caminho_imagem(nome_imagem):
    caminho_imagem = _RAIZ_PROJETO / "assets" / "imgs" / f"{nome_imagem}"
    return str(caminho_imagem)


@lru_cache(maxsize=64)
def _carregar_imagem_referencia(caminho_imagem):
    with Image.open(caminho_imagem) as imagem:
        return imagem.copy()


def _normalizar_nomes_imagem(nomes_imagem):
    if len(nomes_imagem) == 1 and isinstance(nomes_imagem[0], (list, tuple)):
        nomes = tuple(nomes_imagem[0])
    else:
        nomes = tuple(nomes_imagem)
    if not nomes:
        raise ValueError("Informe ao menos uma imagem para localizar")
    return nomes


def _localizar_imagem(nome_imagem, confianca):
    try:
        caminho_imagem = _montar_caminho_imagem(nome_imagem)
        imagem_referencia = _carregar_imagem_referencia(caminho_imagem)
        return pag.locateCenterOnScreen(imagem_referencia, confidence=confianca)
    except pag.PyAutoGUIException:
        return None


def _imagem_esta_na_regiao(imagem_encontrada, centro_x=None, margem_x=None, centro_y=None, margem_y=None):
    if imagem_encontrada is None:
        return False
    if centro_x is None or margem_x is None or centro_y is None or margem_y is None:
        return True
    return (
        centro_x - margem_x < imagem_encontrada.x < centro_x + margem_x
        and centro_y - margem_y < imagem_encontrada.y < centro_y + margem_y
    )


def clicar_imagem(*nomes_imagem, tempo_limite=None, confianca=0.8, exibir_logs=False, usar_scroll=False, valor_scroll=-1000):
    nomes = _normalizar_nomes_imagem(nomes_imagem)
    tempo_restante = tempo_limite
    while tempo_restante is None or tempo_restante > 0:
        for nome_imagem in nomes:
            imagem_encontrada = _localizar_imagem(nome_imagem, confianca)
            if imagem_encontrada:
                aguardar(0.5)
                pag.click(imagem_encontrada.x, imagem_encontrada.y)
                return True
            if exibir_logs:
                print(f"nao encontrou para clicar: {nome_imagem}")
        if usar_scroll:
            pag.scroll(valor_scroll)
        aguardar(0.5)
        if tempo_restante is not None:
            tempo_restante -= 0.5

    return False


def esperar_imagem_sumir(nome_imagem, confianca=0.8, exibir_logs=False):
    procurando_imagem = True
    while procurando_imagem:
        if _localizar_imagem(nome_imagem, confianca):
            aguardando_desaparecer = True
            while aguardando_desaparecer:
                aguardar(0.5)
                if not _localizar_imagem(nome_imagem, confianca):
                    aguardando_desaparecer = False
                    procurando_imagem = False
        else:
            if exibir_logs:
                print(f"ainda nao apareceu: {nome_imagem}")
            aguardar(1)


def contar_imagens_visiveis(nome_imagem, confianca=0.8, tempo_limite=1, exibir_logs=False):
    imagens_encontradas = []
    while len(imagens_encontradas) < 1 and tempo_limite > 0:
        try:
            caminho_imagem = _montar_caminho_imagem(nome_imagem)
            imagem_referencia = _carregar_imagem_referencia(caminho_imagem)
            imagens_encontradas = list(
                pag.locateAllOnScreen(imagem_referencia, confidence=confianca)
            )
            aguardar(1)
            tempo_limite -= 1
        except Exception as erro:
            if exibir_logs:
                print("ndeu: " + str(erro))
    return len(imagens_encontradas)


def mover_mouse_para_imagem(nome_imagem, confianca, exibir_logs=False):
    procurando_imagem = True
    while procurando_imagem:
        imagem_encontrada = _localizar_imagem(nome_imagem, confianca)
        if not imagem_encontrada:
            aguardar(1)
            if exibir_logs:
                print("nao encontrou para mover mouse")
        else:
            pag.moveTo(imagem_encontrada.x, imagem_encontrada.y)
            procurando_imagem = False


def procurar_imagem(
    *nomes_imagem,
    tempo_limite=3,
    confianca=0.8,
    extensao=".png",
    exibir_logs=False,
    centro_x=None,
    margem_x=None,
    centro_y=None,
    margem_y=None,
    usar_scroll=False,
    valor_scroll=-1000,
    retornar_posicao=False,
):
    nomes = _normalizar_nomes_imagem(nomes_imagem)
    tempo_restante = tempo_limite
    while tempo_restante > 0:
        for nome_imagem in nomes:
            imagem_encontrada = _localizar_imagem(nome_imagem, confianca)
            if _imagem_esta_na_regiao(imagem_encontrada, centro_x, margem_x, centro_y, margem_y):
                if retornar_posicao:
                    return True, imagem_encontrada, nome_imagem
                return True
            if exibir_logs:
                print(f"nao encontrou: {nome_imagem}")
        aguardar(0.1)
        tempo_restante -= 0.1
        if usar_scroll:
            pag.scroll(valor_scroll)
    if retornar_posicao:
        return False, None, None
    return False


def imagem_existe(nome_imagem, tempo, confianca=0.8, exibir_logs=False):
    return procurar_imagem(
        nome_imagem,
        tempo_limite=tempo,
        confianca=confianca,
        exibir_logs=exibir_logs,
    )


def imagem_nao_existe(nome_imagem, tempo, confianca=0.8, exibir_logs=False):
    while True:
        if not _localizar_imagem(nome_imagem, confianca):
            return True
        aguardar(1)
        tempo -= 1
        if tempo <= 0:
            return False


def imagem_existe_na_regiao(
    nome_imagem,
    confianca,
    tempo,
    centro_x=640,
    margem_x=640,
    centro_y=360,
    margem_y=360,
):
    return procurar_imagem(
        nome_imagem,
        tempo_limite=tempo,
        confianca=confianca,
        centro_x=centro_x,
        margem_x=margem_x,
        centro_y=centro_y,
        margem_y=margem_y,
    )


def imagem_existe_com_scroll(nome_imagem, tempo, confianca=0.8, exibir_logs=False, valor_scroll=-1000):
    return procurar_imagem(
        nome_imagem,
        tempo_limite=tempo,
        confianca=confianca,
        exibir_logs=exibir_logs,
        usar_scroll=True,
        valor_scroll=valor_scroll,
    )


def _cor_esta_entre_intervalos(cor_pixel, cor_minima, cor_maxima):
    return all(cor_minima[indice] <= cor_pixel[indice] <= cor_maxima[indice] for indice in range(3))


def _encontrar_pixel_por_cor_exata(cor_alvo, regiao=None, passo=1):
    screenshot = pag.screenshot(region=regiao)
    largura, altura = screenshot.size
    base_x = regiao[0] if regiao else 0
    base_y = regiao[1] if regiao else 0

    for y in range(0, altura, passo):
        for x in range(0, largura, passo):
            cor_pixel = screenshot.getpixel((x, y))[:3]
            if cor_pixel == cor_alvo:
                return base_x + x, base_y + y
    return None


def clicar_com_ctrl_f(
    texto_busca=None,
    regiao=None,
    passo_varredura=1,
    tempo_limite=5,
    exibir_logs=False,
):
    cor_laranja = (255, 150, 50)
    cor_azul_min = (0, 51, 161)
    cor_azul_max = (51, 103, 209)

    pag.hotkey("ctrl", "f")
    aguardar(1)

    if texto_busca:
        pag.write(str(texto_busca), interval=0.01)
        aguardar(0.5)

    coordenada_laranja = None
    tempo_restante = tempo_limite
    while tempo_restante > 0 and coordenada_laranja is None:
        coordenada_laranja = _encontrar_pixel_por_cor_exata(
            cor_alvo=cor_laranja,
            regiao=regiao,
            passo=passo_varredura,
        )
        if coordenada_laranja is None:
            aguardar(0.1)
            tempo_restante -= _TEMPO_ESTIMADO_BUSCA_PIXEL_TELA_INTEIRA + 0.1

    pag.press("esc")
    aguardar(0.5)

    if coordenada_laranja is None:
        if exibir_logs:
            print("nao encontrou pixel laranja durante a busca")
        return False

    cor_atual = pag.pixel(coordenada_laranja[0], coordenada_laranja[1])
    cor_atual_rgb = cor_atual[:3]
    ficou_azul = _cor_esta_entre_intervalos(cor_atual_rgb, cor_azul_min, cor_azul_max)

    if ficou_azul:
        pag.click(coordenada_laranja[0], coordenada_laranja[1])
        return True

    if exibir_logs:
        print(f"pixel nao ficou azul apos ESC: {cor_atual[:3]}")
    return False
