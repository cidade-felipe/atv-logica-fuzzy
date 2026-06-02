# Previsao de humor com logica fuzzy

Este projeto traz uma interface interativa simples para estimar o humor do dia usando logica fuzzy.

A pessoa informa quatro valores:

- Horas de sono.
- Nivel de estresse.
- Minutos de atividade fisica.
- Nivel de interacao social positiva.

A interface retorna uma pontuacao de 0 a 100, uma categoria (`baixo`, `neutro` ou `bom`), uma leitura textual do cenario e um proximo passo pratico.

O resultado nao e diagnostico clinico. E uma leitura educativa baseada em regras fuzzy.

## Como usar

Abra o arquivo abaixo no navegador:

```text
index.html
```

Nao precisa instalar bibliotecas, criar ambiente virtual ou rodar servidor local. A versao atual funciona com HTML, CSS e JavaScript puro.

## Estrutura ativa

```text
index.html
assets/css/app.css
assets/js/app.js
codex.md
LICENSE
README.md
```

## Como funciona

Fato: a interface usa funcoes de pertinencia fuzzy triangulares e trapezoidais no JavaScript.

Inferencia: sono, estresse, atividade fisica e interacao social foram mantidos porque sao fatores cotidianos, faceis de preencher e bons para demonstrar conceitos graduais.

Opiniao tecnica: manter a versao final como app estatico e melhor para este projeto, porque reduz custo de manutencao, elimina dependencias e facilita abrir a demonstracao em qualquer navegador.

## Limitacoes

- Nao substitui avaliacao psicologica ou medica.
- As regras foram definidas manualmente.
- A pontuacao e uma aproximacao didatica, nao uma previsao cientifica validada.
- Correlacao nao implica causalidade.
- Em uso real, seria necessario validar regras com dados reais, revisar vieses e tratar dados pessoais com cuidado.
