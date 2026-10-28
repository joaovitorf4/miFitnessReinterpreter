import json

import pandas as pd


def raw(registros: list[dict], campo_tempo: str, tempo0: int = 0) -> pd.DataFrame:
    """Monta um DataFrame[Time, Value, UpdateTime] como o `extract` devolveria."""
    return pd.DataFrame({
        "Time": [r[campo_tempo] for r in registros],
        "Value": [json.dumps(r) for r in registros],
        "UpdateTime": [r[campo_tempo] + 1 for r in registros],
    })


def epoch_local(texto: str) -> int:
    """'2026-09-20 08:00' (hora de Brasília) -> epoch em segundos."""
    return int(pd.Timestamp(texto, tz="America/Sao_Paulo").timestamp())
