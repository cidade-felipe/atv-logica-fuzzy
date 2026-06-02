from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, replace
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent

LIMITES = {
    'sono': (0.0, 10.0),
    'estresse': (0.0, 10.0),
    'atividade': (0.0, 90.0),
    'social': (0.0, 10.0),
}

GRAFICOS = {
    'sono': {'label': 'Sono', 'unidade': 'h', 'casas': 1},
    'estresse': {'label': 'Estresse', 'unidade': '/10', 'casas': 1},
    'atividade': {'label': 'Atividade fisica', 'unidade': 'min', 'casas': 0},
    'social': {'label': 'Interacao social', 'unidade': '/10', 'casas': 1},
}


@dataclass(frozen=True)
class EntradaHumor:
    sono: float
    estresse: float
    atividade: float
    social: float


def limitar(valor: float, minimo: float, maximo: float) -> float:
    return min(max(valor, minimo), maximo)


def trimf(valor: float, pontos: tuple[float, float, float]) -> float:
    a, b, c = pontos

    if valor <= a or valor >= c:
        return 0.0
    if valor == b:
        return 1.0
    if valor < b:
        return (valor - a) / (b - a)
    return (c - valor) / (c - b)


def trapmf(valor: float, pontos: tuple[float, float, float, float]) -> float:
    a, b, c, d = pontos

    if valor < a or valor > d:
        return 0.0
    if b <= valor <= c:
        return 1.0
    if valor < b:
        return (valor - a) / (b - a)
    return (d - valor) / (d - c)


def validar_numero(nome: str, valor: Any) -> float:
    if isinstance(valor, bool):
        raise ValueError(f'{nome} precisa ser numerico.')

    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{nome} precisa ser numerico.') from exc

    minimo, maximo = LIMITES[nome]
    if not math.isfinite(numero):
        raise ValueError(f'{nome} precisa ser finito.')
    if numero < minimo or numero > maximo:
        raise ValueError(f'{nome} deve ficar entre {minimo:g} e {maximo:g}.')

    return numero


def ler_entrada(payload: dict[str, Any]) -> EntradaHumor:
    return EntradaHumor(
        sono=validar_numero('sono', payload.get('sono')),
        estresse=validar_numero('estresse', payload.get('estresse')),
        atividade=validar_numero('atividade', payload.get('atividade')),
        social=validar_numero('social', payload.get('social')),
    )


def pertinencias(entrada: EntradaHumor) -> dict[str, dict[str, float]]:
    return {
        'sono': {
            'ruim': trapmf(entrada.sono, (0, 0, 4, 5.5)),
            'regular': trimf(entrada.sono, (4.5, 6.5, 8)),
            'bom': trapmf(entrada.sono, (7, 8, 10, 10)),
        },
        'estresse': {
            'baixo': trapmf(entrada.estresse, (0, 0, 2, 4)),
            'moderado': trimf(entrada.estresse, (3, 5, 7)),
            'alto': trapmf(entrada.estresse, (6, 8, 10, 10)),
        },
        'atividade': {
            'baixa': trapmf(entrada.atividade, (0, 0, 10, 25)),
            'moderada': trimf(entrada.atividade, (15, 35, 55)),
            'alta': trapmf(entrada.atividade, (45, 65, 90, 90)),
        },
        'social': {
            'baixa': trapmf(entrada.social, (0, 0, 2, 4)),
            'media': trimf(entrada.social, (3, 5.5, 8)),
            'alta': trapmf(entrada.social, (7, 8.5, 10, 10)),
        },
    }


def pertinencia_humor(categoria: str, valor: float) -> float:
    if categoria == 'baixo':
        return trapmf(valor, (0, 0, 25, 45))
    if categoria == 'neutro':
        return trimf(valor, (35, 50, 65))
    return trapmf(valor, (55, 75, 100, 100))


