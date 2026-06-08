from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, replace
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import skfuzzy as fuzz


# Caminho base usado pelo servidor para entregar HTML, CSS e JS locais.
BASE_DIR = Path(__file__).resolve().parent

# Faixas aceitas para cada entrada. Esses limites tambem protegem a API contra valores fora do modelo.
LIMITES = {
    'sono': (0.0, 10.0),
    'estresse': (0.0, 10.0),
    'atividade': (0.0, 90.0),
    'social': (0.0, 10.0),
}

# Metadados usados apenas para rotulos e formatacao do grafico enviado ao frontend.
GRAFICOS = {
    'sono': {'label': 'Sono', 'unidade': 'h', 'casas': 1},
    'estresse': {'label': 'Estresse', 'unidade': '/10', 'casas': 1},
    'atividade': {'label': 'Atividade fisica', 'unidade': 'min', 'casas': 1},
    'social': {'label': 'Interacao social', 'unidade': '/10', 'casas': 1},
}

# Universos discretos onde as funcoes de pertinencia sao avaliadas.
UNIVERSOS = {
    'sono': np.arange(0, 10.1, 0.1),
    'estresse': np.arange(0, 10.1, 0.1),
    'atividade': np.arange(0, 90.1, 1.0),
    'social': np.arange(0, 10.1, 0.1),
    'humor': np.arange(0, 101, 1.0),
}

# Funcoes fuzzy das entradas. Trapmf cria bordas largas, trimf cria uma transicao central.
FUNCOES_ENTRADA = {
    'sono': {
        'ruim': fuzz.trapmf(UNIVERSOS['sono'], [0, 0, 4, 5.5]),
        'regular': fuzz.trimf(UNIVERSOS['sono'], [4.5, 6.5, 8]),
        'bom': fuzz.trapmf(UNIVERSOS['sono'], [7, 8, 10, 10]),
    },
    'estresse': {
        'baixo': fuzz.trapmf(UNIVERSOS['estresse'], [0, 0, 2, 4]),
        'moderado': fuzz.trimf(UNIVERSOS['estresse'], [3, 5, 7]),
        'alto': fuzz.trapmf(UNIVERSOS['estresse'], [6, 8, 10, 10]),
    },
    'atividade': {
        'baixa': fuzz.trapmf(UNIVERSOS['atividade'], [0, 0, 10, 25]),
        'moderada': fuzz.trimf(UNIVERSOS['atividade'], [15, 35, 55]),
        'alta': fuzz.trapmf(UNIVERSOS['atividade'], [45, 65, 90, 90]),
    },
    'social': {
        'baixa': fuzz.trapmf(UNIVERSOS['social'], [0, 0, 2, 4]),
        'media': fuzz.trimf(UNIVERSOS['social'], [3, 5.5, 8]),
        'alta': fuzz.trapmf(UNIVERSOS['social'], [7, 8.5, 10, 10]),
    },
}

# Funcoes fuzzy da saida. O score de humor fica em uma escala interpretavel de 0 a 100.
FUNCOES_HUMOR = {
    'baixo': fuzz.trapmf(UNIVERSOS['humor'], [0, 0, 25, 45]),
    'neutro': fuzz.trimf(UNIVERSOS['humor'], [35, 50, 65]),
    'bom': fuzz.trapmf(UNIVERSOS['humor'], [55, 75, 100, 100]),
}


@dataclass(frozen=True)
class EntradaHumor:
    # Estrutura imutavel para carregar os quatro fatores que entram no modelo.
    sono: float
    estresse: float
    atividade: float
    social: float


def limitar(valor: float, minimo: float, maximo: float) -> float:
    # Mantem valores calculados dentro de uma faixa segura.
    return min(max(valor, minimo), maximo)


def validar_numero(nome: str, valor: Any) -> float:
    # Booleanos sao recusados porque em Python True/False tambem podem virar 1/0.
    if isinstance(valor, bool):
        raise ValueError(f'{nome} precisa ser numerico.')

    # A API aceita numeros vindos do JSON como int, float ou string numerica.
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{nome} precisa ser numerico.') from exc

    # Cada fator precisa respeitar o universo fuzzy definido para ele.
    minimo, maximo = LIMITES[nome]
    if not math.isfinite(numero):
        raise ValueError(f'{nome} precisa ser finito.')
    if numero < minimo or numero > maximo:
        raise ValueError(f'{nome} deve ficar entre {minimo:g} e {maximo:g}.')

    return numero


def ler_entrada(payload: dict[str, Any]) -> EntradaHumor:
    # Converte o JSON bruto em uma entrada validada e pronta para o calculo fuzzy.
    return EntradaHumor(
        sono=validar_numero('sono', payload.get('sono')),
        estresse=validar_numero('estresse', payload.get('estresse')),
        atividade=validar_numero('atividade', payload.get('atividade')),
        social=validar_numero('social', payload.get('social')),
    )


