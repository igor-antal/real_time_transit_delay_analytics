import requests
from google.transit import gtfs_realtime_pb2
from api_key import API_KEY
from .logger import logger


def fetch_gtfs_feed(url: str) -> bytes:
    headers = {"X-Access-Token": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as error:
        logger.exception(error)
        raise
    except requests.exceptions.HTTPError as error:
        logger.exception(error)
        raise

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed
