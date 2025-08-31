import pandas as pd
from car_agent import run_agent
from instagram_poster import post_to_instagram
import os

# Load the CSV file
csv_file = "BMW_3Series_History.csv"
df = pd.read_csv(csv_file)

# Instagram credentials (use environment variables for safety)
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Iterate through each row of CSV
for _, row in df.iterrows():
    generation = row["generation"]
    color = "white"  # or use row["color"] if available
    interior = "red"  # or use row["interior"] if available

    # Call the agent function
    result = run_agent(df, generation, color=color, interior=interior)

    # Save post as text file
    filename = f"{generation}_post.txt"
    with open(filename, "w") as file:
        file.write(result["caption"])

    print(f"✅ Post for {generation} saved as {filename}")
    print(f"Image saved at: {result['image_path']}")

    # # Post to Instagram
    # if result["image_path"]:
    # # image_url = upload_to_imgbb("/Users/jaikiransawant/Documents/Company_Files/Company_projects/ai_agent_ig-manager-master/E21_ai.jpg")
    # # print("Image URL from ImgBB:", image_url)
    # if image_url:
    # post_to_instagram(
    #     image_url="https://storage.googleapis.com/post_hotos/E21_ai.jpg",
    #     caption="Get ready to ignite your passion for the open road with the iconic BMW E21! This 1975-1983 gem may have been a game-changer back in the day, but its simple boxy design and driver-focused cockpit still turn heads today. Did you know it replaced the legendary BMW 2002 and set the template for compact sports sedans? And the best part? You can get behind the wheel of this piece of automotive history for a steal - launch price: $9,500 (1975), current market price: $18,000-25,000 (2025)! So what are you waiting for? Fire up your engine and join the #flame_ngasoline crew! #BMW #E21 #ClassicCars"
    # )
