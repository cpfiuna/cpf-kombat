# CPF Kombat 🎮

Un juego de peleas 2D desarrollado en Python con Pygame, presentando personajes personalizados del Club de Programación FIUNA. Desarrollado para el día de FIUNA Puertas Abiertas 2025.

## 🚀 Características

- **Selección de personajes personalizada** con 8 luchadores únicos
- **Sistema de combate por rounds** (mejor de 3 rounds)
- **Colisiones pixel-perfect** usando máscaras de pygame
- **Sprites animados** para cada personaje con estados: idle, caminar, saltar, agacharse, golpear y patear
- **Múltiples escenarios** seleccionables (Citec, Plazoleta, Cantina)
- **Optimizaciones de rendimiento** con pre-caching de sprites y máscaras
- **Control de FPS ajustable** (toggle con F7)
- **Modo pantalla completa** (toggle con F11)
- **Sistema de hitboxes visualizables** para debugging (toggle con H)
- **Overlay de rostros** sobre los sprites de personajes
- **Música y efectos** personalizables

## 📋 Requisitos

### Dependencias de Python
```bash
pip install pygame numpy
```

### Versiones recomendadas
- Python 3.8+ (preferible 3.10/3.11)
- Pygame 2.0+
- NumPy (para operaciones con arrays)

### Archivos necesarios
El proyecto requiere la siguiente estructura de carpetas (incluidas en el repositorio):

- `Sprites/` - Sprites animados de personajes (GIF/PNG)
- `images/` - Imágenes del selector, mapas y logos
- `images/caras/` - Rostros de personajes para overlay
- `images/logos/` - Logos de victoria y rounds
- `mapas/` - Fondos de escenarios
- `music/` - Música de portada (opcional)

## 🛠️ Instalación

1. **Clona este repositorio:**
```bash
git clone https://github.com/cpfiuna/cpf-kombat.git
cd cpf-kombat
```

2. **Instala las dependencias:**
```bash
pip install pygame numpy
```

3. **Ejecuta el juego:**
```bash
python juego.py
```

### Instalación con entorno virtual (recomendado)
```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install --upgrade pip
pip install pygame numpy

# Ejecutar juego
python juego.py
```

## 📖 Uso

1. Al ejecutar el juego, verás la **pantalla de portada**
2. Presiona **Enter** o haz clic para avanzar a la **selección de personajes**
3. **Jugador 1** selecciona su personaje haciendo clic en uno de los retratos
4. **Jugador 2** selecciona su personaje (debe ser diferente al del Jugador 1)
5. Haz clic en **"Iniciar pelea"** para avanzar a la selección de mapa
6. Selecciona uno de los **3 escenarios** disponibles
7. ¡Comienza la pelea! El primero en ganar **2 rounds** gana el combate
8. Al finalizar, el juego vuelve automáticamente a la selección de personajes

## 🎮 Controles

### Jugador 1
- **A** - Moverse a la izquierda
- **D** - Moverse a la derecha
- **W** - Saltar
- **S** - Agacharse
- **Q** - Puñetazo
- **E** - Patada

### Jugador 2
- **← →** - Moverse (flechas izquierda/derecha)
- **↑** - Saltar
- **↓** - Agacharse
- **Numpad 1** - Puñetazo
- **Numpad 2** - Patada

### Controles especiales
- **H** - Mostrar/ocultar hitboxes de selección (modo debug)
- **F7** - Activar/desactivar límite de FPS
- **F11** - Alternar pantalla completa
- **ESC** - Salir del juego

## 🧑‍🤼 Personajes

El juego incluye 8 personajes únicos:
- **Daniel**
- **David**
- **Esteban**
- **Ivan**
- **Mathi**
- **Osu**
- **Park**
- **Santi**

Cada personaje tiene sprites únicos para:
- Idle (reposo)
- Caminar
- Saltar
- Agacharse
- Golpe (puñetazo)
- Patada

## 🗺️ Escenarios

Tres escenarios disponibles:
1. **Citec** - Centro de Investigación y Tecnología
2. **Plazoleta** - Plaza central de FIUNA
3. **Cantina** - Cantina universitaria

## 🧠 Tecnologías Utilizadas

- **Python** - Lenguaje de programación principal
- **Pygame** - Motor de juego 2D
- **NumPy** - Operaciones matemáticas y arrays
- **Máscaras de pygame** - Colisiones pixel-perfect
- **JSON** - Almacenamiento de configuración de hitboxes

## 📁 Estructura del Proyecto

