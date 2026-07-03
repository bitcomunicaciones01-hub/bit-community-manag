"""
security.py — Módulo de seguridad para el Community Manager BIT.

Protege contra:
- Path traversal en archivos de draft JSON
- Validación de schema de drafts
- Limpieza de archivos temporales huérfanos
- Sanitización de rutas de archivo
"""

import os
import re
import glob
import time
import logging
from typing import Optional

# Logger de seguridad dedicado
sec_logger = logging.getLogger("security.community")
sec_logger.setLevel(logging.WARNING)
if not sec_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[SECURITY %(levelname)s] %(asctime)s — %(message)s"))
    sec_logger.addHandler(handler)


# ---------------------------------------------------------------------------
# Directorios permitidos (rutas absolutas resueltas al importar)
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ALLOWED_DIRS = {
    "drafts":    os.path.realpath(os.path.join(_BASE_DIR, "brain", "drafts")),
    "archive":   os.path.realpath(os.path.join(_BASE_DIR, "brain", "archive")),
    "errors":    os.path.realpath(os.path.join(_BASE_DIR, "brain", "errors")),
    "reels":     os.path.realpath(os.path.join(_BASE_DIR, "brain", "reels")),
    "previews":  os.path.realpath(os.path.join(_BASE_DIR, "brain", "previews")),
    "root":      _BASE_DIR,
}

# Extensiones de video y imagen permitidas para rutas de media
ALLOWED_MEDIA_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv",   # Video
    ".png", ".jpg", ".jpeg", ".webp", ".gif",  # Imagen
}

# Extensiones de imagen permitidas para archivos custom_img
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# Máximo de caracteres para un caption (para evitar DoS / prompt stuffing)
MAX_CAPTION_LENGTH = 2200  # Límite real de Instagram

# Tiempo máximo (en horas) que puede vivir un archivo temp_publish_*.png
TEMP_FILE_MAX_AGE_HOURS = 2


# ---------------------------------------------------------------------------
# 1. PathValidator
# ---------------------------------------------------------------------------

def is_safe_path(base_dir: str, path: str) -> bool:
    """
    Verifica que `path` esté dentro de `base_dir` (previene path traversal).

    Ejemplos bloqueados:
        path = "brain/drafts/../../etc/passwd"  → False
        path = "/etc/shadow"                    → False
    """
    try:
        real_base = os.path.realpath(os.path.abspath(base_dir))
        real_path = os.path.realpath(os.path.abspath(path))
        # Aceptar si la ruta empieza con base + separador (subdirectorio)
        # O si es exactamente la base (edge case)
        return real_path.startswith(real_base + os.sep) or real_path == real_base
    except Exception:
        return False


def validate_media_path(path: str, path_type: str = "media") -> Optional[str]:
    """
    Valida que una ruta de media (video/imagen) sea segura:
      - Existe en disco
      - Está dentro de un directorio permitido
      - Tiene una extensión de archivo permitida

    Returns:
        La ruta absoluta real si es válida, None en caso contrario.
    """
    if not path or not isinstance(path, str):
        return None

    # Resolver a ruta absoluta
    abs_path = os.path.realpath(os.path.abspath(path))

    # Verificar existencia
    if not os.path.isfile(abs_path):
        sec_logger.warning(f"validate_media_path: archivo no existe: '{abs_path}'")
        return None

    # Verificar extensión
    ext = os.path.splitext(abs_path)[1].lower()
    allowed_exts = ALLOWED_IMAGE_EXTENSIONS if path_type == "image" else ALLOWED_MEDIA_EXTENSIONS
    if ext not in allowed_exts:
        sec_logger.warning(f"validate_media_path: extensión no permitida '{ext}' en '{abs_path}'")
        return None

    # Verificar que esté dentro de algún directorio permitido
    in_allowed = any(
        abs_path.startswith(allowed_dir + os.sep) or abs_path == allowed_dir
        for allowed_dir in ALLOWED_DIRS.values()
    )
    if not in_allowed:
        sec_logger.error(
            f"[SECURITY ALERT] PATH TRAVERSAL BLOQUEADO — "
            f"path_type='{path_type}', ruta='{abs_path}'"
        )
        return None

    return abs_path


# ---------------------------------------------------------------------------
# 2. DraftValidator — valida el schema y las rutas de un JSON de draft
# ---------------------------------------------------------------------------

# Campos permitidos en un JSON de draft (whitelist)
DRAFT_ALLOWED_FIELDS = {
    "id", "approval_status", "publish_time_iso", "draft_caption",
    "preferred_format", "reel_path", "selected_product", "design_settings",
    "created_at", "updated_at", "platform", "post_type",
    "image_prompt", "retry_count", "recent_products", "research_summary",
    "critique_feedback", "status",
}

# Valores permitidos para campos de tipo enum
DRAFT_ENUM_FIELDS = {
    "approval_status":  {"approved", "pending", "rejected"},
    "preferred_format": {"image", "video", "tiktok"},
}


