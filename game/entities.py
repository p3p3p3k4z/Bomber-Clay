import time
import random

class Jugador:
    def __init__(self, id, x, y, color):
        self.id = id
        self.x = x
        self.y = y
        self.color = color
        self.vivo = True
        self.bombas_disponibles = 1

class Enemigo:
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo # "SMILE", "SMOKE", "SLIME"
        self.timer_mov = 0
        self.vivo = True

class Bomba:
    def __init__(self, x, y, owner_id):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.tiempo_detonacion = time.time() + 3.0
        self.radio = 2

class Explosion:
    def __init__(self, celdas):
        self.celdas = celdas # Lista de (x,y)
        self.tiempo_fin = time.time() + 0.5