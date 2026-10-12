from PIL import Image
from pypdf import PdfReader
import fitz
import pytesseract
import io
import re
import requests

# ==================================================
# TESSERACT CONFIG
# ==================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ==================================================
# PDF + OCR EXTRACTION
# ==================================================

def extract_text(file_bytes, filename=""):

    try:
        # =====================================
        # TXT FILE
        # =====================================

        if filename.lower().endswith(".txt"):

            return file_bytes.decode(
                "utf-8",
                errors="ignore"
            )

        # =====================================
        # PDF FILE
        # =====================================

        doc = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )

        text_parts = []

        for page in doc:

            page_text = page.get_text("text")

            if page_text and page_text.strip():

                text_parts.append(page_text)

            else:

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(3, 3)
                )

                image = Image.open(
                    io.BytesIO(
                        pix.tobytes("png")
                    )
                )

                ocr_text = pytesseract.image_to_string(
                    image
                )

                if ocr_text:
                    text_parts.append(
                        ocr_text
                    )

        doc.close()

        text = "\n".join(text_parts)

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        return text.strip()

    except Exception as e:

        print(
            "Document Extraction Error:",
            e
        )

        return ""

# ==================================================
# ENTITY EXTRACTION
# ==================================================

def extract_entities(text):

    original_text = text or ""
    t = original_text.lower()

    builders = [
        "lodha",
        "godrej",
        "prestige",
        "sobha",
        "dlf",
        "brigade",
        "hiranandani",
        "oberoi",
        "runwal"
    ]

    # -------------------------------
    # LOCATION
    # -------------------------------

    found_location = "Unknown"

    location_patterns = [
        r"location\s*:\s*([^\n\r]+)",
        r"project location\s*:\s*([^\n\r]+)",
        r"site location\s*:\s*([^\n\r]+)",
        r"address\s*:\s*([^\n\r]+)"
    ]

    for pattern in location_patterns:

        match = re.search(
            pattern,
            original_text,
            re.IGNORECASE
        )

        if match:
            found_location = match.group(1).strip()
            break

    if found_location == "Unknown":

        known_localities = [
            "powai",
            "andheri",
            "bandra",
            "juhu",
            "worli",
            "chembur",
            "thane",
            "mulund",
            "goregaon",
            "borivali",
            "whitefield",
            "gachibowli",
            "gurgaon",
            "noida"
        ]

        for locality in known_localities:

            if locality in t:
                found_location = locality.title()
                break

    # -------------------------------
    # BUILDER
    # -------------------------------

    found_builder = next(
        (
            builder.title()
            for builder in builders
            if builder in t
        ),
        "Unknown"
    )

    # -------------------------------
    # SIZE
    # -------------------------------

    size_sqft = None

    size_match = re.search(
        r"(\d[\d,]*)\s*(sq\.?\s*ft|sqft|square feet)",
        original_text,
        re.IGNORECASE
    )

    if size_match:

        try:

            size_sqft = int(
                size_match.group(1).replace(",", "")
            )

        except Exception:

            size_sqft = None

    return {
        "location": found_location,
        "builder": found_builder,
        "size_sqft": size_sqft
    }

# ==================================================
# LOCATION SCORE
# ==================================================

def location_score(location):

    if not location:
        return 50

    loc = location.lower()

    premium = [
        "powai",
        "bandra",
        "worli",
        "juhu",
        "hiranandani"
    ]

    strong = [
        "andheri",
        "goregaon",
        "thane",
        "mulund"
    ]

    if any(x in loc for x in premium):
        return 90

    if any(x in loc for x in strong):
        return 85

    if "mumbai" in loc:
        return 80

    if "bengaluru" in loc:
        return 80

    if "hyderabad" in loc:
        return 78

    if "delhi" in loc:
        return 82

    return 60

# ==================================================
# CONNECTIVITY SCORE
# ==================================================

def connectivity_score(text):

    t = (text or "").lower()

    score = 50

    if "metro" in t:
        score += 15

    if "highway" in t:
        score += 10

    if "airport" in t:
        score += 10

    if "railway" in t:
        score += 5

    if "bus" in t:
        score += 5

    return min(score, 100)

# ==================================================
# LIFESTYLE SCORE
# ==================================================

def lifestyle_score(text):

    t = (text or "").lower()

    score = 40

    if "school" in t:
        score += 10

    if "hospital" in t:
        score += 10

    if "mall" in t:
        score += 10

    if "park" in t:
        score += 5

    if "gym" in t:
        score += 5

    return min(score, 100)

# ==================================================
# PROPERTY PRICE EXTRACTION
# ==================================================

