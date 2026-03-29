from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/voices")
def api_voices(request: Request):
    vm = request.app.state.voice_manager
    return {"voices": vm.list_voices()}
