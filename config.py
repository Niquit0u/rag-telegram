from pathlib import Path

# Carpeta raíz del proyecto (donde está este archivo)
BASE_DIR = Path(__file__).resolve().parent

# Carpetas
DOCS_DIR = BASE_DIR / "docs"          # acá van los PDFs
CHROMA_DIR = BASE_DIR / "chroma_db"   # acá se guarda la base de vectores

# Modelos de Ollama
LLM_MODEL = "qwen3.5:4b"
EMBED_MODEL = "qwen3-embedding:0.6b"

# Nombre de la colección dentro de ChromaDB
COLLECTION_NAME = "documentos"

# Fragmentación del texto (en caracteres)
TAMANO_FRAGMENTO = 800   # largo de cada pedazo
SOLAPAMIENTO = 150       # cuánto se repite entre un pedazo y el siguiente

# Cuántos fragmentos se le pasan al modelo por cada pregunta
FRAGMENTOS_POR_CONSULTA = 4