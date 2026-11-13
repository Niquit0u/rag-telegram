import ollama

LLM = "qwen3.5:4b"
EMBED = "qwen3-embedding:0.6b"

# 1) Probar el modelo que responde
respuesta = ollama.chat(
    model=LLM,
    messages=[{"role": "user", "content": "Decime hola en una sola oración."}],
)
print("LLM:", respuesta.message.content)

# 2) Probar el modelo de embeddings
emb = ollama.embed(model=EMBED, input="Hola, esto es una prueba")
print("Embedding: vector de", len(emb.embeddings[0]), "números")