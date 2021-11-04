# Brief description:

# transforms json_file with non-linguistic data into inner data entities form
# input: path to json file (str)
# output: Data.Match

# -----------------------------------------------------
# Python's libraries
import json
from typing import List
from dataclasses import dataclass

# Other parts of the code
import Types
import Data
# -----------------------------------------------------


# class handing conversion from JSON to MatchData class
class DataInitializer:
    @staticmethod
    def init_match_data(json_file_str: str) -> Data.Match:
        initializer = DataInitializer()

        with open(json_file_str) as json_file:
            json_match_data = json.load(json_file)

        teams: List[Data.Team] = initializer._init_teams(json_match_data=json_match_data)
        venue: Data.Venue = initializer._init_venue(json_match_data=json_match_data)
        score: Data.Score = initializer._init_score(json_match_data=json_match_data)
        incidents: List[Data.Incidents] = initializer._init_incidents(json_match_data=json_match_data)

        return Data.Match(team_home=teams[0], team_away=teams[1], venue=venue, score=score, incidents=incidents)

    @staticmethod
    def _init_teams(json_match_data: dict) -> List[Data.Team]:
        return [DataInitializer._init_team(json_match_data=json_match_data, team_type=Types.Team.HOME),
                DataInitializer._init_team(json_match_data=json_match_data, team_type=Types.Team.AWAY)]

    @staticmethod
    def _init_team(json_match_data: dict, team_type: Types.Team) -> Data.Team:
        id_ = int(json_match_data['participants'][str(team_type.value)]['id'])
        name = json_match_data['participants'][str(team_type.value)]['name']

        # initialize country
        country_id = int(json_match_data['participants'][str(team_type.value)]['country_id'])
        country_name = json_match_data['participants'][str(team_type.value)]['country_name']
        country = Data.Country.create(id_=country_id, name_=country_name)

        lineup: List[Data.Player] = []
        for p in json_match_data['lineup'][str(team_type.value)]:
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
    def _init_score(json_match_data: dict) -> Data.Score:
        return Data.Score.create(goals_home=json_match_data['score'][str(Types.Team.HOME.value)]['1'],
                            goals_away=json_match_data['score'][str(Types.Team.AWAY.value)]['1'])

    @staticmethod
    def _init_venue(json_match_data: dict) -> Data.Venue:
        name = json_match_data['venue_name']
        town = json_match_data['venue_town']
        capacity = json_match_data['venue_capacity']
        if json_match_data['venue_attendance'] is not None:
            attendance = json_match_data['venue_attendance']
        else:
            attendance = 0

        return Data.Venue.create(name=name, town=town, capacity=capacity, attendance=attendance)

    @staticmethod
    def _init_incidents(json_match_data: dict) -> List[Data.Incidents]:

        def _get_aux_incident(id_: int) -> (int, bool):
            for j in json_match_data['incidents']:
                if id_ == j['parentId']:
                    return j, True
            return None, False

        def _get_participant_from_id(team_: Data.Team, id_: int) -> Data.Player:
            for player in team_.lineup:
                if player.id == id_:
                    return player

        def _get_current_score() -> Data.Score:
            if i['value'] is not None:
                return Data.Score.create(goals_home=int(i['value'].split(":")[0]),
                                    goals_away=int(i['value'].split(":")[1]))
            else:
                return Data.Score.create(0,0)

        incidents: List[Data.Incidents] = []
        teams: List[Data.Team] = DataInitializer._init_teams(json_match_data=json_match_data)

        for i in json_match_data['incidents']:

            time: Data.Time = Data.Time.create(time_base=int(i['time']),
                                     time_added=int(i['addedTime']) if i['addedTime'] is not None else 0)

            if i['eventParticipant']['participant']:
                team: Data.Team = teams[0] if int(i['eventParticipant']['participant'][0]['id']) == teams[0].id else teams[1]
            if i['participant']['id'] is not None:
                if i['type']['name'] == 'Own Goal':
                    team: Data.Team = teams[1] if int(i['eventParticipant']['participant'][0]['id']) == teams[0].id else \
                        teams[0]
                    participant: Data.Player = _get_participant_from_id(team_=team, id_=int(i['participant']['id']))
                elif i['type']['name'] == 'Yellow Card' or i['type']['name'] == 'Red Card':
                    participant: Data.Player = _get_participant_from_id(team_=team, id_=int(i['participant']['id']))
                    if participant is None:
                        # Card for coach
                        participant = Data.Player.create(id_=int(i['participant']['id']),
                                                    full_name=i['participant']['fullName'],
                                                    country=None, number=None, lineup_position_id=None)
                else:
                    participant:Data.Player = _get_participant_from_id(team_=team, id_=int(i['participant']['id']))

            inc_str_type: str = i['type']['name']

            if inc_str_type == "Goal":
                current_score = _get_current_score()
                aux_incident = _get_aux_incident(int(i['id']))

                if aux_incident[1]:
                    # goal with assistance
                    assistance = _get_participant_from_id(team_=team, id_=int(aux_incident[0]['participant']['id']))
                    incidents.append(Data.Incidents.Goal.create(participant=participant, team=team, time=time,
                                                           current_score=current_score, assistance=assistance,
                                                           goal_type=Types.Goal.ASSISTANCE))
                else:
                    # solo play goal
                    incidents.append(Data.Incidents.Goal.create(participant=participant, team=team, time=time,
                                                           current_score=current_score, assistance=None,
                                                           goal_type=Types.Goal.SOLO_PLAY))

            elif inc_str_type == "Own Goal":
                current_score = _get_current_score()
                incidents.append(Data.Incidents.Goal.create(participant=participant, team=team, time=time,
                                                       current_score=current_score, assistance=None,
                                                       goal_type=Types.Goal.OWN_GOAL))

            elif inc_str_type == "Penalty Kick":
                aux_incident = _get_aux_incident(int(i['id']))

                scored = False
                if aux_incident[1]:
                    if aux_incident[0]['type']['name'] == "Penalty scored":
                        scored = True

                current_score = _get_current_score()

                incidents.append(Data.Incidents.Penalty.create(participant=participant, team=team, time=time,
                                                          current_score=current_score, scored=scored))

            elif inc_str_type == "Substitution - Out":
                aux_incident = _get_aux_incident(int(i['id']))
                participant_in_id = aux_incident[0]['participant']['id']
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

        # sort incidents by time

        return incidents
