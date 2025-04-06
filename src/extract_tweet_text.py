import cv2
import numpy as np
import os
from PIL import Image
import sys

# Currently not used
def crop_tweet(input_path, output_path=None):
    print(f"🧪 Reading image from: {input_path}")
    image = cv2.imread(input_path)
    if image is None:
        print("❌ OpenCV failed to read the image.")
        raise ValueError(f"Could not open image at {input_path}")

    x0 = max(image.shape[1] // 2 - 400, 0)
    x1 = min(image.shape[1] // 2 + 400, image.shape[1])

    cropped = image[0:image.shape[0], x0:x1]
    cv2.imwrite(output_path, cropped)
    return output_path

# Currently not used
def crop_tweet_author_and_text_only(input_path, output_path=None):
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    _, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    text_areas = []
    media_y = height

    for i in range(1, len(stats)):
        x, y, w, h, area = stats[i]
        if area < 50:
            continue
        if y < height * 0.5 and h < 50:
            text_areas.append((x, y, w, h))
        if w > width * 0.8 and h > height * 0.2 and y > height * 0.15:
            media_y = min(media_y, y)

    if media_y == height:
        text_max_y = 0
        if text_areas:
            text_max_y = max([y + h for x, y, w, h in text_areas])
        media_y = text_max_y + 20 if text_max_y > 0 else int(height * 0.33)

    if media_y < 100:
        media_y = int(height * 0.33)

    cropped_img = img[0:media_y, 0:width]

    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_header_text.jpg"

    cv2.imwrite(output_path, cropped_img)
    return output_path


# Currently not used
def extract_tweet_card_with_alpha(input_path, output_path=None):
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    
    white_mask = cv2.inRange(hsv, lower_white, upper_white)
    
    kernel = np.ones((5, 5), np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        tweet_card = img[y:y+h, x:x+w]
        
        if output_path is None:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_card_only.png"
        
        cv2.imwrite(output_path, tweet_card)
        
        return output_path
    else:
        raise ValueError("Could not find white tweet card in the image")


def extract_tweet_card(input_path, output_path=None):
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not open image at {input_path}")
    
    height, width = img.shape[:2]
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([40, 255, 255])
    
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    inverted_mask = cv2.bitwise_not(yellow_mask)
    
    contours, _ = cv2.findContours(inverted_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        margin = 0
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(width - x, w + 2*margin)
        h = min(height - y, h + 2*margin)
        
        tweet_card = img[y + 7:y+h - 7, x+7:x+w-7]
        
        if output_path is None:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_card_only.png"
        
        bgr_tweet = tweet_card
        b, g, r = cv2.split(bgr_tweet)
        alpha = np.ones(b.shape, dtype=b.dtype) * 255
        rgba_tweet = cv2.merge((b, g, r, alpha))
        
        cv2.imwrite(output_path, rgba_tweet)
        
        return output_path
    else:
        raise ValueError("Could not find tweet card in the image")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_tweet_text.py <crop_action> <input_image_path> <output_image_path>")
        print("crop_action: 'tweet' or 'author_and_text_only'")
        sys.exit(1)

    crop_action = sys.argv[1]
    input_image_path = os.path.abspath(sys.argv[2])
    output_image_path = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else None

    if crop_action == "tweet":
        crop_tweet(input_image_path, output_image_path)
    elif crop_action == "author_and_text_only":
        crop_tweet_author_and_text_only(input_image_path, output_image_path)
    elif crop_action == "tweet_card":
        extract_tweet_card(input_image_path, output_image_path)
    elif crop_action == "tweet_card_alpha":
        extract_tweet_card_with_alpha(input_image_path, output_image_path)
    else:
        print("Invalid crop action. Use 'tweet' or 'author_and_text_only'.")
        sys.exit(2)
