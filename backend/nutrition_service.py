import os
import json
import requests
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
USDA_API_KEY = os.environ.get("USDA_API_KEY", "DEMO_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# if GEMINI_API_KEY:
genai.configure(api_key=GEMINI_API_KEY, transport='rest')

# When user types what they ate,app sends it to gemini to extract food items and quantities
# Example output: [{"food_item": "chicken", "quantity_g": 150, "meal_type": "lunch"}, {"food_item": "rice", "quantity_g": 100, "meal_type": "lunch"}]
def parse_food_log(log_text: str) -> List[Dict]:
    """
    Uses Gemini to parse natural language food log into structured JSON.
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"""
    Parse the following daily food diary into a JSON array of objects.
    Each object must have: "food_item", "quantity_g", and "meal_type".

    CRITICAL: If the user does not provide grams or explicit portion sizes (e.g., 'a huge steak', 'some salad'), do NOT estimate it. Ask them for a rough estimate before calculating the score by returning a JSON object with an "error" key.
    Example: {{"error": "Please provide a rough estimate of the quantity for your food items (e.g., 150g, 2 pieces, a bowl)."}}
    
    If valid quantities are provided, return the JSON array of objects.
    
    Food diary: "{log_text}"
    Return ONLY the JSON.
    """
    try:
        response = model.generate_content(prompt)
        print("Gemini response:",response)

        # Sometimes Gemini adds markdown backticks, so we strip them
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
            
        items = json.loads(response_text)
        if isinstance(items, dict) and "error" in items:
            raise ValueError(items["error"])
        if not items:
            raise ValueError("Could not find any clear food items. Please specify clearly what you ate.")
        return items
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        raise ValueError("I couldn't understand what you ate. Please try describing your meal more clearly.")
    except Exception as e:
        print(f"Gemini API Error: {e}")
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"An error occurred while parsing the food log.")

# for every food item found, we need to find the kcal and category mapping. 
# We will use USDA FoodData Central API to get the kcal and category mapping.
# If the food item is not found in the USDA FoodData Central API, we will use a heuristic to find the kcal and category mapping.
# Example output: {"kcal": 150, "phdi_category": "chicken_and_substitutes"}
def get_nutritional_data(food_item: str, quantity_g: float) -> Dict:
    """
    Fetches kcal and category mapping for a food item using USDA FoodData Central or heuristic.
    """
    # 1. Try Heuristic first for PHDI mapping (USDA doesn't provide PHDI categories)
    item_lower = food_item.lower()
    mapping = {
        "egg": "eggs",
        "bread": "whole_cereals",
        "rice": "whole_cereals",
        "pasta": "whole_cereals",
        "chicken": "chicken_and_substitutes",
        "beef": "red_meat",
        "pork": "red_meat",
        "lamb": "red_meat",
        "apple": "fruits",
        "banana": "fruits",
        "orange": "fruits",
        "salad": "total_vegetables",
        "broccoli": "total_vegetables",
        "spinach": "total_vegetables",
        "beans": "legumes",
        "lentils": "legumes",
        "nuts": "nuts_and_peanuts",
        "peanuts": "nuts_and_peanuts",
        "milk": "dairy",
        "cheese": "dairy",
        "yogurt": "dairy",
        "butter": "animal_fats",
        "oil": "vegetable_oils",
        "potato": "tubers_and_potatoes",
        "sugar": "added_sugars",
        "salmon": "fish_and_seafood",
        "tuna": "fish_and_seafood",
        "fish": "fish_and_seafood"
    }
    
    phdi_cat = "other"
    for key, cat in mapping.items():
        if key in item_lower:
            phdi_cat = cat
            break

    # 2. Fetch Kcal from USDA
    kcal = quantity_g * 1.5 # Default fallback
    try:
        if USDA_API_KEY != "DEMO_KEY":
            url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_item}&pageSize=1&api_key={USDA_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get("foods"):
                food = data["foods"][0]
                # Search for Energy (kcal) in nutrients
                for nutrient in food.get("foodNutrients", []):
                    if nutrient.get("nutrientName") == "Energy" and nutrient.get("unitName") == "KCAL":
                        kcal_per_100g = nutrient.get("value", 150.0)
                        kcal = (quantity_g / 100.0) * kcal_per_100g
                        break
    except Exception as e:
        print(f"USDA API error: {e}")

    return {
        "kcal": round(kcal, 2),
        "phdi_category": phdi_cat
    }

# calculate the phdi score based on the category_kcal and total_kcal 
# Example output: {"nuts_and_peanuts": 10.0, "legumes": 10.0, 
#                   "fruits": 10.0, "total_vegetables": 10.0, 
#                   "whole_cereals": 10.0, "red_meat": 10.0, 
#                   "chicken_and_substitutes": 10.0, "animal_fats": 10.0, 
#                   "added_sugars": 10.0, "eggs": 10.0, 
#                   "fish_and_seafood": 10.0, "tubers_and_potatoes": 10.0, 
#                   "dairy": 10.0, "vegetable_oils": 10.0, 
#                   "dark_green_veg_ratio": 10.0, "red_orange_veg_ratio": 10.0}
# this is the dictionary that will be used to calculate the phdi score
def map_to_phdi(food_items_data: List[Dict]) -> Dict[str, float]:
    category_kcal = {cat: 0.0 for cat in [
        "nuts_and_peanuts", "legumes", "fruits", "total_vegetables", "whole_cereals",
        "red_meat", "chicken_and_substitutes", "animal_fats", "added_sugars",
        "eggs", "fish_and_seafood", "tubers_and_potatoes", "dairy", "vegetable_oils",
        "dark_green_veg_ratio", "red_orange_veg_ratio"
    ]}
    total_kcal = 0.0
    
    for item in food_items_data:
        cat = item.get("phdi_category")
        kcal = item.get("kcal", 0.0)
        if cat in category_kcal:
            category_kcal[cat] += kcal
        total_kcal += kcal
        
    if total_kcal == 0:
        return {cat: 0.0 for cat in category_kcal}
        
    percentages = {cat: (kcal / total_kcal) * 100 for cat, kcal in category_kcal.items()}
    
    # Ratios (simplified mock)
    total_veg_intake = category_kcal.get("total_vegetables", 0.0)
    if total_veg_intake > 0:
        percentages["dark_green_veg_ratio"] = 3.0
        percentages["red_orange_veg_ratio"] = 4.0
    else:
        percentages["dark_green_veg_ratio"] = 0.0
        percentages["red_orange_veg_ratio"] = 0.0
        
    return percentages
