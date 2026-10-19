import os
import uuid
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="CM Marmitaria | Controle de Estoque",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fuso horário fixo oficial de Brasília
TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")

PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerantes Peq", "Pudim", "Refrigerante lata", "Água"]
PRODUCT_PRICES = {"Marmitex pequena": 11.99, "Marmitex grande": 15.00, "Refrigerantes Peq": 4.00, "Pudim": 5.00, "Refrigerante lata": 7.00, "Água": 4.00}
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# Estilização CSS (Fundo preto para funcionária e tema geral)
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

/* Cartões das Lojas */
.store-box {
    background: #FFFFFF;
    border: 2px solid #FFE082;
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(218, 165, 32, 0.08);
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-success { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
.badge-warning { background-color: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; }

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
    for key in ["supabase_user_id", "supabase_email", "supabase_access_token", "supabase_refresh_token", "profile", "supabase_client"]:
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
    
    rows = []
    for product in PRODUCTS:
        qty = int(form_data.get(product, 0))
        p_path = upload_photo(client, photos_data.get(product), store_id, user_id)
        prod_obs = notes_data.get(product, "")
        
        full_note = f"Obs Produto: {prod_obs} | Maquininha: R$ {fin_data.get('card', 0.0):.2f} (Obs: {fin_notes.get('card', '')}) | Dinheiro: R$ {fin_data.get('cash', 0.0):.2f} (Obs: {fin_notes.get('cash', '')})"
        
        rows.append({
            "store_id": store_id,
            "user_id": user_id,
            "product": product,
            "quantity_remaining": qty,
            "photo_path": p_path,
            "notes": full_note.strip(),
            "created_at": created_at,
        })
    return client.table("stock_entries").insert(rows).execute()


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

    store_id = str(profile.get("store_id", ""))
    store_name = get_store_name(client, store_id)
    display_name = profile.get("display_name") or "Funcionária"

    st.markdown(f"""
    <div class="store-form-box" style="text-align: center;">
        <h1 style="color: #FFB300 !important; margin: 0;">🏠 CM MARMITARIA</h1>
        <h3>Olá, {display_name} · {store_name}</h3>
        <p>Preencha abaixo o formulário completo de fechamento e estoque de hoje.</p>
    </div>
    """, unsafe_allow_html=True)

    # BOTÃO POP-OVER PARA HISTÓRICO SIMPLES DA FUNCIONÁRIA
    c_hist_top, _ = st.columns([2, 1])
    with c_hist_top:
        with st.popover("📜 Ver Meu Histórico de Hoje (Lançamentos Enviados)"):
            st.markdown("### 📜 Meus Lançamentos de Hoje")
            try:
                today_start = datetime.now(TZ_BR).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()
                user_entries = client.table("stock_entries").select(
                    "product, quantity_remaining, notes, created_at"
                ).eq("store_id", store_id).gte("created_at", today_start).order("created_at", desc=True).execute().data or []
                
                if user_entries:
                    # Agrupa os lançamentos por horário de envio
                    df_u = pd.DataFrame(user_entries)
                    df_u["dt"] = pd.to_datetime(df_u["created_at"], errors="coerce", utc=True).dt.tz_convert("America/Sao_Paulo")
                    df_u["Horário"] = df_u["dt"].dt.strftime("%H:%M:%S")
                    
                    grouped = df_u.groupby("Horário")
                    for hr, group in grouped:
                        st.markdown(f"🕒 **Lançamento das {hr}**")
                        for _, r in group.iterrows():
                            st.write(f"• **{r['product']}**: {r['quantity_remaining']} un.")
                        
                        first_note = group["notes"].iloc[0] if not group.empty else ""
                        if "Maquininha:" in first_note:
                            fin_part = first_note.split("Obs Produto:")[1] if "Obs Produto:" in first_note else first_note
                            st.caption(f"💰 {fin_part}")
                        st.divider()
                else:
                    st.info("Nenhum lançamento registrado hoje ainda.")
            except Exception as e:
                st.error("Não foi possível carregar seu histórico recente.")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("show_success_confirm"):
        st.success("✅ SEU FECHAMENTO FOI CONFIRMADO E SALVO COM SUCESSO! A tela foi limpa para novos lançamentos.")
        st.session_state.show_success_confirm = False

    with st.form("single_staff_form", clear_on_submit=True):
        st.markdown("### 📦 1. Quantidades e Fotos dos Produtos")
        
        form_data = {}
        photos_data = {}
        notes_data = {}

        for product in PRODUCTS:
            st.markdown(f"**🍲 {product}**")
            c1, c2, c3 = st.columns([1, 1.5, 2])
            
            with c1:
                form_data[product] = st.number_input(
                    "Quantidade", min_value=0, step=1, value=0, key=f"q_{product}"
                )
            with c2:
                photos_data[product] = st.file_uploader(
                    "Foto", type=["jpg", "jpeg", "png", "webp"], key=f"photo_{product}"
                )
            with c3:
                notes_data[product] = st.text_input(
                    "Observação do item", placeholder=f"Obs sobre {product}...", key=f"note_{product}"
                )
            st.divider()

        st.markdown("### 💰 2. Informações Financeiras")
        
        fc1, fc2 = st.columns(2)
        with fc1:
            card_val = st.number_input("Valor final da maquininha (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val_in")
            card_photo = st.file_uploader("Foto do comprovante da maquininha", type=["jpg", "jpeg", "png", "webp"], key="card_ph_in")
            card_note = st.text_input("Observação da Maquininha", placeholder="Ex: Cartão Visa/Master...", key="card_note_in")
            
        with fc2:
            cash_val = st.number_input("Total em dinheiro em espécie (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val_in")
            cash_photo = st.file_uploader("Foto do envelope/dinheiro (opcional)", type=["jpg", "jpeg", "png", "webp"], key="cash_ph_in")
            cash_note = st.text_input("Observação do Dinheiro", placeholder="Ex: Troco deixado na gaveta...", key="cash_note_in")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("✅ Enviar Fechamento Completo", type="primary", use_container_width=True)

    if submitted:
        try:
            fin_data = {"card": card_val, "cash": cash_val}
            fin_photos = {"card": card_photo, "cash": cash_photo}
            fin_notes = {"card": card_note, "cash": cash_note}
            
            save_complete_form(client, profile, form_data, photos_data, notes_data, fin_data, fin_photos, fin_notes)
            
            st.session_state.show_success_confirm = True
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar o formulário: {e}")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


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

    st.markdown("""
    <div class="hero-header">
        <div style="font-size: 0.85rem; font-weight: 700; color: #8C4A00; text-transform: uppercase;">PAINEL CENTRAL · CM MARMITARIA</div>
        <h1>📊 Controle Consolidado de Estoque</h1>
        <p>Acompanhamento das unidades comerciais em tempo real</p>
    </div>
    """, unsafe_allow_html=True)

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1.2, 3])
    
    now_br = datetime.now(TZ_BR)

    with col_ctrl1:
        if st.button("🔄 Atualizar"):
            st.session_state.last_admin_update = datetime.now(TZ_BR)
            st.rerun()

    with col_ctrl2:
        auto_refresh = st.toggle("⏱️ Auto 5 min", value=False)

    if "last_admin_update" not in st.session_state:
        st.session_state.last_admin_update = now_br

    last_time_formatted = st.session_state.last_admin_update.strftime("%d/%m/%Y às %H:%M:%S")

    with col_ctrl3:
        if auto_refresh:
            @st.fragment(run_every=1)
            def countdown_display():
                now_ts = datetime.now(TZ_BR).timestamp()
                if "next_refresh_ts" not in st.session_state or st.session_state.next_refresh_ts < now_ts:
                    st.session_state.next_refresh_ts = now_ts + 300
                    st.session_state.last_admin_update = datetime.now(TZ_BR)
                    st.rerun()
                
                remaining = int(st.session_state.next_refresh_ts - now_ts)
                mins = max(0, remaining // 60)
                secs = max(0, remaining % 60)
                st.markdown(f"<p style='margin: 0; font-size: 0.85rem; font-weight: 600; color: #8C4A00;'>⏳ Próxima att em: <b>{mins:02d}:{secs:02d}</b> | 🕒 Última atualização do sistema: <b>{last_time_formatted}</b></p>", unsafe_allow_html=True)
            
            countdown_display()
        else:
            st.session_state.pop("next_refresh_ts", None)
            st.markdown(f"<p style='margin: 0; font-size: 0.85rem; font-weight: 600; color: #8C4A00;'>🕒 Última atualização do sistema: <b>{last_time_formatted}</b></p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _load_and_render_admin_content(client, display_store_name, known_store_labels)


def _load_and_render_admin_content(client, display_store_name, known_store_labels):
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
        "📌 Resumo de Marmitas", 
        "🏪 Gerenciar por Loja (Cards)", 
        "🏷️ Carteirinhas de Estoque", 
        "📜 Histórico & Planilha", 
        "📊 Relatório"
    ])

    with tab_overview:
        st.markdown("### 🍲 Resumo de Marmitas por Responsável")
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
                <div class="store-box">
                    <strong style="color: #2A1200; font-size: 1.1rem;">🏪 {name}</strong>
                    <p style="color: #64748B; font-size: 0.85rem; margin: 0.2rem 0 0.75rem 0;">Responsável: <strong>{resp}</strong></p>
                    <hr style="border: 1px solid #FFE082; margin: 0.5rem 0;">
                    <p style="margin: 0.2rem 0; color: #2A1200;">• Marmitex Pequena: <strong>{m_pequena} un.</strong></p>
                    <p style="margin: 0.2rem 0; color: #2A1200;">• Marmitex Grande: <strong>{m_grande} un.</strong></p>
                </div>
                """, unsafe_allow_html=True)

    with tab_stores:
        st.markdown("### 🏪 Gerenciamento por Cards de Lojas")
        st.caption("Visão simultânea de todas as unidades com fotos, observações e controle de exclusão.")

        for store in stores:
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            with st.expander(f"🏪 **{name}** · Responsável: {resp}", expanded=True):
                col_info, col_del = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**Registros Atuais da {name}:**")
                with col_del:
                    with st.popover(f"🗑️ Apagar Registros da {name}"):
                        st.warning("Confirma a exclusão de todos os registros desta loja?")
                        if st.button("Confirmar Apagar Tudo", key=f"del_card_store_{sid}"):
                            try:
                                client.table("stock_entries").delete().eq("store_id", sid).execute()
                                st.success("Registros da loja apagados!")
                                st.rerun()
                            except Exception:
                                st.error("Erro ao apagar.")

                if not store_latest.empty:
                    for _, row in store_latest.iterrows():
                        c1, c2, c3, c4 = st.columns([3, 1.2, 1.2, 1])
                        
                        p_name = row["product"]
                        qty = int(row["quantity_remaining"])
                        notes = row.get("notes") or "Sem observação"
                        
                        c1.markdown(f"• **{p_name}**: <small>{notes}</small>", unsafe_allow_html=True)
                        c2.markdown(f"**{qty} un.**")

                        path = row.get("photo_path")
                        url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                        if url:
                            with c3.popover("📷 Ver Foto"):
                                st.image(url, use_container_width=True)
                        else:
                            c3.caption("Sem foto")

                        row_id = row.get("id")
                        if c4.button("🗑️ Apagar", key=f"del_card_item_{row_id}"):
                            try:
                                client.table("stock_entries").delete().eq("id", row_id).execute()
                                st.success("Item apagado!")
                                st.rerun()
                            except Exception:
                                st.error("Erro ao apagar item.")
                        st.divider()
                else:
                    st.info("Nenhum registro ativo para esta unidade.")

    with tab_carteirinhas:
        st.markdown("### 🏷️ Carteirinhas de Estoque Completo de Todas as Lojas")
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
            <div class="store-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong style="color: #2A1200; font-size: 1.2rem;">🏪 {name}</strong>
                    <span style="color: #64748B; font-size: 0.85rem;">Responsável: <strong>{resp}</strong></span>
                </div>
                <hr style="border: 1px solid #FFE082; margin: 0.5rem 0;">
                <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem;">
                    <div>🍲 Pequena: <strong>{prod_qtys['Marmitex pequena']} un.</strong></div>
                    <div>🍲 Grande: <strong>{prod_qtys['Marmitex grande']} un.</strong></div>
                    <div>🥤 Refri Peq: <strong>{prod_qtys['Refrigerantes Peq']} un.</strong></div>
                    <div>🍮 Pudim: <strong>{prod_qtys['Pudim']} un.</strong></div>
                    <div>🥤 Lata: <strong>{prod_qtys['Refrigerante lata']} un.</strong></div>
                    <div>💧 Água: <strong>{prod_qtys['Água']} un.</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_history:
        st.markdown("### 📜 Histórico Geral e Planilha")
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
                "notes": "Observações & Financeiro"
            })
            st.dataframe(renamed_df, use_container_width=True, hide_index=True)
            
            today_str = datetime.now(TZ_BR).strftime('%d_%m_%Y')
            csv_data = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar Planilha (CSV)",
                data=csv_data,
                file_name=f"historico_cm_marmitaria_{today_str}.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum lançamento registrado no momento.")

    with tab_reports:
        st.markdown("### Visão por Produto")
        if not latest.empty:
            st.bar_chart(latest.groupby("product")["quantity_remaining"].sum())


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
