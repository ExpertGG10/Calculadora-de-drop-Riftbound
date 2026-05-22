import json
import os


def _garantir_pasta_arquivo(caminho_arquivo):
    pasta = os.path.dirname(caminho_arquivo)
    if pasta:
        os.makedirs(pasta, exist_ok=True)


def carregar_checkpoint(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        return {"processados": [], "falhas": {}}

    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_checkpoint(caminho_arquivo, checkpoint):
    _garantir_pasta_arquivo(caminho_arquivo)
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(checkpoint, arquivo, ensure_ascii=False, indent=2)


def limpar_checkpoint(caminho_arquivo):
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)


def obter_ids_processados(caminho_arquivo):
    checkpoint = carregar_checkpoint(caminho_arquivo)
    return set(checkpoint.get("processados", []))


def marcar_como_processado(caminho_arquivo, id_item, erro=None):
    checkpoint = carregar_checkpoint(caminho_arquivo)
    if id_item not in checkpoint["processados"]:
        checkpoint["processados"].append(id_item)
    if erro:
        checkpoint["falhas"][id_item] = erro
    else:
        checkpoint["falhas"].pop(id_item, None)
    salvar_checkpoint(caminho_arquivo, checkpoint)


def carregar_cache(caminho_cache, valor_padrao=None):
    if valor_padrao is None:
        valor_padrao = {}

    if not os.path.exists(caminho_cache):
        return valor_padrao

    with open(caminho_cache, "r", encoding="utf-8") as arquivo_cache:
        return json.load(arquivo_cache)


def salvar_cache(caminho_cache, dados_cache, identacao=2):
    _garantir_pasta_arquivo(caminho_cache)
    with open(caminho_cache, "w", encoding="utf-8") as arquivo_cache:
        json.dump(dados_cache, arquivo_cache, ensure_ascii=False, indent=identacao)


def limpar_cache(caminho_cache):
    if os.path.exists(caminho_cache):
        os.remove(caminho_cache)


__all__ = ["carregar_checkpoint", "salvar_checkpoint", "limpar_checkpoint", "obter_ids_processados", "marcar_como_processado", "carregar_cache", "salvar_cache", "limpar_cache"]