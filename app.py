import json
import os
import re


class GameState:
    # Game state variables
    game_state = None
    players = {}
    teams = {}
    match_started = False

    def check_and_create_player(self, killer_id):
        """
        This method will create a new player if it doesn't exist
        :param killer_id:
        :return: boolean
        """
        if killer_id not in self.players:
            self.players[killer_id] = {
                "playerID": killer_id,
                "alive": True,
                "name": None,
                "gold": 0,
                "minionsKilled": 0,
                "kills": 0,
                "deaths": 0,
                "teamID": None,
                "assists": 0
            }
            return True
        return False

    # Event handlers
    def handle_match_start(self, payload):
        """
        This method will be called at game start only once.
        It will set all state, players, teams and match_started to true
        :param payload: dictionary
        :return: void
        """
        self.game_state = 'MATCH_START'
        self.teams = {team["teamID"]: team for team in payload["teams"]}
        self.players = {player["playerID"]: player for team in payload["teams"] for player in team["players"]}

        for team in payload["teams"]:
            for player in team['players']:
                self.players[player['playerID']]['teamID'] = team['teamID']
        self.match_started = True

    def handle_minion_kill(self, payload):
        """
        This method will be called when a minion killed.
        A player killed a minion. The player is granted some gold and their minion count is updated.
        :param payload:
        :return:
        """
        self.game_state = 'MINION_KILL'
        player_id = payload["playerID"]

        if player_id != 'null' and player_id is not None:
            self.check_and_create_player(player_id)

            if "gold" in self.players[player_id]:
                self.players[player_id]["gold"] += int(payload["goldGranted"])
            else:
                self.players[player_id]["gold"] = int(payload["goldGranted"])

            if "minionsKilled" in self.players[player_id]:
                self.players[player_id]["minionsKilled"] += 1
            else:
                self.players[player_id]["minionsKilled"] = 1

    def handle_player_kill(self, payload):
        """
        This method will be called when a player killed.
        One player killed another, optionally assisted by other members of the team.
        The killer is granted some gold, and each of the assistants receive a reduced amount.
        Kills, deaths and assists stats should be updated for all the players involved.
        :param payload:
        :return:
        """
        self.game_state = 'PLAYER_KILL'
        killer_id = payload.get("killerID", None)
        assistants = payload.get("assistants", [])
        killer_assist_gold = int(payload.get("assistGold", 0))
        killer_gold = int(payload["goldGranted"])

        if killer_id != 'null' and killer_id is not None:
            # check and create player if not exist
            self.check_and_create_player(killer_id)

            if "gold" in self.players[killer_id]:
                self.players[killer_id]["gold"] += killer_gold
            else:
                self.players[killer_id]["gold"] = killer_gold
            if "kills" in self.players[killer_id]:
                self.players[killer_id]["kills"] += 1
            else:
                self.players[killer_id]["kills"] = 1
            # players[killer_id]["killStreak"] += 1
            if "deaths" in self.players[killer_id]:
                self.players[killer_id]["deaths"] += 1
            else:
                self.players[killer_id]["deaths"] = 1

        for assistant_id in assistants:
            # if the amount get distributed among all assistants
            # assistant_gold = killer_assist_gold / len(assistants)
            # here each assistant get the specified same amount
            assistant_gold = killer_assist_gold
            self.check_and_create_player(assistant_id)

            # killer won't get again as assist
            if assistant_id != killer_id:
                if "gold" in self.players[assistant_id]:
                    self.players[assistant_id]["gold"] += assistant_gold
                else:
                    self.players[assistant_id]["gold"] = assistant_gold

                if "assists" in self.players[assistant_id]:
                    self.players[assistant_id]["assists"] += 1
                else:
                    self.players[assistant_id]["assists"] = 1

                if "deaths" in self.players[assistant_id]:
                    self.players[assistant_id]["deaths"] += 1
                else:
                    self.players[assistant_id]["deaths"] = 1

    def handle_dragon_kill(self, payload):
        """
        This method will be called when dragon get killed.
        One player killed a dragon. The team's dragon kill count should be updated,
        and the player is granted some gold.
        :param payload:
        :return:
        """
        self.game_state = 'DRAGON_KILL'
        player_id = payload.get("killerID", None)
        team_id = payload.get("killerTeamID", None)

        if player_id != 'null' and player_id is not None:
            self.check_and_create_player(player_id)

            if "gold" in self.players[player_id]:
                self.players[player_id]["gold"] += int(payload["goldGranted"])
            else:
                self.players[player_id]["gold"] = int(payload["goldGranted"])
            if team_id is None:
                team_id = self.players[player_id]['teamID']

        if team_id is not None and team_id != 'null':
            if "dragonKills" in self.teams[team_id]:
                self.teams[team_id]["dragonKills"] += 1
            else:
                self.teams[team_id]["dragonKills"] = 1

    def handle_turret_destroy(self, payload):
        """
        This method will be called when one turret destroyed.
        A team destroyed an enemy turret. The team's tower kill count should be updated,
        and each of its players receives some gold.
        Additionally, the player who took the tower receives playerGoldGranted gold.
        Keep in mind that sometimes towers are destroyed by minions,
        so no individual player receives playerGold, although team gold is still granted.
        :param payload:
        :return:
        """
        self.game_state = 'TURRET_DESTROY'
        player_id = payload.get("killerID", None)
        team_id = payload.get("killerTeamID", None)
        player_gold_granted = int(payload.get("playerGoldGranted", 0))
        team_gold_granted = int(payload.get("teamGoldGranted", 0))

        if team_id != 'null' and team_id is not None:
            if "towerKills" in self.teams[team_id]:
                self.teams[team_id]["towerKills"] += 1
            else:
                self.teams[team_id]["towerKills"] = 1

            for player in self.teams[team_id]["players"]:
                # who destroyed the tower won't get the gold
                # again from team's grant
                if player['playerID'] != player_id:
                    if "gold" in player:
                        player["gold"] += team_gold_granted
                    else:
                        player["gold"] = team_gold_granted

        # if minions not destroyed tower
        if player_id != 'null' and player_id is not None:
            if "gold" in self.players[player_id]:
                self.players[player_id]["gold"] += player_gold_granted
            else:
                self.players[player_id]["gold"] = player_gold_granted

    def get_winner(self):
        """
        This method will find the winner details
        :return:
        """
        print("\n\nWinner Details:\n")
        highest_gold_player = {}
        highest_minion_killer = {}
        highest_player_killer = {}
        highest_player_killer_assists = {}
        highest_player_killer_deaths = {}

        highest_golds = 0
        highest_minion_kills = 0
        highest_player_kills = 0
        highest_player_assists = 0
        highest_player_deaths = 0

        for player_id in self.players:
            player = self.players[player_id]
            if "gold" in player and int(player['gold']) > highest_golds:
                highest_golds = int(player['gold'])
                highest_gold_player = player_id

            if "minionsKilled" in player and int(player['minionsKilled']) > highest_minion_kills:
                highest_minion_kills = int(player['minionsKilled'])
                highest_minion_killer = player_id

            if "kills" in player and int(player['kills']) > highest_player_kills:
                highest_player_kills = int(player['kills'])
                highest_player_killer = player_id

            if "assists" in player and int(player['assists']) > highest_player_assists:
                highest_player_assists = int(player['assists'])
                highest_player_killer_assists = player_id

            if "deaths" in player and int(player['deaths']) > highest_player_deaths:
                highest_player_deaths = int(player['deaths'])
                highest_player_killer_deaths = player_id

        return [
            {
                "Highest golds": highest_golds,
                'Highest gold player': highest_gold_player
            },
            {
                "Highest minion kills": highest_minion_kills,
                "Highest minion killer": highest_minion_killer
            },
            {
                "Highest player kills": highest_player_kills,
                "Highest player killer": highest_player_killer
            },
            {
                "Highest_player_assists": highest_player_assists,
                "Highest_player_killer_assists": highest_player_killer_assists
            },
            {
                "Highest player deaths": highest_player_deaths,
                "Highest player killer deaths": highest_player_killer_deaths
            }
                ]

    def handle_match_end(self, payload):
        """
        This method will be called when match end. This is last event of the game state.
        The match ended, and a winner is declared. There are never any events after this one.
        :param payload:
        :return:
        """
        self.game_state = 'MATCH_END'
        self.match_started = False

    def process_unparsable(self, contents):
        """
        This method will handle which is unparsable event and update the game_state.
        The regular expression '"type":\s*"([^"]+)"' looks for the string "type":
        followed by any amount of whitespace (\s*), then matches the "type" value
        which is enclosed in double quotes (") and captures it in a group (([^"]+)).
        :param contents:
        :return:
        """
        match = re.search(r'"type":\s*"([^"]+)"', contents)
        if match:
            self.game_state = match.group(1)
            print("No worries! Partial data recovered and updated the game state :)")

    def get_game_state(self):
        """
        This will return the latest game state
        :return:
        """
        return self.game_state

    # Event parser
    def parse_event(self, event):
        try:
            event_type = event["type"]
            payload = event["payload"]

            if event_type == "MATCH_START":
                self.handle_match_start(payload)
            elif event_type == "MINION_KILL":
                self.handle_minion_kill(payload)
            elif event_type == "PLAYER_KILL":
                self.handle_player_kill(payload)
            elif event_type == "DRAGON_KILL":
                self.handle_dragon_kill(payload)
            elif event_type == "TURRET_DESTROY":
                self.handle_turret_destroy(payload)
            elif event_type == "MATCH_END":
                self.handle_match_end(payload)
        except (KeyError, TypeError):
            # Skip parse or incomplete events
            print(f"error occurred at {event_type}")
            # print(event["payload"])


# Main program
if __name__ == "__main__":
    # Load events from file
    # with open("data/events.json", "r") as f:
    #     events = json.load(f)
    os.system('clear')
    data_dir = './data'
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]

    # Sort the file names is important to get the event from game start
    file_names_sorted = sorted(json_files, key=lambda x: int(x.split(".")[0]))

    game_state_obj = GameState()

    # Parse each event and update game state
    for filename in file_names_sorted:
        with open(os.path.join(data_dir, filename), 'r') as f:
            contents = f.read()
            try:
                event = json.loads(contents)
            except json.JSONDecodeError as e:
                print("JSON decoding error:", e)
                game_state_obj.process_unparsable(contents)
            else:
                # print(event['type'])
                print(f"Event File: {filename}")
                game_state_obj.parse_event(event)
                print(f"Game State: {game_state_obj.get_game_state()}")

    # Print final game state
    print("=" * 100)
    print(f"Last Game State: {game_state_obj.get_game_state()}")
    print("Players: ")
    print(game_state_obj.players)
    print("Teams: ")
    print(game_state_obj.teams)

    # declare the winner
    print(json.dumps(game_state_obj.get_winner(), indent=2))
