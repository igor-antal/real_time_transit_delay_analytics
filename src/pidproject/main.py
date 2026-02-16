from pidproject.ingestion.ingest_trip_updates import get_trip_updates
from pidproject.ingestion.ingest_vehicle_updates import get_vehicle_updates


if __name__ == "__main__":
    get_trip_updates()
    get_vehicle_updates()
