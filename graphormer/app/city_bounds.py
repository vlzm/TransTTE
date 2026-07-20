"""Single source of truth for city bounding boxes and town detection.

Coordinates are always (lat, lon). ``lat`` is the North/South degree,
``lon`` is the East/West degree. The two serving apps (``backend`` and
``graphormer``) live in separate Docker contexts without a shared package,
so this file is deliberately duplicated into each context rather than
imported across them. Keep the two copies in sync.
"""

# Bounding boxes of the supported cities. Values taken from the road-graph
# node extents. (lat, lon) — lat_* are latitudes, lon_* are longitudes.
CITY_BOUNDS = {
    'abakan': {
        'lat_min': 52.84332097535,
        'lat_max': 53.9852115715,
        'lon_min': 90.91763111635001,
        'lon_max': 91.88558398090001,
    },
    'omsk': {
        'lat_min': 54.78700068105,
        'lat_max': 55.39520542775,
        'lon_min': 72.8949037781,
        'lon_max': 73.75839039050001,
    },
}


def _in_bounds(start_lat, start_lon, end_lat, end_lon, bounds):
    return (
        min(start_lat, end_lat) >= bounds['lat_min']
        and max(start_lat, end_lat) <= bounds['lat_max']
        and min(start_lon, end_lon) >= bounds['lon_min']
        and max(start_lon, end_lon) <= bounds['lon_max']
    )


def check_town(start_lat, start_lon, end_lat, end_lon):
    """Return the city ('abakan' | 'omsk') containing both endpoints, else None."""
    for city, bounds in CITY_BOUNDS.items():
        if _in_bounds(start_lat, start_lon, end_lat, end_lon, bounds):
            return city
    return None
