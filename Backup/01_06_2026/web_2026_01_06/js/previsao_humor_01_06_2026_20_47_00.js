(function () {
  'use strict';

  function aplicarCategoriaNasLinhas() {
    document.querySelectorAll('[data-categoria]').forEach(function (linha) {
      var categoria = linha.getAttribute('data-categoria');
      if (categoria) {
        linha.classList.add('categoria-' + categoria);
      }
    });
  }

  function mostrarAvisoGraficos(mensagem) {
    document.querySelectorAll('.grafico').forEach(function (grafico) {
      grafico.textContent = mensagem;
    });
  }

  function renderizarGrafico(idElemento, figura) {
    var elemento = document.getElementById(idElemento);

    if (!elemento || !figura) {
      return;
    }

    window.Plotly.newPlot(elemento, figura.data, figura.layout, {
      displaylogo: false,
      responsive: true
    });
  }

  function inicializarRelatorio() {
    aplicarCategoriaNasLinhas();

    if (!window.Plotly) {
      mostrarAvisoGraficos('Plotly nao carregou. Verifique a conexao com a internet.');
      return;
    }

    if (!window.previsaoHumorFiguras) {
      mostrarAvisoGraficos('Dados dos graficos nao foram encontrados.');
      return;
    }

    renderizarGrafico('grafico-resultados', window.previsaoHumorFiguras.resultados);
    renderizarGrafico('grafico-pertinencia', window.previsaoHumorFiguras.pertinencia);
  }

  window.addEventListener('DOMContentLoaded', inicializarRelatorio);
})();
