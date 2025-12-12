# Demo de Pelea - Fase 2

Este pequeño demo implementa la clase `Personaje` con mecánicas de movimiento: caminar, saltar, agacharse, puñetazo y patada.

Requisitos:
- Python 3.8+ (preferible 3.10/3.11)
- Pygame (pip install pygame)

Ejecutar en Windows PowerShell:

```powershell
# Crear e instalar en un entorno virtual (opcional pero recomendado)
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --upgrade pip; pip install pygame

# Ejecutar demo
python .\juego.py
```

Controles por defecto:
- Jugador 1: A (izq), D (der), W (saltar), S (agacharse), Q (puñon), E (patada)
- Jugador 2: Flechas izq/der, Flecha arriba (saltar), Flecha abajo (agacharse), Numpad1 (puñon), Numpad2 (patada)

Presiona H para alternar la visualización de hitboxes.

Notas:
- Este demo usa sprites placeholder (rectángulos). Sustituir por animaciones/frames en `Personaje` si lo deseas.
- La detección de colisiones de ataque está en `Personaje.hitbox` y se puede usar para reducir vida cuando coincide con el rect del oponente.
