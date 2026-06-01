from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
import skfuzzy as fuzz
from skfuzzy import control as ctrl


LOGGER = logging.getLogger(__name__)

RANGES = {
    'sono_horas': (0.0, 10.0),
    'estresse': (0.0, 10.0),
    'atividade_min': (0.0, 90.0),
    'interacao_social': (0.0, 10.0),
}


@dataclass(frozen=True)
class EntradaHumor:
    nome: str
    sono_horas: float
    estresse: float
    atividade_min: float
    interacao_social: float


@dataclass(frozen=True)
class ResultadoHumor:
    entrada: EntradaHumor
    pontuacao: float
    categoria: str
    explicacao: str


def criar_variaveis_fuzzy() -> dict[str, ctrl.FuzzyVariable]:
    sono = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'sono_horas')
    estresse = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'estresse')
    atividade = ctrl.Antecedent(np.arange(0, 90.1, 1.0), 'atividade_min')
    social = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'interacao_social')
    humor = ctrl.Consequent(np.arange(0, 100.1, 1.0), 'humor')

    sono['ruim'] = fuzz.trapmf(sono.universe, [0, 0, 4, 5.5])
    sono['regular'] = fuzz.trimf(sono.universe, [4.5, 6.5, 8])
    sono['bom'] = fuzz.trapmf(sono.universe, [7, 8, 10, 10])

    estresse['baixo'] = fuzz.trapmf(estresse.universe, [0, 0, 2, 4])
    estresse['moderado'] = fuzz.trimf(estresse.universe, [3, 5, 7])
    estresse['alto'] = fuzz.trapmf(estresse.universe, [6, 8, 10, 10])

    atividade['baixa'] = fuzz.trapmf(atividade.universe, [0, 0, 10, 25])
    atividade['moderada'] = fuzz.trimf(atividade.universe, [15, 35, 55])
    atividade['alta'] = fuzz.trapmf(atividade.universe, [45, 65, 90, 90])

    social['baixa'] = fuzz.trapmf(social.universe, [0, 0, 2, 4])
    social['media'] = fuzz.trimf(social.universe, [3, 5.5, 8])
    social['alta'] = fuzz.trapmf(social.universe, [7, 8.5, 10, 10])

    humor['baixo'] = fuzz.trapmf(humor.universe, [0, 0, 25, 45])
    humor['neutro'] = fuzz.trimf(humor.universe, [35, 50, 65])
    humor['bom'] = fuzz.trapmf(humor.universe, [55, 75, 100, 100])

    return {
        'sono': sono,
        'estresse': estresse,
        'atividade': atividade,
        'social': social,
        'humor': humor,
    }


def criar_sistema_fuzzy(variaveis: dict[str, ctrl.FuzzyVariable]) -> ctrl.ControlSystem:
    sono = variaveis['sono']
    estresse = variaveis['estresse']
    atividade = variaveis['atividade']
    social = variaveis['social']
    humor = variaveis['humor']

    regras = [
        ctrl.Rule(sono['ruim'] & estresse['alto'], humor['baixo']),
        ctrl.Rule(estresse['alto'] & social['baixa'], humor['baixo']),
        ctrl.Rule(sono['ruim'] & atividade['baixa'], humor['baixo']),
        ctrl.Rule(estresse['alto'] & sono['regular'], humor['baixo']),
        ctrl.Rule(estresse['alto'] & atividade['baixa'], humor['baixo']),
        ctrl.Rule(estresse['alto'] & atividade['alta'], humor['neutro']),
        ctrl.Rule(sono['regular'] & estresse['moderado'], humor['neutro']),
        ctrl.Rule(social['media'] & atividade['moderada'], humor['neutro']),
        ctrl.Rule(sono['bom'] & estresse['baixo'], humor['bom']),
        ctrl.Rule(sono['bom'] & social['alta'], humor['bom']),
        ctrl.Rule(estresse['baixo'] & atividade['moderada'], humor['bom']),
        ctrl.Rule(estresse['baixo'] & social['alta'] & atividade['alta'], humor['bom']),
    ]

    return ctrl.ControlSystem(regras)


