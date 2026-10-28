import pandas as pd
import pytest

from mifitness_reinterpreter.metrics import diario_cardiaco, diario_passos, diario_sono
from mifitness_reinterpreter.parsers import extrair_campos

from .helpers import epoch_local, raw


def _noite(acordou: str, dur=500, deep=150, rem=85, awake=5, resp=97) -> dict:
    return {"wake_up_time": epoch_local(acordou), "duration": dur, "sleep_deep_duration": deep,
            "sleep_rem_duration": rem, "sleep_awake_duration": awake, "breath_quality": resp}


# ------------------------------------------------------------------ sono
def test_soneca_nao_derruba_o_score_do_dia():
    """Regressão: antes, a média com a soneca fazia 95.8 virar 60.4."""
    noite = _noite("2026-09-20 08:50")
    soneca = {"wake_up_time": epoch_local("2026-09-20 14:26"), "duration": 26,
              "sleep_deep_duration": 0, "sleep_light_duration": 0, "sleep_awake_duration": 0}

    sozinho = diario_sono(raw([noite], "wake_up_time"))
    com_soneca = diario_sono(raw([soneca, noite], "wake_up_time"))

    assert len(com_soneca) == 1
    assert com_soneca["score"].iloc[0] == sozinho["score"].iloc[0]
    assert com_soneca["duracao_h"].iloc[0] == pytest.approx(500 / 60)
    assert com_soneca["soneca_min"].iloc[0] == 26
    assert sozinho["soneca_min"].iloc[0] == 0


def test_sono_e_datado_pelo_despertar_no_fuso_local():
    # 02:30 UTC de 20/09 = 23:30 de 19/09 em Brasília
    r = raw([_noite("2026-09-19 23:30")], "wake_up_time")
    assert list(diario_sono(r).index) == [pd.Timestamp("2026-09-19")]


def test_sono_dias_distintos_geram_linhas_distintas():
    r = raw([_noite("2026-09-01 08:00"), _noite("2026-09-02 08:00", dur=300)], "wake_up_time")
    out = diario_sono(r)
    assert list(out.index) == [pd.Timestamp("2026-09-01"), pd.Timestamp("2026-09-02")]
    assert out["score"].iloc[0] > out["score"].iloc[1]


# ------------------------------------------------------------------ passos
def test_passos_somam_por_dia_local_e_ignoram_json_invalido():
    regs = [{"time": epoch_local("2026-09-01 10:00"), "steps": 100},
            {"time": epoch_local("2026-09-01 10:01"), "steps": 50},
            {"time": epoch_local("2026-09-02 00:01"), "steps": 7}]
    df = raw(regs, "time")
    df.loc[len(df)] = [epoch_local("2026-09-01 11:00"), "isto não é json", 0]
    df.loc[len(df)] = [epoch_local("2026-09-01 12:00"), None, 0]

    out = diario_passos(df)
    assert out["passos"].to_dict() == {pd.Timestamp("2026-09-01"): 150.0,
                                       pd.Timestamp("2026-09-02"): 7.0}


# ------------------------------------------------------------------ cardíaco
def test_cardiaco_gera_um_score_por_dia():
    regs = [{"time": epoch_local("2026-09-01 10:00") + 60 * i, "bpm": 60 + i % 30} for i in range(100)]
    regs += [{"time": epoch_local("2026-09-02 10:00") + 60 * i, "bpm": 70} for i in range(100)]
    out = diario_cardiaco(raw(regs, "time"))
    assert list(out.columns) == ["score"]
    assert len(out) == 2 and out["score"].between(0, 100).all()


# ------------------------------------------------------------------ parser
def test_extrair_campos_tolera_lixo_e_campos_ausentes():
    s = pd.Series(['{"a": 1, "b": 2}', "quebrado", None, "[1, 2]", '{"a": 5}'])
    df = extrair_campos(s, ["a", "b"])
    assert df["a"].tolist()[0] == 1 and df["a"].tolist()[4] == 5
    assert df["a"].isna().tolist() == [False, True, True, True, False]
    assert df["b"].isna().tolist() == [False, True, True, True, True]
