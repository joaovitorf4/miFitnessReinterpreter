# miFitnessReinterpreter

**miFitnessReinterpreter** é uma ferramenta de processamento de dados e análise de saúde desenvolvida em Python para extrair, filtrar e reinterpretar as exportações nativas do aplicativo Mi Fitness (Xiaomi Wear / Zepp Life) de um dispositivo Redmi Watch 5 Lite ou similar.

O projeto transforma os arquivos `.csv` complexos, com milhões de registros em formato JSON bruto, em relatórios de desempenho semanais e mensais. Ele avalia a qualidade da sua saúde gerando um **Score de 0 a 100** para passos, sono e frequência cardíaca utilizando fórmulas baseadas em literatura científica e parâmetros biológicos reais.

---

## 🛠 Funcionalidades

### 1. Extração Inteligente (Data Parser)
O aplicativo Mi Fitness exporta um arquivo massivo que contém todo o histórico de uso misturado e estruturado em JSONs por célula (`Value`).
- O script extrai dinamicamente o **mês** e **ano** baseando-se na data do nome do arquivo original.
- Ajusta os _timestamps_ de UTC para o fuso horário de Brasília (`America/Sao_Paulo`).
- Filtra estritamente as entradas do mês atual e as separa em três arquivos CSV compactos e limpos dentro da pasta `data/`:
  - `steps_data_MM_YYYY.csv`
  - `sleep_data_MM_YYYY.csv`
  - `heart_rate_data_MM_YYYY.csv`

### 2. Módulo de Passos (Steps Score)
Calcula a quantidade e as médias de passos por dia/semana.
- **Score (0-100):** Utiliza uma função logarítmica baseada na utilidade marginal do esforço humano.
- **Sweet Spot:** 16.000 passos garantem a nota máxima (100 pontos). 
- A progressão inicial garante muitos pontos (o ganho entre 1k e 2k é maior que o ganho entre 12k e 14k). 10.000 passos garantem a nota 80.

### 3. Módulo de Sono (Sleep Quality Score)
Avalia a arquitetura e continuidade do sono utilizando referências clínicas padrão:
- **Duração (30pts):** Avalia se o tempo total está na janela ideal (7 a 9 horas), com penalidades suaves para *oversleeping* (excesso) ou déficits drásticos.
- **Fase Profunda (20pts):** Avalia a secreção de hormônios do crescimento (ideal $\ge 15\%$ da noite).
- **Fase REM (20pts):** Avalia a restauração cognitiva (ideal $\ge 20\%$ da noite).
- **Eficiência (15pts):** Razão entre o tempo dormindo vs. tempo na cama.
- **WASO / Continuidade (10pts):** Penaliza grandes períodos acordado após o início do sono (ideal $\le 20$ min).
- **Qualidade de Respiração (5pts):** Lê a saturação/estabilidade (ideal $\ge 95$ / 100).

### 4. Módulo de Coração (Heart Health Score)
Processa a carga alostática diária em ciclos de 24h:
- **Frequência de Repouso (35pts):** Mede o Percentil 5 (P5) para aferir a bradicardia sinusal de condicionamento (ideal entre 45-65 bpm).
- **Variabilidade Macroscópica (25pts):** Avalia o desvio padrão global do dia (SNA responsivo deve ter desvio $\ge 15$ bpm).
- **Tempo Parassimpático (20pts):** Verifica a porcentagem de leituras no dia $\le 75$ bpm para garantir tempo suficiente para síntese proteica e relaxamento ($\ge 55\%$).
- **Reserva Cardíaca (20pts):** Confere se houve um pico de esforço de treinamento diário (máximo $\ge 115$ bpm).

### 5. Consolidação Global
Após gerar os relatórios individuais, as planilhas são mescladas (usando _Outer Joins_) e um peso científico geral é aplicado para fornecer uma métrica única e simples de evolução da sua saúde no mês.
- **Peso do Sono:** 45% (Fator mais crítico para recuperação humana).
- **Peso Cardíaco:** 35% (Base metabólica).
- **Peso dos Passos (NEAT):** 20% (Apenas locomoção e gasto calórico).

---

## 🚀 Como Utilizar

### Pré-requisitos
Certifique-se de ter o Python instalado (3.8+) e as dependências abaixo:
```bash
pip install pandas numpy