def montar_regras(graus: dict[str, dict[str, float]]) -> list[tuple[float, str]]:
    return [
        (graus['sono']['ruim'] * 0.65, 'baixo'),
        (graus['estresse']['alto'] * 0.8, 'baixo'),
        (graus['atividade']['baixa'] * 0.35, 'baixo'),
        (graus['social']['baixa'] * 0.35, 'baixo'),
        (min(graus['sono']['ruim'], graus['estresse']['alto']), 'baixo'),
        (min(graus['estresse']['alto'], graus['social']['baixa']), 'baixo'),
        (min(graus['sono']['ruim'], graus['atividade']['baixa']), 'baixo'),
        (min(graus['estresse']['alto'], graus['sono']['regular']), 'baixo'),
        (min(graus['estresse']['alto'], graus['atividade']['baixa']), 'baixo'),
        (graus['sono']['regular'] * 0.35, 'neutro'),
        (graus['estresse']['moderado'] * 0.45, 'neutro'),
        (graus['atividade']['moderada'] * 0.35, 'neutro'),
        (graus['social']['media'] * 0.35, 'neutro'),
        (min(graus['estresse']['alto'], graus['atividade']['alta']), 'neutro'),
        (min(graus['sono']['regular'], graus['estresse']['moderado']), 'neutro'),
        (min(graus['social']['media'], graus['atividade']['moderada']), 'neutro'),
        (graus['sono']['bom'] * 0.55, 'bom'),
        (graus['estresse']['baixo'] * 0.75, 'bom'),
        (graus['atividade']['alta'] * 0.45, 'bom'),
        (graus['social']['alta'] * 0.45, 'bom'),
        (min(graus['sono']['bom'], graus['estresse']['baixo']), 'bom'),
        (min(graus['sono']['bom'], graus['social']['alta']), 'bom'),
        (min(graus['estresse']['baixo'], graus['atividade']['moderada']), 'bom'),
        (min(graus['estresse']['baixo'], graus['social']['alta'], graus['atividade']['alta']), 'bom'),
    ]


def defuzzificar(regras: list[tuple[float, str]]) -> float:
    numerador = 0.0
    denominador = 0.0

    for humor in range(101):
        agregado = 0.0

        for forca, saida in regras:
            ativacao = min(forca, pertinencia_humor(saida, humor))
            agregado = max(agregado, ativacao)

        numerador += humor * agregado
        denominador += agregado

    if denominador == 0:
        return 50.0

    return numerador / denominador


def calcular_score_continuo(entrada: EntradaHumor) -> float:
    ajuste_sono = (entrada.sono - 7) * 11
    ajuste_estresse = (5 - entrada.estresse) * 8
    ajuste_atividade = (entrada.atividade - 35) * 0.35
    ajuste_social = (entrada.social - 5) * 5
    return limitar(50 + ajuste_sono + ajuste_estresse + ajuste_atividade + ajuste_social, 0, 100)


def combinar_pontuacoes(pontuacao_fuzzy: float, pontuacao_continua: float) -> float:
    return limitar((pontuacao_fuzzy * 0.45) + (pontuacao_continua * 0.55), 0, 100)


def classificar(pontuacao: float) -> str:
    if pontuacao < 45:
        return 'baixo'
    if pontuacao < 65:
        return 'neutro'
    return 'bom'


def diagnosticar(entrada: EntradaHumor, categoria: str) -> str:
    if categoria == 'baixo':
        return 'Os sinais indicam maior risco de humor baixo hoje.'
    if categoria == 'bom':
        return 'Os sinais indicam boa chance de humor positivo hoje.'
    if entrada.estresse >= 7:
        return 'O humor ficou no meio termo, mas o estresse esta pesando.'
    if entrada.sono < 6:
        return 'O humor ficou no meio termo, mas o sono curto esta puxando para baixo.'
    if entrada.atividade < 20:
        return 'O humor ficou no meio termo, mas pouca atividade fisica limitou a melhora.'
    if entrada.social < 4:
        return 'O humor ficou no meio termo, mas baixa interacao social reduziu a leitura.'
    return 'Os fatores ficaram em faixas intermediarias.'


def listar_fatores(entrada: EntradaHumor) -> list[str]:
    fatores = []

    if entrada.estresse >= 7:
        fatores.append('Estresse alto reduziu a previsao.')
    elif entrada.estresse <= 3:
        fatores.append('Baixo estresse ajudou a previsao.')

    if entrada.sono < 6:
        fatores.append('Sono curto aumentou o risco de instabilidade.')
    elif entrada.sono >= 7.5:
        fatores.append('Sono adequado sustentou melhor o resultado.')

    if entrada.atividade >= 45:
        fatores.append('Atividade fisica funcionou como fator de protecao.')
    elif entrada.atividade <= 10:
        fatores.append('Pouca atividade fisica limitou a melhora.')

    if entrada.social >= 7:
        fatores.append('Interacao social positiva elevou a leitura.')
    elif entrada.social <= 3:
        fatores.append('Baixa interacao social aumentou o risco.')

    if not fatores:
        fatores.append('Nenhum fator extremo apareceu no cenario atual.')

    return fatores


