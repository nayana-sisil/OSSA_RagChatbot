# OSSA AI Tutor - Retrieval-Augmented Generation System

A production-ready AI teaching assistant designed for the university module OSSA (Operating Systems and System Architecture). This system utilizes Retrieval-Augmented Generation (RAG) to provide academically grounded support based exclusively on provided lecture materials.

## Project Overview

The OSSA AI Tutor helps students understand complex operating system concepts by interacting with their specific course materials. Unlike general-purpose AI, this system is strictly grounded in the OSSA curriculum, providing verified answers with source citations from lecture PDFs.

## Key Features

- Dual-Mode Learning: Switch between Learning Mode for detailed explanations and analogies, and Exam Mode for concise revision notes.
- Academic Grounding: Powered by LlamaIndex and Google Gemini, ensuring all responses are derived from the pre-populated data folder.
- Source Attribution: Every response includes specific PDF filenames and page numbers for verified study.
- Conversational Memory: Maintains context across messages to support follow-up questions and iterative learning.
- Modern Interface: A clean, dark-mode web interface with typing animations and responsive design.

## Technical Stack

- Backend: Python 3.11, FastAPI, LlamaIndex, FAISS, Google Gemini API.
- Frontend: HTML5, CSS3, Vanilla JavaScript.
- Indexing: Sentence-based chunking with semantic vector search via gemini-embedding-001.

## Supported Document Types

The system currently focuses on PDF processing, which is ideal for university lecture slides and handouts. All documents placed in the `backend/data/` directory will be processed into semantic nodes for the RAG pipeline.

## Repository Structure

- backend/: Contains the FastAPI server, LlamaIndex RAG engine, and document processing logic.
- backend/data/: Directory for storing lecture PDFs.
- backend/vector_db/: Local storage for the FAISS vector index.
- frontend/: Contains the web interface assets (HTML, CSS, JavaScript).

## Local Setup Instructions

### 1. Backend Configuration

Navigate to the backend directory:
cd backend

Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

Install the required dependencies:
pip install -r requirements.txt

Configure the environment variables:
Create a file named .env in the backend folder and add your Google Gemini API key:
GOOGLE_API_KEY=your_actual_api_key_here

Add your lecture materials:
Place your OSSA lecture PDFs inside the backend/data/ folder.

Start the backend server:
python main.py

### 2. Frontend Access

Open the frontend/index.html file in any modern web browser to begin your study session.

## Important Information for Contributors

- The first time the system runs, it will index the documents in the background. Due to free-tier API limits, this may take some time.
- The system uses a local FAISS index. Once indexing is complete, the vector_db folder will store the knowledge base permanently for instant loading on subsequent runs.
- Do not commit your .env file or the contents of vector_db to version control.

## Deployment Notes

### Backend (Render)
- Connect your repository and set the root directory to backend.
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
- Add GOOGLE_API_KEY to the environment variables.

### Frontend (Vercel)
- Connect your repository and deploy the frontend folder.
- Update the API_URL in frontend/script.js to your deployed backend address.

## Academic Integrity
This application is intended as a supplementary study aid. Students should always consult their official module handbook and lecturers for definitive academic guidance.
