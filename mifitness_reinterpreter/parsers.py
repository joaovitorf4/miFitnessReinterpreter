"""Converte o campo `Value` (JSON em texto) do CSV bruto em colunas numéricas."""
from __future__ import annotations

import json
from typing import Sequence

import pandas as pd

from .config import TZ


def _json_ou_vazio(texto) -> dict:
    """Faz o parse de UMA célula; qualquer valor inválido vira {} (nada de `except:` solto)."""
    try:
        dado = json.loads(texto)
    except (TypeError, ValueError):
        return {}
    return dado if isinstance(dado, dict) else {}


def extrair_campos(valores: pd.Series, campos: Sequence[str]) -> pd.DataFrame:
    """Uma única passada de json.loads por linha; campos ausentes viram NaN."""
    registros = [{k: d.get(k) for k in campos} for d in map(_json_ou_vazio, valores)]
    df = pd.DataFrame(registros, columns=list(campos), index=valores.index)
    return df.apply(pd.to_numeric, errors="coerce")


def epoch_para_dia_local(epoch: pd.Series) -> pd.Series:
    """Epoch (s) -> data local (meia-noite, sem fuso). Mantém dtype datetime64 (não `object`)."""
    local = pd.to_datetime(epoch, unit="s", utc=True).dt.tz_convert(TZ)
    return local.dt.tz_localize(None).dt.normalize()
