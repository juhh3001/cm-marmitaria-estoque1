import os
import uuid
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="CM Marmitaria | Gestão Executiva",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")
PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerante pequeno", "Refrigerante lata", "Pudim", "Água"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# CSS Profissional com Wallpaper de Fundo, Letras Brancas na Sidebar e Card de Data Ajustado
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Fundo Geral da Aplicação com Wallpaper / Textura Elegante */
.stApp {
    background-color: #F8FAFC !important;
    background-image: radial-gradient(#E2E8F0 1px, transparent 1px) !important;
    background-size: 20px 20px !important;
}

/* Garante margem do topo para nada ser cortado */
.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1500px !important;
}

/* Menu Lateral Amarelo/Escuro com Texto 100% Branco */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E170A 0%, #2D210F 100%) !important;
    border-right: 3px solid #FFCC00 !important;
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important; /* LETRAS BRANCAS NO MENU ESQUERDO */
}

/* Botões do Menu Lateral em Letras Brancas e Destaque Amarelo */
[data-testid="stSidebar"] div.stButton > button {
    background-color: #3D2D14 !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    border-radius: 10px !important;
    border: 1px solid #FFCC00 !important;
    margin-bottom: 0.4rem !important;
    padding: 0.55rem 1rem !important;
    text-align: left !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #FFCC00 !important;
    color: #1E170A !important;
}

/* Logo no Canto Superior da Sidebar */
.sidebar-logo-box {
    text-align: center;
    padding: 0.5rem 0 1rem 0;
    border-bottom: 2px solid #FFCC00;
    margin-bottom: 1rem;
}
.sidebar-logo-box h2 {
    color: #FFCC00 !important;
    font-weight: 900;
    font-size: 1.5rem;
    margin: 0;
}
.sidebar-logo-box p {
    color: #FFFFFF !important;
    font-size: 0.7rem;
    font-weight: 800;
    margin: 0;
}

/* Card Destacado da "Última Atualização" Ajustado Mais para Baixo */
.update-card-box {
    background: #FFFFFF;
    border: 2px solid #FFCC00;
    border-radius: 14px;
    padding: 0.8rem 1.2rem;
    text-align: right;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    margin-top: 0.5rem; /* Afasta da faixa branca do topo */
}
.update-card-title {
    font-size: 0.72rem;
    font-weight: 800;
    color: #854D0E;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.update-card-value {
    font-size: 0.95rem;
    font-weight: 900;
    color: #0F172A;
    margin-top: 0.1rem;
}

/* Metric Cards do Topo */
.metric-card-clean {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-left: 6px solid #FFCC00;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
.metric-title-clean {
    font-size: 0.78rem;
    font-weight: 800;
    color: #64748B;
    text-transform: uppercase;
}
.metric-value-clean {
    font-size: 1.6rem;
    font-weight: 900;
    color: #0F172A;
    margin-top: 0.2rem;
}

/* Card das Lojas */
.overview-store-card {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 14px;
    padding: 1.1rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.03);
}
.overview-store-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.6rem;
    margin-bottom: 0.8rem;
    border-bottom: 2px solid #F1F5F9;
}
.overview-store-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #0F172A;
}
.overview-store-resp {
    background: #FEF3C7;
    color: #92400E;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
}

.marmita-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}
.marmita-label {
    font-size: 0.85rem;
    font-weight: 700;
    color: #334155;
}
.marmita-qty {
    font-size: 0.95rem;
    font-weight: 800;
    color: #0F172A;
}
.last-update-tag {
    font-size: 0.75rem;
    color: #64748B;
    font-weight: 600;
    margin-top: 0.6rem;
    text-align: right;
}

/* Botões do Sistema */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background: #FFCC00 !important;
    color: #1E170A !important;
    font-weight: 800 !important;
    border: 1px solid #E69900 !important;
    border-radius: 8px !important;
    padding: 0.45rem 0.9rem !important;
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
        except Exception:
            return None
    return st.session_state.supabase_client


def sign_out():
    client = get_client()
    try:
        if client:
            client.auth.sign_out()
    except Exception:
        pass
    for key in ["supabase_user_id", "supabase_email", "supabase_access_token", "supabase_refresh_token", "profile", "supabase_client", "menu_page"]:
        st.session_state.pop(key, None)
    st.rerun()


def login_screen(client: Client):
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        st.markdown("""
        <div style='text-align: center; background: #FFCC00; border: 2px solid #E69900; padding: 2.5rem; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.08);'>
            <h1 style='color: #1E170A; font-size: 2.2rem; font-weight: 900; margin: 0;'>🏠 CM MARMITARIA</h1>
            <p style='color: #4A2300; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px;'>CONTROLE DE ESTOQUE E FECHAMENTO</p>
            <hr style='border: 1px solid #1E170A; margin: 1.2rem 0;'>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Usuário ou e-mail", placeholder="Ex.: bia.loja1")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("ENTRAR NO SISTEMA", type="primary", use_container_width=True)
            
        if submitted:
            login_value = login.strip()
            if not login_value or not password:
                st.warning("Preencha o usuário e a senha.")
                return
            auth_email = login_value if "@" in login_value else f"{login_value.lower()}@{USERNAME_EMAIL_DOMAIN}"
            try:
                response = client.auth.sign_in_with_password({"email": auth_email, "password": password})
                if not response.user or not response.session:
                    st.error("Credenciais inválidas.")
                    return
                st.session_state.supabase_user_id = str(response.user.id)
                st.session_state.supabase_email = response.user.email or auth_email
                st.session_state.supabase_access_token = response.session.access_token
                st.session_state.supabase_refresh_token = response.session.refresh_token
                st.rerun()
            except Exception:
                st.error("Erro no login. Verifique os dados.")


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
        return "Todas as Lojas"
    try:
        result = client.table("stores").select("name").eq("id", store_id).single().execute()
        return result.data["name"]
    except Exception:
        return "Sua Loja"


def upload_photo(client: Client, uploaded_file, store_id: str, user_id: str):
    if uploaded_file is None:
        return None
    suffix = os.path.splitext(uploaded_file.name)[1].lower()
    path = f"{store_id}/{user_id}/{uuid.uuid4().hex}{suffix}"
    client.storage.from_(BUCKET).upload(
        path,
        uploaded_file.getvalue(),
        {"content-type": uploaded_file.type or "image/jpeg", "upsert": "false"},
    )
    return path


def save_complete_form(client: Client, profile: dict, form_data: dict, photos_data: dict, notes_data: dict, fin_data: dict, fin_photos: dict, fin_notes: dict):
    user_id = str(profile["user_id"])
    store_id = str(profile["store_id"])
    created_at = datetime.now(timezone.utc).isoformat()
    
    card_ph_path = upload_photo(client, fin_photos.get("card"), store_id, user_id)
    cash_ph_path = upload_photo(client, fin_photos.get("cash"), store_id, user_id)
    
    financial_summary_note = (
        f"[FECHAMENTO FINANCEIRO DA LOJA] | "
        f"Maquininha: R$ {fin_data.get('card', 0.0):.2f} (Obs: {fin_notes.get('card', 'Sem obs')}) [Foto: {card_ph_path or 'Sem foto'}] | "
        f"Dinheiro: R$ {fin_data.get('cash', 0.0):.2f} (Obs: {fin_notes.get('cash', 'Sem obs')}) [Foto: {cash_ph_path or 'Sem foto'}]"
    )

    rows = []
    for product in PRODUCTS:
        qty = int(form_data.get(product, 0))
        p_path = upload_photo(client, photos_data.get(product), store_id, user_id)
        prod_obs = notes_data.get(product, "")
        
        full_note = f"Obs Item: {prod_obs if prod_obs else 'Sem observação'} || {financial_summary_note}"
        
        rows.append({
            "store_id": store_id,
            "user_id": user_id,
            "product": product,
            "quantity_remaining": qty,
            "photo_path": p_path,
            "notes": full_note,
            "created_at": created_at,
        })
    return client.table("stock_entries").insert(rows).execute()


# Interface das Funcionárias
def staff_screen(client: Client, profile: dict):
    store_id = str(profile.get("store_id", ""))
    store_name = get_store_name(client, store_id)
    display_name = profile.get("display_name") or "Funcionária"

    st.markdown(f"## 🍲 Fechamento de Estoque · **{store_name}**")
    st.caption(f"Responsável: **{display_name}**")

    with st.form("single_staff_form", clear_on_submit=True):
        st.markdown("### 📦 1. Quantidades em Estoque")
        
        form_data = {}
        photos_data = {}
        notes_data = {}

        for product in PRODUCTS:
            st.markdown(f"**🍲 {product}**")
            c1, c2, c3 = st.columns([1, 1.5, 2])
            with c1:
                form_data[product] = st.number_input("Quantidade", min_value=0, step=1, value=0, key=f"q_{product}")
            with c2:
                photos_data[product] = st.file_uploader("Foto do item", type=["jpg", "jpeg", "png", "webp"], key=f"photo_{product}")
            with c3:
                notes_data[product] = st.text_input("Observação", placeholder="Ex: No freezer...", key=f"note_{product}")
            st.divider()

        st.markdown("### 💰 2. Fechamento Financeiro")
        fc1, fc2 = st.columns(2)
        with fc1:
            card_val = st.number_input("Maquininha (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val_in")
            card_photo = st.file_uploader("Foto Comprovante Maquininha", type=["jpg", "jpeg", "png", "webp"], key="card_ph_in")
            card_note = st.text_input("Obs Maquininha", key="card_note_in")
            
        with fc2:
            cash_val = st.number_input("Dinheiro na Gaveta (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val_in")
            cash_photo = st.file_uploader("Foto Dinheiro / Envelope", type=["jpg", "jpeg", "png", "webp"], key="cash_ph_in")
            cash_note = st.text_input("Obs Dinheiro", key="cash_note_in")

        submitted = st.form_submit_button("✅ ENVIAR FECHAMENTO COMPLETO", type="primary", use_container_width=True)

    if submitted:
        try:
            fin_data = {"card": card_val, "cash": cash_val}
            fin_photos = {"card": card_photo, "cash": cash_photo}
            fin_notes = {"card": card_note, "cash": cash_note}
            save_complete_form(client, profile, form_data, photos_data, notes_data, fin_data, fin_photos, fin_notes)
            st.success("✅ Fechamento enviado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


# Painel Administrador Limpo e Organizado
def admin_dashboard(client: Client, profile: dict):
    known_store_labels = {
        "1": ("Matriz", "Bia"),
        "2": ("Tereza", "Gabi"),
        "5": ("Leme", "Kauany"),
        "10": ("Pirajussara", "Júlia"),
        "8": ("Macedônia", "Kamilly"),
        "4": ("Vazame", "Iasmim e Samara"),
    }

    def display_store_name(raw_name):
        raw = str(raw_name or "").strip()
        import re
        match = re.search(r"(?:loja\s*)?(10|[1-9])", raw, flags=re.IGNORECASE)
        if match and match.group(1) in known_store_labels:
            number = match.group(1)
            location, staff = known_store_labels[number]
            return f"Loja {number} - {location}", staff
        return (raw or "Unidade Comercial", "Cadastro Pendente")

    now_time = datetime.now(TZ_BR).strftime("%d/%m/%Y às %H:%M:%S")

    # Cabeçalho com o Card de Atualização bem Visível e Abaixado
    c_top_l, c_top_r = st.columns([3, 1.3])
    with c_top_l:
        st.markdown("""
        <div>
            <h1 style='font-size: 2.2rem; font-weight: 900; color: #0F172A; margin:0;'>Painel Central de Gestão</h1>
            <p style='font-size: 0.95rem; font-weight: 600; color: #64748B; margin-top: 0.2rem;'>Acompanhamento em tempo real do estoque das unidades</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c_top_r:
        st.markdown(f"""
        <div class="update-card-box">
            <div class="update-card-title">🕒 Última Sincronização</div>
            <div class="update-card-value">{now_time}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _load_and_render_admin_content(client, display_store_name)


def _load_and_render_admin_content(client, display_store_name):
    try:
        stores = client.table("stores").select("id, name").execute().data or []
        entries = client.table("stock_entries").select(
            "id, store_id, user_id, product, quantity_remaining, photo_path, notes, created_at"
        ).order("created_at", desc=True).limit(5000).execute().data or []
        profiles = client.table("profiles").select("user_id, display_name").execute().data or []
    except Exception:
        st.error("Erro ao carregar os dados das lojas.")
        return

    if not stores:
        st.warning("Nenhuma loja cadastrada.")
        return

    store_names = {str(x["id"]): str(x.get("name") or "Unidade") for x in stores}
    display_names = {key: display_store_name(value)[0] for key, value in store_names.items()}
    staff_by_store = {key: display_store_name(value)[1] for key, value in store_names.items()}
    profile_names = {str(x["user_id"]): x.get("display_name") or "Usuário" for x in profiles}
    
    df = pd.DataFrame(entries)
    if not df.empty:
        df["store_id"] = df["store_id"].astype(str)
        df["Loja"] = df["store_id"].map(display_names).fillna("Unidade")
        df["Funcionária"] = df["user_id"].astype(str).map(profile_names).fillna("Usuário")
        df["dt_object"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.tz_convert("America/Sao_Paulo")
        df["Data"] = df["dt_object"].dt.strftime("%d/%m/%Y")
        df["Hora"] = df["dt_object"].dt.strftime("%H:%M:%S")
        latest = df.dropna(subset=["created_at"]).sort_values("created_at").groupby(["store_id", "product"], as_index=False).tail(1)
    else:
        latest = pd.DataFrame(columns=["store_id", "product", "quantity_remaining", "created_at", "notes"])

    total_stores = len(stores)
    today_br = datetime.now(TZ_BR).date()
    
    stores_with_entries_today = set()
    if not df.empty:
        df_today = df[df["dt_object"].dt.date == today_br]
        stores_with_entries_today = set(df_today["store_id"].unique())

    stores_pending_today = total_stores - len(stores_with_entries_today)
    
    total_marmitas = 0
    if not latest.empty:
        marmitas_df = latest[latest["product"].isin(["Marmitex pequena", "Marmitex grande"])]
        total_marmitas = int(marmitas_df["quantity_remaining"].sum())

    total_financial = len(stores_with_entries_today)

    # 4 Cards Métricas do Topo
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card-clean">
            <div class="metric-title-clean">Lojas Cadastradas</div>
            <div class="metric-value-clean">🏪 {total_stores}</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="metric-card-clean" style="border-left-color: #EF4444;">
            <div class="metric-title-clean">Pendente de Registro</div>
            <div class="metric-value-clean" style="color:#DC2626;">⚠️ {stores_pending_today}</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-card-clean" style="border-left-color: #3B82F6;">
            <div class="metric-title-clean">Total de Marmitex</div>
            <div class="metric-value-clean">📦 {total_marmitas}</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="metric-card-clean" style="border-left-color: #10B981;">
            <div class="metric-title-clean">Fechamentos Hoje</div>
            <div class="metric-value-clean">💳 {total_financial}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Navegação das Abas do Menu
    menu = st.session_state.get("menu_page", "lojas")

    if menu in ["lojas", "inicio"]:
        st.markdown("### 📌 Visão Geral do Estoque de Marmitas")
        st.caption("Apenas marmitas grandes e pequenas com a última hora de atualização.")

        grid_cols = st.columns(3)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            m_pequena = 0
            m_grande = 0
            last_time_str = "Sem atualização hoje"

            if not store_latest.empty:
                p_eq = store_latest[store_latest["product"] == "Marmitex pequena"]
                if not p_eq.empty:
                    m_pequena = int(p_eq["quantity_remaining"].values[0])
                p_gr = store_latest[store_latest["product"] == "Marmitex grande"]
                if not p_gr.empty:
                    m_grande = int(p_gr["quantity_remaining"].values[0])
                
                dt_last = store_latest["created_at"].max()
                if pd.notnull(dt_last):
                    dt_obj = pd.to_datetime(dt_last, utc=True).tz_convert("America/Sao_Paulo")
                    last_time_str = dt_obj.strftime("%d/%m/%Y às %H:%M")

            with grid_cols[idx % 3]:
                st.markdown(f"""
                <div class="overview-store-card">
                    <div class="overview-store-header">
                        <span class="overview-store-title">🏪 {name}</span>
                        <span class="overview-store-resp">Resp: {resp}</span>
                    </div>
                    <div class="marmita-box">
                        <span class="marmita-label">🍲 Marmitex Pequena</span>
                        <span class="marmita-qty">{m_pequena} un.</span>
                    </div>
                    <div class="marmita-box">
                        <span class="marmita-label">🍲 Marmitex Grande</span>
                        <span class="marmita-qty">{m_grande} un.</span>
                    </div>
                    <div class="last-update-tag">🕒 Atualizado: {last_time_str}</div>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "detalhes":
        st.markdown("### 🏪 Gerenciamento Completo das Lojas")
        st.caption("Visão individual com refrigerantes, pudim, água e o fechamento financeiro do dia.")

        grid_cols = st.columns(2)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            with grid_cols[idx % 2]:
                st.markdown(f"""
                <div class="overview-store-card">
                    <div class="overview-store-header">
                        <span class="overview-store-title">🏪 {name}</span>
                        <span class="overview-store-resp">Resp: {resp}</span>
                    </div>
                """, unsafe_allow_html=True)

                if not store_latest.empty:
                    for _, r in store_latest.iterrows():
                        p_n = r["product"]
                        qty_v = int(r["quantity_remaining"])
                        st.markdown(f"""
                        <div class="marmita-box">
                            <span class="marmita-label">📦 {p_n}</span>
                            <span class="marmita-qty">{qty_v} un.</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with st.expander("🔎 Ver Fotos e Fechamento Financeiro"):
                        for _, r in store_latest.iterrows():
                            p_n = r["product"]
                            path = r.get("photo_path")
                            notes_raw = r.get("notes") or ""
                            
                            obs_item = notes_raw.split("||")[0].replace("Obs Item:", "").strip() if "||" in notes_raw else notes_raw
                            url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                            
                            st.write(f"• **{p_n}**: {obs_item}")
                            if url:
                                st.image(url, width=150)
                            st.divider()

                        first_note = store_latest["notes"].iloc[0] if not store_latest.empty else ""
                        if "[FECHAMENTO FINANCEIRO" in first_note:
                            fin_part = first_note.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1]
                            st.info(f"💰 **Financeiro:** {fin_part}")

                        if st.button(f"🗑️ Zerar registros da {name}", key=f"del_st_{sid}"):
                            client.table("stock_entries").delete().eq("store_id", sid).execute()
                            st.success("Registros zerados!")
                            st.rerun()
                else:
                    st.info("Nenhum lançamento ativo para esta loja.")

                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "produtos":
        st.markdown("### 📦 Inventário Geral por Produto")
        if not latest.empty:
            st.dataframe(
                latest[["Loja", "product", "quantity_remaining"]].rename(columns={
                    "Loja": "Unidade Comercial", "product": "Produto", "quantity_remaining": "Estoque Atual"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhum produto cadastrado.")

    elif menu == "financeiro":
        st.markdown("### 💳 Demonstrativo Financeiro das Lojas")
        if not df.empty:
            fin_entries = df[df["notes"].str.contains("FECHAMENTO FINANCEIRO", na=False)]
            if not fin_entries.empty:
                for _, r in fin_entries.groupby("store_id").first().iterrows():
                    st.markdown(f"#### 🏪 {r['Loja']} (Resp: {r['Funcionária']})")
                    notes = r["notes"]
                    fin_part = notes.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1] if "[FECHAMENTO FINANCEIRO DA LOJA] |" in notes else notes
                    st.success(f"💰 {fin_part}")
                    st.divider()
            else:
                st.info("Nenhum fechamento registrado hoje.")
        else:
            st.info("Sem dados até o momento.")

    elif menu == "historico":
        st.markdown("### 📜 Histórico Completo de Lançamentos")
        if not df.empty:
            st.dataframe(
                df[["Data", "Hora", "Loja", "Funcionária", "product", "quantity_remaining", "notes"]].rename(columns={
                    "product": "Produto", "quantity_remaining": "Quantidade", "notes": "Observações & Financeiro"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Histórico de lançamentos vazio.")

    elif menu == "relatorios":
        st.markdown("### 📊 Relatório Gráfico do Estoque")
        if not latest.empty:
            st.bar_chart(latest.groupby("product")["quantity_remaining"].sum())
        else:
            st.info("Sem dados suficientes.")

    elif menu == "configuracoes":
        st.markdown("### ⚙️ Configurações do Sistema")
        st.success("Sistema conectado com sucesso ao Supabase · Fuso Horário de Brasília.")


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
        st.error("Perfil não encontrado.")
        if st.button("Sair"):
            sign_out()
        st.stop()

    st.session_state.profile = profile
    display_name = profile.get("display_name") or "Usuário"
    
    # Sidebar Estilizada com Logo e Textos em Branco Puro
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo-box">
            <h2>CM MARMITARIA</h2>
            <p>QUALIDADE | SABOR | TRADIÇÃO</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📌 Visão Geral (Marmitas)", use_container_width=True):
            st.session_state.menu_page = "lojas"
            st.rerun()
        if st.button("🏪 Lojas (Detalhes)", use_container_width=True):
            st.session_state.menu_page = "detalhes"
            st.rerun()
        if st.button("📦 Produtos", use_container_width=True):
            st.session_state.menu_page = "produtos"
            st.rerun()
        if st.button("💳 Financeiro", use_container_width=True):
            st.session_state.menu_page = "financeiro"
            st.rerun()
        if st.button("📜 Histórico", use_container_width=True):
            st.session_state.menu_page = "historico"
            st.rerun()
        if st.button("📊 Relatórios", use_container_width=True):
            st.session_state.menu_page = "relatorios"
            st.rerun()
        if st.button("⚙️ Configurações", use_container_width=True):
            st.session_state.menu_page = "configuracoes"
            st.rerun()

        st.divider()
        st.markdown(f"👤 **{display_name}**")
        st.caption("Acesso Administrador" if profile.get("role") == "admin" else f"Loja: {get_store_name(client, profile.get('store_id'))}")
        st.divider()
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)


if __name__ == "__main__":
    main()
