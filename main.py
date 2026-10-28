"""miFitnessReinterpreter — atalho: `python main.py [arquivo.csv] [--mes AAAA-MM]`."""
import sys

from mifitness_reinterpreter.cli import main

if __name__ == "__main__":
    sys.exit(main())
