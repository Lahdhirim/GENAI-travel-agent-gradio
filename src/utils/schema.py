class ToolsSchema:
    GET_LIVE_WEATHER = "get_live_weather"
    LIST_DESTINATIONS = "list_destinations"
    GET_DESTINATION_INFO = "get_destination_info"
    SEARCH_DESTINATIONS_BY_KEYWORD = "search_destinations_by_keyword"
    RECOMMEND_DESTINATIONS_BY_SEASON = "recommend_destinations_by_season"
    SEARCH_FLIGHTS = "search_flights"


class DBSchema:
    DESTINATION = "destination"
    KEYWORDS = "keywords"
    BEST_SEASON = "best_season"


class WeatherSchema:
    DESTINATION = "destination"
    COUNTRY = "country"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    TEMPERATURE = "temperature"
    WIND_SPEED = "wind_speed"
    PRECIPITATION_PROB = "precipitation_probability"
    DATE = "date"
    TEMPERATURE_C = "temperature (°C)"
    WIND_SPEED_KM_H = "wind_speed (km/h)"
