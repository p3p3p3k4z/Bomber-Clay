import random
from config import *
# ### AQUI 1: Importamos el nuevo enemigo ###
from game.entities import EnemigoErratico, EnemigoFantasma, EnemigoCazador, EnemigoTanque

class Spawner:
    @staticmethod
    def spawn_enemigos_iniciales(gamestate, nivel, singleplayer):
        if nivel < 3:
            # Más enemigos al inicio 
            base = 6 if singleplayer else 5
            total = base + ((nivel - 1) * 3)
            
            # Enemigos básicos disponibles siempre
            tipos = [EnemigoErratico, EnemigoFantasma, EnemigoCazador]
            
            # ### AQUI 2: El Tanque solo sale en Nivel 2 ###
            if nivel >= 1:
                tipos.append(EnemigoTanque)
            # ---------------------------------------------
            
            for _ in range(total):
                Spawner.intentar_spawn(gamestate, random.choice(tipos))

    @staticmethod
    def intentar_spawn(gamestate, ClaseEnemigo):
        for _ in range(50):
            ex, ey = random.randint(1, COLS-2), random.randint(1, FILAS-2)
            if gamestate.mapa[ey][ex] == V:
                # Seguridad: no spawnear muy cerca de los jugadores
                seguro = True
                for p in gamestate.jugadores.values():
                    if abs(p.x - ex) + abs(p.y - ey) < 12: seguro = False
                
                if seguro:
                    gamestate.enemigos.append(ClaseEnemigo(ex, ey))
                    return True
        return False

    @staticmethod
    def generar_item(gamestate, x, y, nivel):
        # Probabilidad reduce con el nivel (se hace más difícil)
        chance = max(0.15, 0.40 - (nivel * 0.08))
        
        if random.random() < chance:
            r = random.random()
            
            # ### AQUI 3: Probabilidades actualizadas para incluir FUEGO ###
            if r < 0.30: 
                gamestate.mapa[y][x] = ITEM_BOMBA      # 30% Bomba
            elif r < 0.55: 
                gamestate.mapa[y][x] = ITEM_VELOCIDAD  # 25% Velocidad
            elif r < 0.80:
                gamestate.mapa[y][x] = ITEM_FUEGO      # 25% Fuego (NUEVO)
            else: 
                gamestate.mapa[y][x] = ITEM_ESCUDO     # 20% Escudo
            # ----------------------------------------------------------
            
        else:
            gamestate.mapa[y][x] = V