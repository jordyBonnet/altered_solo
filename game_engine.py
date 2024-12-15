from statemachine import State
from statemachine import StateMachine
from fastapi.encoders import jsonable_encoder
from player import Player
import random
import json
import os
import shortuuid
import time

class Altered_game_engine(StateMachine):
    """ State machine Altered game engine """

    ### GAME STATES
    waiting_for_players = State(initial=True)   # we are waiting for players
    initialized = State()   # game is initialized
    morning = State()
    noon = State()
    afternoon = State(final=True)

    ### GAME TRANSITIONS
    start = initialized.from_(waiting_for_players, cond='two_or_4_Players') | waiting_for_players.from_(waiting_for_players, unless='cond_two_or_4_Players')
    to_noon = initialized.to(noon, cond='all_players_3_mana')
    to_afternoon = noon.to(afternoon, cond='all_noon_effets_done')

    def __init__(self):
        self.GAMES_FOLDER  = r'C:\Users\jbonnet\Documents\python\projects\_small_ones\_allin\TCG_Altered_sm\games'
        
        self.id: str
        self.players = []
        self.n_players = 0
        self.first_player = None
        # self.state = None                   # not needed as we are using statemachine
        self.day = None
        self.day_phase = None                 # Morning, Noon, Afternoon, Dusk, Night
        self.winner = None
        self.days_history = None
        
        super().__init__()

    def create_a_new_game(self, player):
        self.id = shortuuid.uuid() + '_' + time.strftime("%Y%m%dT%H%M%S", time.localtime())
        player.game_id = self.id    # update game id info for player
        player.id = 1               # update player id
        self.players = [player]
        self.n_players = 1
        self.save_game()
        return self.players[player.id-1]    # we retrun the whole player object every time

    def join_a_game(self, player):
        self.n_players += 1
        player.id = self.n_players
        self.players.append(player)
        self.save_game()
        return self.players[player.id-1]

    def get_available_actions(self, player):
        """ returns a message and a list of all available actions for the player """
        
        if self.current_state.value == 'initialized':
            # check if all players have 3 mana
            if not self.all_players_3_mana():
                actions_list = self.gather_available_actions(self.players[player.id-1])
                self.players[player.id-1].available_actions = actions_list[:-1] # remove pass action here
                self.players[player.id-1].message = "Discard 3 cards to mana and/or wait for other players to do so"
            else: # if so go to Day1 Noon
                self.to_noon()
        
        if self.current_state.value == 'noon':
            if not self.all_noon_effects_done():
                effect_lst = self.gather_at_noon_effects(self.players[player.id-1])
                self.players[player.id-1].effects_available = effect_lst
                self.players[player.id-1].message = "Play noon effect(s) or pass and/or wait for other players to do so"
        
        return self.players[player.id-1]

    # region state machine actions in states #############################################
    def on_enter_initialized(self):
        # 0. define first player
        self.first_player = random.randint(0, self.n_players - 1)
        # self.first_player = self.players[random.randint(0, self.n_players - 1)]
        
        # 1. shuffle deck
        for player in self.players:
            random.shuffle(player.deck)

        # 2. give 6 cards to each player
        for player in self.players:
            player.hand[:] = player.deck[:6]
            del player.deck[:6]

    def on_enter_noon(self):
        # from 1st player to others check if "at noon" effect has to be applied
        for i in range(self.n_players):
            effect_lst = self.gather_at_noon_effects(self.players[((self.first_player-1) + i) % self.n_players])
            self.players[((self.first_player-1) + i) % self.n_players].effects_available = effect_lst
            
    # endregion state machine actions in states

    # region state machine conditions #####################################################
    def two_or_4_Players(self):
        if self.n_players==2 or self.n_players==4:
            return True
        else:
            return False

    def all_players_3_mana(self):
        # check if all players have discarded 3 cards to mana
        if all(len(p.mana_pile) == 3 for p in self.players):
            # if any(len(p.mana_pile) > 3 for p in self.players): # if any player has more than 3 mana
            #     message = "Error: At least one player has more than 3 mana"
            return True
        else:
            return False

    def all_noon_effects_done(self):
        pass

    # endregion state machine conditions

    # region nested functions   ############################################################
    def to_dict(self):
        # Convert all class variables to a dictionary
        game_dict_copy = self.__dict__.copy()
        game_dict_copy['players'] = [jsonable_encoder(player) for player in self.players]
        keys_to_remove = [
            'model', 'state_field', 'start_value', 'allow_event_without_transition',
            '_external_queue', '_callbacks_registry', '_states_for_instance',
            '_listeners', '_engine'
        ]
        for key in keys_to_remove:
            if key in game_dict_copy:
                del game_dict_copy[key]
        return game_dict_copy

    def save_game(self):
        # Convert the dictionary to a JSON string and save it to a file
        json_path = os.path.join(self.GAMES_FOLDER, f"{self.id}.json")
        with open(json_path, 'w') as json_file:
            json.dump(self.to_dict(), json_file, indent=4)
    
    def gather_available_actions(self, player):
        # mainly gather all cards in the player's hand and reserve
        actions_lst = [card for card in player.hand]
        for card in player.reserve:
            actions_lst.append(card)
        # TODO: also add Exhaust abilities (quick action of Heroes or landmarks "{t}")
        # TODO: also add cases where player has to select cards for removal spells for example
        actions_lst.append("pass")
        return actions_lst

    def gather_at_noon_effects(self, player):
        return None

    # endregion nested functions


    # to be removed ?
    def load_json_game(self, game_id):
        json_path = os.path.join(self.GAMES_FOLDER, f"{game_id}.json")
        if not os.path.exists(json_path):
            print(f'⚠️ Game not found (load_json_game) - json_path: {json_path}')
            return {"Success": False, "message": "Game not found"}
        
        # wait until json game file is accessible (writable)
        while not os.access(json_path, os.W_OK):
            time.sleep(0.1)

        with open(json_path, 'r') as json_file:
            game_dict = json.load(json_file)
            # return the json as a pydantic model
        return Game(**game_dict)