def validar_entrada(entrada: EntradaHumor) -> None:
    valores = {
        'sono_horas': entrada.sono_horas,
        'estresse': entrada.estresse,
        'atividade_min': entrada.atividade_min,
        'interacao_social': entrada.interacao_social,
    }

    for campo, valor in valores.items():
        minimo, maximo = RANGES[campo]
        if not isinstance(valor, (int, float)) or not np.isfinite(valor):
            raise ValueError(f'{campo} precisa ser um numero finito.')
        if valor < minimo or valor > maximo:
            raise ValueError(f'{campo} deve ficar entre {minimo:g} e {maximo:g}. Valor recebido: {valor:g}.')


def classificar_humor(pontuacao: float) -> str:
    if pontuacao < 40:
        return 'baixo'
    if pontuacao < 65:
        return 'neutro'
    return 'bom'


def explicar_resultado(entrada: EntradaHumor, categoria: str) -> str:
    sinais = []

    if entrada.estresse >= 7:
        sinais.append('estresse alto puxou a previsao para baixo')
    elif entrada.estresse <= 3:
        sinais.append('baixo estresse favoreceu um humor melhor')

    if entrada.sono_horas < 6:
        sinais.append('sono curto reduziu a estabilidade do humor')
    elif entrada.sono_horas >= 7.5:
        sinais.append('sono adequado ajudou a sustentar a previsao')

    if entrada.atividade_min >= 45:
        sinais.append('atividade fisica funcionou como fator de protecao')
    elif entrada.atividade_min <= 10:
        sinais.append('baixa atividade fisica limitou a melhora do humor')

    if entrada.interacao_social >= 7:
        sinais.append('boa interacao social elevou o resultado')
    elif entrada.interacao_social <= 3:
        sinais.append('pouca interacao social aumentou o risco de humor baixo')

    if not sinais:
        sinais.append('os fatores ficaram em faixas intermediarias')

    return f'Categoria {categoria}: ' + '; '.join(sinais) + '.'


def prever_humor(
    entrada: EntradaHumor,
    sistema: ctrl.ControlSystem,
) -> ResultadoHumor:
    validar_entrada(entrada)

    simulador = ctrl.ControlSystemSimulation(sistema)
    simulador.input['sono_horas'] = entrada.sono_horas
    simulador.input['estresse'] = entrada.estresse
    simulador.input['atividade_min'] = entrada.atividade_min
    simulador.input['interacao_social'] = entrada.interacao_social
    simulador.compute()

    pontuacao = float(simulador.output['humor'])
    categoria = classificar_humor(pontuacao)
    return ResultadoHumor(
        entrada=entrada,
        pontuacao=pontuacao,
        categoria=categoria,
        explicacao=explicar_resultado(entrada, categoria),
    )


def perfis_de_exemplo() -> list[EntradaHumor]:
    return [
        EntradaHumor('Segunda pesada', sono_horas=4.5, estresse=8.5, atividade_min=5, interacao_social=2),
        EntradaHumor('Dia equilibrado', sono_horas=7.0, estresse=4.5, atividade_min=35, interacao_social=6),
        EntradaHumor('Depois do treino', sono_horas=8.0, estresse=2.5, atividade_min=60, interacao_social=8),
        EntradaHumor('Dormiu bem, mas sob pressao', sono_horas=8.2, estresse=8.0, atividade_min=20, interacao_social=5),
        EntradaHumor('Pouco sono, amigos por perto', sono_horas=5.0, estresse=5.5, atividade_min=25, interacao_social=8),
    ]


