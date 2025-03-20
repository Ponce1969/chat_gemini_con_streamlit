import os
import dotenv
import streamlit as st
from google import genai 
import psycopg2  
import csv

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
    import os
    # Obtener la ruta absoluta al directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_file = os.path.join(current_dir, "styles.css")
    
    with open(css_file, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def get_chat_history(limit=5):
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_message, gemini_response FROM chat_history ORDER BY id DESC LIMIT %s", (limit,))
            return cursor.fetchall()
    return []

def generate_csv():
    chat_history = get_chat_history()
    csv_filename = "chat_history.csv"
    
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Usuario", "Gemini"])  # Encabezados
        for user_message, gemini_response in chat_history:
            writer.writerow([user_message, gemini_response])
    
    return csv_filename

def delete_chat_history():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM chat_history")
            conn.commit()
        conn.close()

# Llamamos a la función para aplicar los estilos
load_css()

def main():
    # Selección del modelo
    st.markdown('<p class="selectbox-label">Selecciona un modelo de Gemini:</p>', unsafe_allow_html=True)
    model_options = ["gemini-2.0-flash"]
    selected_model = st.selectbox(" ", model_options)

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
            
            # Procesar la respuesta para mejorar la visualización del código
            response_text = response.text
            
            # Función para formatear el código y asegurar que no sobrepase el contenedor
            def format_code_blocks(text):
                import re
                
                # Detectar bloques de código (entre ```)
                code_block_pattern = r'```([\w]*)[\n]([\s\S]*?)```'
                
                def process_code_block(match):
                    lang = match.group(1) or ''
                    code = match.group(2)
                    
                    # Procesar cada línea para asegurar que no sobrepase el ancho
                    lines = code.split('\n')
                    processed_lines = []
                    
                    for line in lines:
                        # Si la línea es muy larga, la dividimos
                        if len(line) > 80:  # Limitar a 80 caracteres por línea
                            # Dividir la línea en segmentos de 80 caracteres máximo
                            # pero respetando palabras completas cuando sea posible
                            current_line = ''
                            words = line.split(' ')
                            
                            for word in words:
                                if len(current_line) + len(word) + 1 <= 80:  # +1 por el espacio
                                    current_line += ('' if not current_line else ' ') + word
                                else:
                                    processed_lines.append(current_line)
                                    current_line = word
                            
                            if current_line:  # Añadir la última línea
                                processed_lines.append(current_line)
                        else:
                            processed_lines.append(line)
                    
                    formatted_code = '\n'.join(processed_lines)
                    return f'```{lang}\n{formatted_code}```'
                
                # Reemplazar todos los bloques de código con versiones formateadas
                formatted_text = re.sub(code_block_pattern, process_code_block, text)
                return formatted_text
            
            # Formatear la respuesta para que el código no sobrepase el contenedor
            formatted_response = format_code_blocks(response_text)
            
            # Mostrar la respuesta con formato mejorado
            st.markdown(
                f'<div class="assistant-message"><strong>🤖</strong> {formatted_response}</div>',
                unsafe_allow_html=True
            )
            
            # Guardar respuesta en el historial
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Guardar en la base de datos
            save_chat_to_db(prompt, response_text)
        except Exception as e:
            st.error(f"Error: {e}")

    # Sección de botones para CSV y eliminación
    st.markdown("<h2>Opciones de Historial</h2>", unsafe_allow_html=True)
    if st.button("Generar CSV del historial"):
        csv_file = generate_csv()
        st.success(f"CSV generado: {csv_file}")
        st.download_button(label="Descargar CSV", data=open(csv_file, "rb"), file_name=csv_file, mime="text/csv")

    if st.button("Eliminar historial de chat"):
        delete_chat_history()  # Llamar a la función para eliminar los registros
        st.success("Historial de chat eliminado.")

if __name__ == "__main__":
    main()