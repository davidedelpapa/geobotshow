from quakefeeds import QuakeFeed
from datetime import datetime, timezone
import logging
import tweepy
import io
import os
import json
from urllib.request import urlopen, Request

logging.basicConfig(filename='tweet.bot.log', level=logging.INFO)
logger = logging.getLogger()

base_url = os.getenv("API_HTTPS").rstrip('/')
POINT_ENDPOINT = "api/point"

def check_events(api, last_events=[]):
    try:
        feed = QuakeFeed("significant", "hour")
        if len(feed) == 0:
            return last_events
        
        new_last_events = []
        for event in feed:
            try:
                e_id = event['id']
                new_last_events.append(e_id)
                if e_id in last_events:
                    continue

                what = event['properties']['type']
                coordinates = event['geometry']['coordinates']
                lon = float(coordinates[0])
                lat = float(coordinates[1])
                place = event['properties']['place']
                magnitude = event['properties']['mag']
                depth = coordinates[2]
                time_raw = event['properties']['time']
                time = datetime.fromtimestamp(float(time_raw) / 1000.0, tz=timezone.utc)
                formatted_time = time.strftime("%b %d, %Y - %H:%M:%S")
                url = event['properties']['url']
                msg = f"{formatted_time}; {what} @ {place}.\nMagnitude: {magnitude}, depth: {depth}\nMore info: {url}"
                geo_data = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat],
                                
                            },
                            "properties": {
                                    "marker": "true"
                            }
                        }
                    ]
                }
                geojson = json.dumps(geo_data, sort_keys=True)

                # Tweet now!
                url = f"{base_url}/{POINT_ENDPOINT}/{lon}/{lat}?near=10000&cropped=1"
                # get file; Need Browser info to avoid Error 403!
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3',
                    'Content-Type': 'application/json; charset=utf-8'
                }
                jsondataasbytes = geojson.encode('utf-8')
                req = Request(url=url, headers=headers, data=jsondataasbytes)
                req.add_header('Content-Length', len(jsondataasbytes))
                fd = urlopen(req)
                image_file = io.BytesIO(fd.read())
                
                # reply to mention
                api.update_with_media(
                    f"{e_id}.png",
                    status=msg, # Still needed for valid reply
                    lat=lat,
                    long=lon,
                    file=image_file
                )
                logger.info(f"Earthquake_id: {e_id}")
            except Exception as e:
                logger.warning(f"Error in event routine: {e}", exc_info=True)
                continue
    except Exception as e:
        logger.warning(f"Error in retrieving feed: {e}", exc_info=True)
    return new_last_events


