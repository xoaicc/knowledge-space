import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Database Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "knowledge_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5434")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Hugging Face Model Configuration
# Models will automatically download on first run to standard HF cache directory
CACHE_DIR = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-base")

# Vector Search Dimensions
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))

# Hybrid RRF Search Settings
DEFAULT_TOP_K = 10
RRF_K = 60
RERANK_THRESHOLD = 0.0
