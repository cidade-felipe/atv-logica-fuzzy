# Previsao de humor com logica fuzzy

Este projeto traz uma interface interativa para estimar o humor do dia usando logica fuzzy.

A versao atual usa Python com `scikit-fuzzy` para calcular a logica fuzzy. O JavaScript fica responsavel apenas por manter a tela interativa, chamar a API local e desenhar o grafico em Canvas. Nao usa Plotly, CDN ou internet para os graficos.

O resultado nao e diagnostico clinico. E uma leitura educativa baseada em regras fuzzy.

## Como usar

Crie o ambiente virtual:

```powershell
python -m venv venv
```

Ative o ambiente:

```powershell
venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Rode o servidor local:

```powershell
python app.py
```

Abra no navegador:

```text
http://127.0.0.1:8000
```

## Estrutura ativa

```text
app.py
requirements.txt
index.html
assets/css/app.css
assets/js/app.js
codex.md
LICENSE
README.md
```

## Como funciona

Fato: `app.py` serve os arquivos da interface e expoe a rota `POST /api/humor`.

Fato: o calculo fuzzy usa `scikit-fuzzy` no Python para funcoes de pertinencia, interpolacao de pertinencia e defuzzificacao.

Fato: o JavaScript envia os valores preenchidos para o Python, atualiza o resultado na tela e desenha o grafico local em Canvas.

Inferencia: centralizar a logica fuzzy no Python reduz o risco de divergencia entre backend e frontend.

Opiniao tecnica: usar `scikit-fuzzy` e melhor do que manter as funcoes fuzzy implementadas manualmente, porque reduz risco de erro matematico e deixa o projeto mais alinhado com boas praticas.

## Limitacoes

- Nao substitui avaliacao psicologica ou medica.
- As regras foram definidas manualmente.
- A pontuacao e uma aproximacao didatica, nao uma previsao cientifica validada.
- Correlacao nao implica causalidade.
- Em uso real, seria necessario validar regras com dados reais, revisar vieses e tratar dados pessoais com cuidado.
