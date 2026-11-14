"""
El "cerebro" del RAG: recibe una pregunta y devuelve una respuesta
basada solamente en los PDFs cargados con ingest.py.

Pasos:
  1. Convierte la pregunta en un vector (embedding).
  2. Busca en ChromaDB los fragmentos más parecidos.
  3. Le pasa esos fragmentos + la pregunta al modelo de Ollama.
  4. Devuelve la respuesta y de qué archivo/página salió.

Se puede probar solo, desde la consola, ejecutando este archivo.
"""
import chromadb
import ollama

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBED_MODEL,
    FRAGMENTOS_POR_CONSULTA,
    LLM_MODEL,
)

# qwen3-embedding funciona mejor si a la PREGUNTA (no a los documentos)
# se le antepone esta instrucción, tal como indica su documentación.
INSTRUCCION_BUSQUEDA = (
    "Instruct: Given a question, retrieve relevant passages that answer the question\n"
    "Query: "
)

PROMPT_SISTEMA = """Sos un asistente que responde preguntas usando ÚNICAMENTE la información de los documentos que se te pasan.

Reglas:
- Respondé siempre en español, de forma clara y breve.
- Si la respuesta no está en los documentos, decí que no encontraste esa información. No inventes nada.
- No uses conocimiento propio que no esté en los documentos."""

_coleccion = None


def obtener_coleccion():
    """Abre la colección de ChromaDB una sola vez y la reutiliza."""
    global _coleccion
    if _coleccion is None:
        cliente = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _coleccion = cliente.get_collection(COLLECTION_NAME)
    return _coleccion


def buscar_fragmentos(pregunta, cantidad=FRAGMENTOS_POR_CONSULTA):
    """Devuelve una lista de (texto, metadatos) con los fragmentos más relevantes."""
    vector = ollama.embed(model=EMBED_MODEL, input=INSTRUCCION_BUSQUEDA + pregunta).embeddings[0]
    resultado = obtener_coleccion().query(query_embeddings=[vector], n_results=cantidad)
    return list(zip(resultado["documents"][0], resultado["metadatas"][0]))


def armar_contexto(fragmentos):
    """Une los fragmentos en un solo texto, indicando de dónde sale cada uno."""
    partes = []
    for i, (texto, meta) in enumerate(fragmentos, start=1):
        partes.append(f"[{i}] ({meta['archivo']}, página {meta['pagina']})\n{texto}")
    return "\n\n".join(partes)


def responder(pregunta):
    """Devuelve (respuesta, fuentes). Fuentes es una lista de (archivo, página)."""
    fragmentos = buscar_fragmentos(pregunta)
    contexto = armar_contexto(fragmentos)

    mensajes = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": f"Documentos:\n{contexto}\n\nPregunta: {pregunta}"},
    ]

    respuesta = ollama.chat(
        model=LLM_MODEL,
        messages=mensajes,
        think=False,                    # sin "modo razonamiento": responde mucho más rápido
        options={"temperature": 0.2},   # bajo = respuestas más fieles al texto, menos creativas
    )

    fuentes = sorted({(meta["archivo"], meta["pagina"]) for _, meta in fragmentos})
    return respuesta.message.content.strip(), fuentes


def main():
    try:
        obtener_coleccion()
    except Exception:
        print("No encontré la base de documentos. Ejecutá primero ingest.py.")
        return

    print("Hacé preguntas sobre tus PDFs. Escribí 'salir' para terminar.\n")
    while True:
        pregunta = input("Pregunta: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            break
        if not pregunta:
            continue

        respuesta, fuentes = responder(pregunta)
        print(f"\nRespuesta: {respuesta}")
        print("Fuentes: " + ", ".join(f"{archivo} (pág. {pagina})" for archivo, pagina in fuentes))
        print()


if __name__ == "__main__":
    main()