"""Transforms json_file with non-linguistic data into inner data entities form."""

# Python's libraries
import json
from typing import List
from dataclasses import dataclass

# Other parts of the code
import Types
import Data


class DataInitializer:
    """Class handling conversion from JSON to Data.Match class."""
    @staticmethod
    def init_match_data(json_file_str: str) -> Data.Match:
        """Transforms json_file with non-linguistic data into inner data entities form."""
        initializer = DataInitializer()

        with open(json_file_str, encoding='utf-8') as json_file:
            json_match_data: dict = json.load(json_file)

        teams: (Data.Team, Data.Team) = initializer._init_teams(json_match_data=json_match_data)
        venue: Data.Venue = initializer._init_venue(json_match_data=json_match_data)
        score: Data.Score = initializer._init_score(json_match_data=json_match_data)
        incidents: List[Data.Incidents] = initializer._init_incidents(json_match_data=json_match_data,
                                                                      team_home=teams[0], team_away=teams[1])

        return Data.Match(team_home=teams[0], team_away=teams[1], venue=venue, score=score, incidents=incidents)

    @staticmethod
    def _init_teams(json_match_data: dict) -> (Data.Team, Data.Team):
        """Initializes tuple of Teams - home team [0] and away team [1]."""
        return (DataInitializer._init_team(json_match_data=json_match_data, team_type=Types.Team.HOME),
                DataInitializer._init_team(json_match_data=json_match_data, team_type=Types.Team.AWAY))

    @staticmethod
    def _init_team(json_match_data: dict, team_type: Types.Team) -> Data.Team:
        """Initializes Team from json dictionary, team_type says if the team to initialize is home or away."""
        id_ = int(json_match_data['participants'][str(team_type.value)]['id'])
        name = json_match_data['participants'][str(team_type.value)]['name']
        country: Data.Country = DataInitializer._init_country(json_match_data, team_type)

        # initializing every player of the team lineup
        lineup: List[Data.Player] = []
        for p in json_match_data['lineup'][str(team_type.value)]:
            # extracting every attribute of player
            p_full_name = p['participant']['fullName']
            p_id = int(p['participant']['id'])
            p_country_id = int(p['participant']['countries'][0]['id'])
            p_country_name = p['participant']['countries'][0]['name']
            p_country: Data.Country = Data.Country.create(id_=p_country_id, name_=p_country_name)
            p_lineup_position_id = int(p['lineupPositionId'])
            p_number = int(p['number'])

            lineup.append(Data.Player.create(id_=p_id, full_name=p_full_name, country=p_country,
                                             lineup_position_id=p_lineup_position_id, number=p_number))

        return Data.Team.create(id_=id_, name=name, country=country, type_=team_type, lineup=lineup)

    @staticmethod
    def _init_country(json_match_data: dict, team_type: Types.Team) -> Data.Country:
        """Initializes Country from json dictionary."""
        country_id = int(json_match_data['participants'][str(team_type.value)]['country_id'])
        country_name = json_match_data['participants'][str(team_type.value)]['country_name']
        return Data.Country.create(id_=country_id, name_=country_name)

    @staticmethod
    def _init_score(json_match_data: dict) -> Data.Score:
        """Initializes Score from json dictionary."""
        return Data.Score.create(goals_home=json_match_data['score'][str(Types.Team.HOME.value)]['1'],
                                 goals_away=json_match_data['score'][str(Types.Team.AWAY.value)]['1'])

    @staticmethod
    def _init_venue(json_match_data: dict) -> Data.Venue:
        """Initializes Venue from json dictionary."""
        name = json_match_data['venue_name']
        town = json_match_data['venue_town']
        capacity = json_match_data['venue_capacity']

        # attendance may not be recorded
        attendance = int(json_match_data['venue_attendance']) if json_match_data['venue_attendance'] is not None else 0

        return Data.Venue.create(name=name, town=town, capacity=capacity, attendance=attendance)

    @staticmethod
    def _init_incidents(json_match_data: dict, team_home: Data.Team, team_away: Data.Team) -> List[Data.Incidents]:
        """Initializes list of Incidents from json dictionary."""

        def _get_aux_incident(id_: int) -> (bool, int):
            """Searches for parent incidents. Returns tuple of bool and int.
            Bool indicates if parent incident exists, number is the id of the parent.
            """
            for j in json_match_data['incidents']:
                if id_ == j['parentId']:
                    return True, j
            return False, None   # int is set to None, because the value is never needed

        def _get_participant_from_id(team_: Data.Team, id_: int) -> Data.Player:
            """Returns Player from the lineup according his id."""
            for player in team_.lineup:
                if player.id == id_:   # else branch not required since json file is well-build
                    return player

        def _get_current_score() -> Data.Score:
            """Returns current Score of the match."""
            if i['value'] is not None:  # check if value exists, if not, create explicit score 0:0
                return Data.Score.create(goals_home=int(i['value'].split(":")[0]),
                                         goals_away=int(i['value'].split(":")[1]))
            else:
                return Data.Score.create(0, 0)

        # initializing list of Incidents
        incidents: List[Data.Incidents] = []
        for i in json_match_data['incidents']:
            # initializing every attribute of an Incident

            # time
            time: Data.Time = Data.Time.create(time_base=int(i['time']),
                                               time_added=int(i['addedTime']) if i['addedTime'] is not None else 0)

            # team
            team: Data.Team = None
            if i['eventParticipant']['participant']:  # ToDO: do i even need it here?
                team = team_home if int(i['eventParticipant']['participant'][0]['id']) == team_home.id else team_away

            inc_str_type: str = i['type']['name']

            # participant
            participant: Data = None
            if i['participant']['id'] is not None:
                participant: Data.Player = _get_participant_from_id(team_=team, id_=int(i['participant']['id']))
                if inc_str_type == 'Own Goal':   # if the incident is own goal, teams are switched
                    # ToDo team: Data.Team = team_away if int(i['eventParticipant']['participant'][0]['id'])
                    #  == team_home.id else team_home
                    team: Data.Team = team_away if team == team_home else team_home   # performing switch
                if inc_str_type == 'Yellow Card' or inc_str_type == 'Red Card':
                    if participant is None:   # card for coach
                        participant = Data.Player.create(id_=int(i['participant']['id']),
                                                         full_name=i['participant']['fullName'],
                                                         country=None, number=None, lineup_position_id=None)

            # initializing the whole Incident according to inc_string_type
            if inc_str_type == "Goal":
                aux_incident = _get_aux_incident(int(i['id']))

                if aux_incident[0]:   # goal with assistance
                    assistance = _get_participant_from_id(team_=team, id_=int(aux_incident[1]['participant']['id']))
                    incidents.append(Data.Incidents.Goal.create(participant=participant, team=team, time=time,
                                                                current_score=_get_current_score(),
                                                                assistance=assistance,
                                                                goal_type=Types.Goal.ASSISTANCE))
                else:   # solo play goal
                    incidents.append(Data.Incidents.Goal.create(participant=participant, team=team, time=time,
                                                                current_score=_get_current_score(),
                                                                assistance=None,
                                                                goal_type=Types.Goal.SOLO_PLAY))
            elif inc_str_type == "Own Goal":
                incidents.append(Data.Incidents.Goal.create(participant=participant, team=team, time=time,
                                                            current_score=_get_current_score(),
                                                            assistance=None,
                                                            goal_type=Types.Goal.OWN_GOAL))
            elif inc_str_type == "Penalty Kick":
                # scored penalty is represented by parent Incident
                aux_incident = _get_aux_incident(int(i['id']))
                scored = True if aux_incident[0] and aux_incident[1]['type']['name'] == "Penalty scored" else False

                incidents.append(Data.Incidents.Penalty.create(participant=participant, team=team, time=time,
                                                               current_score=_get_current_score(), scored=scored))
            elif inc_str_type == "Substitution - Out":
                aux_incident = _get_aux_incident(int(i['id']))
                participant_in_id = aux_incident[1]['participant']['id']
                participant_in = _get_participant_from_id(team_=team, id_=participant_in_id)

                incidents.append(Data.Incidents.Substitution.create(participant=participant, team=team, time=time,
                                                                    participant_in=participant_in))
            elif inc_str_type == "Yellow Card":
                aux_incident = _get_aux_incident(int(i['id']))
                if aux_incident[1]:
                    incidents.append(Data.Incidents.Card.create(participant=participant, team=team, time=time,
                                                                card_type=Types.Card.RED_AUTO))
                else:
                    incidents.append(Data.Incidents.Card.create(participant=participant, team=team, time=time,
                                                                card_type=Types.Card.YELLOW))

            elif inc_str_type == "Red Card":
                if i['parentId'] is None:
                    incidents.append(Data.Incidents.Card.create(participant=participant, team=team, time=time,
                                                                card_type=Types.Card.RED_INSTANT))

            elif inc_str_type == "Substitution - In" \
                    or inc_str_type == "Assistance" \
                    or inc_str_type == "Penalty scored" \
                    or inc_str_type == "Penalty missed" \
                    or inc_str_type == "Extended time second half"\
                    or inc_str_type == "Extended time first half"\
                    or inc_str_type == "Action not on pitch"\
                    or inc_str_type == "Goal Disallowed":
                pass

            else:
                raise ValueError("Unknown incident occurred")

        incidents.sort()
        return incidents
