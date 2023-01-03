"""Creating document structure from Match information."""

# Python's libraries
from typing import List
from dataclasses import dataclass

# Other parts of the code
import Types
import Data
import data_initializer as di

"""Using dataclass(frozen=True) to guarantee immutability.
Each data class has create static method (usually needs specific set of attributes), 
which returns immutable instance (to prevent data from changing during the running of the code).
"""


@dataclass(frozen=True)
class MessageParent:
    """Parent class to represent message."""
    type: Types.Message
    """ 
    This class exists to have common parent for all data class.
    Every message class has a message type. This way we can ensure to address all 
    messages as one type. Also every message has attribute type: Types.Message
    and every message type can have numerous different attributes.
    """


class Message:
    """Class to store every message type."""
    @dataclass(frozen=True)
    class Result(MessageParent):
        """Class to represent result message."""
        team_home: Data.Team
        team_away: Data.Team
        score: Data.Score

        @staticmethod
        def create(team_home: Data.Team, team_away: Data.Team, score: Data.Score):
            """
            Creates immutable instance of message - Result.
            :param team_home: Team which plays home.
            :param team_away: Team which plays away.
            :param score: Final score of the match.
            :return: Message.Result
            """
            return Message.Result(type=Types.Message.RESULT, team_home=team_home, team_away=team_away, score=score)

        def __str__(self):
            return f"-> Type: {self.type.name}, team_home: {self.team_home.name}, team_away: {self.team_away}" \
                f", score: {self.score}"

    @dataclass(frozen=True)
    class Card(MessageParent):
        """Class to represent card message."""
        participant: Data.Player
        team: Data.Team
        time: Data.Time
        card_type: Types.Card

        @staticmethod
        def create(participant: Data.Player, team: Data.Team, time: Data.Time, card_type: Types.Card):
            """
            Creates immutable instance of message - Card.
            :param participant: Player who got the card.
            :param team: Team the participant plays for.
            :param time: Time, when the incident happened.
            :param card_type: Type of the card the participant received.
            :return: Message.Card
            """
            return Message.Card(type=Types.Message.CARD, participant=participant,
                                team=team, time=time, card_type=card_type)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, " \
                f"participant: {self.participant.full_name}, team: {self.team.name}, card_type: {self.card_type.name}"

    @dataclass(frozen=True)
    class Goal(MessageParent):
        """Class to represent goal message."""
        participant: Data.Player
        assistance: Data.Player
        current_score: Data.Score
        team: Data.Team
        time: Data.Time
        goal_type: Types.Goal

        @staticmethod
        def create(participant: Data.Player, team: Data.Team, time: Data.Time, current_score: Data.Score,
                   assistance: Data.Player, goal_type: Types.Goal):
            """
            Creates immutable instance of message - Goal.
            :param participant: Player who scored the goal.
            :param team: Team the participant plays for.
            :param time: Time, when the incident happened.
            :param current_score: Score after the goal.
            :param assistance: Player who made the assist to the goal.
            :param goal_type: Type of the goal.
            :return: Message.Goal
            """
            return Message.Goal(type=Types.Message.GOAL, participant=participant, assistance=assistance,
                                current_score=current_score, team=team, time=time, goal_type=goal_type)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, participant: {self.participant.full_name}" \
                f", team: {self.team.name}, score: {self.current_score.goals_home}-{self.current_score.goals_away}" \
                f", goal_type: {self.goal_type}"

    @dataclass(frozen=True)
    class Substitution(MessageParent):
        """Class to represent substitution message."""
        participant_out: Data.Player
        participant_in: Data.Player
        team: Data.Team
        time: Data.Time

        @staticmethod
        def create(participant_out: Data.Player, team: Data.Team, time: Data.Time, participant_in: Data.Player):
            """
            Creates immutable instance of message - Substitution.
            :param participant_out: Player subbed out.
            :param team: Team who took part in substitution.
            :param time: Time when the substitution happened.
            :param participant_in: Player subbed in
            :return: Message.Substitution
            """
            return Message.Substitution(type=Types.Message.SUBSTITUTION, participant_out=participant_out,
                                        participant_in=participant_in, team=team, time=time)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, participant_out: {self.participant_out.full_name}" \
                f", participant_in: {self.participant_in.full_name}, team: {self.team.name}"

    @dataclass(frozen=True)
    class MissedPenalty(MessageParent):
        """Class to represent missed penalty message."""
        participant: Data.Player
        team: Data.Team
        time: Data.Time

        @staticmethod
        def create(participant: Data.Player, team: Data.Team, time: Data.Time):
            """
            Creates immutable instance of message - MissedPenalty.
            :param participant: Player who missed the penalty.
            :param team: Team the participant plays for.
            :param time: Time when the penalty was missed.
            :return: Message.MissedPenalty
            """
            return Message.MissedPenalty(type=Types.Message.PENALTY_KICK_MISSED, participant=participant,
                                         team=team, time=time)

        def __str__(self):
            return f"-> Type: {self.type.name}, time: {self.time}, participant: " \
                f"{self.participant.full_name}, team: {self.team.name}"


