from .espera import aguardar, aguardar_inicio_processo, pausar_ate_confirmacao
from .excecoes import PararExecucao, ProblemaEsperadoError
from .tela import (
    clicar_imagem,
    clicar_com_ctrl_f,
    contar_imagens_visiveis,
    imagem_existe,
    imagem_existe_com_scroll,
    imagem_existe_na_regiao,
    imagem_nao_existe,
    mover_mouse_para_imagem,
    procurar_imagem,
    esperar_imagem_sumir,
)
from .teclado import colar_texto, digitar_texto, digitar_texto_formatado, pressionar_atalho, pressionar_tab
from .texto import preencher_template, separar_texto_por_marcadores
from .misc import corresponder_coluna, contar_ocorrencias
from .sistemas.dominio import atalho_dominio, trocar_empresa_dominio
from .dados import planilha_para_dicionario, dicionario_para_planilha, obter_id_empresa, obter_codigo
from .cache import (carregar_checkpoint, salvar_checkpoint, limpar_checkpoint, obter_ids_processados, marcar_como_processado,
                    carregar_cache, salvar_cache, limpar_cache)
from .fluxo_erro import executar_etapa_fluxo_problema, executar_acao_problema_esperado

__all__ = [
    "aguardar",
    "aguardar_inicio_processo",
    "pausar_ate_confirmacao",
    "PararExecucao",
    "ProblemaEsperadoError",
    "clicar_imagem",
    "clicar_com_ctrl_f",
    "contar_imagens_visiveis",
    "imagem_existe",
    "imagem_existe_com_scroll",
    "imagem_existe_na_regiao",
    "imagem_nao_existe",
    "mover_mouse_para_imagem",
    "procurar_imagem",
    "esperar_imagem_sumir",
    "colar_texto",
    "digitar_texto",
    "digitar_texto_formatado",
    "pressionar_atalho",
    "pressionar_tab",
    "preencher_template",
    "separar_texto_por_marcadores",
    "contar_ocorrencias",
    "corresponder_coluna",
    "atalho_dominio",
    "trocar_empresa_dominio",
    "planilha_para_dicionario",
    "dicionario_para_planilha",
    "carregar_checkpoint",
    "salvar_checkpoint",
    "limpar_checkpoint",
    "obter_ids_processados",
    "marcar_como_processado",
    "carregar_cache",
    "salvar_cache",
    "limpar_cache",
    "executar_etapa_fluxo_problema",
    "executar_acao_problema_esperado",
]
