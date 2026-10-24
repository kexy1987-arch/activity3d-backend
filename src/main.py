from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from routes import create_player_router, rooms_router, lobby_router, teams_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(create_player_router)
app.include_router(rooms_router)
app.include_router(lobby_router)
app.include_router(teams_router)



























