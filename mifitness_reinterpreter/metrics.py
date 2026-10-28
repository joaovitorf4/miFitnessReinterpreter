"""Métricas: cada uma transforma os registros brutos de UMA chave em uma tabela diária.

Para adicionar uma métrica nova (HRV, estresse...), escreva `diario_xxx(raw)` e
acrescente uma `Metrica(...)` em METRICAS — o score global e o relatório não mudam.

Contrato de `diario`: recebe DataFrame[Time, Value, UpdateTime] e devolve um
DataFrame indexado por `data` (datetime64, dia local) com a coluna `score` (+ extras).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from . import config as c
from .parsers import epoch_para_dia_local, extrair_campos
from .scoring import score_cardiaco_diario, score_passos, score_sono


# --------------------------------------------------------------------------- modelos
@dataclass(frozen=True)
class Campo:
    """Um número do relatório: agg ('sum'/'mean') de uma coluna diária + como formatar."""
    rotulo: str
    coluna: str
    agg: str
    fmt: Callable[[float], str]


@dataclass(frozen=True)
class Metrica:
    nome: str                       # id usado nas colunas (score_<nome>)
    titulo: str                     # cabeçalho do relatório
    key: str                        # chave no CSV bruto
    peso: float                     # peso no score global
    diario: Callable[[pd.DataFrame], pd.DataFrame]
    campos_mes: tuple[Campo, ...] = ()
    campos_semana: tuple[Campo, ...] = ()


def _milhar(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def _horas(v: float) -> str:
    return f"{v:.1f} hrs/noite"


def _minutos(v: float) -> str:
    return f"{v:.0f} min"


# --------------------------------------------------------------------------- passos
def diario_passos(raw: pd.DataFrame) -> pd.DataFrame:
    p = extrair_campos(raw["Value"], ["time", "steps"]).dropna()
    por_dia = p["steps"].groupby(epoch_para_dia_local(p["time"])).sum().rename_axis("data")
    return pd.DataFrame({"passos": por_dia, "score": por_dia.map(score_passos)})


# --------------------------------------------------------------------------- sono
_CAMPOS_SONO = ["wake_up_time", "duration", "sleep_deep_duration",
                "sleep_rem_duration", "sleep_awake_duration", "breath_quality"]


def diario_sono(raw: pd.DataFrame) -> pd.DataFrame:
    """Um score por dia = sessão MAIS LONGA do dia (sono principal), datada pelo despertar.

    Sessões menores do mesmo dia (sonecas) não entram no score — elas não têm REM nem
    respiração e ganhariam pontos de "eficiência" de graça, puxando a média para baixo.
    Ficam registradas à parte em `soneca_min`.
    """
    s = extrair_campos(raw["Value"], _CAMPOS_SONO).dropna(subset=["wake_up_time", "duration"])
    s["data"] = epoch_para_dia_local(s["wake_up_time"])
    s["score"] = [
        score_sono(r.duration, r.sleep_deep_duration, r.sleep_rem_duration,
                   r.sleep_awake_duration, r.breath_quality)
        for r in s.itertuples()
    ]

    s = s.sort_values("duration", kind="stable")
    principal = s.groupby("data").tail(1)
    sonecas = s.drop(principal.index).groupby("data")["duration"].sum()

    principal = principal.set_index("data")
    out = pd.DataFrame({"duracao_h": principal["duration"] / 60, "score": principal["score"]})
    out["soneca_min"] = sonecas.reindex(out.index).fillna(0.0)
    return out.sort_index()


# --------------------------------------------------------------------------- cardíaco
def diario_cardiaco(raw: pd.DataFrame) -> pd.DataFrame:
    h = extrair_campos(raw["Value"], ["time", "bpm"]).dropna()
    score = h["bpm"].groupby(epoch_para_dia_local(h["time"])).apply(score_cardiaco_diario)
    return score.rename("score").rename_axis("data").to_frame()


# --------------------------------------------------------------------------- registro
METRICAS: tuple[Metrica, ...] = (
    Metrica(
        nome="passos", titulo="PASSOS", key=c.KEY_PASSOS, peso=c.PESO_PASSOS,
        diario=diario_passos,
        campos_mes=(Campo("Total de passos no mês", "passos", "sum", _milhar),
                    Campo("Média de passos por dia", "passos", "mean", _milhar)),
        campos_semana=(Campo("Passos Totais", "passos", "sum", _milhar),
                       Campo("Média Diária", "passos", "mean", _milhar)),
    ),
    Metrica(
        nome="sono", titulo="SONO", key=c.KEY_SONO, peso=c.PESO_SONO,
        diario=diario_sono,
        campos_mes=(Campo("Média de duração no mês", "duracao_h", "mean", _horas),
                    Campo("Tempo total de sonecas no mês", "soneca_min", "sum", _minutos)),
        campos_semana=(Campo("Duração Média", "duracao_h", "mean", _horas),),
    ),
    Metrica(
        nome="cardiaco", titulo="CARDÍACO", key=c.KEY_CARDIACO, peso=c.PESO_CARDIACO,
        diario=diario_cardiaco,
    ),
)
