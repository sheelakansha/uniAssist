import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ingestion.engine import IngestionEngine
if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--metadata-only',action='store_true')
    args=parser.parse_args(); print(IngestionEngine().sync_all(metadata_only=args.metadata_only))
