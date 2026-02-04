import math

def bbox_from_point(lat: float, lon: float, radius_nm: float):
    # 1 degree lat ~ 60 NM
    dlat = radius_nm / 60.0
    dlon = radius_nm / (60.0 * max(0.1, math.cos(math.radians(lat))))
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)