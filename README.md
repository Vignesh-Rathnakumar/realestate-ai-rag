# 🏠 Real Estate AI RAG System

An AI-powered **Document Question Answering System** that allows users to ask questions from real estate documents (PDFs) and get intelligent answers using **Azure OpenAI + Azure AI Search**.

---

## 🚀 Project Overview

This project implements a **Retrieval-Augmented Generation (RAG)** pipeline to extract meaningful insights from documents.

Users can:

* Upload documents (via backend ingestion)
* Ask natural language questions
* Get accurate, AI-generated answers based on document content

---

## ✨ Features

* 📄 **Document Processing**

  * Extracts text from PDFs using Azure Document Intelligence

* 🔍 **Semantic Search**

  * Uses Azure AI Search with vector embeddings

* 🤖 **AI-Powered Answers**

  * Uses Azure OpenAI (GPT) for intelligent responses

* 📊 **Confidence Scoring**

  * Provides confidence score based on retrieved data

* 🧠 **Multi-Document Support**

  * Works across multiple documents

* 💬 **ChatGPT-style UI**

  * Clean React + Tailwind frontend

---

## 🏗️ Architecture

```
User (Frontend - React)
        ↓
Azure Function API (Python)
        ↓
Azure AI Search (Vector DB)
        ↓
Azure OpenAI (LLM)
        ↓
Response → Frontend
```

---

## 🛠️ Tech Stack

### 🔹 Backend

* Python
* Azure Functions
* Azure Document Intelligence
* Azure AI Search
* Azure OpenAI

### 🔹 Frontend

* React.js
* Tailwind CSS

### 🔹 Tools

* Git & GitHub
* VS Code
* Postman / Curl

---

## 📁 Project Structure

```
realestate-ai-backend/
│
├── function_app.py        # Azure Function backend
├── host.json              # Azure config
├── requirements.txt       # Python dependencies
├── local.settings.json    # Environment variables (NOT pushed)
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 🔹 1. Clone Repository

```
git clone https://github.com/your-username/realestate-ai-rag.git
cd realestate-ai-rag
```

---

### 🔹 2. Backend Setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 🔹 3. Configure Environment Variables

Create `local.settings.json`:

```
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "OPENAI_KEY": "your-key",
    "OPENAI_ENDPOINT": "your-endpoint",
    "SEARCH_KEY": "your-key",
    "SEARCH_ENDPOINT": "your-endpoint"
  }
}
```

---

### 🔹 4. Run Backend

```
func start --cors http://localhost:3000
```

---

### 🔹 5. Frontend Setup

```
cd frontend
npm install
npm start
```

---

## 💡 How It Works

1. Documents are uploaded and processed into chunks
2. Each chunk is converted into embeddings
3. Stored in Azure AI Search
4. User asks a question
5. Relevant chunks are retrieved
6. OpenAI generates the final answer

---

## 🧪 Example Questions

* What is the policy number?
* Who is the insured?
* What is the insurance amount?
* Where is the property located?

---

## 🔒 Security

* API keys are stored locally (`local.settings.json`)
* Sensitive files are ignored via `.gitignore`
* No secrets are pushed to GitHub

---

## 📸 Screenshots

> Add screenshots of:

* Chat UI
* Response output
* Backend running

---

## 🚀 Future Improvements

* Upload PDF from frontend
* Chat history storage
* Multi-user support
* Deployment (Azure + Vercel)
* Better UI animations

---

## 👨‍💻 Author

**Vignesh Rathnakumar**

* 💼 Data Science Student
* 🔐 Interested in AI & Cybersecurity
* 🚀 Building real-world AI applications

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
