from src.utils.logger_config import logger


def get_ticket_price(destination_city):
    if destination_city:
        destination_city_norm = destination_city.lower()

    ticket_prices = {"london": "799", "paris": "899"}
    logger.info(f"Get ticket price tool called for city {destination_city_norm}")
    price = ticket_prices.get(destination_city_norm, "Unkown city")
    return f"The price of a ticket to {destination_city_norm} is {price}"
