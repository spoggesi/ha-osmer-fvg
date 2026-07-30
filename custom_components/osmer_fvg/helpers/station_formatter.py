def format_station(
    station,
    icons,
) -> str:
    return (
        f"{station.name} • "
        f"{station.altitude} m • "
        f"{icons}"
    )