# 🧠 Dijkstra Visual Simulator

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Tkinter](https://img.shields.io/badge/Tkinter-GUI-blue?logo=python&logoColor=white)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> Um simulador interativo do algoritmo de Dijkstra com visualização passo a passo, desenvolvido em Python com Tkinter.

![Dijkstra Simulator Demo](demo.gif) <!-- Substitua pelo link do GIF real -->

## ✨ Funcionalidades

- ✅ **Adicionar/Remover Nós** — Clique no canvas para criar ou remover vértices.
- ✅ **Criar Arestas Ponderadas** — Selecione dois nós e defina o peso (número positivo).
- ✅ **Definir Origem (S) e Destino (E)** — Escolha os pontos de partida e chegada.
- ✅ **Execução Passo a Passo** — Visualize cada iteração do algoritmo:
  - Nó atual em destaque (amarelo)
  - Nós visitados (roxo)
  - Distâncias atualizadas em tempo real
- ✅ **Controles de Animação**:
  - ▶️ Executar automático (com velocidade ajustável)
  - ⏪ Passo anterior
  - ⏩ Próximo passo
- ✅ **Painéis Informativos**:
  - Distâncias atualizadas para todos os nós
  - Caminho mínimo encontrado com custo total
  - Passo atual / total
- ✅ **Tema Escuro** — Interface moderna e confortável para os olhos.

---

## 🧪 Demonstração

<p align="center">
  <img src="screenshot.png" alt="Screenshot" width="700">
</p>

*Exemplo: Caminho mínimo entre os nós 1 e 6 com custo 8.0*

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Descrição |
|------------|-----------|
| **Python 3.7+** | Linguagem base |
| **Tkinter** | Interface gráfica nativa |
| **Heapq** | Fila de prioridade para Dijkstra |
| **Threading** | Animação assíncrona |

---

## 📦 Instalação e Execução

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/seu-usuario/dijkstra-visual-simulator.git
cd dijkstra-visual-simulator
