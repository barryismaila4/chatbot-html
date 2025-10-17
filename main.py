from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI  # Importation de la classe OpenAI
import mysql.connector

# Configuration OpenAI avec la nouvelle clé API
client = OpenAI(api_key="api-key")
# Initialisation FastAPI
app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour développement local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion à MySQL
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "AA0556563a",
}

# Vérification et création de la base de données si nécessaire
def initialize_database():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS chatdb")
    cursor.close()
    connection.close()

    db = mysql.connector.connect(**db_config, database="chatdb")
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    cursor.close()
    db.close()

# Initialiser la base de données
initialize_database()

# Connexion persistante à la base
db = mysql.connector.connect(**db_config, database="chatdb")
cursor = db.cursor()

# Modèles de données
class Query(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str

@app.post("/ask", response_model=Answer)
async def ask_question(query: Query):
    try:
        # Appel à l'API OpenAI
        response = client.responses.create(
            model="gpt-5-nano",
            input=query.question,
            store=True
        )
        answer = response.output_text.strip()

        # Enregistrement dans la base de données
        cursor.execute(
            "INSERT INTO conversations (question, answer) VALUES (%s, %s)",
            (query.question, answer)
        )
        db.commit()

        return Answer(answer=answer)

    except Exception as e:
        print("🔥 ERREUR :", e)
        raise HTTPException(status_code=500, detail=str(e))