def imprimir_resultados(resultados: Iterable[ResultadoHumor]) -> None:
    print('\nPrevisao fuzzy de humor')
    print('-' * 118)
    print(f'{"Perfil":<28} {"Sono":>6} {"Estresse":>9} {"Ativ.":>7} {"Social":>7} {"Score":>8} {"Categoria":>10}')
    print('-' * 118)

    for resultado in resultados:
        entrada = resultado.entrada
        print(
            f'{entrada.nome:<28} '
            f'{entrada.sono_horas:>6.1f} '
            f'{entrada.estresse:>9.1f} '
            f'{entrada.atividade_min:>7.0f} '
            f'{entrada.interacao_social:>7.1f} '
            f'{resultado.pontuacao:>8.1f} '
            f'{resultado.categoria:>10}'
        )

    print('-' * 118)
    for resultado in resultados:
        print(f'- {resultado.entrada.nome}: {resultado.explicacao}')
    print()


def criar_grafico_pertinencia(variaveis: dict[str, ctrl.FuzzyVariable]) -> go.Figure:
    itens = [
        ('Sono (horas)', variaveis['sono']),
        ('Estresse (0 a 10)', variaveis['estresse']),
        ('Atividade fisica (minutos)', variaveis['atividade']),
        ('Interacao social (0 a 10)', variaveis['social']),
        ('Humor previsto (0 a 100)', variaveis['humor']),
    ]

    figura = make_subplots(
        rows=len(itens),
        cols=1,
        subplot_titles=[titulo for titulo, _ in itens],
        vertical_spacing=0.08,
    )

    for linha, (_, variavel) in enumerate(itens, start=1):
        for nome_termo, termo in variavel.terms.items():
            figura.add_trace(
                go.Scatter(
                    x=variavel.universe,
                    y=termo.mf,
                    mode='lines',
                    name=f'{variavel.label}: {nome_termo}',
                ),
                row=linha,
                col=1,
            )

    figura.update_layout(
        title='Funcoes de pertinencia usadas na previsao de humor',
        height=1050,
        template='plotly_white',
        legend_title='Termos fuzzy',
    )
    figura.update_yaxes(range=[0, 1.05], title='Pertinencia')
    return figura


def criar_grafico_resultados(resultados: list[ResultadoHumor]) -> go.Figure:
    cores = {
        'baixo': '#d95f59',
        'neutro': '#d9a441',
        'bom': '#2f9c67',
    }

    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            x=[resultado.entrada.nome for resultado in resultados],
            y=[resultado.pontuacao for resultado in resultados],
            marker_color=[cores[resultado.categoria] for resultado in resultados],
            text=[f'{resultado.pontuacao:.1f}' for resultado in resultados],
            textposition='outside',
            hovertext=[resultado.explicacao for resultado in resultados],
            hoverinfo='text',
        )
    )
    figura.add_hrect(y0=0, y1=40, fillcolor='#f7d4d2', opacity=0.35, line_width=0)
    figura.add_hrect(y0=40, y1=65, fillcolor='#f7e7c1', opacity=0.35, line_width=0)
    figura.add_hrect(y0=65, y1=100, fillcolor='#d8f0e0', opacity=0.35, line_width=0)
    figura.update_layout(
        title='Pontuacao prevista por perfil',
        yaxis_title='Humor previsto (0 a 100)',
        xaxis_title='Perfil analisado',
        yaxis_range=[0, 105],
        template='plotly_white',
        height=520,
    )
    return figura


