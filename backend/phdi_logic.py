from typing import Dict, List

# the brain of the index
# Adequacy Components: (e.g., Legumes, Nuts) – You get more points for eating more, up to a target.
# Moderation Components: (e.g., Red Meat, Added Sugars) – You get fewer points for eating more, with a hard cap.
# Optimum Components: (e.g., Fish, Dairy) – You get points for eating within a specific "sweet spot" range.
# Ratio Components: (e.g., Vegetable Ratios) – You get points based on the variety or balance of certain food groups.
def calculate_phdi_score(categories_kcal_pct: Dict[str, float]) -> Dict[str, any]:
    """
    Calculates the PHDI score based on the percentage of daily kcal for each category.
     categories_kcal_pct: Dict mapping category names to their percentage of total kcal.
    """
    scores = {}
    total_score = 0.0

    # 1. Adequacy Components (Max 10 pts each)
    # Formula: Score = 10 * (Intake / Target), max 10
    adequacy_targets = {
        "nuts_and_peanuts": 11.6,
        "legumes": 11.3,
        "fruits": 5.0,
        "total_vegetables": 3.1,
        "whole_cereals": 32.4
    }
    
    for cat, target in adequacy_targets.items():
        intake = categories_kcal_pct.get(cat, 0.0)
        score = min(10.0, (intake / target) * 10.0) if target > 0 else 0.0
        scores[cat] = round(score, 2)
        total_score += score

    # 2. Moderation Components (Max 10 pts each)
    # Formula: Score = 10 - (10 * Intake / Upper Limit), min 0
    moderation_limits = {
        "red_meat": 2.4,
        "chicken_and_substitutes": 5.0,
        "animal_fats": 1.4,
        "added_sugars": 4.8
    }
    
    for cat, limit in moderation_limits.items():
        intake = categories_kcal_pct.get(cat, 0.0)
        score = max(0.0, 10.0 - (10.0 * intake / limit)) if limit > 0 else 10.0
        scores[cat] = round(score, 2)
        total_score += score

    # 3. Optimum Components (Max 10 pts each)
    # Formula: Linear up to Target, Linear down to Upper Limit, 0 beyond.
    optimum_bounds = {
        "eggs": (0.8, 1.5),
        "fish_and_seafood": (1.6, 5.7),
        "tubers_and_potatoes": (1.6, 3.1),
        "dairy": (6.1, 12.2),
        "vegetable_oils": (16.5, 30.7)
    }
    
    for cat, (target, upper) in optimum_bounds.items():
        intake = categories_kcal_pct.get(cat, 0.0)
        if intake == 0:
            score = 0.0
        elif intake <= target:
            score = (intake / target) * 10.0
        elif intake <= upper:
            # Linear decrease from 10 to 0
            score = 10.0 - ((intake - target) / (upper - target) * 10.0)
        else:
            score = 0.0
        scores[cat] = round(score, 2)
        total_score += score

    # 4. Ratio Components (Max 5 pts each)
    # Note: These use (specific veg energy / total veg energy) * 10.
    veg_ratios = {
        "dark_green_veg_ratio": {"target": 29.5, "upper": 100.0},
        "red_orange_veg_ratio": {"target": 38.5, "upper": 100.0}
    }
    


    for cat, bounds in veg_ratios.items():
        target = bounds["target"]
        upper = bounds["upper"]
        ratio_val = categories_kcal_pct.get(cat, 0.0) 
        
        if ratio_val <= target:
            score = (ratio_val / target) * 5.0 if target > 0 else 0.0
        elif ratio_val <= upper:
            score = 5.0 - ((ratio_val - target) / (upper - target) * 5.0)
        else:
            score = 0.0
            
        scores[cat] = round(score, 2)
        total_score += score

    return {
        "total_score": round(total_score, 2),
        "component_scores": scores
    }
