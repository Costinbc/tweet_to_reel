import pika_sdk
import sys
import os

def download_tweet_image(link, id):
    ps = pika_sdk.PikaSdk(os.environ.get("PIKA_API_KEY"))

    response = ps.generate_image_from_template('tweet-image', {
        "tweetUrl": link,
        "tweetId": id,
        "hideMetrics": "true",
        "hideVerifiedIcon": "false",
        "tweetFontSize": "2",
        "tweetBackgroundColor": "#ffffff",
        "tweetTextColor": "#111111",
        "hideDateTime": "true",
        "backgroundColor": "#ffffff",
        "backgroundImageUrl": "",
        "padding": "0",
        "width": "1080"
    }, 'binary')

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
