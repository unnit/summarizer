# Text Summarizer

A Flask application that provides text summarization using Hugging Face's BART model.

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
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

## Environment Variables

- `HF_API_KEY`: Your Hugging Face API key (required)
  - Get it from: https://huggingface.co/settings/tokens
  - Never commit your actual API key to version control

## Security Notes

- The `.env` file is included in `.gitignore` to prevent accidental commits of sensitive information
- Always use environment variables for sensitive data
- Never share your API keys publicly

## Features

- Text summarization with different formats:
  - Single paragraph
  - Two paragraphs
  - Paragraph with bullet points
  - Bullet points only
- Rate limiting to prevent abuse
- Caching for improved performance
- Error handling and logging 