# AayuCare POC - Healthcare AI with Google Maps Grounding

A minimal healthcare application that uses **Google Gemini AI**, **Google Maps Grounding**, and **Sarvam AI** to help users find the right doctors based on their symptoms.

## ✨ Features

- 🎤 **Multi-language Speech-to-Text** using Sarvam AI
- 🤖 **AI-powered Symptom Analysis** with Google Gemini
- 🗺️ **Real Doctor Locations** via Google Maps Grounding (no mock data!)
- 🎨 **Minimalistic UI** with clean, modern design
- 📱 **Single Input Field** for symptoms and location

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API Key ([Get it here](https://ai.google.dev/))
- Sarvam AI API Key ([Get it here](https://dashboard.sarvam.ai/speech-to-text?utm_source=Vinayak%20Worksghops&utm_medium=social&utm_campaign=adoption))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vinayakgavariya/Hands-on-with-Google-Maps-Grounding-Sarvam-AI.git
cd Hands-on-with-Google-Maps-Grounding-Sarvam-AI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
```

4. Run the server:
```bash
python backend.py
```

5. Open your browser and visit:
```
http://localhost:8000
```

## 🎯 How to Use

1. **Type or Speak** your symptoms and location in one field
   - Example: "I have chest pain and breathing difficulty in Mumbai"
   
2. **Click the microphone button** 🎤 to use voice input (supports Hindi, English, and other Indian languages)

3. **Get Results** - AI analyzes your symptoms and shows:
   - Recommended doctor type
   - Real nearby doctors with Google Maps links
   - Ratings and contact information

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **AI**: Google Gemini 2.0 Flash
- **Maps**: Google Maps Grounding
- **Speech-to-Text**: Sarvam AI (Saaras v2)
- **Frontend**: Vanilla JavaScript with minimalistic CSS

## 📝 API Endpoints

- `GET /` - Serves the frontend
- `GET /api/health` - Health check
- `POST /api/speech-to-text` - Convert audio to text
- `POST /api/find-doctor` - Analyze symptoms and find doctors

## 🎨 Design

Minimalistic design with:
- Peachy cream background (#fff7f3)
- Clean typography
- Subtle borders and shadows
- Simple, intuitive interactions

## 📄 License

MIT License

## 🙏 Acknowledgments

- Google Gemini AI for symptom analysis
- Google Maps for location services
- Sarvam AI for multi-language speech recognition

