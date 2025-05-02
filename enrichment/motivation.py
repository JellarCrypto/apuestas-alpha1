def motivation_factor(league_round: str, total_rounds: int) -> int:
    """
    1=baja (primera mitad), 2=media (segunda mitad), 3=alta (playoffs/final).
    league_round ejemplo: "Regular Season - 12"
    """
    num = int(league_round.split()[-1])
    pct = num / total_rounds
    return 1 if pct < 0.5 else (2 if pct < 0.9 else 3)
