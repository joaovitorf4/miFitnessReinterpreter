"""Leitura do CSV bruto do Mi Fitness: filtra o mês e separa por chave, tudo em memória."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import KEY_CARDIACO, KEY_PASSOS, KEY_SONO, TZ

log = logging.getLogger(__name__)

KEYS_PADRAO = (KEY_SONO, KEY_PASSOS, KEY_CARDIACO)
COLUNAS = ["Key", "Time", "Value", "UpdateTime"]


def limites_do_mes(ano: int, mes: int) -> tuple[int, int]:
    """Intervalo [inicio, fim) do mês em epoch (s), no fuso local."""
    inicio = pd.Timestamp(year=ano, month=mes, day=1, tz=TZ)
    fim = inicio + pd.offsets.MonthBegin(1)
    return int(inicio.timestamp()), int(fim.timestamp())


def mes_mais_recente(caminho: str | Path) -> tuple[int, int]:
    """(ano, mês) do registro mais recente do arquivo — lê só a coluna Time."""
    ultimo = pd.read_csv(caminho, usecols=["Time"])["Time"].max()
    dt = pd.Timestamp(int(ultimo), unit="s", tz="UTC").tz_convert(TZ)
    return dt.year, dt.month


def carregar_mes(caminho: str | Path, ano: int, mes: int,
                 keys: Iterable[str] = KEYS_PADRAO,
                 tamanho_chunk: int = 500_000) -> dict[str, pd.DataFrame]:
    """Devolve {key: DataFrame[Time, Value, UpdateTime]} só com o mês pedido.

    - lê apenas as colunas necessárias, em chunks (memória constante);
    - filtra por chave e por faixa de epoch ANTES de qualquer conversão de data;
    - remove duplicatas (Key, Time) mantendo a versão mais recente (UpdateTime).
    """
    keys = tuple(keys)
    t0, t1 = limites_do_mes(ano, mes)

    partes = []
    for chunk in pd.read_csv(caminho, usecols=COLUNAS, chunksize=tamanho_chunk):
        partes.append(chunk[chunk["Key"].isin(keys) & chunk["Time"].between(t0, t1 - 1)])
    df = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUNAS)

    df = df.sort_values("UpdateTime").drop_duplicates(["Key", "Time"], keep="last")

    dados = {}
    for k in keys:
        sub = df[df["Key"] == k].sort_values("Time").drop(columns="Key").reset_index(drop=True)
        dados[k] = sub
        log.info("  %-11s %6d registros", k, len(sub))
    return dados


def salvar_intermediarios(dados: dict[str, pd.DataFrame], pasta: str | Path,
                          ano: int, mes: int) -> None:
    """Opcional: grava um CSV por chave (ex.: sleep_data_09_2026.csv), como o script antigo fazia."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    for k, df in dados.items():
        destino = pasta / f"{k}_data_{mes:02d}_{ano}.csv"
        df.to_csv(destino, index=False)
        log.info("  -> %s", destino)
