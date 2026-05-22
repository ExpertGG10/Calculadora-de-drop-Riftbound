def separar_texto_por_marcadores(texto, marcadores):
    partes = []
    indice_inicio = 0
    texto_restante = texto
    deslocamento = 0
    for caractere in texto:
        if caractere in marcadores:
            partes.append(texto[indice_inicio : texto_restante.find(caractere) + deslocamento])
            partes.append(caractere)
            indice_inicio = texto_restante.find(caractere) + 1 + deslocamento
            texto_restante = texto_restante[indice_inicio:]
            deslocamento += indice_inicio
    partes.append(texto[indice_inicio:])
    return partes


def preencher_template(nomes_campos, valores, template):
    while template.find("{") != -1:
        texto_antes = template[: template.find("{")]
        texto_depois = template[template.find("}") + 1 :]
        nome_campo = template[template.find("{") + 1 : template.find("}")]
        indice_valor = nomes_campos.index(nome_campo)
        template = texto_antes + valores[indice_valor] + texto_depois
    return template
