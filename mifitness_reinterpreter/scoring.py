"""Funções PURAS de score (sem I/O, sem pandas): recebem números, devolvem números."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from . import config as c


def _ou_zero(x) -> float:
    """Trata None/NaN como 0 (campo ausente no registro bruto)."""
    return 0.0 if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def _sobe(x: float, minimo: float, alvo: float, pontos: float) -> float:
    """0 em `minimo`, `pontos` em `alvo`, linear no meio (com saturação)."""
    return pontos * min(1.0, max(0.0, (x - minimo) / (alvo - minimo)))


def _desce(x: float, ok_ate: float, zero_em: float, pontos: float) -> float:
    """`pontos` até `ok_ate`, 0 em `zero_em`, linear no meio (com saturação)."""
    return pontos * min(1.0, max(0.0, (zero_em - x) / (zero_em - ok_ate)))


# --------------------------------------------------------------------------- passos
def score_passos(passos: float) -> float:
    passos = _ou_zero(passos)
    if passos <= 0:
        return 0.0
    if passos >= c.PASSOS_TETO:
        return 100.0
    return min(100.0, c.PASSOS_A * math.log(c.PASSOS_B * passos + 1))


# --------------------------------------------------------------------------- sono
def score_sono(duracao: float, deep: float = 0, rem: float = 0,
               acordado: float = 0, respiracao: float = 0) -> float:
    """Score (0-100) de UMA sessão de sono. Durações em minutos."""
    t = _ou_zero(duracao)
    if t == 0:
        return 0.0
    deep, rem = _ou_zero(deep), _ou_zero(rem)
    acordado, respiracao = _ou_zero(acordado), _ou_zero(respiracao)

    if t <= c.SONO_TST_IDEAL_MAX:
        s_tst = _sobe(t, c.SONO_TST_ZERO_ABAIXO, c.SONO_TST_IDEAL_MIN, c.SONO_PTS_TST)
    else:
        s_tst = _desce(t, c.SONO_TST_IDEAL_MAX, c.SONO_TST_ZERO_ACIMA, c.SONO_PTS_TST)

    s_deep = _sobe(deep / t, 0, c.SONO_DEEP_ALVO, c.SONO_PTS_DEEP)
    s_rem = _sobe(rem / t, 0, c.SONO_REM_ALVO, c.SONO_PTS_REM)

    eficiencia = t / (t + acordado)
    s_ef = _sobe(eficiencia, c.SONO_EFICIENCIA_MIN, c.SONO_EFICIENCIA_ALVO, c.SONO_PTS_EFICIENCIA)
    s_cont = _desce(acordado, c.SONO_DESPERTO_OK, c.SONO_DESPERTO_ZERO, c.SONO_PTS_CONTINUIDADE)
    s_resp = _sobe(respiracao, c.SONO_RESP_MIN, c.SONO_RESP_ALVO, c.SONO_PTS_RESPIRACAO)

    return round(s_tst + s_deep + s_rem + s_ef + s_cont + s_resp, 2)


# --------------------------------------------------------------------------- cardíaco
def score_cardiaco_diario(bpm: Iterable[float]) -> float:
    """Score (0-100) de um dia, a partir de todas as leituras de bpm do dia."""
    v = np.asarray(list(bpm), dtype=float)
    v = v[~np.isnan(v)]
    if v.size == 0:
        return 0.0

    p5 = np.percentile(v, 5)
    sd = np.std(v)
    recuperacao = (v <= c.CARD_BPM_REPOUSO).mean()
    maximo = v.max()

    lo, hi = c.CARD_P5_FAIXA
    if p5 < lo:
        s1 = _sobe(p5, c.CARD_P5_ZERO_ABAIXO, lo, c.CARD_PTS_P5)
    else:
        s1 = _desce(p5, hi, c.CARD_P5_ZERO_ACIMA, c.CARD_PTS_P5)
    s2 = _sobe(sd, c.CARD_SD_MIN, c.CARD_SD_ALVO, c.CARD_PTS_SD)
    s3 = _sobe(recuperacao, c.CARD_RECUP_MIN, c.CARD_RECUP_ALVO, c.CARD_PTS_RECUP)
    s4 = _sobe(maximo, c.CARD_MAX_MIN, c.CARD_MAX_ALVO, c.CARD_PTS_MAX)

    return round(s1 + s2 + s3 + s4, 2)
