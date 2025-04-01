import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin

def download_kakata_image(url, folder_path, output_prefix_filename):
    """
    Download the first image inside the div with ID 'content' from a given URL,
    save it as the latest image in a specified folder, and maintain a rolling history of 7 days.

    Parameters:
        url (str): The URL of the webpage.
        folder_path (str): The path to the folder where images will be saved.
        output_prefix_filename (str): The prefix for the latest image file.

    Returns:
        None
    """
    try:
        # Ensure the folder exists
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Full path for the latest image file
        latest_file_path = os.path.join(folder_path, f"{output_prefix_filename}.jpg")

        # Rolling rename for the last 7 days
        print("Checking ", latest_file_path, " exists = ", os.path.exists(latest_file_path))
        for i in range(6, 0, -1):
            old_file = os.path.join(folder_path, f"{output_prefix_filename}_{i}.jpg")
            new_file = os.path.join(folder_path, f"{output_prefix_filename}_{i + 1}.jpg")
            print(f"Checking {old_file} with {new_file}");
            if os.path.exists(old_file):
                print(f"Rename {old_file} to {new_file}")
                os.rename(old_file, new_file)
        if os.path.exists(latest_file_path):
            target_path = os.path.join(folder_path, f"{output_prefix_filename}_1.jpg")
            print(f"Rename {latest_file_path} to {target_path}")
            os.rename(latest_file_path, target_path)
        if os.path.exists(os.path.join(folder_path, f"{output_prefix_filename}_7.jpg")):
            os.remove(os.path.join(folder_path, f"{output_prefix_filename}_7.jpg"))

        # Send a GET request to fetch the page content
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the div with id "content" and extract the first image
        content_div = soup.find("div", id="content")
        if content_div:
            img_tag = content_div.find("img")  # Find the first <img> inside the div
            if img_tag and img_tag.get("src"):
                image_url = img_tag["src"]

                # Handle relative URLs
                if not image_url.startswith("http"):
                    image_url = urljoin(url, image_url)

                # Download the image
                img_response = requests.get(image_url)
                img_response.raise_for_status()

                # Open the image and save as the latest image file
                image = Image.open(BytesIO(img_response.content))
                image = image.convert("RGB")  # Ensure compatibility for saving as JPEG
                image.save(latest_file_path, format="JPEG")
                print(f"Image successfully downloaded and saved as '{latest_file_path}'.")
            else:
                print("No image found inside the div with id 'content'.")
        else:
            print("The div with id 'content' was not found on the page.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Test block
if __name__ == "__main__":
    # Define the test URL and folder
    test_url = "https://kakatachungkhoan.vn/cap-nhat-dong-tien-nganh-moi-ngay/"
    test_folder = "external"  # Replace with your desired folder path

    # Call the function for testing
    download_kakata_image(test_url, test_folder, output_prefix_filename="kakata")

