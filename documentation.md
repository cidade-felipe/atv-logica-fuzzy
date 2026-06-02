# Documentacao tecnica do projeto

## 1. Objetivo

Este projeto cria uma aplicacao local para previsao educativa de humor usando logica fuzzy.

A pessoa informa quatro fatores do dia:

- Sono, em horas.
- Estresse, em escala de 0 a 10.
- Atividade fisica, em minutos.
- Interacao social positiva, em escala de 0 a 10.

A aplicacao retorna:

- Pontuacao de humor de 0 a 100.
- Categoria: `baixo`, `neutro` ou `bom`.
- Diagnostico textual educativo.
- Fatores principais que influenciaram a leitura.
- Recomendacao pratica.
- Grafico local de sensibilidade.

Fato: o sistema nao faz diagnostico clinico.

Inferencia: o tema de humor funciona bem para logica fuzzy porque as variaveis sao graduais. Uma pessoa nao esta apenas "sem estresse" ou "com estresse". Ela pode estar levemente, moderadamente ou altamente estressada.

Opiniao tecnica: usar fuzzy aqui e melhor do que regras binarias, porque melhora a interpretabilidade e evita cortes artificiais demais.

## 2. Arquitetura

Arquivos principais:

```text
app.py
requirements.txt
index.html
assets/css/app.css
assets/js/app.js
README.md
codex.md
documentation.md
LICENSE
```

Responsabilidades:

- `app.py`: backend local, API, validacao, fuzzy, defuzzificacao, recomendacao e pontos do grafico.
- `assets/js/app.js`: interacao da tela, chamada da API e desenho do Canvas.
- `assets/css/app.css`: layout e estilo.
- `index.html`: estrutura da interface.
- `requirements.txt`: dependencias Python.
- `documentation.md`: explicacao tecnica detalhada.

## 3. Bibliotecas

### Python

#### `numpy`

Usado para criar universos numericos e agregar funcoes fuzzy.

Exemplos no projeto:

```python
np.arange(0, 10.1, 0.1)
np.zeros_like(UNIVERSOS['humor'], dtype=float)
np.fmin(forca, FUNCOES_HUMOR[saida])
np.fmax(agregado, ativacao)
```

Impacto pratico:

- Evita loops manuais grandes.
- Facilita calculo vetorizado.
- Reduz risco de erro em agregacao numerica.

#### `scikit-fuzzy`

Biblioteca principal de logica fuzzy.

Usada para:

- `fuzz.trimf`, funcao de pertinencia triangular.
- `fuzz.trapmf`, funcao de pertinencia trapezoidal.
- `fuzz.interp_membership`, grau de pertinencia de um valor.
- `fuzz.defuzz`, defuzzificacao por centroide.

Impacto pratico:

- Evita implementar formulas fuzzy manualmente.
- Deixa o projeto mais profissional.
- Reduz risco matematico.

#### `scipy`

Dependencia do ecossistema cientifico usado pelo `scikit-fuzzy`.

#### `networkx`

Dependencia usada pelo `scikit-fuzzy` em alguns modulos.

#### `packaging`

Dependencia importada por modulos internos do `scikit-fuzzy`.

### Frontend

Nao ha biblioteca externa no frontend.

O grafico usa Canvas nativo do navegador.

Impacto pratico:

- Funciona localmente.
- Nao depende de Plotly.
- Nao depende de CDN.
- Nao precisa de internet.

## 4. API local

### `GET /api/health`

Verifica se o servidor Python esta ativo.

Resposta:

```json
{"status": "ok"}
```

### `POST /api/humor`

Calcula o humor.

Payload:

```json
{
  "sono": 7,
  "estresse": 4.5,
  "atividade": 35,
  "social": 6,
  "grafico": "sono"
}
```

Resposta resumida:

```json
{
  "pontuacao": 55.0,
  "categoria": "neutro",
  "diagnostico": "Os fatores ficaram em faixas intermediarias.",
  "fatores": ["Nenhum fator extremo apareceu no cenario atual."],
  "recomendacao": "Escolha um ajuste pequeno e concreto, porque o cenario esta equilibrado.",
  "componentes": {
    "fuzzy": 50.1,
    "continuo": 59.0
  },
  "grafico": {
    "fator": "sono",
    "label": "Sono",
    "unidade": "h",
    "valorAtual": 7.0,
    "pontos": []
  }
}
```

