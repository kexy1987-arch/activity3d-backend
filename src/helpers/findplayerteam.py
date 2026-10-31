def find_player_team(player_id: str, teams: list[dict]):
    return next(
        (t for t in teams if any(p["id"] == player_id for p in t.get("players", []))),
        None
    )
