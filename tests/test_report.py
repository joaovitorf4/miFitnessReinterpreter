import numpy as np
import pandas as pd
import pytest

from mifitness_reinterpreter.metrics import METRICAS
from mifitness_reinterpreter.report import consolidar_global, gerar_relatorio_completo, semana_do_mes

from .helpers import epoch_local, raw


def _diario(scores: dict[str, float]) -> pd.DataFrame:
    idx = pd.DatetimeIndex(list(scores), name="data")
    return pd.DataFrame({"score": list(scores.values())}, index=idx)


# ------------------------------------------------------------------ semanas
@pytest.mark.parametrize("dia,semana", [(1, 1), (7, 1), (8, 2), (14, 2), (15, 3), (21, 3),
                                        (22, 4), (28, 4), (31, 4)])
def test_semana_do_mes(dia, semana):
    datas = pd.DatetimeIndex([f"2026-10-{dia:02d}"])
    assert semana_do_mes(datas)[0] == semana


# ------------------------------------------------------------------ global
def test_global_completo_usa_os_pesos():
    d = {"sono": _diario({"2026-09-01": 100.0}),
         "cardiaco": _diario({"2026-09-01": 50.0}),
         "passos": _diario({"2026-09-01": 0.0})}
    g = consolidar_global(d)
    assert g["score_geral"].iloc[0] == pytest.approx(100 * .45 + 50 * .35 + 0 * .20)


def test_global_dia_sem_sono_nao_e_tratado_como_zero():
    d = {"sono": _diario({"2026-09-01": 90.0}),
         "cardiaco": _diario({"2026-09-01": 80.0, "2026-09-02": 80.0}),
         "passos": _diario({"2026-09-01": 70.0, "2026-09-02": 70.0})}
    g = consolidar_global(d)
    # dia 2: sem sono -> média ponderada só de cardíaco e passos (pesos renormalizados)
    esperado = (80 * .35 + 70 * .20) / (.35 + .20)
    assert g.loc["2026-09-02", "score_geral"] == pytest.approx(esperado)
    assert g.loc["2026-09-02", "score_sono"] != g.loc["2026-09-02", "score_sono"]  # NaN, não 0


def test_global_dia_com_uma_unica_metrica_fica_sem_score():
    d = {"sono": _diario({"2026-09-01": 90.0}),
         "cardiaco": _diario({"2026-09-02": 80.0}),
         "passos": _diario({"2026-09-02": 70.0})}
    g = consolidar_global(d)
    assert np.isnan(g.loc["2026-09-01", "score_geral"])
    assert not np.isnan(g.loc["2026-09-02", "score_geral"])


# ------------------------------------------------------------------ pipeline
def _dados_sinteticos():
    passos = [{"time": epoch_local("2026-09-01 10:00") + 60 * i, "steps": 100} for i in range(30)]
    bpm = [{"time": epoch_local("2026-09-01 10:00") + 60 * i, "bpm": 60 + i} for i in range(60)]
    sono = [{"wake_up_time": epoch_local("2026-09-01 08:00"), "duration": 480,
             "sleep_deep_duration": 100, "sleep_rem_duration": 100, "breath_quality": 96}]
    return {"steps": raw(passos, "time"), "heart_rate": raw(bpm, "time"),
            "sleep": raw(sono, "wake_up_time")}


def test_relatorio_completo_contem_todas_as_secoes():
    txt = gerar_relatorio_completo(_dados_sinteticos(), 2026, 9)
    for trecho in ("RESULTADOS PASSOS: 09/2026", "RESULTADOS SONO: 09/2026",
                   "RESULTADOS CARDÍACO: 09/2026", "SCORE GERAL MENSAL MÉDIO", "Semana 1"):
        assert trecho in txt


def test_relatorio_ignora_metrica_sem_registros():
    dados = _dados_sinteticos()
    dados["sleep"] = dados["sleep"].iloc[0:0]
    txt = gerar_relatorio_completo(dados, 2026, 9)
    assert "RESULTADOS SONO" not in txt and "SCORE GERAL MENSAL MÉDIO" in txt


def test_relatorio_sem_nenhum_dado():
    vazio = {m.key: pd.DataFrame(columns=["Time", "Value", "UpdateTime"]) for m in METRICAS}
    assert gerar_relatorio_completo(vazio, 2026, 9) == "Nenhum dado encontrado para o período."
