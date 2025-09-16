from flask_login import UserMixin

class Usuario(UserMixin):
    def __init__(self, id, nombre_usuario, nombre_completo, email, activo):
        self.id = id
        self.nombre_usuario = nombre_usuario
        self.nombre_completo = nombre_completo
        self.email = email
        self.activo = activo
        self.roles = []  # se llenará después
