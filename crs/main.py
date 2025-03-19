import os
import dotenv
import streamlit as st
from google import genai
import psycopg2  

# Configurar la página
def load_css():
    st.markdown("""
    <style>
    /* 📌 Fondo de la aplicación con diseño elegante */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to right, #E3FDFD, #FFE6FA);
        color: #333;
        font-family: 'Arial', sans-serif;
    }

    /* 📌 Estilos del título (ahora con color visible) */
    .title-container {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        color: #2C3E50;  /* Gris oscuro profesional */
        margin-bottom: 20px;
    }
    
    /* 📌 Contenedor del chat */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        max-width: 800px;
        margin: auto;
    }
    
    /* 📌 Mensajes del usuario */
    .user-message {
        background-color: #4A90E2;
        color: white;
        text-align: right;
        border-radius: 18px;
        padding: 12px;
        margin: 8px 0;
        font-size: 16px;
        font-weight: bold;
        max-width: 80%;
        display: inline-block;
    }

    /* 📌 Mensajes del asistente (gris claro elegante con sombra sutil) */
    .assistant-message {
        background-color: #F0F0F0;
        color: black;
        text-align: left;
        border-radius: 18px;
        padding: 12px;
        margin: 8px 0;
        font-size: 16px;
        font-weight: 600; /* Un poco menos bold para más elegancia */
        max-width: 80%;
        display: inline-block;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Sombra ligera */
    }

    /* 📌 Efecto hover en los mensajes */
    .user-message:hover, .assistant-message:hover {
        opacity: 0.9;
        transform: scale(1.02);
        transition: 0.3s;
    }

    /* 📌 Estilo del input del chat */
    [data-testid="stChatInput"] {
        background-color: white;
        border: 2px solid #4A90E2;
        border-radius: 10px;
        font-size: 16px;
        padding: 10px;
    }

    /* 📌 Botón de enviar con diseño moderno */
    button {
        background-color: #4A90E2;
        color: white;
        border-radius: 8px;
        font-size: 16px;
        padding: 10px 15px;
        transition: 0.3s;
    }

    button:hover {
        background-color: #357ABD;
        transform: scale(1.05);
    }

    </style>
    """, unsafe_allow_html=True)


load_css()

# Cargar la clave API
dotenv.load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("Error: No se encontró la clave de API en el archivo .env")
    st.stop()

# Inicializar el cliente de Gemini
client = genai.Client(api_key=API_KEY)

# Conexión a PostgreSQL
DB_HOST = "localhost"
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = "5434"

def get_db_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Guardar mensajes en PostgreSQL
def save_chat_to_db(user_message, gemini_response):
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_history (user_message, gemini_response) VALUES (%s, %s)",
                (user_message, gemini_response)
            )
            conn.commit()
        conn.close()

def main():
    # Selección del modelo
    model_options = ["gemini-2.0-flash"]
    selected_model = st.selectbox("Selecciona un modelo de Gemini:", model_options)

    # Configurar historial de conversación
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Encabezado
    st.markdown("<h1 style='text-align: center; color: #5D6D7E;'>💬 Chat con Gemini</h1>", unsafe_allow_html=True)

    # Contenedor de mensajes con estilo
    message_container = st.container()

    # Mostrar historial de conversación
    for message in st.session_state.messages:
        avatar = "🤖" if message["role"] == "assistant" else "😎"
        role_class = "assistant-message" if message["role"] == "assistant" else "user-message"
        
        st.markdown(f"""
        <div class="{role_class}">
            <strong>{avatar}</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)

    # Input de usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        try:
            # Mostrar mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.markdown(f'<div class="user-message"><strong>😎</strong> {prompt}</div>', unsafe_allow_html=True)

            # Respuesta de Gemini
            with st.spinner("Gemini está pensando..."):
                response = client.models.generate_content(
                    model=selected_model,
                    contents=[prompt]
                )

            st.markdown(f'<div class="assistant-message"><strong>🤖</strong> {response.text}</div>', unsafe_allow_html=True)
            
            # Guardar respuesta en el historial
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Guardar en la base de datos
            save_chat_to_db(prompt, response.text)
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
