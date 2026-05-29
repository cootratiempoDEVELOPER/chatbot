from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from handlers import handlers
from fastapi.responses import JSONResponse, PlainTextResponse
from supabase_client import supabase  # ✅ ya contiene el client creado
from messages import welcome_message
from datetime import datetime, timezone, timedelta

load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("TOKEN_PER")
WHATSAPP_PHONE = os.getenv("PHONE_PER")

app = FastAPI()

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    
    return JSONResponse(content={"error": "Verification failed"}, status_code=403)

@app.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        value = data["entry"][0]["changes"][0]["value"]

        # ✅ Verifica si contiene mensajes (puede ser un evento de estado u otro)
        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]
        phone_number = message["from"]
        message_type = message.get("type")
        
        if message_type == "text":
            text = message["text"]["body"].strip().lower()

        elif message_type == "interactive":

            interactive = message["interactive"]

            if interactive["type"] == "button_reply":
                text = interactive["button_reply"]["id"]

            elif interactive["type"] == "list_reply":
                text = interactive["list_reply"]["id"]

        res = supabase.table("session").select("*").eq("phone", phone_number).execute()
        now = datetime.now(timezone.utc)
        
        if not res.data:
            # Crear nueva sesión
            session = supabase.table("session").insert({
                "phone": phone_number,
                "option": 0,
                "init": True,
                "updated_at": now.isoformat()
            }).execute()
            sendMessage(welcome_message, phone_number)
        else:
            now = datetime.now(timezone.utc)
            session = res.data[0]
            
            updated_at_str = session.get("updated_at")

            try:
                # Convertir y asegurar que updated_at tenga zona horaria UTC
                updated_at = datetime.fromisoformat(updated_at_str)
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
            except Exception:
                # Si hay error, forzamos expiración
                updated_at = now - timedelta(minutes=20)

            # Ahora sí puedes comparar
            if now - updated_at > timedelta(minutes=15):
                # Sesión expirada
                supabase.table("session").delete().eq("phone", phone_number).execute()
                sendMessage("Tu tiempo de respuesta superó nuestro tiempo de espera. Por favor, inicia una nueva conversación para continuar con la atención.", phone_number)
                return {"status": "session ended"}
            else:
                # Sesión válida, actualizar timestamp
                supabase.table("session").update({
                    "init": True,
                    "updated_at": now.isoformat()
                }).eq("phone", phone_number).execute()
                        
        # Si el usuario escribe "salir"
        if text == "salir":
            sendMessage("Gracias por contactarnos. ¡Hasta luego!", phone_number)
            supabase.table("session").delete().eq("phone", phone_number).execute()
            return {"status": "session ended"}

        # Si el usuario escribe "menu"
        if text == "menu":
            sendMessage(welcome_message, phone_number)
            supabase.table("session").update({"option": 0, "step": 1}).eq("phone", phone_number).execute()
            return {"status": "menu displayed"}
        
        if text == "asesor":
            sendMessage("Para comunicarte directamente con un asesor escribenos a este numero: https://wa.me/573144756457", phone_number)
            supabase.table("session").update({"option": 4, "step": 0}).eq("phone", phone_number).execute()
            return {"status": "menu displayed"}

        # Obtener y procesar handler
        option = session.get("option", 0)
        handler = handlers.get(option)

        if handler:
            result = handler(text, session, phone_number, sendMessage)

            if result == "end":
                supabase.table("session").delete().eq("phone", phone_number).execute()
            elif isinstance(result, dict):
                supabase.table("session").update(result).eq("phone", phone_number).execute()


    except Exception as e:
        print(f"Error: {e}")

    return {"status": "received"}

def sendMessage(text, phone_number):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)


def sendButtons(text, phone_number):
    buttons = [
        {
            "type": "reply",
            "reply": {
                "id": "accept_yes",
                "title": "Sí"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "accept_no",
                "title": "No"
            }
        }
    ]

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": text
            },
            "action": {
                "buttons": buttons
            }
        }
    }

    requests.post(url, headers=headers, json=payload)
