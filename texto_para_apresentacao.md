## Roteiro de apresentação — Previsão de Humor com Lógica Fuzzy

---

**Introdução — O que é o projeto**

> "O projeto é uma aplicação que tenta estimar o humor de uma pessoa com base em quatro fatores do dia: quanto ela dormiu, o nível de estresse, quanto de atividade física fez e o quanto interagiu socialmente. A ideia é usar lógica fuzzy pra fazer essa estimativa, o que é bem diferente de um sistema de regras normal."

---

**Por que lógica fuzzy?**

> "A lógica clássica trabalha com verdadeiro ou falso — ou você dormiu bem, ou não dormiu. A lógica fuzzy aceita o meio-termo. Você pode ter dormido 'mais ou menos', com grau 0.7 de pertinência na categoria 'regular' e 0.3 em 'ruim' ao mesmo tempo. Isso é mais próximo de como a gente raciocina no dia a dia."

---

**Como o código funciona — passo a passo**

> "O processo tem quatro etapas principais. Primeiro, a fuzzificação: o usuário informa um valor numérico, como 6 horas de sono, e o sistema converte isso em graus linguísticos usando as curvas de pertinência. Pra isso uso a função `interp_membership` do `scikit-fuzzy`."

> "Segundo, a avaliação das regras. Tenho 24 regras definidas manualmente, combinando os fatores. Por exemplo: se o sono está ruim E o estresse está alto, isso puxa o humor pra baixo com força máxima. O AND fuzzy é feito com `min()`, porque no fuzzy você pega o menor grau entre as condições."

> "Terceiro, a agregação: as regras ativadas são combinadas numa curva de saída única, usando `fmax`, que é o OR fuzzy — fica com o maior valor em cada ponto."

> "Quarto, a defuzzificação: a curva agregada é transformada num número único usando o método do centroide, que é basicamente o centro de gravidade da área. Isso me dá um score de 0 a 100."

---

**O detalhe híbrido**

> "Além do resultado fuzzy puro, tem uma camada linear que calcula uma pontuação contínua em paralelo. O score final mistura os dois: 45% do resultado fuzzy e 55% da camada linear. Isso garante que pequenas variações nos controles apareçam no score, porque o fuzzy sozinho às vezes fica 'preso' numa faixa."

---

**As bibliotecas**

> "As dependências principais são o `scikit-fuzzy`, que fornece as funções de pertinência trapezoidais e triangulares, a interpolação e a defuzzificação por centroide; e o `numpy`, que trabalha com os arrays numéricos dos universos de discurso e faz as operações vetorizadas de `fmin` e `fmax`. O `scipy` e o `networkx` estão ali como dependências internas do próprio `scikit-fuzzy`."

---

**Arquitetura da aplicação**

> "A arquitetura é simples: o `app.py` em Python sobe um servidor HTTP local na porta 8000, serve os arquivos estáticos da interface e expõe uma rota `POST /api/humor`. O frontend em JavaScript manda os valores preenchidos pra essa rota, o Python faz todo o cálculo fuzzy e devolve o diagnóstico com o score, a categoria — baixo, neutro ou bom —, os fatores que mais pesaram e uma recomendação. O gráfico é desenhado pelo próprio JavaScript em Canvas, sem biblioteca externa."

---

**Limitações e honestidade técnica**

> "É importante deixar claro: o resultado não é diagnóstico clínico. As regras foram definidas manualmente, sem validação com dados reais. É um projeto educativo pra demonstrar como a lógica fuzzy funciona na prática. Em um cenário real, as regras precisariam ser calibradas com dados e revisadas por especialistas."

---

**Encerramento**

> "No geral, o projeto mostra bem o ciclo completo de um sistema fuzzy de Mamdani: você parte de valores numéricos, passa por fuzzificação, avaliação de regras, agregação e defuzzificação, e chega num resultado interpretável. O `scikit-fuzzy` cuida da parte matemática pesada e o código fica focado na lógica do domínio."