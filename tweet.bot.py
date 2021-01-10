import time
import os
import re
import io
import logging
import tweepy
import requests
from urllib.request import urlopen, Request

from config_tweepy import get_api

logging.basicConfig(filename='tweet.bot.log', level=logging.INFO)
logger = logging.getLogger()

# No Geolocation reponse
NO_GEO_MSG = "It seems as the user has not enabled geolocation for this tweet. Please enable geolocation and retry."

# URL constants
base_url = os.getenv("API_HTTPS").rstrip('/')
BB_ENDPOINT = "api/bbox"
POINT_ENDPOINT = "api/point"

def bounding_box(points):
    x_coordinates, y_coordinates = zip(*points)
    return [(min(x_coordinates), min(y_coordinates)), (max(x_coordinates), max(y_coordinates))]
def get_point(points):
    x_coordinates, y_coordinates = zip(*points)
    return [min(x_coordinates), min(y_coordinates)]

def check_mentions(api, since_id):
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline,
        since_id=since_id).items():
        try:
            geolocation_error = False
            new_since_id = max(tweet.id, new_since_id)
            if tweet.in_reply_to_status_id is not None:
                continue
            try:
                # Checking the location
                location = tweet.coordinates
                if location is None:
                    location = tweet.place.bounding_box.coordinates
                    if location is None:
                        geolocation_error = True
                # Have to use RegEx, because there are various ways in which these coords can be shown, sadly
                loc = re.findall(r"[-+]?\d*\.\d+|\d+", str(location))
                loc = [float(i) for i in loc]
            except TypeError:
               geolocation_error = True

            if geolocation_error is True:
                 # User not geolocated; Abort and reply
                api.update_status(
                    status=f"@{tweet.user.screen_name} {NO_GEO_MSG}",
                    in_reply_to_status_id=tweet.id,
                )
                logger.info(f"Since_id: {new_since_id}")
                os.environ['BOT_SINCEID'] = str(new_since_id)
                continue

            coords = []
            for lon, lat in [loc[pos:pos + 2] for pos in range(0, len(loc), 2)]:
                coords.append((lon, lat))
            bb = bounding_box(coords)
            # Flatten the list
            list_bb = list(sum(bb, ()))
            # check if it is a bounding box or a point!
            if list_bb[0] == list_bb[0] and list_bb[0] == list_bb[0]:
                p = get_point(coords)
                lon = p[0]
                lat = p[1]
                url = f"{base_url}/{POINT_ENDPOINT}/{lon}/{lat}?near=300&cropped=1"
            else:
                lon = list_bb[0]
                lat = list_bb[1]
                url = f"{base_url}/{BB_ENDPOINT}/{lon}/{lat}/{list_bb[2]}/{list_bb[3]}?cropped=1"
            # get file; Need Browser info to avoid Error 403!
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
            req = Request(url=url, headers=headers)
            fd = urlopen(req)
            image_file = io.BytesIO(fd.read())
            
            # reply to mention
            api.update_with_media(
                "image.png",
                status=f"@{tweet.user.screen_name}", # Still needed for valid reply
                in_reply_to_status_id=tweet.id,
                lat=lat,
                long=lon,
                file=image_file
            )
            logger.info(f"Since_id: {new_since_id}")
            os.environ['BOT_SINCEID'] = str(new_since_id)
        except Exception as e:
            logger.warning(f"Error answering to mention: {e}", exc_info=True)
            continue
    return new_since_id

def main():
    api = get_api()
    since_id = int(os.getenv("BOT_SINCEID"))
    while True:
        since_id = check_mentions(api, since_id)
        time.sleep(30)



if __name__ == "__main__":
    main()