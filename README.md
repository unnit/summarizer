# Text Summarizer

A Flask application that provides text summarization using Hugging Face's BART model.

## Setup

### Option 1: Virtual Environment (Development)

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Set up virtual environment:
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Set up environment variables:
   - Create a `.env` file in the project root directory
   - Add your Hugging Face API key:
   ```
   HF_API_KEY=your_api_key_here
   ```
   - You can get your API key from [Hugging Face Settings](https://huggingface.co/settings/tokens)

4. Run the application:
```bash
python app.py
```

### Option 2: Docker (Production)

1. Build and run with Docker Compose:
```bash
# Build and start the container
docker-compose up --build

# To run in detached mode
docker-compose up -d
```

2. Stop the container:
```bash
docker-compose down
```

## Environment Variables

- `HF_API_KEY`: Your Hugging Face API key (required)
  - Get it from: https://huggingface.co/settings/tokens
  - Never commit your actual API key to version control

## Security Notes

- The `.env` file is included in `.gitignore` to prevent accidental commits of sensitive information
- Always use environment variables for sensitive data
- Never share your API keys publicly
- The Docker setup uses a non-root user for security

## Features

- Text summarization with different formats:
  - Single paragraph
  - Two paragraphs
  - Paragraph with bullet points
  - Bullet points only
- Rate limiting to prevent abuse
- Caching for improved performance
- Error handling and logging

## Development

- Virtual environment for isolated development
- Docker for consistent deployment
- Automatic restart on code changes (Docker)
- Volume mounting for live code updates 