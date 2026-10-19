import os
import uuid
import io
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="CM Marmitaria | Controle de Estoque",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")
PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerantes Peq", "Pudim", "Refrigerante lata", "Água"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# Estilização CSS Mantida (Com cores de cada setor e bloquinhos arredondados)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Menu Lateral */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFCC00 0%, #F5B800 100%) !important;
    border-right: 2px solid #E6A100;
}
[data-testid="stSidebar"] * {
    color: #2A1200 !important;
}

/* Cabeçalho Principal */
.hero-header {
    background: linear-gradient(120deg, #FFC107 0%, #FF9800 100%);
    padding: 1.5rem 1.8rem;
    border-radius: 18px;
    color: #2A1200;
    margin-bottom: 1.5rem;
    border: 2px solid #E68A00;
    box-shadow: 0 8px 16px rgba(230, 138, 0, 0.15);
}
.hero-header h1 {
    color: #2A1200 !important;
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
}
.hero-header p {
    color: #4A2300 !important;
    font-size: 0.95rem;
    font-weight: 600;
    margin-top: 0.25rem;
}

/* Cartões de Status / Alertas */
.alert-status-box {
    background: #FFF8E1;
    border: 2px solid #FFE082;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 1.5rem;
    color: #2A1200;
    font-weight: 600;
}

/* Bloquinhos Customizados Arredondados com Cores */
.custom-card {
    background: #FFFFFF;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Setor 1: Laranja/Dourado (Abertura) */
.header-abertura {
    background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%);
    border: 2px solid #F59E0B;
}

/* Setor 2: Rosa (Acompanhamento) */
.header-acomp {
    background: linear-gradient(90deg, #F472B6 0%, #FB7185 100%);
    border: 2px solid #F472B6;
}

/* Setor 3: Roxo (Fechamento) */
.header-fechamento {
    background: linear-gradient(90deg, #8B5CF6 0%, #6D28D9 100%);
    border: 2px solid #8B5CF6;
}

.custom-card-header {
    color: #FFFFFF;
    padding: 0.75rem 1.2rem;
    font-weight: 800;
    font-size: 1.05rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.custom-card-body {
    padding: 1rem 1.2rem;
    border-left: 2px solid #E2E8F0;
    border-right: 2px solid #E2E8F0;
    border-bottom: 2px solid #E2E8F0;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
}

.custom-card-resp {
    font-size: 0.85rem;
    color: #334155;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.custom-card-marmitas {
    display: flex;
    gap: 1.2rem;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    padding: 0.6rem 0.9rem;
    border-radius: 10px;
    font-weight: 700;
    color: #1E293B;
}

/* Botões Gerais */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background-color: #FFB300 !important;
    color: #2A1200 !important;
    font-weight: 700 !important;
    border: 2px solid #E69900 !important;
    border-radius: 12px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:hover {
    background-color: #FFA000 !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)


def get_config():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_ANON_KEY", "")
    return url.strip(), key.strip()


def get_client() -> Client | None:
    if "supabase_client" not in st.session_state:
        url, key = get_config()
        if not url or not key:
            return None
        try:
            st.session_state.supabase_client = create_client(url, key)
        except Exception as exc:
            st.error(f"Não foi possível conectar ao Supabase: {type(exc).__name__}")
            return None
    return st.session_state.supabase_client


def sign_out():
    client = get_client()
    try:
        if client:
            client.auth.sign_out()
    except Exception:
        pass
    for key in ["supabase_user_id", "supabase_email", "supabase_access_token", "supabase_refresh_token", "profile", "supabase_client", "staff_flow_mode", "form_success_msg"]:
        st.session_state.pop(key, None)
    st.rerun()


def login_screen(client: Client):
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 1.5rem; background: #FFFFFF; padding: 2rem; border-radius: 20px; border: 2px solid #FFD54F; box-shadow: 0 8px 20px rgba(0,0,0,0.05);'>
            <h1 style='color: #2A1200; font-size: 2.2rem; font-weight: 800; margin-bottom: 0;'>🏠 CM MARMITARIA</h1>
            <p style='color: #8C4A00; font-size: 0.85rem; font-weight: 600; margin-top: 0;'>QUALIDADE | SABOR | TRADIÇÃO · DESDE 2015</p>
            <hr style='border: 1px solid #FFE082; margin: 1rem 0;'>
            <p style='color: #4A2300; font-size: 1rem; font-weight: 600;'>Controle de Estoque das Lojas</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Usuário ou e-mail", placeholder="Ex.: bia.loja1")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
            
        if submitted:
            login_value = login.strip()
            if not login_value or not password:
                st.warning("Preencha o usuário e a senha.")
                return
            auth_email = login_value if "@" in login_value else f"{login_value.lower()}@{USERNAME_EMAIL_DOMAIN}"
            try:
                response = client.auth.sign_in_with_password({"email": auth_email, "password": password})
                if not response.user or not response.session:
                    st.error("Não foi possível entrar. Confira seus dados.")
                    return
                st.session_state.supabase_user_id = str(response.user.id)
                st.session_state.supabase_email = response.user.email or auth_email
                st.session_state.supabase_access_token = response.session.access_token
                st.session_state.supabase_refresh_token = response.session.refresh_token
                st.rerun()
            except Exception:
                st.error("Não foi possível entrar. Confira o usuário e a senha.")


def restore_auth_session(client: Client):
    access_token = st.session_state.get("supabase_access_token")
    refresh_token = st.session_state.get("supabase_refresh_token")
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            for key in ["supabase_user_id", "supabase_email", "supabase_access_token", "supabase_refresh_token", "profile"]:
                st.session_state.pop(key, None)
            return False
    return True


def load_profile(client: Client, user_id: str):
    try:
        result = client.table("profiles").select("user_id, display_name, role, store_id").eq("user_id", user_id).single().execute()
        return result.data
    except Exception:
        return None


def get_store_name(client: Client, store_id):
    if not store_id:
        return "Todas as lojas"
    try:
        result = client.table("stores").select("name").eq("id", store_id).single().execute()
        return result.data["name"]
    except Exception:
        return "Sua loja"


def optimize_image(uploaded_file, max_width=1200, quality=80):
    if uploaded_file is None:
        return None
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > max_width:
            new_height = int((max_width / img.width) * img.height)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return uploaded_file.getvalue()


def upload_photo(client: Client, uploaded_file, store_id: str, user_id: str):
    if uploaded_file is None:
        return None
    try:
        suffix = os.path.splitext(uploaded_file.name)[1].lower()
        if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
            return None
        
        optimized_bytes = optimize_image(uploaded_file)
        path = f"{store_id}/{user_id}/{uuid.uuid4().hex}.jpg"
        
        client.storage.from_(BUCKET).upload(
            path,
            optimized_bytes,
            {"content-type": "image/jpeg", "upsert": "false"},
        )
        return path
    except Exception:
        return None


# SALVAMENTO TOTALMENTE COMPATÍVEL E ROBUSTO (Evita erros de API)
def save_form_data(client: Client, profile: dict, entry_type: str, form_data: dict, photos_data: dict, notes_data: dict, general_note: str, fin_data: dict = None, fin_photos: dict = None, fin_notes: dict = None):
    user_id = str(profile["user_id"])
    store_id = str(profile["store_id"])
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Prepara as linhas de estoque utilizando tipos estritamente inteiros
    for product in PRODUCTS:
        try:
            qty = int(form_data.get(product, 0))
        except (ValueError, TypeError):
            qty = 0
            
        p_path = None
        if photos_data and photos_data.get(product):
            p_path = upload_photo(client, photos_data.get(product), store_id, user_id)
        
        prod_obs = notes_data.get(product, "").strip() if notes_data else ""
        
        note_parts = []
        if entry_type == "abertura":
            note_parts.append("[ABERTURA]")
        elif entry_type == "acompanhamento":
            note_parts.append("[ACOMPANHAMENTO]")
        elif entry_type == "fechamento":
            note_parts.append("[FECHAMENTO]")

        if prod_obs:
            note_parts.append(f"Obs Item: {prod_obs}")
        if general_note and general_note.strip():
            note_parts.append(f"Obs Geral: {general_note.strip()}")

        clean_note = " | ".join(note_parts)
        
        row = {
            "store_id": store_id,
            "user_id": user_id,
            "product": product, # Mantém o nome exato do produto no banco
            "quantity_remaining": qty,
            "photo_path": p_path,
            "notes": clean_note,
            "created_at": created_at,
        }
        client.table("stock_entries").insert(row).execute()
        
    # Insere linhas financeiras apenas no fechamento
    if entry_type == "fechamento" and fin_data:
        card_ph_path = None
        if fin_photos and fin_photos.get("card"):
            card_ph_path = upload_photo(client, fin_photos.get("card"), store_id, user_id)
                
        card_obs = fin_notes.get("card", "").strip() if fin_notes else ""
        try:
            card_val = float(fin_data.get("card", 0.0))
        except (ValueError, TypeError):
            card_val = 0.0
            
        row_card = {
            "store_id": store_id,
            "user_id": user_id,
            "product": "Maquininha",
            "quantity_remaining": int(round(card_val)),
            "photo_path": card_ph_path,
            "notes": f"[FECHAMENTO] Valor R$ {card_val:.2f} | {card_obs}".strip(" |"),
            "created_at": created_at,
        }
        client.table("stock_entries").insert(row_card).execute()
        
        cash_obs = fin_notes.get("cash", "").strip() if fin_notes else ""
        try:
            cash_val = float(fin_data.get("cash", 0.0))
        except (ValueError, TypeError):
            cash_val = 0.0
            
        row_cash = {
            "store_id": store_id,
            "user_id": user_id,
            "product": "Dinheiro",
            "quantity_remaining": int(round(cash_val)),
            "photo_path": None,
            "notes": f"[FECHAMENTO] Valor R$ {cash_val:.2f} | {cash_obs}".strip(" |"),
            "created_at": created_at,
        }
        client.table("stock_entries").insert(row_cash).execute()


# Interface das Funcionárias
def staff_screen(client: Client, profile: dict):
    st.markdown("""
    <style>
    .stApp {
        background-color: #000000 !important;
    }
    h1, h2, h3, h4, p, label, span, div {
        color: #FFFFFF !important;
    }
    .store-form-box {
        background: #1A1A1A !important;
        border: 2px solid #FFB300 !important;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    store_name = get_store_name(client, profile.get("store_id"))
    display_name = profile.get("display_name") or "Funcionária"

    st.markdown(f"""
    <div class="store-form-box" style="text-align: center;">
        <h1 style="color: #FFB300 !important; margin: 0;">🏠 CM MARMITARIA</h1>
        <h3>Olá, {display_name} · {store_name}</h3>
        <p>Escolha abaixo o tipo de lançamento que deseja realizar agora:</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("form_success_msg"):
        st.success(st.session_state.form_success_msg)
        st.balloons()
        st.session_state.pop("form_success_msg", None)

    m1, m2, m3 = st.columns(3)
    with m1:
        if st.button("☀️ 1. Estoque do Início do Dia", use_container_width=True):
            st.session_state.staff_flow_mode = "abertura"
    with m2:
        if st.button("🔄 2. Registrar Estoque/Marmitas", use_container_width=True):
            st.session_state.staff_flow_mode = "meio_dia"
    with m3:
        if st.button("🌙 3. Fechamento do Dia", use_container_width=True):
            st.session_state.staff_flow_mode = "fechamento"

    flow_mode = st.session_state.get("staff_flow_mode", "abertura")
    st.markdown("<br>", unsafe_allow_html=True)

    # 1. ESTOQUE DO INÍCIO DO DIA
    if flow_mode == "abertura":
        st.markdown("### ☀️ 1. Contagem de Abertura (Início do Dia)")
        st.caption("Registre o estoque inicial ao abrir a loja. Foto por produto.")
        
        with st.form("form_abertura", clear_on_submit=True):
            form_data, photos_data, notes_data = {}, {}, {}
            for product in PRODUCTS:
                st.markdown(f"**🍲 {product}**")
                c1, c2, c3 = st.columns([1, 1.5, 2])
                with c1:
                    form_data[product] = st.number_input("Quantidade Inicial", min_value=0, step=1, value=0, key=f"ab_{product}")
                with c2:
                    photos_data[product] = st.file_uploader("Foto do Item", type=["jpg", "jpeg", "png", "webp"], key=f"ab_ph_{product}")
                with c3:
                    notes_data[product] = st.text_input("Observação do Item", placeholder="Ex: Na geladeira...", key=f"ab_nt_{product}")
                st.divider()

            gen_note = st.text_area("Observação Geral do Início do Dia", placeholder="Alguma observação importante do início?")
            if st.form_submit_button("✅ ENVIAR ESTOQUE INICIAL", use_container_width=True):
                try:
                    save_form_data(client, profile, "abertura", form_data, photos_data, notes_data, gen_note)
                    st.session_state.form_success_msg = "🎉 SEU ENVIO DO ESTOQUE INICIAL FOI SALVO E ENVIADO COM SUCESSO PARA A ADMINISTRADORA!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro ao salvar: {err}")

    # 2. REGISTRAR ESTOQUE DO DIA (ACOMPANHAMENTO)
    elif flow_mode == "meio_dia":
        st.markdown("### 🔄 2. Registrar Estoque do Dia / Marmitas")
        st.caption("Envie quantas vezes forem necessárias ao longo do dia com fotos atualizadas.")
        
        with st.form("form_meio_dia", clear_on_submit=True):
            form_data, photos_data, notes_data = {}, {}, {}
            for product in PRODUCTS:
                st.markdown(f"**🍲 {product}**")
                c1, c2, c3 = st.columns([1, 1.5, 2])
                with c1:
                    form_data[product] = st.number_input("Quantidade Atual", min_value=0, step=1, value=0, key=f"md_{product}")
                with c2:
                    photos_data[product] = st.file_uploader("Foto Atual do Item", type=["jpg", "jpeg", "png", "webp"], key=f"md_ph_{product}")
                with c3:
                    notes_data[product] = st.text_input("Observação do Item", placeholder="Ex: Preparando mais...", key=f"md_nt_{product}")
                st.divider()

            gen_note = st.text_area("Observação Geral do Lançamento", placeholder="Obs geral sobre o estoque de agora...")
            if st.form_submit_button("✅ ENVIAR ATUALIZAÇÃO DE ESTOQUE", use_container_width=True):
                try:
                    save_form_data(client, profile, "acompanhamento", form_data, photos_data, notes_data, gen_note)
                    st.session_state.form_success_msg = "🎉 SEU ENVIO DE ATUALIZAÇÃO DE ESTOQUE FOI SALVO E ENVIADO COM SUCESSO PARA A ADMINISTRADORA!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro ao salvar: {err}")

    # 3. FECHAMENTO DO DIA
    elif flow_mode == "fechamento":
        st.markdown("### 🌙 3. Fechamento Final do Dia")
        st.caption("Registre o que sobrou no final do dia (sem foto do estoque) e as informações financeiras.")
        
        with st.form("form_fechamento", clear_on_submit=True):
            st.markdown("#### 📦 1. Sobras de Estoque")
            form_data, notes_data = {}, {}
            for product in PRODUCTS:
                st.markdown(f"**🍲 {product}**")
                c1, c2 = st.columns([1, 3])
                with c1:
                    form_data[product] = st.number_input("Sobra Final", min_value=0, step=1, value=0, key=f"fc_{product}")
                with c2:
                    notes_data[product] = st.text_input("Observação da Sobra", placeholder="Ex: Guardado no freezer...", key=f"fc_nt_{product}")
                st.divider()

            st.markdown("#### 💰 2. Fechamento Financeiro da Loja")
            fc1, fc2 = st.columns(2)
            with fc1:
                card_val = st.number_input("Valor Final Maquininha (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val")
                card_photo = st.file_uploader("Foto do Comprovante da Maquininha", type=["jpg", "jpeg", "png", "webp"], key="card_ph")
                card_note = st.text_input("Obs Maquininha", placeholder="Ex: Cartões Visa/Master...", key="card_nt")
            with fc2:
                cash_val = st.number_input("Dinheiro em Espécie na Gaveta (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val")
                cash_note = st.text_input("Obs Dinheiro / Pix", placeholder="Ex: Troco deixado / Pix pendente...", key="cash_nt")

            gen_note = st.text_area("Observação Geral Final do Fechamento", placeholder="Algum recado final do dia?")
            
            if st.form_submit_button("✅ ENVIAR FECHAMENTO FINAL", use_container_width=True):
                try:
                    fin_data = {"card": card_val, "cash": cash_val}
                    fin_photos = {"card": card_photo}
                    fin_notes = {"card": card_note, "cash": cash_note}
                    save_form_data(client, profile, "fechamento", form_data, None, notes_data, gen_note, fin_data, fin_photos, fin_notes)
                    st.session_state.form_success_msg = "🎉 SEU FECHAMENTO FINAL FOI SALVO E ENVIADO COM SUCESSO PARA A ADMINISTRADORA!"
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro ao salvar: {err}")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


def clean_display_note(note_raw):
    if not note_raw or not isinstance(note_raw, str):
        return ""
    text = note_raw.replace("[ACOMPANHAMENTO]", "").replace("[ABERTURA]", "").replace("[FECHAMENTO]", "").strip(" |").strip()
    return text


# Painel do Administrador
def admin_dashboard(client: Client, profile: dict):
    known_store_labels = {
        "5": ("Leme", "Kauany"),
        "10": ("Pirajussara", "Julia"),
        "8": ("Macedônia", "Kamilly"),
        "2": ("Tereza", "Gabi"),
        "1": ("Matriz", "Bia"),
        "4": ("Vazame", "Iasmim e Samara"),
    }

    def display_store_name(raw_name):
        raw = str(raw_name or "").strip()
        import re
        match = re.search(r"(?:loja\s*)?(10|[1-9])", raw, flags=re.IGNORECASE)
        if match and match.group(1) in known_store_labels:
            number = match.group(1)
            location, staff = known_store_labels[number]
            return f"Loja {number} · {location}", staff
        return (raw or "Unidade sem nome", "Cadastro pendente")

    now_br = datetime.now(TZ_BR)
    last_time_formatted = now_br.strftime("%d/%m/%Y às %H:%M:%S")

    st.markdown("""
    <div class="hero-header">
        <div style="font-size: 0.85rem; font-weight: 700; color: #8C4A00; text-transform: uppercase;">PAINEL CENTRAL · CM MARMITARIA</div>
        <h1>📊 Controle Consolidado de Estoque</h1>
        <p>Acompanhamento das unidades comerciais em tempo real</p>
    </div>
    """, unsafe_allow_html=True)

    col_ctrl1, col_ctrl2 = st.columns([1, 4])
    with col_ctrl1:
        if st.button("🔄 Atualizar Painel"):
            st.rerun()
    with col_ctrl2:
        st.markdown(f"<p style='margin-top: 0.5rem; font-size: 0.9rem; font-weight: 600; color: #8C4A00;'>🕒 Última atualização (Horário de Brasília): <b>{last_time_formatted}</b></p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _load_and_render_admin_content(client, display_store_name, known_store_labels, now_br)


def _load_and_render_admin_content(client, display_store_name, known_store_labels, now_br):
    try:
        stores = client.table("stores").select("id, name").execute().data or []
        entries = client.table("stock_entries").select(
            "id, store_id, user_id, product, quantity_remaining, photo_path, notes, created_at"
        ).order("created_at", desc=True).limit(5000).execute().data or []
    except Exception:
        st.error("Erro ao carregar dados do Supabase.")
        return

    if not stores:
        st.warning("Nenhuma loja cadastrada.")
        return

    store_names = {str(x["id"]): str(x.get("name") or "Unidade") for x in stores}
    display_names = {key: display_store_name(value)[0] for key, value in store_names.items()}
    staff_by_store = {key: display_store_name(value)[1] for key, value in store_names.items()}
    
    df = pd.DataFrame(entries)
    today_date = now_br.date()

    if not df.empty:
        df["store_id"] = df["store_id"].astype(str)
        df["Loja"] = df["store_id"].map(display_names).fillna("Unidade")
        df["dt_object"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.tz_convert("America/Sao_Paulo")
        df["Data"] = df["dt_object"].dt.strftime("%d/%m/%Y")
        df["Hora"] = df["dt_object"].dt.strftime("%H:%M:%S")
    else:
        df["dt_object"] = pd.Series(dtype="datetime64[ns, America/Sao_Paulo]")

    tab_abertura, tab_meio_dia, tab_fechamento = st.tabs([
        "☀️ 1. Aberturas do Dia", 
        "🔄 2. Acompanhamento (Meio do Dia)", 
        "🌙 3. Fechamento Final"
    ])

    # 1. ABA DE ABERTURA DO DIA
    with tab_abertura:
        df_ab_today = df[(df["notes"].str.contains("ABERTURA", na=False)) & (df["dt_object"].dt.date == today_date)] if not df.empty else pd.DataFrame()
        registered_stores_ab = set(df_ab_today["store_id"].unique()) if not df_ab_today.empty else set()
        
        pending_ab = [display_names[str(s["id"])] for s in stores if str(s["id"]) not in registered_stores_ab]
        count_reg = len(registered_stores_ab)
        pending_str = ", ".join(pending_ab) if pending_ab else "Nenhuma! Todas as lojas já registraram."
        
        st.markdown(f"""
        <div class="alert-status-box">
            📌 <b>Status Abertura de Hoje:</b> {count_reg} de {len(stores)} lojas registraram.<br>
            ⚠️ <b>Lojas pendentes de Abertura:</b> {pending_str}
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            s_name = display_names[sid]
            s_resp = staff_by_store[sid]
            st_data = df_ab_today[df_ab_today["store_id"] == sid] if not df_ab_today.empty else pd.DataFrame()
            
            m_g, m_p, time_txt = 0, 0, "Pendente"
            
            if not st_data.empty:
                time_txt = st_data.sort_values("created_at", ascending=False)["Hora"].iloc[0]
                mg_row = st_data[st_data["product"] == "Marmitex grande"]
                mp_row = st_data[st_data["product"] == "Marmitex pequena"]
                if not mg_row.empty:
                    m_g = int(mg_row.iloc[0]["quantity_remaining"])
                if not mp_row.empty:
                    m_p = int(mp_row.iloc[0]["quantity_remaining"])

            with cols[idx % 2]:
                st.markdown(f"""
                <div class="custom-card">
                    <div class="custom-card-header header-abertura">
                        <span>🏪 {s_name}</span>
                        <span style="font-size: 0.8rem; background: rgba(255,255,255,0.25); padding: 0.2rem 0.6rem; border-radius: 6px;">🕒 {time_txt}</span>
                    </div>
                    <div class="custom-card-body">
                        <div class="custom-card-resp">👤 Responsável: <strong>{s_resp}</strong></div>
                        <div class="custom-card-marmitas">
                            <div>🍲 Marmitas Pequenas: <strong>{m_p} un.</strong></div>
                            <div>🍲 Marmitas Grandes: <strong>{m_g} un.</strong></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"🔎 Ver Estoque Inicial Completo - {s_name}", expanded=False):
                    if not st_data.empty:
                        last_items = st_data.sort_values("created_at").groupby("product").last().reset_index()
                        for _, r in last_items.iterrows():
                            p_clean = r['product']
                            if p_clean in PRODUCTS:
                                obs_text = clean_display_note(r['notes'])
                                obs_str = f" | *Obs:* {obs_text}" if obs_text else ""
                                c_item1, c_item2 = st.columns([3, 1])
                                c_item1.write(f"• **{p_clean}**: **{int(r['quantity_remaining'])} un.**{obs_str}")
                                if pd.notnull(r.get("photo_path")) and str(r["photo_path"]).strip():
                                    url = signed_photo_url(client, r["photo_path"])
                                    if url:
                                        with c_item2.popover("📷 Ver Foto"):
                                            st.image(url, use_container_width=True)
                    else:
                        st.info("Nenhum registro de abertura para esta loja hoje.")

    # 2. ABA DE ACOMPANHAMENTO DO DIA
    with tab_meio_dia:
        if not df.empty:
            df_md_today = df[(df["notes"].str.contains("ACOMPANHAMENTO", na=False)) & (df["dt_object"].dt.date == today_date)]
        else:
            df_md_today = pd.DataFrame()

        registered_stores_md = set(df_md_today["store_id"].unique()) if not df_md_today.empty else set()
        
        pending_md = [display_names[str(s["id"])] for s in stores if str(s["id"]) not in registered_stores_md]
        count_reg_md = len(registered_stores_md)
        pending_str_md = ", ".join(pending_md) if pending_md else "Nenhuma! Todas as lojas enviaram acompanhamento."
        
        st.markdown(f"""
        <div class="alert-status-box">
            📌 <b>Status Acompanhamento de Hoje:</b> {count_reg_md} de {len(stores)} lojas enviaram atualização.<br>
            ⚠️ <b>Lojas sem atualização hoje:</b> {pending_str_md}
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            s_name = display_names[sid]
            s_resp = staff_by_store[sid]
            st_data = df_md_today[df_md_today["store_id"] == sid] if not df_md_today.empty else pd.DataFrame()
            
            m_g, m_p, time_txt = 0, 0, "Pendente"
            
            if not st_data.empty:
                time_txt = st_data.sort_values("created_at", ascending=False)["Hora"].iloc[0]
                mg_row = st_data[st_data["product"] == "Marmitex grande"]
                mp_row = st_data[st_data["product"] == "Marmitex pequena"]
                if not mg_row.empty:
                    m_g = int(mg_row.iloc[0]["quantity_remaining"])
                if not mp_row.empty:
                    m_p = int(mp_row.iloc[0]["quantity_remaining"])

            with cols[idx % 2]:
                st.markdown(f"""
                <div class="custom-card">
                    <div class="custom-card-header header-acomp">
                        <span>🏪 {s_name}</span>
                        <span style="font-size: 0.8rem; background: rgba(255,255,255,0.25); padding: 0.2rem 0.6rem; border-radius: 6px;">🕒 {time_txt}</span>
                    </div>
                    <div class="custom-card-body">
                        <div class="custom-card-resp">👤 Responsável: <strong>{s_resp}</strong></div>
                        <div class="custom-card-marmitas">
                            <div>🍲 Marmitas Pequenas: <strong>{m_p} un.</strong></div>
                            <div>🍲 Marmitas Grandes: <strong>{m_g} un.</strong></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"🔎 Ver Estoque Completo - {s_name}", expanded=False):
                    if not st_data.empty:
                        last_items = st_data.sort_values("created_at").groupby("product").last().reset_index()
                        for _, r in last_items.iterrows():
                            p_clean = r['product']
                            if p_clean in PRODUCTS:
                                obs_text = clean_display_note(r['notes'])
                                obs_str = f" | *Obs:* {obs_text}" if obs_text else ""
                                c_item1, c_item2 = st.columns([3, 1])
                                c_item1.write(f"• **{p_clean}**: **{int(r['quantity_remaining'])} un.**{obs_str}")
                                if pd.notnull(r.get("photo_path")) and str(r["photo_path"]).strip():
                                    url = signed_photo_url(client, r["photo_path"])
                                    if url:
                                        with c_item2.popover("📷 Ver Foto"):
                                            st.image(url, use_container_width=True)
                    else:
                        st.info("Nenhuma atualização enviada hoje para esta loja.")

    # 3. ABA DE FECHAMENTO FINAL
    with tab_fechamento:
        df_fc_today = df[(df["notes"].str.contains("FECHAMENTO", na=False)) & (df["dt_object"].dt.date == today_date)] if not df.empty else pd.DataFrame()
        registered_stores_fc = set(df_fc_today["store_id"].unique()) if not df_fc_today.empty else set()
        
        pending_fc = [display_names[str(s["id"])] for s in stores if str(s["id"]) not in registered_stores_fc]
        count_reg_fc = len(registered_stores_fc)
        pending_str_fc = ", ".join(pending_fc) if pending_fc else "Nenhuma! Todas as lojas fecharam o dia."
        
        st.markdown(f"""
        <div class="alert-status-box">
            📌 <b>Status Fechamento de Hoje:</b> {count_reg_fc} de {len(stores)} lojas fecharam o dia.<br>
            ⚠️ <b>Lojas pendentes de Fechamento:</b> {pending_str_fc}
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            s_name = display_names[sid]
            s_resp = staff_by_store[sid]
            st_data = df_fc_today[df_fc_today["store_id"] == sid] if not df_fc_today.empty else pd.DataFrame()
            
            val_card, val_cash, time_txt = 0.0, 0.0, "Pendente"
            
            if not st_data.empty:
                time_txt = st_data.sort_values("created_at", ascending=False)["Hora"].iloc[0]
                card_row = st_data[st_data["product"] == "Maquininha"]
                cash_row = st_data[st_data["product"] == "Dinheiro"]
                if not card_row.empty:
                    val_card = float(card_row.iloc[0]["quantity_remaining"])
                if not cash_row.empty:
                    val_cash = float(cash_row.iloc[0]["quantity_remaining"])

            with cols[idx % 2]:
                st.markdown(f"""
                <div class="custom-card">
                    <div class="custom-card-header header-fechamento">
                        <span>🌙 {s_name}</span>
                        <span style="font-size: 0.8rem; background: rgba(255,255,255,0.25); padding: 0.2rem 0.6rem; border-radius: 6px;">🕒 {time_txt}</span>
                    </div>
                    <div class="custom-card-body">
                        <div class="custom-card-resp">👤 Responsável: <strong>{s_resp}</strong></div>
                        <div class="custom-card-marmitas">
                            <div>💳 Maquininha: <strong>R$ {val_card:.2f}</strong></div>
                            <div>💵 Dinheiro: <strong>R$ {val_cash:.2f}</strong></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"🔎 Ver Sobras e Detalhes do Caixa - {s_name}", expanded=False):
                    if not st_data.empty:
                        for _, r in st_data.iterrows():
                            clean_p_name = r["product"]
                            obs_text = clean_display_note(r['notes'])
                            obs_str = f" | *Obs:* {obs_text}" if obs_text else ""
                            c_item1, c_item2 = st.columns([3, 1])
                            
                            if "Maquininha" in clean_p_name or "Dinheiro" in clean_p_name:
                                c_item1.write(f"💰 **{clean_p_name}**: R$ {r['quantity_remaining']:.2f}{obs_str}")
                                if pd.notnull(r.get("photo_path")) and str(r["photo_path"]).strip():
                                    url = signed_photo_url(client, r["photo_path"])
                                    if url:
                                        with c_item2.popover("📷 Ver Comprovante"):
                                            st.image(url, use_container_width=True)
                            else:
                                c_item1.write(f"• **{clean_p_name}**: Sobraram **{int(r['quantity_remaining'])} un.**{obs_str}")
                    else:
                        st.info("Fechamento ainda não enviado para esta loja hoje.")


def main():
    client = get_client()
    if client is None:
        st.error("Erro na conexão com o Supabase.")
        st.stop()

    user_id = st.session_state.get("supabase_user_id")
    if not user_id:
        login_screen(client)
        st.stop()

    if not restore_auth_session(client):
        st.warning("Sessão expirada.")
        st.rerun()

    profile = load_profile(client, user_id)
    if not profile:
        st.error("Perfil de acesso não encontrado no Supabase.")
        if st.button("Sair"):
            sign_out()
        st.stop()

    st.session_state.profile = profile
    display_name = profile.get("display_name") or "Usuário"
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:center; color: #2A1200; margin-bottom: 0;'>🏠 CM MARMITARIA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size: 0.75rem; color: #4A2300; font-weight: 700;'>QUALIDADE | SABOR | TRADIÇÃO</p>", unsafe_allow_html=True)
        st.divider()
        st.markdown(f"👤 **{display_name}**")
        st.caption("Acesso: Administrador" if profile.get("role") == "admin" else f"Loja: {get_store_name(client, profile.get('store_id'))}")
        st.divider()
        if st.button("🚪 Sair da Conta", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)


if __name__ == "__main__":
    main()