def grau_pertinencia(variavel: str, termo: str, valor: float) -> float:
    # Interpola o grau de pertinencia do valor informado dentro da curva fuzzy escolhida.
    universo = UNIVERSOS[variavel]
    funcao = FUNCOES_ENTRADA[variavel][termo]
    return float(fuzz.interp_membership(universo, funcao, valor))


def pertinencias(entrada: EntradaHumor) -> dict[str, dict[str, float]]:
    # Calcula quanto cada entrada pertence a cada termo linguistico, como ruim, regular ou bom.
    return {
        'sono': {
            'ruim': grau_pertinencia('sono', 'ruim', entrada.sono),
            'regular': grau_pertinencia('sono', 'regular', entrada.sono),
            'bom': grau_pertinencia('sono', 'bom', entrada.sono),
        },
        'estresse': {
            'baixo': grau_pertinencia('estresse', 'baixo', entrada.estresse),
            'moderado': grau_pertinencia('estresse', 'moderado', entrada.estresse),
            'alto': grau_pertinencia('estresse', 'alto', entrada.estresse),
        },
        'atividade': {
            'baixa': grau_pertinencia('atividade', 'baixa', entrada.atividade),
            'moderada': grau_pertinencia('atividade', 'moderada', entrada.atividade),
            'alta': grau_pertinencia('atividade', 'alta', entrada.atividade),
        },
        'social': {
            'baixa': grau_pertinencia('social', 'baixa', entrada.social),
            'media': grau_pertinencia('social', 'media', entrada.social),
            'alta': grau_pertinencia('social', 'alta', entrada.social),
        },
    }


def montar_regras(graus: dict[str, dict[str, float]]) -> list[tuple[float, str]]:
    # Cada tupla representa: forca de ativacao da regra, categoria de humor impactada.
    return [
        # Evidencias individuais negativas, neutras e positivas.
        (graus['sono']['ruim'] * 0.65, 'baixo'),
        (graus['estresse']['alto'] * 0.8, 'baixo'),
        (graus['atividade']['baixa'] * 0.35, 'baixo'),
        (graus['social']['baixa'] * 0.35, 'baixo'),
        # Combinacoes negativas usando AND fuzzy por minimo.
        (min(graus['sono']['ruim'], graus['estresse']['alto']), 'baixo'),
        (min(graus['estresse']['alto'], graus['social']['baixa']), 'baixo'),
        (min(graus['sono']['ruim'], graus['atividade']['baixa']), 'baixo'),
        (min(graus['estresse']['alto'], graus['sono']['regular']), 'baixo'),
        (min(graus['estresse']['alto'], graus['atividade']['baixa']), 'baixo'),
        # Evidencias intermediarias que seguram o resultado na faixa neutra.
        (graus['sono']['regular'] * 0.35, 'neutro'),
        (graus['estresse']['moderado'] * 0.45, 'neutro'),
        (graus['atividade']['moderada'] * 0.35, 'neutro'),
        (graus['social']['media'] * 0.35, 'neutro'),
        # Combinacoes de compensacao, onde um fator bom pode suavizar outro mais pesado.
        (min(graus['estresse']['alto'], graus['atividade']['alta']), 'neutro'),
        (min(graus['sono']['regular'], graus['estresse']['moderado']), 'neutro'),
        (min(graus['social']['media'], graus['atividade']['moderada']), 'neutro'),
        # Evidencias positivas que aumentam a chance de humor bom.
        (graus['sono']['bom'] * 0.55, 'bom'),
        (graus['estresse']['baixo'] * 0.75, 'bom'),
        (graus['atividade']['alta'] * 0.45, 'bom'),
        (graus['social']['alta'] * 0.45, 'bom'),
        # Combinacoes positivas, mais fortes quando varios sinais bons aparecem juntos.
        (min(graus['sono']['bom'], graus['estresse']['baixo']), 'bom'),
        (min(graus['sono']['bom'], graus['social']['alta']), 'bom'),
        (min(graus['estresse']['baixo'], graus['atividade']['moderada']), 'bom'),
        (min(graus['estresse']['baixo'], graus['social']['alta'], graus['atividade']['alta']), 'bom'),
    ]


def defuzzificar(regras: list[tuple[float, str]]) -> float:
    # Comeca com uma curva de saida zerada e vai agregando as regras ativadas.
    agregado = np.zeros_like(UNIVERSOS['humor'], dtype=float)

    # Cada regra corta a funcao de humor pela sua forca e combina com OR fuzzy por maximo.
    for forca, saida in regras:
        ativacao = np.fmin(forca, FUNCOES_HUMOR[saida])
        agregado = np.fmax(agregado, ativacao)

    # Fallback defensivo para evitar defuzzificacao em uma curva totalmente vazia.
    if np.max(agregado) == 0:
        return 50.0

    # Centroide transforma a area fuzzy agregada em um score unico.
    return float(fuzz.defuzz(UNIVERSOS['humor'], agregado, 'centroid'))


