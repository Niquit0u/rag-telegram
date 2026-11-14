"""
Bot de Telegram que responde preguntas sobre tus PDFs usando el RAG de rag.py.

Antes de ejecutarlo:
  - Ollama tiene que estar corriendo.
  - Tenés que haber ejecutado ingest.py al menos una vez.
  - El archivo .env tiene que tener TELEGRAM_TOKEN=...

El bot funciona mientras este script esté ejecutándose (Ctrl+C o el botón Stop para cortarlo).
"""
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BASE_DIR
from rag import obtener_coleccion, responder

load_dotenv(BASE_DIR / ".env")
TOKEN = os.getenv("TELEGRAM_TOKEN")

LIMITE_MENSAJE = 4000  # Telegram no acepta mensajes de más de 4096 caracteres

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # oculta logs repetitivos
log = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    await update.message.reply_text(
        f"¡Hola {nombre}! 👋\n\n"
        "Soy un bot que responde preguntas sobre los documentos que tengo cargados.\n"
        "Escribime tu pregunta y te contesto, indicando de qué archivo y página saqué la información.\n\n"
        "Usá /ayuda si necesitás más info."
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Cómo usarme:\n"
        "• Escribime una pregunta normal, por ejemplo: ¿Qué es un sistema operativo?\n"
        "• Respondo solo con lo que está en los documentos. Si no está, te aviso.\n"
        "• Puedo tardar unos segundos, porque la IA corre en una PC local."
    )


async def mostrar_escribiendo(chat, parar: asyncio.Event):
    """Muestra 'escribiendo...' en Telegram hasta que la respuesta esté lista."""
    while not parar.is_set():
        try:
            await chat.send_action(ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(parar.wait(), timeout=4)
        except asyncio.TimeoutError:
            pass


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text.strip()
    usuario = update.effective_user.first_name
    log.info("Pregunta de %s: %s", usuario, pregunta)

    parar = asyncio.Event()
    tarea_escribiendo = asyncio.create_task(mostrar_escribiendo(update.effective_chat, parar))

    try:
        # responder() tarda (usa Ollama), así que corre en otro hilo
        # para que el bot no se congele mientras tanto.
        respuesta, fuentes = await asyncio.to_thread(responder, pregunta)
    except Exception:
        log.exception("Error al generar la respuesta")
        await update.message.reply_text(
            "⚠️ Hubo un error al generar la respuesta. ¿Está corriendo Ollama?"
        )
        return
    finally:
        parar.set()
        await tarea_escribiendo

    texto = f"{respuesta}"

    # Si la respuesta es muy larga, se manda en varias partes
    for i in range(0, len(texto), LIMITE_MENSAJE):
        await update.message.reply_text(texto[i:i + LIMITE_MENSAJE])


def main():
    if not TOKEN:
        print("Falta TELEGRAM_TOKEN en el archivo .env")
        return

    try:
        obtener_coleccion()
    except Exception:
        print("No encontré la base de documentos. Ejecutá primero ingest.py.")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("🤖 Bot funcionando. Escribile en Telegram. (Ctrl+C o Stop para detenerlo)")
    app.run_polling()


if __name__ == "__main__":
    main()