## 5. Variaveis de entrada

### Sono

Escala:

```text
0 a 10 horas
```

Termos fuzzy:

- `ruim`
- `regular`
- `bom`

Funcoes:

```python
ruim = trapmf([0, 0, 4, 5.5])
regular = trimf([4.5, 6.5, 8])
bom = trapmf([7, 8, 10, 10])
```

Leitura pratica:

- Abaixo de 4 horas, o sono e fortemente ruim.
- Entre 4.5 e 8 horas, existe transicao entre ruim, regular e bom.
- A partir de 8 horas, o sono tende a ser fortemente bom.

### Estresse

Escala:

```text
0 a 10
```

Termos fuzzy:

- `baixo`
- `moderado`
- `alto`

Funcoes:

```python
baixo = trapmf([0, 0, 2, 4])
moderado = trimf([3, 5, 7])
alto = trapmf([6, 8, 10, 10])
```

Leitura pratica:

- 0 a 2 representa baixo estresse.
- 5 representa pico de estresse moderado.
- 8 a 10 representa estresse alto.

### Atividade fisica

Escala:

```text
0 a 90 minutos
```

Termos fuzzy:

- `baixa`
- `moderada`
- `alta`

Funcoes:

```python
baixa = trapmf([0, 0, 10, 25])
moderada = trimf([15, 35, 55])
alta = trapmf([45, 65, 90, 90])
```

Leitura pratica:

- Poucos minutos de atividade tendem a nao proteger tanto o humor.
- 35 minutos fica no centro da atividade moderada.
- 65 minutos ou mais ativa fortemente o termo `alta`.

### Interacao social

Escala:

```text
0 a 10
```

Termos fuzzy:

- `baixa`
- `media`
- `alta`

Funcoes:

```python
baixa = trapmf([0, 0, 2, 4])
media = trimf([3, 5.5, 8])
alta = trapmf([7, 8.5, 10, 10])
```

Leitura pratica:

- 0 a 2 indica pouca interacao social positiva.
- 5.5 representa interacao media.
- 8.5 a 10 representa alta interacao social positiva.

## 6. Variavel de saida

### Humor

Escala:

```text
0 a 100
```

Termos fuzzy:

- `baixo`
- `neutro`
- `bom`

Funcoes:

```python
baixo = trapmf([0, 0, 25, 45])
neutro = trimf([35, 50, 65])
bom = trapmf([55, 75, 100, 100])
```

Leitura pratica:

- Ate 45, o humor tende a baixo.
- Em torno de 50, o humor tende a neutro.
- Acima de 65, o humor tende a bom.

## 7. Formulas das funcoes fuzzy

### Funcao triangular

Usada por `fuzz.trimf`.

Pontos:

```text
[a, b, c]
```

Formula:

```text
mu(x) = 0, se x <= a ou x >= c
mu(x) = (x - a) / (b - a), se a < x < b
mu(x) = 1, se x = b
mu(x) = (c - x) / (c - b), se b < x < c
```

Interpretacao:

- `a`: inicio da pertinencia.
- `b`: ponto de pertinencia maxima.
- `c`: fim da pertinencia.

Exemplo:

```python
estresse_moderado = trimf([3, 5, 7])
```

Se `estresse = 5`, a pertinencia em `moderado` e 1.

### Funcao trapezoidal

Usada por `fuzz.trapmf`.

Pontos:

```text
[a, b, c, d]
```

Formula:

```text
mu(x) = 0, se x < a ou x > d
mu(x) = (x - a) / (b - a), se a <= x < b
mu(x) = 1, se b <= x <= c
mu(x) = (d - x) / (d - c), se c < x <= d
```

Observacao:

Quando `a = b` ou `c = d`, a funcao cria um ombro. O `scikit-fuzzy` lida com esses casos corretamente.

Exemplo:

```python
sono_ruim = trapmf([0, 0, 4, 5.5])
```