def calcular_score_continuo(entrada: EntradaHumor) -> float:
    # Camada complementar que deixa pequenas mudancas nos controles aparecerem no score.
    ajuste_sono = (entrada.sono - 7) * 11
    ajuste_estresse = (5 - entrada.estresse) * 8
    ajuste_atividade = (entrada.atividade - 35) * 0.35
    ajuste_social = (entrada.social - 5) * 5
    return limitar(50 + ajuste_sono + ajuste_estresse + ajuste_atividade + ajuste_social, 0, 100)


def combinar_pontuacoes(pontuacao_fuzzy: float, pontuacao_continua: float) -> float:
    # Mistura o raciocinio fuzzy com a camada continua para preservar didatica e sensibilidade.
    return limitar((pontuacao_fuzzy * 0.45) + (pontuacao_continua * 0.55), 0, 100)


def classificar(pontuacao: float) -> str:
    # Converte o score numerico em uma categoria simples para a interface.
    if pontuacao < 45:
        return 'baixo'
    return 'neutro' if pontuacao < 65 else 'bom'


def diagnosticar(entrada: EntradaHumor, categoria: str) -> str:
    # Texto principal do resultado, priorizando a categoria e depois o fator mais relevante.
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
    # Lista explicacoes curtas que ajudam o usuario a entender o que mais pesou.
    fatores = []

    # Estresse e sono recebem prioridade porque costumam puxar bastante a instabilidade.
    if entrada.estresse >= 7:
        fatores.append('Estresse alto reduziu a previsao.')
    elif entrada.estresse <= 3:
        fatores.append('Baixo estresse ajudou a previsao.')

    # Sono adequado protege o score, enquanto sono curto aumenta risco de humor baixo.
    if entrada.sono < 6:
        fatores.append('Sono curto aumentou o risco de instabilidade.')
    elif entrada.sono >= 7.5:
        fatores.append('Sono adequado sustentou melhor o resultado.')

    # Atividade fisica entra como fator pratico e facil de ajustar no dia.
    if entrada.atividade >= 45:
        fatores.append('Atividade fisica funcionou como fator de protecao.')
    elif entrada.atividade <= 10:
        fatores.append('Pouca atividade fisica limitou a melhora.')

    # Interacao social captura o efeito de isolamento ou conexao positiva no cenario.
    if entrada.social >= 7:
        fatores.append('Interacao social positiva elevou a leitura.')
    elif entrada.social <= 3:
        fatores.append('Baixa interacao social aumentou o risco.')

    # Evita deixar a area vazia quando todos os fatores estao em faixas medianas.
    if not fatores:
        fatores.append('Nenhum fator extremo apareceu no cenario atual.')

    return fatores


def recomendar(entrada: EntradaHumor, categoria: str) -> str:
    # Proximo passo sugerido. A ordem escolhe o ajuste com maior potencial imediato.
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
    # Pipeline principal: fuzzificacao, regras, defuzzificacao, combinacao e explicacao.
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
    # A curva mostra como o score mudaria ao variar apenas um fator por vez.
    if fator not in LIMITES:
        fator = 'sono'

    # Usa os limites e rotulos do fator escolhido para montar pontos coerentes para o Canvas.
    minimo, maximo = LIMITES[fator]
    info = GRAFICOS[fator]
    pontos = []

    # Trinta e um pontos sao suficientes para uma curva suave sem pesar a resposta da API.
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
    # Handler HTTP simples: serve arquivos estaticos e responde as rotas da API local.
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self) -> None:
        # Rota pequena para confirmar que o servidor Python esta ativo.
        caminho = urlparse(self.path).path

        if caminho == '/api/health':
            self.enviar_json({'status': 'ok'})
            return

        super().do_GET()

    def do_POST(self) -> None:
        # Rota principal: recebe valores da interface e devolve diagnostico + curva.
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
        # Le o corpo da requisicao com limite simples para evitar payload exagerado.
        tamanho = int(self.headers.get('Content-Length', '0'))
        if tamanho > 4096:
            raise ValueError('Payload muito grande.')

        # Decodifica o JSON e garante que o formato seja um objeto com chaves.
        corpo = self.rfile.read(tamanho)
        payload = json.loads(corpo.decode('utf-8') or '{}')

        if not isinstance(payload, dict):
            raise ValueError('JSON precisa ser um objeto.')

        return payload

    def enviar_json(self, payload: dict[str, Any], status: int = 200) -> None:
        # Centraliza a resposta JSON para manter charset, status e tamanho consistentes.
        corpo = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def parse_args() -> argparse.Namespace:
    # Permite trocar host e porta sem editar o arquivo.
    parser = argparse.ArgumentParser(description='Servidor local da previsao fuzzy de humor.')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    # Inicializa o servidor com suporte a requisicoes paralelas simples.
    args = parse_args()
    servidor = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f'Aplicacao rodando em http://{args.host}:{args.port}')
    servidor.serve_forever()


if __name__ == '__main__':
    main()