@dataclass(frozen=True)
class DocumentPlan:
    """Class to represent article as a list of messages and title - creating core structure of the article."""
    title: Message
    body: List[Message]

    @staticmethod
    def create(title: Message, body: List[Message]):
        """
        Creates document plan from messages.
        :param title: Message.Result what to say in the title.
        :param body: List of Message that should be in the document plan.
        :return: DocumentPlan
        """
        return DocumentPlan(title=title, body=body)

    def __str__(self):
        return f"TITLE MESSAGE: \n\t{self.title}\nMESSAGES\n\t" + "\n\t".join(map(str, self.body))


class DocumentPlanner:
    """Creating document structure from Match information."""
    @staticmethod
    def plan_document(match_data: Data.Match) -> DocumentPlan:
        """
        Plans the document plan from non-linguistic data (represented as Data.Match).
        :param match_data: Data.Match
        :return: DocumentPlan
        """

        doc_planner = DocumentPlanner()
        title: Message = doc_planner.__plan_title(match_data)   # title has its own specific message
        body: List[Message] = doc_planner.__plan_body(match_data)

        return DocumentPlan.create(title, body)

    @staticmethod
    def __plan_title(match_data: Data.Match) -> Message:
        """
        Plans title message from match data.
        :param match_data: Data.Match
        :return: Message
        """

        return Message.Result.create(match_data.team_home, match_data.team_away, match_data.score)

    @staticmethod
    def __plan_incident_msg(inc: Data.Incident) -> Message:
        """
        Transforms incident into a message.
        :param inc: Data.Incident
        :return: Message
        """

        if type(inc) is Data.Incident.Goal:
            return Message.Goal.create(participant=inc.participant, team=inc.team, time=inc.time,
                                       current_score=inc.current_score, assistance=inc.assistance,
                                       goal_type=inc.goal_type)
        elif inc.type == Types.Incident.PENALTY_KICK:
            if inc.scored is True:
                return Message.Goal.create(participant=inc.participant, team=inc.team, time=inc.time,
                                           current_score=inc.current_score, assistance=None,
                                           goal_type=Types.Goal.PENALTY)
            else:
                return Message.MissedPenalty.create(inc.participant, inc.team, inc.time)
        elif inc.type == Types.Incident.CARD:
            return Message.Card.create(participant=inc.participant, team=inc.team, time=inc.time,
                                       card_type=inc.card_type)
        elif inc.type == Types.Incident.SUBSTITUTION:
            return Message.Substitution.create(participant_out=inc.participant, team=inc.team, time=inc.time,
                                               participant_in=inc.participant_in)
        else:
            print("failed")

    @staticmethod
    def __plan_body(match_data: Data.Match) -> List[Message]:
        """
        Plans body of the article (as list of messages) from match data.
        :param match_data: Data.Match
        :return: List[Message]
        """
        return [DocumentPlanner.__plan_incident_msg(inc) for inc in match_data.incidents]
