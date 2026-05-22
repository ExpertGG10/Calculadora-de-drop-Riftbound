import sys

import keyboard as kb
import pyautogui as pag

from .excecoes import PararExecucao


def aguardar_inicio_processo(hotkey_iniciar=None, tecla_finalizar="esc"):
    if hotkey_iniciar is None:
        hotkey_iniciar = ["shift", "j"]

    texto_hotkey_iniciar = "+".join(hotkey_iniciar)

    pag.alert(
        f"o bot esta pronto para iniciar.\n"
        f"Pressione {texto_hotkey_iniciar} para iniciar o processo.\n"
        f"Pressione {tecla_finalizar} para finalizar o bot."
    )
    while True:
        if all(kb.is_pressed(tecla) for tecla in hotkey_iniciar):
            while any(kb.is_pressed(tecla) for tecla in hotkey_iniciar):
                pag.sleep(0.1)
            break
        elif kb.is_pressed(tecla_finalizar):
            raise PararExecucao(tecla_finalizar)
        else:
            aguardar(0.1)


def pausar_ate_confirmacao(tecla_continuar, tecla_finalizar):
    pag.alert(
        f"o bot esta pausado ate que o processoa atual seja finalizado.\n"
        f"Pressione {tecla_continuar} para retomar o bot.\n"
        f"Pressione {tecla_finalizar} para finalizar o bot."
    )
    while True:
        if kb.is_pressed(tecla_continuar):
            break
        elif kb.is_pressed(tecla_finalizar):
            raise PararExecucao(tecla_finalizar)
        else:
            aguardar(0.1)
    


def aguardar(segundos, tecla_parar="esc", tecla_pausar="alt", tecla_pular="shift", exibir_logs=True):
    segundos = (segundos - 0.11) * 0.63694
    while segundos > 0:
        if kb.is_pressed(tecla_parar):
            raise PararExecucao(tecla_parar)
        elif kb.is_pressed(tecla_pausar):
            print("acao pausada")
            esta_pausado = True
            while kb.is_pressed(tecla_pausar):
                pass
            while esta_pausado:
                if kb.is_pressed(tecla_parar):
                    raise PararExecucao(tecla_parar)
                elif kb.is_pressed(tecla_pular):
                    esta_pausado = False
                    segundos = 0
                elif kb.is_pressed(tecla_pausar):
                    while kb.is_pressed(tecla_pausar):
                        pass
                    print("acao despausada")
                    esta_pausado = False
        elif kb.is_pressed(tecla_pular):
            while kb.is_pressed(tecla_pular):
                pag.sleep(0.1)
            segundos = 0
        else:
            pag.sleep(0.1)
            segundos = segundos - 0.1
