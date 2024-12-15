import requests
import random
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Optional

class Player(BaseModel):
    """ Pydantic Model for FASTAPI
     &
        requests functions wrapper """
    
    name: str = Field(max_length=12)
    deck: list
    game_id: Optional[str] = None
    id: Optional[int] = None
    hand: Optional[list] = []
    reserve: Optional[list] = []
    landmarks: Optional[list] = []
    exp_hero: Optional[list] = []
    exp_companion: Optional[list] = []
    mana_pile: Optional[list] = []
    discard_pile: Optional[list] = []
    has_passed_afternoon: Optional[bool] = False
    turn_not_ended: Optional[bool] = False
    effects_available: Optional[list] = None
    pending_effects: Optional[list] = None
    actions: Optional[list] = None                  # list of dict of actions
    message: Optional[str] = None                   # message for the player
    available_actions: Optional[list] = None        # list available cards to play
    server : str = "http://127.0.0.1:8000"
    is_AI : bool = False
    AI_level : str = 'random'    # 'random' or 'smart'

    # region API functions
    def create_new_game(self):
        response = requests.post(f"{self.server}/game/create", json=jsonable_encoder(self))
        if response.status_code == 200:
            rep_player_data = response.json()['data']   # {'success': True, 'data': player_data}
            return Player(**rep_player_data)
        else:
            raise Exception("Failed to create a new game")
    
    def get_all_running_games(self):
        response = requests.post(f"{self.server}/game/get_all_running_games")
        if response.status_code == 200:
            return response.json()['data']
        else:
            raise Exception("Failed to get all running games")

    def join_game(self):
        response = requests.post(f"{self.server}/game/join", json=jsonable_encoder(self))
        if response.status_code == 200:
            rep_player_data = response.json()['data']   # {'success': True, 'data': player_data}
            return Player(**rep_player_data)
        else:
            raise Exception("Failed to join the game")
    
    def start_game(self):
        response = requests.post(f"{self.server}/game/start", json=jsonable_encoder(self))
        # {"Success": True, "message": "game 'initialized', then do a get_available_actions"}
        # or {"Success": False, "message": "waiting for the right number of players (2 or 4)"}
        if response.status_code == 200:
            message = response.json()['message']
            return message
        else:
            raise Exception("Failed to start the game")
    
    def play_actions(self):
        response = requests.post(f"{self.server}/game/play_actions", json=jsonable_encoder(self))
        if response.status_code == 200:
            rep_player_data = response.json()['data']   # {'success': True, 'data': player_data}
            return Player(**rep_player_data)
        else:
            raise Exception("Failed to play actions")
    
    def get_available_actions(self):
        response = requests.get(f"{self.server}/game/get_available_actions", json=jsonable_encoder(self))
        if response.status_code == 200:
            rep_player_data = response.json()['data']   # {'success': True, 'data': player_data}
            return Player(**rep_player_data)
        else:
            raise Exception("Failed get playable actions")

    # endregion API functions

    # region AI functions
    def AI_discard_3_to_mana(self):
        # Returns a list of actions
        actions_lst = []

        if self.AI_level == 'random':
            selected_cards = random.sample(self.hand, 3)
        
        for card in selected_cards:
            actions_lst.append({
                "action": "move_card",
                "card": card,
                "from": "hand",
                "to": "mana_pile"
            })
        
        # add actions to the player object
        self.actions = actions_lst

        return actions_lst


    # endregion

    