def extract_price(text):

    if not text:
        return None

    # ----------------------------------
    # ₹3,45,00,000
    # ----------------------------------

    rupee_match = re.search(
        r"₹\s*([\d,]+)",
        text,
        re.IGNORECASE
    )

    if rupee_match:

        try:

            value = int(
                rupee_match.group(1)
                .replace(",", "")
            )

            if value > 100000:
                return value

        except:
            pass

    # ----------------------------------
    # INR 3,45,00,000
    # ----------------------------------

    inr_match = re.search(
        r"inr\s*([\d,]+)",
        text,
        re.IGNORECASE
    )

    if inr_match:

        try:

            value = int(
                inr_match.group(1)
                .replace(",", "")
            )

            if value > 100000:
                return value

        except:
            pass

    # ----------------------------------
    # 3.45 crore
    # ----------------------------------

    crore_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(crore|cr)",
        text,
        re.IGNORECASE
    )

    if crore_match:

        return int(
            float(crore_match.group(1))
            * 10000000
        )

    # ----------------------------------
    # 345 lakh
    # ----------------------------------

    lakh_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(lakh|lakhs)",
        text,
        re.IGNORECASE
    )

    if lakh_match:

        return int(
            float(lakh_match.group(1))
            * 100000
        )

    return None

# ==================================================
# AFFORDABILITY ANALYSIS
# ==================================================

def affordability_analysis(
    property_price,
    monthly_income,
    existing_emi=0,
    down_payment=0
):

    loan_amount = max(
        0,
        property_price - down_payment
    )

    annual_rate = 0.085
    monthly_rate = annual_rate / 12
    tenure = 20 * 12

    if loan_amount <= 0:
        emi = 0

    else:
        emi = (
            loan_amount
            * monthly_rate
            * ((1 + monthly_rate) ** tenure)
        ) / (
            ((1 + monthly_rate) ** tenure) - 1
        )

    debt_ratio = (
        emi + existing_emi
    ) / max(monthly_income, 1)

    if debt_ratio < 0.35:
        rating = "Excellent"

    elif debt_ratio < 0.50:
        rating = "Manageable"

    elif debt_ratio < 0.65:
        rating = "Stretch"

    else:
        rating = "High Risk"

    return {
        "loan_amount": round(loan_amount, 2),
        "estimated_emi": round(emi, 2),
        "debt_ratio": round(debt_ratio * 100, 2),
        "income_utilization": round(debt_ratio * 100, 2),
        "affordability_rating": rating
    }

# ==================================================
# INVESTMENT GRADE
# ==================================================

def investment_grade(score):

    if score >= 85:
        return "A+"

    elif score >= 75:
        return "A"

    elif score >= 65:
        return "B"

    elif score >= 55:
        return "C"

    return "D"

# ==================================================
# CONFIDENCE SCORE
# ==================================================

def confidence_score(entities):
    score = 40

    if entities.get("location") != "Unknown":
        score += 25

    if entities.get("builder") != "Unknown":
        score += 20

    if entities.get("size_sqft"):
        score += 15

    return min(score, 100)

# ==================================================
# SCORE COLOR
# ==================================================

def score_color(score):

    if score >= 80:
        return "green"

    elif score >= 60:
        return "orange"

    return "red"


# ==================================================
# GEO LOCATION
# ==================================================

import requests


def geocode_location(location_name):

    if not location_name:
        return None

    if str(location_name).strip().lower() == "unknown":
        return None

    try:

        location_name = str(location_name).strip()

        # ---------------------------------------
        # KNOWN HIGH-CONFIDENCE LOCATIONS
        # ---------------------------------------

        known_locations = {

            "powai": {
                "lat": 19.1176,
                "lon": 72.9060
            },

            "powai, mumbai": {
                "lat": 19.1176,
                "lon": 72.9060
            },

            "prem nagar, powai": {
                "lat": 19.1176,
                "lon": 72.9060
            },

            "prem nagar, powai, mumbai": {
                "lat": 19.1176,
                "lon": 72.9060
            },

            "hiranandani gardens, powai": {
                "lat": 19.1185,
                "lon": 72.9113
            },

            "hiranandani gardens, powai, mumbai": {
                "lat": 19.1185,
                "lon": 72.9113
            },

            "bandra west": {
                "lat": 19.0607,
                "lon": 72.8363
            },

            "andheri east": {
                "lat": 19.1136,
                "lon": 72.8697
            },

            "andheri west": {
                "lat": 19.1364,
                "lon": 72.8272
            }
        }

        key = (
            location_name
            .lower()
            .strip()
        )

        # ---------------------------------------
        # PARTIAL MATCHING
        # ---------------------------------------

        for known_name, coords in known_locations.items():

            if known_name in key:
                return coords

        # ---------------------------------------
        # NOMINATIM FALLBACK
        # ---------------------------------------

        search_location = location_name

        if "india" not in search_location.lower():
            search_location += ", India"

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": search_location,
                "format": "json",
                "limit": 1
            },
            headers={
                "User-Agent":
                "PropertyIntelligencePlatform/2.0"
            },
            timeout=10
        )

        if response.status_code != 200:
            print(
                f"Geocoder HTTP Error: "
                f"{response.status_code}"
            )
            return None

        results = response.json()

        if not results:
            print(
                f"No geocode results for: "
                f"{search_location}"
            )
            return None

        return {
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"])
        }

    except Exception as e:

        print(
            f"Geocode Error for "
            f"'{location_name}': {e}"
        )

        return None