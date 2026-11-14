"""
Carga los PDFs de la carpeta docs/ en ChromaDB.

Pasos:
  1. Lee cada PDF página por página.
  2. Corta el texto en fragmentos chicos (con un poco de solapamiento).
  3. Convierte cada fragmento en un vector con el modelo de embeddings.
  4. Guarda fragmento + vector + datos de origen (archivo y página) en ChromaDB.

Ejecutalo cada vez que agregues, cambies o borres PDFs en docs/.
"""
import chromadb
import ollama
from pypdf import PdfReader

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    DOCS_DIR,
    EMBED_MODEL,
    SOLAPAMIENTO,
    TAMANO_FRAGMENTO,
)

TAMANO_LOTE = 32  # cuántos fragmentos se mandan juntos a Ollama


def dividir_en_fragmentos(texto, tamano=TAMANO_FRAGMENTO, solapamiento=SOLAPAMIENTO):
    """Corta el texto en pedazos de ~`tamano` caracteres, sin partir palabras."""
    texto = " ".join(texto.split())  # limpia saltos de línea y espacios dobles
    fragmentos = []
    inicio = 0

    while inicio < len(texto):
        fin = min(inicio + tamano, len(texto))

        # Si no es el final, retrocede hasta el último espacio para no cortar una palabra
        if fin < len(texto):
            corte = texto.rfind(" ", inicio, fin)
            if corte > inicio + tamano // 2:
                fin = corte

        fragmentos.append(texto[inicio:fin].strip())

        if fin >= len(texto):
            break
        inicio = fin - solapamiento

    return [f for f in fragmentos if f]


def leer_pdf(ruta):
    """Devuelve una lista de (numero_de_pagina, texto) del PDF."""
    lector = PdfReader(ruta)
    paginas = []
    for numero, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        if texto.strip():
            paginas.append((numero, texto))
    return paginas


def generar_embeddings(textos):
    """Convierte una lista de textos en vectores, por lotes."""
    vectores = []
    for i in range(0, len(textos), TAMANO_LOTE):
        lote = textos[i:i + TAMANO_LOTE]
        respuesta = ollama.embed(model=EMBED_MODEL, input=lote)
        vectores.extend(respuesta.embeddings)
    return vectores


def main():
    DOCS_DIR.mkdir(exist_ok=True)
    pdfs = sorted(DOCS_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No hay PDFs en {DOCS_DIR}. Copiá alguno ahí y volvé a ejecutar.")
        return

    cliente = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Borra la colección anterior para no duplicar fragmentos al volver a cargar
    try:
        cliente.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # no existía todavía

    coleccion = cliente.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total = 0
    for pdf in pdfs:
        print(f"\nLeyendo {pdf.name}...")
        paginas = leer_pdf(pdf)

        if not paginas:
            print("  ⚠ No se pudo extraer texto. ¿Es un PDF escaneado (imágenes)?")
            continue

        ids, textos, metadatos = [], [], []
        for numero_pagina, texto in paginas:
            for i, fragmento in enumerate(dividir_en_fragmentos(texto)):
                ids.append(f"{pdf.stem}-p{numero_pagina}-c{i}")
                textos.append(fragmento)
                metadatos.append({"archivo": pdf.name, "pagina": numero_pagina})

        print(f"  {len(paginas)} páginas → {len(textos)} fragmentos. Generando embeddings...")
        vectores = generar_embeddings(textos)

        coleccion.add(ids=ids, documents=textos, embeddings=vectores, metadatas=metadatos)
        total += len(textos)
        print("  ✔ Guardado")

    print(f"\nListo: {total} fragmentos en la base '{COLLECTION_NAME}' ({CHROMA_DIR}).")


if __name__ == "__main__":
    main()