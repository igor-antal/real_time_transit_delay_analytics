import requests
from google.transit import gtfs_realtime_pb2
from api_key import API_KEY


def fetch_gtfs_feed(url: str) -> bytes:
    headers = {"X-Access-Token": API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed
