# miFitnessReinterpreter

Reinterpreta o export do **Mi Fitness** e gera um relatório de saúde com **passos**, **sono** e **frequência cardíaca**: score diário, resumo semanal/mensal e score global.

## Uso

```bash
pip install -r requirements.txt

python main.py                                   # usa o CSV mais recente de data/ e o mês do registro mais recente
python main.py data\20260929_..._fitness_data.csv --mes 2026-09
python main.py --mes 2026-08 --salvar-intermediarios data   # também grava sleep/steps/heart_rate por mês
```

- `--mes AAAA-MM` evita a inferência (lê o arquivo uma vez só, ~0,3 s mais rápido) e é a forma segura se você exportar nos primeiros dias do mês seguinte.
- Os CSVs brutos ficam em `data/` (já no `.gitignore`: são dados pessoais de saúde e o nome do arquivo contém seu Uid).

## Estrutura

```
miFitnessReinterpreter/
├── main.py                      # atalho para a CLI
├── mifitness_reinterpreter/     # pacote (nome de import em minúsculas, como manda a PEP 8)
├── tests/
├── requirements.txt
└── requirements-dev.txt
```

| Arquivo (em `mifitness_reinterpreter/`) | Responsabilidade |
|---|---|
| `config.py` | Fuso, chaves do CSV, pesos e **todos os limiares** dos scores |
| `extract.py` | Lê o CSV bruto em chunks, filtra mês/chave, remove duplicatas |
| `parsers.py` | JSON do campo `Value` -> colunas numéricas; epoch -> dia local |
| `scoring.py` | Funções **puras** de score (sem I/O, fáceis de testar) |
| `metrics.py` | Uma `Metrica` por indicador (bruto -> tabela diária) + registro `METRICAS` |
| `report.py` | Semanas, score global e formatação do texto |
| `cli.py` | Argumentos e orquestração |

### Adicionar uma métrica (ex.: estresse)

1. Escreva `diario_estresse(raw)` em `metrics.py` (devolve DataFrame indexado por `data` com coluna `score`).
2. Crie uma `Metrica(...)` e acrescente em `METRICAS`, com `peso` e os `Campo`s do relatório.
3. Ajuste os pesos em `config.py` para somarem 1. O score global e o relatório não precisam mudar.

## Como o relatório trata os dados

- **Sonecas não entram na média do sono.** O score do dia é o da sessão mais longa; as sonecas ficam em `soneca_min`.
- **Score global sem `fillna(0)`.** Dia sem leitura de uma métrica renormaliza os pesos das demais (e exige pelo menos 2 métricas).
- **Semanas com contagem de dias** no cabeçalho: a semana 4 vai do dia 22 ao fim do mês e pode ter até 10 dias, então compare pela média diária, não pelo total.
- Leitura do bruto em chunks, só com as colunas necessárias, filtrando por epoch antes de converter datas; duplicatas `(Key, Time)` são removidas.

## Limitações conhecidas

- Um dia que tenha **só** uma soneca registrada (sem sono noturno) tem essa soneca pontuada como sono principal.
- Os limiares dos scores são heurísticos e ficam perto do teto (cardíaco e sono); recalibrar contra a sua própria linha de base é um passo à parte.
- Os pesos do score global (sono 45%, cardíaco 35%, passos 20%) também são heurísticos.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```
