from fastapi import FastAPI
from datetime import date
from player import Player
from game_engine import Altered_game_engine

gameengines_running = []   # List of running game engines
# a new game engine is appended to this list every time a new game is created

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Altered TCG"}

@app.post("/game/create")
def create_game(player: Player):
    gameengines_running.append(Altered_game_engine())
    player_data = gameengines_running[-1].create_a_new_game(player)
    return {"Success": True, "data": player_data}

@app.post("/game/get_all_running_games")
def get_all_running_games():
    return {"Success": True, "data": [game.id for game in gameengines_running]}

@app.post("/game/join")
def create_game(player: Player):
    game = get_game_engine(player.game_id)  # retrieve the game_engine running for this player game
    player_data = game.join_a_game(player)
    return {"Success": True, "data": player_data}

@app.post("/game/start")
def start_game(player: Player):
    game = get_game_engine(player.game_id)    # retrieve the game_engine running for this player game
    game.start()
    if game.current_state.value == 'initialized':
        return {"Success": True, "message": "game 'initialized', then do a get_available_actions"}
    elif game.current_state.value == 'waiting_for_players':
        return {"Success": False, "message": "waiting for the right number of players (2 or 4)"}

@app.post("/game/play_actions")
def play_actions(player: Player):
    player_data = game_engine.play_actions(player)
    if type(player_data) == dict:   # error
        return player_data
    return {"Success": True, "data": player_data}

@app.get("/game/get_available_actions")
def get_available_actions(player: Player):
    game = get_game_engine(player.game_id)    # retrieve the game_engine running for this player game
    player_data = game.get_available_actions(player)
    if type(player_data) == dict:   # error
        return player_data
    return {"Success": True, "data": player_data}

# region nested functions
def get_game_engine(game_id):
    for game_engine in gameengines_running:
        if game_engine.id == game_id:
            return game_engine
    raise 'Game not found'

# @app.get("/game/actions_available")
# def get_actions_available(game_id: str, player_game_id: int):
#     json_path = os.path.join(GAMES_FOLDER, f"{game_id}.json")
#     if not os.path.exists(json_path):
#         return {"Success": False, "message": "Game not found"}
#     with open(json_path, 'r') as json_file:
#         game_dict = json.load(json_file)
#     player_dict = game_dict[f"player{player_game_id}"]
#     return {"Success": True, "actions": ["draw6cards"]}

# @app.post("/game/{id}/draw6cards")
# def create_game(id):
