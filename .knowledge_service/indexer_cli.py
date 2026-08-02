import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.indexer import KnowledgeIndexer

if __name__ == "__main__":
    force_mode = "--force" in sys.argv
    indexer = KnowledgeIndexer()
    indexer.run_indexing(force=force_mode)
