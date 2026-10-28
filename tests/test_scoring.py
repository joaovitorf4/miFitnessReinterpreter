import math

import pytest

from mifitness_reinterpreter.scoring import score_cardiaco_diario, score_passos, score_sono


# ------------------------------------------------------------------ passos
@pytest.mark.parametrize("entrada", [0, -5, None, float("nan")])
def test_passos_invalidos_ou_zero_valem_zero(entrada):
    assert score_passos(entrada) == 0.0


def test_passos_saturam_em_100_a_partir_do_teto():
    assert score_passos(16000) == 100.0
    assert score_passos(30000) == 100.0


def test_passos_valor_de_referencia_e_monotonia():
    assert score_passos(10000) == pytest.approx(80.0, abs=0.01)
    valores = [score_passos(p) for p in range(0, 16001, 500)]
    assert valores == sorted(valores)


# ------------------------------------------------------------------ sono
def test_sono_noite_boa():
    assert score_sono(535, 149, 70, 1, 96) == 93.08


def test_sono_duracao_zero_vale_zero():
    assert score_sono(0) == 0.0


def test_sono_longo_demais_zera_so_o_componente_de_duracao():
    # 990 min => 0 pts de duração; os outros 30 pts vêm de eficiência/continuidade/respiração
    assert score_sono(990, 0, 0, 0, 100) == 30.0


def test_sono_campos_ausentes_contam_como_zero():
    assert score_sono(300, float("nan"), None, float("nan"), float("nan")) == score_sono(300)


def test_sono_soneca_sem_estagios_ganha_25_pts_de_graca():
    """Documenta POR QUE sonecas não podem entrar na média do dia."""
    assert score_sono(75, 0, float("nan"), 0, float("nan")) == 25.0


# ------------------------------------------------------------------ cardíaco
def test_cardiaco_sem_leituras_vale_zero():
    assert score_cardiaco_diario([]) == 0.0
    assert score_cardiaco_diario([float("nan")]) == 0.0


def test_cardiaco_fc_constante_perde_variabilidade_e_pico():
    # p5 ok (35) + sd 0 (0) + 100% das leituras <= 75 (20) + máx 60 (0)
    assert score_cardiaco_diario([60] * 100) == 55.0


def test_cardiaco_dia_variado_com_pico():
    assert score_cardiaco_diario(list(range(50, 121))) == pytest.approx(89.5)


def test_scores_ficam_entre_0_e_100():
    for bpm in ([40], [200] * 10, list(range(30, 220))):
        assert 0 <= score_cardiaco_diario(bpm) <= 100
    for t in (1, 100, 300, 480, 700, 2000):
        assert 0 <= score_sono(t, t * .2, t * .2, 500, 100) <= 100
        assert not math.isnan(score_sono(t))
