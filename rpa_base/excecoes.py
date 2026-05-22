import pyautogui as pag


class PararExecucao(Exception):
    """Excecao para interromper o programa ao pressionar tecla de parada."""

    def __init__(self, tecla_parar):
        super().__init__(f"A tecla de escape ({tecla_parar}) foi pressionada")
        pag.keyUp("shift")
        pag.keyUp("ctrl")
        pag.keyUp("alt")


class ProblemaEsperadoError(Exception):
    """Excecao para interromper ao encontrar problema conhecido."""

    def __init__(self, nome_problema, fluxo=None, indice=None):
        self.nome_problema = nome_problema
        self.fluxo = fluxo
        self.indice = indice
        super().__init__(f"Problema ja conhecido: {nome_problema}, seguindo para o proximo registro")
        pag.keyUp("shift")
        pag.keyUp("ctrl")
        pag.keyUp("alt")

