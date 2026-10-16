#!/usr/bin/env python3
"""Stage files into a package manager's private build root, never the host."""
import argparse
from pathlib import Path
from payload import stage

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    stage(parser.parse_args().destination)

