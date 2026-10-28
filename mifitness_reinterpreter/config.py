"""Constantes do projeto: fuso, chaves do CSV, pesos e limiares dos scores.

Tudo que é "número mágico" fica aqui, para ajustar sem tocar na lógica.
"""
from __future__ import annotations

# --- Dados -----------------------------------------------------------------
TZ = "America/Sao_Paulo"
ARQUIVO_PADRAO_GLOB = "data/*_MiFitness_hlth_center_fitness_data.csv"

KEY_PASSOS = "steps"
KEY_SONO = "sleep"
KEY_CARDIACO = "heart_rate"

# --- Semanas ---------------------------------------------------------------
# Dias 1-7, 8-14, 15-21 e 22 até o fim do mês (a última semana pode ter até 10 dias).
DIAS_POR_SEMANA = 7
N_SEMANAS = 4
ROTULOS_SEMANA = ("Dias 01 a 07", "Dias 08 a 14", "Dias 15 a 21", "Dia 22 ao fim")

# --- Score global ----------------------------------------------------------
# Pesos heurísticos (somam 1.0). Se uma métrica faltar num dia, os pesos das
# demais são renormalizados em vez de tratar a falta como zero.
PESO_SONO = 0.45
PESO_CARDIACO = 0.35
PESO_PASSOS = 0.20
# Um dia só recebe score global se tiver pelo menos N métricas disponíveis.
GLOBAL_MIN_METRICAS = 2

# --- Passos: score = A * ln(B * passos + 1), saturando em 100 ---------------
PASSOS_A = 51.70184
PASSOS_B = 0.00036989
PASSOS_TETO = 16000

# --- Sono (pontos máximos somam 100) ---------------------------------------
SONO_PTS_TST, SONO_PTS_DEEP, SONO_PTS_REM = 30, 20, 20
SONO_PTS_EFICIENCIA, SONO_PTS_CONTINUIDADE, SONO_PTS_RESPIRACAO = 15, 10, 5

SONO_TST_ZERO_ABAIXO = 240      # min: abaixo disso, 0 pontos de duração
SONO_TST_IDEAL_MIN = 420        # min: a partir daqui, pontuação cheia
SONO_TST_IDEAL_MAX = 540        # min: acima disso começa a penalizar
SONO_TST_ZERO_ACIMA = 990       # min: zera (equivale a -1 ponto a cada 15 min)
SONO_DEEP_ALVO = 0.15           # fração do sono total
SONO_REM_ALVO = 0.20
SONO_EFICIENCIA_MIN = 0.50      # abaixo: 0 pontos
SONO_EFICIENCIA_ALVO = 0.85
SONO_DESPERTO_OK = 20           # min acordado sem penalidade
SONO_DESPERTO_ZERO = 70         # min acordado que zera a continuidade
SONO_RESP_MIN = 70
SONO_RESP_ALVO = 95

# --- Cardíaco (pontos máximos somam 100) -----------------------------------
CARD_PTS_P5, CARD_PTS_SD, CARD_PTS_RECUP, CARD_PTS_MAX = 35, 25, 20, 20

CARD_P5_FAIXA = (45, 65)        # bpm: percentil 5 nessa faixa = pontuação cheia
CARD_P5_ZERO_ABAIXO = 35
CARD_P5_ZERO_ACIMA = 85
CARD_SD_MIN, CARD_SD_ALVO = 5, 15
CARD_BPM_REPOUSO = 75           # "recuperação" = fração das leituras <= 75 bpm
CARD_RECUP_MIN, CARD_RECUP_ALVO = 0.20, 0.55
CARD_MAX_MIN, CARD_MAX_ALVO = 90, 115
