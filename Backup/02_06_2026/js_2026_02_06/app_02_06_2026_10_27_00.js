(function () {
  'use strict';

  var API_URL = '/api/humor';

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

  var graficoAtual = 'sono';
  var debounceId = null;
  var requisicaoAtual = 0;

  function limitar(valor, minimo, maximo) {
    return Math.min(Math.max(valor, minimo), maximo);
  }

  function formatarValor(nome, valor) {
    var limite = LIMITES[nome];
    return Number(valor).toFixed(limite.casas) + limite.unidade;
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
    var apiStatus = document.querySelector('[data-api-status]');
    var canvas = document.querySelector('[data-chart-canvas]');
    var chartCaption = document.querySelector('[data-chart-caption]');

    function lerEntrada() {
      return campos.reduce(function (valores, campo) {
        valores[campo.name] = Number(campo.value);
        return valores;
      }, {});
    }

    function sincronizarCampo(nome, valor) {
      var limite = LIMITES[nome];
      var range = formulario.querySelector('input[name="' + nome + '"]');
      var numero = formulario.querySelector('[data-number="' + nome + '"]');
      var saida = formulario.querySelector('[data-output="' + nome + '"]');
      var valorNormalizado = limitar(Number(valor || 0), limite.min, limite.max);

      range.value = valorNormalizado;
      numero.value = valorNormalizado;
      saida.textContent = formatarValor(nome, valorNormalizado);
    }

    function definirStatus(texto, tipo) {
      apiStatus.textContent = texto;
      apiStatus.setAttribute('data-status', tipo);
    }

    function renderizarResultado(resultado) {
      var categoriaTexto = resultado.categoria.charAt(0).toUpperCase() + resultado.categoria.slice(1);

      Object.keys(resultado.entrada).forEach(function (nome) {
        sincronizarCampo(nome, resultado.entrada[nome]);
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

      desenharGrafico(canvas, resultado.grafico, resultado.categoria);
      chartCaption.textContent = 'Variando ' + resultado.grafico.label.toLowerCase() + ', mantendo os outros valores atuais.';
      definirStatus('Python local conectado', 'ok');
    }

    function renderizarErro(mensagem) {
      painel.setAttribute('data-categoria', 'neutro');
      categoriaLabel.textContent = 'Offline';
      diagnostico.textContent = mensagem;
      recomendacao.textContent = 'Execute python app.py e acesse http://127.0.0.1:8000.';
      fatores.innerHTML = '<li>O JavaScript esta ativo, mas a API Python nao respondeu.</li>';
      definirStatus('Python local indisponivel', 'erro');
      limparGrafico(canvas, 'Sem dados do Python local.');
    }

    function consultarDiagnostico() {
      var id = ++requisicaoAtual;
      var entrada = lerEntrada();

      definirStatus('Calculando no Python...', 'loading');

      fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({}, entrada, { grafico: graficoAtual }))
      })
        .then(function (resposta) {
          if (!resposta.ok) {
            return resposta.json().then(function (erro) {
              throw new Error(erro.erro || 'Erro ao calcular diagnostico.');
            });
          }
          return resposta.json();
        })
        .then(function (resultado) {
          if (id === requisicaoAtual) {
            renderizarResultado(resultado);
          }
        })
        .catch(function (erro) {
          if (id === requisicaoAtual) {
            renderizarErro(erro.message);
          }
        });
    }

    function agendarDiagnostico() {
      window.clearTimeout(debounceId);
      debounceId = window.setTimeout(consultarDiagnostico, 90);
    }

    campos.forEach(function (campo) {
      var numero = formulario.querySelector('[data-number="' + campo.name + '"]');

      campo.addEventListener('input', function () {
        sincronizarCampo(campo.name, campo.value);
        agendarDiagnostico();
      });

      numero.addEventListener('input', function () {
        sincronizarCampo(campo.name, numero.value);
        agendarDiagnostico();
      });
    });

    document.querySelectorAll('[data-profile]').forEach(function (botao) {
      botao.addEventListener('click', function () {
        var perfil = PERFIS[botao.getAttribute('data-profile')];
        Object.keys(perfil).forEach(function (nome) {
          sincronizarCampo(nome, perfil[nome]);
        });
        consultarDiagnostico();
      });
    });

    document.querySelector('[data-reset]').addEventListener('click', function () {
      Object.keys(PERFIS.equilibrado).forEach(function (nome) {
        sincronizarCampo(nome, PERFIS.equilibrado[nome]);
      });
      consultarDiagnostico();
    });

    document.querySelectorAll('[data-chart-factor]').forEach(function (botao) {
      botao.addEventListener('click', function () {
        graficoAtual = botao.getAttribute('data-chart-factor');
        document.querySelectorAll('[data-chart-factor]').forEach(function (outroBotao) {
          outroBotao.setAttribute('aria-pressed', String(outroBotao === botao));
        });
        consultarDiagnostico();
      });
    });

    consultarDiagnostico();
  }

  function limparGrafico(canvas, mensagem) {
    var contexto = prepararCanvas(canvas);
    contexto.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
    contexto.fillStyle = '#667085';
    contexto.font = '14px Arial';
    contexto.fillText(mensagem, 18, 34);
  }

  function prepararCanvas(canvas) {
    var proporcao = window.devicePixelRatio || 1;
    var largura = canvas.clientWidth || 640;
    var altura = canvas.clientHeight || 240;
    var contexto = canvas.getContext('2d');

    canvas.width = largura * proporcao;
    canvas.height = altura * proporcao;
    contexto.setTransform(proporcao, 0, 0, proporcao, 0, 0);
    return contexto;
  }

  function desenharGrafico(canvas, grafico, categoria) {
    var contexto = prepararCanvas(canvas);
    var largura = canvas.clientWidth || 640;
    var altura = canvas.clientHeight || 240;
    var margem = { topo: 18, direita: 18, baixo: 34, esquerda: 42 };
    var areaLargura = largura - margem.esquerda - margem.direita;
    var areaAltura = altura - margem.topo - margem.baixo;
    var pontos = grafico.pontos;
    var minX = pontos[0].x;
    var maxX = pontos[pontos.length - 1].x;
    var cor = categoria === 'baixo' ? '#d95f59' : categoria === 'bom' ? '#2f9c67' : '#d9a441';

    contexto.clearRect(0, 0, largura, altura);
    contexto.strokeStyle = '#d9e0e8';
    contexto.lineWidth = 1;
    contexto.beginPath();
    contexto.moveTo(margem.esquerda, margem.topo);
    contexto.lineTo(margem.esquerda, margem.topo + areaAltura);
    contexto.lineTo(margem.esquerda + areaLargura, margem.topo + areaAltura);
    contexto.stroke();

    [25, 50, 75].forEach(function (valor) {
      var y = margem.topo + areaAltura - ((valor / 100) * areaAltura);
      contexto.strokeStyle = '#edf1f5';
      contexto.beginPath();
      contexto.moveTo(margem.esquerda, y);
      contexto.lineTo(margem.esquerda + areaLargura, y);
      contexto.stroke();
    });

    contexto.strokeStyle = cor;
    contexto.lineWidth = 3;
    contexto.beginPath();
    pontos.forEach(function (ponto, indice) {
      var x = margem.esquerda + ((ponto.x - minX) / (maxX - minX)) * areaLargura;
      var y = margem.topo + areaAltura - ((ponto.y / 100) * areaAltura);

      if (indice === 0) {
        contexto.moveTo(x, y);
      } else {
        contexto.lineTo(x, y);
      }
    });
    contexto.stroke();

    var atualX = margem.esquerda + ((grafico.valorAtual - minX) / (maxX - minX)) * areaLargura;
    contexto.strokeStyle = '#1f2933';
    contexto.lineWidth = 1.5;
    contexto.beginPath();
    contexto.moveTo(atualX, margem.topo);
    contexto.lineTo(atualX, margem.topo + areaAltura);
    contexto.stroke();

    contexto.fillStyle = '#1f2933';
    contexto.font = '12px Arial';
    contexto.fillText('0', 14, margem.topo + areaAltura + 4);
    contexto.fillText('50', 8, margem.topo + (areaAltura / 2) + 4);
    contexto.fillText('100', 4, margem.topo + 4);
    contexto.fillText(String(minX), margem.esquerda, altura - 10);
    contexto.fillText(String(maxX), margem.esquerda + areaLargura - 20, altura - 10);
    contexto.fillText('Atual: ' + grafico.valorAtual + grafico.unidade, atualX + 6, margem.topo + 14);
  }

  document.addEventListener('DOMContentLoaded', iniciarInterface);
})();
