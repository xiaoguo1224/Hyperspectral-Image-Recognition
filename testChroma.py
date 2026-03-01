from langchain_chroma import Chroma

from rag.config import Config
from rag.vector_store import VectorStore

vector_store = VectorStore(
    Config.DB_DIR,
    Config.EMBEDDING_MODEL,
    Config.OLLAMA_BASE_URL
)

db = vector_store.load_vectorstore()

results = vector_store.similarity_search(
    "What is the main contribution of the paper?",
    k=5
)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")
