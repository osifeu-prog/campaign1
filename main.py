
from fastapi import FastAPI, Request
from bot import tg_app
from telegram import Update
import os

app = FastAPI()

@app.on_event("startup")
async def startup():
    await tg_app.initialize()

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
