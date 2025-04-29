from flask import Flask, request, render_template_string
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import PyPDF2
import os
from werkzeug.utils import secure_filename
import tempfile


# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()  # Use temporary directory for uploads

def scrape_text_from_url(url):
    """
    Scrape text content from a given URL.
    
    Args:
        url (str): The URL of the webpage to scrape
        
    Returns:
        str: The extracted text content from the webpage
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")

        # Send GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Remove blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): The path to the PDF file
        
    Returns:
        str: The extracted text content from the PDF
    """
    try:
        # Check if file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} does not exist")
            
        # Check if file is a PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("The file must be a PDF")

        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            text = ""
            for page_num in range(num_pages):
                # Get the page
                page = pdf_reader.pages[page_num]
                # Extract text from the page
                text += page.extract_text() + "\n\n"
            
            return text.strip()

    except PyPDF2.PdfReadError as e:
        print(f"Error reading PDF: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

class TextSummarizer:
    def __init__(self, model_name='en_core_web_sm'):
        self.nlp = spacy.load(model_name)
        self.stopwords = STOP_WORDS
        self.punctuations = punctuation
        
    def summarize(self, text, ratio=0.3):
        doc = self.nlp(text)
        word_frequencies = {}
        for word in doc:
            if word.text.lower() not in self.stopwords and word.text.lower() not in self.punctuations:
                if word.text.lower() not in word_frequencies.keys():
                    word_frequencies[word.text.lower()] = 1
                else:
                    word_frequencies[word.text.lower()] += 1

        max_freq = max(word_frequencies.values(), default=1)
        for word in word_frequencies:
            word_frequencies[word] = word_frequencies[word] / max_freq

        sentence_scores = {}
        for sent in doc.sents:
            for word in sent:
                if word.text.lower() in word_frequencies:
                    if sent not in sentence_scores:
                        sentence_scores[sent] = word_frequencies[word.text.lower()]
                    else:
                        sentence_scores[sent] += word_frequencies[word.text.lower()]

        select_length = int(len(list(doc.sents)) * ratio)
        summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)

        return ' '.join([str(s) for s in summary])


summarizer = TextSummarizer()

# Simple HTML interface
HTML_TEMPLATE = '''
<!doctype html>
<html>
    <head>
        <title>Text Summarizer</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px;
                line-height: 1.6;
                color: #333;
                background-color: #f5f5f5;
            }
            h2, h3 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .form-group {
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 6px;
                border-left: 4px solid #3498db;
            }
            textarea, input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            textarea:focus, input[type="text"]:focus {
                border-color: #3498db;
                outline: none;
                box-shadow: 0 0 5px rgba(52, 152, 219, 0.3);
            }
            textarea {
                min-height: 150px;
                resize: vertical;
            }
            .btn {
                background-color: #3498db;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background-color: #2980b9;
            }
            .error {
                color: #e74c3c;
                font-weight: bold;
                padding: 10px;
                background-color: #fadbd8;
                border-radius: 4px;
                margin: 10px 0;
            }
            .summary {
                background-color: #f9f9f9;
                padding: 25px;
                border-radius: 6px;
                margin-top: 30px;
                border-left: 4px solid #2ecc71;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .summary h3 {
                color: #2ecc71;
                margin-top: 0;
            }
            .summary p {
                font-size: 18px;
                line-height: 1.8;
                text-align: justify;
                margin-bottom: 20px;
            }
            .stats {
                margin-top: 20px;
                font-size: 0.9em;
                color: #7f8c8d;
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
            }
            .stat-item {
                background-color: #ecf0f1;
                padding: 10px 15px;
                border-radius: 4px;
                flex: 1;
                min-width: 200px;
            }
            .stat-item strong {
                color: #2c3e50;
            }
            input[type="file"] {
                padding: 10px 0;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .header p {
                color: #7f8c8d;
                font-size: 18px;
            }
            .options-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }
            .option-card {
                flex: 1;
                min-width: 300px;
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .option-card h3 {
                color: #3498db;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 0;
            }
            @media (max-width: 768px) {
                .container {
                    padding: 15px;
                }
                .form-group {
                    padding: 15px;
                }
                .summary {
                    padding: 15px;
                }
            }
        </style>
        <script>
            // Function to scroll to the summary section
            function scrollToSummary() {
                const summaryElement = document.getElementById('summary-section');
                if (summaryElement) {
                    summaryElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
            
            // Add event listeners to all forms
            document.addEventListener('DOMContentLoaded', function() {
                const forms = document.querySelectorAll('form');
                forms.forEach(form => {
                    form.addEventListener('submit', function() {
                        // Store the form submission in sessionStorage
                        sessionStorage.setItem('scrollToSummary', 'true');
                    });
                });
                
                // Check if we should scroll to summary (after page reload)
                if (sessionStorage.getItem('scrollToSummary') === 'true') {
                    // Clear the flag
                    sessionStorage.removeItem('scrollToSummary');
                    // Wait a bit for the page to fully load and render
                    setTimeout(scrollToSummary, 500);
                }
            });
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Text Summarizer</h1>
                <p>Extract key information from text, web pages, or PDF files</p>
            </div>
            
            <div class="options-container">
                <div class="option-card">
                    <h3>Option 1: Enter text directly</h3>
                    <form method="POST" action="/summarize-text">
                        <textarea name="text" placeholder="Enter your text here...">{{ request.form.text or '' }}</textarea><br><br>
                        <input type="submit" value="Summarize Text" class="btn">
                    </form>
                </div>
                
                <div class="option-card">
                    <h3>Option 2: Enter a URL</h3>
                    <form method="POST" action="/summarize-url">
                        <input type="text" name="url" placeholder="https://example.com" value="{{ request.form.url or '' }}"><br><br>
                        <input type="submit" value="Scrape and Summarize" class="btn">
                    </form>
                </div>
                
                <div class="option-card">
                    <h3>Option 3: Upload a PDF</h3>
                    <form method="POST" action="/summarize-pdf" enctype="multipart/form-data">
                        <input type="file" name="pdf_file" accept=".pdf"><br><br>
                        <input type="submit" value="Upload and Summarize" class="btn">
                    </form>
                </div>
            </div>
            
            {% if error %}
            <p class="error"><strong>Error:</strong> {{ error }}</p>
            {% endif %}
            
            {% if summary %}
            <div id="summary-section" class="summary">
                <h3>Summary</h3>
                <p>{{ summary }}</p>
                <div class="stats">
                    <div class="stat-item">
                        <strong>Input Length:</strong> {{ input_length }} characters
                    </div>
                    <div class="stat-item">
                        <strong>Summary Length:</strong> {{ summary_length }} characters
                    </div>
                    <div class="stat-item">
                        <strong>Compression Ratio:</strong> {{ compression_ratio }}%
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </body>
</html>
'''


