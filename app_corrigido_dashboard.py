import os
import uuid
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="CM Marmitaria | Controle de Estoque & Fechamento",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fuso horário oficial de Brasília
TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")

PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerantes Peq", "Pudim", "Refrigerante lata", "Água"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# Design System - CSS Totalmente Reformulado (Layout Limpo, Moderno e Espaçado)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Sidebar Estilizada */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

/* Header Central do Admin */
.hero-header {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 2rem;
    border-radius: 20px;
    color: #FFFFFF;
    margin-bottom: 2rem;
    border: 1px solid #334155;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}
.hero-header h1 {
    color: #FACC15 !important;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-header p {
    color: #94A3B8 !important;
    font-size: 0.95rem;
    margin-top: 0.4rem;
}

/* Card das Lojas no Admin - Espaçados e Modernos */
.store-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    transition: all 0.2s ease;
}
.store-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1rem;
    margin-bottom: 1.2rem;
    border-bottom: 2px solid #F1F5F9;
}
.store-card-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: #0F172A;
}
.store-card-badge {
    background: #FEF3C7;
    color: #92400E;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
}

/* Grade de Produtos dentro do Card */
.product-grid-item {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
}

/* Painel do Financeiro Final */
.financial-summary-box {
    background: linear-gradient(135deg, #FEFCE8 0%, #FEF3C7 100%);
    border: 1px solid #FDE68A;
    border-radius: 16px;
    padding: 1.25rem;
    margin-top: 1rem;
}

/* Banner de Alerta em Tela para as Funcionárias */
.alert-banner {
    background: #FEF2F2;
    color: #991B1B;
    padding: 1.5rem;
    border-radius: 18px;
    border: 2px solid #FCA5A5;
    text-align: center;
    font-weight: 800;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 20px rgba(239, 68, 68, 0.1);
}

/* Botões do Sistema */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 12px rgba(202, 138, 4, 0.25) !important;
}
div.stButton > button:hover {
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
    for key in ["supabase_user_id", "supabase_email", "supabase_access_token", "supabase_refresh_token", "profile", "supabase_client"]:
        st.session_state.pop(key, None)
    st.rerun()


def login_screen(client: Client):
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
        <div style='text-align: center; background: #FFFFFF; padding: 2.5rem; border-radius: 24px; border: 1px solid #E2E8F0; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);'>
            <h1 style='color: #0F172A; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.2rem;'>🏠 CM MARMITARIA</h1>
            <p style='color: #CA8A04; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;'>CONTROLE DE ESTOQUE E FECHAMENTO</p>
            <hr style='border: 0; height: 1px; background: #E2E8F0; margin: 1.5rem 0;'>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Usuário ou e-mail", placeholder="Ex.: bia.loja1")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Acessar o Sistema", type="primary", use_container_width=True)
            
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
                st.error("Erro na autenticação. Verifique os dados digitados.")


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


def check_and_get_alert(client: Client):
    try:
        res = client.table("system_settings").select("value").eq("key", "stock_request_alert").single().execute()
        if res.data and res.data.get("value") == "active":
            return True
    except Exception:
        pass
    return False


def set_alert_status(client: Client, active: bool):
    try:
        val = "active" if active else "inactive"
        client.table("system_settings").upsert({"key": "stock_request_alert", "value": val}).execute()
    except Exception:
        pass


def upload_photo(client: Client, uploaded_file, store_id: str, user_id: str):
    if uploaded_file is None:
        return None
    suffix = os.path.splitext(uploaded_file.name)[1].lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise ValueError("Use uma imagem JPG, PNG ou WEBP.")
    if uploaded_file.size > 8 * 1024 * 1024:
        raise ValueError("A imagem deve ter no máximo 8 MB.")
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