```
cpf-kombat/
├── juego.py                     # Script principal del juego
├── personaje.py                 # Clase Personaje (legacy)
├── Sprites/                     # Sprites de personajes
│   ├── SpritesDaniel/
│   ├── SpritesDavid/
│   ├── SpritesEsteban/
│   ├── SpritesIvan/
│   ├── SpritesMathi/
│   ├── SpritesOsu/
│   ├── SpritesPark/
│   └── SpritesSanti/
├── images/                      # Imágenes del juego
│   ├── SelectorDePersonajes.jpg
│   ├── SelectorDeMapas.jpg
│   ├── portada.jpg
│   ├── caras/                   # Rostros de personajes
│   ├── logos/                   # Logos de victoria y rounds
│   ├── selector_rects.json      # Hitboxes de selector
│   └── map_selector_rects.json  # Hitboxes de mapas
├── mapas/                       # Fondos de escenarios
│   └── Citec.jpg
├── music/                       # Música del juego
│   └── portada.ogg
├── logs/                        # Archivos de log
├── tools/                       # Herramientas auxiliares
│   └── match_face.py
├── LICENSE                      # Licencia del proyecto
└── README.md                    # Este archivo
```

## 🔧 Configuración

### Sistema de Combate
- **Vida inicial**: 100 puntos por personaje
- **Tiempo por round**: 90 segundos
- **Rounds para ganar**: 2 de 3
- **Daño por golpe**: Configurable en el código
- **Cooldown entre golpes**: Previene spam de ataques

### Optimizaciones de Rendimiento
El juego incluye varias optimizaciones:
- **Pre-caching de sprites**: Los sprites se escalan y cachean al inicio
- **Máscaras precomputadas**: Las máscaras de colisión se calculan una sola vez
- **Bounding boxes precalculados**: Rectángulos de colisión optimizados
- **Superficies reutilizables**: Reduce allocaciones de memoria
- **FPS cap opcional**: Limita el framerate para estabilidad

### Personalización
Puedes personalizar:
- Sprites de personajes (carpeta `Sprites/`)
- Rostros overlay (carpeta `images/caras/`)
- Fondos de escenarios (carpeta `mapas/`)
- Música (carpeta `music/`)
- Hitboxes de selección (archivos JSON en `images/`)

## 🚨 Solución de Problemas

### Error: "Pygame no está instalado"
```bash
pip install pygame
```

### Error: "No se encuentra el archivo de sprite"
- Verifica que todas las carpetas de `Sprites/` tengan los archivos correspondientes
- Los nombres de archivo deben seguir el formato: `estado{Derecha|Izquierda}{Nombre}.{png|gif}`
- Ejemplo: `idleDerechaDaniel.gif`, `patadaIzquierdaDavid.png`

### Rendimiento lento / Bajones de FPS
1. Presiona **F7** para activar el límite de FPS
2. Reduce la resolución de ventana si es necesario
3. Cierra otras aplicaciones que consuman recursos
4. Los sprites grandes pueden ralentizar el juego - considera optimizar las imágenes

### La selección de personajes no funciona
- Presiona **H** para visualizar las hitboxes de selección
- Asegúrate de hacer clic dentro de las cajas rojas pequeñas
- Presiona **R** para recargar las configuraciones de hitboxes

### El juego no vuelve a la selección después del combate
- Esto debería funcionar automáticamente
- Si no funciona, verifica que no haya errores en la consola
- Presiona **ESC** para salir y reinicia el juego

## 📄 Licencia

Este proyecto está disponible bajo los términos especificados en el archivo LICENSE.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz un **Fork** del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un **Pull Request**

### Ideas para contribuir
- Agregar nuevos personajes
- Crear nuevos escenarios
- Implementar power-ups o ítems
- Mejorar la IA para modo un jugador
- Agregar efectos de sonido
- Implementar combos y movimientos especiales
- Crear un sistema de ranking online

## 👥 Créditos

- **Sprites y arte**: Comunidad del Club de Programación FIUNA
- **Desarrollo**: Equipo CPF Kombat
- **Motor**: Pygame Community
- **Inspiración**: Juegos de pelea clásicos
- Desarrollado por el **Club de Programación FIUNA**

---

**Nota**: Este es un proyecto educativo desarrollado con fines de aprendizaje y demostración durante FIUNA Puertas Abiertas 2025.

## 📞 Contacto

- **Instagram**: [@cpfiuna](https://www.instagram.com/cpfiuna)
- **Discord**: [CPF Discord](https://discord.gg/cpfiuna)
- **YouTube**: [CPF YouTube](https://www.youtube.com/@cpfiuna)

**Visitá nuestra página web**: [cpf.fiuna.edu.py](https://cpfiuna.io/) :)
