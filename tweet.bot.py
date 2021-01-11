import time
import os

from config_tweepy import get_api
from geobotshow.mentions import check_mentions
from geobotshow.earthquakes import check_events

def main():
    api = get_api()
    since_id = int(os.getenv("BOT_SINCEID"))
    last_events = []
    while True:
        since_id = check_mentions(api, since_id)
        last_events = check_events(api, last_events)
        time.sleep(30)

if __name__ == "__main__":
    main()