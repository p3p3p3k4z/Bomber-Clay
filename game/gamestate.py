import random
import time
import json
import os
from config import *
from game.entities import Jugador, Bomba, Explosion, Jefe, EnemigoErratico, EnemigoFantasma, EnemigoCazador

class GameState:
    def __init__(self, modo_singleplayer=False):
        self.mapa = []
        self.jugadores = {}
        self.bombas = []
        self.explosiones = []
        self.enemigos = []
        self.jefe = None
        self.audio_events = []
        
        self.singleplayer = modo_singleplayer
        self.nivel_actual = 1
        self.max_niveles = 3
        
        self.estado_partida = STATE_PLAYING
        self.tiempo_inicio = time.time()
        
        # Iniciar primer nivel
        self.cargar_nivel(1)

    def cargar_nivel(self, nivel):
        self.nivel_actual = nivel
        self.mapa = [[V for _ in range(COLS)] for _ in range(FILAS)]
        self.bombas = []
        self.explosiones = []
        self.enemigos = []
        self.jefe = None
        
        # Reset posiciones jugadores
        positions = [(1,1), (COLS-2, FILAS-2)]
        idx = 0
        for p in self.jugadores.values():
            if p.vivo:
                p.x, p.y = positions[idx % len(positions)]
                idx += 1

        # Bordes fijos
        for y in range(FILAS):
            for x in range(COLS):
                if x==0 or x==COLS-1 or y==0 or y==FILAS-1: self.mapa[y][x] = R
                elif x%2==0 and y%2==0: self.mapa[y][x] = R # Muro fijo intercalado

        if nivel < 3:
            # Niveles 1 y 2
            for y in range(1, FILAS-1):
                for x in range(1, COLS-1):
                    if self.mapa[y][x] == R: continue
                    
                    rand = random.random()
                    # AUMENTO DIFICULTAD: 20% Muros, 60% Arbustos
                    if rand < 0.10: self.mapa[y][x] = R
                    elif rand < 0.50: self.mapa[y][x] = B
            
            # Limpiar zonas inicio
            for (sx, sy) in [(1,1), (1,2), (2,1), (COLS-2, FILAS-2), (COLS-3, FILAS-2), (COLS-2, FILAS-3)]:
                self.mapa[sy][sx] = V
            
            # Spawn Enemigos (Aumentan con el nivel)
            base = 1 if self.singleplayer else 1
            total = base + ((nivel-1) * 3)
            tipos = [EnemigoErratico, EnemigoFantasma, EnemigoCazador]
            
            for _ in range(total):
                self.spawn_enemigo(random.choice(tipos))
            
        else:
            # Nivel 3: Jefe
            for y in range(1, FILAS-1):
                for x in range(1, COLS-1):
                    if self.mapa[y][x] == V and random.random() < 0.15:
                        self.mapa[y][x] = B
            self.jefe = Jefe(ANCHO//2 - 75, 50)

    def spawn_enemigo(self, Clase):
        for _ in range(50):
            ex, ey = random.randint(1, COLS-2), random.randint(1, FILAS-2)
            # Evitar spawnear encima de jugadores
            seguro = True
            for p in self.jugadores.values():
                if abs(p.x - ex) + abs(p.y - ey) < 5: seguro = False
            
            if self.mapa[ey][ex] == V and seguro:
                self.enemigos.append(Clase(ex, ey))
                break

    def update(self):
        if self.estado_partida != STATE_PLAYING: return
        now = time.time()

        # JEFE
        if self.jefe and self.jefe.vivo:
            self.jefe.mover()
            rect_j = (self.jefe.x, self.jefe.y, self.jefe.w, self.jefe.h)
            for p in self.jugadores.values():
                px, py = p.x * TAM_CELDA, p.y * TAM_CELDA
                if (px < rect_j[0]+rect_j[2] and px+TAM_CELDA > rect_j[0] and
                    py < rect_j[1]+rect_j[3] and py+TAM_CELDA > rect_j[1]):
                    if not p.escudo_activo:
                        p.vivo = False
                        self.audio_events.append("DEATH_PLAYER")

        # BOMBAS
        for b in self.bombas[:]:
            if now >= b.tiempo_detonacion:
                self.detonar(b)
                self.bombas.remove(b)
                if b.owner_id in self.jugadores:
                    self.jugadores[b.owner_id].bombas_disponibles += 1

        # EXPLOSIONES
        for e in self.explosiones[:]:
            if now >= e.tiempo_fin: self.explosiones.remove(e)

        # ENEMIGOS
        cnt_enemigos = 0
        for e in self.enemigos:
            if e.vivo:
                cnt_enemigos += 1
                e.mover(self.mapa, self.jugadores)
                for p in self.jugadores.values():
                    if p.vivo and not p.escudo_activo and p.x==e.x and p.y==e.y:
                        p.vivo = False
                        self.audio_events.append("DEATH_PLAYER")

        # JUGADORES
        cnt_vivos = 0
        for p in self.jugadores.values():
            p.update()
            if p.vivo: cnt_vivos += 1

        # LOGICA DE NIVELES
        if cnt_vivos == 0:
            self.estado_partida = STATE_GAMEOVER
        elif self.jefe:
            if not self.jefe.vivo: self.estado_partida = STATE_WIN
        elif cnt_enemigos == 0:
            if self.nivel_actual < self.max_niveles:
                self.nivel_actual += 1
                self.cargar_nivel(self.nivel_actual) # ¡AQUÍ ESTABA EL ERROR!
                self.estado_partida = STATE_NEXT_LEVEL
                self.audio_events.append("LEVEL_UP")
            else:
                self.estado_partida = STATE_WIN

    def detonar(self, bomba):
        self.audio_events.append("EXPLOSION")
        hits = [(bomba.x, bomba.y)]
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        for dx, dy in dirs:
            for i in range(1, bomba.radio+1):
                nx, ny = bomba.x + dx*i, bomba.y + dy*i
                if not (0<=nx<COLS and 0<=ny<FILAS): break
                cell = self.mapa[ny][nx]
                if cell == R: break
                if cell == B:
                    self.destruir_bloque(nx, ny)
                    hits.append((nx, ny)); break
                hits.append((nx, ny))
        
        self.explosiones.append(Explosion(hits, bomba.owner_id))
        
        for hx, hy in hits:
            # Enemigos
            for e in self.enemigos:
                if e.vivo and e.x==hx and e.y==hy:
                    e.vivo = False
                    self.audio_events.append("ENEMY_DIE")
                    if bomba.owner_id in self.jugadores: self.jugadores[bomba.owner_id].score += 100
            # Jugadores
            for p in self.jugadores.values():
                if p.x==hx and p.y==hy and not p.escudo_activo:
                    p.vivo = False; self.audio_events.append("DEATH_PLAYER")
            # Jefe
            if self.jefe and self.jefe.vivo:
                jx, jy = self.jefe.x, self.jefe.y
                ex, ey = hx*TAM_CELDA, hy*TAM_CELDA
                if (ex < jx+self.jefe.w and ex+TAM_CELDA > jx and ey < jy+self.jefe.h and ey+TAM_CELDA > jy):
                    self.jefe.vida -= 1
                    self.audio_events.append("BOSS_HIT")
                    if self.jefe.vida <= 0:
                        self.jefe.vivo = False
                        self.audio_events.append("BOSS_DIE")
                        if bomba.owner_id in self.jugadores: self.jugadores[bomba.owner_id].score += 5000

    def destruir_bloque(self, x, y):
        self.mapa[y][x] = V
        # MENOS ITEMS SEGÚN NIVEL
        chance = max(0.10, 0.35 - (self.nivel_actual * 0.05))
        if random.random() < chance:
            r = random.random()
            if r<0.4: self.mapa[y][x] = ITEM_BOMBA
            elif r<0.7: self.mapa[y][x] = ITEM_VELOCIDAD
            else: self.mapa[y][x] = ITEM_ESCUDO

    def mover_jugador(self, pid, dx, dy):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if not p.vivo: return
        nx, ny = p.x+dx, p.y+dy
        if 0<=nx<COLS and 0<=ny<FILAS:
            cell = self.mapa[ny][nx]
            if cell in [ITEM_BOMBA, ITEM_VELOCIDAD, ITEM_ESCUDO]:
                tipo = "BOMBA" if cell==ITEM_BOMBA else "VELOCIDAD" if cell==ITEM_VELOCIDAD else "ESCUDO"
                p.aplicar_item(tipo)
                self.mapa[ny][nx] = V
                p.score += 50
                self.audio_events.append("POWERUP")
                return
            if cell == V:
                if not any(b.x==nx and b.y==ny for b in self.bombas): p.x, p.y = nx, ny

    def poner_bomba(self, pid):
        if pid in self.jugadores:
            p = self.jugadores[pid]
            if p.vivo and p.bombas_disponibles > 0:
                self.bombas.append(Bomba(p.x, p.y, pid))
                p.bombas_disponibles -= 1
                self.audio_events.append("PLANT_BOMB")

    def guardar_puntaje(self, nombre, puntaje):
        archivo = "scores.json"
        datos = []
        if os.path.exists(archivo):
            try:
                with open(archivo,'r') as f: datos = json.load(f)
            except: pass
        datos.append({"nombre": nombre, "score": puntaje})
        datos.sort(key=lambda x: x["score"], reverse=True)
        datos = datos[:10]
        with open(archivo,'w') as f: json.dump(datos, f)

    def cargar_puntajes(self):
        try:
            with open("scores.json",'r') as f: return json.load(f)
        except: return []