def gerar_relatorio_html(
    variaveis: dict[str, ctrl.FuzzyVariable],
    resultados: list[ResultadoHumor],
    caminho_saida: Path,
) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    grafico_pertinencia = criar_grafico_pertinencia(variaveis)
    grafico_resultados = criar_grafico_resultados(resultados)

    linhas_tabela = '\n'.join(
        (
            '<tr>'
            f'<td>{resultado.entrada.nome}</td>'
            f'<td>{resultado.entrada.sono_horas:.1f}</td>'
            f'<td>{resultado.entrada.estresse:.1f}</td>'
            f'<td>{resultado.entrada.atividade_min:.0f}</td>'
            f'<td>{resultado.entrada.interacao_social:.1f}</td>'
            f'<td>{resultado.pontuacao:.1f}</td>'
            f'<td>{resultado.categoria}</td>'
            f'<td>{resultado.explicacao}</td>'
            '</tr>'
        )
        for resultado in resultados
    )

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Previsao fuzzy de humor</title>
  <style>
    body {{
      color: #222;
      font-family: Arial, sans-serif;
      line-height: 1.5;
      margin: 32px auto;
      max-width: 1120px;
      padding: 0 20px;
    }}
    h1, h2 {{
      color: #1f2933;
    }}
    table {{
      border-collapse: collapse;
      font-size: 14px;
      width: 100%;
    }}
    th, td {{
      border-bottom: 1px solid #d9dee3;
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f4f6f8;
    }}
    .nota {{
      background: #eef6ff;
      border-left: 4px solid #3b82f6;
      padding: 12px 16px;
    }}
  </style>
</head>
<body>
  <h1>Previsao fuzzy de humor</h1>
  <p class="nota">
    Este exemplo nao e diagnostico psicologico. Ele demonstra como a logica fuzzy pode
    transformar sinais cotidianos em uma estimativa interpretavel de humor.
  </p>
  <h2>Cenarios avaliados</h2>
  <table>
    <thead>
      <tr>
        <th>Perfil</th>
        <th>Sono</th>
        <th>Estresse</th>
        <th>Atividade</th>
        <th>Social</th>
        <th>Score</th>
        <th>Categoria</th>
        <th>Leitura</th>
      </tr>
    </thead>
    <tbody>
      {linhas_tabela}
    </tbody>
  </table>
  {plot(grafico_resultados, output_type='div', include_plotlyjs='cdn')}
  {plot(grafico_pertinencia, output_type='div', include_plotlyjs=False)}
</body>
</html>
"""
    caminho_saida.write_text(html, encoding='utf-8')
    LOGGER.info('Relatorio gerado em %s', caminho_saida)


def construir_entrada_por_cli(args: argparse.Namespace) -> EntradaHumor | None:
    valores = [args.sono, args.estresse, args.atividade, args.social]
    if all(valor is None for valor in valores):
        return None
    if any(valor is None for valor in valores):
        raise ValueError('Informe sono, estresse, atividade e social juntos, ou deixe todos em branco.')

    return EntradaHumor(
        nome=args.nome,
        sono_horas=args.sono,
        estresse=args.estresse,
        atividade_min=args.atividade,
        interacao_social=args.social,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Exemplo pratico de logica fuzzy para previsao de humor.')
    parser.add_argument('--nome', default='Meu dia', help='Nome do cenario analisado.')
    parser.add_argument('--sono', type=float, help='Horas de sono, de 0 a 10.')
    parser.add_argument('--estresse', type=float, help='Nivel de estresse, de 0 a 10.')
    parser.add_argument('--atividade', type=float, help='Minutos de atividade fisica, de 0 a 90.')
    parser.add_argument('--social', type=float, help='Nivel de interacao social positiva, de 0 a 10.')
    parser.add_argument(
        '--saida',
        default='outputs/previsao_humor.html',
        help='Caminho do relatorio HTML gerado.',
    )
    parser.add_argument('--sem-graficos', action='store_true', help='Executa sem gerar relatorio HTML.')
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    args = parse_args()

    variaveis = criar_variaveis_fuzzy()
    sistema = criar_sistema_fuzzy(variaveis)
    entrada_cli = construir_entrada_por_cli(args)
    entradas = [entrada_cli] if entrada_cli else perfis_de_exemplo()

    resultados = [prever_humor(entrada, sistema) for entrada in entradas]
    imprimir_resultados(resultados)

    if not args.sem_graficos:
        gerar_relatorio_html(variaveis, resultados, Path(args.saida))


if __name__ == '__main__':
    main()
