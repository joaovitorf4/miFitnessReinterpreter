import pandas as pd

from mifitness_reinterpreter.extract import carregar_mes, limites_do_mes, mes_mais_recente, salvar_intermediarios

from .helpers import epoch_local


def test_limites_do_mes_incluem_so_o_mes_no_fuso_local():
    t0, t1 = limites_do_mes(2026, 9)
    assert t0 == epoch_local("2026-09-01 00:00")
    assert t1 == epoch_local("2026-10-01 00:00")


def test_limites_virada_de_ano():
    _, t1 = limites_do_mes(2026, 12)
    assert t1 == epoch_local("2027-01-01 00:00")


def _csv(tmp_path):
    linhas = [
        # Key, Time, Value, UpdateTime
        ("steps", epoch_local("2026-09-01 10:00"), '{"time":1,"steps":10}', 100),
        ("steps", epoch_local("2026-09-01 10:00"), '{"time":1,"steps":99}', 200),   # duplicata mais nova
        ("steps", epoch_local("2026-08-31 23:59"), '{"time":1,"steps":5}', 100),    # mês anterior
        ("steps", epoch_local("2026-10-01 00:00"), '{"time":1,"steps":5}', 100),    # mês seguinte
        ("heart_rate", epoch_local("2026-09-15 12:00"), '{"time":1,"bpm":70}', 100),
        ("stress", epoch_local("2026-09-15 12:00"), '{"x":1}', 100),                 # chave ignorada
    ]
    df = pd.DataFrame(linhas, columns=["Key", "Time", "Value", "UpdateTime"])
    df.insert(0, "Uid", 1)
    df.insert(1, "Sid", "abc")
    caminho = tmp_path / "bruto.csv"
    df.to_csv(caminho, index=False)
    return caminho


def test_carregar_mes_filtra_mes_chave_e_deduplica(tmp_path):
    dados = carregar_mes(_csv(tmp_path), 2026, 9, tamanho_chunk=2)
    assert set(dados) == {"sleep", "steps", "heart_rate"}
    assert len(dados["steps"]) == 1 and '"steps":99' in dados["steps"]["Value"].iloc[0]
    assert len(dados["heart_rate"]) == 1
    assert dados["sleep"].empty
    assert list(dados["steps"].columns) == ["Time", "Value", "UpdateTime"]


def test_mes_mais_recente(tmp_path):
    # o registro mais recente é 01/10 00:00 (início de outubro)
    assert mes_mais_recente(_csv(tmp_path)) == (2026, 10)


def test_salvar_intermediarios(tmp_path):
    dados = carregar_mes(_csv(tmp_path), 2026, 9)
    salvar_intermediarios(dados, tmp_path / "saida", 2026, 9)
    assert (tmp_path / "saida" / "steps_data_09_2026.csv").exists()
    assert (tmp_path / "saida" / "sleep_data_09_2026.csv").exists()
