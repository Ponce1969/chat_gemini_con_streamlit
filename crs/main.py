import os
import dotenv
import streamlit as st
from google import genai 
import psycopg2  



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

def load_css():
    """Carga el CSS desde el archivo externo styles.css."""
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Llamamos a la función para aplicar los estilos
load_css()

def main():
    # Selección del modelo
    st.markdown('<p class="selectbox-label">Selecciona un modelo de Gemini:</p>', unsafe_allow_html=True)
    model_options = ["gemini-2.0-flash"]
    selected_model = st.selectbox(" ",model_options)

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
