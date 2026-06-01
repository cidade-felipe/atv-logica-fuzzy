(function (global) {
  'use strict';

  var LIMITES = {
    sono: { min: 0, max: 10, unidade: ' h', casas: 1 },
    estresse: { min: 0, max: 10, unidade: '/10', casas: 1 },
    atividade: { min: 0, max: 90, unidade: ' min', casas: 0 },
    social: { min: 0, max: 10, unidade: '/10', casas: 1 }
  };

  var PERFIS = {
    pesado: { sono: 4.5, estresse: 8.5, atividade: 5, social: 2 },
    equilibrado: { sono: 7, estresse: 4.5, atividade: 35, social: 6 },
    treino: { sono: 8, estresse: 2.5, atividade: 60, social: 8 }
  };

  function limitar(valor, minimo, maximo) {
    return Math.min(Math.max(valor, minimo), maximo);
  }

  function trimf(valor, pontos) {
    var a = pontos[0];
    var b = pontos[1];
    var c = pontos[2];

    if (valor <= a || valor >= c) {
      return 0;
    }

    if (valor === b) {
      return 1;
    }

    if (valor < b) {
      return (valor - a) / (b - a);
    }

    return (c - valor) / (c - b);
  }

  function trapmf(valor, pontos) {
    var a = pontos[0];
    var b = pontos[1];
    var c = pontos[2];
    var d = pontos[3];

    if (valor < a || valor > d) {
      return 0;
    }

    if (valor >= b && valor <= c) {
      return 1;
    }

    if (valor < b) {
      return (valor - a) / (b - a);
    }

    return (d - valor) / (d - c);
  }

  function pertinencias(entrada) {
    return {
      sono: {
        ruim: trapmf(entrada.sono, [0, 0, 4, 5.5]),
        regular: trimf(entrada.sono, [4.5, 6.5, 8]),
        bom: trapmf(entrada.sono, [7, 8, 10, 10])
      },
      estresse: {
        baixo: trapmf(entrada.estresse, [0, 0, 2, 4]),
        moderado: trimf(entrada.estresse, [3, 5, 7]),
        alto: trapmf(entrada.estresse, [6, 8, 10, 10])
      },
      atividade: {
        baixa: trapmf(entrada.atividade, [0, 0, 10, 25]),
        moderada: trimf(entrada.atividade, [15, 35, 55]),
        alta: trapmf(entrada.atividade, [45, 65, 90, 90])
      },
      social: {
        baixa: trapmf(entrada.social, [0, 0, 2, 4]),
        media: trimf(entrada.social, [3, 5.5, 8]),
        alta: trapmf(entrada.social, [7, 8.5, 10, 10])
      }
    };
  }

  function pertinenciaHumor(categoria, valor) {
    if (categoria === 'baixo') {
      return trapmf(valor, [0, 0, 25, 45]);
    }

    if (categoria === 'neutro') {
      return trimf(valor, [35, 50, 65]);
    }

    return trapmf(valor, [55, 75, 100, 100]);
  }

  function montarRegras(graus) {
    return [
      { forca: Math.min(graus.sono.ruim, graus.estresse.alto), saida: 'baixo' },
      { forca: Math.min(graus.estresse.alto, graus.social.baixa), saida: 'baixo' },
      { forca: Math.min(graus.sono.ruim, graus.atividade.baixa), saida: 'baixo' },
      { forca: Math.min(graus.estresse.alto, graus.sono.regular), saida: 'baixo' },
      { forca: Math.min(graus.estresse.alto, graus.atividade.baixa), saida: 'baixo' },
      { forca: Math.min(graus.estresse.alto, graus.atividade.alta), saida: 'neutro' },
      { forca: Math.min(graus.sono.regular, graus.estresse.moderado), saida: 'neutro' },
      { forca: Math.min(graus.social.media, graus.atividade.moderada), saida: 'neutro' },
      { forca: Math.min(graus.sono.bom, graus.estresse.baixo), saida: 'bom' },
      { forca: Math.min(graus.sono.bom, graus.social.alta), saida: 'bom' },
      { forca: Math.min(graus.estresse.baixo, graus.atividade.moderada), saida: 'bom' },
      {
        forca: Math.min(graus.estresse.baixo, graus.social.alta, graus.atividade.alta),
        saida: 'bom'
      }
    ];
  }

  function defuzzificar(regras) {
    var numerador = 0;
    var denominador = 0;

    for (var humor = 0; humor <= 100; humor += 1) {
      var agregado = 0;

      regras.forEach(function (regra) {
        var ativacao = Math.min(regra.forca, pertinenciaHumor(regra.saida, humor));
        agregado = Math.max(agregado, ativacao);
      });

      numerador += humor * agregado;
      denominador += agregado;
    }

    if (denominador === 0) {
      return 50;
    }

    return numerador / denominador;
  }

  function classificar(pontuacao) {
    if (pontuacao < 40) {
      return 'baixo';
    }

    if (pontuacao < 65) {
      return 'neutro';
    }

    return 'bom';
  }

  function diagnosticar(entrada, categoria) {
    if (categoria === 'baixo') {
      return 'Os sinais indicam maior risco de humor baixo hoje.';
    }

    if (categoria === 'bom') {
      return 'Os sinais indicam boa chance de humor positivo hoje.';
    }

    if (entrada.estresse >= 7) {
      return 'O humor ficou no meio termo, mas o estresse está pesando.';
    }

    return 'Os fatores ficaram em faixas intermediárias.';
  }

  function listarFatores(entrada) {
    var fatores = [];

    if (entrada.estresse >= 7) {
      fatores.push('Estresse alto reduziu a previsão.');
    } else if (entrada.estresse <= 3) {
      fatores.push('Baixo estresse ajudou a previsão.');
    }

    if (entrada.sono < 6) {
      fatores.push('Sono curto aumentou o risco de instabilidade.');
    } else if (entrada.sono >= 7.5) {
      fatores.push('Sono adequado sustentou melhor o resultado.');
    }

    if (entrada.atividade >= 45) {
      fatores.push('Atividade física funcionou como fator de proteção.');
    } else if (entrada.atividade <= 10) {
      fatores.push('Pouca atividade física limitou a melhora.');
    }

    if (entrada.social >= 7) {
      fatores.push('Interação social positiva elevou a leitura.');
    } else if (entrada.social <= 3) {
      fatores.push('Baixa interação social aumentou o risco.');
    }

    if (fatores.length === 0) {
      fatores.push('Nenhum fator extremo apareceu no cenário atual.');
    }

    return fatores;
  }

  function recomendar(entrada, categoria) {
    if (entrada.estresse >= 7) {
      return 'Priorize reduzir carga mental: pausa curta, respiração, caminhada leve ou uma tarefa menor por vez.';
    }

    if (entrada.sono < 6) {
      return 'O maior ganho provável vem de recuperar sono ou reduzir exigências no resto do dia.';
    }

    if (entrada.atividade < 20) {
      return 'Uma atividade leve de 10 a 20 minutos pode melhorar a leitura sem exigir muito.';
    }

    if (entrada.social < 4) {
      return 'Uma conversa curta com alguém de confiança pode funcionar como fator de proteção.';
    }

    if (categoria === 'bom') {
      return 'Mantenha os fatores que estão funcionando e evite sobrecarregar o dia.';
    }

    return 'Escolha um ajuste pequeno e concreto, porque o cenário está equilibrado.';
  }

  function normalizarEntrada(entrada) {
    return {
      sono: limitar(Number(entrada.sono), LIMITES.sono.min, LIMITES.sono.max),
      estresse: limitar(Number(entrada.estresse), LIMITES.estresse.min, LIMITES.estresse.max),
      atividade: limitar(Number(entrada.atividade), LIMITES.atividade.min, LIMITES.atividade.max),
      social: limitar(Number(entrada.social), LIMITES.social.min, LIMITES.social.max)
    };
  }

  function calcularHumor(entradaBruta) {
    var entrada = normalizarEntrada(entradaBruta);
    var graus = pertinencias(entrada);
    var regras = montarRegras(graus);
    var pontuacao = defuzzificar(regras);
    var categoria = classificar(pontuacao);

    return {
      entrada: entrada,
      pontuacao: pontuacao,
      categoria: categoria,
      diagnostico: diagnosticar(entrada, categoria),
      fatores: listarFatores(entrada),
      recomendacao: recomendar(entrada, categoria)
    };
  }

  function formatarValor(nome, valor) {
    var limite = LIMITES[nome];
    return valor.toFixed(limite.casas) + limite.unidade;
  }

  function iniciarInterface() {
    var formulario = document.querySelector('[data-humor-form]');

    if (!formulario) {
      return;
    }

    var campos = Array.from(formulario.querySelectorAll('input[type="range"]'));
    var painel = document.querySelector('[data-result-panel]');
    var score = document.querySelector('[data-score]');
    var scoreFill = document.querySelector('[data-score-fill]');
    var categoriaLabel = document.querySelector('[data-category-label]');
    var diagnostico = document.querySelector('[data-diagnostic]');
    var fatores = document.querySelector('[data-factors]');
    var recomendacao = document.querySelector('[data-recommendation]');

    function lerEntrada() {
      return campos.reduce(function (valores, campo) {
        valores[campo.name] = Number(campo.value);
        return valores;
      }, {});
    }

    function sincronizarCampo(nome, valor) {
      var range = formulario.querySelector('input[name="' + nome + '"]');
      var numero = formulario.querySelector('[data-number="' + nome + '"]');
      var saida = formulario.querySelector('[data-output="' + nome + '"]');
      var entrada = normalizarEntrada(Object.assign(lerEntrada(), { [nome]: valor }));
      var valorNormalizado = entrada[nome];

      range.value = valorNormalizado;
      numero.value = valorNormalizado;
      saida.textContent = formatarValor(nome, valorNormalizado);
    }

    function renderizar() {
      var resultado = calcularHumor(lerEntrada());
      var categoriaTexto = resultado.categoria.charAt(0).toUpperCase() + resultado.categoria.slice(1);

      Object.keys(resultado.entrada).forEach(function (nome) {
        var saida = formulario.querySelector('[data-output="' + nome + '"]');
        saida.textContent = formatarValor(nome, resultado.entrada[nome]);
      });

      painel.setAttribute('data-categoria', resultado.categoria);
      score.textContent = resultado.pontuacao.toFixed(1);
      scoreFill.style.width = resultado.pontuacao.toFixed(1) + '%';
      categoriaLabel.textContent = categoriaTexto;
      diagnostico.textContent = resultado.diagnostico;
      recomendacao.textContent = resultado.recomendacao;

      fatores.innerHTML = '';
      resultado.fatores.forEach(function (fator) {
        var item = document.createElement('li');
        item.textContent = fator;
        fatores.appendChild(item);
      });
    }

    campos.forEach(function (campo) {
      var numero = formulario.querySelector('[data-number="' + campo.name + '"]');

      campo.addEventListener('input', function () {
        sincronizarCampo(campo.name, campo.value);
        renderizar();
      });

      numero.addEventListener('input', function () {
        sincronizarCampo(campo.name, numero.value);
        renderizar();
      });
    });

    document.querySelectorAll('[data-profile]').forEach(function (botao) {
      botao.addEventListener('click', function () {
        var perfil = PERFIS[botao.getAttribute('data-profile')];
        Object.keys(perfil).forEach(function (nome) {
          sincronizarCampo(nome, perfil[nome]);
        });
        renderizar();
      });
    });

    document.querySelector('[data-reset]').addEventListener('click', function () {
      Object.keys(PERFIS.equilibrado).forEach(function (nome) {
        sincronizarCampo(nome, PERFIS.equilibrado[nome]);
      });
      renderizar();
    });

    renderizar();
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', iniciarInterface);
  }

  global.HumorFuzzy = {
    calcularHumor: calcularHumor
  };
})(typeof window !== 'undefined' ? window : globalThis);
