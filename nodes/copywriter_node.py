import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timedelta

def draft_content(state):
    print("--- [Node] Copywriter (GPT-4o-mini) ---")
    
    product = state.get("selected_product")
    research = state.get("research_summary")
    retry_count = state.get("retry_count", 0)
    critique = state.get("critique_feedback", "")
    
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    print(f"--- [Node] Copywriter ({model_name}) ---")
    
    llm = ChatOpenAI(model=model_name, temperature=0.7)
    
    # Logic for Scheduling:
    now = datetime.now()
    if now.hour < 12:
        target_date = now
        publish_time = now.replace(hour=18, minute=0, second=0).isoformat()
    else:
        target_date = now + timedelta(days=1)
        publish_time = (target_date).replace(hour=10, minute=0, second=0).isoformat()

    # --- SETTINGS & THEME ---
    settings_path = os.path.join("brain", "settings.json")
    weekly_theme = ""
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
                weekly_theme = settings.get("weekly_theme", "")
        except:
            pass

    # --- CONTENT CALENDAR STRATEGY ---
    # Days: 0=Monday, 6=Sunday
    weekday = target_date.weekday()
    days_map = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    day_name = days_map[weekday]
    
    CALENDAR = {
        0: "Producto destacado (Review amigable, para qué sirve, por qué lo necesitás)",
        1: "Tecnología y Futuro (Tendencias, nuevas placas, qué se viene en el mundo tech)",
        2: "Curiosidades Técnicas (Datos que no sabías, historia de componentes, mitos)",
        3: "Tips y Mantenimiento (Cómo cuidar tu equipo, limpieza, optimización)",
        4: "Oferta de la Semana / Stock (Disponibilidad inmediata, precio especial)",
        5: "Detrás de Escena / Calidad (Cómo testeamos en BIT, seriedad y garantía)",
        6: "Comunidad BIT (Consultas comunes, interacción, ¿qué equipo tenés vos?)"
    }
    
    daily_theme = CALENDAR.get(weekday, "Producto destacado")
    print(f"Strategy for {day_name}: {daily_theme}")
    if weekly_theme:
        print(f"Weekly Theme: {weekly_theme}")

    # --- Memory Retrieval ---
    past_posts_examples = "No style memory available yet."
    print("Memory disabled temporarily to prevent hangs")

    # Get brand identity from environment
    store_name = os.getenv("STORE_NAME", "BIT Comunicaciones")
    store_persona = "BIT Robot - El experto técnico más buena onda de Santa Fe"
    store_location = os.getenv("STORE_LOCATION", "Santa Fe Capital")
    store_phone = os.getenv("STORE_PHONE", "(342) 5482454")
    store_web = "bitcomunicaciones.com"
    store_instagram = "@bitcomunicaciones"
    
    # Extract product information
    product_name = product.get("name", "")
    # Price Formatting (Argentine style)
    raw_price = product.get("price", "")
    try:
        if raw_price:
            float_price = float(raw_price)
            product_price = "{:,.0f}".format(float_price).replace(",", ".")
        else:
            product_price = "Consultar"
    except:
        product_price = raw_price
    product_categories = ", ".join(product.get("categories", []))
    product_description = product.get("short_description", "")

    # --- PROMPT SELECTION ---
    post_type = product.get("post_type", "sales")
    
    # Build Theme instruction
    theme_inst = ""
    if weekly_theme:
        theme_inst = f"IMPORTANTE: Estamos en la semana de '{weekly_theme}'. Intentá vincular el post con este tema si tiene sentido, o usalo como contexto."

    if post_type == "sales":
        prompt_text = """
        Actuá como el experto técnico principal de '{store_name}', una tienda líder en hardware y repuestos en {location} (Argentina).
        Tus seguidores son técnicos, entusiastas del hardware y clientes que buscan SOLUCIONES REALES, no solo marketing.
        
        {theme_inst}
        
        📅 FOCO ESTRATÉGICO ({day_name}):
        **{daily_theme}**.
        
        DATOS PRECISOS DEL PRODUCTO:
        - Nombre: {product_name}
        - Precio: ${price}
        - Información Técnica: {research}
        
        REGLAS DE RIGOR TÉCNICO Y ESTILO BIT:
        1. **Voseo Argentino Natural**: Usá "tenés", "querés", "necesitás", "vení". Nada de "puedes" ni "tienes".
        2. **Experto, no Vendedor**: Evitá frases genéricas como "puente mágico" o "maravilla". Sé específico. Si es un receptor WiFi, hablá de su chipset, frecuencia, compatibilidad exacta y estabilidad de señal.
        3. **Rigor Técnico**: Explicá por qué este repuesto es la elección correcta. Mencioná compatibilidades de modelos, voltajes o especificaciones que un técnico valoraría.
        4. **Identidad BIT**: Mantené los datos de contacto claros. Somos serios, probamos todo lo que vendemos y damos garantía.
        
        ESTRUCTURA TÉCNICA REQUERIDA:
        - Título directo (¿Buscás el repuesto exacto para tu equipo?).
        - Especificaciones técnicas clave y compatibilidad.
        - Beneficio real de elegir este componente original/testeado.
        - Bloque de Acción (Precio y Contacto).
        
        CONTACTO BIT:
        📍 {location} | 📱 WhatsApp: {phone} | 🌐 {web}
        
        Hashtags: Generá 6-8 hashtags específicos de hardware y la marca (ej: #RepuestosPC #{category_clean} #BitComunicaciones #HardwareSantaFe).
        
        Output: SOLO el texto del caption.
        """
    else:
        prompt_text = """
        Actuá como el experto técnico de '{store_name}' en {location}. 
        Hoy el objetivo es aportar conocimiento técnico de alto nivel para nuestra comunidad de reparadores y fanáticos del hardware.
        
        {theme_inst}
        
        📅 TEMA TÉCNICO DEL DÍA ({day_name}):
        **{daily_theme}**.
        
        COMPONENTE DE REFERENCIA: {product_name}
        DATOS TÉCNICOS: {research}
        
        ESTILO EXIGIDO:
        - Profesional, preciso y con autoridad técnica.
        - Usá voseo argentino (Tú no existe en BIT).
        - Nada de lenguaje infantilizado o genérico. Explicá cómo funciona el componente o cómo se diagnostica una falla.
        
        ESTRUCTURA:
        - Dato técnico preciso o diagnóstico de falla.
        - Explicación de ingeniería o funcionamiento del componente.
        - Tip profesional para técnicos (ej: cuidado con la estática, limpieza de contactos).
        - Bloque de contacto:
        📍 {location} | 📱 WhatsApp: {phone} | 🌐 {web}
        
        Hashtags: Generá 5-6 hashtags técnicos y de comunidad.
        
        Output: SOLO el texto del caption.
        """

    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    
    # Clean category for hashtag
    category_clean = product_categories.replace(" ", "").replace(",", "") if product_categories else "Repuestos"
    
    print(f"Generating balanced caption for: {product_name}...")
    response = chain.invoke({
        "store_name": store_name,
        "location": store_location,
        "phone": store_phone,
        "web": store_web,
        "instagram": store_instagram,
        "category_clean": category_clean,
        "product_name": product_name,
        "price": product_price,
        "research": research,
        "day_name": day_name,
        "daily_theme": daily_theme,
        "theme_inst": theme_inst
    })
    
    caption = response.content.strip()
    print(f"Caption generated ({len(caption)} chars)")
    
    # Generate Image Prompt for BIT aesthetic (NOT cyberpunk)
    print("Generating image prompt...")
    # BIT style: Clean, professional, green/blue colors, robot mascot, educational
    image_prompt_text = f"""Product showcase for {product_name} from BIT Comunicaciones. 
    Style: Clean, professional, tech-focused. 
    Colors: Green (#00AA00) and Navy Blue (#1E3A8A) accents on white background.
    Include: BIT robot mascot (friendly gamepad-face robot), product image, trust elements.
    Mood: Educational, trustworthy, modern but approachable.
    Layout: Professional e-commerce style, NOT futuristic or cyberpunk.
    Quality: High resolution, 1080x1080 Instagram format."""
    
    print("Image prompt ready")

    return {
        "draft_caption": caption,
        "image_prompt": image_prompt_text,
        "publish_time_iso": publish_time,
        "retry_count": retry_count + 1,
        "status": "critique"
    }
