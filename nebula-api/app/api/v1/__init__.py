"""Version 1 of the HTTP API.

New domains (battle, party, voice) register their router here so `main.py`
never has to change again.
"""

from fastapi import APIRouter

from app.api.v1 import chat, inventory, quests

api_router = APIRouter()
api_router.include_router(chat.router)
api_router.include_router(inventory.router)
api_router.include_router(quests.router)

__all__ = ["api_router"]
