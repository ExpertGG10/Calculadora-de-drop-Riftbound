from .espera import aguardar
from .teclado import pressionar_esc


def executar_etapa_fluxo_problema(etapa):
    acao = etapa.get("acao")

    if acao == "aguardar":
        segundos = float(etapa.get("segundos", 0))
        if segundos > 0:
            aguardar(segundos)
        return

    if acao == "pressionar_esc":
        quantidade = int(etapa.get("quantidade", etapa.get("vezes", 1)))
        intervalo = float(etapa.get("intervalo", 0.2))
        if quantidade > 0:
            pressionar_esc(quantidade=quantidade, intervalo=intervalo)
        return

    raise ValueError(f"Acao de fluxo nao suportada: {acao}")


def executar_acao_problema_esperado(nome_problema, fluxos):
    fluxo = fluxos.get(
        nome_problema,
        [{"acao": "pressionar_esc", "quantidade": 1, "intervalo": 0.2}],
    )

    for etapa in fluxo:
        executar_etapa_fluxo_problema(etapa)


__all__ = ["executar_etapa_fluxo_problema", "executar_acao_problema_esperado"]