def recomendar(entrada: EntradaHumor, categoria: str) -> str:
    if entrada.estresse >= 7:
        return 'Priorize reduzir carga mental: pausa curta, respiracao, caminhada leve ou uma tarefa menor por vez.'
    if entrada.sono < 6:
        return 'O maior ganho provavel vem de recuperar sono ou reduzir exigencias no resto do dia.'
    if entrada.atividade < 20:
        return 'Uma atividade leve de 10 a 20 minutos pode melhorar a leitura sem exigir muito.'
    if entrada.social < 4:
        return 'Uma conversa curta com alguem de confianca pode funcionar como fator de protecao.'
    if categoria == 'bom':
        return 'Mantenha os fatores que estao funcionando e evite sobrecarregar o dia.'
    return 'Escolha um ajuste pequeno e concreto, porque o cenario esta equilibrado.'


def calcular_humor(entrada: EntradaHumor) -> dict[str, Any]:
    graus = pertinencias(entrada)
    regras = montar_regras(graus)
    pontuacao_fuzzy = defuzzificar(regras)
    pontuacao_continua = calcular_score_continuo(entrada)
    pontuacao = combinar_pontuacoes(pontuacao_fuzzy, pontuacao_continua)
    categoria = classificar(pontuacao)

    return {
        'entrada': asdict(entrada),
        'pontuacao': round(pontuacao, 1),
        'categoria': categoria,
        'diagnostico': diagnosticar(entrada, categoria),
        'fatores': listar_fatores(entrada),
        'recomendacao': recomendar(entrada, categoria),
        'componentes': {
            'fuzzy': round(pontuacao_fuzzy, 1),
            'continuo': round(pontuacao_continua, 1),
        },
    }


def gerar_curva(entrada: EntradaHumor, fator: str) -> dict[str, Any]:
    if fator not in LIMITES:
        fator = 'sono'

    minimo, maximo = LIMITES[fator]
    info = GRAFICOS[fator]
    pontos = []

    for indice in range(31):
        valor = minimo + ((maximo - minimo) * indice / 30)
        entrada_variada = replace(entrada, **{fator: valor})
        resultado = calcular_humor(entrada_variada)
        pontos.append({
            'x': round(valor, info['casas']),
            'y': resultado['pontuacao'],
        })

    return {
        'fator': fator,
        'label': info['label'],
        'unidade': info['unidade'],
        'valorAtual': round(getattr(entrada, fator), info['casas']),
        'pontos': pontos,
    }


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self) -> None:
        caminho = urlparse(self.path).path

        if caminho == '/api/health':
            self.enviar_json({'status': 'ok'})
            return

        super().do_GET()

    def do_POST(self) -> None:
        caminho = urlparse(self.path).path

        if caminho != '/api/humor':
            self.enviar_json({'erro': 'Rota nao encontrada.'}, status=404)
            return

        try:
            payload = self.ler_json()
            entrada = ler_entrada(payload)
            resultado = calcular_humor(entrada)
            resultado['grafico'] = gerar_curva(entrada, str(payload.get('grafico', 'sono')))
            self.enviar_json(resultado)
        except ValueError as exc:
            self.enviar_json({'erro': str(exc)}, status=400)
        except json.JSONDecodeError:
            self.enviar_json({'erro': 'JSON invalido.'}, status=400)

    def ler_json(self) -> dict[str, Any]:
        tamanho = int(self.headers.get('Content-Length', '0'))
        if tamanho > 4096:
            raise ValueError('Payload muito grande.')

        corpo = self.rfile.read(tamanho)
        payload = json.loads(corpo.decode('utf-8') or '{}')

        if not isinstance(payload, dict):
            raise ValueError('JSON precisa ser um objeto.')

        return payload

    def enviar_json(self, payload: dict[str, Any], status: int = 200) -> None:
        corpo = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Servidor local da previsao fuzzy de humor.')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    servidor = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f'Aplicacao rodando em http://{args.host}:{args.port}')
    servidor.serve_forever()


if __name__ == '__main__':
    main()
