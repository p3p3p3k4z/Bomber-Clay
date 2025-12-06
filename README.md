# Bomber-Clay 

este es un videojuego tipo arcade multijugador inspirado en el clásico *Bomberman*, desarrollado en Python utilizando la biblioteca **Pygame**.

Este proyecto fue creado como parte de la materia de **Redes de Computadoras**, con el objetivo principal de implementar una arquitectura de comunicación en tiempo real utilizando **Sockets TCP/IP** crudos, sin depender de motores de red de alto nivel.

![](assets/intro_bg.png)

---

### Jugabilidad
* **Multijugador LAN/IP Directa:** Juega con un amigo conectando dos instancias del juego mediante IP.
* **Modo Solitario:** Práctica contra la IA sin necesidad de conexión.
* **Sistema de Niveles:** 2 niveles generados proceduralmente y un **Jefe Final** gigante en el nivel 3.
* **Enemigos con IA Variada:**
    * *Smile (Errático):* Se mueve al azar.
    * *Ghost (Fantasma):* Atraviesa obstáculos blandos.
    * *Hunter (Cazador):* Persigue al jugador activamente utilizando heurística de distancia.
* **Power-Ups:** Bombas extra, Velocidad y Escudo.
* **Ranking:** Sistema de puntuaciones altas con persistencia de datos (JSON).

---

## Arquitectura de Red 

El núcleo del proyecto es su implementación de red, diseñada bajo el modelo **Cliente-Servidor Autoritativo**.

### 1. Modelo de Conexión: Listen Server
Se utiliza una arquitectura *Listen Server* (Servidor Escucha), donde una de las instancias del juego actúa simultáneamente como **Servidor (Host)** y como **Cliente (Jugador 1)**.
* **Host (Servidor Autoritativo):** Ejecuta la simulación del mundo, calcula la IA de los enemigos, detecta colisiones y gestiona los eventos globales (tiempo, spawn). Posee la "verdad absoluta" del estado del juego (`GameState`).
* **Cliente Remoto:** Actúa como una "terminal tonta". No calcula lógica de juego; solo captura las entradas del usuario (teclas) para enviarlas al servidor y recibe el estado del mundo serializado para renderizarlo.

### 2. Protocolo de Comunicación
* **Sockets:** Se utilizan Sockets BSD estándar a través de la librería `socket` de Python.
* **Transporte:** **TCP (Transmission Control Protocol)**.
    * *Justificación:* Se eligió TCP sobre UDP para garantizar la integridad y el orden de los datos críticos del juego (como la colocación de una bomba, la muerte de un jugador o el cambio de nivel). En este tipo de juego, la pérdida de un paquete de "poner bomba" afectaría gravemente la jugabilidad.
* **Puerto:** `7777`.

### 3. Sincronización y Serialización
* **Serialización:** Se utiliza `pickle` para serializar el objeto complejo `GameState` y transmitirlo a través de la red.
* **Ciclo de Actualización (Game Loop de Red):**
    1.  **Input:** El cliente captura inputs y envía un paquete de acción (`MOV`, `BOMBA`) al servidor.
    2.  **Procesamiento:** El servidor recibe inputs, actualiza la física, mueve la IA y resuelve explosiones.
    3.  **Broadcast:** El servidor serializa el estado actual y lo envía a todos los clientes conectados.
    4.  **Renderizado:** El cliente deserializa el objeto y dibuja el fotograma.
    5.  **Eventos:** Los eventos de audio (explosiones, powerups) se sincronizan enviando una lista de "flags" desde el servidor.

---

## Estructura del Proyecto

```text
EcoBomber/
│
├── game/               # Lógica de Negocio (Modelo)
│   ├── entities.py     # Clases (Jugador, Enemigo, Jefe, Bomba)
│   ├── gamestate.py    # Máquina de estados y reglas del juego
│   ├── map_gen.py      # Generación procedural de mapas
│   └── spawner.py      # Gestión de aparición de enemigos e ítems
│
├── network/            # Lógica de Red (Controlador)
│   └── manager.py      # Gestión de Sockets (Bind, Listen, Connect, Send/Recv)
│
├── ui/                 # Interfaz Gráfica (Vista)
│   └── renderer.py     # Motor de renderizado y dibujo de assets
│
├── utils/              # Utilidades
│   └── asset_manager.py # Carga optimizada de imágenes y sonidos
│
├── config.py           # Constantes globales
└── main.py             # Punto de entrada y Bucle Principal