Nesse caso, de 0 a 4 horas a pertinencia em `ruim` e maxima.

## 8. Interpolacao de pertinencia

O projeto usa:

```python
fuzz.interp_membership(universo, funcao, valor)
```

Objetivo:

Encontrar o grau de pertinencia de um valor especifico dentro de uma funcao fuzzy definida no universo.

Formula conceitual:

```text
mu(valor) = interpolacao_linear(universo, funcao, valor)
```

Exemplo pratico:

Se `sono = 5.5`, o backend calcula quanto esse valor pertence a:

- `sono.ruim`
- `sono.regular`
- `sono.bom`

Impacto pratico:

O valor pode pertencer parcialmente a mais de um termo ao mesmo tempo.

## 9. Regras fuzzy

As regras retornam uma lista de pares:

```python
(forca, saida)
```

Onde:

- `forca`: ativacao da regra.
- `saida`: termo fuzzy da saida, podendo ser `baixo`, `neutro` ou `bom`.

### Regras individuais ponderadas

Formula geral:

```text
forca = mu(termo) * peso
```

Regras:

```text
sono ruim * 0.65 -> humor baixo
estresse alto * 0.80 -> humor baixo
atividade baixa * 0.35 -> humor baixo
social baixa * 0.35 -> humor baixo
sono regular * 0.35 -> humor neutro
estresse moderado * 0.45 -> humor neutro
atividade moderada * 0.35 -> humor neutro
social media * 0.35 -> humor neutro
sono bom * 0.55 -> humor bom
estresse baixo * 0.75 -> humor bom
atividade alta * 0.45 -> humor bom
social alta * 0.45 -> humor bom
```

Por que existem pesos:

- Evitam que um unico fator domine o resultado.
- Ainda deixam o score reagir quando uma variavel muda sozinha.
- Melhoram a sensibilidade visual da interface.

### Regras combinadas

Formula geral:

```text
forca = min(mu_1, mu_2, ..., mu_n)
```

O operador `min` representa o AND fuzzy.

Regras:

```text
min(sono ruim, estresse alto) -> humor baixo
min(estresse alto, social baixa) -> humor baixo
min(sono ruim, atividade baixa) -> humor baixo
min(estresse alto, sono regular) -> humor baixo
min(estresse alto, atividade baixa) -> humor baixo
min(estresse alto, atividade alta) -> humor neutro
min(sono regular, estresse moderado) -> humor neutro
min(social media, atividade moderada) -> humor neutro
min(sono bom, estresse baixo) -> humor bom
min(sono bom, social alta) -> humor bom
min(estresse baixo, atividade moderada) -> humor bom
min(estresse baixo, social alta, atividade alta) -> humor bom
```

Interpretacao:

Uma regra combinada so fica forte quando todos os fatores envolvidos estao relevantes.

## 10. Agregacao da saida fuzzy

Para cada regra, o projeto corta a funcao de saida pela forca da regra.

Formula:

```text
ativacao_i(y) = min(forca_i, mu_saida_i(y))
```

No codigo:

```python
ativacao = np.fmin(forca, FUNCOES_HUMOR[saida])
```

Depois, todas as regras sao combinadas pelo maximo.

Formula:

```text
agregado(y) = max(ativacao_1(y), ativacao_2(y), ..., ativacao_n(y))
```

No codigo:

```python
agregado = np.fmax(agregado, ativacao)
```

Interpretacao:

Cada regra contribui com uma parte da funcao de saida. A agregacao cria uma unica curva fuzzy final para o humor.

## 11. Defuzzificacao

O projeto usa defuzzificacao por centroide:

```python
fuzz.defuzz(UNIVERSOS['humor'], agregado, 'centroid')
```

Formula conceitual continua:

```text
score_fuzzy = integral(y * mu_agregado(y)) / integral(mu_agregado(y))
```

Como o projeto usa universo discreto de 0 a 100:

```text
score_fuzzy = soma(y * mu_agregado(y)) / soma(mu_agregado(y))
```

Fallback:

```python
if np.max(agregado) == 0:
    return 50.0
```

Por que 50:

- E o centro da escala.
- Evita erro quando nenhuma regra e ativada.
- Representa neutralidade operacional.

## 12. Camada continua de sensibilidade

Alem do score fuzzy, existe uma camada continua para melhorar a resposta visual.

Formula:

```text
score_continuo =
    50
    + (sono - 7) * 11
    + (5 - estresse) * 8
    + (atividade - 35) * 0.35
    + (social - 5) * 5
```

Depois:

```text
score_continuo = clamp(score_continuo, 0, 100)
```

Onde:

```text
clamp(x, min, max) = min(max(x, min), max)
```

Interpretacao dos pesos:

- Sono tem peso 11 porque a mudanca de horas de sono deve ser bem perceptivel.
- Estresse tem peso 8 e sinal invertido, porque mais estresse reduz a leitura.
- Atividade tem peso 0.35 porque sua escala vai ate 90 minutos.
- Social tem peso 5 porque sua escala vai de 0 a 10.

Exemplo:

```text
sono = 8
estresse = 2.5
atividade = 60
social = 8
```

Calculo:

```text
50
+ (8 - 7) * 11
+ (5 - 2.5) * 8
+ (60 - 35) * 0.35
+ (8 - 5) * 5
= 103.75
```

Depois do clamp:

```text
score_continuo = 100
```

## 13. Score final

Formula:

```text
score_final = clamp((score_fuzzy * 0.45) + (score_continuo * 0.55), 0, 100)
```

Motivo da mistura:

- O fuzzy traz interpretabilidade.
- O continuo traz sensibilidade.
- A interface fica menos travada em valores neutros.

Trade-off:

- Fica menos "fuzzy puro".
- Fica mais util como ferramenta interativa.

## 14. Classificacao

Formula:

```text
baixo, se score_final < 45
neutro, se 45 <= score_final < 65
bom, se score_final >= 65
```

Impacto:

- Valores abaixo de 45 sao tratados como risco de humor baixo.
- Valores entre 45 e 65 sao intermediarios.
- Valores acima de 65 sao positivos.

## 15. Diagnostico textual

A categoria controla o texto principal.

Regras:

```text
se categoria = baixo:
    "Os sinais indicam maior risco de humor baixo hoje."

se categoria = bom:
    "Os sinais indicam boa chance de humor positivo hoje."

se categoria = neutro e estresse >= 7:
    "O humor ficou no meio termo, mas o estresse esta pesando."

se categoria = neutro e sono < 6:
    "O humor ficou no meio termo, mas o sono curto esta puxando para baixo."

se categoria = neutro e atividade < 20:
    "O humor ficou no meio termo, mas pouca atividade fisica limitou a melhora."

se categoria = neutro e social < 4:
    "O humor ficou no meio termo, mas baixa interacao social reduziu a leitura."

caso contrario:
    "Os fatores ficaram em faixas intermediarias."
```

## 16. Fatores principais

O backend lista fatores com base em limites simples.

Regras:

```text
estresse >= 7 -> Estresse alto reduziu a previsao.
estresse <= 3 -> Baixo estresse ajudou a previsao.

sono < 6 -> Sono curto aumentou o risco de instabilidade.
sono >= 7.5 -> Sono adequado sustentou melhor o resultado.

atividade >= 45 -> Atividade fisica funcionou como fator de protecao.
atividade <= 10 -> Pouca atividade fisica limitou a melhora.

social >= 7 -> Interacao social positiva elevou a leitura.
social <= 3 -> Baixa interacao social aumentou o risco.
```

Se nenhum fator extremo aparecer:

```text
Nenhum fator extremo apareceu no cenario atual.
```

## 17. Recomendacao

Ordem de prioridade:

```text
1. estresse >= 7
2. sono < 6
3. atividade < 20
4. social < 4
5. categoria = bom
6. caso equilibrado
```

Motivo:

Inferencia: estresse alto e sono curto tendem a ser fatores mais urgentes para uma acao pratica imediata.

## 18. Grafico de sensibilidade

O grafico mostra como o score mudaria se apenas um fator variasse.

Formula para gerar os 31 pontos:

