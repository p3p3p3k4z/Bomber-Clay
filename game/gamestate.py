import time
import json
import os
from config import *
from game.entities import Jugador, Bomba, Explosion, Jefe, EnemigoErratico
from game.map_gen import MapGenerator
from game.spawner import Spawner

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
        
        self.cargar_nivel(1)

    def cargar_nivel(self, nivel):
        self.nivel_actual = nivel
        self.mapa = MapGenerator.generar(nivel)
        
        self.bombas = []
        self.explosiones = []
        self.enemigos = []
        self.jefe = None
        
        start_pos = [(1,1), (COLS-2, FILAS-2)]
        idx = 0
        for p in self.jugadores.values():
            if p.vivo:
                p.x, p.y = start_pos[idx % 2]
                idx += 1

        if nivel < 3:
            Spawner.spawn_enemigos_iniciales(self, nivel, self.singleplayer)
        else:
            self.jefe = Jefe(ANCHO//2 - 75, 50)

    def update(self):
        if self.estado_partida != STATE_PLAYING: return
        now = time.time()

        # JEFE
        if self.jefe and self.jefe.vivo:
            self.jefe.mover()
            if self.jefe.debe_invocar():
                Spawner.intentar_spawn(self, EnemigoErratico)
            
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

        # ESTADOS
        if cnt_vivos == 0:
            self.estado_partida = STATE_GAMEOVER
        elif self.jefe:
            if not self.jefe.vivo: self.estado_partida = STATE_WIN
        elif cnt_enemigos == 0:
            if self.nivel_actual < self.max_niveles:
                self.estado_partida = STATE_LEVEL_COMPLETED
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
                    Spawner.generar_item(self, nx, ny, self.nivel_actual)
                    hits.append((nx, ny)); break
                hits.append((nx, ny))
        
        self.explosiones.append(Explosion(hits, bomba.owner_id))
        
        for hx, hy in hits:
            for e in self.enemigos:
                if e.vivo and e.x==hx and e.y==hy:
                    e.vivo = False
                    self.audio_events.append("ENEMY_DIE")
                    if bomba.owner_id in self.jugadores: self.jugadores[bomba.owner_id].score += 100
            for p in self.jugadores.values():
                if p.x==hx and p.y==hy and not p.escudo_activo:
                    p.vivo = False; self.audio_events.append("DEATH_PLAYER")
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
        try:
            if os.path.exists(archivo):
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