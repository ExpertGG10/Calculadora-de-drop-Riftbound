import pyautogui as pag
import pyperclip as ppc

from .espera import aguardar


def pressionar_atalho(*teclas):
    teclas_atalho = list(teclas)
    for tecla in teclas_atalho:
        pag.keyDown(tecla)
        aguardar(0.5)
    teclas_atalho.reverse()
    for tecla in teclas_atalho:
        pag.keyUp(tecla)
        aguardar(0.5)


def digitar_texto(texto):
    for caractere in texto:
        pag.press(caractere)


def colar_texto(texto):
    ppc.copy(texto)
    pag.hotkey("ctrl", "v")


def digitar_texto_formatado(texto, marcador_negrito="*", marcador_sublinhado="_", marcador_italico="~"):
    for parte_texto in texto:
        if parte_texto == marcador_negrito:
            pag.hotkey("ctrl", "b")
        elif parte_texto == marcador_italico:
            pag.hotkey("ctrl", "i")
        elif parte_texto == marcador_sublinhado:
            pag.hotkey("ctrl", "u")
        else:
            digitar_texto(str(parte_texto))


def pressionar_tab(quantidade, intervalo=0.2):
    if quantidade > 0:
        for _ in range(quantidade):
            aguardar(intervalo)
            pag.press("tab")
    else:
        quantidade_shift_tab = quantidade * -1
        pag.keyDown("shift")
        for _ in range(quantidade_shift_tab):
            aguardar(intervalo)
            pag.press("tab")
        pag.keyUp("shift")

def pressionar_esc(quantidade=1, intervalo=0.2):
    if quantidade > 0:
        for _ in range(quantidade):
            aguardar(intervalo)
            pag.press("esc")
