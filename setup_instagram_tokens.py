import requests
import os
from dotenv import load_dotenv, set_key

# Configuración
APP_ID = "10239780534400413"
APP_SECRET = "902b8eadeb5a01af577ff6cd83c2788c"
ENV_FILE = ".env"

def exchange_for_long_lived_token(short_lived_token):
    """Intercambia un token de corta duración por uno de larga duración (60 días)"""
    print("🔄 Intercambiando token por uno de larga duración...")
    
    url = "https://graph.facebook.com/v24.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_lived_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "access_token" in data:
        print("✅ Token de larga duración obtenido")
        return data["access_token"]
    else:
        print(f"❌ Error: {data}")
        return None

def get_page_access_token(user_token):
    """Obtiene el Page Access Token de la página de Facebook"""
    print("\n📄 Obteniendo información de páginas...")
    
    url = f"https://graph.facebook.com/v24.0/me/accounts"
    params = {
        "access_token": user_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "data" in data and len(data["data"]) > 0:
        page = data["data"][0]  # Toma la primera página
        page_name = page.get("name", "Unknown")
        page_id = page.get("id")
        page_token = page.get("access_token")
        
        print(f"✅ Página encontrada: {page_name} (ID: {page_id})")
        return page_id, page_token, page_name
    else:
        print(f"❌ No se encontraron páginas: {data}")
        return None, None, None

def get_instagram_account_id(page_id, page_token):
    """Obtiene el Instagram Business Account ID vinculado a la página"""
    print("\n📸 Obteniendo Instagram Business Account...")
    
    url = f"https://graph.facebook.com/v24.0/{page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": page_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "instagram_business_account" in data:
        ig_account_id = data["instagram_business_account"]["id"]
        print(f"✅ Instagram Business Account ID: {ig_account_id}")
        return ig_account_id
    else:
        print(f"⚠️  No se encontró cuenta de Instagram Business vinculada")
        print(f"Respuesta: {data}")
        return None

def get_instagram_username(ig_account_id, page_token):
    """Obtiene el username de Instagram"""
    print("\n👤 Obteniendo username de Instagram...")
    
    url = f"https://graph.facebook.com/v24.0/{ig_account_id}"
    params = {
        "fields": "username",
        "access_token": page_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "username" in data:
        username = data["username"]
        print(f"✅ Username: @{username}")
        return username
    else:
        print(f"⚠️  No se pudo obtener el username")
        return None

def save_to_env(page_token, ig_account_id, page_id, page_name, ig_username):
    """Guarda los tokens en el archivo .env"""
    print("\n💾 Guardando configuración en .env...")
    
    # Crear archivo .env si no existe
    if not os.path.exists(ENV_FILE):
        open(ENV_FILE, 'w').close()
    
    # Guardar valores
    set_key(ENV_FILE, "META_ACCESS_TOKEN", page_token)
    set_key(ENV_FILE, "INSTAGRAM_ACCOUNT_ID", ig_account_id or "")
    set_key(ENV_FILE, "FACEBOOK_PAGE_ID", page_id or "")
    
    print("✅ Configuración guardada en .env:")
    print(f"   - META_ACCESS_TOKEN: {page_token[:20]}...")
    print(f"   - INSTAGRAM_ACCOUNT_ID: {ig_account_id}")
    print(f"   - FACEBOOK_PAGE_ID: {page_id}")
    print(f"   - Página: {page_name}")
    if ig_username:
        print(f"   - Instagram: @{ig_username}")

def main():
    print("=" * 60)
    print("🚀 CONFIGURADOR DE TOKENS DE INSTAGRAM BUSINESS")
    print("=" * 60)
    
    # Solicitar token temporal
    print("\n📋 Necesito un User Access Token temporal.")
    print("   Obtén uno en: https://developers.facebook.com/tools/explorer/")
    print("   1. Selecciona tu app 'Community'")
    print("   2. Selecciona 'Obtener token de acceso de usuario'")
    print("   3. Haz clic en 'Generate Access Token'")
    print("   4. Copia el token generado\n")
    
    short_token = input("🔑 Pega aquí tu User Access Token: ").strip()
    
    if not short_token:
        print("❌ No se proporcionó ningún token")
        return
    
    # Paso 1: Intercambiar por token de larga duración
    long_token = exchange_for_long_lived_token(short_token)
    if not long_token:
        return
    
    # Paso 2: Obtener Page Access Token
    page_id, page_token, page_name = get_page_access_token(long_token)
    if not page_token:
        return
    
    # Paso 3: Obtener Instagram Account ID
    ig_account_id = get_instagram_account_id(page_id, page_token)
    
    # Paso 4: Obtener username de Instagram
    ig_username = None
    if ig_account_id:
        ig_username = get_instagram_username(ig_account_id, page_token)
    
    # Paso 5: Guardar en .env
    save_to_env(page_token, ig_account_id, page_id, page_name, ig_username)
    
    print("\n" + "=" * 60)
    print("✅ ¡CONFIGURACIÓN COMPLETADA!")
    print("=" * 60)
    print("\n💡 El Page Access Token no expira mientras la app esté activa.")
    print("   Puedes usar estos tokens en tu aplicación Community Concept.\n")

if __name__ == "__main__":
    main()
