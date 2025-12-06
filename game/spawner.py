import random
from config import *
from game.entities import EnemigoErratico, EnemigoFantasma, EnemigoCazador

class Spawner:
    @staticmethod
    def spawn_enemigos_iniciales(gamestate, nivel, singleplayer):
        if nivel < 3:
            # Más enemigos al inicio 
            base = 5 if singleplayer else 3
            total = base + ((nivel - 1) * 3)
            tipos = [EnemigoErratico, EnemigoFantasma, EnemigoCazador]
            
            for _ in range(total):
                Spawner.intentar_spawn(gamestate, random.choice(tipos))

    @staticmethod
    def intentar_spawn(gamestate, ClaseEnemigo):
        for _ in range(50):
            ex, ey = random.randint(1, COLS-2), random.randint(1, FILAS-2)
            if gamestate.mapa[ey][ex] == V:
                # Seguridad
                seguro = True
                for p in gamestate.jugadores.values():
                    if abs(p.x - ex) + abs(p.y - ey) < 8: seguro = False
                
                if seguro:
                    gamestate.enemigos.append(ClaseEnemigo(ex, ey))
                    return True
        return False

    @staticmethod
    def generar_item(gamestate, x, y, nivel):
        # Probabilidad reduce con el nivel
        chance = max(0.15, 0.40 - (nivel * 0.08))
        if random.random() < chance:
            r = random.random()
            if r < 0.4: gamestate.mapa[y][x] = ITEM_BOMBA
            elif r < 0.7: gamestate.mapa[y][x] = ITEM_VELOCIDAD
            else: gamestate.mapa[y][x] = ITEM_ESCUDO
        else:
            gamestate.mapa[y][x] = V