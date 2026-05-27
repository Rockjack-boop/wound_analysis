import os
import numpy as np
from PIL import Image
from c_modules.image_processor import (
    process_grayscale, 
    process_sobel_edges, 
    process_redness_detection
)

def analyze_wound_image(image_path, static_dir):
    """
    Analyzes an uploaded wound image using the C image processing module 
    and simulates an AI decision framework based on real image features.
    
    Generates three processed visualization images in the static folder:
    1. Grayscale representation
    2. Sobel edge gradient map
    3. Redness/inflammation isolation map
    
    Returns a dictionary filled with diagnostic reports:
    - wound_type (Surgical, Burn, Laceration, Ulcer, Abrasion, Puncture)
    - severity_level (Critical, High, Moderate, Low)
    - major_minor (Major vs. Minor)
    - infection_possibility (High, Medium, Low)
    - confidence (Percentage score)
    - first_aid (Formatted recommended steps)
    - metrics (edge density, redness ratio, processing durations)
    """
    
    # Define paths for saving processed images in the static folder
    filename = os.path.basename(image_path)
    base_name, ext = os.path.splitext(filename)
    
    # Destination directories for C processing outputs
    gray_name = f"{base_name}_gray{ext}"
    sobel_name = f"{base_name}_sobel{ext}"
    redness_name = f"{base_name}_redness{ext}"
    
    gray_path = os.path.join(static_dir, "processed", gray_name)
    sobel_path = os.path.join(static_dir, "processed", sobel_name)
    redness_path = os.path.join(static_dir, "processed", redness_name)
    
    os.makedirs(os.path.dirname(gray_path), exist_ok=True)
    
    # 1. Execute Grayscale processing (C / NumPy fallback)
    gray_result = process_grayscale(image_path, gray_path)
    
    # 2. Execute Sobel Edge Detection (C / NumPy fallback)
    sobel_result = process_sobel_edges(image_path, sobel_path)
    
    # 3. Execute Redness/Inflammation profiling (C / NumPy fallback)
    redness_result = process_redness_detection(image_path, redness_path)
    
    # 4. Extract metrics from processed images
    # We can measure edge density from the Sobel edge image
    sobel_img = Image.open(sobel_path).convert("L")
    sobel_arr = np.array(sobel_img)
    total_pixels = sobel_arr.size
    
    # Calculate Sobel edge density (percentage of pixels exceeding edge threshold)
    edge_pixels = np.sum(sobel_arr > 50)
    edge_density = (edge_pixels / total_pixels) * 100
    
    red_count = redness_result["red_pixel_count"]
    redness_ratio = redness_result["redness_ratio"]
    
    # 5. Advanced Medical Diagnostic Inference logic based on C visual characteristics:
    
    # Let's inspect raw image properties using Pillow to determine base brightness
    original_img = Image.open(image_path).convert("RGB")
    original_arr = np.array(original_img)
    avg_r = float(np.mean(original_arr[:, :, 0]))
    avg_g = float(np.mean(original_arr[:, :, 1]))
    avg_b = float(np.mean(original_arr[:, :, 2]))
    overall_brightness = (avg_r + avg_g + avg_b) / 3
    
    # Classification Rules (Mathematical heuristics linking visual symptoms to diagnoses):
    # - Diabetic Ulcer: Medium-to-high edges (crater structure) + prominent redness surrounding a darker central necrotic core (lower brightness)
    # - Laceration: Very high edge density (sharp cuts/ruptured skin) + moderate redness
    # - Surgical Wound: High edge density (straight suture lines) + low redness
    # - Burn: Extremely high redness ratio + lower edge density (blisters/diffuse skin texture)
    # - Puncture: Low edge density (small focal point) + moderate red inflammation ring
    # - Abrasion: Medium edge density (surface scratches) + low/medium redness
    
    wound_type = "Abrasion"
    confidence_offset = 0.0
    
    if redness_ratio > 18.0 and edge_density < 10.0:
        wound_type = "Thermal Burn"
        confidence_offset = 2.5
    elif redness_ratio > 12.0 and edge_density > 15.0 and overall_brightness < 110:
        wound_type = "Diabetic Ulcer"
        confidence_offset = 4.2
    elif edge_density > 18.0:
        # Lacerations have highly sharp edges
        if redness_ratio > 8.0:
            wound_type = "Infected Laceration"
        else:
            wound_type = "Laceration"
        confidence_offset = 1.8
    elif edge_density > 10.0 and redness_ratio < 4.0:
        wound_type = "Surgical Wound"
        confidence_offset = 3.0
    elif edge_density < 6.0 and redness_ratio > 6.0:
        wound_type = "Puncture Wound"
        confidence_offset = -1.0
    else:
        # Default or surface scratch
        wound_type = "Abrasion"
        confidence_offset = 0.5
        
    # Severity classification (Major vs Minor):
    # A wound is Major if it is highly inflamed, has extremely complex texture (edges),
    # or shows low brightness indicating necrosis/tissue death.
    is_major = False
    severity = "Moderate"
    emergency_level = "Standard First Aid"
    
    if redness_ratio > 14.0 or edge_density > 18.0 or (overall_brightness < 90 and redness_ratio > 8.0):
        is_major = True
        severity = "Critical"
    elif redness_ratio > 6.0 or edge_density > 10.0:
        severity = "High"
    else:
        severity = "Minor"
        
    major_minor_str = "Major" if is_major else "Minor"
    
    # Infection Possibility profiling based on the extracted redness ratio
    infection_possibility = "Low"
    if redness_ratio > 12.0:
        infection_possibility = "High"
    elif redness_ratio > 4.0:
        infection_possibility = "Medium"
    else:
        infection_possibility = "Low"
        
    # Emergency Level calculation:
    if is_major and infection_possibility == "High":
        emergency_level = "Critical (Immediate ER Visit)"
    elif is_major or infection_possibility == "High":
        emergency_level = "Urgent (Urgent Care Clinic)"
    elif infection_possibility == "Medium":
        emergency_level = "Moderate (Consult Doctor)"
    else:
        emergency_level = "Low (Standard First Aid)"
        
    # Confidence score calculation (Normalized with minor random variation for realism, but mathematically tied to image contrast)
    contrast = float(np.std(original_arr))
    base_confidence = 80.0
    if contrast > 40:
        base_confidence += 10.0
    else:
        base_confidence += 5.0
        
    confidence = base_confidence + confidence_offset
    confidence = min(max(confidence, 70.0), 99.2)
    
    # Recommended Medical Guidelines & First Aid
    first_aid_steps = []
    if wound_type == "Thermal Burn":
        first_aid_steps = [
            "Cool the burn: Run cool (not cold) tap water over the burn area for 10-15 minutes or apply a cool, wet compress.",
            "Remove tight items: Gently remove rings, bracelets, or clothing from the burned area before it swells.",
            "Do not pop blisters: Fluid-filled blisters protect the skin from infection. If one pops, clean gently with soap/water.",
            "Apply sterile bandage: Cover the burn loosely with a sterile, non-stick gauze bandage.",
            "Seek emergency care immediately if the burn covers a large area, involves face/hands, or if skin looks charred/peeled."
        ]
    elif wound_type == "Diabetic Ulcer":
        first_aid_steps = [
            "Decompress / Offload: Avoid putting any weight or pressure whatsoever on the ulcerated area.",
            "Cleanse carefully: Wash the ulcer gently with normal saline solution or mild soap. Avoid rubbing/scrubbing.",
            "Keep dry and covered: Apply a clean, breathable, non-adhesive dressing to shield against micro-organisms.",
            "Inspect daily: Carefully check for expanding redness, warmth, or foul odor.",
            "CRITICAL: Do not self-treat. Contact your endocrinologist, podiatrist, or wound care specialist immediately."
        ]
    elif wound_type == "Infected Laceration" or infection_possibility == "High":
        first_aid_steps = [
            "Control bleeding: Apply continuous gentle pressure with a sterile cloth until bleeding completely stops.",
            "Rinse thoroughly: Flush the laceration with clean lukewarm water for 5 minutes. Do not apply harsh alcohol.",
            "Apply antibacterial barrier: Apply a thin layer of sterile antibiotic ointment (e.g. Neosporin).",
            "Dressing: Wrap with a sterile dressing, changing it at least twice daily.",
            "Doctor visit: Since active infection symptoms were detected, medical assessment and prescription antibiotics may be required."
        ]
    elif wound_type == "Laceration" or wound_type == "Surgical Wound":
        first_aid_steps = [
            "Protect stitches: Keep surgical incisions dry for the first 24-48 hours, then gently wash with mild soap.",
            "Apply compression: If minor bleeding occurs, press a sterile pad gently against the incision line.",
            "Check structural integrity: Ensure sutures, staples, or adhesive strips remain intact. Do not pick scabs.",
            "Minimize tension: Rest the affected limb to prevent the wound margins from pulling apart.",
            "Change dressing daily: Re-apply fresh sterile gauze to keep the area protected from friction."
        ]
    elif wound_type == "Puncture Wound":
        first_aid_steps = [
            "Promote minor drainage: Allow the puncture to bleed slightly to help flush out internal contaminants, unless bleeding is heavy.",
            "Clean depth: Wash the area thoroughly with soap and warm water under pressure for at least 5 minutes.",
            "Avoid sealing: Do not apply heavy ointment or waterproof tape immediately; this can trap anaerobic bacteria deep inside.",
            "Tetanus Check: Ensure you have received a tetanus booster shot within the last 5 years. If not, seek a booster within 48 hours.",
            "Monitor closely: Deep punctures are highly prone to severe deep-tissue infections."
        ]
    else: # Abrasion
        first_aid_steps = [
            "Wash hands: Always clean hands with soap and water before handling or touching damaged skin.",
            "Flush surface: Rinse the abrasion with clean tap water to flush away embedded dirt, gravel, or grit.",
            "Apply protective barrier: Spread a thin layer of petroleum jelly or antibiotic ointment to keep the skin moist.",
            "Cover loosely: Apply a sterile, breathable adhesive bandage or non-stick pad to protect from friction.",
            "Aerate: Once a thin scab forms, you can leave it open to dry air to speed up late-stage healing."
        ]
        
    first_aid_text = "||".join(first_aid_steps)
    
    return {
        "wound_type": wound_type,
        "severity": severity,
        "major_minor": major_minor_str,
        "infection_possibility": infection_possibility,
        "emergency_level": emergency_level,
        "confidence": round(confidence, 1),
        "first_aid": first_aid_text,
        "metrics": {
            "edge_density": round(edge_density, 2),
            "redness_ratio": round(redness_ratio, 2),
            "red_pixels": red_count,
            "brightness": round(overall_brightness, 1),
            "gray_time_ms": gray_result["time_ms"],
            "sobel_time_ms": sobel_result["time_ms"],
            "redness_time_ms": redness_result["time_ms"],
            "c_mode_gray": gray_result["mode"],
            "c_mode_sobel": sobel_result["mode"],
            "c_mode_red": redness_result["mode"]
        },
        "visuals": {
            "gray": f"processed/{gray_name}",
            "sobel": f"processed/{sobel_name}",
            "redness": f"processed/{redness_name}"
        }
    }
