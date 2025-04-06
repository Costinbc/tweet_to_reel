import orshot
import sys
import os
from dotenv import load_dotenv
load_dotenv()

def download_tweet_image(link, id):
    ors = orshot.Orshot(os.environ.get("ORSHOT_API_KEY"))
    tweet_url = link
    tweet_id = id

    response = ors.render_from_template({
    "template_id": "tweet-image",
    "response_type": "binary",
    "response_format": "png",
    "modifications": {
        "tweetUrl": tweet_url, 
        "tweetId": tweet_id, 
        "hideMetrics": True, 
        "hideVerifiedIcon": False, 
        "tweetFontSize": 2, 
        "tweetBackgroundColor": "#fff", 
        "tweetTextColor": "#111", 
        "hideDateTime": True, 
        "hideMedia": True, 
        "hideShadow": True, 
        "backgroundColor": "#fff000", 
        "backgroundImageUrl": "", 
        "padding": 0, 
        "width": 1000
    }
    })

    script_path = os.path.abspath(__file__)
    project_root = os.path.abspath(os.path.join(script_path, "..", ".."))
    downloads_dir = os.path.join(project_root, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    output_path = os.path.join(downloads_dir, f"{id}.png")
    with open(output_path, 'wb') as file:
        file.write(response.content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python screenshot.py <tweet_url>")
        sys.exit(1)

    tweet_url = sys.argv[1]
    tweet_id = tweet_url.split('/')[-1]

    download_tweet_image(tweet_url, tweet_id)
