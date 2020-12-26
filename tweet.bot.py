import time
import os
import logging
import tweepy
import requests


from config_tweepy import get_api


logging.basicConfig(filename='tweet.bot.log', level=logging.INFO)
logger = logging.getLogger()

def check_mentions(api, since_id):
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline,
        since_id=since_id).items():
        try:
            new_since_id = max(tweet.id, new_since_id)
            if tweet.in_reply_to_status_id is not None:
                continue
        
            # getting the API response
            response = requests.get(os.getenv("API_HTTPS"))
            
            # reply to mention
            api.update_status(
                status=f"@{tweet.user.screen_name} {response.text}",
                in_reply_to_status_id=tweet.id,
            )
            logger.info(f"Since_id: {new_since_id}")
        except Exception as e:
            logger.Warning(f"Error answering to mention: {e}", exc_info=True)
            continue
    return new_since_id

def main():
    api = get_api()
    since_id = int(os.getenv("BOT_SINCEID"))
    while True:
        since_id = check_mentions(api, since_id)
        time.sleep(60)

if __name__ == "__main__":
    main()