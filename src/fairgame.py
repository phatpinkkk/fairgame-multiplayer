# FAIRGAME\src\fairgame.py

from src.payoff_matrix import PayoffMatrix
from src.game_history import GameHistory
from src.game_round import GameRound
from collections import Counter

class FairGame:
    """
    Top-level game engine that orchestrates multiple rounds, applies payoff matrices,
    and checks for stop conditions.
    
    Supports:
      - Classic 2-agent games (original FAIRGAME behaviour)
      - Team games (e.g., 3 vs 3), where payoffs are applied at team level
        based on aggregated (e.g. majority) team decisions.
    """

    def __init__(self, name, language, agents, n_rounds, n_rounds_known,
                 payoff_matrix_data, prompt_template, stop_conditions,
                 agents_communicate, teams=None):
        """
        Initialize the FairGame with all required parameters.

        Args:
            name (str): The name of the game.
            language (str): The language used by the game and payoff matrix.
            agents (dict): A dictionary mapping agent names to agent objects.
            n_rounds (int): The total number of rounds to play.
            n_rounds_known (str or bool): If the number of rounds is known to agents.
            payoff_matrix_data (dict): The data defining the payoff matrix.
            prompt_template (str): The template used to generate prompts for agents.
            stop_conditions (list): A list of combinations that end the game early if chosen.
            agents_communicate (str or bool): Whether agents communicate before choosing strategies.
            teams (dict or None): Optional mapping from team IDs (e.g. "A", "B") to lists of agent names.
        """
        self.name = name
        self.language = language
        self.agents = agents
        self.n_rounds = int(n_rounds)
        self.n_rounds_known = self._str2bool(n_rounds_known)
        self.prompt_template = prompt_template
        self.stop_conditions = stop_conditions
        self.agents_communicate = self._str2bool(agents_communicate)
        self.current_round = 1
        self.history = GameHistory()
        
        # Stores per-round "effective choices" for stop conditions:
        # - in classic mode: list of strategies for each agent (e.g. ["C", "D"])
        # - in team mode: list of team strategies (e.g. ["C", "D"] for team A, team B)
        self.choices_made = []
        
         # Payoff matrix wrapper
        self.payoff_matrix = PayoffMatrix(payoff_matrix_data, language)
        
        # Team structure (if any). Example:
        #   teams = {"A": ["agent1", "agent2", "agent3"],
        #            "B": ["agent4", "agent5", "agent6"]}
        self.teams = teams
        
        # Fix team order for consistent payoff and stop-condition mapping
        self.team_order = list(teams.keys()) if teams is not None else None
        
        
    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    
    def _str2bool(self, value):
        """
        Convert a string or bool to a boolean value.

        Args:
            value (str or bool): The value to interpret as bool.

        Returns:
            bool: The interpreted boolean value.
        """
        return value if isinstance(value, bool) else value.strip().lower() == "true"

    @property
    def description(self):
        """
        dict: A description of the game settings, including agents, language,
              number of rounds, and payoff matrix data.
        """
        return {
            "name": self.name,
            "language": self.language,
            "agents": {name: agent.get_info() for name, agent in self.agents.items()},
            "teams": self.teams,
            "n_rounds": self.n_rounds,
            "number_of_rounds_is_known": self.n_rounds_known,
            "payoff_matrix": self.payoff_matrix.matrix_data,
            "agents_communicate": self.agents_communicate
        }

    # -------------------------------------------------------------------------
    # Team aggregation & payoff helpers (used only when self.teams is not None)
    # -------------------------------------------------------------------------

    def _majority_vote(self, choices):
        """
        Compute a majority vote over a list of strategy choices.

        Args:
            choices (list[str]): Strategy labels chosen by agents in a team.

        Returns:
            str: The majority strategy. In case of tie, returns one of the most
                 frequent strategies deterministically.
        """
        if not choices:
            return None
        counter = Counter(choices)
        most_common = counter.most_common()
        # If tie, just pick the first in the most_common list (deterministic)
        return most_common[0][0]
    
    
    def _aggregate_team_decisions(self, round_strategies):
        """
        Aggregate per-agent strategies into per-team decisions.

        Args:
            round_strategies (dict[str, str]): Mapping from agent name to strategy.

        Returns:
            dict[str, str]: Mapping from team_id to aggregated strategy.
        """
        team_choices = {}

        for team_id in self.team_order:
            members = self.teams.get(team_id, [])
            member_choices = [round_strategies[name] for name in members if name in round_strategies]
            team_choices[team_id] = self._majority_vote(member_choices)

        return team_choices


    def _find_combination_key(self, strategy_list):
        """
        Given an ordered list of strategies (length = number of players/teams),
        find the corresponding combination key in the payoff matrix.

        Args:
            strategy_list (list[str]): e.g. ["C", "D"]

        Returns:
            str or None: The combination key, or None if not found.
        """
        combos = self.payoff_matrix.matrix_data["combinations"]
        for key, value in combos.items():
            if value == strategy_list:
                return key
        return None


    def _assign_team_scores(self, team_choices):
        """
        Compute team-level payoffs from the payoff matrix and assign scores
        to all agents on each team.

        Args:
            team_choices (dict[str,str]): e.g. {"A": "C", "B": "D"}.
        """
        # Strategies in fixed team order, e.g. ["C", "D"]
        ordered_strategies = [team_choices[tid] for tid in self.team_order]
        comb_key = self._find_combination_key(ordered_strategies)
        if comb_key is None:
            raise ValueError(
                f"No payoff matrix combination matches strategies: {ordered_strategies}"
            )

        # Expected: matrix[comb_key] is a list of payoffs per 'player' (here per team)
        # E.g. [payoff_for_team_A, payoff_for_team_B]
        payoffs = self.payoff_matrix.matrix_data["matrix"][comb_key]

        if len(payoffs) != len(self.team_order):
            raise ValueError(
                f"Payoff matrix returned {len(payoffs)} payoffs for {len(self.team_order)} teams."
            )

        # Map team_id -> team_payoff
        numeric_payoffs = [
            self.payoff_matrix.weights[label] for label in payoffs
        ]

        team_payoff_map = {
            team_id: numeric_payoffs[i] for i, team_id in enumerate(self.team_order)
        }


        # Assign the team payoff to each member of that team
        for agent_name, agent in self.agents.items():
            team_id = getattr(agent, "team_id", None)
            if team_id is None:
                # If an agent has no team_id, this is a config error in team mode.
                raise ValueError(f"Agent '{agent_name}' has no team_id in a team-based game.")
            if team_id not in team_payoff_map:
                raise ValueError(f"Agent '{agent_name}' belongs to unknown team '{team_id}'.")
            agent.add_score(team_payoff_map[team_id])
    
    # -------------------------------------------------------------------------
    # Main round logic
    # -------------------------------------------------------------------------
    
    def run_round(self):
        """
        Run a single round of the game using the GameRound helper class.

        Behaviour:
        - If no teams are defined (self.teams is None), this behaves as in the
            original FAIRGAME: payoff matrix is applied directly to agents.
        - If teams are defined, it:
            1. Gets individual strategies for all agents,
            2. Aggregates them to team decisions (majority vote),
            3. Applies payoffs at team level,
            4. Distributes team payoff to each agent in that team.
        """

        round_runner = GameRound(self)

        # Get individual strategies (list or dict)
        round_strategies = round_runner.run()

        # Convert list or dict → dict
        if isinstance(round_strategies, dict):
            strategies_by_agent = round_strategies
        else:
            agent_names = list(self.agents.keys())
            if len(round_strategies) != len(agent_names):
                raise ValueError(
                    f"Expected {len(agent_names)} strategies, got {len(round_strategies)}."
                )
            strategies_by_agent = dict(zip(agent_names, round_strategies))

        # -------------------------------
        # Case 1 – Classic FAIRGAME (no teams)
        # -------------------------------
        if self.teams is None:
            self.choices_made.append(
                [strategies_by_agent[name] for name in self.agents.keys()]
            )
            self.payoff_matrix.attribute_scores(
                list(self.agents.values()),
                [strategies_by_agent[name] for name in self.agents.keys()]
            )

        # -------------------------------
        # Case 2 – Team-Based Mode (3v3, 5v5, etc.)
        # -------------------------------
        else:
            # 1. Aggregate team majority votes
            team_choices = self._aggregate_team_decisions(strategies_by_agent)

            # store for stop-condition compatibility
            self.choices_made.append(
                [team_choices[tid] for tid in self.team_order]
            )

            # 2. Assign team-level scores
            self._assign_team_scores(team_choices)
            
            # --- NEW: store team-level info ---
            ordered_strats = [team_choices[tid] for tid in self.team_order]
            comb_key = self._find_combination_key(ordered_strats)
            payoff_labels = self.payoff_matrix.matrix_data["matrix"][comb_key]
            payoff_values = [self.payoff_matrix.weights[label] for label in payoff_labels]

            self.history.update_round(
                self.current_round,
                "__teams__",  # special pseudo-agent key
                {
                    "team_strategies": {
                        tid: team_choices[tid] for tid in self.team_order
                    },
                    "team_payoffs": {
                        tid: payoff_values[i] for i, tid in enumerate(self.team_order)
                    }
                }
            )


        # Final: Update history
        round_runner._update_round_history()


    # -------------------------------------------------------------------------
    # Stop condition & main run loop
    # -------------------------------------------------------------------------

    def stop_condition_is_met(self):
        """
        Check whether the stop condition is met based on the last round's
        *effective* choices.

        In classic mode:
            - "effective" choices = per-agent strategies (e.g. ["C", "D"])
        In team mode:
            - "effective" choices = per-team strategies (e.g. ["C", "D"])
              ordered by self.team_order.

        Returns:
            bool: True if the last round's combination matches any stop condition,
                  False otherwise.
        """
        if not self.choices_made:
            return False

        last_round_choices = self.choices_made[-1]  # a list of strategies

        # Look up the combination key based on the effective choices
        combination = self._find_combination_key(last_round_choices)

        if combination is not None and combination in self.stop_conditions:
            return True
        return False


    def run(self):
        """
        Runs the simulation until all rounds are complete or a stop condition is met.

        Returns:
            GameHistory: The history object containing all round data.
        """
        while self.current_round <= self.n_rounds and not self.stop_condition_is_met():
            self.run_round()
            self.current_round += 1

        return self.history
