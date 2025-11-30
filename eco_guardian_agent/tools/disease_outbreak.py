import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from tools.helpers import get_coords

def get_disease_outbreaks(location: str) -> Dict:
    """
    Get disease outbreak information from public health sources.
    Uses multiple data sources including WHO, GDELT, and outbreak databases.
    
    Args:
        location: City, region, or country name
        
    Returns:
        Dictionary with outbreak information
    """
    lat, lon = get_coords(location)
    if lat is None:
        return {
            "status": "error",
            "message": f"Could not find coordinates for: {location}"
        }

    try:
        outbreaks = []

        if who_outbreaks := fetch_who_outbreaks(location):
            outbreaks.extend(who_outbreaks)

        if gdelt_outbreaks := fetch_gdelt_disease_events(location, lat, lon):
            outbreaks.extend(gdelt_outbreaks)

        if covid_data := fetch_outbreak_info(location):
            outbreaks.append(covid_data)

        return {
            "status": "success",
            "location": location,
            "coords": {"lat": lat, "lon": lon},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outbreaks": outbreaks,
            "outbreak_count": len(outbreaks),
            "sources": [
                "WHO Disease Outbreak News",
                "GDELT Disease Events",
                "outbreak.info",
            ],
            "note": "Data aggregated from multiple public health surveillance sources.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching outbreak data: {str(e)}"
        }


def fetch_who_outbreaks(location: str) -> List[Dict]:
    # sourcery skip: low-code-quality
    """
    Fetch disease outbreaks from WHO Disease Outbreak News RSS feed.
    """
    try:
        # WHO Disease Outbreak News RSS
        who_rss = "https://www.who.int/feeds/entity/csr/don/en/rss.xml"
        
        response = requests.get(who_rss, timeout=15)
        if response.status_code != 200:
            return []
        
        # Parse RSS feed (simple XML parsing)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        outbreaks = []
        location_lower = location.lower()
        
        # Parse RSS items
        for item in root.findall('.//item')[:20]:  # Last 20 items
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            description = item.find('description')
            
            if title is not None and title.text:
                title_text = title.text.lower()
                
                # Check if location is mentioned in title or description
                desc_text = description.text.lower() if description is not None and description.text else ""
                
                if location_lower in title_text or location_lower in desc_text:
                    # Extract disease name from title
                    disease_name = title.text.split('-')[0].strip() if '-' in title.text else title.text
                    
                    outbreaks.append({
                        "source": "WHO",
                        "disease": disease_name,
                        "title": title.text if title is not None else "Unknown",
                        "url": link.text if link is not None else "",
                        "published_date": pub_date.text if pub_date is not None else "",
                        "description": description.text[:200] if description is not None and description.text else "",
                        "severity": "official_who_report"
                    })
        
        return outbreaks
        
    except Exception as e:
        print(f"[ERROR] WHO RSS fetch failed: {e}")
        return []


def fetch_gdelt_disease_events(location: str, lat: float, lon: float) -> List[Dict]:
    """
    Fetch disease outbreak events from GDELT (Global Database of Events).
    GDELT monitors news worldwide for disease outbreak mentions.
    """
    try:
        # GDELT GEO API - search for disease-related events
        # Free API, no key required

        # Calculate date range (last 30 days)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)

        # Format dates for GDELT (YYYYMMDD)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        # Disease keywords to search
        disease_keywords = [
            "outbreak", "epidemic", "disease", "infection", 
            "dengue", "malaria", "cholera", "typhoid", "covid"
        ]

        outbreaks = []

        gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        # GDELT DOC API endpoint
        for keyword in disease_keywords[:3]:  # Limit to 3 keywords to avoid rate limits
            params = {
                "query": f"{keyword} {location}",
                "mode": "artlist",
                "maxrecords": 5,
                "format": "json",
                "startdatetime": f"{start_str}000000",
                "enddatetime": f"{end_str}235959",
            }

            response = requests.get(gdelt_url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])

                outbreaks.extend(
                    {
                        "source": "GDELT News Monitor",
                        "disease": keyword.title(),
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "published_date": article.get("seendate", ""),
                        "domain": article.get("domain", ""),
                        "language": article.get("language", ""),
                        "severity": "news_mention",
                    }
                    for article in articles[:3]
                )
        return outbreaks

    except Exception as e:
        print(f"[ERROR] GDELT fetch failed: {e}")
        return []


