# KuberAI Gold Investment Agent - 

This project is a sophisticated, multi-layered AI agent built to fulfill the requirements of the SimplifyMoney backend assignment. It emulates the KuberAI workflow for gold investments by providing two primary APIs: a conversational AI endpoint to assist users and a transactional endpoint to handle digital gold purchases.

The application is built with a focus on resilience, intelligence, and professional software design patterns.
---

## ✨ Core Features

### 👤 Normal User
- **Ask KuberAI**: Submit queries about gold prices, trends, and investment suggestions.  
- **Investment Nudges**: Receive actionable prompts to invest based on AI recommendations.  
- **View Transaction Summary**: Check completed digital gold purchases and grams owned.  
- **Fallback Handling**: Ensures responses even when live data is unavailable.  

### 👑 Admin / System
- **Transaction Logging**: Records all digital gold purchases securely in the database.  
- **Trend Analysis**: Generates 7-day and 30-day gold price trends for monitoring.  
- **Fallback Management**: Monitors data and AI service fallbacks, ensuring operational continuity.  
- **API Analytics**: View metrics such as the number of user queries and transactions.  

---

## 🛡️ Security & Reliability
- **Database Security**: MySQL with SQLAlchemy ORM.  
- **Environment Variables**: API keys and database credentials securely stored in `.env`.  
- **Error Handling**: Structured responses for API or database errors.  

---

## 🛠️ Tech Stack

| Category      | Technology / Library                   |
|---------------|--------------------------------------|
| Backend       | FastAPI                               |
| Database      | MySQL                                 |
| ORM           | SQLAlchemy                            |
| AI / LLM      | Google Gemini API (gemini-1.5-flash) |
| Live Data     | GoldApi.io                            |
| Deployment    | Python (Render) |

## 📂 Project Structure
```
KuberAI_Simulation/
├── app/
│   ├── __init__.py         # Marks the directory as a Python package
│   ├── main.py             # FastAPI app instance and route definitions
│   ├── models.py           # SQLAlchemy ORM models for Users and Transactions
│   ├── schemas.py          # Pydantic models for request and response validation
│   └── database.py         # Database connection, session creation, and Base
├── gold_data_backup.json   # Backup data for fallback in case live gold API fails
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── venv/                   # Python virtual environment
├── .gitignore              # Files and directories to ignore in git
└── Readme.md               # Project documentation
```

## 🛠️ Getting Started

### Prerequisites
- Python 3.8+
- Git

### Installation & Setup

1. Clone the repository:**
```bash
git clone <your-repo-url>
cd <project-directory>
```

2. Create and activate a virtual environment:
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Configure Environment Variables:
## Create a .env file in the root directory and add the following:
```
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GOLD_API_KEY="YOUR_GOLD_API_KEY"
DATABASE_URL="mysql+pymysql://user:password@host/dbname"
```
5. Start the FastAPI server:
```
uvicorn app.main:app --reload
The backend will be running at http://12-7.0.0.1:8000
Swagger UI for API documentation will be available at http://127.0.0.1:8000/docs
```

## 📋 API Endpoints

| Method | Endpoint       | Description                               | Access Control |
|--------|----------------|-------------------------------------------|----------------|
| POST   | /ask-kuber     | Conversational AI endpoint for user queries | Public         |
| POST   | /buy-gold      | Simulate a digital gold purchase           | Public         |


## 🔑 Key Functionalities
- Role-based query handling and transactional separation.  
- Users can get real-time gold prices and trend insights.  
- Transactional API securely records digital gold purchases.  
- Fallback mechanisms ensure continuity if Gold API or Gemini AI fails.  
- Structured AI responses with actionable suggestions.  
- On-the-fly calculation of 7-day and 30-day trends.  
- Error handling and logging for a smooth user experience.  

---

## 👤 Author
Jay Arya
   

