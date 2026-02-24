import streamlit as st
import os
import json
import glob
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Load environment
load_dotenv()

# Page Config
st.set_page_config(
    page_title="BIT AI Community Manager",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stTextArea textarea {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        line-height: 1.5;
    }
    
    .block-container {
        padding-top: 2rem;
    }
    
    div[data-testid="stStatusWidget"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

def refine_post(current_caption, user_instruction, product_data={}, weekly_theme=""):
    """
    AI Assistant that handles CAPTION refinement. (Strictly text-only).
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    p_name = product_data.get("name", "Producto")
    p_desc = product_data.get("description", "")[:400]
    p_price = product_data.get("price", "")
    
    theme_inst = ""
    if weekly_theme:
        theme_inst = f"Estamos en la semana de: '{weekly_theme}'. Si tiene sentido, alineá el cambio con este tema."

    prompt = ChatPromptTemplate.from_template("""
    Sos un **Redactor Senior y Especialista en Copywriting** para BIT Comunicaciones (Santa Fe).
    Tu misión UNICA es procesar una ORDEN del usuario para mejorar el TEXTO (Caption) de un post.
    
    {theme_inst}
    
    ESTADO ACTUAL DEL TEXTO:
    - Caption: {current_caption}
    
    PRODUCTO (Para contexto):
    - Nombre: {p_name}
    - Descripción: {p_desc}
    - Precio: ${p_price}
    
    ORDEN DEL USUARIO:
    "{user_instruction}"
    
    REGLAS:
    1. Tu prioridad absoluta es REFINAR EL TEXTO del post.
    2. Asegurá un tono profesional, amigable, persuasivo y con buena gramática.
    3. NO menciones ni intentes cambiar el diseño visual (fotos, tamaños, posiciones). 
    4. Centrate solo en palabras, emojis y estructura del post.
    
    5. Retorná SIEMPRE un JSON válido con esta estructura:
       {{
         "caption": "texto corregido y mejorado aquí..."
       }}

    SOLO respondé el JSON. Sin explicaciones.
    """)
    
    chain = prompt | llm
    
    response = chain.invoke({
        "current_caption": current_caption, 
        "user_instruction": user_instruction,
        "p_name": p_name,
        "p_desc": p_desc,
        "p_price": p_price,
        "theme_inst": theme_inst
    })
    
    try:
        raw = response.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except:
        return {"caption": current_caption}

# Create drafts dir
draft_dir = "./brain/drafts"
os.makedirs(draft_dir, exist_ok=True)

# Helper functions for callbacks
def select_draft(filepath):
    st.session_state["selected_file"] = filepath

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=80)
    st.title("BIT Manager")
    st.caption("v1.0.0 • Local Mode")

    st.markdown("---")
    
    # 1. GENERATION BUTTON (Restored)
    if st.button("✨ Generar Nuevo Post", use_container_width=True, type="primary"):
        with st.status("🤖 Creando contenido...", expanded=True) as status:
            st.write("Analizando productos...")
            os.environ["DASHBOARD_MODE"] = "true"
            try:
                from graph import app
                app.invoke({"messages": [], "status": "start"})
                status.update(label="¡Post generado!", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # --- SETTINGS SECTION ---
    st.markdown("### ⚙️ Configuración")
    settings_path = os.path.join("brain", "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = json.load(f)
    else:
        settings = {"weekly_theme": ""}

    weekly_theme = st.text_input("Tema de la Semana", value=settings.get("weekly_theme", ""), help="Ej: Placas Madres, Pantallas, Tips de Limpieza")
    if weekly_theme != settings.get("weekly_theme"):
        settings["weekly_theme"] = weekly_theme
        with open(settings_path, "w") as f:
            json.dump(settings, f)
        st.toast(f"Tema actualizado: {weekly_theme}")

    st.markdown("---")
    
    # Template Uploader
    with st.expander("🎨 Cargar Diseño (Fondo)"):
        uploaded_template = st.file_uploader("Sube tu imagen (1080x1080)", type=["png", "jpg", "jpeg"])
        if uploaded_template:
            save_path = os.path.join("brand_assets", "template.png")
            if not os.path.exists("brand_assets"):
                os.makedirs("brand_assets")
            with open(save_path, "wb") as f:
                f.write(uploaded_template.getbuffer())
            st.success("¡Diseño actualizado!")
    
    st.markdown("### 📂 Posts Generados")
    # File selector
    draft_files = glob.glob(os.path.join(draft_dir, "*.json"))
    draft_files.sort(key=os.path.getmtime, reverse=True)
    
    # Initialize selection
    if "selected_file" not in st.session_state and draft_files:
        st.session_state["selected_file"] = draft_files[0]
    
    selected_file = None
    
    def format_draft_name(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                product_name = data.get("selected_product", {}).get("name", "Producto")
                timestamp = os.path.basename(filepath).split('_')[1]
                hhmm = os.path.basename(filepath).split('_')[2][:4]
                return f"📝 {timestamp[6:8]}/{timestamp[4:6]} {hhmm[:2]}:{hhmm[2:]} - {product_name[:20]}"
        except:
            return os.path.basename(filepath)

    if draft_files:
        selected_file = st.selectbox(
            "Seleccionar para Editar", 
            draft_files, 
            format_func=format_draft_name,
            key="selected_file" 
        )
    else:
        st.info("Hacé clic en 'Generar Nuevo Post' para empezar.")

# Main View
if not draft_files:
     st.title("👋 Bienvenido al BIT Manager")
     st.info("No hay publicaciones generadas. Usá el botón 'Generar Nuevo Post' en el sidebar para empezar.")
     st.stop()

# 1. Main Editor View
if selected_file:
    with open(selected_file, "r", encoding="utf-8") as f:
        draft = json.load(f)
    
    did = draft.get('id', 'draft')
    product = draft.get("selected_product", {})

    # Define design state EARLY to avoid NameErrors in other columns/tabs
    design = draft.get("design_settings", {
        "title_override": product.get("name", ""),
        "product_scale": 1.0,
        "title_scale": 1.0,
        "show_logo": True,
        "show_footer": True,
        "remove_bg": False,
        "title_y_offset": 0,
        "product_y_offset": 0,
        "product_x_offset": 0
    })

    st.title("🛠️ Editor de Publicación")

    # Status Banner
    status = draft.get("approval_status", "draft")
    if status == "approved":
        st.success("✅ **APROBADO** | Programado para publicación automática.")
    else:
        st.info("✏️ **BORRADOR** | Requiere revisión.")

    col1, col2 = st.columns([1, 1], gap="large")

    # --- Column 1: Live Preview (Fixed/Main) ---
    with col1:
        st.subheader("📸 Vista Previa")
        preview_placeholder = st.empty()
        
        try:
            from image_composer import create_social_post
            # Default paths
            pid = product.get("id", "unknown")
            default_preview = os.path.join("brain", "previews", f"preview_{did}_{pid}.png")
            
            # Check for custom image
            custom_img_path = os.path.join("brain", "drafts", f"custom_img_{did}.png")
            if not os.path.exists(custom_img_path): custom_img_path = None

            # Generate/Update preview
            with st.spinner("Actualizando diseño..."):
                final_display_path = create_social_post(
                    product, 
                    default_preview,
                    override_image_path=custom_img_path,
                    remove_bg=design.get("remove_bg", False),
                    design_settings=design
                )

            if final_display_path and os.path.exists(final_display_path):
                from PIL import Image
                import time
                display_img = Image.open(final_display_path)
                preview_placeholder.image(display_img, use_container_width=True)
            
            st.markdown(f"**{product.get('name', 'Producto')}**")
            st.caption(f"Precio: ${product.get('price', '0')}")
            
            st.markdown("---")
            st.markdown("#### ⏰ Programación")
            current_iso = draft.get("publish_time_iso")
            try:
                dt = datetime.fromisoformat(current_iso) if current_iso else datetime.now()
            except:
                dt = datetime.now()
            
            c_date, c_time = st.columns(2)
            with c_date: new_date = st.date_input("Fecha", value=dt.date(), key=f"date_{did}")
            with c_time: new_time = st.time_input("Hora", value=dt.time(), key=f"time_{did}")
            
            new_dt = datetime.combine(new_date, new_time)
            if new_dt != dt:
                draft["publish_time_iso"] = new_dt.isoformat()
                with open(selected_file, "w", encoding="utf-8") as f:
                    json.dump(draft, f, indent=2, ensure_ascii=False)
                st.toast(f"Horario actualizado", icon="⏰")

        except Exception as e:
            preview_placeholder.error(f"Error de diseño: {e}")

    # --- Column 2: Editor & Chat ---
    with col2:
        tab_design, tab_text, tab_video = st.tabs(["🎨 Diseño", "✍️ Texto", "🎥 Video (Beta)"])
        
        file_id = os.path.basename(selected_file).replace(".json", "")
        if f"version_{file_id}" not in st.session_state:
            st.session_state[f"version_{file_id}"] = 0
        version = st.session_state[f"version_{file_id}"]
        editor_key = f"editor_{file_id}_v{version}"

        with tab_design:
            @st.fragment
            def design_editor_fragment():
                st.markdown("### Ajustes Visuales")
                # 1. Manual Title Override
                new_img_title = st.text_input("Título en Imagen", value=design.get("title_override", ""), key=f"title_img_{did}")
                if new_img_title != design.get("title_override"):
                    design["title_override"] = new_img_title
                    draft["design_settings"] = design
                    with open(selected_file, "w", encoding="utf-8") as f:
                        json.dump(draft, f, indent=2, ensure_ascii=False)
                    st.rerun()

                # 2. Image Upload
                uploaded_prod = st.file_uploader("Cambiar Imagen del Producto", type=["png", "jpg"], key=f"up_{did}")
                if uploaded_prod:
                    c_path = os.path.join("brain", "drafts", f"custom_img_{did}.png")
                    with open(c_path, "wb") as f:
                        f.write(uploaded_prod.getbuffer())
                    st.rerun()
                
                # 3. Quick Toggles
                ca, cb = st.columns(2)
                with ca:
                    rem_bg_val = st.checkbox("🪄 Quitar Fondo", value=design.get("remove_bg", False), key=f"rembg_chk_{did}")
                    if rem_bg_val != design.get("remove_bg", False):
                        design["remove_bg"] = rem_bg_val
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()
                    
                    new_scale = st.slider("Escala Producto", 0.5, 1.5, float(design.get("product_scale", 1.0)), 0.05, key=f"scale_{did}")
                    if new_scale != design.get("product_scale"):
                        design["product_scale"] = new_scale
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()

                    new_title_y = st.slider("Posición Título (Y)", -200, 200, int(design.get("title_y_offset", 0)), 10, key=f"ty_{did}")
                    if new_title_y != design.get("title_y_offset", 0):
                        design["title_y_offset"] = new_title_y
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()

                    new_title_scale = st.slider("Escala Título", 0.5, 2.0, float(design.get("title_scale", 1.0)), 0.1, key=f"tscale_{did}")
                    if new_title_scale != design.get("title_scale", 1.0):
                        design["title_scale"] = new_title_scale
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()

                with cb:
                    limpieza_val = not design.get("show_logo", True)
                    limpieza_on = st.checkbox("🤖 Limpieza Foto (y Mascota)", value=limpieza_val, key=f"logo_{did}")
                    if (not limpieza_on) != design.get("show_logo"):
                        design["show_logo"] = not limpieza_on
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()
                    
                    new_prod_y = st.slider("Posición Producto (Y)", -300, 300, int(design.get("product_y_offset", 0)), 10, key=f"py_{did}")
                    if new_prod_y != design.get("product_y_offset", 0):
                        design["product_y_offset"] = new_prod_y
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()

                    new_prod_x = st.slider("Posición Producto (X)", -500, 500, int(design.get("product_x_offset", 0)), 10, key=f"px_{did}")
                    if new_prod_x != design.get("product_x_offset", 0):
                        design["product_x_offset"] = new_prod_x
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()
                    
                    show_footer = st.checkbox("📍 Mostrar Pie", value=design.get("show_footer", True), key=f"footer_{did}")
                    if show_footer != design.get("show_footer"):
                        design["show_footer"] = show_footer
                        draft["design_settings"] = design
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.rerun()

            design_editor_fragment()

        with tab_text:
            @st.fragment
            def text_editor_fragment():
                st.markdown("### Editor de Texto")
                current_caption = draft.get("draft_caption", "")
                new_caption = st.text_area("Caption de Instagram", value=current_caption, height=250, key=editor_key)
                
                if st.button("💾 Guardar Cambios Manuales", use_container_width=True, key=f"save_manual_{did}"):
                    draft["draft_caption"] = new_caption
                    with open(selected_file, "w", encoding="utf-8") as f:
                        json.dump(draft, f, indent=2, ensure_ascii=False)
                    st.success("¡Texto guardado!")

            text_editor_fragment()

        with tab_video:
            st.markdown("### 🎬 Generador de Reels")
            st.info("Creá un video de 5 segundos con zoom animado y placas de texto.")
            
            reel_path = draft.get("reel_path")
            if reel_path and os.path.exists(reel_path):
                st.video(reel_path)
                if st.button("🗑️ Borrar Video", key=f"del_reel_{did}"):
                    try:
                        if os.path.exists(reel_path):
                            os.remove(reel_path)
                        draft["reel_path"] = None
                        with open(selected_file, "w", encoding="utf-8") as f:
                            json.dump(draft, f, indent=2, ensure_ascii=False)
                        st.toast("Video borrado con éxito")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al borrar: {e}")
            else:
                st.warning("No hay un Reel generado para este borrador.")

            if st.button("🚀 Generar Reel Animado", use_container_width=True, key=f"gen_reel_{did}"):
                with st.status("🎬 Generando video (150 frames)...", expanded=True) as v_status:
                    try:
                        from video_composer import create_reel_video
                        import time
                        
                        # Remove OLD one if exists to keep clean
                        if reel_path and os.path.exists(reel_path):
                            try: os.remove(reel_path)
                            except: pass
                        
                        # Generate UNIQUE path to force reload (avoids browser cache)
                        ts = int(time.time())
                        v_output = os.path.join("brain", "reels", f"reel_{did}_{ts}.mp4")
                        os.makedirs(os.path.dirname(v_output), exist_ok=True)
                        
                        # Use custom image if exists, else product default
                        custom_img = os.path.join("brain", "drafts", f"custom_img_{did}.png")
                        if not os.path.exists(custom_img): custom_img = None
                        
                        # Ensure design settings include the full caption for the video engine
                        design["full_caption"] = draft.get("draft_caption", "")
                        
                        v_res = create_reel_video(product, v_output, override_image_path=custom_img, design_settings=design)
                        
                        if v_res:
                            # Verify normalization of path for Windows
                            v_res_norm = os.path.normpath(v_res)
                            draft["reel_path"] = v_res_norm
                            with open(selected_file, "w", encoding="utf-8") as f:
                                json.dump(draft, f, indent=2, ensure_ascii=False)
                            v_status.update(label="✅ Video generado con éxito!", state="complete")
                            st.rerun()
                        else:
                            v_status.error("Fallo al generar frames.")
                    except Exception as ve:
                        v_status.error(f"Error: {ve}")

        st.markdown("---")
        @st.fragment
        def chat_assistant_fragment():
            st.markdown("### 💬 Asistente Chat")
            chat_container = st.container(height=350, border=True)
            chat_history_key = f"chat_history_{did}"
            if chat_history_key not in st.session_state:
                st.session_state[chat_history_key] = [
                    {"role": "assistant", "content": "¡Hola! ¿Qué ajustamos hoy? Decime por acá si querés cambiar el tono, las specs o el diseño. 🤖"}
                ]
            
            with chat_container:
                for msg in st.session_state[chat_history_key]:
                    st.chat_message(msg["role"]).write(msg["content"])

            if user_prompt := st.chat_input("Refiná el texto del post..."):
                st.session_state[chat_history_key].append({"role": "user", "content": user_prompt})
                # We can't use st.chat_message here as a placeholder easily inside fragment before logic, 
                # but we can rely on session state rerun of the fragment.
                
                try:
                    current_text = draft.get("draft_caption", "")
                    w_theme = st.session_state.get("weekly_theme", "")
                    
                    with st.spinner("🤖 Escribiendo..."):
                         ai_res = refine_post(current_text, user_prompt, product_data=product, weekly_theme=w_theme)
                    
                    # Update draft
                    draft["draft_caption"] = ai_res.get("caption", current_text)
                    
                    with open(selected_file, "w", encoding="utf-8") as f:
                        json.dump(draft, f, indent=2, ensure_ascii=False)
                    
                    st.session_state[chat_history_key].append({"role": "assistant", "content": "¡Texto actualizado! Podés verlo en la pestaña **✍️ Texto**."})
                    st.session_state[f"version_{file_id}"] += 1
                    st.rerun() # This will rerun JUST the fragment
                except Exception as e:
                    st.error(f"Error: {e}")

        chat_assistant_fragment()

    # Footer Actions
    st.markdown("---")
    
    # --- POST FORMAT SELECTION ---
    st.markdown("##### 🚀 Configuración de Publicación")
    format_options = ["🖼️ Imagen (Feed IG)", "🎥 Reel (IG)", "🎥 TikTok Video"]
    current_format = draft.get("preferred_format", "image")
    
    # Map stored format to UI options
    mapping = {"image": 0, "video": 1, "tiktok": 2}
    def_idx = mapping.get(current_format, 0)
    
    col_fmt1, col_fmt2 = st.columns([1, 1])
    with col_fmt1:
        st.write("¿Dónde querés publicar este post?")
        selected_fmt = st.pills("Destino", options=format_options, selection_mode="single", default=format_options[def_idx], key=f"fmt_sel_{did}")
        
        # Resolve format logic
        if "TikTok" in selected_fmt: new_fmt = "tiktok"
        elif "Reel" in selected_fmt: new_fmt = "video"
        else: new_fmt = "image"
        
        if new_fmt != current_format:
            draft["preferred_format"] = new_fmt
            with open(selected_file, "w", encoding="utf-8") as f:
                json.dump(draft, f, indent=2, ensure_ascii=False)
            st.rerun()

    if new_fmt == "video" and not draft.get("reel_path"):
        st.warning("⚠️ Seleccionaste 'Video' pero no has generado un Reel para este post. Generalo en la pestaña 'Video'.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        if new_fmt == "tiktok":
            btn_label = "✅ Aprobar y Publicar en TIKTOK 🎥"
        elif new_fmt == "video":
            btn_label = "✅ Aprobar y Publicar REEL 🎥"
        else:
            btn_label = "✅ Aprobar y Publicar IMAGEN 🖼️"
            
        btn_type = "primary"
        
        if st.button(btn_label, type=btn_type, use_container_width=True, disabled=(status=="approved")):
            draft["approval_status"] = "approved"
            with open(selected_file, "w", encoding="utf-8") as f:
                json.dump(draft, f, indent=2, ensure_ascii=False)
            
            # --- EXTERNAL SAVE LOGIC ---
            try:
                import shutil
                external_dir = r"C:\Users\Pachi\Desktop\Bit Comunicaciones\canva bit repuestos\Instagram\2026"
                os.makedirs(external_dir, exist_ok=True)
                
                # Create a clean filename base
                clean_name = "".join([c if c.isalnum() else "_" for c in product.get("name", "post")[:30]])
                ts = datetime.now().strftime("%H%M%S")
                base_path = os.path.join(external_dir, f"{clean_name}_{ts}")
                
                # 1. Save Image
                if 'final_display_path' in locals() and os.path.exists(final_display_path):
                    shutil.copy2(final_display_path, base_path + ".png")
                
                # 2. Save Caption
                with open(base_path + ".txt", "w", encoding="utf-8") as tf:
                    tf.write(new_caption)
                
                # 3. Save Reel (Video) if exists
                reel_path = draft.get("reel_path")
                if reel_path and os.path.exists(reel_path):
                    shutil.copy2(reel_path, base_path + ".mp4")
                
                st.toast(f"Backup guardado en Escritorio", icon="📂")
            except Exception as e:
                st.error(f"Error al guardar backup externo: {e}")

            st.balloons()
            st.rerun()
            
    with c2:
         if st.button("🗑️ Descartar", use_container_width=True):
            os.remove(selected_file)
            st.rerun()
    
    with c3:
        if st.button("🚫 Cancelar", use_container_width=True):
            # Just go back to "Simple" mode or clear selection if we had one
            # Streamlit rerun will handle resetting local UI state
            st.rerun()
