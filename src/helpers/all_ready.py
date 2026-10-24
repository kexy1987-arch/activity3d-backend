def all_ready(room: dict) -> bool:
    """
    Returns True only if:
    - all teams are ready (team["ready"] == True)
    - all players in ready_players dict are ready (value == True)
    """

    # Team readiness
    teams = room.get("teams", [])
    for team in teams:
        if not team.get("ready", False):
            return False

    # Player readiness
    ready_players = room.get("ready_players", {})
    for player_id, is_ready in ready_players.items():
        if not is_ready:
            return False

    return True