@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/summarize-text', methods=['POST'])
def summarize_text():
    summary = ""
    input_length = 0
    summary_length = 0
    compression_ratio = 0
    error = ""
    
    text = request.form['text']
    if text.strip():
        try:
            summary = summarizer.summarize(text)
            input_length = len(text)
            summary_length = len(summary)
            compression_ratio = round((1 - summary_length / input_length) * 100, 2) if input_length > 0 else 0
        except Exception as e:
            error = f"Error summarizing text: {str(e)}"
    else:
        error = "Please enter some text to summarize"
        
    return render_template_string(HTML_TEMPLATE, 
                                 summary=summary, 
                                 input_length=input_length, 
                                 summary_length=summary_length,
                                 compression_ratio=compression_ratio,
                                 error=error)

@app.route('/summarize-url', methods=['POST'])
def summarize_url():
    summary = ""
    input_length = 0
    summary_length = 0
    compression_ratio = 0
    error = ""
    
    url = request.form['url']
    if url.strip():
        try:
            # Scrape text from URL
            scraped_text = scrape_text_from_url(url)
            
            if scraped_text:
                # Summarize the scraped text
                summary = summarizer.summarize(scraped_text)
                input_length = len(scraped_text)
                summary_length = len(summary)
                compression_ratio = round((1 - summary_length / input_length) * 100, 2) if input_length > 0 else 0
            else:
                error = "Failed to scrape text from the URL. Please check the URL and try again."
        except Exception as e:
            error = f"Error processing URL: {str(e)}"
    else:
        error = "Please enter a URL to scrape"
        
    return render_template_string(HTML_TEMPLATE, 
                                 summary=summary, 
                                 input_length=input_length, 
                                 summary_length=summary_length,
                                 compression_ratio=compression_ratio,
                                 error=error)

@app.route('/summarize-pdf', methods=['POST'])
def summarize_pdf():
    summary = ""
    input_length = 0
    summary_length = 0
    compression_ratio = 0
    error = ""
    
    # Check if a file was uploaded
    if 'pdf_file' not in request.files:
        error = "No file uploaded"
        return render_template_string(HTML_TEMPLATE, error=error)
    
    file = request.files['pdf_file']
    
    # Check if a file was selected
    if file.filename == '':
        error = "No file selected"
        return render_template_string(HTML_TEMPLATE, error=error)
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        error = "The uploaded file must be a PDF"
        return render_template_string(HTML_TEMPLATE, error=error)
    
    try:
        # Save the uploaded file to a temporary location
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(filepath)
        
        # Clean up the temporary file
        try:
            os.remove(filepath)
        except:
            pass  # Ignore errors during cleanup
        
        if extracted_text:
            # Summarize the extracted text
            summary = summarizer.summarize(extracted_text)
            input_length = len(extracted_text)
            summary_length = len(summary)
            compression_ratio = round((1 - summary_length / input_length) * 100, 2) if input_length > 0 else 0
        else:
            error = "Failed to extract text from the PDF. The file might be corrupted or password-protected."
    except Exception as e:
        error = f"Error processing PDF: {str(e)}"
        
    return render_template_string(HTML_TEMPLATE, 
                                 summary=summary, 
                                 input_length=input_length, 
                                 summary_length=summary_length,
                                 compression_ratio=compression_ratio,
                                 error=error)

if __name__ == '__main__':
    app.run(debug=True)

    