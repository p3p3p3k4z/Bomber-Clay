import time
import random
from config import *

class Jugador:
    def __init__(self, id, x, y, color):
        self.id = id
        self.x, self.y = x, y
        self.color = color
        self.vivo = True
        self.nombre = f"Player {id}"
        self.score = 0
        self.bombas_disponibles = 1
        self.max_bombas = 1
        self.velocidad_extra = False
        self.escudo_activo = False
        self.timer_efecto = 0 

    def aplicar_item(self, tipo):
        if tipo == "BOMBA":
            self.max_bombas += 1
            self.bombas_disponibles += 1
        elif tipo == "VELOCIDAD":
            self.velocidad_extra = True
            self.timer_efecto = time.time() + 10
        elif tipo == "ESCUDO":
            self.escudo_activo = True
            self.timer_efecto = time.time() + 8

    def update(self):
        if time.time() > self.timer_efecto:
            self.velocidad_extra = False
            self.escudo_activo = False

class Jefe:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.w, self.h = 150, 150
        self.vida = BOSS_HP
        self.max_vida = BOSS_HP
        self.vivo = True
        self.direccion = 1
        self.velocidad = 2
        self.timer_spawn = time.time() + 5.0

    def mover(self):
        self.x += self.velocidad * self.direccion
        if self.x < 50 or self.x > ANCHO - 50 - self.w: self.direccion *= -1
            
    def debe_invocar(self):
        if time.time() > self.timer_spawn:
            self.timer_spawn = time.time() + 8.0
            return True
        return False

class Enemigo:
    def __init__(self, x, y, tipo):
        self.x, self.y = x, y
        self.tipo = tipo
        self.vivo = True
        self.timer_mov = 0
        self.velocidad = 1.0

    def get_velocidad(self):
        if self.tipo == "SLIME": return 0.6
        if self.tipo == "SMOKE": return 1.2
        return 0.8
    
    def puede_moverse(self, nx, ny, mapa):
        if 0 <= nx < COLS and 0 <= ny < FILAS: return mapa[ny][nx] == V
        return False

    def mover(self, mapa, jugadores): pass 

class EnemigoErratico(Enemigo):
    def __init__(self, x, y): super().__init__(x, y, "SMILE"); self.velocidad=0.8
    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            dirs = [(0,1), (0,-1), (1,0), (-1,0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = self.x + dx, self.y + dy
                if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny; break
            self.timer_mov = time.time() + self.velocidad

class EnemigoFantasma(Enemigo):
    def __init__(self, x, y): super().__init__(x, y, "SMOKE"); self.velocidad=1.2
    def puede_moverse(self, nx, ny, mapa):
        if 0 <= nx < COLS and 0 <= ny < FILAS: return mapa[ny][nx] in [V, B]
        return False
    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
            nx, ny = self.x + dx, self.y + dy
            if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny
            self.timer_mov = time.time() + self.velocidad

class EnemigoCazador(Enemigo):
    def __init__(self, x, y): super().__init__(x, y, "SLIME"); self.velocidad=0.6
    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            target = None
            min_dist = 999
            for p in jugadores.values():
                if p.vivo:
                    d = abs(p.x - self.x) + abs(p.y - self.y)
                    if d < min_dist and d < 8: min_dist = d; target = p
            moved = False
            if target:
                dx = 1 if target.x > self.x else -1 if target.x < self.x else 0
                dy = 1 if target.y > self.y else -1 if target.y < self.y else 0
                intentos = []
                if dx!=0: intentos.append((dx,0))
                if dy!=0: intentos.append((0,dy))
                for mx, my in intentos:
                    nx, ny = self.x+mx, self.y+my
                    if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny; moved = True; break
            if not moved:
                dirs = [(0,1), (0,-1), (1,0), (-1,0)]
                dx, dy = random.choice(dirs)
                nx, ny = self.x + dx, self.y + dy
                if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny
            self.timer_mov = time.time() + self.velocidad

class Bomba:
    def __init__(self, x, y, owner_id):
        self.x, self.y = x, y
        self.owner_id = owner_id
        self.tiempo_detonacion = time.time() + 3.0
        self.radio = 2

class Explosion:
    def __init__(self, celdas, owner_id):
        self.celdas = celdas
        self.owner_id = owner_id
        self.tiempo_fin = time.time() + 0.5