def validate_draft_json(data: dict, draft_file_path: str) -> tuple[bool, list[str]]:
    """
    Valida el contenido de un JSON de draft antes de procesarlo.

    Returns:
        (es_válido: bool, lista_de_errores: list[str])
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["El draft no es un objeto JSON válido"]

    # 1. Verificar que no haya campos inesperados (posible inyección de payload)
    unexpected = set(data.keys()) - DRAFT_ALLOWED_FIELDS
    if unexpected:
        sec_logger.warning(
            f"validate_draft_json: campos inesperados en '{draft_file_path}': {unexpected}"
        )
        # No bloqueamos, solo advertimos (puede ser una versión futura del schema)

    # 2. Validar enums
    for field, allowed_values in DRAFT_ENUM_FIELDS.items():
        value = data.get(field)
        if value is not None and value not in allowed_values:
            errors.append(f"Campo '{field}' tiene valor inválido: '{value}'")

    # 3. Validar caption (evitar prompts gigantes o contenido malicioso)
    caption = data.get("draft_caption", "")
    if not isinstance(caption, str):
        errors.append("'draft_caption' debe ser una cadena de texto")
    elif len(caption) > MAX_CAPTION_LENGTH:
        sec_logger.warning(
            f"validate_draft_json: caption demasiado largo ({len(caption)} chars), truncando"
        )
        data["draft_caption"] = caption[:MAX_CAPTION_LENGTH]

    # 4. Validar reel_path (PATH TRAVERSAL - vulnerabilidad crítica)
    reel_path = data.get("reel_path")
    if reel_path is not None:
        safe_reel = validate_media_path(reel_path, path_type="media")
        if safe_reel is None:
            errors.append(f"'reel_path' inválido o fuera de directorio permitido: '{reel_path}'")
            # Nullificar para que no se use
            data["reel_path"] = None
        else:
            data["reel_path"] = safe_reel  # Normalizar a ruta absoluta real

    # 5. Validar selected_product (solo debe ser un dict, no código)
    product = data.get("selected_product")
    if product is not None and not isinstance(product, dict):
        errors.append("'selected_product' debe ser un objeto JSON")

    # 6. Validar que publish_time_iso sea un string con formato básico de fecha
    pub_time = data.get("publish_time_iso")
    if pub_time is not None:
        if not isinstance(pub_time, str):
            errors.append("'publish_time_iso' debe ser una cadena de texto")
        elif not re.match(r"^\d{4}-\d{2}-\d{2}", pub_time):
            errors.append(f"'publish_time_iso' tiene formato inválido: '{pub_time}'")

    is_valid = len(errors) == 0
    return is_valid, errors


# ---------------------------------------------------------------------------
# 3. Limpieza de archivos temporales huérfanos
# ---------------------------------------------------------------------------

def cleanup_orphaned_temp_files(base_dir: str = None, max_age_hours: float = TEMP_FILE_MAX_AGE_HOURS):
    """
    Elimina archivos temp_publish_*.png con más de `max_age_hours` horas de antigüedad.
    Previene DoS por llenado de disco.

    Args:
        base_dir: Directorio donde buscar. Por defecto, el directorio del script.
        max_age_hours: Antigüedad máxima en horas antes de eliminar.
    """
    if base_dir is None:
        base_dir = _BASE_DIR

    if not is_safe_path(_BASE_DIR, base_dir):
        sec_logger.error(f"cleanup: directorio base inseguro: '{base_dir}'")
        return

    pattern = os.path.join(base_dir, "temp_publish_*.png")
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted = 0

    for f in glob.glob(pattern):
        try:
            if now - os.path.getmtime(f) > max_age_seconds:
                os.remove(f)
                deleted += 1
        except Exception as e:
            sec_logger.warning(f"cleanup: no se pudo eliminar '{f}': {e}")

    if deleted > 0:
        print(f"[Security] Limpieza: {deleted} archivo(s) temp_publish_*.png eliminados.")


# ---------------------------------------------------------------------------
# 4. Sanitización de queries WooCommerce
# ---------------------------------------------------------------------------

_DANGEROUS_CHARS_RE = re.compile(r"[<>\"'`;\\{}\[\]|]")
MAX_SEARCH_QUERY_LENGTH = 200


def sanitize_search_query(query: str) -> str:
    """
    Sanitiza un query de búsqueda antes de enviarlo a la API de WooCommerce.
    """
    if not isinstance(query, str):
        return ""

    query = query[:MAX_SEARCH_QUERY_LENGTH]
    query = _DANGEROUS_CHARS_RE.sub("", query)
    query = re.sub(r"\s+", " ", query).strip()
    return query


def validate_product_id(product_id) -> Optional[int]:
    """
    Valida que un product_id sea un entero positivo válido.
    Previene inyecciones en URLs de la API (/products/{id}).
    """
    try:
        pid = int(product_id)
        if pid <= 0:
            return None
        return pid
    except (ValueError, TypeError):
        sec_logger.warning(f"validate_product_id: ID inválido recibido: '{product_id}'")
        return None
