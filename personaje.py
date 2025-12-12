try:
    import pygame
except ModuleNotFoundError:
    print("Error: Pygame no está instalado. Instala con: pip install pygame")
    raise


class Personaje(pygame.sprite.Sprite):
    """Clase Personaje con movimiento básico, salto, agacharse y ataques.

    Controles por defecto:
      - Jugador 1: A,D para moverse, W para saltar, S agacharse, Q puñetazo, E patada
      - Jugador 2: Flechas para moverse, Up para saltar, Down agacharse, Numpad1 puñetazo, Numpad2 patada
    """

    def __init__(self, nombre, vida, x, y, animaciones=None, es_jugador1=True):
        super().__init__()
        self.nombre = nombre
        self.vida = vida

        # Controles
        if es_jugador1:
            self.controles = {
                "IZQ": pygame.K_a,
                "DER": pygame.K_d,
                "SALTAR": pygame.K_w,
                "AGACHAR": pygame.K_s,
                "PUNZON": pygame.K_q,
                "PATADA": pygame.K_e,
            }
        else:
            self.controles = {
                "IZQ": pygame.K_LEFT,
                "DER": pygame.K_RIGHT,
                "SALTAR": pygame.K_UP,
                "AGACHAR": pygame.K_DOWN,
                "PUNZON": pygame.K_KP1,
                "PATADA": pygame.K_KP2,
            }

        # Tamaño y visual provisional
        self.ancho = 50
        self.alto = 100
        self.image = pygame.Surface([self.ancho, self.alto], pygame.SRCALPHA)
        color = (255, 0, 0) if es_jugador1 else (0, 0, 255)
        self.image.fill(color)
        self.rect = self.image.get_rect()
        # Colocamos la base (bottom) en y
        self.rect.x = x
        self.rect.bottom = y

        # Física
        self.gravedad = 1.5
        self.fuerza_salto = -20
        self.velocidad_movimiento = 5
        self.velocidad_x = 0
        self.velocidad_y = 0
        self.en_tierra = True

        # Estados
        self.estado_actual = "idle"  # idle, caminar, saltar, agacharse, pegar, patear
        self.mirando_derecha = True
        self.is_attacking = False
        self.attack_frame = 0
        self.attack_duration = 15  # frames

        # Hitbox para colisiones de ataque (puede ajustarse)
        self.hitbox = self.rect.copy()

        # Guardar si es jugador 1
        self.es_jugador1 = es_jugador1

    def aplicar_gravedad(self, limite_suelo):
        if self.rect.bottom < limite_suelo:
            self.velocidad_y += self.gravedad
            self.en_tierra = False
        else:
            self.velocidad_y = 0
            self.rect.bottom = limite_suelo
            self.en_tierra = True

    def manejar_input(self, teclas_presionadas, ancho_pantalla, suelo_y):
        # Solo procesar input si no estamos en una animación que lo bloquee (a excepción del salto que se verifica en tierra)
        self.velocidad_x = 0
        # Por defecto no agachado
        agachado = False

        # Movimiento horizontal
        if teclas_presionadas[self.controles["IZQ"]]:
            self.velocidad_x = -self.velocidad_movimiento
            self.mirando_derecha = False
            self.estado_actual = "caminar"

        if teclas_presionadas[self.controles["DER"]]:
            self.velocidad_x = self.velocidad_movimiento
            self.mirando_derecha = True
            self.estado_actual = "caminar"

        # Saltar
        if teclas_presionadas[self.controles["SALTAR"]] and self.en_tierra and not self.is_attacking:
            self.velocidad_y = self.fuerza_salto
            self.en_tierra = False
            self.estado_actual = "saltar"

        # Agacharse (solo en tierra)
        if teclas_presionadas[self.controles["AGACHAR"]] and self.en_tierra and not self.is_attacking:
            agachado = True
            self.velocidad_x = 0
            self.estado_actual = "agacharse"

        # Ataques (acción puntual)
        # Solo iniciar ataque si no estamos atacando actualmente
        if not self.is_attacking:
            if teclas_presionadas[self.controles["PUNZON"]]:
                self.estado_actual = "pegar"
                self.is_attacking = True
                self.attack_frame = 0
            elif teclas_presionadas[self.controles["PATADA"]]:
                self.estado_actual = "patear"
                self.is_attacking = True
                self.attack_frame = 0

        # Ajuste de la hitbox y visual al agacharse
        if agachado:
            # Reducir la altura visual y rect para el hitbox
            altura_agachado = int(self.alto * 0.6)
            # Ajustamos la imagen y rect manteniendo la bottom
            old_bottom = self.rect.bottom
            self.image = pygame.Surface([self.ancho, altura_agachado], pygame.SRCALPHA)
            color = (255, 0, 0) if self.es_jugador1 else (0, 0, 255)
            self.image.fill(color)
            self.rect = self.image.get_rect()
            self.rect.x = max(0, min(ancho_pantalla - self.rect.width, self.rect.x))
            self.rect.bottom = old_bottom
        else:
            # Restaurar tamaño si no está agachado
            if self.rect.height != self.alto:
                old_bottom = self.rect.bottom
                self.image = pygame.Surface([self.ancho, self.alto], pygame.SRCALPHA)
                color = (255, 0, 0) if self.es_jugador1 else (0, 0, 255)
                self.image.fill(color)
                self.rect = self.image.get_rect()
                self.rect.x = max(0, min(ancho_pantalla - self.rect.width, self.rect.x))
                self.rect.bottom = old_bottom

    def actualizar(self, ancho_pantalla, suelo_y):
        # Aplicar gravedad y actualizar Y
        self.aplicar_gravedad(suelo_y)
        self.rect.y += int(self.velocidad_y)

        # Aplicar movimiento X
        self.rect.x += int(self.velocidad_x)

        # Limitar a pantalla
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > ancho_pantalla:
            self.rect.right = ancho_pantalla

        # Manejo del estado de ataque
        if self.is_attacking:
            self.attack_frame += 1
            # Durante los frames iniciales del ataque podemos ajustar el hitbox
            # (Ejemplo simple): extendemos el hitbox en la dirección que mira
            alcance = 30
            if self.mirando_derecha:
                self.hitbox = pygame.Rect(self.rect.right, self.rect.top + 20, alcance, int(self.rect.height * 0.6))
            else:
                self.hitbox = pygame.Rect(self.rect.left - alcance, self.rect.top + 20, alcance, int(self.rect.height * 0.6))

            if self.attack_frame > self.attack_duration:
                self.is_attacking = False
                self.estado_actual = "idle"
                self.hitbox = self.rect.copy()
        else:
            # Hitbox normal
            self.hitbox = self.rect.copy()

    def dibujar_hitbox(self, surface):
        # Dibuja el rect del hitbox para debugging (semi-transparente)
        s = pygame.Surface((self.hitbox.width, self.hitbox.height), pygame.SRCALPHA)
        s.fill((255, 255, 0, 120))
        surface.blit(s, (self.hitbox.x, self.hitbox.y))

