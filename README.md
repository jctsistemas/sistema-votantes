# 🗳️ Sistema de Registro de Visitas

Aplicación web desarrollada en **Flask** que permite registrar visitas por índice, adjuntar fotos, geolocalización, historial personal y administración de galerías.

## 🚀 Funcionalidades

- ✅ Registro de visitas por índice
- 📷 Carga de fotos por visita
- 📍 Geolocalización automática
- 📋 Historial personal con fotos
- 🖼️ Visor de fotos navegable
- 📦 Descarga de fotos como ZIP
- 📤 Compartir galería por WhatsApp
- 🔐 Sistema de login con roles
- 🧑‍💻 Panel de administración

## 🧰 Tecnologías usadas

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS (estilo iOS), JavaScript
- **Base de datos**: MySQL
- **Estilo**: Diseño responsive, tipo iOS

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/sistema-votantes.git

# Entrar al proyecto
cd sistema-votantes

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos (ver config.py)
# Ejecutar
python app.py
