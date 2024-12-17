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
    """ State machine Altered game engine 
        Game rules:

        Phase 1 - Morning:
            change the owner of the first player marker
            ready your mana orbs and exhausted cards
            draw 2 cards from your deck
            starting with the first player, each player choose if they want to place a card from their hand to their mana zone

        Phase 2 - Noon:
            activate any card with an "at noon" trigger

        Phase 3 - Afternoon:
            starting with the first player, players take turns in this phase, during which they each play one card at a time
            (1 turn = 1 card)
            Turn structure:
                1. take as many Quick actions as you want
                2. play a card or pass

        Phase 4 - Dusk:
            compare statistics of all biomes if at least one stat is higher than the opponent, the player advance in expedition

        Phase 5 - Night:
            Rest: send all characters in your expeditions to your reserve, if they have "fleeting", discard them instead
            cleanup: if you have 3 or more cards in your Reserve, you must discard down to 2. do the same for your landmarks 
    """

    ### GAME STATES
    waiting_for_players = State(initial=True)   # we are waiting for players
    initialized = State()   # game is initialized
    morning = State()
    noon = State()
    afternoon = State()
    dusk = State()
    night = State()
    # end_game = State(final=True)

    ### GAME TRANSITIONS
    start = initialized.from_(waiting_for_players, cond='two_or_4_Players') | waiting_for_players.from_(waiting_for_players, unless='two_or_4_Players')
    to_noon = initialized.to(noon, cond='all_players_3_mana') | initialized.from_(initialized, unless='all_players_3_mana')| morning.to(noon)
    to_afternoon = noon.to(afternoon, cond='all_noon_effects_done')
    to_dusk = afternoon.to(dusk)
    to_night = dusk.to(night)
    to_morning = night.to(morning)

    def __init__(self):
        self.GAMES_FOLDER  = r'games'
        
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

    def get_player(self, player):
        """ returns player object """
        return self.players[player.id-1]

    def play_actions(self, player):
        # [{'action': 'move_card', 'card': 'c81', 'from': 'hand', 'to': 'mana_pile'},
        # {'action': 'move_card', 'card': 'c72', 'from': 'hand', 'to': 'mana_pile'},
        # {'action': 'move_card', 'card': 'c21', 'from': 'hand', 'to': 'mana_pile'}]
        
        for action in player.actions:
            # 1. play the card
            if action['action'] == 'move_card':
                # 1. remove card from source
                source = getattr(player, action['from'])
                # check if card really is in source
                if action['card'] not in source:
                    player.message = f"Error: Card {action['card']} not in {action['from']}"
                source.remove(action["card"])
                setattr(player, action['from'], source)     # update player object

                # 2. add card to destination
                destination = getattr(player, action['to'])
                destination.append(action['card'])
                setattr(player, action['to'], destination)  # update player object
        
        self.players[player.id-1] = player
        self.save_game()
        return self.players[player.id-1]

    # region state machine actions in states #############################################
    def on_exit_waiting_for_players(self):
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

        # 3. set message for each player
        for player in self.players:
            player.message = "Discard 3 cards to mana and/or wait for other players to do so"
        
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
            '_listeners', '_engine', '_callbacks'
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