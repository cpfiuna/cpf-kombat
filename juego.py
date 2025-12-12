try:
    import pygame
except ModuleNotFoundError:
    print("Error: Pygame no está instalado. Instala con: pip install pygame")
    raise
import numpy as np
import sys
import os
import json
from personaje import Personaje

class Juego:
    def __init__(self, ancho=1366, alto=768, fps=60):
        # Ventana fija a 1366x768 (no fullscreen)
        self.ancho = ancho
        self.alto = alto
        self.fps = fps
        pygame.init()
        self.pantalla = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Demo Pelea - Fase 2")
        self.reloj = pygame.time.Clock()

        # Datos de ejemplo para personajes
        self.personaje_p1 = {"nombre": "Ryu"}
        self.personaje_p2 = {"nombre": "Ken"}

        # Atributos que se crearán en ejecutar_pelea
        self.luchador_p1 = None
        self.luchador_p2 = None
        self.grupo_sprites = None
        self.limite_suelo = None

        # Opcional: mostrar hitboxes
        self.mostrar_hitbox = True
        # FPS cap settings (can be toggled in-game with F7)
        self.fps_cap_enabled = True
        self.fps_cap = 60
        # Reusable surfaces for selector hitbox drawing
        self.selector_hitbox_surf = None

    def ejecutar_pelea(self):
        # Mostrar menú de inicio antes de iniciar la pelea
        musica_portada = "music/portada.ogg"

        # tamaño por defecto de ventana (para volver de fullscreen)
        windowed_w, windowed_h = self.ancho, self.alto

        # Buscar automáticamente un archivo de portada dentro de images/
        portada_img = None
        portada_path = None
        images_dir = "images"
        if os.path.isdir(images_dir):
            # Priorizar archivos que empiecen por 'portada.' (case-insensitive)
            for name in os.listdir(images_dir):
                low = name.lower()
                if low.startswith("portada.") or low == "portada" or low.startswith("portada_"):
                    portada_path = os.path.join(images_dir, name)
                    break
            # Si no se encontró, tomar cualquier imagen válida dentro de la carpeta
            if portada_path is None:
                for name in os.listdir(images_dir):
                    if name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                        portada_path = os.path.join(images_dir, name)
                        break

        portada_original = None
        if portada_path and os.path.exists(portada_path):
            try:
                # Cargamos el original y lo guardamos para poder reescalar al cambiar modo de pantalla
                portada_original = pygame.image.load(portada_path).convert_alpha()
            except Exception:
                portada_original = None

        # Cargar portada y escalar directamente a 1920x1080 (sin preservación especial de aspect ratio)
        portada_img = None
        portada_original = None
        if portada_path and os.path.exists(portada_path):
            try:
                # Cargar el original con alpha si existe para preservar calidad
                portada_original = pygame.image.load(portada_path).convert_alpha()
            except Exception:
                try:
                    portada_original = pygame.image.load(portada_path).convert()
                except Exception:
                    portada_original = None

        def high_quality_scale(surface, target_w, target_h):
            if surface is None:
                return None
            sw, sh = surface.get_size()
            # Preserve aspect ratio
            scale = min(target_w / sw, target_h / sh)
            new_w = max(1, int(sw * scale))
            new_h = max(1, int(sh * scale))
            try:
                scaled = pygame.transform.smoothscale(surface, (new_w, new_h))
            except Exception:
                scaled = pygame.transform.scale(surface, (new_w, new_h))
            final = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            # Fill with black background to avoid transparent borders
            final.fill((0, 0, 0))
            x = (target_w - new_w) // 2
            y = (target_h - new_h) // 2
            final.blit(scaled, (x, y))
            return final

        if portada_original:
            portada_img = high_quality_scale(portada_original, self.ancho, self.alto)
        else:
            portada_img = None

        # Guardar originales para reescalar al cambiar a fullscreen
        selector_original = None

        # Intentar reproducir música de portada si existe
        if os.path.exists(musica_portada):
            try:
                pygame.mixer.music.load(musica_portada)
                pygame.mixer.music.play(-1)
            except Exception:
                pass

        mostrando_menu = True
        font_title = pygame.font.SysFont(None, 72)
        font_sub = pygame.font.SysFont(None, 32)

        # Datos para la pantalla de selección basada en imagen
        selector_path = None
        # Preferir archivos que indiquen claramente que son para personajes
        for name in os.listdir(images_dir):
            low = name.lower()
            if low.startswith("selectordepersonajes") or "personaje" in low or "personajes" in low:
                selector_path = os.path.join(images_dir, name)
                break
        # Si no hay coincidencias explícitas, buscar archivos que empiecen por 'selector' pero evitar los que indiquen 'map'/'mapas'
        if selector_path is None:
            for name in os.listdir(images_dir):
                low = name.lower()
                if low.startswith("selector") and not ("map" in low or "mapas" in low or "mapa" in low):
                    selector_path = os.path.join(images_dir, name)
                    break

        selector_img = None
        if selector_path and os.path.exists(selector_path):
            try:
                 selector_original = pygame.image.load(selector_path).convert()
                 selector_img = high_quality_scale(selector_original, self.ancho, self.alto)
            except Exception:
                selector_img = None

        # Intentar cargar un selector de mapas (imagen donde el usuario marca regiones para elegir mapa)
        map_selector_path = None
        map_selector_original = None
        # Buscar archivos que empiecen por 'selector_map', 'SelectorDeMapas' u otras variantes, o estén en images/maps/
        image_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
        for name in os.listdir(images_dir):
            low = name.lower()
            # Only consider image files (avoid matching json/other files)
            if not low.endswith(image_exts):
                continue
            if ('selector_map' in low) or ('selectormap' in low) or ('map_selector' in low) or ('selectordemap' in low) or ('selectordemapas' in low):
                map_selector_path = os.path.join(images_dir, name)
                break
        # fallback: buscar en images/maps/
        maps_dir = os.path.join(images_dir, 'maps')
        if map_selector_path is None and os.path.isdir(maps_dir):
            # si hay una imagen llamada selector en maps, úsala; si no, tomar la primera imagen disponible
            for name in os.listdir(maps_dir):
                low = name.lower()
                if low.startswith('selector') or 'selector' in low:
                    map_selector_path = os.path.join(maps_dir, name)
                    break
            if map_selector_path is None:
                for name in os.listdir(maps_dir):
                    if name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                        map_selector_path = os.path.join(maps_dir, name)
                        break

        map_selector_img = None
        if map_selector_path and os.path.exists(map_selector_path):
            try:
                map_selector_original = pygame.image.load(map_selector_path).convert()
                map_selector_img = high_quality_scale(map_selector_original, self.ancho, self.alto)
            except Exception:
                map_selector_img = None

        # Inicializar estructuras para regiones/mapping del selector de mapas (declaradas antes de rescale_assets)
        map_selector_regions = []
        map_selector_mapping = []

        # Detectar regiones (marcos) en la imagen de selector: heurística simple
        # Función para detectar regiones (marcos) en la imagen de selector: heurística simple
        def detect_selector_regions(surf, rects_filename='selector_rects.json'):
            regions = []
            if surf is None:
                return regions
            w, h = surf.get_size()
            # 1. Si existe archivo de rectángulos, cargarlo (archivo configurable)
            rects_path = os.path.join('images', rects_filename)
            if os.path.exists(rects_path):
                try:
                    with open(rects_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for r in data:
                        rx, ry, rw, rh = r
                        regions.append(pygame.Rect(rx, ry, rw, rh))
                    if regions:
                        return regions
                except Exception:
                    pass
                # Build per-character registry from Sprites/ subfolders (SpritesName)
                try:
                    self.char_sprites_by_character = {}
                    roots = []
                    if os.path.isdir('Sprites'):
                        roots.append('Sprites')
                    # Try to import PIL for GIF support if available
                    try:
                        from PIL import Image, ImageSequence
                        pil_available_local = True
                    except Exception:
                        pil_available_local = False

                    if roots:
                        for root in roots:
                            for entry in os.listdir(root):
                                entry_path = os.path.join(root, entry)
                                if not os.path.isdir(entry_path):
                                    continue
                                # infer character name from folder name (strip common prefix 'Sprites')
                                pd = entry
                                try:
                                    lowpd = pd.lower()
                                    if lowpd.startswith('sprites'):
                                        char = pd[len('sprites'):].lstrip('_- ') or pd
                                    elif lowpd.startswith('sprite'):
                                        char = pd[len('sprite'):].lstrip('_- ') or pd
                                    else:
                                        char = pd
                                    # strip non-alpha ends
                                    while char and not char[0].isalpha():
                                        char = char[1:]
                                    while char and not char[-1].isalpha():
                                        char = char[:-1]
                                except Exception:
                                    char = pd
                                if not char:
                                    char = pd
                                try:
                                    char = char[0].upper() + char[1:]
                                except Exception:
                                    pass
                                # ensure registry
                                if char not in self.char_sprites_by_character:
                                    self.char_sprites_by_character[char] = {}
                                    for stt in state_patterns.keys():
                                        self.char_sprites_by_character[char][stt] = {'derecha': [], 'izquierda': [], 'any': []}

                                # scan files in this folder
                                for fname in os.listdir(entry_path):
                                    fpath = os.path.join(entry_path, fname)
                                    if not os.path.isfile(fpath):
                                        continue
                                    low = fname.lower()
                                    # determine direction
                                    if ('derecha' in low or 'derech' in low or '_r' in low or 'right' in low):
                                        dir_key = 'derecha'
                                    elif ('izquierda' in low or 'iquierda' in low or 'izq' in low or '_l' in low or 'left' in low):
                                        dir_key = 'izquierda'
                                    else:
                                        dir_key = 'any'
                                    # determine state
                                    matched_state = None
                                    for st, patterns in state_patterns.items():
                                        for p in patterns:
                                            if p in low:
                                                matched_state = st
                                                break
                                        if matched_state:
                                            break
                                    if not matched_state:
                                        # Try extra heuristics: classify kick-related filenames as 'patear'
                                        try:
                                            if any(k in low for k in ('patad', 'pate', 'kick')):
                                                matched_state = 'patear'
                                        except Exception:
                                            matched_state = None
                                        if not matched_state:
                                            # unknown, skip
                                            continue
                                    # load frames (support GIF via PIL)
                                    frames = []
                                    ext = os.path.splitext(fpath)[1].lower()
                                    if ext == '.gif' and pil_available_local:
                                        try:
                                            img = Image.open(fpath)
                                            for frame in ImageSequence.Iterator(img):
                                                try:
                                                    f = frame.convert('RGBA')
                                                    w, h = f.size
                                                    data = f.tobytes()
                                                    surf = pygame.image.fromstring(data, (w, h), 'RGBA').convert_alpha()
                                                    frames.append(surf)
                                                except Exception:
                                                    continue
                                        except Exception:
                                            frames = []
                                    else:
                                        try:
                                            surf = pygame.image.load(fpath).convert_alpha()
                                            frames = [surf]
                                        except Exception:
                                            frames = []

                                    if frames:
                                        try:
                                            self.char_sprites_by_character[char][matched_state][dir_key].extend(frames)
                                        except Exception:
                                            pass
                except Exception:
                    # per-character registry optional; ignore failures
                    pass
            try:
                px = pygame.PixelArray(surf)
                # Primera estrategia: detectar marcos rojos (bordes marcados en la imagen)
                def detect_red_frames():
                    visited = [[False]*h for _ in range(w)]
                    comps = []
                    for x in range(w):
                        for y in range(h):
                            if visited[x][y]:
                                continue
                            col = px[x, y]
                            r = (col >> 16) & 0xFF
                            g = (col >> 8) & 0xFF
                            b = col & 0xFF
                            # heurística para rojo brillante usado en tu imagen
                            if r >= 180 and g <= 80 and b <= 80:
                                # BFS para componente conectada (4-neighbors)
                                stack = [(x, y)]
                                visited[x][y] = True
                                minx, maxx = x, x
                                miny, maxy = y, y
                                while stack:
                                    cx, cy = stack.pop()
                                    # expand bounds
                                    if cx < minx: minx = cx
                                    if cx > maxx: maxx = cx
                                    if cy < miny: miny = cy
                                    if cy > maxy: maxy = cy
                                    for nx in (cx-1, cx+1):
                                        if 0 <= nx < w and not visited[nx][cy]:
                                            coln = px[nx, cy]
                                            rn = (coln >> 16) & 0xFF
                                            gn = (coln >> 8) & 0xFF
                                            bn = coln & 0xFF
                                            if rn >= 180 and gn <= 80 and bn <= 80:
                                                visited[nx][cy] = True
                                                stack.append((nx, cy))
                                    for ny in (cy-1, cy+1):
                                        if 0 <= ny < h and not visited[cx][ny]:
                                            coln = px[cx, ny]
                                            rn = (coln >> 16) & 0xFF
                                            gn = (coln >> 8) & 0xFF
                                            bn = coln & 0xFF
                                            if rn >= 180 and gn <= 80 and bn <= 80:
                                                visited[cx][ny] = True
                                                stack.append((cx, ny))
                                comps.append((minx, miny, maxx, maxy))
                            else:
                                visited[x][y] = True
                    # Compactar bounding boxes y generar rects
                    rects = []
                    for (minx, miny, maxx, maxy) in comps:
                        # añadir padding pequeño para incluir el interior
                        pad = 6
                        rx = max(0, minx - pad)
                        ry = max(0, miny - pad)
                        rw = min(w, maxx + pad) - rx
                        rh = min(h, maxy + pad) - ry
                        if rw > 20 and rh > 20:
                            rects.append([rx, ry, rw, rh])
                    return rects

                red_rects = detect_red_frames()
                if red_rects:
                    # Guardar los rects detectados para uso futuro
                    try:
                        with open(rects_path, 'w', encoding='utf-8') as f:
                            json.dump(red_rects, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                    del px
                    return [pygame.Rect(*r) for r in red_rects]
                # fallback after red frames: contar columnas/filas oscuras
                col_counts = [0] * w
                row_counts = [0] * h
                for x in range(w):
                    c = 0
                    for y in range(h):
                        col = px[x, y]
                        # extraer rgb
                        r = (col >> 16) & 0xFF
                        g = (col >> 8) & 0xFF
                        b = col & 0xFF
                        if (r + g + b) < (255 * 3 * 0.9):
                            c += 1
                    col_counts[x] = c
                for y in range(h):
                    c = 0
                    for x in range(w):
                        col = px[x, y]
                        r = (col >> 16) & 0xFF
                        g = (col >> 8) & 0xFF
                        b = col & 0xFF
                        if (r + g + b) < (255 * 3 * 0.9):
                            c += 1
                    row_counts[y] = c
                del px

                # detectar runs de columnas oscuras (bordes)
                def detect_runs(counts, length, min_density=0.05):
                    runs = []
                    thresh = int(length * min_density)
                    in_run = False
                    start = 0
                    for i, v in enumerate(counts):
                        if v >= thresh and not in_run:
                            in_run = True
                            start = i
                        elif v < thresh and in_run:
                            in_run = False
                            runs.append((start, i - 1))
                    if in_run:
                        runs.append((start, len(counts) - 1))
                    return runs

                col_runs = detect_runs(col_counts, h, min_density=0.08)
                row_runs = detect_runs(row_counts, w, min_density=0.02)

                # si encontramos bordes verticales, construir intervalos entre ellos
                vert_edges = []
                for s, e in col_runs:
                    vert_edges.append((s + e) // 2)
                horiz_edges = []
                for s, e in row_runs:
                    horiz_edges.append((s + e) // 2)

                # si no hay edges suficientes, fallback a grid
                if len(vert_edges) >= 2 and len(horiz_edges) >= 2:
                    xs = sorted(vert_edges)
                    ys = sorted(horiz_edges)
                    # regiones entre edges adyacentes
                    for i in range(len(xs) - 1):
                        for j in range(len(ys) - 1):
                            rx = xs[i]
                            rw = xs[i + 1] - rx
                            ry = ys[j]
                            rh = ys[j + 1] - ry
                            rect = pygame.Rect(rx, ry, rw, rh)
                            # filtrar rects muy pequeños
                            if rect.width > 40 and rect.height > 40:
                                regions.append(rect)
                else:
                    # Fallback: grid 4x2
                    cols = 4
                    rows = 2
                    cell_w = w // cols
                    cell_h = h // rows
                    for j in range(rows):
                        for i in range(cols):
                            rect = pygame.Rect(i * cell_w + 10, j * cell_h + 10, cell_w - 20, cell_h - 20)
                            regions.append(rect)
            except Exception:
                # en caso de fallo, usar grid 4x2
                cols = 4
                rows = 2
                cell_w = surf.get_width() // cols
                cell_h = surf.get_height() // rows
                for j in range(rows):
                    for i in range(cols):
                        rect = pygame.Rect(i * cell_w + 10, j * cell_h + 10, cell_w - 20, cell_h - 20)
                        regions.append(rect)
            return regions

        # helper para reescalar assets y volver a detectar regiones y mapping
        is_fullscreen = False
        def rescale_assets(target_w, target_h):
            nonlocal portada_img, selector_img, selector_regions, selector_mapping
            nonlocal map_selector_original, map_selector_img, map_selector_regions, map_selector_mapping
            if portada_original:
                portada_img = high_quality_scale(portada_original, target_w, target_h)
            else:
                portada_img = None
            if selector_original:
                selector_img = high_quality_scale(selector_original, target_w, target_h)
            else:
                selector_img = None
            if map_selector_original:
                map_selector_img = high_quality_scale(map_selector_original, target_w, target_h)
            else:
                map_selector_img = None
            # recalcular regiones y mapping
            selector_regions = detect_selector_regions(selector_img, 'selector_rects.json')
            # reasignar nombres manteniendo orden visual. Preferir el manifest `selector_map.json`
            default_nombres = ["David", "Daniel", "Santi", "Esteban", "Osu", "Mathi", "Ivan", "Park"]
            selector_mapping = []
            if selector_regions:
                def sort_key(r):
                    return (r.top // 10, r.left)
                regiones_ordenadas = sorted(selector_regions, key=sort_key)
                # intentar leer un mapping persistente (orden deseado) desde images/selector_map.json
                map_path = os.path.join(images_dir, 'selector_map.json')
                map_names = None
                try:
                    if os.path.exists(map_path):
                        with open(map_path, 'r', encoding='utf-8') as mf:
                            data_names = json.load(mf)
                            if isinstance(data_names, list) and data_names:
                                map_names = data_names
                except Exception:
                    map_names = None

                for i, rect in enumerate(regiones_ordenadas):
                    if map_names and i < len(map_names):
                        selector_mapping.append((rect, map_names[i]))
                    elif i < len(default_nombres):
                        selector_mapping.append((rect, default_nombres[i]))
                    else:
                        selector_mapping.append((rect, f"Extra_{i}"))
                # Si sólo se detectaron 7 rects (falta Park), crear una nueva hitbox a la derecha
                try:
                    if len(selector_mapping) == 7:
                        last_rect = regiones_ordenadas[-1]
                        if len(regiones_ordenadas) >= 2:
                            dx = regiones_ordenadas[-1].left - regiones_ordenadas[-2].left
                        else:
                            dx = last_rect.width + 20
                        new_rect = pygame.Rect(last_rect.left + dx, last_rect.top, last_rect.width, last_rect.height)
                        selector_mapping.append((new_rect, "Park"))
                except Exception:
                    pass
                # intentar guardar manifest
                try:
                    manifest_path = os.path.join(images_dir, 'selector_map.json')
                    mapa = [name for _, name in selector_mapping]
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(mapa, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            # recalcular regiones para selector de mapas si existe (archivo de rects separado)
            map_selector_regions = detect_selector_regions(map_selector_img, 'map_selector_rects.json')
            map_selector_mapping = []
            if map_selector_regions:
                def sort_key_map(r):
                    return (r.top // 10, r.left)
                regiones_map = sorted(map_selector_regions, key=sort_key_map)
                # Nombres fijos para los tres primeros mapas
                map_names = ["Citec", "Plazoleta", "Cantina"]
                for i, rect in enumerate(regiones_map):
                    if i < len(map_names):
                        map_selector_mapping.append((rect, map_names[i]))
                    else:
                        map_selector_mapping.append((rect, f"Mapa {i+1}"))
            return selector_img, selector_regions, selector_mapping

        # Inicializar regiones y mapping usando el tamaño actual de la pantalla
        selector_regions = detect_selector_regions(selector_img, 'selector_rects.json')
        # asignación inicial (orden exacto según imagen suministrada)
        # incluir 'Park' (nuevo personaje) como octavo nombre
            # default order (used if no selector_map.json present)
        default_nombres = ["David", "Daniel", "Santi", "Esteban", "Osu", "Mathi", "Ivan", "Park"]
        selector_mapping = []
        if selector_regions:
            def sort_key(r):
                return (r.top // 10, r.left)
            regiones_ordenadas = sorted(selector_regions, key=sort_key)
            # Preferir el manifest `selector_map.json` si existe para forzar el orden
            map_path = os.path.join(images_dir, 'selector_map.json')
            map_names = None
            try:
                if os.path.exists(map_path):
                    with open(map_path, 'r', encoding='utf-8') as mf:
                        data_names = json.load(mf)
                        if isinstance(data_names, list) and data_names:
                            map_names = data_names
            except Exception:
                map_names = None

            for i, rect in enumerate(regiones_ordenadas):
                if map_names and i < len(map_names):
                    selector_mapping.append((rect, map_names[i]))
                elif i < len(default_nombres):
                    selector_mapping.append((rect, default_nombres[i]))
                else:
                    selector_mapping.append((rect, f"Extra_{i}"))
            # Si sólo se detectaron 7 rects (falta Park), crear una nueva hitbox a la derecha
            try:
                if len(selector_mapping) == 7:
                    last_rect = regiones_ordenadas[-1]
                    if len(regiones_ordenadas) >= 2:
                        dx = regiones_ordenadas[-1].left - regiones_ordenadas[-2].left
                    else:
                        dx = last_rect.width + 20
                    new_rect = pygame.Rect(last_rect.left + dx, last_rect.top, last_rect.width, last_rect.height)
                    selector_mapping.append((new_rect, "Park"))
            except Exception:
                pass

        # Inicializar selector de mapas (regiones/mapping). Se rellenará si existe una imagen de selector de mapas
        map_selector_img = map_selector_img if 'map_selector_img' in locals() else None
        map_selector_regions = []
        map_selector_mapping = []
        map_hitboxes = []  # lista de (pygame.Rect, name) con tamaño fijo para selección
        selected_map = None
        selected_map_name = None
        # tamaño fijo solicitado: 90x60 (w x h)  -> aumentado al triple del ancho original (30 -> 90)
        hit_w, hit_h = 295, 170
        if map_selector_img:
            map_selector_regions = detect_selector_regions(map_selector_img, 'map_selector_rects.json')
            def sort_key_map(r):
                return (r.top // 10, r.left)
            regiones_map = sorted(map_selector_regions, key=sort_key_map)
            # Nombres fijos para los tres primeros mapas
            map_names = ["Citec", "Plazoleta", "Cantina"]
            for i, rect in enumerate(regiones_map):
                if i < len(map_names):
                    name = map_names[i]
                else:
                    name = f"Mapa {i+1}"
                map_selector_mapping.append((rect, name))
                # crear hitbox centralizada sobre el rect detectado con tamaño fijo
                # desplazar verticalmente hacia abajo +30px
                # NOTA: sólo aplicamos desplazamientos horizontales finos a mapas específicos
                cx, cy = rect.centerx, rect.centery + 30
                if name == "Cantina":
                    cx -= 15
                elif name == "Citec":
                    cx += 15
                hb = pygame.Rect(int(cx - hit_w//2), int(cy - hit_h//2), hit_w, hit_h)
                map_hitboxes.append((hb, name))
        else:
            # fallback: crear una grid de hitboxes en la imagen si no se detectaron regiones
            # intentamos usar el tamaño de la imagen para distribuir zonas
            try:
                mw, mh = map_selector_img.get_size()
            except Exception:
                mw, mh = self.ancho, self.alto
            cols = 4
            rows = 2
            # Reducir la separación entre hitboxes de la grid en 10px
            cell_w = max(1, mw // cols - 10)
            cell_h = max(1, mh // rows - 10)
            for j in range(rows):
                for i in range(cols):
                    # desplazar verticalmente +30px para la grid de fallback
                    cx = i * cell_w + cell_w // 2
                    cy = j * cell_h + cell_h // 2 + 30
                    # ajustar sólo 'Cantina' o 'Citec' en la fallback si coincide por nombre
                    name = f"Mapa {j*cols + i + 1}"
                    if name == "Cantina":
                        cx -= 15
                    elif name == "Citec":
                        cx += 15
                    hb = pygame.Rect(int(cx - hit_w//2), int(cy - hit_h//2), hit_w, hit_h)
                    map_hitboxes.append((hb, name))
        # Debug flag to print hitboxes once
        _map_rects_printed = False

        # Ensure hitboxes are hidden when opening the menu (user can still toggle with H)
        # This forces them hidden at menu start even if the attribute existed previously.
        self.mostrar_hitbox = False
        # Separate flag to control visibility of map-selection hitboxes (hidden by default)
        # This keeps map selection clean while still allowing selection logic to work.
        if not hasattr(self, 'mostrar_map_hitbox'):
            self.mostrar_map_hitbox = False

        seleccion_p1 = None  # will hold dict {'name': str, 'pos': (x,y)}
        seleccion_p2 = None
        hovered_region = None
        mouse_pos = (0, 0)
        menu_stage = "portada"  # 'portada' -> 'selector' -> salir

        while mostrando_menu:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_RETURN:
                        # Si estamos en portada, avanzar al selector; si en selector, iniciar
                        if menu_stage == "portada":
                            menu_stage = "selector"
                        else:
                            mostrando_menu = False
                    elif evento.key == pygame.K_F11:
                        # Toggle fullscreen
                        info = pygame.display.Info()
                        if not is_fullscreen:
                            # cambiar a fullscreen a resolución del monitor
                            self.ancho, self.alto = info.current_w, info.current_h
                            self.pantalla = pygame.display.set_mode((self.ancho, self.alto), pygame.FULLSCREEN)
                            is_fullscreen = True
                            rescale_assets(self.ancho, self.alto)
                        else:
                            # volver a ventana
                            self.ancho, self.alto = windowed_w, windowed_h
                            self.pantalla = pygame.display.set_mode((self.ancho, self.alto))
                            is_fullscreen = False
                            rescale_assets(self.ancho, self.alto)
                    elif evento.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif evento.key == pygame.K_h:
                        # Alternar visibilidad de hitboxes en el selector
                        try:
                            self.mostrar_hitbox = not self.mostrar_hitbox
                            # Al alternar, recargar rects por si se editaron externamente
                            try:
                                rescale_assets(self.ancho, self.alto)
                            except Exception:
                                pass
                        except Exception:
                            self.mostrar_hitbox = False
                    elif evento.key == pygame.K_r:
                        # Recargar manifest de rects y reasignar mapping en caliente
                        try:
                            # rescale_assets recalcula selector_regions y selector_mapping
                            rescale_assets(self.ancho, self.alto)
                            print("DEBUG: selector_rects recargados desde images/selector_rects.json")
                        except Exception:
                            print("DEBUG: fallo al recargar selector_rects.json")

                # Manejo del mouse
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    mx, my = evento.pos
                    if menu_stage == "portada":
                        # Click en la portada avanza al selector
                        menu_stage = "selector"
                    elif menu_stage == "selector":
                        # Registro de selección usando los pequeños hitboxes rojos (120x200)
                        clicked_pair = None
                        try:
                            # Construir la misma secuencia de hitboxes que se dibuja (fila con offset)
                            small_w, small_h = 120, 200
                            # Keep the order from selector_mapping (which may be forced by selector_map.json)
                            ordenadas = list(selector_mapping)
                            if ordenadas:
                                # construir fila de hitboxes con spacing consistente
                                # start layout from the minimum detected left to keep boxes near the image
                                min_left = min(r.left for r, _ in ordenadas)
                                current_x = min_left
                                avg_cy = int(sum(r.centery for r, _ in ordenadas) / len(ordenadas))
                                spacing = 38
                                small_offset_x = 40  # desplazar las hitboxes visuales/clickables 30px a la derecha
                                small_list = []
                                for rect, name in ordenadas:
                                    hb = pygame.Rect(int(current_x + small_offset_x), int(avg_cy - small_h // 2), small_w, small_h)
                                    small_list.append((hb, name))
                                    current_x += small_w + spacing
                                # comprobar colisión contra los hitboxes pequeños
                                for hb, name in small_list:
                                    if hb.collidepoint((mx, my)):
                                        clicked_pair = (hb, name)
                                        break
                        except Exception:
                            clicked_pair = None

                        if clicked_pair:
                            hb, name = clicked_pair
                            cx = hb.centerx
                            cy = hb.centery
                            if seleccion_p1 is None:
                                seleccion_p1 = {'name': name, 'pos': (cx, cy)}
                            elif seleccion_p2 is None:
                                # evitar seleccionar el mismo personaje dos veces
                                if seleccion_p1['name'] != name:
                                    seleccion_p2 = {'name': name, 'pos': (cx, cy)}
                        else:
                            # Click fuera de regiones: comprobar si se pulsó el botón Iniciar
                            # Botón 'Iniciar' estará en la parte inferior central
                            btn_w, btn_h = 220, 56
                            btn_x = (self.ancho - btn_w) // 2
                            btn_y = self.alto - 120
                            if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h:
                                # solo avanzar si ambos seleccionados
                                if seleccion_p1 and seleccion_p2:
                                    # si existe un selector de mapas, avanzar a esa etapa; si no, iniciar pelea
                                    if map_selector_img is not None:
                                        menu_stage = 'map_selector'
                                    else:
                                        mostrando_menu = False
                    elif menu_stage == 'map_selector':
                        # seleccionar mapa por hitboxes (solo uno)
                        clicked_pair = None
                        for hb, name in map_hitboxes:
                            if hb.collidepoint((mx, my)):
                                clicked_pair = (hb, name)
                                break
                        if clicked_pair:
                            hb, name = clicked_pair
                            cx = hb.centerx
                            cy = hb.centery
                            # seleccionar sólo uno (reemplaza selección anterior)
                            selected_map = {'name': name, 'pos': (cx, cy)}
                            selected_map_name = name
                        else:
                            # Click fuera de hitboxes: comprobar si se pulsó el botón Iniciar
                            btn_w, btn_h = 220, 56
                            btn_x = (self.ancho - btn_w) // 2
                            btn_y = self.alto - 120
                            if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h:
                                if selected_map:
                                    mostrando_menu = False

                if evento.type == pygame.MOUSEMOTION:
                    mouse_pos = evento.pos
                    # actualizar hovered_region según la etapa actual
                    hovered_region = None
                    mx, my = mouse_pos
                    if menu_stage == 'selector':
                        try:
                            # Hover based on the same small hitboxes used for selection (centered on rect.centerx)
                            small_w, small_h = 120, 200
                            # Keep the order from selector_mapping for hover detection
                            ordenadas = list(selector_mapping)
                            if ordenadas:
                                # construir fila de hitboxes con spacing consistente para hover
                                min_left = min(r.left for r, _ in ordenadas)
                                current_x = min_left
                                avg_cy = int(sum(r.centery for r, _ in ordenadas) / len(ordenadas))
                                spacing = 38
                                small_offset_x = 40
                                for rect, name in ordenadas:
                                    hb = pygame.Rect(int(current_x + small_offset_x), int(avg_cy - small_h // 2), small_w, small_h)
                                    if hb.collidepoint((mx, my)):
                                        hovered_region = (hb, name)
                                        break
                                    current_x += small_w + spacing
                        except Exception:
                            hovered_region = None
                    elif menu_stage == 'map_selector':
                        for hb, name in map_hitboxes:
                            if hb.collidepoint((mx, my)):
                                hovered_region = (hb, name)
                                break
                    # No seleccionar automáticamente por hover; hovered_region ya se actualizó arriba
                # (La detección de maximizar se realiza más abajo comparando el tamaño de la ventana con la resolución del monitor.)

            # Dibujar menú (ventana fija)
            if menu_stage == "portada":
                if portada_img:
                    # Mostrar la portada centrada/escala con la máxima calidad posible
                    self.pantalla.blit(portada_img, (0, 0))
                else:
                    self.pantalla.fill((10, 10, 40))
                    title = font_title.render("CPF Kombat", True, (255, 220, 0))
                    self.pantalla.blit(title, ((self.ancho - title.get_width()) // 2, 120))
                # No mostrar texto encima de la portada según tu instrucción

            elif menu_stage == "selector":
                # Mostrar la imagen del selector (si existe) y permitir seleccionar dos posiciones
                if selector_img:
                    self.pantalla.blit(selector_img, (0, 0))
                else:
                    self.pantalla.fill((30, 30, 30))
                    info_text = font_sub.render("No hay imagen de selector en images/", True, (255, 255, 255))
                    self.pantalla.blit(info_text, info_text.get_rect(center=(self.ancho//2, self.alto//2)))

                # No dibujar outline de regiones

                # Mostrar texto de turno de selección (Jugador 1/Jugador 2)
                # Parpadeo: mostrar texto solo si el tiempo es par (cada ~500ms)
                show_turno = ((pygame.time.get_ticks() // 500) % 2) == 0
                if seleccion_p1 is None:
                    turno_txt = "Jugador 1: selecciona tu personaje"
                    if show_turno:
                        turno_surf = font_sub.render(turno_txt, True, (255, 255, 255))
                        sx = (self.pantalla.get_width() - turno_surf.get_width()) // 2
                        sy = 30
                        self.pantalla.blit(turno_surf, (sx, sy))
                elif seleccion_p2 is None:
                    turno_txt = "Jugador 2: selecciona tu personaje"
                    if show_turno:
                        turno_surf = font_sub.render(turno_txt, True, (255, 255, 255))
                        sx = (self.pantalla.get_width() - turno_surf.get_width()) // 2
                        sy = 30
                        self.pantalla.blit(turno_surf, (sx, sy))
                else:
                    turno_txt = "Personajes seleccionados"
                    turno_surf = font_sub.render(turno_txt, True, (255, 255, 255))
                    sx = (self.pantalla.get_width() - turno_surf.get_width()) // 2
                    sy = 30
                    self.pantalla.blit(turno_surf, (sx, sy))

                # Mostrar marcadores para selecciones si existen (con nombre)
                if seleccion_p1:
                    pygame.draw.circle(self.pantalla, (0, 200, 0), seleccion_p1['pos'], 20, 4)
                    l = font_sub.render(seleccion_p1['name'], True, (200, 255, 200))
                    self.pantalla.blit(l, (seleccion_p1['pos'][0] - l.get_width()//2, seleccion_p1['pos'][1] + 24))
                if seleccion_p2:
                    pygame.draw.circle(self.pantalla, (200, 0, 0), seleccion_p2['pos'], 20, 4)
                    l2 = font_sub.render(seleccion_p2['name'], True, (255, 200, 200))
                    self.pantalla.blit(l2, (seleccion_p2['pos'][0] - l2.get_width()//2, seleccion_p2['pos'][1] + 24))

                # Botón Iniciar en la parte inferior
                btn_w, btn_h = 220, 56
                btn_x = (self.ancho - btn_w) // 2
                btn_y = self.alto - 120
                btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                ok = (seleccion_p1 is not None and seleccion_p2 is not None)
                pygame.draw.rect(self.pantalla, (30, 120, 30) if ok else (80, 80, 80), btn_rect, 0, border_radius=8)
                pygame.draw.rect(self.pantalla, (0,0,0), btn_rect, 2, border_radius=8)
                btn_text = font_sub.render("Iniciar pelea" if ok else "Selecciona personajes", True, (255,255,255))
                self.pantalla.blit(btn_text, (btn_x + (btn_w - btn_text.get_width())//2, btn_y + (btn_h - btn_text.get_height())//2))

                # Dibujar hitboxes pequeñas del selector si están activadas (toggle con H)
                # Se dibujan cajas pequeñas colocadas en fila horizontal con 10px de separación
                if getattr(self, 'mostrar_hitbox', False):
                    try:
                        # ajustar tamaño de las hitboxes visuales a 120x200 px según petición
                        small_w, small_h = 120, 200
                        # Use the mapping order (which prefers selector_map.json) to label and place boxes
                        ordenadas = list(selector_mapping)
                        if ordenadas:
                            # punto de inicio: la mínima izquierda entre rects
                            min_left = min(r.left for r, _ in ordenadas)
                            current_x = min_left
                            # calcular una Y común (media de los centros) para alinear todas las cajas en la misma línea
                            avg_cy = int(sum(r.centery for r, _ in ordenadas) / len(ordenadas))
                            spacing = 38
                            small_offset_x = 40
                            # reuse a single semi-transparent surface for all small hitboxes
                            if not getattr(self, 'selector_hitbox_surf', None):
                                try:
                                    s_surf = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
                                    s_surf.fill((255, 0, 0, 40))
                                    self.selector_hitbox_surf = s_surf
                                except Exception:
                                    self.selector_hitbox_surf = None
                            for idx, (rect, name) in enumerate(ordenadas):
                                # crear cada caja en fila, empezando en current_x y desplazada small_offset_x
                                hb = pygame.Rect(int(current_x + small_offset_x), int(avg_cy - small_h // 2), small_w, small_h)
                                # relleno semi-transparente para visualizar el área pequeña (reutilizar superficie)
                                if getattr(self, 'selector_hitbox_surf', None):
                                    try:
                                        self.pantalla.blit(self.selector_hitbox_surf, (hb.left, hb.top))
                                    except Exception:
                                        pass
                                else:
                                    try:
                                        surf = pygame.Surface((hb.width, hb.height), pygame.SRCALPHA)
                                        surf.fill((255, 0, 0, 40))
                                        self.pantalla.blit(surf, (hb.left, hb.top))
                                    except Exception:
                                        pass
                                # contorno del hitbox pequeño
                                pygame.draw.rect(self.pantalla, (255, 0, 0), hb, 2)
                                # etiqueta con índice y nombre encima de la caja pequeña
                                try:
                                    lbl = font_sub.render(f"{idx+1}: {name}", True, (255,255,255))
                                    self.pantalla.blit(lbl, (hb.left + 4, hb.top - lbl.get_height() - 2))
                                except Exception:
                                    pass
                                # avanzar X para la siguiente caja dejando spacing px de separación
                                current_x += small_w + spacing
                    except Exception:
                        pass

            elif menu_stage == 'map_selector':
                # Mostrar la imagen del selector de mapas y permitir seleccionar un mapa (solo uno)
                if map_selector_img:
                    self.pantalla.blit(map_selector_img, (0, 0))
                    # Dibujar hitboxes fijas (30x60) y etiquetas ONLY if mostrar_map_hitbox is True
                    try:
                        if getattr(self, 'mostrar_map_hitbox', False):
                            for idx, (hb, name) in enumerate(map_hitboxes):
                                # color: verde si seleccionado, naranja si no
                                if selected_map and selected_map.get('name') == name:
                                    col = (0, 200, 0)
                                else:
                                    col = (255, 160, 40)
                                pygame.draw.rect(self.pantalla, col, hb, 2)
                                lbl = font_sub.render(f"{idx+1}: {name}", True, (255,255,255))
                                # colocar etiqueta encima del hitbox
                                self.pantalla.blit(lbl, (hb.left + 4, hb.top - lbl.get_height() - 2))
                    except Exception:
                        pass
                else:
                    self.pantalla.fill((30, 30, 30))
                    info_text = font_sub.render("No hay imagen de selector de mapas (images/maps/)", True, (255, 255, 255))
                    self.pantalla.blit(info_text, info_text.get_rect(center=(self.ancho//2, self.alto//2)))

                # Texto instructivo
                turno_txt = "Selecciona un mapa"
                turno_surf = font_sub.render(turno_txt, True, (255, 255, 255))
                sx = (self.pantalla.get_width() - turno_surf.get_width()) // 2
                sy = 30
                self.pantalla.blit(turno_surf, (sx, sy))

                # Mostrar marcador del mapa seleccionado (si existe)
                if selected_map:
                    pygame.draw.circle(self.pantalla, (255, 200, 0), selected_map['pos'], 24, 4)
                    l = font_sub.render(selected_map['name'], True, (255, 220, 180))
                    self.pantalla.blit(l, (selected_map['pos'][0] - l.get_width()//2, selected_map['pos'][1] + 28))

                # Print hitboxes una sola vez para debugging en consola
                if not _map_rects_printed:
                    try:
                        print("DEBUG: map_hitboxes:")
                        for i, (hb, name) in enumerate(map_hitboxes):
                            print(f"  {i+1}: rect={hb}, name={name}")
                    except Exception:
                        print("DEBUG: no se pudieron listar map_hitboxes")
                    _map_rects_printed = True

                # Mostrar hovered region (si hay) con un resaltado blanco
                # Only show hover outline if map hitboxes are visible
                if getattr(self, 'mostrar_map_hitbox', False) and hovered_region:
                    rect, name = hovered_region
                    pygame.draw.rect(self.pantalla, (255,255,255), rect, 3)

                # Botón Iniciar en la parte inferior: activo cuando hay selección
                btn_w, btn_h = 220, 56
                btn_x = (self.ancho - btn_w) // 2
                btn_y = self.alto - 120
                btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                ok = (selected_map is not None)
                pygame.draw.rect(self.pantalla, (30, 120, 30) if ok else (80, 80, 80), btn_rect, 0, border_radius=8)
                pygame.draw.rect(self.pantalla, (0,0,0), btn_rect, 2, border_radius=8)
                btn_text = font_sub.render("Iniciar pelea" if ok else "Selecciona un mapa", True, (255,255,255))
                self.pantalla.blit(btn_text, (btn_x + (btn_w - btn_text.get_width())//2, btn_y + (btn_h - btn_text.get_height())//2))

            pygame.display.flip()
            # respect runtime FPS cap toggle: when enabled, throttle to self.fps_cap;
            # when disabled, let tick() run uncapped (no arg). Fallback to self.fps.
            try:
                if getattr(self, 'fps_cap_enabled', True):
                    self.reloj.tick(getattr(self, 'fps_cap', self.fps))
                else:
                    self.reloj.tick()
            except Exception:
                try:
                    self.reloj.tick(self.fps)
                except Exception:
                    pass

        # Si hay música de portada, detenerla antes de iniciar
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        # Guardar mapa seleccionado (si lo hubo) en el objeto para usar durante la pelea
        # Compatibilidad: self.selected_map contiene el nombre (o None)
        self.selected_map = selected_map_name if 'selected_map_name' in locals() and selected_map_name else None
        # Guardar secuencia como una lista de un elemento (si se seleccionó)
        if self.selected_map:
            self.selected_map_sequence = [self.selected_map]
        else:
            self.selected_map_sequence = []

        # Inicializar personajes si no existen
        # Reemplazar nombres con las selecciones si el usuario escogió
        if seleccion_p1:
            self.personaje_p1 = {"nombre": seleccion_p1['name']}
        if seleccion_p2:
            self.personaje_p2 = {"nombre": seleccion_p2['name']}

        # (Re)crear personajes para la pelea usando las selecciones actuales.
        # Siempre recreamos los objetos de Personaje al iniciar una pelea para
        # garantizar que las nuevas selecciones se apliquen.
        suelo_y = self.alto - 50
        # Crear personajes usando los nombres seleccionados (o valores por defecto)
        p1_name = self.personaje_p1.get("nombre", "David")
        p2_name = self.personaje_p2.get("nombre", "Ken")
        # instantiate fresh Personaje objects for this match
        try:
            self.luchador_p1 = Personaje(p1_name, 100, 100, suelo_y, {}, es_jugador1=True)
        except Exception:
            # fallback to a safe default
            self.luchador_p1 = Personaje("David", 100, 100, suelo_y, {}, es_jugador1=True)
        try:
            self.luchador_p2 = Personaje(p2_name, 100, self.ancho - 150, suelo_y, {}, es_jugador1=False)
        except Exception:
            self.luchador_p2 = Personaje("Ken", 100, self.ancho - 150, suelo_y, {}, es_jugador1=False)
        self.grupo_sprites = pygame.sprite.Group(self.luchador_p1, self.luchador_p2)
        self.limite_suelo = suelo_y
        # Reset stickman_state (visual/animation state) so the next match
        # starts with canonical starting positions instead of leftover final positions
        try:
            base_y = self.limite_suelo - 220 - 140
            self.stickman_state = {
                'p1': {'x': 220, 'y': base_y, 'vx': 0, 'vy': 0, 'estado': 'idle', 'mirando_derecha': True, 'anim': 0, 'en_tierra': True},
                'p2': {'x': self.ancho - 220, 'y': base_y, 'vx': 0, 'vy': 0, 'estado': 'idle', 'mirando_derecha': False, 'anim': 0, 'en_tierra': True}
            }
        except Exception:
            # safe fallback: remove stickman_state so later code will reinitialize it
            try:
                delattr(self, 'stickman_state')
            except Exception:
                pass

        # Temporizador de pelea (90 segundos)
        tiempo_total = 90  # segundos
        tiempo_restante = tiempo_total
        tiempo_ultimo_tick = pygame.time.get_ticks()
        # Mostrar logo Fight centrado y pequeño por 1.5 segundos antes de iniciar la pelea
        fight_logo_path = os.path.join('images', 'logos', 'Fight.png')
        fight_logo_scaled = None
        logo_w, logo_h = 900, 300  # tamaño mucho más grande
        logo_x = (self.ancho - logo_w) // 2 + 25  # desplazado 25 px a la derecha
        logo_y = (self.alto - logo_h) // 2
        if os.path.exists(fight_logo_path):
            fight_logo = pygame.image.load(fight_logo_path).convert_alpha()
            fight_logo_scaled = pygame.transform.smoothscale(fight_logo, (logo_w, logo_h))
        pelea_start_time = pygame.time.get_ticks()
        # Duración en pantalla para el logo de Fight y para las imágenes de round (ms)
        fight_logo_duration = 1500
        # Pequeña pausa extra entre el round-logo y la aparición de Fight.png (ms)
        fight_logo_delay_after_round = 100

        # Cargar imágenes de Round1, Round2 y FinalRound desde images/logos/ si existen
        def load_logo_variant(base_name):
            logos_dir = os.path.join('images', 'logos')
            exts = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
            if not os.path.isdir(logos_dir):
                return None
            # Buscar fichero que empiece con base_name (case-insensitive)
            for fname in os.listdir(logos_dir):
                low = fname.lower()
                if low.startswith(base_name.lower()) and any(low.endswith(ext) for ext in exts):
                    try:
                        surf = pygame.image.load(os.path.join(logos_dir, fname)).convert_alpha()
                        try:
                            return pygame.transform.smoothscale(surf, (logo_w, logo_h))
                        except Exception:
                            return pygame.transform.scale(surf, (logo_w, logo_h))
                    except Exception:
                        return None
            return None

        round1_logo_scaled = load_logo_variant('Round1')
        round2_logo_scaled = load_logo_variant('Round2')
        finalround_logo_scaled = load_logo_variant('FinalRound')
        # Helper to load a winner logo: flexible matching for filenames like 'DavidWins.png' or containing 'win'
        def load_winner_logo(name):
            logos_dir = os.path.join('images', 'logos')
            exts = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
            if not os.path.isdir(logos_dir):
                return None
            lname = name.lower() if name else ''
            # Prefer files that start with '<name>win' or '<name>wins'
            for fname in os.listdir(logos_dir):
                low = fname.lower()
                if (low.startswith(lname) and ('win' in low)) and any(low.endswith(ext) for ext in exts):
                    try:
                        surf = pygame.image.load(os.path.join(logos_dir, fname)).convert_alpha()
                        try:
                            return pygame.transform.smoothscale(surf, (logo_w, logo_h))
                        except Exception:
                            return pygame.transform.scale(surf, (logo_w, logo_h))
                    except Exception:
                        return None
            # Fallback: any file that contains the name and 'win'
            for fname in os.listdir(logos_dir):
                low = fname.lower()
                if lname in low and 'win' in low and any(low.endswith(ext) for ext in exts):
                    try:
                        surf = pygame.image.load(os.path.join(logos_dir, fname)).convert_alpha()
                        try:
                            return pygame.transform.smoothscale(surf, (logo_w, logo_h))
                        except Exception:
                            return pygame.transform.scale(surf, (logo_w, logo_h))
                    except Exception:
                        return None
            return None
        # Helper: mostrar primero el logo de Round (según número/estado) y luego el logo Fight
        # NOTE: this function now PRESERVES the already-drawn scene (does not clear or redraw background).
        def show_pre_round_sequence(rnum):
            nonlocal pelea_start_time
            try:
                # elegir cuál logo de round mostrar
                use_surf = None
                if rnum == 1:
                    use_surf = round1_logo_scaled
                else:
                    # si ambos tienen 1, preferimos FinalRound
                    if rounds_won.get('p1', 0) == 1 and rounds_won.get('p2', 0) == 1:
                        use_surf = finalround_logo_scaled
                    else:
                        use_surf = round2_logo_scaled

                # No redibujar el fondo ni los luchadores: asumimos la escena ya está dibujada debajo.
                if use_surf:
                    self.pantalla.blit(use_surf, (logo_x, logo_y))
                    pygame.display.flip()
                # esperar la misma duración que Fight.png
                pygame.time.wait(fight_logo_duration)

                # Después de mostrar el round-logo, marcar el tiempo de inicio de la pelea
                # para que el bucle principal muestre Fight.png tras una pequeña pausa.
                pelea_start_time = pygame.time.get_ticks() + fight_logo_delay_after_round
            except Exception:
                # en caso de fallo, simplemente esperar la duración total
                pygame.time.wait(fight_logo_duration * 2)
    
        # Cargar fondo del mapa seleccionado (si existe)
        fight_bg = None
        if hasattr(self, 'selected_map') and self.selected_map:
            maps_dir = os.path.join('images', 'maps')
            name = self.selected_map
            # posibles extensiones
            exts = ['.jpg', '.jpeg', '.png', '.bmp']
            found = None
            # Especial: buscar en la carpeta top-level 'mapas' primero (case-insensitive, varias extensiones)
            try:
                mapas_dir = 'mapas'
                if os.path.isdir(mapas_dir):
                    for fname in os.listdir(mapas_dir):
                        low = fname.lower()
                        if low.startswith(name.lower()) and any(low.endswith(e) for e in exts):
                            found = os.path.join(mapas_dir, fname)
                            break
            except Exception:
                pass
            # buscar en images/maps/<name>.* (case-insensitive)
            if os.path.isdir(maps_dir):
                for ext in exts:
                    candidate = os.path.join(maps_dir, f"{name}{ext}")
                    if os.path.exists(candidate):
                        found = candidate
                        break
                # intentar versiones con mayúsculas/minúsculas si no se encontró
                if not found:
                    for fname in os.listdir(maps_dir):
                        if fname.lower().startswith(name.lower()):
                            if any(fname.lower().endswith(e) for e in exts):
                                found = os.path.join(maps_dir, fname)
                                break
            # fallback: buscar en images/
            if not found:
                for ext in exts:
                    candidate = os.path.join('images', f"{name}{ext}")
                    if os.path.exists(candidate):
                        found = candidate
                        break
            if found:
                try:
                    bg_orig = pygame.image.load(found).convert()
                    # Si el mapa seleccionado es Citec, estiramos a toda la pantalla (llenar sin preservar aspect ratio)
                    if name.lower() == 'citec':
                        try:
                            fight_bg = pygame.transform.smoothscale(bg_orig, (self.ancho, self.alto))
                        except Exception:
                            fight_bg = pygame.transform.scale(bg_orig, (self.ancho, self.alto))
                    else:
                        fight_bg = high_quality_scale(bg_orig, self.ancho, self.alto)
                except Exception:
                    fight_bg = None
        # Preparar conteo de rounds: mejor de 3 (primero a 2 wins)
        # Cargar sprites genéricos (si existen) para usar en lugar de dibujar stickmen
        try:
            # Build a mapping: char_sprites[state] = {'derecha': frames, 'izquierda': frames, 'any': frames}
            self.char_sprites = {}
            # Define patterns for states to match filenames
            state_patterns = {
                'idle': ['idle', 'stand'],
                # include a broad 'camin' substring to catch typos like 'caminataz'
                'caminar': ['camin', 'camina', 'caminar', 'caminata', 'walk'],
                'pegar': ['puñet', 'pegar', 'punch', 'hit'],
                'patear': ['pate', 'patear', 'patad', 'patada', 'kick'],
                'agacharse': ['agach', 'agacharse', 'crouch'],
                'saltar': ['salt', 'saltar', 'jump']
            }
            # Try to import PIL for GIF frame extraction; fall back if not available
            try:
                from PIL import Image, ImageSequence
                pil_available = True
            except Exception:
                pil_available = False

            # Initialize empty dicts and a record of filenames assigned
            loaded_files = {}
            for st in state_patterns.keys():
                self.char_sprites[st] = {'derecha': [], 'izquierda': [], 'any': []}
                loaded_files[st] = {'derecha': [], 'izquierda': [], 'any': []}

            if os.path.isdir('sprites'):
                for fname in os.listdir('sprites'):
                    low = fname.lower()
                    fpath = os.path.join('sprites', fname)
                    # detect direction tag in filename (robust to common typos)
                    dir_key = None
                    if ('derecha' in low or 'derech' in low or '_r' in low or 'right' in low):
                        dir_key = 'derecha'
                    elif ('izquierda' in low or 'iquierda' in low or 'izq' in low or '_l' in low or 'left' in low):
                        dir_key = 'izquierda'
                    else:
                        # fallback: if filename contains hints of left/right despite not matching exactly
                        if any(k in low for k in ('iquierda','izquierda','izq','left')):
                            dir_key = 'izquierda'
                        elif any(k in low for k in ('derech','derecha','right','_r')):
                            dir_key = 'derecha'
                        else:
                            dir_key = 'any'

                    # find state by pattern
                    matched_state = None
                    for st, patterns in state_patterns.items():
                        for p in patterns:
                            if p in low:
                                matched_state = st
                                break
                        if matched_state:
                            break

                    if not matched_state:
                        # unknown file, skip
                        continue

                    frames = []
                    ext = os.path.splitext(fpath)[1].lower()
                    if ext == '.gif' and pil_available:
                        try:
                            img = Image.open(fpath)
                            for frame in ImageSequence.Iterator(img):
                                try:
                                    f = frame.convert('RGBA')
                                    w, h = f.size
                                    data = f.tobytes()
                                    surf = pygame.image.fromstring(data, (w, h), 'RGBA').convert_alpha()
                                    frames.append(surf)
                                except Exception:
                                    continue
                        except Exception:
                            frames = []
                    else:
                        try:
                            surf = pygame.image.load(fpath).convert_alpha()
                            frames = [surf]
                        except Exception:
                            frames = []

                    if frames:
                        self.char_sprites[matched_state][dir_key].extend(frames)
                        loaded_files[matched_state][dir_key].append(fname)

            # If no direction-specific frames, but 'any' exists, keep as-is. We'll fallback to flipping when needed.
            # Build scaled+flipped cache for common target heights to avoid per-frame scaling
            try:
                self.char_sprites_cache = {}
                target_heights = [360, 220]
                for st in state_patterns.keys():
                    self.char_sprites_cache[st] = {'derecha': {}, 'izquierda': {}, 'any': {}}
                    for dk in ('derecha','izquierda','any'):
                        frames = self.char_sprites[st].get(dk, [])
                        for h_t in target_heights:
                            scaled_list = []
                            for f in frames:
                                try:
                                    fh = f.get_height()
                                    fw = f.get_width()
                                    if fh > 0:
                                        scale = h_t / float(fh)
                                        s2 = pygame.transform.smoothscale(f, (int(fw * scale), int(fh * scale)))
                                    else:
                                        s2 = f
                                except Exception:
                                    s2 = f
                                scaled_list.append(s2)
                            self.char_sprites_cache[st][dk][h_t] = scaled_list

                # Precompute masks and bounding rects for cached scaled frames to
                # avoid creating masks every frame (expensive). Store parallel
                # structures: char_sprites_masks_cache and char_sprites_bounds_cache.
                try:
                    self.char_sprites_masks_cache = {}
                    self.char_sprites_bounds_cache = {}
                    for stt in list(self.char_sprites_cache.keys()):
                        self.char_sprites_masks_cache[stt] = {'derecha': {}, 'izquierda': {}, 'any': {}}
                        self.char_sprites_bounds_cache[stt] = {'derecha': {}, 'izquierda': {}, 'any': {}}
                        for dk in ('derecha','izquierda','any'):
                            for h_t, frames_list in (self.char_sprites_cache.get(stt, {}).get(dk, {}) or {}).items():
                                masks = []
                                rects = []
                                for surf in frames_list:
                                    try:
                                        m = pygame.mask.from_surface(surf)
                                        masks.append(m)
                                        try:
                                            br = m.get_bounding_rect()
                                        except Exception:
                                            # older pygame may have get_bounding_rects
                                            try:
                                                brs = m.get_bounding_rects()
                                                if brs:
                                                    btemp = brs[0].copy()
                                                    for r in brs[1:]:
                                                        btemp.union_ip(r)
                                                    br = btemp
                                                else:
                                                    br = surf.get_rect()
                                            except Exception:
                                                br = surf.get_rect()
                                    except Exception:
                                        masks.append(None)
                                        br = surf.get_rect()
                                    try:
                                        rects.append(pygame.Rect(int(br.left), int(br.top), int(br.width), int(br.height)))
                                    except Exception:
                                        rects.append(surf.get_rect())
                                self.char_sprites_masks_cache[stt][dk][h_t] = masks
                                self.char_sprites_bounds_cache[stt][dk][h_t] = rects
                except Exception:
                    # if mask precompute fails, leave caches absent and fall back to runtime masks
                    if hasattr(self, 'char_sprites_masks_cache'):
                        try:
                            del self.char_sprites_masks_cache
                        except Exception:
                            pass
                    if hasattr(self, 'char_sprites_bounds_cache'):
                        try:
                            del self.char_sprites_bounds_cache
                        except Exception:
                            pass

                    # Fill missing direction caches from 'any' only.
                    # IMPORTANT: do NOT auto-generate flipped frames from the opposite
                    # direction. This preserves directional intent: when 'izquierda' is
                    # requested we will only use true left-facing frames (or 'any').
                    for h_t in target_heights:
                        any_list = self.char_sprites_cache[st]['any'].get(h_t, [])
                        right_list = self.char_sprites_cache[st]['derecha'].get(h_t, [])
                        left_list = self.char_sprites_cache[st]['izquierda'].get(h_t, [])
                        # if derecha missing but any exists -> use any (no flipping)
                        if not right_list and any_list:
                            self.char_sprites_cache[st]['derecha'][h_t] = list(any_list)
                        # if izquierda missing but any exists -> use any (no flipping)
                        if not left_list and any_list:
                            self.char_sprites_cache[st]['izquierda'][h_t] = list(any_list)
                        # Do NOT populate missing direction from the opposite side by flipping.
                        # This ensures left-key uses left sprites only.

                # Detailed debug: list global sprites, per-character sprites (Sprites/), and cache summary
                try:
                    lines = []
                    print("DEBUG: sprite mapping (global 'sprites' folder):")
                    lines.append("DEBUG: sprite mapping (global 'sprites' folder):")
                    for st in state_patterns.keys():
                        for dk in ('derecha','izquierda','any'):
                            files = loaded_files.get(st, {}).get(dk, [])
                            if files:
                                msg = f"  {st:<12} {dk:<9}: {files}"
                                print(msg)
                                lines.append(msg)

                    # Also list sprites found per-character under 'Sprites/'
                    sprites_root = 'Sprites'
                    if os.path.isdir(sprites_root):
                        print("DEBUG: sprites por personaje (carpeta 'Sprites'):")
                        lines.append("DEBUG: sprites por personaje (carpeta 'Sprites'):")
                        sprites_by_char = {}
                        for sub in sorted(os.listdir(sprites_root)):
                            subp = os.path.join(sprites_root, sub)
                            if not os.path.isdir(subp):
                                continue
                            # infer character name by stripping 'sprites' prefix if present
                            pname = sub
                            low = pname.lower()
                            if low.startswith('sprites'):
                                pname = pname[len('sprites'):].strip('_- ') or sub
                            pname = pname.strip('_- ')
                            pname = pname.capitalize() if pname else sub
                            sprites_by_char[pname] = {}
                            for fname in sorted(os.listdir(subp)):
                                lowf = fname.lower()
                                # detect state
                                matched_state = None
                                for st, patterns in state_patterns.items():
                                    if any(p in lowf for p in patterns):
                                        matched_state = st
                                        break
                                dir_key = 'any'
                                if ('derecha' in lowf or 'derech' in lowf or '_r' in lowf or 'right' in lowf):
                                    dir_key = 'derecha'
                                elif ('izquierda' in lowf or 'iquierda' in lowf or 'izq' in lowf or '_l' in lowf or 'left' in lowf):
                                    dir_key = 'izquierda'
                                key_state = matched_state or 'unknown'
                                sprites_by_char[pname].setdefault(key_state, {}).setdefault(dir_key, []).append(fname)
                        for pname, mapping in sprites_by_char.items():
                            header = f"  Personaje: {pname}"
                            print(header)
                            lines.append(header)
                            for st, dirs in mapping.items():
                                for dk, files in dirs.items():
                                    msg = f"    {st:<12} {dk:<9}: {files}"
                                    print(msg)
                                    lines.append(msg)
                    else:
                        msg = "DEBUG: no existe la carpeta 'Sprites' para sprites por personaje."
                        print(msg)
                        lines.append(msg)

                    # Summary of scaled cache
                    if hasattr(self, 'char_sprites_cache'):
                        print("DEBUG: char_sprites_cache summary (states -> dir -> heights with frames):")
                        lines.append("DEBUG: char_sprites_cache summary (states -> dir -> heights with frames):")
                        for st in sorted(self.char_sprites_cache.keys()):
                            try:
                                entries = []
                                for dk in ('derecha','izquierda','any'):
                                    heights = [str(h) for h, lst in (self.char_sprites_cache.get(st, {}).get(dk, {}) or {}).items() if lst]
                                    if heights:
                                        entries.append(f"{dk}({', '.join(heights)})")
                                if entries:
                                    msg = f"  {st}: " + "; ".join(entries)
                                else:
                                    msg = f"  {st}: (no frames cached)"
                                print(msg)
                                lines.append(msg)
                            except Exception:
                                msg = f"  {st}: (error reading cache)"
                                print(msg)
                                lines.append(msg)

                    # Write debug log to file for easier inspection
                    try:
                        logs_dir = 'logs'
                        os.makedirs(logs_dir, exist_ok=True)
                        log_path = os.path.join(logs_dir, 'sprites_debug.txt')
                        with open(log_path, 'w', encoding='utf-8') as lf:
                            lf.write('\n'.join(lines))
                        print(f"DEBUG: sprite log saved to {log_path}")
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                self.char_sprites_cache = {}
        except Exception:
            self.char_sprites = {}
        # Build per-character registry from Sprites/ subfolders (SpritesName)
        try:
            self.char_sprites_by_character = {}
            # Try to import PIL for GIF support if available
            try:
                from PIL import Image, ImageSequence
                pil_available_local = True
            except Exception:
                pil_available_local = False

            sprites_root = 'Sprites'
            if os.path.isdir(sprites_root):
                for entry in sorted(os.listdir(sprites_root)):
                    entry_path = os.path.join(sprites_root, entry)
                    if not os.path.isdir(entry_path):
                        continue
                    # infer character name from folder name (strip common prefix 'Sprites')
                    pd = entry
                    try:
                        lowpd = pd.lower()
                        if lowpd.startswith('sprites'):
                            char = pd[len('sprites'):].lstrip('_- ') or pd
                        elif lowpd.startswith('sprite'):
                            char = pd[len('sprite'):].lstrip('_- ') or pd
                        else:
                            char = pd
                        # strip non-alpha ends
                        while char and not char[0].isalpha():
                            char = char[1:]
                        while char and not char[-1].isalpha():
                            char = char[:-1]
                    except Exception:
                        char = pd
                    if not char:
                        char = pd
                    try:
                        char = char[0].upper() + char[1:]
                    except Exception:
                        pass
                    # ensure registry
                    if char not in self.char_sprites_by_character:
                        self.char_sprites_by_character[char] = {}
                        for stt in state_patterns.keys():
                            self.char_sprites_by_character[char][stt] = {'derecha': [], 'izquierda': [], 'any': []}

                    # scan files in this folder
                    for fname in sorted(os.listdir(entry_path)):
                        fpath = os.path.join(entry_path, fname)
                        if not os.path.isfile(fpath):
                            continue
                        low = fname.lower()
                        # determine direction
                        if ('derecha' in low or 'derech' in low or '_r' in low or 'right' in low):
                            dir_key = 'derecha'
                        elif ('izquierda' in low or 'iquierda' in low or 'izq' in low or '_l' in low or 'left' in low):
                            dir_key = 'izquierda'
                        else:
                            dir_key = 'any'
                        # determine state
                        matched_state = None
                        for st, patterns in state_patterns.items():
                            for p in patterns:
                                if p in low:
                                    matched_state = st
                                    break
                            if matched_state:
                                break
                        if not matched_state:
                            continue
                        # load frames (support GIF via PIL)
                        frames = []
                        ext = os.path.splitext(fpath)[1].lower()
                        if ext == '.gif' and pil_available_local:
                            try:
                                img = Image.open(fpath)
                                for frame in ImageSequence.Iterator(img):
                                    try:
                                        f = frame.convert('RGBA')
                                        w, h = f.size
                                        data = f.tobytes()
                                        surf = pygame.image.fromstring(data, (w, h), 'RGBA').convert_alpha()
                                        frames.append(surf)
                                    except Exception:
                                        continue
                            except Exception:
                                frames = []
                        else:
                            try:
                                surf = pygame.image.load(fpath).convert_alpha()
                                frames = [surf]
                            except Exception:
                                frames = []

                        if frames:
                            try:
                                self.char_sprites_by_character[char][matched_state][dir_key].extend(frames)
                            except Exception:
                                pass
        except Exception:
            # optional: ignore failures in per-character registry
            self.char_sprites_by_character = {}

        # Pre-scale per-character frames (if any) and precompute masks/bounds to avoid runtime scaling
        try:
            if hasattr(self, 'char_sprites_by_character') and self.char_sprites_by_character:
                self.char_sprites_cache_by_character = {}
                self.char_sprites_masks_by_character = {}
                self.char_sprites_bounds_by_character = {}
                ths = target_heights if 'target_heights' in locals() else [360, 220]
                for cname, cmap in (self.char_sprites_by_character or {}).items():
                    try:
                        self.char_sprites_cache_by_character[cname] = {}
                        self.char_sprites_masks_by_character[cname] = {}
                        self.char_sprites_bounds_by_character[cname] = {}
                        for stt, dirs in cmap.items():
                            self.char_sprites_cache_by_character[cname].setdefault(stt, {'derecha': {}, 'izquierda': {}, 'any': {}})
                            self.char_sprites_masks_by_character[cname].setdefault(stt, {'derecha': {}, 'izquierda': {}, 'any': {}})
                            self.char_sprites_bounds_by_character[cname].setdefault(stt, {'derecha': {}, 'izquierda': {}, 'any': {}})
                            for dk in ('derecha','izquierda','any'):
                                frames = dirs.get(dk, []) or []
                                for h_t in ths:
                                    scaled_list = []
                                    masks = []
                                    rects = []
                                    for f in frames:
                                        try:
                                            fh = f.get_height()
                                            fw = f.get_width()
                                            if fh > 0 and fh != h_t:
                                                scale = h_t / float(fh)
                                                f2 = pygame.transform.smoothscale(f, (int(fw * scale), int(fh * scale)))
                                            else:
                                                f2 = f
                                            scaled_list.append(f2)
                                            try:
                                                m = pygame.mask.from_surface(f2)
                                                masks.append(m)
                                                try:
                                                    br = m.get_bounding_rect()
                                                except Exception:
                                                    br = f2.get_rect()
                                            except Exception:
                                                masks.append(None)
                                                br = f2.get_rect()
                                            rects.append(pygame.Rect(int(br.left), int(br.top), int(br.width), int(br.height)))
                                        except Exception:
                                            continue
                                    self.char_sprites_cache_by_character[cname][stt][dk][h_t] = scaled_list
                                    self.char_sprites_masks_by_character[cname][stt][dk][h_t] = masks
                                    self.char_sprites_bounds_by_character[cname][stt][dk][h_t] = rects
                    except Exception:
                        # skip this character on error
                        continue
        except Exception:
            # leave per-character caches absent on failure
            if hasattr(self, 'char_sprites_cache_by_character'):
                try:
                    del self.char_sprites_cache_by_character
                except Exception:
                    pass

        # Helper: provide sprites for a specific character/state/direction/height
        def get_sprites_for(character, state, direction='derecha', height=360):
            """Return a list of surfaces for the requested character/state/direction at the target height.

            Priority:
              1. If `self.char_sprites_by_character` has frames for that character, use those.
              2. Otherwise, fall back to the global `self.char_sprites_cache`.
            """
            try:
                if not character:
                    return []
                cname = str(character)
                if len(cname) > 1:
                    cname = cname[0].upper() + cname[1:]
                else:
                    cname = cname.upper()
                # Try per-character registry first
                if hasattr(self, 'char_sprites_by_character') and cname in self.char_sprites_by_character:
                    # Prefer precomputed per-character cache if available
                    try:
                        if hasattr(self, 'char_sprites_cache_by_character') and cname in self.char_sprites_cache_by_character:
                            cached = self.char_sprites_cache_by_character[cname].get(state, {}).get(direction, {}).get(height, [])
                            if cached:
                                return list(cached)
                    except Exception:
                        pass
                    # Fallback: scale on demand (rare if no per-character cache was built)
                    chreg = self.char_sprites_by_character[cname]
                    lst = chreg.get(state, {}).get(direction, [])
                    if lst:
                        out = []
                        for s in lst:
                            try:
                                fh = s.get_height()
                                fw = s.get_width()
                                if fh > 0 and fh != height:
                                    scale = height / float(fh)
                                    s2 = pygame.transform.smoothscale(s, (int(fw * scale), int(fh * scale)))
                                else:
                                    s2 = s
                            except Exception:
                                s2 = s
                            out.append(s2)
                        return out
                # Fallback to global cache
                try:
                    return list(self.char_sprites_cache.get(state, {}).get(direction, {}).get(height, []))
                except Exception:
                    return []
            except Exception:
                return []

        # Attach helper to self for external access
        self.get_sprites_for = get_sprites_for
        # Precreate common fonts and caches to avoid recreating per-frame (performance)
        try:
            font_small = pygame.font.SysFont(None, 32)
            font_round = pygame.font.SysFont(None, 72)
            font_timer = pygame.font.SysFont(None, 64)
        except Exception:
            font_small = None
            font_round = None
            font_timer = None
        # Cache for masked/scaled head images: key = (name, radius)
        if not hasattr(self, 'head_cache'):
            self.head_cache = {}

        rounds_to_win = 2
        rounds_won = {'p1': 0, 'p2': 0}
        round_number = 1
        match_winner = None
        # Bucle principal del juego (manejo de rounds: mejor de 3)
        corriendo = True
        ganador = None
        
        # Flag para mostrar la secuencia de inicio de round (se mostrará sobre la escena ya dibujada)
        round_start_pending = True
        # rounds_won, round_number y match_winner fueron inicializados arriba
        while corriendo:
            # Actualizar temporizador
            ahora = pygame.time.get_ticks()
            if ahora - tiempo_ultimo_tick >= 1000:
                tiempo_restante -= 1
                tiempo_ultimo_tick = ahora
                if tiempo_restante <= 0:
                    tiempo_restante = 0

            # Verificar fin de round (vida o tiempo)
            if self.luchador_p1.vida <= 0 or self.luchador_p2.vida <= 0 or tiempo_restante == 0:
                # Determinar ganador de ROUND
                if self.luchador_p1.vida > self.luchador_p2.vida:
                    round_winner = 'p1'
                    round_winner_name = self.luchador_p1.nombre
                    rounds_won['p1'] += 1
                elif self.luchador_p2.vida > self.luchador_p1.vida:
                    round_winner = 'p2'
                    round_winner_name = self.luchador_p2.nombre
                    rounds_won['p2'] += 1
                else:
                    round_winner = None
                    round_winner_name = 'Empate'

                # Comprobar si alguien alcanzó el objetivo de rounds
                if rounds_won['p1'] >= rounds_to_win:
                    match_winner = self.luchador_p1.nombre
                    corriendo = False
                elif rounds_won['p2'] >= rounds_to_win:
                    match_winner = self.luchador_p2.nombre
                    corriendo = False
                else:
                    # Mostrar mensaje de fin de round breve
                    font_round = pygame.font.SysFont(None, 72)
                    if round_winner is None:
                        msg_round = None
                    else:
                        msg_round = font_round.render(f"¡{round_winner_name} gana el round!", True, (255, 255, 0))
                    # Mostrar resultado textual brevemente (si se desea)
                    # ahora prepararnos para el siguiente round y mostrar la secuencia de logos antes del inicio
                    # NOTA: se mostrará la secuencia (RoundX -> Fight) antes de que comience el siguiente round

                    # Preparar siguiente round: resetar vidas, timer, posiciones y cooldowns
                    round_number += 1
                    tiempo_restante = tiempo_total
                    tiempo_ultimo_tick = pygame.time.get_ticks()
                    pelea_start_time = pygame.time.get_ticks()
                    # reset vida
                    self.luchador_p1.vida = 100
                    self.luchador_p2.vida = 100
                    # reset posiciones y estados de stickman si existen
                    if hasattr(self, 'stickman_state'):
                        base_y = self.limite_suelo - 220 - 140
                        self.stickman_state['p1']['x'] = 220
                        self.stickman_state['p1']['y'] = base_y
                        self.stickman_state['p1']['vx'] = 0
                        self.stickman_state['p1']['vy'] = 0
                        self.stickman_state['p1']['estado'] = 'idle'
                        self.stickman_state['p1']['anim'] = 0
                        self.stickman_state['p1']['en_tierra'] = True
                        self.stickman_state['p1']['mirando_derecha'] = True

                        self.stickman_state['p2']['x'] = self.ancho - 220
                        self.stickman_state['p2']['y'] = base_y
                        self.stickman_state['p2']['vx'] = 0
                        self.stickman_state['p2']['vy'] = 0
                        self.stickman_state['p2']['estado'] = 'idle'
                        self.stickman_state['p2']['anim'] = 0
                        self.stickman_state['p2']['en_tierra'] = True
                        self.stickman_state['p2']['mirando_derecha'] = False

                    # reset cooldowns
                    self.hit_cooldown = {'p1': 0, 'p2': 0}
                    if hasattr(self, 'key_last_state'):
                        self.key_last_state = {'q': False, 'e': False, 'kp1': False, 'kp2': False}

                    # Marcar que la secuencia de inicio debe mostrarse antes del próximo round
                    round_start_pending = True
                    # saltar resto del frame para evitar doble conteo
                    continue
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    corriendo = False
                # Alternar mostrar hitboxes con H y otras teclas
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_h:
                        self.mostrar_hitbox = not getattr(self, 'mostrar_hitbox', False)
                    elif evento.key == pygame.K_F7:
                        # Toggle FPS cap
                        try:
                            self.fps_cap_enabled = not getattr(self, 'fps_cap_enabled', True)
                            print(f"FPS cap enabled: {self.fps_cap_enabled}")
                        except Exception:
                            pass
                    elif evento.key == pygame.K_F11:
                        info = pygame.display.Info()
                        if not is_fullscreen:
                            self.ancho, self.alto = info.current_w, info.current_h
                            self.pantalla = pygame.display.set_mode((self.ancho, self.alto), pygame.FULLSCREEN)
                            is_fullscreen = True
                            rescale_assets(self.ancho, self.alto)
                        else:
                            self.ancho, self.alto = windowed_w, windowed_h
                            self.pantalla = pygame.display.set_mode((self.ancho, self.alto))
                            is_fullscreen = False
                            rescale_assets(self.ancho, self.alto)
                # (La detección de maximizar/restaurar se realiza por comparación de tamaño de ventana con la resolución del monitor.)

            teclas = pygame.key.get_pressed()

            # Manejar input
            self.luchador_p1.manejar_input(teclas, self.ancho, self.limite_suelo)
            self.luchador_p2.manejar_input(teclas, self.ancho, self.limite_suelo)

            # Actualizar
            self.grupo_sprites.update(self.ancho, self.limite_suelo)

            # Dibujo (fondo del mapa si existe)
            if fight_bg:
                self.pantalla.blit(fight_bg, (0, 0))
            else:
                self.pantalla.fill((30, 30, 30))
            # Dibujar la franja del suelo solo si el mapa seleccionado NO es Citec
            if not (hasattr(self, 'selected_map') and self.selected_map and self.selected_map.lower() == 'citec'):
                pygame.draw.rect(self.pantalla, (80, 80, 80), (0, self.limite_suelo, self.ancho, self.alto - self.limite_suelo))

            # OCULTAR/ELIMINAR RECTÁNGULOS VERTICALES AMARILLOS
            # (No dibujar ningún rectángulo amarillo junto a los stickman)

            # OCULTAR BARRAS AMARILLAS: No dibujar rectángulos verticales junto a los stickman
            # (Elimina o comenta cualquier pygame.draw.rect con color amarillo cerca de los luchadores)

            # Eliminar cualquier barra amarilla: no dibujar rectángulos verticales junto a los stickman

            # NO dibujar self.grupo_sprites.draw(self.pantalla) para evitar las barras amarillas

            # Dibujar stickman para cada luchador
            def draw_stickman(surface, x, y, color, nombre, estado, mirando_derecha, cabeza_radio=110, anim_frame=0):
                # Si hay sprites cargadas para este estado, usarlas en lugar de dibujar el stickman
                try:
                        sprites = getattr(self, 'char_sprites', None)
                        # Global vertical offset for all sprite images (move sprites down)
                        try:
                            vertical_sprite_offset = 90
                        except Exception:
                            vertical_sprite_offset = 90
                        # Special larger offset for crouch ('agacharse') images only
                        try:
                            vertical_sprite_offset_agach = 200
                        except Exception:
                            vertical_sprite_offset_agach = 200
                        # map 'saltar' to 'idle' frames (use idleRight/idleLeft for jump)
                        lookup_state = 'idle' if estado == 'saltar' else estado
                        # Per-player horizontal adjustment for face images only (player1: left -10, player2: right +10)
                        try:
                            head_dx = 0
                            if hasattr(self, 'luchador_p1') and nombre == getattr(self.luchador_p1, 'nombre', None):
                                head_dx = -12
                            elif hasattr(self, 'luchador_p2') and nombre == getattr(self.luchador_p2, 'nombre', None):
                                head_dx = 12
                            # Additional temporary shift when performing a kick: move face further left/right by 30px
                            try:
                                head_kick_dx = 0
                                if estado == 'patear':
                                    # Move the head offset depending on facing direction
                                    # so kicking left produces the opposite head shift
                                    # than kicking right. This applies equally to both players.
                                    kick_amt = 110
                                    try:
                                        # head should shift opposite to facing direction
                                        # so invert the sign: when facing right, move left (-);
                                        # when facing left, move right (+).
                                        if mirando_derecha:
                                            head_kick_dx = -kick_amt
                                        else:
                                            head_kick_dx = kick_amt
                                    except Exception:
                                        head_kick_dx = 0
                            except Exception:
                                head_kick_dx = 0
                        except Exception:
                            head_dx = 0
                            head_kick_dx = 0
                        # Special-case: when crouching, prefer explicit agacharse images if present
                        if lookup_state == 'agacharse':
                            target_h = 220
                            # Make crouch images a bit bigger than normal: scale factor > 1.0
                            # Only affects 'agacharse' images — other states keep their sizes
                            try:
                                scale_factor_agach = 1.12
                            except Exception:
                                scale_factor_agach = 1.12
                            # pick candidates depending on facing direction
                            if mirando_derecha:
                                candidates = ['agacharseDerecha.png','agacharse_derecha.png','agachDerecha.png','agach_right.png','crouchRight.png','crouch_right.png']
                            else:
                                candidates = ['agacharseIzquierda.png','agacharse_izquierda.png','agachIzquierda.png','agach_left.png','crouchLeft.png','crouch_left.png']
                            found_surf = None
                            sprites_dir = os.path.join('sprites')
                            # Try explicit candidate filenames first
                            for cf in candidates:
                                fp = os.path.join(sprites_dir, cf)
                                if os.path.exists(fp):
                                    try:
                                        tmp = pygame.image.load(fp).convert_alpha()
                                        h = tmp.get_height()
                                        if h > 0:
                                            scale = (target_h * scale_factor_agach) / float(h)
                                            tmp = pygame.transform.smoothscale(tmp, (int(tmp.get_width() * scale), int(tmp.get_height() * scale)))
                                        found_surf = tmp
                                        break
                                    except Exception:
                                        found_surf = None
                            # Fallback: search for any "agach"/"crouch" file and use/flip as needed
                            if found_surf is None and os.path.isdir(sprites_dir):
                                for fname in os.listdir(sprites_dir):
                                    low = fname.lower()
                                    if ('agach' in low) or ('crouch' in low):
                                        fp = os.path.join(sprites_dir, fname)
                                        try:
                                            tmp = pygame.image.load(fp).convert_alpha()
                                            h = tmp.get_height()
                                            if h > 0:
                                                scale = (target_h * scale_factor_agach) / float(h)
                                                tmp = pygame.transform.smoothscale(tmp, (int(tmp.get_width() * scale), int(tmp.get_height() * scale)))
                                            # Do not auto-flip loaded images. We expect separate
                                            # left/right assets; keep the image as-is.
                                            found_surf = tmp
                                            break
                                        except Exception:
                                            pass
                            # If we found a crouch surface, scale to match punch size if possible, cache and register it, then draw and return
                            if found_surf is not None:
                                try:
                                    dir_key = 'derecha' if mirando_derecha else 'izquierda'
                                    # Attempt to match punch ('pegar') size for consistency
                                    try:
                                        punch_surf = None
                                        pegar_dict = self.char_sprites_cache.get('pegar', {}) if hasattr(self, 'char_sprites_cache') else {}
                                        p_list = pegar_dict.get(dir_key, {}).get(target_h, []) if pegar_dict else []
                                        if not p_list:
                                            opp = 'izquierda' if dir_key == 'derecha' else 'derecha'
                                            p_list = pegar_dict.get(opp, {}).get(target_h, []) if pegar_dict else []
                                        if p_list:
                                            punch_surf = p_list[0]
                                        if punch_surf is not None:
                                            desired = punch_surf.get_size()
                                            # Make crouch slightly larger than punch for visual separation
                                            try:
                                                if desired and hasattr(found_surf, 'get_size'):
                                                    desired_w = int(desired[0] * scale_factor_agach)
                                                    desired_h = int(desired[1] * scale_factor_agach)
                                                    found_surf = pygame.transform.smoothscale(found_surf, (desired_w, desired_h))
                                            except Exception:
                                                # fallback to exact size if anything fails
                                                if desired and hasattr(found_surf, 'get_size'):
                                                    found_surf = pygame.transform.smoothscale(found_surf, desired)
                                    except Exception:
                                        pass
                                    # store in cache
                                    try:
                                        if not hasattr(self, 'char_sprites_cache') or not isinstance(self.char_sprites_cache, dict):
                                            self.char_sprites_cache = {}
                                        if 'agacharse' not in self.char_sprites_cache:
                                            self.char_sprites_cache['agacharse'] = {'derecha': {}, 'izquierda': {}, 'any': {}}
                                        self.char_sprites_cache['agacharse'][dir_key][target_h] = [found_surf]
                                    except Exception:
                                        pass
                                    # register in self.char_sprites
                                    try:
                                        if not hasattr(self, 'char_sprites') or not isinstance(self.char_sprites, dict):
                                            self.char_sprites = {}
                                        if 'agacharse' not in self.char_sprites:
                                            self.char_sprites['agacharse'] = {'derecha': [], 'izquierda': [], 'any': []}
                                        lst = self.char_sprites['agacharse'].get(dir_key, []) or []
                                        try:
                                            sizes = [s.get_size() for s in lst if hasattr(s, 'get_size')]
                                            if not hasattr(found_surf, 'get_size') or found_surf.get_size() not in sizes:
                                                lst.append(found_surf)
                                        except Exception:
                                            if found_surf not in lst:
                                                lst.append(found_surf)
                                        self.char_sprites['agacharse'][dir_key] = lst
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                                try:
                                    rect = found_surf.get_rect()
                                    rect.centerx = x
                                    try:
                                        # Align sprite base to the ground (same as agacharse)
                                        if 'suelo' in globals():
                                            rect.bottom = suelo
                                            # For crouch images use larger offset
                                            rect.bottom += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                        else:
                                            rect.top = y - cabeza_radio
                                            rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                    except Exception:
                                        rect.top = y - cabeza_radio
                                        rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                    try:
                                        surface.blit(found_surf, rect)
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                                # overlay head (position relative to rendered rect.top when possible)
                                try:
                                    # head_scale reduces the visual radius of face overlays
                                    try:
                                        head_scale = 1
                                    except Exception:
                                        head_scale = 1
                                    reduced_radius = int(cabeza_radio * head_scale)
                                    reduced_size = reduced_radius * 2
                                    img_key = (nombre, cabeza_radio, head_scale)
                                    cara = self.head_cache.get(img_key)
                                    if cara is None:
                                        img_path = os.path.join('images', 'caras', f'{nombre}.png')
                                        if os.path.exists(img_path):
                                            tmp = pygame.image.load(img_path).convert_alpha()
                                            tmp = pygame.transform.smoothscale(tmp, (reduced_size, reduced_size))
                                            # keep full face image (do not multiply by mask) so it's always visible
                                            self.head_cache[img_key] = tmp
                                            cara = tmp
                                    try:
                                        # prefer rect.top as head y position (keeps head aligned to sprite)
                                        head_y = rect.top
                                    except Exception:
                                        head_y = y + 100 if estado == 'agacharse' else y
                                        head_y += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                    if cara:
                                        surface.blit(cara, (x-reduced_radius + head_dx + (head_kick_dx if 'head_kick_dx' in locals() else 0), head_y - 60))
                                    else:
                                        pygame.draw.circle(surface, color, (x, head_y + reduced_radius), reduced_radius, 0)
                                except Exception:
                                    pass
                                return
                        # Special-case: when kicking, prefer explicit patada images if present
                        if lookup_state == 'patear':
                            target_h = 220 if estado == 'agacharse' else 360
                            # pick candidates depending on facing direction
                            if mirando_derecha:
                                candidates = ['patadaDerecha.png','patada_derecha.png','patearDerecha.png','patear_derecha.png','kickRight.png','kick_right.png']
                            else:
                                candidates = ['patadaIzquierda.png','patada_izquierda.png','patearIzquierda.png','patear_izquierda.png','kickLeft.png','kick_left.png']
                            found_surf = None
                            sprites_dir = os.path.join('sprites')
                            # Try explicit candidate filenames first
                            for cf in candidates:
                                fp = os.path.join(sprites_dir, cf)
                                if os.path.exists(fp):
                                    try:
                                        tmp = pygame.image.load(fp).convert_alpha()
                                        h = tmp.get_height()
                                        if h > 0:
                                            scale = target_h / float(h)
                                            tmp = pygame.transform.smoothscale(tmp, (int(tmp.get_width() * scale), int(tmp.get_height() * scale)))
                                        found_surf = tmp
                                        break
                                    except Exception:
                                        found_surf = None
                            # Fallback: search for any "patad"/"pate"/"kick" file and use/flip as needed
                            if found_surf is None and os.path.isdir(sprites_dir):
                                for fname in os.listdir(sprites_dir):
                                    low = fname.lower()
                                    if ('patad' in low) or ('pate' in low) or ('kick' in low):
                                        fp = os.path.join(sprites_dir, fname)
                                        try:
                                            tmp = pygame.image.load(fp).convert_alpha()
                                            h = tmp.get_height()
                                            if h > 0:
                                                scale = target_h / float(h)
                                                tmp = pygame.transform.smoothscale(tmp, (int(tmp.get_width() * scale), int(tmp.get_height() * scale)))
                                            # Do not auto-flip loaded images. We expect separate
                                            # left/right assets; keep the image as-is.
                                            found_surf = tmp
                                            break
                                        except Exception:
                                            pass
                            # If we found a kick surface, cache it (for reuse) then draw it and overlay head, then return
                            if found_surf is not None:
                                try:
                                    # Insert into char_sprites_cache for 'patear' to reuse elsewhere
                                    try:
                                        dir_key = 'derecha' if mirando_derecha else 'izquierda'
                                        target_h = 220 if estado == 'agacharse' else 360
                                        if not hasattr(self, 'char_sprites_cache') or not isinstance(self.char_sprites_cache, dict):
                                            self.char_sprites_cache = {}
                                        # ensure structure for 'patear'
                                        if 'patear' not in self.char_sprites_cache:
                                            self.char_sprites_cache['patear'] = {'derecha': {}, 'izquierda': {}, 'any': {}}

                                        # Try to match the size of existing punch ('pegar') frames so kicks look consistent
                                        punch_surf = None
                                        try:
                                            pegar_dict = self.char_sprites_cache.get('pegar', {})
                                            # prefer same direction, fallback to opposite
                                            p_list = pegar_dict.get(dir_key, {}).get(target_h, []) if pegar_dict else []
                                            if not p_list:
                                                opp = 'izquierda' if dir_key == 'derecha' else 'derecha'
                                                p_list = pegar_dict.get(opp, {}).get(target_h, []) if pegar_dict else []
                                            if p_list:
                                                punch_surf = p_list[0]
                                        except Exception:
                                            punch_surf = None

                                        # If we found a punch surface, scale kick to that exact size
                                        try:
                                            if punch_surf is not None:
                                                desired = punch_surf.get_size()
                                                if desired and hasattr(found_surf, 'get_size'):
                                                    found_surf = pygame.transform.smoothscale(found_surf, desired)
                                            else:
                                                # fallback: keep target_h scaling already applied earlier
                                                pass
                                        except Exception:
                                            pass

                                        # store single-frame list for the target height
                                        try:
                                            self.char_sprites_cache['patear'][dir_key][target_h] = [found_surf]
                                        except Exception:
                                            # defensive: recreate inner dict if needed
                                            self.char_sprites_cache['patear'][dir_key] = {target_h: [found_surf]}

                                        # Also register the found kick surface in self.char_sprites so 'patear' is treated as a normal state
                                        try:
                                            if not hasattr(self, 'char_sprites') or not isinstance(self.char_sprites, dict):
                                                self.char_sprites = {}
                                            if 'patear' not in self.char_sprites:
                                                self.char_sprites['patear'] = {'derecha': [], 'izquierda': [], 'any': []}
                                            lst = self.char_sprites['patear'].get(dir_key, []) or []
                                            # avoid adding duplicates by size
                                            try:
                                                sizes = [s.get_size() for s in lst if hasattr(s, 'get_size')]
                                                if not hasattr(found_surf, 'get_size') or found_surf.get_size() not in sizes:
                                                    lst.append(found_surf)
                                            except Exception:
                                                # if any problem, just append once
                                                if found_surf not in lst:
                                                    lst.append(found_surf)
                                            self.char_sprites['patear'][dir_key] = lst
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                                try:
                                    rect = found_surf.get_rect()
                                    rect.centerx = x
                                    try:
                                        # Align visual kicks to the crouch height (same base/suelo)
                                        if 'suelo' in globals():
                                            rect.bottom = suelo
                                            rect.bottom += vertical_sprite_offset
                                        else:
                                            rect.top = y - cabeza_radio
                                            rect.top += vertical_sprite_offset
                                    except Exception:
                                        rect.top = y - cabeza_radio
                                        rect.top += vertical_sprite_offset
                                    try:
                                        surface.blit(found_surf, rect)
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                                # superponer cabeza personalizada si existe (cached)
                                try:
                                    try:
                                        head_scale = 1
                                    except Exception:
                                        head_scale = 1
                                    reduced_radius = int(cabeza_radio * head_scale)
                                    reduced_size = reduced_radius * 2
                                    img_key = (nombre, cabeza_radio, head_scale)
                                    cara = self.head_cache.get(img_key)
                                    if cara is None:
                                        img_path = os.path.join('images', 'caras', f'{nombre}.png')
                                        if os.path.exists(img_path):
                                            tmp = pygame.image.load(img_path).convert_alpha()
                                            tmp = pygame.transform.smoothscale(tmp, (reduced_size, reduced_size))
                                            # keep full face image (do not multiply by mask) so it's always visible
                                            self.head_cache[img_key] = tmp
                                            cara = tmp
                                    try:
                                        head_y = rect.top
                                    except Exception:
                                        head_y = y
                                        head_y += vertical_sprite_offset
                                    if cara:
                                        surface.blit(cara, (x-reduced_radius + head_dx + (head_kick_dx if 'head_kick_dx' in locals() else 0), head_y - 60))
                                    else:
                                        pygame.draw.circle(surface, color, (x, head_y + reduced_radius), reduced_radius, 0)
                                except Exception:
                                    pass
                                return
                        # First try per-character sprites via helper (preferred)
                        try:
                            target_h = 220 if estado == 'agacharse' else 360
                        except Exception:
                            target_h = 360
                        try:
                            dir_key = 'derecha' if mirando_derecha else 'izquierda'
                        except Exception:
                            dir_key = 'derecha' if mirando_derecha else 'izquierda'
                        tried_pc = False
                        try:
                            get_sprites = getattr(self, 'get_sprites_for', None)
                            if callable(get_sprites):
                                pc_frames = get_sprites(nombre, lookup_state, dir_key, target_h)
                                if pc_frames:
                                    tried_pc = True
                                    frames = pc_frames
                                    idx = 0
                                    try:
                                        idx = (anim_frame // 4) % max(1, len(frames))
                                    except Exception:
                                        idx = 0
                                    frame_surf = frames[idx]
                                    # already scaled by helper to target_h; do NOT flip —
                                    # assets for left/right must be provided separately.
                                    s2 = frame_surf
                                    try:
                                        rect = s2.get_rect()
                                        rect.centerx = x
                                        try:
                                            if 'suelo' in globals():
                                                rect.bottom = suelo
                                                rect.bottom += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                            else:
                                                rect.top = y - cabeza_radio
                                                rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                        except Exception:
                                            rect.top = y - cabeza_radio
                                            rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                        try:
                                            surface.blit(s2, rect)
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                    # superponer cabeza personalizada si existe (cached)
                                    try:
                                        try:
                                            head_scale = 1
                                        except Exception:
                                            head_scale = 1
                                        reduced_radius = int(cabeza_radio * head_scale)
                                        reduced_size = reduced_radius * 2
                                        img_key = (nombre, cabeza_radio, head_scale)
                                        cara = self.head_cache.get(img_key)
                                        if cara is None:
                                            img_path = os.path.join('images', 'caras', f'{nombre}.png')
                                            if os.path.exists(img_path):
                                                tmp = pygame.image.load(img_path).convert_alpha()
                                                tmp = pygame.transform.smoothscale(tmp, (reduced_size, reduced_size))
                                                self.head_cache[img_key] = tmp
                                                cara = tmp
                                        try:
                                            head_y = rect.top
                                        except Exception:
                                            head_y = y
                                            head_y += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                        if cara:
                                            surface.blit(cara, (x-reduced_radius + head_dx + (head_kick_dx if 'head_kick_dx' in locals() else 0), head_y - 60))
                                        else:
                                            pygame.draw.circle(surface, color, (x, head_y + reduced_radius), reduced_radius, 0)
                                    except Exception:
                                        pass
                                        # If we successfully drew per-character sprite + head, stop here to avoid drawing fallback stickman
                                        return
                        except Exception:
                            tried_pc = False

                        # If we didn't draw per-character frames, fall back to global sprites
                        if not tried_pc and sprites and sprites.get(lookup_state):
                            entry = sprites[lookup_state]
                            frame_surf = None
                            came_from_any = False
                            try:
                                if isinstance(entry, dict):
                                    # If walking, prefer explicit direction-specific lists first.
                                    if lookup_state == 'caminar':
                                        # Try to use exact left/right lists when available
                                        if not mirando_derecha and entry.get('izquierda'):
                                            frames = entry.get('izquierda')
                                        elif mirando_derecha and entry.get('derecha'):
                                            frames = entry.get('derecha')
                                        else:
                                            # fallback order: any, derecha, izquierda
                                            frames = entry.get('any') or entry.get('derecha') or entry.get('izquierda') or []
                                    else:
                                        dir_key = 'derecha' if mirando_derecha else 'izquierda'
                                        frames = entry.get(dir_key) or entry.get('any') or []
                                    came_from_any = (not entry.get('derecha') and not entry.get('izquierda') and bool(entry.get('any')))
                                    if frames:
                                        idx = 0
                                        try:
                                            idx = (anim_frame // 4) % max(1, len(frames))
                                        except Exception:
                                            idx = 0
                                        frame_surf = frames[idx]
                                elif isinstance(entry, list):
                                    frames = entry
                                    idx = 0
                                    try:
                                        idx = (anim_frame // 4) % max(1, len(frames))
                                    except Exception:
                                        idx = 0
                                    frame_surf = frames[idx]
                                else:
                                    frame_surf = entry
                            except Exception:
                                frame_surf = None
                            # Use cached scaled+flipped frames when available to avoid per-frame transforms
                            try:
                                target_h = 220 if estado == 'agacharse' else 360
                                dir_key = 'derecha' if mirando_derecha else 'izquierda'
                                frames_cached = None
                                if hasattr(self, 'char_sprites_cache'):
                                    try:
                                        frames_cached = self.char_sprites_cache.get(lookup_state, {}).get(dir_key, {}).get(target_h, [])
                                    except Exception:
                                        frames_cached = None
                                if frames_cached:
                                    idx = 0
                                    try:
                                        idx = (anim_frame // 4) % max(1, len(frames_cached))
                                    except Exception:
                                        idx = 0
                                    s2 = frames_cached[idx]
                                else:
                                    # fallback: scale the single frame_surf
                                    h = frame_surf.get_height()
                                    w = frame_surf.get_width()
                                    if h > 0:
                                        scale = target_h / float(h)
                                        s2 = pygame.transform.smoothscale(frame_surf, (int(w * scale), int(h * scale)))
                                    else:
                                        s2 = frame_surf
                                    # Do NOT perform any flipping here. If only 'any' frames
                                    # exist they will be used as provided; left/right assets
                                    # must be distinct files.
                            except Exception:
                                s2 = frame_surf

                            rect = s2.get_rect()
                            rect.centerx = x
                            # Align sprite base to 'suelo' for all sprites when using image assets
                            try:
                                if 'suelo' in globals():
                                    rect.bottom = suelo
                                    # If the lookup state is crouch, apply the larger crouch offset
                                    rect.bottom += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                else:
                                    rect.top = y - cabeza_radio
                                    rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                            except Exception:
                                rect.top = y - cabeza_radio
                                rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                            try:
                                surface.blit(s2, rect)
                            except Exception:
                                pass
                            # superponer cabeza personalizada si existe (cached)
                            try:
                                try:
                                    head_scale = 1
                                except Exception:
                                    head_scale = 1
                                reduced_radius = int(cabeza_radio * head_scale)
                                reduced_size = reduced_radius * 2
                                img_key = (nombre, cabeza_radio, head_scale)
                                cara = self.head_cache.get(img_key)
                                if cara is None:
                                    img_path = os.path.join('images', 'caras', f'{nombre}.png')
                                    if os.path.exists(img_path):
                                            tmp = pygame.image.load(img_path).convert_alpha()
                                            tmp = pygame.transform.smoothscale(tmp, (reduced_size, reduced_size))
                                            # keep full face image (do not multiply by mask) so it's always visible
                                            self.head_cache[img_key] = tmp
                                            cara = tmp
                                # Position head according to sprite rect.top so it follows the visual image
                                try:
                                    head_y = rect.top
                                except Exception:
                                    head_y = y + 100 if estado == 'agacharse' else y
                                    head_y += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                                if cara:
                                    surface.blit(cara, (x-reduced_radius + head_dx + (head_kick_dx if 'head_kick_dx' in locals() else 0), head_y - 60))
                                else:
                                    pygame.draw.circle(surface, color, (x, head_y + reduced_radius), reduced_radius, 0)
                            except Exception:
                                pass
                            return
                except Exception:
                    pass
                # Stickman drawing disabled: using only sprites and overlay faces.
                # If we reach here, there were no per-character or global sprite frames for this state, so do not draw the stickman fallback.
                return

            # Estados y controles para animación
            # Variables de estado para cada luchador
            if not hasattr(self, 'stickman_state'):
                self.stickman_state = {
                    'p1': {'x': 220, 'y': 0, 'vx': 0, 'vy': 0, 'estado': 'idle', 'mirando_derecha': True, 'anim': 0, 'en_tierra': True},
                    'p2': {'x': self.ancho - 220, 'y': 0, 'vx': 0, 'vy': 0, 'estado': 'idle', 'mirando_derecha': False, 'anim': 0, 'en_tierra': True}
                }
                suelo = self.limite_suelo
                base_y = suelo - 220 - 140
                self.stickman_state['p1']['y'] = base_y
                self.stickman_state['p2']['y'] = base_y

            suelo = self.limite_suelo
            gravedad = 3
            velocidad = 12
            fuerza_salto = -38

            # Controles
            keys = pygame.key.get_pressed()
            # Inicializar memoria de teclas para pulsación única
            if not hasattr(self, 'key_last_state'):
                self.key_last_state = {'q': False, 'e': False, 'kp1': False, 'kp2': False}
            # P1: A/D/W/S/Q/E
            s1 = self.stickman_state['p1']
            s1['vx'] = 0
            if keys[pygame.K_a]:
                s1['vx'] = -velocidad
                s1['mirando_derecha'] = False
                s1['estado'] = 'caminar'
            if keys[pygame.K_d]:
                s1['vx'] = velocidad
                s1['mirando_derecha'] = True
                s1['estado'] = 'caminar'
            if keys[pygame.K_s] and s1['en_tierra']:
                s1['estado'] = 'agacharse'
            if keys[pygame.K_w] and s1['en_tierra']:
                s1['vy'] = fuerza_salto
                s1['en_tierra'] = False
                s1['estado'] = 'saltar'
            # Puñetazo (Q): solo primera pulsación
            if keys[pygame.K_q] and not self.key_last_state['q']:
                s1['estado'] = 'pegar'
            # Patada (E): solo primera pulsación
            if keys[pygame.K_e] and not self.key_last_state['e']:
                s1['estado'] = 'patear'
            if not (keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_s] or keys[pygame.K_w] or keys[pygame.K_q] or keys[pygame.K_e]):
                if s1['en_tierra']:
                    s1['estado'] = 'idle'
            # Actualizar memoria de teclas
            self.key_last_state['q'] = keys[pygame.K_q]
            self.key_last_state['e'] = keys[pygame.K_e]

            # P2: Flechas y Numpad1/Numpad2
            s2 = self.stickman_state['p2']
            s2['vx'] = 0
            if keys[pygame.K_LEFT]:
                s2['vx'] = -velocidad
                s2['mirando_derecha'] = False
                s2['estado'] = 'caminar'
            if keys[pygame.K_RIGHT]:
                s2['vx'] = velocidad
                s2['mirando_derecha'] = True
                s2['estado'] = 'caminar'
            if keys[pygame.K_DOWN] and s2['en_tierra']:
                s2['estado'] = 'agacharse'
            if keys[pygame.K_UP] and s2['en_tierra']:
                s2['vy'] = fuerza_salto
                s2['en_tierra'] = False
                s2['estado'] = 'saltar'
            # Puñetazo (KP1): solo primera pulsación
            if keys[pygame.K_KP1] and not self.key_last_state['kp1']:
                s2['estado'] = 'pegar'
            # Patada (KP2): solo primera pulsación
            if keys[pygame.K_KP2] and not self.key_last_state['kp2']:
                s2['estado'] = 'patear'
            if not (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_DOWN] or keys[pygame.K_UP] or keys[pygame.K_KP1] or keys[pygame.K_KP2]):
                if s2['en_tierra']:
                    s2['estado'] = 'idle'
            # Actualizar memoria de teclas
            self.key_last_state['kp1'] = keys[pygame.K_KP1]
            self.key_last_state['kp2'] = keys[pygame.K_KP2]

            # Actualizar física y animación con colisiones
            ancho_cuerpo = 40
            alto_cuerpo = 140
            base_y = suelo - 220 - 140
            for idx, s in enumerate([s1, s2]):
                prev_x = s['x']
                s['x'] += s['vx']
                s['x'] = max(120, min(self.ancho-120, s['x']))
                if not s['en_tierra']:
                    s['vy'] += gravedad
                    s['y'] += s['vy']
                    if s['y'] >= base_y:
                        s['y'] = base_y
                        s['vy'] = 0
                        s['en_tierra'] = True
                        if s['estado'] == 'saltar':
                            s['estado'] = 'idle'
                # Animaciones:
                # - caminar: avanzar anim cuando realmente se mueve
                # - idle: animar automáticamente cuando está quieto (en tierra y sin moverse)
                if s['estado'] == 'caminar' and abs(s['x'] - prev_x) > 0:
                    s['anim'] += 1
                elif s['estado'] == 'idle' and s['en_tierra'] and abs(s['x'] - prev_x) == 0:
                    # avanzar contador de animación de idle para reproducir el GIF sin pulsar tecla
                    s['anim'] += 1
                else:
                    s['anim'] = 0

            # Colisión física: no atravesarse (solo saltar por encima)
            # Definir rectángulo de cuerpo para cada stickman
            # Preferir rects basados en el sprite actualmente mostrado (si existen)
            def visual_rect_for(s, personaje_obj):
                """Return a pygame.Rect positioned in world coords that matches the
                non-transparent bounding box of the current sprite frame for the
                given state/direction. Falls back to a default body rect.
                """
                try:
                    # basic offsets used by draw_stickman for alignment
                    vertical_sprite_offset = 90
                    vertical_sprite_offset_agach = 200
                    lookup_state = 'idle' if s['estado'] == 'saltar' else s['estado']
                    target_h = 220 if lookup_state == 'agacharse' else 360
                    dir_key = 'derecha' if s.get('mirando_derecha', True) else 'izquierda'

                    # determine character name
                    if personaje_obj is None:
                        # fallback: infer by identity (s1/s2) when caller provides None
                        if s is s1:
                            cname = getattr(self.luchador_p1, 'nombre', None)
                        else:
                            cname = getattr(self.luchador_p2, 'nombre', None)
                    else:
                        cname = getattr(personaje_obj, 'nombre', None)

                    # try per-character frames first
                    get_sprites = getattr(self, 'get_sprites_for', None)
                    frame_surf = None
                    if callable(get_sprites) and cname:
                        try:
                            frames = get_sprites(cname, lookup_state, dir_key, target_h)
                            if frames:
                                idx = 0
                                try:
                                    idx = (s.get('anim', 0) // 4) % max(1, len(frames))
                                except Exception:
                                    idx = 0
                                frame_surf = frames[idx]
                        except Exception:
                            frame_surf = None

                    # fallback to global cache
                    if frame_surf is None:
                        try:
                            frames_cached = self.char_sprites_cache.get(lookup_state, {}).get(dir_key, {}).get(target_h, []) if hasattr(self, 'char_sprites_cache') else []
                            if frames_cached:
                                idx = 0
                                try:
                                    idx = (s.get('anim', 0) // 4) % max(1, len(frames_cached))
                                except Exception:
                                    idx = 0
                                frame_surf = frames_cached[idx]
                        except Exception:
                            frame_surf = None

                    if frame_surf is None:
                        # No sprite frame available -> use default simple body rect
                        return pygame.Rect(s['x']-ancho_cuerpo//2, s['y']+110, ancho_cuerpo, alto_cuerpo)

                    # compute bounding rect of visible pixels in frame_surf
                    bounding = None
                    try:
                        # animation index used to select frame (matches how frames were chosen above)
                        anim_idx = 0
                        try:
                            anim_idx = (s.get('anim', 0) // 4)
                        except Exception:
                            anim_idx = 0

                        # Prefer per-character precomputed bounds (most specific)
                        try:
                            if hasattr(self, 'char_sprites_bounds_by_character') and cname:
                                bmap = self.char_sprites_bounds_by_character.get(cname, {}).get(lookup_state, {}).get(dir_key, {}).get(target_h, [])
                                if bmap and anim_idx < len(bmap):
                                    bounding = bmap[anim_idx]
                        except Exception:
                            bounding = None

                        # Then try precomputed global bounds (fast)
                        try:
                            if bounding is None and hasattr(self, 'char_sprites_bounds_cache'):
                                bmap = self.char_sprites_bounds_cache.get(lookup_state, {}).get(dir_key, {}).get(target_h, [])
                                if bmap and anim_idx < len(bmap):
                                    bounding = bmap[anim_idx]
                        except Exception:
                            bounding = None

                        # If no global cached bounds, and per-character frames were used,
                        # try computing mask (rare path)
                        if bounding is None:
                            try:
                                # compute mask for this specific surface (only if we must)
                                mask = pygame.mask.from_surface(frame_surf)
                                try:
                                    bounding = mask.get_bounding_rect()
                                except Exception:
                                    try:
                                        brs = mask.get_bounding_rects()
                                        if brs:
                                            btemp = brs[0].copy()
                                            for r in brs[1:]:
                                                btemp.union_ip(r)
                                            bounding = btemp
                                        else:
                                            bounding = frame_surf.get_rect()
                                    except Exception:
                                        bounding = frame_surf.get_rect()
                            except Exception:
                                bounding = frame_surf.get_rect()
                    except Exception:
                        bounding = frame_surf.get_rect()

                    # Translate bounding to world coordinates using same alignment as draw_stickman
                    try:
                        rect = frame_surf.get_rect()
                        rect.centerx = s['x']
                        # align bottom to ground (suelo)
                        if 'suelo' in locals() or 'suelo' in globals():
                            suelo_local = self.limite_suelo
                            rect.bottom = suelo_local
                            rect.bottom += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                        else:
                            rect.top = s['y'] - 110
                            rect.top += vertical_sprite_offset_agach if lookup_state == 'agacharse' else vertical_sprite_offset
                    except Exception:
                        rect = pygame.Rect(s['x']-ancho_cuerpo//2, s['y']+110, ancho_cuerpo, alto_cuerpo)

                    # bounding is relative to (0,0) of the frame; map to rect.topleft
                    try:
                        hit_rect = pygame.Rect(rect.left + bounding.left, rect.top + bounding.top, bounding.width, bounding.height)
                        return hit_rect
                    except Exception:
                        return rect
                except Exception:
                    return pygame.Rect(s['x']-ancho_cuerpo//2, s['y']+110, ancho_cuerpo, alto_cuerpo)

            rect1 = visual_rect_for(s1, self.luchador_p1 if hasattr(self, 'luchador_p1') else None)
            rect2 = visual_rect_for(s2, self.luchador_p2 if hasattr(self, 'luchador_p2') else None)
            # Update Personaje.hitbox for debugging/visualization so it matches sprites
            try:
                if hasattr(self, 'luchador_p1') and getattr(self, 'luchador_p1') is not None:
                    try:
                        self.luchador_p1.hitbox = rect1.copy()
                    except Exception:
                        pass
                if hasattr(self, 'luchador_p2') and getattr(self, 'luchador_p2') is not None:
                    try:
                        self.luchador_p2.hitbox = rect2.copy()
                    except Exception:
                        pass
            except Exception:
                pass
            # Si colisionan y ambos están en el suelo, empujar
            if rect1.colliderect(rect2):
                if s1['en_tierra'] and s2['en_tierra']:
                    # Empujar a cada uno hacia su lado
                    if s1['x'] < s2['x']:
                        s1['x'] -= 8
                        s2['x'] += 8
                    else:
                        s1['x'] += 8
                        s2['x'] -= 8
            # Si uno está saltando, permitir pasar por encima
            # (no hacer nada extra)

            # Colisiones de ataque (puñetazo/patada)
            # Definir hitbox de ataque basada en el rect visual del sprite actual
            def ataque_hitbox(s, tipo):
                try:
                    # obtain visual sprite rect for this character
                    personaje_obj = self.luchador_p1 if s is s1 else self.luchador_p2
                    sprite_rect = visual_rect_for(s, personaje_obj)
                    # Default small fallback rect if something fails
                    if not sprite_rect or sprite_rect.width == 0 or sprite_rect.height == 0:
                        sprite_rect = pygame.Rect(s['x']-ancho_cuerpo//2, s['y']+110, ancho_cuerpo, alto_cuerpo)

                    if tipo == 'pegar' and s['estado'] == 'pegar':
                        attack_w = max(30, int(sprite_rect.width * 0.5))
                        attack_h = max(20, int(sprite_rect.height * 0.25))
                        attack_y = sprite_rect.top + int(sprite_rect.height * 0.4)
                        if s['mirando_derecha']:
                            return pygame.Rect(sprite_rect.right, attack_y, attack_w, attack_h)
                        else:
                            return pygame.Rect(sprite_rect.left - attack_w, attack_y, attack_w, attack_h)

                    if tipo == 'patear' and s['estado'] == 'patear':
                        attack_w = max(40, int(sprite_rect.width * 0.7))
                        attack_h = max(24, int(sprite_rect.height * 0.2))
                        # kicks usually hit lower than punches
                        attack_y = sprite_rect.top + int(sprite_rect.height * 0.55)
                        if s['mirando_derecha']:
                            return pygame.Rect(sprite_rect.right, attack_y, attack_w, attack_h)
                        else:
                            return pygame.Rect(sprite_rect.left - attack_w, attack_y, attack_w, attack_h)
                except Exception:
                    # fallback to previous hardcoded positions
                    if tipo == 'pegar' and s['estado'] == 'pegar':
                        if s['mirando_derecha']:
                            return pygame.Rect(s['x']+60, s['y']+140, 60, 30)
                        else:
                            return pygame.Rect(s['x']-120, s['y']+140, 60, 30)
                    if tipo == 'patear' and s['estado'] == 'patear':
                        if s['mirando_derecha']:
                            return pygame.Rect(s['x']+60, s['y']+200, 80, 30)
                        else:
                            return pygame.Rect(s['x']-140, s['y']+200, 80, 30)
                return None

            # Solo restar vida una vez por ataque
            # Delay entre golpes (por personaje)
            if not hasattr(self, 'hit_cooldown'):
                self.hit_cooldown = {'p1': 0, 'p2': 0}
            now_time = pygame.time.get_ticks()
            cooldown_ms = 800  # 0.8 segundos entre golpes

            # P1 ataca a P2
            def get_mask_and_rect_for_state(s_obj, personaje_obj):
                """Return (mask, sprite_rect) for the current animation frame of s_obj.
                Prefers per-character precomputed masks, then global masks cache.
                If no mask cached, will attempt to compute a mask from the frame surface.
                """
                try:
                    lookup_state = 'idle' if s_obj['estado'] == 'saltar' else s_obj['estado']
                    target_h = 220 if lookup_state == 'agacharse' else 360
                    dir_key = 'derecha' if s_obj.get('mirando_derecha', True) else 'izquierda'
                    # determine character name
                    cname = None
                    if personaje_obj is None:
                        if s_obj is s1:
                            cname = getattr(self.luchador_p1, 'nombre', None)
                        else:
                            cname = getattr(self.luchador_p2, 'nombre', None)
                    else:
                        cname = getattr(personaje_obj, 'nombre', None)
                    # compute anim index used in draw selection
                    try:
                        anim_idx = (s_obj.get('anim', 0) // 4)
                    except Exception:
                        anim_idx = 0

                    # Try per-character masks first
                    if cname and hasattr(self, 'char_sprites_masks_by_character'):
                        try:
                            mm = self.char_sprites_masks_by_character.get(cname, {}).get(lookup_state, {}).get(dir_key, {}).get(target_h, [])
                            if mm and anim_idx < len(mm):
                                mask = mm[anim_idx]
                                # sprite rect world position
                                rect = visual_rect_for(s_obj, personaje_obj)
                                return mask, rect
                        except Exception:
                            pass

                    # Then try global masks cache
                    if hasattr(self, 'char_sprites_masks_cache'):
                        try:
                            mm = self.char_sprites_masks_cache.get(lookup_state, {}).get(dir_key, {}).get(target_h, [])
                            if mm and anim_idx < len(mm):
                                mask = mm[anim_idx]
                                rect = visual_rect_for(s_obj, personaje_obj)
                                return mask, rect
                        except Exception:
                            pass

                    # Last resort: attempt to get the frame surface and compute mask
                    try:
                        frames = []
                        get_sprites = getattr(self, 'get_sprites_for', None)
                        if callable(get_sprites) and cname:
                            frames = get_sprites(cname, lookup_state, dir_key, target_h) or []
                        if not frames:
                            frames = self.char_sprites_cache.get(lookup_state, {}).get(dir_key, {}).get(target_h, []) if hasattr(self, 'char_sprites_cache') else []
                        if frames:
                            fidx = anim_idx % max(1, len(frames))
                            frame = frames[fidx]
                            try:
                                mask = pygame.mask.from_surface(frame)
                            except Exception:
                                mask = None
                            rect = visual_rect_for(s_obj, personaje_obj)
                            return mask, rect
                    except Exception:
                        pass
                except Exception:
                    pass
                return None, visual_rect_for(s_obj, personaje_obj)

            for tipo in ['pegar','patear']:
                hb1 = ataque_hitbox(s1, tipo)
                if hb1 and rect2.colliderect(hb1) and now_time > self.hit_cooldown['p1']:
                    # use pixel-perfect check (masks) to confirm hit when possible
                    try:
                        mask2, sprite2_rect = get_mask_and_rect_for_state(s2, self.luchador_p2)
                        if mask2 is not None:
                            # create attack mask (full rectangle)
                            attack_w = hb1.width
                            attack_h = hb1.height
                            try:
                                attack_mask = pygame.Mask((attack_w, attack_h), fill=True)
                                offset = (hb1.left - sprite2_rect.left, hb1.top - sprite2_rect.top)
                                overlap = mask2.overlap(attack_mask, offset)
                                if overlap is None:
                                    # no pixel overlap -> ignore this as a hit
                                    continue
                            except Exception:
                                # fallback to rect-based if any mask operation fails
                                pass
                    except Exception:
                        pass
                    # Evitar que la extremidad atraviese al oponente: reposicionar ligeramente al atacante
                    try:
                        if s1['mirando_derecha']:
                            # calcular cuanto alcanza la hitbox a la derecha desde s1['x']
                            # para 'pegar' es +120, para 'patear' es +140
                            reach = 120 if tipo == 'pegar' else 140
                            # si la hitbox llega más allá del borde izquierdo del cuerpo del rival, retroceder atacante
                            if (s1['x'] + reach) > rect2.left:
                                s1['x'] = rect2.left - reach - 2
                        else:
                            reach = 120 if tipo == 'pegar' else 140
                            if (s1['x'] - reach) < rect2.right:
                                s1['x'] = rect2.right + reach + 2
                    except Exception:
                        pass
                    dmg = 5 if tipo=='pegar' else 10
                    self.luchador_p2.vida = max(0, self.luchador_p2.vida - dmg)
                    # Empujar ligeramente al objetivo si está en tierra
                    if s2['en_tierra']:
                        s2['x'] += 30 if s1['x'] < s2['x'] else -30
                    self.hit_cooldown['p1'] = now_time + cooldown_ms

            # P2 ataca a P1
            for tipo in ['pegar','patear']:
                hb2 = ataque_hitbox(s2, tipo)
                if hb2 and rect1.colliderect(hb2) and now_time > self.hit_cooldown['p2']:
                    # pixel-perfect check for P1 using masks if available
                    try:
                        mask1, sprite1_rect = get_mask_and_rect_for_state(s1, self.luchador_p1)
                        if mask1 is not None:
                            attack_w = hb2.width
                            attack_h = hb2.height
                            try:
                                attack_mask = pygame.Mask((attack_w, attack_h), fill=True)
                                offset = (hb2.left - sprite1_rect.left, hb2.top - sprite1_rect.top)
                                overlap = mask1.overlap(attack_mask, offset)
                                if overlap is None:
                                    continue
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # Prevent limb clipping by nudging attacker back if necessary
                    try:
                        if s2['mirando_derecha']:
                            reach = 120 if tipo == 'pegar' else 140
                            if (s2['x'] + reach) > rect1.left:
                                s2['x'] = rect1.left - reach - 2
                        else:
                            reach = 120 if tipo == 'pegar' else 140
                            if (s2['x'] - reach) < rect1.right:
                                s2['x'] = rect1.right + reach + 2
                    except Exception:
                        pass
                    dmg = 5 if tipo=='pegar' else 10
                    self.luchador_p1.vida = max(0, self.luchador_p1.vida - dmg)
                    if s1['en_tierra']:
                        s1['x'] += 30 if s2['x'] < s1['x'] else -30
                    self.hit_cooldown['p2'] = now_time + cooldown_ms

            # Destruction handling removed: match/round end is handled by the round-check above

            color1 = (200, 40, 40)
            color2 = (40, 40, 200)
            # Dibujar ambos stickman (la lógica de "destruido" ya no aplica)
            draw_stickman(self.pantalla, s1['x'], s1['y'], color1, self.luchador_p1.nombre, s1['estado'], s1['mirando_derecha'], 110, s1['anim'])
            draw_stickman(self.pantalla, s2['x'], s2['y'], color2, self.luchador_p2.nombre, s2['estado'], s2['mirando_derecha'], 110, s2['anim'])

            # Hitboxes desactivadas en pantalla (se eliminaron los rectángulos amarillos de depuración)


            # Barra de vida para cada jugador
            max_vida = 100
            barra_w = 400
            barra_h = 32
            margen = 20
            # P1 (izquierda)
            vida_p1 = max(0, min(self.luchador_p1.vida, max_vida))
            x1, y1 = margen, margen
            pygame.draw.rect(self.pantalla, (60,60,60), (x1, y1, barra_w, barra_h), 0, border_radius=8)
            ancho_vida1 = int(barra_w * vida_p1 / max_vida)
            pygame.draw.rect(self.pantalla, (200,40,40), (x1, y1, ancho_vida1, barra_h), 0, border_radius=8)
            font = font_small if font_small else pygame.font.SysFont(None, 32)
            nombre1 = font.render(self.luchador_p1.nombre, True, (255,255,255))
            self.pantalla.blit(nombre1, (x1 + 8, y1 + barra_h//2 - nombre1.get_height()//2))
            # Mostrar contador de rounds para P1
            try:
                rounds_surf1 = font.render(f"Rounds: {rounds_won['p1']}", True, (255,255,255))
                self.pantalla.blit(rounds_surf1, (x1, y1 + barra_h + 6))
            except Exception:
                pass
            # P2 (derecha)
            vida_p2 = max(0, min(self.luchador_p2.vida, max_vida))
            x2, y2 = self.ancho - barra_w - margen, margen
            pygame.draw.rect(self.pantalla, (60,60,60), (x2, y2, barra_w, barra_h), 0, border_radius=8)
            ancho_vida2 = int(barra_w * vida_p2 / max_vida)
            pygame.draw.rect(self.pantalla, (40,40,200), (x2 + barra_w - ancho_vida2, y2, ancho_vida2, barra_h), 0, border_radius=8)
            nombre2 = font.render(self.luchador_p2.nombre, True, (255,255,255))
            self.pantalla.blit(nombre2, (x2 + barra_w - nombre2.get_width() - 8, y2 + barra_h//2 - nombre2.get_height()//2))
            # Mostrar contador de rounds para P2
            try:
                rounds_surf2 = font.render(f"Rounds: {rounds_won['p2']}", True, (255,255,255))
                self.pantalla.blit(rounds_surf2, (x2 + barra_w - rounds_surf2.get_width(), y2 + barra_h + 6))
            except Exception:
                pass


            # Dibujar temporizador centrado arriba
            # use precreated font_timer to avoid allocating per-frame
            # font_timer was created before the main loop
            timer_text = font_timer.render(f"{tiempo_restante:02}", True, (255,255,0))
            self.pantalla.blit(timer_text, (self.ancho//2 - timer_text.get_width()//2, 20))

            # Antes de volcar el frame, si está pendiente la secuencia de inicio de round,
            # mostrarla (esto pintará RoundX -> Fight sobre la escena ya dibujada)
            if 'round_start_pending' in locals() and round_start_pending:
                try:
                    show_pre_round_sequence(round_number)
                except Exception:
                    pass
                round_start_pending = False

            # Mostrar logo Fight sobre el escenario durante los primeros 1.5 segundos
            if fight_logo_scaled:
                if pygame.time.get_ticks() - pelea_start_time < fight_logo_duration:
                    self.pantalla.blit(fight_logo_scaled, (logo_x, logo_y))

            pygame.display.flip()
            try:
                if getattr(self, 'fps_cap_enabled', True):
                    self.reloj.tick(getattr(self, 'fps_cap', self.fps))
                else:
                    self.reloj.tick()
            except Exception:
                try:
                    self.reloj.tick(self.fps)
                except Exception:
                    pass

        # Mostrar mensaje de victoria del MATCH (primero en 2 rounds)
        font_win = pygame.font.SysFont(None, 80)
        final_winner = None
        if match_winner:
            final_winner = match_winner
        else:
            # si por alguna razón no se estableció match_winner, inferir por rounds
            if rounds_won.get('p1', 0) > rounds_won.get('p2', 0):
                final_winner = self.luchador_p1.nombre
            elif rounds_won.get('p2', 0) > rounds_won.get('p1', 0):
                final_winner = self.luchador_p2.nombre
            else:
                final_winner = None

        # Intentar mostrar logo de ganador en lugar de texto
        winner_logo = None
        if final_winner:
            try:
                winner_logo = load_winner_logo(final_winner)
            except Exception:
                winner_logo = None

        try:
            if winner_logo:
                # Mostrar el logo del ganador SUPERPUESTO a la escena actual (como hace Fight.png)
                # No reescribimos el fondo para preservar los personajes y HUD debajo.
                self.pantalla.blit(winner_logo, (logo_x, logo_y))
                pygame.display.flip()
            else:
                # Fallback: mostrar texto genérico (sin la palabra 'Empate')
                if final_winner:
                    msg = font_win.render(f"¡{final_winner} gana el match!", True, (0,255,0))
                else:
                    msg = font_win.render("¡Match terminado!", True, (255,255,0))
                self.pantalla.blit(msg, (self.ancho//2 - msg.get_width()//2, self.alto//2 - msg.get_height()//2))
                pygame.display.flip()
        except Exception:
            pass
        pygame.time.wait(3500)

        # After showing the match result, return to caller so the caller can
        # re-open the character selection menu. Do not quit the whole program
        # here so the player can play again.
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        return


if __name__ == '__main__':
    juego = Juego()
    # Run the game loop repeatedly: after each match `ejecutar_pelea` will
    # return here and we call it again to show the character selection screen.
    try:
        while True:
            juego.ejecutar_pelea()
    except SystemExit:
        # Allow clean exit when the code calls sys.exit()
        pass
