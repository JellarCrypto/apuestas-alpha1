def estimate_xg(shots_on_target: int, league_avg_conv: float) -> float:
    """
    Estima xG = tiros a puerta × tasa de conversión de la liga.
    """
    return shots_on_target * league_avg_conv