def fetch_outbreak_info(location: str) -> Optional[Dict]:
    """
    Fetch COVID-19 data from outbreak.info API.
    """
    try:
        # outbreak.info provides COVID-19 genomic surveillance data
        api_url = "https://api.outbreak.info/genomics/location-lookup"
        
        params = {
            "name": location,
            "cumulative": True
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                
                return {
                    "source": "outbreak.info",
                    "disease": "COVID-19",
                    "location": result.get("name", location),
                    "total_sequences": result.get("total_count", 0),
                    "last_updated": result.get("date_modified", ""),
                    "severity": "ongoing_surveillance",
                    "url": "https://outbreak.info"
                }
        
        return None
        
    except Exception as e:
        print(f"[ERROR] outbreak.info fetch failed: {e}")
        return None


def search_disease_outbreaks_web(location: str, disease: Optional[str] = None) -> Dict:
    """
    Search for disease outbreak information using web sources.
    Searches WHO, CDC, and health news for recent outbreaks.
    
    Args:
        location: City, region, or country
        disease: Optional specific disease to search for
        
    Returns:
        Dictionary with outbreak information from web sources
    """
    lat, lon = get_coords(location)
    
    search_query = f"disease outbreak {location}"
    if disease:
        search_query = f"{disease} outbreak {location}"
    
    search_query += " site:who.int OR site:cdc.gov OR site:healthmap.org"
    
    return {
        "status": "success",
        "location": location,
        "search_query": search_query,
        "note": "This function should trigger web_search tool in the agent. Search WHO.int, CDC.gov for recent outbreak reports.",
        "recommended_sources": [
            "https://www.who.int/emergencies/disease-outbreak-news",
            "https://www.cdc.gov/outbreaks/",
            "https://www.healthmap.org/",
            "https://www.promedmail.org/"
        ]
    }


# -------------------------------------------------
# SYMPTOM CHECKER
# -------------------------------------------------
def check_symptoms(symptoms: List[str], location: str) -> Dict:
    """
    Analyze symptoms and match with known disease patterns in the area.
    
    Args:
        symptoms: List of symptoms (e.g., ["fever", "cough", "headache"])
        location: User's location
        
    Returns:
        Possible disease matches with severity
    """
    # Common disease symptom patterns
    disease_patterns = {
        "COVID-19": {
            "symptoms": ["fever", "cough", "fatigue", "loss of taste", "loss of smell", "shortness of breath"],
            "severity": "moderate to severe",
            "action": "Get tested immediately, isolate, seek medical care if breathing difficulty"
        },
        "Influenza": {
            "symptoms": ["fever", "cough", "sore throat", "body aches", "fatigue", "headache"],
            "severity": "moderate",
            "action": "Rest, hydrate, antiviral medication within 48 hours"
        },
        "Dengue Fever": {
            "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint pain", "muscle pain", "rash", "bleeding"],
            "severity": "severe",
            "action": "Seek immediate medical attention, monitor for warning signs"
        },
        "Malaria": {
            "symptoms": ["fever", "chills", "sweating", "headache", "nausea", "vomiting", "body aches"],
            "severity": "severe",
            "action": "Urgent medical evaluation and blood test required"
        },
        "Typhoid": {
            "symptoms": ["sustained fever", "headache", "abdominal pain", "constipation", "weakness"],
            "severity": "severe",
            "action": "Medical evaluation and blood culture needed"
        },
        "Cholera": {
            "symptoms": ["severe diarrhea", "vomiting", "dehydration", "muscle cramps"],
            "severity": "severe",
            "action": "Emergency medical care - severe dehydration risk"
        },
        "Measles": {
            "symptoms": ["fever", "cough", "runny nose", "red eyes", "rash", "white spots in mouth"],
            "severity": "moderate to severe",
            "action": "Isolate and seek medical care, highly contagious"
        },
        "Common Cold": {
            "symptoms": ["runny nose", "sneezing", "sore throat", "cough", "mild fever"],
            "severity": "mild",
            "action": "Rest, hydrate, over-the-counter medications"
        }
    }

    # Normalize symptoms
    symptoms_lower = [s.lower().strip() for s in symptoms]

    # Match symptoms with diseases
    matches = []
    for disease, info in disease_patterns.items():
        disease_symptoms = [s.lower() for s in info["symptoms"]]

        if matching_symptoms := [
            s
            for s in symptoms_lower
            if any(ds in s or s in ds for ds in disease_symptoms)
        ]:
            match_score = len(matching_symptoms) / len(info["symptoms"])

            matches.append({
                "disease": disease,
                "match_score": round(match_score * 100, 1),
                "matching_symptoms": matching_symptoms,
                "all_symptoms": info["symptoms"],
                "severity": info["severity"],
                "recommended_action": info["action"]
            })

    # Sort by match score
    matches.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "status": "success",
        "location": location,
        "input_symptoms": symptoms,
        "possible_diseases": matches[:5],  # Top 5 matches
        "warning": "This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
        "urgent_care_needed": any(m["severity"] == "severe" and m["match_score"] > 40 for m in matches)
    }


