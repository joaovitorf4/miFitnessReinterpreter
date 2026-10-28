"""Interface de linha de comando."""
from __future__ import annotations

import argparse
import glob
import logging
import sys
from pathlib import Path

from .config import ARQUIVO_PADRAO_GLOB
from .extract import carregar_mes, mes_mais_recente, salvar_intermediarios
from .report import gerar_relatorio_completo

log = logging.getLogger("mifitness_reinterpreter")


def _mes_arg(texto: str) -> tuple[int, int]:
    try:
        ano, mes = texto.split("-")
        ano, mes = int(ano), int(mes)
        if not 1 <= mes <= 12:
            raise ValueError
        return ano, mes
    except ValueError:
        raise argparse.ArgumentTypeError("use o formato AAAA-MM (ex.: 2026-09)")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="miFitnessReinterpreter: relatório de saúde a partir do export do Mi Fitness (passos, sono e frequência cardíaca).")
    p.add_argument("arquivo", nargs="?", help=f"CSV bruto do Mi Fitness (padrão: o mais recente de {ARQUIVO_PADRAO_GLOB})")
    p.add_argument("--mes", type=_mes_arg, metavar="AAAA-MM",
                   help="mês a analisar (padrão: mês do registro mais recente do arquivo)")
    p.add_argument("--salvar-intermediarios", metavar="PASTA",
                   help="grava um CSV por chave (sleep/steps/heart_rate) na pasta indicada")
    return p


def _resolver_arquivo(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    candidatos = sorted(glob.glob(ARQUIVO_PADRAO_GLOB))
    if not candidatos:
        raise FileNotFoundError(f"Nenhum arquivo em {ARQUIVO_PADRAO_GLOB}; informe o caminho.")
    return Path(candidatos[-1])  # prefixo AAAAMMDD => o último é o mais recente


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parser().parse_args(argv)

    try:
        caminho = _resolver_arquivo(args.arquivo)
        ano, mes = args.mes or mes_mais_recente(caminho)
        log.info("Arquivo: %s | Referência: %02d/%d", caminho.name, mes, ano)
        dados = carregar_mes(caminho, ano, mes)
        if args.salvar_intermediarios:
            salvar_intermediarios(dados, args.salvar_intermediarios, ano, mes)
    except FileNotFoundError as e:
        log.error("Arquivo não encontrado: %s", e)
        return 1

    print()
    print(gerar_relatorio_completo(dados, ano, mes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
