from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
import requests
import hashlib
from datetime import datetime, timedelta
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_API_KEY = os.getenv('HF_API_KEY')

if not HF_API_KEY:
    raise ValueError("HF_API_KEY environment variable is not set. Please create a .env file with your Hugging Face API key.")

headers = {"Authorization": f"Bearer {HF_API_KEY}"}

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

def query(payload):
    """Make API request with error handling"""
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Check if model is loading
        if isinstance(response.json(), list) and len(response.json()) > 0:
            return response.json()
        else:
            raise Exception("Model is still loading. Please try again in a few seconds.")
            
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Invalid response from API")
    except Exception as e:
        raise Exception(f"Error processing API response: {str(e)}")

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

def generate_paragraph_summary(text):
    output = query({
        "inputs": text,
        "parameters": {
            "max_length": 130,
            "min_length": 30,
            "do_sample": False
        }
    })
    return output[0]['summary_text']

def generate_two_paragraph_summary(text):
    # First paragraph - focus on main points
    first_output = query({
        "inputs": text,
        "parameters": {
            "max_length": 100,
            "min_length": 50,
            "do_sample": False
        }
    })
    first_para = first_output[0]['summary_text']
    
    # Second paragraph - focus on supporting details
    second_output = query({
        "inputs": text,
        "parameters": {
            "max_length": 100,
            "min_length": 50,
            "do_sample": True  # Use sampling to get different content
        }
    })
    second_para = second_output[0]['summary_text']
    
    return f"{first_para}\n\n{second_para}"

def generate_paragraph_bullet_summary(text):
    # Generate paragraph focusing on main points
    para_output = query({
        "inputs": text,
        "parameters": {
            "max_length": 100,
            "min_length": 50,
            "do_sample": False
        }
    })
    para_summary = para_output[0]['summary_text']
    
    # Generate bullet points focusing on key details
    bullet_output = query({
        "inputs": text,
        "parameters": {
            "max_length": 150,
            "min_length": 50,
            "do_sample": True  # Use sampling to get different content
        }
    })
    bullet_text = bullet_output[0]['summary_text']
    # Convert to bullet points and ensure they're different from paragraph
    bullet_points = []
    for point in bullet_text.split('.'):
        point = point.strip()
        if point and point not in para_summary:  # Only add points not in paragraph
            bullet_points.append('• ' + point)
    
    # If we don't have enough distinct bullet points, generate more
    if len(bullet_points) < 3:
        additional_output = query({
            "inputs": text,
            "parameters": {
                "max_length": 100,
                "min_length": 30,
                "do_sample": True
            }
        })
        additional_points = ['• ' + point.strip() for point in additional_output[0]['summary_text'].split('.') 
                           if point.strip() and point.strip() not in para_summary]
        bullet_points.extend(additional_points)
    
    return f"{para_summary}\n\n" + '\n'.join(bullet_points[:5])  # Limit to 5 bullet points

def generate_bullet_summary(text):
    output = query({
        "inputs": text,
        "parameters": {
            "max_length": 150,
            "min_length": 50,
            "do_sample": False
        }
    })
    bullet_text = output[0]['summary_text']
    bullet_points = ['• ' + point.strip() for point in bullet_text.split('.') if point.strip()]
    return '\n'.join(bullet_points[:5])  # Limit to 5 bullet points

if __name__ == '__main__':
    app.run(debug=True) 