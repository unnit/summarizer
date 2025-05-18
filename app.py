from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, timedelta
import hashlib
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize rate limiter with in-memory storage (for development)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please create a .env file with your Gemini API key.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

# In-memory cache with expiration
cache = {}
CACHE_EXPIRATION = timedelta(hours=1)

def get_cache_key(text, summary_type):
    """Generate a unique cache key for the text and summary type"""
    return hashlib.md5(f"{text}_{summary_type}".encode()).hexdigest()

def get_cached_summary(text, summary_type):
    """Get summary from cache if it exists and hasn't expired"""
    cache_key = get_cache_key(text, summary_type)
    if cache_key in cache:
        cached_data = cache[cache_key]
        if datetime.now() - cached_data['timestamp'] < CACHE_EXPIRATION:
            return cached_data['summary']
    return None

def cache_summary(text, summary_type, summary):
    """Cache the summary with timestamp"""
    cache_key = get_cache_key(text, summary_type)
    cache[cache_key] = {
        'summary': summary,
        'timestamp': datetime.now()
    }

def generate_summary(text, prompt):
    """Generate summary using Gemini API"""
    try:
        response = model.generate_content(prompt + "\n\nText to summarize:\n" + text)
        return response.text
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")

def generate_paragraph_summary(text):
    prompt = """Summarize the following large text into a well-structured paragraph. 
    Focus on the main points and key information. 
    Make it concise but comprehensive. 
    Use clear and professional language."""
    return generate_summary(text, prompt)

def generate_two_paragraph_summary(text):
    prompt = """Summarize the following large text into two well-structured paragraphs.
    First paragraph should focus on the main points and key information.
    Second paragraph should cover supporting details and additional context.
    Use clear and professional language."""
    return generate_summary(text, prompt)

def generate_paragraph_bullet_summary(text):
    prompt = """Summarize the following large text into a small well-structured paragraph and 3 bullet points.
    The paragraph should cover the main points and key information.
    The bullet points should highlight specific details or important aspects.
    Use clear and professional language.
    Format the output as:
    [Paragraph text]

    • [First bullet point]
    • [Second bullet point]
    • [Third bullet point]"""
    return generate_summary(text, prompt)

def generate_bullet_summary(text):
    prompt = """Summarize the following large text into a maximum of 15 bullet points.
    Focus on the most important information and key details.
    Each bullet point should be concise but informative.
    Use clear and professional language.
    The number of bullet points should be according to the length of the text and should cover all the important information.
    Format each point with a bullet point (•) symbol."""
    return generate_summary(text, prompt)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
@limiter.limit("10 per minute")
def summarize_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        summary_type = data.get('type', 'paragraph')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Check cache first
        cached_summary = get_cached_summary(text, summary_type)
        if cached_summary:
            return jsonify({
                'summary': cached_summary,
                'type': summary_type,
                'cached': True
            })
            
        # Generate summary based on type
        if summary_type == 'paragraph':
            summary = generate_paragraph_summary(text)
        elif summary_type == 'two_paragraph':
            summary = generate_two_paragraph_summary(text)
        elif summary_type == 'paragraph_bullet':
            summary = generate_paragraph_bullet_summary(text)
        elif summary_type == 'bullet':
            summary = generate_bullet_summary(text)
        else:
            return jsonify({'error': 'Invalid summary type'}), 400
            
        # Cache the result
        cache_summary(text, summary_type, summary)
            
        return jsonify({
            'summary': summary,
            'type': summary_type,
            'cached': False
        })
        
    except Exception as e:
        app.logger.error(f"Error in summarize_text: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 