# -------------------------------------------------
# HOSPITAL FINDER
# -------------------------------------------------
def find_nearest_hospitals(location: str, specialty: Optional[str] = None) -> Dict:
    # sourcery skip: extract-method
    """
    Find nearest hospitals and clinics using OpenStreetMap Overpass API.
    
    Args:
        location: City or area name
        specialty: Optional specialty (e.g., "emergency", "infectious disease")
        
    Returns:
        List of nearest hospitals with contact information
    """
    lat, lon = get_coords(location)
    if lat is None:
        return {
            "status": "error",
            "message": f"Could not find coordinates for: {location}"
        }
    
    try:
        # Use Overpass API to find hospitals
        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Search radius: 10km
        radius = 10000
        
        # Overpass QL query for hospitals and clinics
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          way["amenity"="hospital"](around:{radius},{lat},{lon});
          node["amenity"="clinic"](around:{radius},{lat},{lon});
          way["amenity"="clinic"](around:{radius},{lat},{lon});
          node["amenity"="doctors"](around:{radius},{lat},{lon});
        );
        out center;
        """
        
        response = requests.post(overpass_url, data={"data": query}, timeout=30)
        data = response.json()
        
        hospitals = []
        for element in data.get("elements", [])[:10]:  # Limit to 10 results
            tags = element.get("tags", {})
            
            # Get coordinates
            if element["type"] == "node":
                h_lat = element.get("lat")
                h_lon = element.get("lon")
            else:  # way
                h_lat = element.get("center", {}).get("lat")
                h_lon = element.get("center", {}).get("lon")
            
            # Calculate distance
            distance = calculate_distance(lat, lon, h_lat, h_lon)
            
            hospital_info = {
                "name": tags.get("name", "Unnamed Healthcare Facility"),
                "type": tags.get("amenity", "hospital"),
                "address": tags.get("addr:street", "") + " " + tags.get("addr:city", ""),
                "phone": tags.get("phone", "N/A"),
                "emergency": tags.get("emergency", "yes") == "yes",
                "website": tags.get("website", "N/A"),
                "coordinates": {"lat": h_lat, "lon": h_lon},
                "distance_km": round(distance, 2)
            }
            
            hospitals.append(hospital_info)
        
        # Sort by distance
        hospitals.sort(key=lambda x: x["distance_km"])
        
        return {
            "status": "success",
            "location": location,
            "search_coords": {"lat": lat, "lon": lon},
            "hospitals_found": len(hospitals),
            "nearest_hospitals": hospitals[:5],  # Top 5 nearest
            "search_radius_km": radius / 1000,
            "emergency_number": get_emergency_number(location)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error finding hospitals: {str(e)}"
        }


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def get_emergency_number(location: str) -> str:  # sourcery skip: use-next
    """Get emergency number based on location."""
    # Common emergency numbers by region
    emergency_numbers = {
        "default": "112 (International)",
        "US": "911",
        "UK": "999 or 112",
        "EU": "112",
        "India": "102 (Ambulance), 108 (Emergency)",
        "China": "120",
        "Japan": "119",
        "Australia": "000",
        "Singapore": "995",
        "UAE": "998 or 999"
    }
    
    # Simple location matching (can be enhanced)
    location_lower = location.lower()
    for country, number in emergency_numbers.items():
        if country.lower() in location_lower:
            return number
    
    return emergency_numbers["default"]
