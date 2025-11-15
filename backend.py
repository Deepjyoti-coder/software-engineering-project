from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AayuCare POC API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️  Warning: GEMINI_API_KEY not found in .env file")
    print("Get your API key from: https://ai.google.dev/")
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured successfully")

# Configure Sarvam AI
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    print("⚠️  Warning: SARVAM_API_KEY not found in .env file")
    print("Get your API key from: https://www.sarvam.ai/")
else:
    print("✅ Sarvam API configured successfully")


# Request model
class SymptomRequest(BaseModel):
    input: str


# Root endpoint - serves the frontend
@app.get("/")
async def root():
    """Serve the frontend HTML file"""
    return FileResponse("index.html")


# Health check endpoint
@app.get("/api/health")
async def health():
    """Check if the API is running"""
    return {
        "status": "healthy",
        "message": "AayuCare POC API is running!",
        "gemini_configured": bool(GEMINI_API_KEY),
        "sarvam_configured": bool(SARVAM_API_KEY),
    }


# Speech to text endpoint using Sarvam AI
@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Convert speech to text using Sarvam AI
    Supports multiple Indian languages
    """

    if not SARVAM_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Sarvam API key not configured. Please add SARVAM_API_KEY to .env file",
        )

    try:
        # Read audio file
        audio_content = await audio.read()

        # Prepare request to Sarvam API
        url = "https://api.sarvam.ai/speech-to-text-translate"

        headers = {
            "api-subscription-key": SARVAM_API_KEY,
        }

        # Send audio file to Sarvam
        files = {
            "file": (audio.filename, audio_content, audio.content_type),
        }

        data = {
            "model": "saaras:v2",
            "prompt": "medical symptoms healthcare",
        }

        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Sarvam API error: {response.text}",
            )

        result = response.json()

        return {
            "success": True,
            "text": result.get("transcript", ""),
            "language": result.get("language_code", "en"),
        }

    except Exception as e:
        print(f"Speech to text error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to convert speech to text: {str(e)}"
        )


# Main endpoint - analyze symptoms and find doctors
@app.post("/api/find-doctor")
async def find_doctor(request: SymptomRequest):
    """
    Analyze symptoms using Google Gemini and recommend doctors

    This is a simplified version that:
    1. Uses Gemini to understand symptoms
    2. Recommends appropriate doctor type
    3. Suggests what to look for
    """

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Please add GEMINI_API_KEY to .env file",
        )

    try:
        # First, extract location and symptoms from the combined input
        extraction_prompt = f"""Extract the symptoms and location from the following user input.

User Input: {request.input}

Provide the response in this exact format:
SYMPTOMS: [extracted symptoms]
LOCATION: [extracted city name or "Mumbai" if not mentioned]
LATITUDE: [latitude of the location]
LONGITUDE: [longitude of the location]

If location is not mentioned, use Mumbai as default (19.0760, 72.8777)."""

        response1 = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=extraction_prompt,
        )
        extraction_text = response1.text

        # Parse extracted symptoms and location
        symptoms = "General symptoms"
        location = "Mumbai"
        latitude = 19.0760
        longitude = 72.8777

        for line in extraction_text.split("\n"):
            line = line.strip()
            if line.startswith("SYMPTOMS:"):
                symptoms = line.replace("SYMPTOMS:", "").strip()
            elif line.startswith("LOCATION:"):
                location = line.replace("LOCATION:", "").strip()
            elif line.startswith("LATITUDE:"):
                try:
                    latitude = float(line.replace("LATITUDE:", "").strip())
                except:
                    pass
            elif line.startswith("LONGITUDE:"):
                try:
                    longitude = float(line.replace("LONGITUDE:", "").strip())
                except:
                    pass

        # Now create the doctor recommendation prompt
        recommendation_prompt = f"""You are a helpful healthcare assistant for rural areas.

User Symptoms: {symptoms}
User Location: {location}

Please provide:
1. What type of doctor they should see (e.g., General Physician, Cardiologist, Dermatologist)
2. A brief, simple explanation (1-2 sentences)
3. What to tell the doctor when they visit

Keep it simple and in plain language. Don't give medical advice, just help them find the right doctor type.

Format your response as:
Doctor Type: [type]
Reason: [simple explanation]
What to mention: [key symptoms to tell doctor]
"""

        # Call Gemini API for recommendation
        response2 = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=recommendation_prompt,
        )

        # Parse response
        ai_response = response2.text

        # Extract doctor type (simple parsing)
        doctor_type = "General Physician"  # default
        if "cardiologist" in ai_response.lower():
            doctor_type = "Cardiologist"
        elif "dermatologist" in ai_response.lower():
            doctor_type = "Dermatologist"
        elif "orthopedic" in ai_response.lower():
            doctor_type = "Orthopedic"
        elif "neurologist" in ai_response.lower():
            doctor_type = "Neurologist"
        elif "ent" in ai_response.lower() or "ear" in ai_response.lower():
            doctor_type = "ENT Specialist"
        elif "pediatrician" in ai_response.lower():
            doctor_type = "Pediatrician"

        # Use Google Maps grounding to find real nearby doctors
        maps_prompt = f"Find the best {doctor_type} doctors or clinics near me. List top 5 options with their name, address, rating, and distance."

        maps_response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=maps_prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_maps=types.GoogleMaps())],
                tool_config=types.ToolConfig(
                    retrieval_config=types.RetrievalConfig(
                        lat_lng=types.LatLng(latitude=latitude, longitude=longitude)
                    )
                ),
            ),
        )

        # Extract nearby doctors from Google Maps grounding
        nearby_doctors = []

        if hasattr(maps_response, "candidates") and maps_response.candidates:
            candidate = maps_response.candidates[0]
            if (
                hasattr(candidate, "grounding_metadata")
                and candidate.grounding_metadata
            ):
                grounding = candidate.grounding_metadata
                if (
                    hasattr(grounding, "grounding_chunks")
                    and grounding.grounding_chunks
                ):
                    for chunk in grounding.grounding_chunks[:5]:  # Limit to top 5
                        if hasattr(chunk, "maps") and chunk.maps:
                            maps = chunk.maps
                            doctor_info = {
                                "name": (
                                    maps.title
                                    if hasattr(maps, "title")
                                    else "Medical Center"
                                ),
                                "address": location,  # Address is in the response text
                                "distance": "See Google Maps",
                                "rating": 4.5,  # Rating is in the response text
                                "open": "See Google Maps for hours",
                                "url": maps.uri if hasattr(maps, "uri") else "",
                            }
                            nearby_doctors.append(doctor_info)

        # Fallback to search link if no grounding data
        if not nearby_doctors:
            nearby_doctors = [
                {
                    "name": f"Search {doctor_type} in {location}",
                    "address": f"{location}",
                    "distance": "Click to search",
                    "rating": 0,
                    "open": "Search on Google Maps",
                    "url": f"https://www.google.com/maps/search/{doctor_type}+near+{location.replace(' ', '+')}",
                }
            ]

        return {
            "success": True,
            "doctor_type": doctor_type,
            "recommendation": ai_response,
            "location": location,
            "symptoms": symptoms,
            "nearby_doctors": nearby_doctors,
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze symptoms: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("\n🚀 Starting AayuCare POC Server...")
    print("📱 Open: http://localhost:8000")
    print("💡 Press Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
