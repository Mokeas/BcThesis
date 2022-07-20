"""Module storing class representation of data entities - player, score, etc."""

# Python's libraries
from typing import List
from dataclasses import dataclass

# Other parts of the code
import Types

"""
Using dataclass(frozen=True) to guarantee immutability.
Each data class has create static method (usually needs specific set of attributes), 
which returns immutable instance (to prevent data from changing during the running of the code).
"""


@dataclass(frozen=True)
class Score:
    """Data class to store information about score."""
    goals_home: int
    goals_away: int
    goals_sum: int
    goals_difference: int
    result: Types.Result

    @staticmethod
    def create(goals_home: int, goals_away: int):
        """
        Creates immutable instance of Score.
        :param goals_home: Number of goals scored by home team.
        :param goals_away: Number of goals scored by away team.
        :return: Score
        """
        goals_sum = goals_home + goals_away
        goals_difference = abs(goals_home - goals_away)
        result: Types.Result = Score.__init_result(goals_home=goals_home, goals_away=goals_away)
        return Score(goals_home=goals_home, goals_away=goals_away, goals_sum=goals_sum,
                     goals_difference=goals_difference, result=result)

    @staticmethod
    def __init_result(goals_home: int, goals_away: int) -> Types.Result:
        """
        Takes number of goals for each team and calculates result.
        :param goals_home: Number of goals scored by home team.
        :param goals_away: Number of goals scored by away team.
        :return: Types.Result
        """

        if goals_home > goals_away:
            return Types.Result.WIN
        elif goals_home == goals_away:
            return Types.Result.DRAW
        else:
            return Types.Result.LOSS

    def __str__(self):
        return f'{self.goals_home}:{self.goals_away}'


@dataclass(frozen=True)
class Venue:
    """Data class to store information about venue."""
    name: str
    town: str
    capacity: int
    attendance: int
    full_percentage: int

    @staticmethod
    def create(name: str, town: str, capacity: int, attendance: int):
        """
        Creates immutable instance of Venue.
        :param name: Name of the venue.
        :param town: Town of the venue.
        :param capacity: Capacity of the venue.
        :param attendance: Number of people that attended the match.
        :return: Venue
        """
        full_percentage = round((attendance / capacity) * 100)
        return Venue(name=name, town=town, capacity=capacity, attendance=attendance, full_percentage=full_percentage)

    def __str__(self):
        return f"--Venue-- Name: {self.name}, Town: {self.town}, Capacity: {self.capacity}, " \
            f"Attendance: {self.attendance}, Percentage of at.: {self.full_percentage}, "


@dataclass(frozen=True)
class Country:
    """Data class to store information about country."""
    id: int
    name: str

    @staticmethod
    def create(id_: int, name_: str):
        """
        Creates immutable instance of Country.
        :param id_: Identification number.
        :param name_: Name of the country
        :return: Country
        """
        return Country(id=id_, name=name_)


@dataclass(frozen=True)
class Player:
    """Data class to store information about player."""
    id: int
    full_name: str
    country: Country
    lineup_position_id: int
    number: int

    @staticmethod
    def create(id_: int, full_name: str, country: Country, lineup_position_id: int, number: int):
        """
        Creates immutable instance of Player.
        :param id_: Identification number.
        :param full_name: Full name of the player
        :param country: Country where the player was born
        :param lineup_position_id: Id, which signalize whether the player was in the starting lineup.
        :param number: Jersey number of the player.
        :return: Player
        """
        return Player(id=id_, full_name=full_name, country=country,
                      lineup_position_id=lineup_position_id, number=number)

    def get_first_name(self) -> str:
        """Returns first name of the player from his full name."""
        return self.full_name.split()[-1]

    def get_last_name(self) -> str:
        """Returns last name of the player from his full name."""
        return self.full_name.split()[0]

    def get_short_name(self) -> str:
        """Returns last name of the player from his full name."""
        return self.full_name.split()[1][0] + '. ' + self.full_name.split()[0]

    def __str__(self):
        return f"({self.full_name}, {self.number})"


@dataclass(frozen=True)
class Team:
    """Data class to store information about team."""
    id: int
    name: str
    country: Country
    type: Types.Team
    lineup: List[Player]

    @staticmethod
    def create(id_: int, name: str, country: Country, type_: Types.Team, lineup: List[Player]):
        """
        Creates immutable instance of Team.
        :param id_: Identification number.
        :param name: Name of the team.
        :param country: Country of the team.
        :param type_: Whether the team played home, or away.
        :param lineup: List of players who attended the match.
        :return: Team
        """
        return Team(id=id_, name=name, country=country, type=type_, lineup=lineup)

    def __str__(self):
        return f"--Team-- Id: {self.id}, Name: {self.name}, type: {self.type.name}"


@dataclass(frozen=True)
class Time:
    """Data class to store information about time."""
    base: int   # base is normal time, but ends on 45 or 90
    added: int   # added time is number of minutes after 45 or 90

    @staticmethod
    def create(time_base: int, time_added: int):
        """
        Creates immutable instance of Time.
        :param time_base: Number of minutes played.
        :param time_added: Time added to 45/90 minutes (depending on a half)
        :return: Time
        """
        return Time(base=time_base, added=time_added)

    def __str__(self):
        if self.added != 0:
            return f"{self.base} + {self.added}"
        else:
            return str(self.base)

    def __lt__(self, other):
        """Custom comparator to sort times correctly."""
        if self.base != other.base:
            return self.base < other.base
        else:
            return self.added < other.added


@dataclass(frozen=True)
class IncidentParent:
    """Data class to store information about incident."""
    type: Types.Incident
    participant: Player
    team: Team
    time: Time

    def __lt__(self, other):
        """Sorting incidents according to their Time."""
        return self.time < other.time

    def __str__(self):
        return f"-> {self.type.name} ---  time: {self.time}, \
          participant: {self.participant.full_name}, team: {self.team.name}"


class Incident:
    """Data class to store information about each type of incident.
    Each type of incident has it's own subclass (named same as the incident type).
    """
    @dataclass(frozen=True)
    class Goal(IncidentParent):
        """Data class to store information about goal incident."""
        current_score: Score
        assistance: Player
        goal_type: Types.Goal

        @staticmethod
        def create(
                participant: Player, team: Team, time: Time, current_score: Score,
                assistance: Player, goal_type: Types.Goal):
            """
            Creates immutable instance of incident - Incident.Goal.
            :param participant: Player who took part in the incident.
            :param team: Team who took part in the incident (whose player took part in).
            :param time: Time when the incident happened.
            :param current_score: Current score after the goal.
            :param assistance: Player who assisted the to the goal .
            :param goal_type: Type of the goal.
            :return: Incident.Goal
            """
            return Incident.Goal(type=Types.Incident.GOAL, participant=participant, team=team, time=time,
                                 current_score=current_score, assistance=assistance, goal_type=goal_type)

    @dataclass(frozen=True)
    class Penalty(IncidentParent):
        """Data class to store information about penalty incident."""
        scored: bool
        current_score: Score

        @staticmethod
        def create(participant: Player, team: Team, time: Time, current_score: Score, scored: bool):
            """
            Creates immutable instance of incident - Incident.Penalty.
            :param participant: Player who took part in the incident.
            :param team: Team who took part in the incident (whose player took part in).
            :param time: Time when the incident happened.
            :param current_score: Current score after the goal.
            :param scored: Boolean value if the penalty was scored or not.
            :return: Incident.Penalty
            """
            return Incident.Penalty(type=Types.Incident.PENALTY_KICK, participant=participant, team=team, time=time,
                                    scored=scored, current_score=current_score)

    @dataclass(frozen=True)
    class Card(IncidentParent):
        """Data class to store information about card incident."""
        card_type: Types.Card

        @staticmethod
        def create(participant: Player, team: Team, time: Time, card_type: Types.Card):
            """
            Creates immutable instance of incident - Incident.Card.
            :param participant: Player who took part in the incident.
            :param team: Team who took part in the incident (whose player took part in).
            :param time: Time when the incident happened.
            :param card_type: Type of the card.
            :return: Incident.Card
            """
            return Incident.Card(type=Types.Incident.CARD, participant=participant, team=team, time=time,
                                 card_type=card_type)

    @dataclass(frozen=True)
    class Substitution(IncidentParent):
        """Data class to store information about substitution incident."""
        participant_in: Player

        @staticmethod
        def create(participant: Player, team: Team, time: Time, participant_in: Player):
            """
            Create immutable instance of incident - Incident.Substitution.
            :param participant: Player who went out of the pitch (got subbed out).
            :param team: Team who took part in the incident (whose player took part in).
            :param time: Time when the incident happened.
            :param participant_in: Player who went out on the pitch (got subbed in).
            :return: Incident.Substitution
            """
            return Incident.Substitution(type=Types.Incident.SUBSTITUTION, participant=participant,
                                         team=team, time=time, participant_in=participant_in)


@dataclass(frozen=True)
class Match:
    """Data class to store information about the whole match.
    This class stores everything you need to know about the match.
    """
    team_home: Team
    team_away: Team
    score: Score
    venue: Venue
    incidents: List[Incident]

    @staticmethod
    def create(team_home: Team, team_away: Team, score: Score, venue: Venue, incidents: List[Incident]):
        """
        Creates immutable instance of Match.
        :param team_home: Home team.
        :param team_away: Away team.
        :param score: Final score of the match.
        :param venue: Venue where the match was held.
        :param incidents: List of incidents that occurred during the match.
        :return: Match
        """
        return Match(team_home=team_home, team_away=team_away, score=score, venue=venue, incidents=incidents)

    def __str__(self):
        return f"MATCH DATA SUMMARY \n\t{self.team_home}\n\t{self.team_away}\n\t{self.score}\n\t{self.venue}\n" \
               f"TEAM LINEUPS\n\t-> team home lineup: " + ",".join(map(str, self.team_home.lineup)) + \
               f"\n\t-> team away lineup: " + ",".join(map(str, self.team_away.lineup)) + '\n' + \
               f"INCIDENTS\n\t" + "\n\t".join(map(str, self.incidents))
