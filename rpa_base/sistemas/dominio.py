import pyautogui as pag

from rpa_base.espera import aguardar
from rpa_base.tela import procurar_imagem
from rpa_base.excecoes import ProblemaEsperadoError


def atalho_dominio(*teclas, intervalo=1):
    pag.keyDown("alt")
    try:
        for tecla in teclas:
            pag.press(tecla)
            aguardar(intervalo)
    finally:
        pag.keyUp("alt")


def trocar_empresa_dominio(numero_empresa):
    codigo_dominio = int(numero_empresa)
    pag.press("f8")
    aguardar(0.5)
    pag.typewrite(str(codigo_dominio))
    aguardar(2)
    pag.press("enter")
    aguardar(1)

    
    if procurar_imagem("troca_de_empresas", tempo_limite=5):
        for tentativa in range(20):
            if procurar_imagem("troca_de_empresas", tempo_limite=0.2):
                if procurar_imagem("parametro_nao_cadastrado_para_essa_empresa", tempo_limite=0.2):
                    print(f"Erro ao trocar para empresa {numero_empresa}")
                    raise ProblemaEsperadoError("Parametro não cadastrado para empresa")
                else:
                    aguardar(0.2)
            else:
                break
        if tentativa == 19:
            raise ProblemaEsperadoError("Empresa não encontrada")
    aguardar(0.5)
    pag.press("esc")
    aguardar(0.2)
    pag.press("esc")
    aguardar(0.5)


__all__ = ["atalho_dominio", "trocar_empresa_dominio"]
