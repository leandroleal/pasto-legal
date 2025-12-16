import os
import sys
# Ensure the parent directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.app.fastapi.app import FastAPIApp
from fastapi.routing import APIRoute
from teams.multi_language_team import multi_language_team
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from typing import Annotated
from fastapi import Body
import json
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi import WebSocket, WebSocketDisconnect
import requests
load_dotenv()


def download_categories():
    cache_dir = "src/tmp"
    cache_file_path = os.path.join(cache_dir, "categories.json")
    if not os.path.exists(cache_file_path):
        try:
            os.makedirs(cache_dir, exist_ok=True)
            url = "https://plataforma.mapbiomas.org/api/v1/brazil/territories/categories"
            response = requests.get(url)
            response.raise_for_status()
            original_data = response.json()
            filtered_categories = []
            for category in original_data["categories"]:
                filtered_data={
                    "id": category['id'],
                    "name": category['name'],
                }
                filtered_categories.append(filtered_data)
            filtered_categories = {"categories":filtered_categories}
            
            with open(cache_file_path, "w", encoding="utf-8") as json_file:
                json.dump(filtered_categories, json_file, ensure_ascii=False, indent=2)            
        except requests.exceptions.RequestException as e:
            print(f"ERRO: Falha ao baixar o cache de categorias: {e}")

def download_legends():
    cache_dir = "src/tmp"
    cache_file_path = os.path.join(cache_dir, "legends.json")
    if not os.path.exists(cache_file_path):
        try:
            os.makedirs(cache_dir, exist_ok=True)
            url = "https://plataforma.mapbiomas.org/api/v1/brazil/themes?expand=true"
            response = requests.get(url)
            response.raise_for_status()
            original_data = response.json()
            filtered_themes = []
            for theme in original_data.get("themes", []):
                filtered_subthemes_list = []
                for subtheme in theme.get("subthemes", []):
                    filtered_legends_list = []
                    for legend in subtheme.get("legends", []):
                        filtered_items_list = []
                        for item in legend.get("items", []):
                            filtered_items_list.append({
                                "pixelValue":item.get("pixelValue"),
                                "name": item.get("name"),
                                "level": item.get("level"),
                            })
                        filtered_legends_list.append({
                            "key": legend.get("key"),
                            # "name":legend.get("name"),
                            "items": filtered_items_list
                        })
                    filtered_subthemes_list.append({
                        "key": subtheme.get("key"),
                        # "name": subtheme.get("name"),
                        "legends": filtered_legends_list
                    })
                filtered_themes.append({
                    "key": theme.get("key"),
                    # "name":theme.get("name"),
                    "subthemes": filtered_subthemes_list
                })

            filtered_themes = {"themes":filtered_themes}
            
            with open(cache_file_path, "w", encoding="utf-8") as json_file:
                json.dump(filtered_themes, json_file, ensure_ascii=False, indent=2)            
        except requests.exceptions.RequestException as e:
            print(f"ERRO: Falha ao baixar o cache de legendas: {e}")



fastapi_app = FastAPIApp(
    teams=[multi_language_team],
    name="Flora 0.2",
    app_id="flora",
    description="FLORA é um agente para responder a perguntas sobre o projeto MapBiomas",
)

app = fastapi_app.get_app(use_async=True, prefix="/flora") #https://fastapi.tiangolo.com/advanced/events/#lifespan


@app.websocket("/flora/runs/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # try:
    # while True:
    data = await websocket.receive_json()
    user_message, session_id = data.get("message"),data.get("session_id")
    if user_message and session_id:
        run_stream = multi_language_team.run(
            message=user_message,
            session_id=session_id,
            stream=True
        )
        buffer = ''
        for response_chunk in run_stream:
            if response_chunk.event=='TeamRunResponseContent' and response_chunk.content:
                content = response_chunk.content
                buffer += content
                # print(content)
                # print(buffer)
                if len(buffer) > 30 or content.endswith(('.', '?', '!', '\n')):
                    print(f'\n\n\n\n Tentando enviar {buffer}')
                    await  websocket.send_json({"content": buffer})
                    buffer = ""

                # await asyncio.sleep(0.01)
        if buffer:
            await  websocket.send_json({"content": buffer})
            
        await websocket.send_text("[[END]]")
        await websocket.close()
    # except WebSocketDisconnect:
    #     print(f"Cliente {session_id} desconectado.")
    # except Exception as e:
    #     print(f"Ocorreu um erro na conexão WebSocket: {e}")
    #     await websocket.send_json({"error": str(e)})
    # # finally:
    #     await websocket.close()


@app.post("/flora/runs/stream") # Server-Sent Events (SSE)
async def handle_run_stream(
    message: Annotated[str, Body(embed=True)],
    session_id: Annotated[str, Body(embed=True)]
):
    async def stream_generator():
        run_stream = multi_language_team.run(
            message=message,
            session_id=session_id,
            stream=True
        )
        for response_chunk in run_stream:
            if response_chunk.event == "on_chat_model_stream" and response_chunk.content:
                yield f"data: {json.dumps({'content': response_chunk.content})}\n\n" # formato "data: {...}\n\n" é o padrão SSE
                await asyncio.sleep(0.01)
    return StreamingResponse(stream_generator(), media_type="text/event-stream")





@app.on_event("startup")
async def startup_event():
    download_categories()
    download_legends()
    # print("\n[Rotas disponíveis]")
    # for route in app.routes:
        # if isinstance(route, APIRoute):
            # print(f"{route.path} → {route.methods}")


# reload	bool	False	Enable auto-reload for development.
if __name__ == "__main__":
    fastapi_app.serve(app="app.fastapi_server:app", host="0.0.0.0", port=7778, reload=False,workers=8)
 