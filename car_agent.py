import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI as OpenAIClient
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.tools import StructuredTool
from diffusers import StableDiffusionPipeline
import torch
import google.generativeai as genai
# -------------------------------
# LOAD ENV + MODEL
# -------------------------------
load_dotenv()
model = ChatOllama(model="llama3", temperature=0)
print("Using Google key:", os.getenv("GOOGLE_API_KEY")[:6], "...")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# -------------------------------
# TOOL FUNCTIONS
# -------------------------------
def search(q: str) -> dict:
    """Search with Serper API"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": q})
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def scrape_and_summarize(url: str) -> str:
    """Scrape a webpage and summarize with LLM"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            text = response.text
            prompt = PromptTemplate(
                input_variables=["text"],
                template="Summarize the following webpage content for BMW car details (facts, performance, prices):\n\n{text}",
            )
            formatted = prompt.format(text=text[:3000])
            summary = model.invoke(formatted).content
            return summary
        else:
            return f"Failed to scrape {url}"
    except Exception as e:
        return f"Scrape error: {e}"


# -------------------------------
# IMAGE FUNCTIONS
# -------------------------------
def get_unsplash_image(query: str, save_path="car_image.jpg"):
    """Fetch car image from Unsplash"""
    UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=5&client_id={UNSPLASH_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                img_url = data["results"][0]["urls"]["regular"]
                img_data = requests.get(img_url, timeout=10).content
                with open(save_path, "wb") as f:
                    f.write(img_data)
                return save_path
    except Exception as e:
        print(f"Unsplash image fetch error: {e}")
    return None


def generate_gemini_image(prompt_text: str, save_path: str):
    print(genai.list_models())
    model = genai.GenerativeModel("gemini-2.5-flash-image-preview")

    # request image generation
    response = model.generate_content(
        prompt_text
    )

    # Gemini returns inline base64 image data
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                with open(save_path, "wb") as f:
                    f.write(part.inline_data.data)
                return save_path
    return None


def generate_local_sd_image(prompt: str, save_path="car_image_sd.jpg"):
    """Fallback: Local Stable Diffusion image"""
    try:
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16
        )
        pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
        image = pipe(prompt).images[0]
        image.save(save_path)
        return save_path
    except Exception as e:
        print(f"Local SD image generation error: {e}")
    return None


# -------------------------------
# CAPTION GENERATOR
# -------------------------------
def generate_instagram_post(car_row, enriched_data=""):
    template = """
    You are an automotive expert and social media content creator for the Instagram page @flame_n_gasoline.
    Create an engaging Instagram post about the following BMW.

    ### BASELINE DATA (from CSV)
    - Generation: {generation}
    - Production Years: {production_years}
    - Design Highlights: {design_highlights}
    - Interesting Fact: {interesting_fact}
    - Engine: {engine_data}
    - Launch Price: {launch_price}
    - Current Market Price: {current_market_price}

    ### ENRICHED DATA (from web search & scraping)
    {enriched_data}

    ### TASK
    Write a fun, engaging Instagram caption (3–4 sentences) that:
    - Blends baseline and enriched data
    - Includes at least one interesting fact
    - Mentions performance/tech
    - Highlights cost (launch vs current price)
    - Is motivational, fun, and car-enthusiast friendly
    """
    prompt = PromptTemplate(
        input_variables=[
            "generation",
            "production_years",
            "design_highlights",
            "interesting_fact",
            "engine_data",
            "launch_price",
            "current_market_price",
            "enriched_data",
        ],
        template=template,
    )
    formatted_prompt = prompt.format(**car_row, enriched_data=enriched_data)
    response = model.invoke(formatted_prompt)
    return response.content


# -------------------------------
# AGENT RUNNER
# -------------------------------
def run_agent(df, generation: str, color="white", interior="red"):
    # 1. Get baseline CSV row
    car_row = df[df["generation"] == generation].iloc[0].to_dict()

    # 2. Build enriched query
    base_query = (
        f"BMW {car_row['generation']} "
        f"{car_row.get('production_years','')} "
        f"{car_row.get('engine_data','')} "
        f"launch price {car_row.get('launch_price','')} "
        f"current market price {car_row.get('current_market_price','')}"
    )

    # 3. Search + scrape
    enriched_data = ""
    search_results = search(base_query)
    if search_results and "organic" in search_results:
        for r in search_results["organic"][:2]:  # scrape top 2
            enriched_data += scrape_and_summarize(r["link"]) + "\n"

    # 4. Generate caption
    caption = generate_instagram_post(car_row, enriched_data=enriched_data)

    # 5. Get image (Unsplash → OpenAI → SD fallback)
    # img_query = f"BMW {car_row['generation']} {car_row.get('production_years','')} in {color} with {interior} interior"
    # img_path = get_unsplash_image(img_query, save_path=f"{generation}_unsplash.jpg")

    # if not img_path:
    ai_prompt = f"Photorealistic BMW {car_row['generation']} ({car_row.get('production_years','')}) in {color} with {interior} leather interior, cinematic lighting"
    img_path = generate_gemini_image(ai_prompt, save_path=f"{generation}_ai.jpg")
    # if not img_path:
    #     img_path = generate_local_sd_image(ai_prompt, save_path=f"{generation}_sd.jpg")

    return {"caption": caption, "image_path": img_path}
