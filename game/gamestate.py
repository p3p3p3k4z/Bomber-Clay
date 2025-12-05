import random
import time
from config import *
# Importamos las clases específicas para que funcione la IA de cada uno
from game.entities import Jugador, Bomba, Explosion, EnemigoErratico, EnemigoFantasma, EnemigoCazador

class GameState:
    def __init__(self, modo_singleplayer=False):
        self.mapa = [[V for _ in range(COLS)] for _ in range(FILAS)]
        self.jugadores = {} 
        self.bombas = []
        self.explosiones = []
        self.enemigos = []
        
        # COLA DE EVENTOS DE AUDIO
        self.audio_events = [] 
        
        self.singleplayer = modo_singleplayer
        self.estado_partida = "PLAYING"
        self.tiempo_inicio = time.time()
        
        self.generar_nivel()

    def generar_nivel(self):
        # 1. Mapa Procedural
        for y in range(FILAS):
            for x in range(COLS):
                if x == 0 or x == COLS-1 or y == 0 or y == FILAS-1:
                    self.mapa[y][x] = R
                elif x % 2 == 0 and y % 2 == 0:
                    self.mapa[y][x] = R
                elif random.random() < 0.4:
                    self.mapa[y][x] = B
        
        # 2. Zonas seguras (Esquinas para J1 y J2)
        for (sx, sy) in [(1,1), (1,2), (2,1), (COLS-2, FILAS-2)]:
            self.mapa[sy][sx] = V
        
        # 3. Spawning de Enemigos con IA específica
        # Si es Singleplayer ponemos menos enemigos para que sea justo
        if self.singleplayer:
            cant_tipos = [2, 1, 1] # 2 Smiles, 1 Fantasma, 1 Cazador
        else:
            cant_tipos = [2, 2, 2] # 2 de cada uno

        # Generar Smiles (Erráticos)
        for _ in range(cant_tipos[0]): self.spawn_enemigo(EnemigoErratico)
        # Generar Fantasmas (Smoke)
        for _ in range(cant_tipos[1]): self.spawn_enemigo(EnemigoFantasma)
        # Generar Cazadores (Slime)
        for _ in range(cant_tipos[2]): self.spawn_enemigo(EnemigoCazador)

    def spawn_enemigo(self, ClaseEnemigo):
        """Busca un lugar vacío aleatorio y pone el enemigo correcto"""
        intentos = 0
        while intentos < 50:
            ex, ey = random.randint(3, COLS-3), random.randint(3, FILAS-3)
            if self.mapa[ey][ex] == V:
                self.enemigos.append(ClaseEnemigo(ex, ey))
                break
            intentos += 1

    def update(self):
        if self.estado_partida != "PLAYING": return
        now = time.time()

        # A. Bombas
        for b in self.bombas[:]:
            if now >= b.tiempo_detonacion:
                self.detonar(b)
                self.bombas.remove(b)
                if b.owner_id in self.jugadores:
                    self.jugadores[b.owner_id].bombas_disponibles += 1

        # B. Explosiones
        for e in self.explosiones[:]:
            if now >= e.tiempo_fin: self.explosiones.remove(e)

        # C. Enemigos (IA Polimórfica)
        enemigos_vivos = 0
        for e in self.enemigos:
            if e.vivo:
                enemigos_vivos += 1
                # POLIMORFISMO: Cada enemigo decide cómo moverse
                e.mover(self.mapa, self.jugadores)
                
                # Colisión con Jugadores (Muerte)
                for p in self.jugadores.values():
                    if p.vivo and not p.escudo_activo and p.x == e.x and p.y == e.y:
                        p.vivo = False
                        self.audio_events.append("DEATH_PLAYER")

        # D. Jugadores (Timers de items)
        jugadores_vivos = 0
        for p in self.jugadores.values():
            p.update()
            if p.vivo: jugadores_vivos += 1

        # E. Estado de Victoria/Derrota
        if jugadores_vivos == 0:
            self.estado_partida = "LOSE"
        elif enemigos_vivos == 0:
            # Bonus de victoria
            for p in self.jugadores.values():
                if p.vivo: p.score += PUNTOS_VICTORIA
            self.estado_partida = "WIN"

    def detonar(self, bomba):
        self.audio_events.append("EXPLOSION")
        
        hits = [(bomba.x, bomba.y)]
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        
        for dx, dy in dirs:
            for i in range(1, bomba.radio + 1):
                nx, ny = bomba.x + dx*i, bomba.y + dy*i
                if not (0 <= nx < COLS and 0 <= ny < FILAS): break
                
                cell = self.mapa[ny][nx]
                if cell == R: break
                if cell == B:
                    self.destruir_bloque(nx, ny)
                    hits.append((nx, ny))
                    break
                hits.append((nx, ny))
        
        self.explosiones.append(Explosion(hits, bomba.owner_id))
        
        # Daño de la explosión
        for (hx, hy) in hits:
            # Matar Enemigos
            for e in self.enemigos:
                if e.vivo and e.x == hx and e.y == hy:
                    e.vivo = False
                    self.audio_events.append("ENEMY_DIE")
                    if bomba.owner_id in self.jugadores:
                        self.jugadores[bomba.owner_id].score += PUNTOS_ENEMIGO
            
            # Matar Jugadores
            for p in self.jugadores.values():
                if p.x == hx and p.y == hy and not p.escudo_activo:
                    p.vivo = False
                    self.audio_events.append("DEATH_PLAYER")

    def destruir_bloque(self, x, y):
        self.mapa[y][x] = V
        # Generación de Ítems Aleatorios
        if random.random() < 0.30: # 30% de probabilidad
            r = random.random()
            if r < 0.4: item = ITEM_BOMBA
            elif r < 0.7: item = ITEM_VELOCIDAD
            else: item = ITEM_ESCUDO
            self.mapa[y][x] = item

    def mover_jugador(self, pid, dx, dy):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if not p.vivo: return

        nx, ny = p.x + dx, p.y + dy
        
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            cell = self.mapa[ny][nx]
            
            # Recoger Items
            if cell in [ITEM_BOMBA, ITEM_VELOCIDAD, ITEM_ESCUDO]:
                tipo = "BOMBA" if cell == ITEM_BOMBA else "VELOCIDAD" if cell == ITEM_VELOCIDAD else "ESCUDO"
                p.aplicar_item(tipo)
                self.mapa[ny][nx] = V
                p.score += 50
                self.audio_events.append("POWERUP")
                return # Se queda en la casilla y consume el item
            
            # Movimiento normal en vacío
            if cell == V:
                if not any(b.x == nx and b.y == ny for b in self.bombas):
                    p.x, p.y = nx, ny

    def poner_bomba(self, pid):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if p.vivo and p.bombas_disponibles > 0:
            self.bombas.append(Bomba(p.x, p.y, pid))
            p.bombas_disponibles -= 1
            self.audio_events.append("PLANT_BOMB")