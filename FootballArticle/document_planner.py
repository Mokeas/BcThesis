# Brief description:

# creating document structure from match information
# input: Data.Match
# output: DocumentPlan

# -----------------------------------------------------
# Python's libraries
from typing import List
from dataclasses import dataclass

# Other parts of the code
import Types
import Data
import data_initializer as DI
# -----------------------------------------------------


@dataclass(frozen=True)
class Message:
    type: Types.Message


class Messages:
    @dataclass(frozen=True)
    class Result(Message):
        team_home: Data.Team
        team_away: Data.Team
        score: Data.Score

        @staticmethod
        def create(team_home: Data.Team, team_away: Data.Team, score: Data.Score):
            return Messages.Result(type=Types.Message.RESULT, team_home=team_home, team_away=team_away, score=score)

        def __str__(self):
            return f"-> Type: {self.type.name}, team_home: {self.team_home.name}, team_away: {self.team_away}" \
                f", score: {self.score}"

    @dataclass(frozen=True)
    class Card(Message):
        participant: Data.Player
        team: Data.Team
        time: Data.Time
        card_type: Types.Card

        @staticmethod
        def create(participant: Data.Player, team: Data.Team, time: Data.Time, card_type: Types.Card):
            return Messages.Card(type=Types.Message.CARD, participant=participant,
                                 team=team, time=time, card_type=card_type)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, " \
                f"participant: {self.participant.full_name}, team: {self.team.name}, card_type: {self.card_type.name}"

    @dataclass(frozen=True)
    class Goal(Message):
        participant: Data.Player
        assistance: Data.Player
        current_score: Data.Score
        team: Data.Team
        time: Data.Time
        goal_type: Types.Goal

        @staticmethod
        def create(participant: Data.Player, team: Data.Team, time: Data.Time, current_score: Data.Score,
                   assistance: Data.Player, goal_type: Types.Goal):
            return Messages.Goal(type=Types.Message.GOAL, participant=participant, assistance=assistance,
                                 current_score=current_score, team=team, time=time, goal_type=goal_type)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, participant: {self.participant.full_name}" \
                f", team: {self.team.name}, score: {self.current_score.goals_home}-{self.current_score.goals_away}" \
                f", goal_type: {self.goal_type}"

    @dataclass(frozen=True)
    class Substitution(Message):
        participant_out: Data.Player
        participant_in: Data.Player
        team: Data.Team
        time: Data.Time

        @staticmethod
        def create(participant_out: Data.Player, team: Data.Team, time: Data.Time, participant_in: Data.Player):
            return Messages.Substitution(type=Types.Message.SUBSTITUTION, participant_out=participant_out,
                                         participant_in=participant_in, team=team, time=time)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, participant_out: {self.participant_out.full_name}" \
                f", participant_in: {self.participant_in.full_name}, team: {self.team.name}"

    @dataclass(frozen=True)
    class MissedPenalty(Message):
        participant: Data.Player
        team: Data.Team
        time: Data.Time

        @staticmethod
        def create(participant: Data.Player, team: Data.Team, time: Data.Time):
            return Messages.MissedPenalty(type=Types.Message.PENALTY_KICK_MISSED, participant=participant,
                                          team=team, time=time)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, participant: " \
                f"{self.participant.full_name}, team: {self.team.name}"


@dataclass(frozen=True)
class DocumentPlan:
    title: Messages
    body: List[Messages]

    @staticmethod
    def create(title: Messages, body: List[Messages]):
        return DocumentPlan(title=title, body=body)

    def __str__(self):
        return f"TITLE MESSAGE: \n\t{self.title}\nMESSAGES\n\t" + "\n\t".join(map(str, self.body))


class DocumentPlanner:

    @staticmethod
    def plan_document(match_data: Data.Match) -> DocumentPlan:
        doc_planner = DocumentPlanner()
        title: Messages = doc_planner._plan_title(match_data)
        body: List[Messages] = doc_planner._plan_body(match_data)

        return DocumentPlan.create(title, body)

    @staticmethod
    def _plan_title(match_data: Data.Match) -> Messages:
        return Messages.Result.create(match_data.team_home, match_data.team_away, match_data.score)

    @staticmethod
    def _plan_incident_msg(inc: Data.Incidents) -> Messages:
        if type(inc) is Data.Incidents.Goal:
            return Messages.Goal.create(participant=inc.participant, team=inc.team, time=inc.time,
                                        current_score=inc.current_score, assistance=inc.assistance,
                                        goal_type=inc.goal_type)
        elif inc.type == Types.Incident.PENALTY_KICK:
            if inc.scored is True:
                return Messages.Goal.create(participant=inc.participant, team=inc.team, time=inc.time,
                                            current_score=inc.current_score, assistance=None,
                                            goal_type=Types.Goal.PENALTY)
            else:
                return Messages.MissedPenalty.create(inc.participant, inc.team, inc.time)
        elif inc.type == Types.Incident.CARD:
            return Messages.Card.create(participant=inc.participant, team=inc.team, time=inc.time,
                                        card_type=inc.card_type)
        elif inc.type == Types.Incident.SUBSTITUTION:
            return Messages.Substitution.create(participant_out=inc.participant, team=inc.team, time=inc.time,
                                                participant_in=inc.participant_in)
        else:
            print("failed")

    @staticmethod
    def _plan_body(match_data: Data.Match) -> List[Messages]:
        return [DocumentPlanner._plan_incident_msg(inc) for inc in match_data.incidents]