# 📝 Text Summarizer Web App

A Flask web application that allows users to extract summaries from:
- 🔤 Plain text
- 🌐 URLs (web pages)
- 📄 PDF files

Built using **spaCy** for NLP, **BeautifulSoup** for web scraping, and **PyPDF2** for PDF parsing.

---

## 🚀 Features

- 🧠 **Automatic Text Summarization** using word frequency-based extractive summarization
- 🌍 **URL Scraper**: Fetch and summarize textual content from any public web page
- 📁 **PDF Reader**: Upload a PDF and get a clean summary of its contents
- 📊 Displays input size, summary size, and compression ratio
- 📱 Simple and responsive HTML interface (no frontend framework needed)

---

## 📁 Project Structure
```bash
.
├── app.py               # Main Flask application
├── requirements.txt     # Project dependencies
└── README.md            # This documentation file

```

---

## 🧠 How It Works
- The app uses spaCy to:

- Tokenize input into words and sentences

- Remove stop words and punctuation

- Rank sentences based on word frequency

- Select top-ranked sentences as the summary

---

## ✅ Example Use Cases
- Summarizing long articles or research PDFs

- Quick analysis of web content

- Simplifying textual inputs for reports

---

## 📌 Notes
- File uploads are limited to 16 MB.

- Only .pdf files are accepted for upload.

- Uses a temporary folder for storing PDFs.

---

## 📦 Requirements

Install dependencies using pip:

```bash
pip install -r requirements.txt
```
---

## ▶️ Running the App


```bash
python app.py
```
- Then open your browser and navigate to: http://127.0.0.1:5000/


