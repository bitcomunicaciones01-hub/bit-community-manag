# BIT Comunicaciones Community Manager

Community manager automatizado para BIT Comunicaciones - Tienda de repuestos usados de notebooks y PC en Santa Fe Capital.

## Descripción

Este sistema automatiza la creación y publicación de contenido en Instagram para BIT Comunicaciones. Utiliza **GPT-4o-mini** para generar contenido educativo y confiable sobre repuestos de notebooks y PC, respetando la identidad de marca de BIT.

## Características

- 🛒 **Integración con WooCommerce**: Obtiene productos recientes de bitcomunicaciones.com
- 🔍 **Investigación automática**: Combina búsqueda web + base de conocimientos técnicos (RAG)
- ✍️ **Generación de contenido**: Crea captions educativos con GPT-4o-mini
- 🎨 **Generación de imágenes**: DALL-E 3 con identidad de marca BIT (colores verde/azul)
- 📱 **Publicación en Instagram**: Automática 2 veces al día (10:00 y 18:00)
- 🧠 **Memoria RAG**: Base de conocimientos técnicos + evita repetir contenido
- ✅ **Aprobación manual**: Revisa contenido antes de publicar
- 🤖 **Anti-detección**: Medidas para evitar bloqueos de Instagram

## Instalación

### 1. Clonar o descargar el proyecto

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

El archivo `.env` ya está configurado con tus credenciales.

### 4. Inicializar base de conocimientos RAG

```powershell
python init_rag.py
```

Este comando carga la base de conocimientos técnicos (baterías, SSDs, RAM, etc.) en ChromaDB.

## Uso

### Testing del Sistema

Antes de ejecutar el agente completo, verifica que todo funcione:

```powershell
python test_system.py
```

Este script verifica:
- ✅ Conexión a WooCommerce
- ✅ Sistema RAG funcional
- ✅ API de OpenAI
- ✅ Autenticación de Instagram
- ✅ Generación de imágenes con DALL-E

### Ejecutar una vez (testing)

```powershell
python main.py
```

El agente:
1. Obtiene un producto de WooCommerce
2. Investiga información técnica (RAG + Web)
3. Genera caption con GPT-4o-mini
4. Valida calidad y marca
5. **Te pide aprobación manual**
6. Genera imagen con DALL-E
7. Publica en Instagram

### Ejecutar en modo programado

El sistema está configurado para ejecutarse automáticamente **2 veces al día** (10:00 y 18:00).

Deja corriendo:
```powershell
python main.py
```

El scheduler ejecutará el workflow en los horarios programados.

## Estructura del Proyecto

```
Community Concept/
├── .env                      # Variables de entorno (configurado)
├── main.py                   # Punto de entrada principal
├── graph.py                  # Workflow de LangGraph
├── woocommerce_client.py     # Cliente API de WooCommerce
├── instagram_client.py       # Cliente Instagram (Instagrapi + anti-detección)
├── rag_system.py             # Sistema RAG con ChromaDB
├── generate_image.py         # Generación de imágenes con DALL-E 3
├── init_rag.py               # Script de inicialización RAG
├── test_system.py            # Tests end-to-end
├── approval_system.py        # Sistema de aprobación manual
├── requirements.txt          # Dependencias
├── nodes/
│   ├── woocommerce_node.py   # Obtención de productos
│   ├── researcher_node.py    # Investigación (RAG + Web)
│   ├── copywriter_node.py    # Generación de contenido
│   ├── critic_node.py        # Control de calidad
│   ├── approval_node.py      # Aprobación manual
│   └── publisher_node.py     # Publicación (DALL-E + Instagram)
├── brain/
│   ├── knowledge_base/       # Documentos técnicos (RAG)
│   │   ├── baterias_notebooks.txt
│   │   ├── discos_ssd.txt
│   │   └── memorias_ram.txt
│   ├── rag_knowledge/        # Base de datos RAG (ChromaDB)
│   ├── memory_openai/        # Memoria de posts (ChromaDB)
│   └── instagram_session.json # Sesión de Instagram
└── brand_assets/             # Imágenes de marca BIT
```

## Workflow del Agente

```
1. WooCommerce Intake → Obtiene productos recientes
2. Researcher → Busca info técnica (RAG + Web)
3. Copywriter → Genera caption con GPT-4o-mini
4. Critic → Verifica calidad y marca
5. Approval → Aprobación manual (tú decides)
6. Publisher → Genera imagen (DALL-E) + Publica (Instagram)
```

## Identidad de Marca BIT

### Colores
- **Verde**: `#00AA00` (primario)
- **Azul marino**: `#1E3A8A` (secundario)

### Tono
- Educativo
- Amigable
- Confiable
- Accesible

### Temas de Contenido
- Comparaciones Original vs Genérico
- Datos curiosos sobre tecnología
- Consejos prácticos sobre repuestos
- Garantías y calidad

## Medidas Anti-Detección Instagram

✅ **Sesión persistente** - Evita logins repetidos
✅ **Delays aleatorios** - Simula comportamiento humano
✅ **User Agent realista** - Simula dispositivos Android
✅ **Configuración de dispositivo** - Samsung Galaxy S10+
✅ **Actividad humana** - Navega entre publicaciones

## Troubleshooting

### Error: "RAG query failed"
```powershell
python init_rag.py
```

### Error: "Instagram Challenge Required"
- Inicia sesión manualmente en Instagram desde tu navegador
- Elimina `brain/instagram_session.json`
- Vuelve a ejecutar

### Error: "WooCommerce API Error"
- Verifica credenciales en `.env`
- Verifica que la URL sea correcta

### Error: "OpenAI API Error"
- Verifica `OPENAI_API_KEY` en `.env`
- Verifica que tengas créditos en tu cuenta

## Contacto

**BIT Comunicaciones**  
📍 Santa Fe Capital  
📞 (342) 5482454  
🌐 bitcomunicaciones.com  
📷 @bitcomunicaciones
