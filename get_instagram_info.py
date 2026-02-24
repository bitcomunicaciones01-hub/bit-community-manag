import requests
from dotenv import set_key

print("=" * 70)
print("🔍 OBTENER INFORMACIÓN DE INSTAGRAM BUSINESS")
print("=" * 70)

# Solicitar token
print("\n📋 Necesitas un User Access Token de tu app 'Community'")
print("   App ID: 10239780534400413")
print("\n   Pasos:")
print("   1. Ve a: https://developers.facebook.com/tools/explorer/")
print("   2. Selecciona la app 'Community' (ID: 10239780534400413)")
print("   3. Selecciona 'Obtener token de acceso de usuario'")
print("   4. Haz clic en 'Generate Access Token'")
print("   5. Copia el token\n")

token = input("🔑 Pega tu User Access Token aquí: ").strip()

if not token:
    print("❌ No se proporcionó token")
    exit(1)

# Obtener información de páginas
print("\n📄 Obteniendo tus páginas de Facebook...")
url = "https://graph.facebook.com/v24.0/me/accounts"
params = {
    "fields": "id,name,access_token,instagram_business_account",
    "access_token": token
}

response = requests.get(url, params=params)
data = response.json()

if "error" in data:
    print(f"\n❌ Error: {data['error']['message']}")
    print(f"   Código: {data['error']['code']}")
    print(f"   Tipo: {data['error']['type']}")
    print("\n💡 Asegúrate de que:")
    print("   - El token fue generado con la app correcta (ID: 10239780534400413)")
    print("   - Tienes los permisos: pages_show_list, instagram_basic")
    exit(1)

if "data" not in data or len(data["data"]) == 0:
    print("❌ No se encontraron páginas de Facebook")
    exit(1)

print(f"\n✅ Se encontraron {len(data['data'])} página(s):\n")

for i, page in enumerate(data["data"], 1):
    page_name = page.get("name")
    page_id = page.get("id")
    page_token = page.get("access_token")
    
    print(f"{i}. Página: {page_name}")
    print(f"   Page ID: {page_id}")
    print(f"   Page Token: {page_token[:30]}...")
    
    # Verificar si tiene Instagram Business
    if "instagram_business_account" in page:
        ig_account = page["instagram_business_account"]
        ig_id = ig_account.get("id")
        print(f"   ✅ Instagram Business ID: {ig_id}")
        
        # Obtener username
        ig_url = f"https://graph.facebook.com/v24.0/{ig_id}"
        ig_params = {
            "fields": "username",
            "access_token": page_token
        }
        ig_response = requests.get(ig_url, params=ig_params)
        ig_data = ig_response.json()
        
        if "username" in ig_data:
            print(f"   📸 Instagram: @{ig_data['username']}")
        
        # Guardar en .env
        print("\n💾 Guardando en .env...")
        set_key(".env", "META_APP_ID", "10239780534400413")
        set_key(".env", "META_APP_SECRET", "902b8eadeb5a01af577ff6cd83c2788c")
        set_key(".env", "META_ACCESS_TOKEN", page_token)
        set_key(".env", "INSTAGRAM_ACCOUNT_ID", ig_id)
        set_key(".env", "FACEBOOK_PAGE_ID", page_id)
        
        print("✅ Configuración guardada:")
        print(f"   META_ACCESS_TOKEN: {page_token[:30]}...")
        print(f"   INSTAGRAM_ACCOUNT_ID: {ig_id}")
        print(f"   FACEBOOK_PAGE_ID: {page_id}")
        
    else:
        print("   ⚠️  No tiene Instagram Business vinculado")
    
    print()

print("=" * 70)
print("✅ ¡PROCESO COMPLETADO!")
print("=" * 70)
print("\n💡 Nota: El Page Access Token no expira mientras la app esté activa.")
print("   Puedes usarlo directamente en tu aplicación.\n")
