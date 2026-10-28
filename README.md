# miFitnessReinterpreter

**miFitnessReinterpreter** é uma ferramenta de processamento de dados e análise de saúde desenvolvida em Python para extrair, filtrar e reinterpretar as exportações nativas do aplicativo Mi Fitness (Xiaomi Wear / Zepp Life) de um dispositivo Redmi Watch 5 Lite ou similar.

O projeto transforma os arquivos `.csv` complexos, com milhões de registros em formato JSON bruto, em relatórios de desempenho semanais e mensais. Ele avalia a qualidade da sua saúde gerando um **Score de 0 a 100** para passos, sono e frequência cardíaca utilizando fórmulas baseadas em literatura científica e parâmetros biológicos reais.

---

## 🛠 Funcionalidades

### 1. Extração Inteligente (Data Parser)

O aplicativo Mi Fitness exporta um arquivo massivo que contém todo o histórico de uso misturado e estruturado em JSONs por célula (`Value`).

- O script extrai dinamicamente o **mês** e **ano** baseando-se na data do nome do arquivo original.
- Ajusta os *timestamps* de UTC para o fuso horário de Brasília (`America/Sao_Paulo`).
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
- **Fase Profunda (20pts):** Avalia a secreção de hormônios do crescimento (ideal ≥ 15% da noite).
- **Fase REM (20pts):** Avalia a restauração cognitiva (ideal ≥ 20% da noite).
- **Eficiência (15pts):** Razão entre o tempo dormindo vs. tempo na cama.
- **WASO / Continuidade (10pts):** Penaliza grandes períodos acordado após o início do sono (ideal ≤ 20 min).
- **Qualidade de Respiração (5pts):** Lê a saturação/estabilidade (ideal ≥ 95 / 100).

### 4. Módulo de Coração (Heart Health Score)

Processa a carga alostática diária em ciclos de 24h:

- **Frequência de Repouso (35pts):** Mede o Percentil 5 (P5) para aferir a bradicardia sinusal de condicionamento (ideal entre 45-65 bpm).
- **Variabilidade Macroscópica (25pts):** Avalia o desvio padrão global do dia (SNA responsivo deve ter desvio ≥ 15 bpm).
- **Tempo Parassimpático (20pts):** Verifica a porcentagem de leituras no dia ≤ 75 bpm para garantir tempo suficiente para síntese proteica e relaxamento (≥ 55%).
- **Reserva Cardíaca (20pts):** Confere se houve um pico de esforço de treinamento diário (máximo ≥ 115 bpm).

### 5. Consolidação Global

Após gerar os relatórios individuais, as planilhas são mescladas (usando *Outer Joins*) e um peso científico geral é aplicado para fornecer uma métrica única e simples de evolução da sua saúde no mês.

- **Peso do Sono:** 45% (Fator mais crítico para recuperação humana).
- **Peso Cardíaco:** 35% (Base metabólica).
- **Peso dos Passos (NEAT):** 20% (Apenas locomoção e gasto calórico).

### 6. Arquivo de Entrada para Consolidação (`center_fitness_data.csv`)

Para gerar o arquivo final `center_fitness_data.csv`, é necessário criar ou disponibilizar um arquivo de entrada no formato `.csv` dentro da pasta `data/`.

- **Localização:** O arquivo de entrada deve estar dentro da pasta `data/` do projeto.
- **Formato:** O arquivo precisa ser um `.csv` com os dados esperados pelo processo de consolidação.
- **Arquivo final:** O processamento utiliza esse arquivo como fonte de dados para gerar o resultado `center_fitness_data.csv`.
- **Nome do arquivo:** Verifique a linha 304 do código e substitua o nome do arquivo pelo nome correto do `.csv` criado na pasta `data/`. O nome informado no código deve corresponder exatamente ao nome do arquivo, incluindo a extensão `.csv`.

Exemplo de estrutura:

```text
miFitnessReinterpreter/
├── data/
│   ├── seu_arquivo.csv
│   ├── steps_data_MM_YYYY.csv
│   ├── sleep_data_MM_YYYY.csv
│   └── heart_rate_data_MM_YYYY.csv
├── ...
└── center_fitness_data.csv
```

Substitua `seu_arquivo.csv` pelo nome real do arquivo de entrada utilizado no projeto. O exemplo é ilustrativo; mantenha os nomes e caminhos exigidos pelo código.

---

## 🚀 Como Utilizar

### Pré-requisitos

Certifique-se de ter o Python instalado (3.8+) e as dependências abaixo:

```bash
pip install pandas numpy
```
