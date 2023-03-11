import unittest
from app import GameState
import os
import json


class TestApp(unittest.TestCase):

    game_state_obj = None
    file_name_sorted = []
    data_dir = None
    gold_count_before = 0
    gold_count_after = 0

    def setUp(self):
        print("Setting up!")
        os.system('clear')
        self.data_dir = './samples'
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]

        # Sort the file names is important to get the event from game start
        temp_file_names_sorted = sorted(json_files, key=lambda x: x.split(".")[0])

        # for this test requires following
        self.file_name_sorted = [file for file in temp_file_names_sorted if
                                 file == 'player_kill.json' or file == 'dragon_kill.json']

        # game state obj
        self.game_state_obj = GameState()
        self.game_state_obj.game_state = 'MATCH_START'
        self.gold_count_before = 0
        self.gold_count_after = 0
        print(self.game_state_obj.players)

    def tearDown(self):
        print("Tearing down!\n")
        self.game_state_obj.players = {}
        self.game_state_obj.teams = {}
        self.game_state_obj.game_state = None
        self.gold_count_before = 0
        self.gold_count_after = 0

    def test_handle_player_kill(self):
        """
        This will test the player kill event and what game state after that
        :return:
        """
        # as per sort order player_kill will come last on the list of two
        with open(os.path.join(self.data_dir, self.file_name_sorted[1]), 'r') as f:
            contents = f.read()
            try:
                event = json.loads(contents)
            except json.JSONDecodeError as e:
                print("JSON decoding error:", e)
                self.game_state_obj.process_unparsable(contents)
            else:
                self.game_state_obj.parse_event(event)
        self.assertEqual(self.game_state_obj.game_state, 'PLAYER_KILL')

    def test_handle_player_kill_gold(self):
        """
        This will test the gold count before and after the player kill
        :return:
        """
        self.gold_count_after = self.game_state_obj.players["riot:lol:player:b8945185-74af-35f1-8f66-89043bc89e91"]["gold"]
        self.assertEqual(self.gold_count_after, (self.gold_count_before + 600 + 25))

    def test_handle_dragon_kill(self):
        """
        This will test the dragon kill event and what game state after that
        :return:
        """
        # as per sort order player_kill will come last on the list of two
        with open(os.path.join(self.data_dir, self.file_name_sorted[0]), 'r') as f:
            contents = f.read()
            try:
                event = json.loads(contents)
            except json.JSONDecodeError as e:
                print("JSON decoding error:", e)
                self.game_state_obj.process_unparsable(contents)
            else:
                self.game_state_obj.parse_event(event)
        self.assertEqual(self.game_state_obj.game_state, 'DRAGON_KILL')

    def test_handle_dragon_kill_gold(self):
        """
        This will test the gold count before and after the dragon kill
        :return:
        """
        self.gold_count_after = self.game_state_obj.players["riot:lol:player:b8945185-74af-35f1-8f66-89043bc89e91"]["gold"]
        self.assertEqual(self.gold_count_after, (self.gold_count_before + 25))


if __name__ == '__main__':
    # call all tests
    unittest.main()
