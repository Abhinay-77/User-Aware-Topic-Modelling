# User-Aware Topic Modeling on Transliteration-Based Telugu Text using BERTopic

## 🚀 Project Overview
This project presents a comprehensive full-stack application for **User-Aware Topic Modeling (UATM)** specifically designed for code-mixed and transliterated Telugu text (Tanglish). The system addresses the challenges of orthographic variability in social media text by integrating a three-tier normalization pipeline with neural topic modeling and temporal drift detection.

### 🌟 Key Features
- 🔄 **Three-Tier Normalization Pipeline** - Lexical cleaning, phonetic grouping (Soundex/Metaphone), and contextual disambiguation using intelligent language models.
- 🏷️ **Neural Topic Modeling** - BERTopic-powered thematic extraction using multilingual sentence transformers for high-coherence topics.
- 📈 **User-Aware Analytics** - Personalized tracking of user interests using Shannon Entropy (diversity) and Jensen-Shannon Divergence (temporal drift).
- 📊 **Role-Based Dashboards** - Customized analytics views for General Users and Researchers/Administrators.
- 🔐 **Secure Authentication** - JWT-based session management with encrypted password storage.
- 📄 **Automated Documentation** - Includes a complete, professional 40+ page academic project report.

## 🏗️ Project Architecture

### Backend
- **Framework**: FastAPI (Python 3.11)
- **NLP Engine**: BERTopic, HuggingFace Transformers, mBERT
- **Database**: Relational storage for users, posts, and analytics
- **Authentication**: JWT with role-based access control

### Frontend
- **Framework**: React 18 with Vite
- **Visualizations**: Recharts for interactive behavioral charts
- **Styling**: Tailwind CSS for a modern, responsive UI

## 📁 Project Structure

```
User-Aware-Topic-Modelling-main/
├── backend/
│   ├── auth/                # JWT and Password handling
│   ├── baselines/           # Baseline models (LDA)
│   ├── dashboards/          # Analytics and dashboard routes
│   ├── database/            # Connection and ORM models
│   ├── nlp/                 # Tanglish converter & pipeline
│   ├── topic_modeling/      # BERTopic service logic
│   ├── translation/         # Translation services
│   └── main.py              # Application entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Role-specific dashboards
│   │   ├── services/        # API communication layer
│   │   └── App.jsx          # Main application routing
│   ├── index.html
│   └── package.json
├── data/                    # Sample datasets and uploads
├── models/                  # Persistent model storage
├── Major Project documnetation.docx  # Full-length academic documentation
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 📚 Documentation
The project includes a comprehensive 65 page documentation file: [Major Project documnetation.docx](Major Project documentation.docx). This report covers the literature survey, system design, methodology, implementation, and detailed results of the normalization and topic modeling components.

## 📜 License
This project is developed as part of the Final Year Project requirements at CVR College of Engineering.
