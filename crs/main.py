import os
import dotenv
import streamlit as st
from google import genai

# Configurar la página
st.set_page_config(
    page_title="Chat con Gemini",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Inyectar CSS personalizado
def load_css():
    # Ruta absoluta al archivo styles.css
    css_path = "/home/gonzapython/Escritorio/probando_ia/styles.css"
    
    try:
        with open(css_path, "r") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: No se pudo encontrar el archivo 'styles.css' en {css_path}")
        st.stop()

load_css()  # Llamar la función al inicio del script


# Cargar la clave API desde el archivo .env
dotenv.load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("Error: No se encontró la clave de API en el archivo .env")
    st.stop()

# Inicializar el cliente de Gemini
client = genai.Client(api_key=API_KEY)

# Lista de modelos disponibles
model_options = ["gemini-2.0-flash"]  # Se pueden agregar más variantes en el futuro

def main():
    # Selección del modelo
    selected_model = st.selectbox("Selecciona un modelo de Gemini:", model_options)
    
    # Configurar historial de conversación
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Encabezado
    st.subheader("💬 Chat con Gemini", divider="blue", anchor=False)
    
    # Contenedor de mensajes
    message_container = st.container(height=500, border=True)
    
    # Mostrar historial de conversación
    for message in st.session_state.messages:
        avatar = "🤖" if message["role"] == "assistant" else "😎"
        with message_container.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    
    # Input de usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        try:
            # Agregar entrada del usuario al historial
            st.session_state.messages.append({"role": "user", "content": prompt})
            message_container.chat_message("user", avatar="😎").markdown(prompt)
    
            with message_container.chat_message("assistant", avatar="🤖"):
                with st.spinner("Gemini está pensando..."):
                    response = client.models.generate_content(
                        model=selected_model,
                        contents=[prompt]  # Corregido: ahora es una lista de strings
                    )
                    st.markdown(response.text)
            
            # Agregar respuesta de Gemini al historial
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}", icon="⛔️")

if __name__ == "__main__":
    main()