# Interface Limpa e Espaçada das Funcionárias
def staff_screen(client: Client, profile: dict):
    st.markdown("""
    <style>
    .stApp {
        background-color: #0F172A !important;
    }
    h1, h2, h3, h4, p, label, span, div {
        color: #F8FAFC !important;
    }
    .staff-card {
        background: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    store_id = str(profile.get("store_id", ""))
    store_name = get_store_name(client, store_id)
    display_name = profile.get("display_name") or "Funcionária"

    if check_and_get_alert(client):
        st.markdown("""
        <div class="alert-banner">
            🚨 ATENÇÃO: A ADMINISTRAÇÃO SOLICITOU A ATUALIZAÇÃO DO ESTOQUE AGORA!<br>
            <span style="font-size: 0.95rem; font-weight: 500;">Por favor, preencha as quantidades atuais dos produtos e o fechamento no final.</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="staff-card" style="text-align: center;">
        <h1 style="color: #FACC15 !important; margin: 0; font-size: 2.2rem;">🏠 CM MARMITARIA</h1>
        <h3 style="margin-top: 0.5rem; color: #E2E8F0 !important;">{display_name} · <span style="color: #FACC15;">{store_name}</span></h3>
        <p style="color: #94A3B8 !important; margin-bottom: 0;">Preencha a contagem atual dos produtos e o fechamento financeiro no final.</p>
    </div>
    """, unsafe_allow_html=True)

    # Popover de Histórico de Lançamentos do Dia
    c_hist_top, _ = st.columns([2, 1])
    with c_hist_top:
        with st.popover("📜 Ver Histórico de Hoje (Lançamentos Enviados)"):
            st.markdown("### 📜 Lançamentos Enviados Hoje")
            try:
                today_start = datetime.now(TZ_BR).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()
                user_entries = client.table("stock_entries").select(
                    "product, quantity_remaining, notes, created_at"
                ).eq("store_id", store_id).gte("created_at", today_start).order("created_at", desc=True).execute().data or []
                
                if user_entries:
                    df_u = pd.DataFrame(user_entries)
                    df_u["dt"] = pd.to_datetime(df_u["created_at"], errors="coerce", utc=True).dt.tz_convert("America/Sao_Paulo")
                    df_u["Horário"] = df_u["dt"].dt.strftime("%H:%M:%S")
                    
                    grouped = df_u.groupby("Horário")
                    for hr, group in grouped:
                        st.markdown(f"🕒 **Lançamento realizado às {hr}**")
                        for _, r in group.iterrows():
                            st.write(f"• **{r['product']}**: {r['quantity_remaining']} un.")
                        
                        first_note = group["notes"].iloc[0] if not group.empty else ""
                        if "[FECHAMENTO FINANCEIRO" in first_note:
                            fin_part = first_note.split("[FECHAMENTO FINANCEIRO DA LOJA]")[1]
                            st.caption(f"💰 Financeiro: {fin_part}")
                        st.divider()
                else:
                    st.info("Nenhum lançamento registrado hoje ainda.")
            except Exception:
                st.error("Não foi possível carregar o histórico.")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("show_success_confirm"):
        st.success("✅ FECHAMENTO ENVIADO E SALVO COM SUCESSO! Formulário limpo para o próximo lançamento.")
        st.session_state.show_success_confirm = False

    with st.form("single_staff_form", clear_on_submit=True):
        st.markdown("<h2 style='color: #FACC15;'>📦 1. Quantidade de Produtos em Estoque</h2>", unsafe_allow_html=True)
        st.caption("Apenas contagem e foto individual do produto. Sem valores financeiros aqui.")
        st.markdown("<br>", unsafe_allow_html=True)

        form_data = {}
        photos_data = {}
        notes_data = {}

        for product in PRODUCTS:
            st.markdown(f"#### 🍲 {product}")
            c1, c2, c3 = st.columns([1, 1.5, 2])
            
            with c1:
                form_data[product] = st.number_input(
                    "Quantidade Atual", min_value=0, step=1, value=0, key=f"q_{product}"
                )
            with c2:
                photos_data[product] = st.file_uploader(
                    "Foto do Item", type=["jpg", "jpeg", "png", "webp"], key=f"photo_{product}"
                )
            with c3:
                notes_data[product] = st.text_input(
                    "Observação (Opcional)", placeholder=f"Ex: Apenas 2 no freezer...", key=f"note_{product}"
                )
            st.markdown("<hr style='border: 0; height: 1px; background: #334155; margin: 1.5rem 0;'>", unsafe_allow_html=True)

        st.markdown("<br><h2 style='color: #FACC15;'>💰 2. Fechamento Financeiro Geral da Loja</h2>", unsafe_allow_html=True)
        st.caption("Valores totais do dia e comprovantes/fotos gerais.")
        st.markdown("<br>", unsafe_allow_html=True)

        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown("##### 💳 Maquininha / Cartão")
            card_val = st.number_input("Valor total da maquininha (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val_in")
            card_photo = st.file_uploader("Foto do Comprovante do Cartão", type=["jpg", "jpeg", "png", "webp"], key="card_ph_in")
            card_note = st.text_input("Observação da Maquininha", placeholder="Ex: Fechamento das 15h...", key="card_note_in")
            
        with fc2:
            st.markdown("##### 💵 Dinheiro em Espécie")
            cash_val = st.number_input("Total em dinheiro na gaveta (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val_in")
            cash_photo = st.file_uploader("Foto do Dinheiro / Envelope", type=["jpg", "jpeg", "png", "webp"], key="cash_ph_in")
            cash_note = st.text_input("Observação do Dinheiro", placeholder="Ex: R$ 50 de troco mantido...", key="cash_note_in")

        st.markdown("<br><br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("✅ ENVIAR FECHAMENTO E SALVAR ESTOQUE", type="primary", use_container_width=True)

    if submitted:
        try:
            fin_data = {"card": card_val, "cash": cash_val}
            fin_photos = {"card": card_photo, "cash": cash_photo}
            fin_notes = {"card": card_note, "cash": cash_note}
            
            save_complete_form(client, profile, form_data, photos_data, notes_data, fin_data, fin_photos, fin_notes)
            
            st.session_state.show_success_confirm = True
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


# Painel do Administrador (Dashboard Espaçado e Moderno)
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

    st.markdown("""
    <div class="hero-header">
        <div style="font-size: 0.8rem; font-weight: 700; color: #FACC15; text-transform: uppercase; letter-spacing: 1px;">PAINEL CENTRAL · CM MARMITARIA</div>
        <h1>📊 Controle Consolidado de Estoque</h1>
        <p>Acompanhamento das unidades e fechamentos em tempo real</p>
    </div>
    """, unsafe_allow_html=True)

    col_alert_btn, col_alert_off, col_ctrl1 = st.columns([2, 1.2, 1])
    with col_alert_btn:
        if st.button("🔔 Solicitar Atualização de Estoque Agora", type="primary"):
            set_alert_status(client, True)
            st.success("Alerta emitido no celular das funcionárias!")

    with col_alert_off:
        if st.button("🔕 Desativar Alerta"):
            set_alert_status(client, False)
            st.info("Alerta desativado.")

    with col_ctrl1:
        if st.button("🔄 Atualizar"):
            st.session_state.last_admin_update = datetime.now(TZ_BR)
            st.rerun()

    now_br = datetime.now(TZ_BR)
    if "last_admin_update" not in st.session_state:
        st.session_state.last_admin_update = now_br

    last_time_formatted = st.session_state.last_admin_update.strftime("%d/%m/%Y às %H:%M:%S")
    st.caption(f"🕒 Última atualização do sistema: **{last_time_formatted}**")
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
        st.error("Erro ao carregar dados do Supabase.")
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
        df["Hora e Minuto"] = df["dt_object"].dt.strftime("%H:%M:%S")
        df["Data e Hora"] = df["dt_object"].dt.strftime("%d/%m/%Y %H:%M:%S")
        
        latest = df.dropna(subset=["created_at"]).sort_values("created_at").groupby(["store_id", "product"], as_index=False).tail(1)
    else:
        df["dt_object"] = pd.Series(dtype="datetime64[ns, America/Sao_Paulo]")
        latest = pd.DataFrame(columns=["store_id", "product", "quantity_remaining", "created_at", "Loja", "Data e Hora", "Funcionária", "photo_path", "notes"])

    tab_overview, tab_stores, tab_carteirinhas, tab_history, tab_reports = st.tabs([
        "📌 Resumo das Lojas", 
        "🏪 Gerenciar por Loja (Cards Modernos)", 
        "🏷️ Carteirinhas de Estoque", 
        "📜 Histórico & Planilha", 
        "📊 Relatórios"
    ])

    with tab_overview:
        st.markdown("### 🍲 Resumo Geral das Unidades")
        cards = st.columns(3)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else latest
            
            m_pequena = 0
            m_grande = 0
            if not store_latest.empty:
                p_eq = store_latest[store_latest["product"] == "Marmitex pequena"]
                if not p_eq.empty:
                    m_pequena = int(p_eq["quantity_remaining"].values[0])
                p_gr = store_latest[store_latest["product"] == "Marmitex grande"]
                if not p_gr.empty:
                    m_grande = int(p_gr["quantity_remaining"].values[0])

            with cards[idx % 3]:
                st.markdown(f"""
                <div class="store-card">
                    <div class="store-card-header">
                        <span class="store-card-title">🏪 {name}</span>
                        <span class="store-card-badge">{resp}</span>
                    </div>
                    <p style="margin: 0.4rem 0; color: #334155;">🍲 Marmitex Pequena: <strong style="color: #0F172A;">{m_pequena} un.</strong></p>
                    <p style="margin: 0.4rem 0; color: #334155;">🍲 Marmitex Grande: <strong style="color: #0F172A;">{m_grande} un.</strong></p>
                </div>
                """, unsafe_allow_html=True)

    # ABA GERENCIAR POR LOJA - CARDS INDIVIDUALIZADOS E ESPAÇADOS
    with tab_stores:
        st.markdown("### 🏪 Gerenciamento Detalhado por Unidade")
        st.caption("Visão ampla e limpa de cada loja. Produtos e fechamento financeiro no mesmo card.")

        for store in stores:
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            st.markdown(f"""
            <div class="store-card">
                <div class="store-card-header">
                    <span class="store-card-title">🏪 {name}</span>
                    <span class="store-card-badge">Responsável: {resp}</span>
                </div>
            """, unsafe_allow_html=True)

            with st.expander(f"🔎 Expandir Detalhes do Estoque e Fechamento da {name}", expanded=True):
                col_del, _ = st.columns([1, 2])
                with col_del:
                    with st.popover(f"🗑️ Apagar Registros da {name}"):
                        st.warning("Confirma a exclusão de todos os registros desta loja?")
                        if st.button("Confirmar Apagar Tudo", key=f"del_card_store_{sid}"):
                            try:
                                client.table("stock_entries").delete().eq("store_id", sid).execute()
                                st.success("Registros apagados!")
                                st.rerun()
                            except Exception:
                                st.error("Erro ao apagar.")

                st.markdown("<br>", unsafe_allow_html=True)

                if not store_latest.empty:
                    # Grelha de produtos em colunas separadas para não embolar
                    p_cols = st.columns(2)
                    for p_idx, (_, row) in enumerate(store_latest.iterrows()):
                        p_name = row["product"]
                        qty = int(row["quantity_remaining"])
                        notes = row.get("notes") or ""
                        
                        prod_obs = notes.split("||")[0].replace("Obs Item:", "").strip() if "||" in notes else notes

                        with p_cols[p_idx % 2]:
                            st.markdown(f"""
                            <div class="product-grid-item">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                                    <strong style="color: #0F172A; font-size: 1.05rem;">🍲 {p_name}</strong>
                                    <span style="background: #E2E8F0; color: #0F172A; padding: 0.25rem 0.75rem; border-radius: 8px; font-weight: 800;">{qty} un.</span>
                                </div>
                                <p style="margin: 0; color: #64748B; font-size: 0.85rem;">📝 {prod_obs}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            c3, c4 = st.columns([1, 1])
                            path = row.get("photo_path")
                            url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                            if url:
                                with c3.popover("📷 Foto do Item"):
                                    st.image(url, use_container_width=True)
                            else:
                                c3.caption("Sem foto")

                            row_id = row.get("id")
                            if c4.button("🗑️ Excluir", key=f"del_card_item_{row_id}"):
                                try:
                                    client.table("stock_entries").delete().eq("id", row_id).execute()
                                    st.success("Item apagado!")
                                    st.rerun()
                                except Exception:
                                    st.error("Erro ao apagar.")

                    # Exibe o Painel Financeiro do Fechamento no final do card da loja
                    first_notes = store_latest["notes"].iloc[0] if not store_latest.empty else ""
                    if "[FECHAMENTO FINANCEIRO" in first_notes:
                        fin_text = first_notes.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1] if "[FECHAMENTO FINANCEIRO DA LOJA] |" in first_notes else first_notes
                        st.markdown(f"""
                        <div class="financial-summary-box">
                            <strong style="color: #854D0E; font-size: 1rem;">💰 FECHAMENTO FINANCEIRO GERAL DA LOJA:</strong>
                            <p style="color: #713F12; margin: 0.4rem 0 0 0; font-weight: 600;">{fin_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhum registro de estoque ativo para esta loja.")

            st.markdown("</div>", unsafe_allow_html=True)

    with tab_carteirinhas:
        st.markdown("### 🏷️ Carteirinhas de Estoque Completo")
        for store in stores:
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()
            
            prod_qtys = {p: 0 for p in PRODUCTS}
            if not store_latest.empty:
                for _, r in store_latest.iterrows():
                    prod_name = r["product"]
                    if prod_name in prod_qtys:
                        prod_qtys[prod_name] = int(r["quantity_remaining"])

            st.markdown(f"""
            <div class="store-card">
                <div class="store-card-header">
                    <span class="store-card-title">🏪 {name}</span>
                    <span class="store-card-badge">Responsável: {resp}</span>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 1.5rem; margin-top: 0.8rem;">
                    <div>🍲 Pequena: <strong style="color: #0F172A;">{prod_qtys['Marmitex pequena']} un.</strong></div>
                    <div>🍲 Grande: <strong style="color: #0F172A;">{prod_qtys['Marmitex grande']} un.</strong></div>
                    <div>🥤 Refri Peq: <strong style="color: #0F172A;">{prod_qtys['Refrigerantes Peq']} un.</strong></div>
                    <div>🍮 Pudim: <strong style="color: #0F172A;">{prod_qtys['Pudim']} un.</strong></div>
                    <div>🥤 Lata: <strong style="color: #0F172A;">{prod_qtys['Refrigerante lata']} un.</strong></div>
                    <div>💧 Água: <strong style="color: #0F172A;">{prod_qtys['Água']} un.</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_history:
        st.markdown("### 📜 Histórico de Registros e Planilha (CSV)")
        if not df.empty:
            f_col1, f_col2 = st.columns([2, 2])
            with f_col1:
                store_filter_options = ["Todas as Lojas"] + list(display_names.values())
                selected_store_filter = st.selectbox("Filtrar por Loja", store_filter_options)
            with f_col2:
                today_br = datetime.now(TZ_BR).date()
                date_range = st.date_input("Filtrar por Período", value=[today_br, today_br])
            
            filtered_df = df.copy()
            if selected_store_filter != "Todas as Lojas":
                filtered_df = filtered_df[filtered_df["Loja"] == selected_store_filter]
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (filtered_df["dt_object"].dt.date >= start_date) & 
                    (filtered_df["dt_object"].dt.date <= end_date)
                ]

            st.markdown("<br>", unsafe_allow_html=True)
            display_cols = ["Data", "Hora e Minuto", "Loja", "Funcionária", "product", "quantity_remaining", "notes"]
            renamed_df = filtered_df[display_cols].rename(columns={
                "product": "Produto",
                "quantity_remaining": "Quantidade Restante",
                "notes": "Observações & Fechamento Financeiro"
            })
            st.dataframe(renamed_df, use_container_width=True, hide_index=True)
            
            today_str = datetime.now(TZ_BR).strftime('%d_%m_%Y')
            csv_data = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar Planilha Completa (CSV)",
                data=csv_data,
                file_name=f"historico_cm_marmitaria_{today_str}.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum lançamento registrado no momento.")

    with tab_reports:
        st.markdown("### Visão Consolidada por Produto")
        if not latest.empty:
            st.bar_chart(latest.groupby("product")["quantity_remaining"].sum())


def main():
    client = get_client()
    if client is None:
        st.error("Erro de conexão com o Supabase.")
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
        st.error("Perfil de acesso não encontrado.")
        if st.button("Sair"):
            sign_out()
        st.stop()

    st.session_state.profile = profile
    display_name = profile.get("display_name") or "Usuário"
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:center; color: #FACC15; margin-bottom: 0;'>🏠 CM MARMITARIA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size: 0.75rem; color: #94A3B8; font-weight: 600;'>CONTROLE & FECHAMENTO</p>", unsafe_allow_html=True)
        st.divider()
        st.markdown(f"👤 **{display_name}**")
        st.caption("Administrador" if profile.get("role") == "admin" else f"Loja: {get_store_name(client, profile.get('store_id'))}")
        st.divider()
        if st.button("🚪 Sair da Conta", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)


if __name__ == "__main__":
    main()
    