```text
valor_i = minimo + ((maximo - minimo) * i / 30)
```

Onde:

```text
i = 0, 1, 2, ..., 30
```

Para cada ponto:

```text
entrada_variada = entrada_atual com fator = valor_i
score_i = calcular_humor(entrada_variada)
```

Exemplo:

Se o grafico selecionado e `social`, o Python varia `social` de 0 a 10 e mantem sono, estresse e atividade nos valores atuais.

## 19. Desenho do Canvas

O Python calcula os pontos. O JavaScript apenas desenha.

Conversao de coordenada X:

```text
x_canvas = margem_esquerda + ((x - minX) / (maxX - minX)) * area_largura
```

Conversao de coordenada Y:

```text
y_canvas = margem_topo + area_altura - ((score / 100) * area_altura)
```

Por que subtrair no Y:

No Canvas, o eixo Y cresce para baixo. Para score alto aparecer mais acima, a formula inverte a coordenada.

Tooltip:

- O texto fixo do valor atual nao e desenhado dentro do Canvas.
- O hover encontra o ponto mais proximo da curva.
- O tooltip mostra fator e score sem cortar no limite direito.

Formula conceitual do ponto mais proximo:

```text
ponto_proximo = argmin(|ponto.x - valor_x_do_mouse|)
```

## 20. Validacao dos dados

Cada entrada precisa ser numerica, finita e dentro da faixa.

Faixas:

```text
sono: 0 a 10
estresse: 0 a 10
atividade: 0 a 90
social: 0 a 10
```

Regras de validacao:

```text
booleano nao e aceito
valor precisa converter para float
valor precisa ser finito
valor precisa estar dentro do limite
```

Impacto pratico:

- Evita score sem sentido.
- Evita erro silencioso.
- Reduz risco de entrada ruim na API.

## 21. Exemplo completo

Entrada:

```json
{
  "sono": 8,
  "estresse": 2.5,
  "atividade": 60,
  "social": 8,
  "grafico": "sono"
}
```

Resultado validado:

```text
categoria = bom
score_final = 91.5
score_fuzzy = 81.0
pontos_do_grafico = 31
```

Interpretacao:

- Sono bom ajuda.
- Estresse baixo ajuda bastante.
- Atividade alta ajuda.
- Interacao social alta ajuda.
- O score continuo chega perto do teto.
- A defuzzificacao fuzzy fica em torno de 81.
- A mistura final resulta em 91.5.

## 22. Como validar o projeto

Ativar ambiente:

```powershell
venv\Scripts\Activate.ps1
```

Validar Python:

```powershell
venv\Scripts\python -m py_compile app.py
```

Validar calculo:

```powershell
venv\Scripts\python -c "from app import EntradaHumor, calcular_humor, gerar_curva; e=EntradaHumor(8,2.5,60,8); r=calcular_humor(e); g=gerar_curva(e,'sono'); print(r['categoria'], r['pontuacao'], r['componentes']['fuzzy'], len(g['pontos']))"
```

Saida esperada:

```text
bom 91.5 81.0 31
```

Validar JavaScript:

```powershell
node --check assets\js\app.js
```

Rodar servidor:

```powershell
venv\Scripts\python app.py
```

Acessar:

```text
http://127.0.0.1:8000
```

## 23. Cuidados conceituais

Fato: o modelo e baseado em regras manuais.

Fato: nao existe validacao com dados reais neste projeto.

Inferencia: o modelo serve bem como exemplo didatico, mas nao como ferramenta clinica.

Opiniao tecnica: em uma aplicacao real, seria necessario coletar dados com consentimento, validar vieses, revisar regras com especialistas e testar generalizacao.

## 24. Possiveis melhorias

Melhorias simples:

- Adicionar testes unitarios para `calcular_humor`.
- Exibir os graus de pertinencia na interface.
- Permitir exportar resultado em JSON.
- Adicionar exemplos prontos de cenarios.

Melhorias avancadas:

- Ajustar pesos com dados reais.
- Criar arquivo de configuracao para regras.
- Separar regras em modulo proprio.
- Adicionar historico temporal.
- Comparar fuzzy com modelo estatistico.

