"""Agregação semanal, score global e formatação do relatório (devolve texto; quem imprime é a CLI)."""
from __future__ import annotations

import logging
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from . import config as c
from .metrics import METRICAS, Campo, Metrica

log = logging.getLogger(__name__)
SEPARADOR = "=" * 60


# --------------------------------------------------------------------------- semanas
def semana_do_mes(datas: pd.DatetimeIndex) -> np.ndarray:
    """1..N_SEMANAS; a última semana absorve os dias restantes do mês."""
    return np.minimum((datas.day - 1) // c.DIAS_POR_SEMANA + 1, c.N_SEMANAS)


def _agregar(serie: pd.Series, agg: str) -> float:
    return float(getattr(serie, agg)())


# --------------------------------------------------------------------------- global
def consolidar_global(diarios: Mapping[str, pd.DataFrame],
                      metricas: Sequence[Metrica] = METRICAS) -> pd.DataFrame:
    """Média ponderada dos scores diários, renormalizando os pesos quando falta uma métrica.

    Dia sem leitura NÃO é tratado como score 0. Dias com menos de GLOBAL_MIN_METRICAS
    métricas ficam sem score global (NaN).
    """
    ativas = [m for m in metricas if m.nome in diarios]
    scores = pd.concat({m.nome: diarios[m.nome]["score"] for m in ativas}, axis=1, sort=True)
    pesos = pd.Series({m.nome: m.peso for m in ativas})

    validos = scores.notna()
    peso_disponivel = validos.mul(pesos, axis=1).sum(axis=1)
    geral = scores.fillna(0).mul(pesos, axis=1).sum(axis=1) / peso_disponivel
    geral = geral.where(validos.sum(axis=1) >= min(c.GLOBAL_MIN_METRICAS, len(ativas)))

    out = scores.add_prefix("score_")
    out["score_geral"] = geral
    out["semana"] = semana_do_mes(out.index)
    return out


# --------------------------------------------------------------------------- texto
def _linhas_campos(df: pd.DataFrame, campos: Sequence[Campo], indent: str) -> list[str]:
    return [f"{indent}{f.rotulo}: {f.fmt(_agregar(df[f.coluna], f.agg))}" for f in campos]


def relatorio_metrica(m: Metrica, diario: pd.DataFrame, ano: int, mes: int) -> str:
    """Resumo mensal + semanal de uma métrica (mesmo layout para todas)."""
    semana = semana_do_mes(diario.index)
    linhas = [f"[ RELATÓRIO DE {m.titulo} ]", "",
              f"--- RESULTADOS {m.titulo}: {mes:02d}/{ano} ---"]
    linhas += _linhas_campos(diario, m.campos_mes, "")
    linhas.append(f"SCORE MENSAL MÉDIO: {diario['score'].mean():.1f} / 100")
    linhas += ["", f"Desempenho por Semana ({m.titulo.capitalize()}):"]

    for n in range(1, c.N_SEMANAS + 1):
        sub = diario[semana == n]
        if sub.empty:
            continue
        linhas.append(f"  Semana {n} ({c.ROTULOS_SEMANA[n - 1]}, {len(sub)} dias):")
        linhas += _linhas_campos(sub, m.campos_semana, "    - ")
        linhas.append(f"    - Score da Sem:  {sub['score'].mean():.1f} / 100")
    linhas.append(SEPARADOR)
    return "\n".join(linhas)


def relatorio_global(df: pd.DataFrame) -> str:
    linhas = ["[ RELATÓRIO GLOBAL DE SAÚDE ]", "", "--- RESULTADO GLOBAL INTEGRADO ---",
              f"SCORE GERAL MENSAL MÉDIO: {df['score_geral'].mean():.1f} / 100", ""]
    for n in range(1, c.N_SEMANAS + 1):
        sub = df[df["semana"] == n]
        if sub.empty:
            continue
        validos = int(sub["score_geral"].notna().sum())
        linhas.append(f"  Semana {n} ({c.ROTULOS_SEMANA[n - 1]}, {validos} dias): "
                      f"{sub['score_geral'].mean():.1f} / 100")
    linhas.append(SEPARADOR)
    return "\n".join(linhas)


def gerar_relatorio_completo(dados: Mapping[str, pd.DataFrame], ano: int, mes: int,
                             metricas: Sequence[Metrica] = METRICAS) -> str:
    """Pipeline: registros brutos por chave -> tabelas diárias -> relatórios + global."""
    diarios, blocos = {}, []
    for m in metricas:
        raw = dados.get(m.key)
        if raw is None or raw.empty:
            log.warning("Sem registros de '%s' em %02d/%d; métrica ignorada.", m.key, mes, ano)
            continue
        diarios[m.nome] = m.diario(raw)
        blocos.append(relatorio_metrica(m, diarios[m.nome], ano, mes))

    if not diarios:
        return "Nenhum dado encontrado para o período."
    blocos.append(relatorio_global(consolidar_global(diarios, metricas)))
    return "\n\n".join(blocos)
