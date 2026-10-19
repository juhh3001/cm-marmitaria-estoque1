import os
import uuid
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

PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerantes Peq", "Pudim", "Refrigerante lata", "Água"]
PRODUCT_PRICES = {"Marmitex pequena": 11.99, "Marmitex grande": 15.00, "Refrigerantes Peq": 4.00, "Pudim": 5.00, "Refrigerante lata": 7.00, "Água": 4.00}
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# Estilização CSS (Ajustada para o fundo preto na área da funcionária e tema geral)
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

/* Cartões de Métricas */
.kpi-card {
    background: #FFFFFF;
    border: 2px solid #FFD54F;
    border-radius: 16px;
    padding: 1rem 1.25rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03);
}
.kpi-title {
    font-size: 0.8rem;
    color: #8C4A00;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: #2A1200;
    margin-top: 0.2rem;
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
    for key in ["supabase_user_id", "supabase_email", "supabase_access_token", "supabase_refresh_token", "profile", "supabase_client", "staff_step", "form_qtys", "form_photos", "form_fin"]:
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


def save_complete_record(client: Client, profile: dict, quantities: dict, photos: dict, fin_data: dict):
    user_id = str(profile["user_id"])
    store_id = str(profile["store_id"])
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Faz upload do comprovante de cartão se houver
    card_receipt_path = upload_photo(client, fin_data.get("card_photo"), store_id, user_id)
    
    rows = []
    for product in PRODUCTS:
        qty = int(quantities.get(product, 0))
        p_path = upload_photo(client, photos.get(product), store_id, user_id)
        rows.append({
            "store_id": store_id,
            "user_id": user_id,
            "product": product,
            "quantity_remaining": qty,
            "photo_path": p_path,
            "notes": f"Maquininha: R$ {fin_data.get('card_amount', 0.0):.2f} | Dinheiro: R$ {fin_data.get('cash_amount', 0.0):.2f}",
            "created_at": created_at,
        })
    return client.table("stock_entries").insert(rows).execute()


# Interface das Funcionárias (Fundo Preto e 4 Telas Sequenciais)
def staff_screen(client: Client, profile: dict):
    # Aplica o fundo preto para a funcionária
    st.markdown("""
    <style>
    .stApp {
        background-color: #000000 !important;
    }
    h1, h2, h3, h4, p, label, span, div {
        color: #FFFFFF !important;
    }
    .store-box {
        background: #1A1A1A !important;
        border: 2px solid #FFB300 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    store_name = get_store_name(client, profile.get("store_id"))
    display_name = profile.get("display_name") or "Funcionária"

    if "staff_step" not in st.session_state:
        st.session_state.staff_step = 1
    if "form_qtys" not in st.session_state:
        st.session_state.form_qtys = {p: 0 for p in PRODUCTS}
    if "form_photos" not in st.session_state:
        st.session_state.form_photos = {p: None for p in PRODUCTS}
    if "form_fin" not in st.session_state:
        st.session_state.form_fin = {"card_amount": 0.0, "card_photo": None, "cash_amount": 0.0}

    step = st.session_state.staff_step

    # TELA 1 — Início
    if step == 1:
        st.markdown(f"""
        <div style="background: #1A1A1A; padding: 1.5rem; border-radius: 16px; border: 2px solid #FFB300; text-align: center; margin-bottom: 1.5rem;">
            <h1 style="color: #FFB300 !important;">🏠 CM MARMITARIA</h1>
            <h3>Olá, {display_name} ({store_name})</h3>
            <p>Seja bem-vinda ao sistema de fechamento e controle diário.</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Fazer Registro de Hoje", use_container_width=True, type="primary"):
            st.session_state.staff_step = 2
            st.rerun()

    # TELA 2 — Estoque com botões de - e +
    elif step == 2:
        st.markdown(f"<h2>📦 Tela 2/4: Estoque · {store_name}</h2>", unsafe_allow_html=True)
        st.info("Ajuste a quantidade restante de cada produto. Foto opcional.")

        for product in PRODUCTS:
            st.markdown(f"**{product}**")
            col_btn1, col_val, col_btn2, col_foto = st.loc_cols([1, 1.5, 1, 3]) if hasattr(st, "loc_cols") else st.columns([1, 1.5, 1, 3])
            
            # Botão de menos
            if col_btn1.button("➖", key=f"minus_{product}"):
                if st.session_state.form_qtys[product] > 0:
                    st.session_state.form_qtys[product] -= 1
                    st.rerun()
            
            # Valor atual
            col_val.markdown(f"<div style='text-align: center; font-size: 1.2rem; font-weight: bold; padding-top: 5px;'>{st.session_state.form_qtys[product]} un.</div>", unsafe_allow_html=True)
            
            # Botão de mais
            if col_btn2.button("➕", key=f"plus_{product}"):
                st.session_state.form_qtys[product] += 1
                st.rerun()

            # Foto opcional
            with col_foto.expander("📷 Foto opcional"):
                p_up = st.file_uploader(f"Foto {product}", type=["jpg", "jpeg", "png", "webp"], key=f"ph_{product}", label_visibility="collapsed")
                if p_up:
                    st.session_state.form_photos[product] = p_up

            st.divider()

        c_vol, c_av = st.columns(2)
        if c_vol.button("⬅️ Voltar", use_container_width=True):
            st.session_state.staff_step = 1
            st.rerun()
        if c_av.button("Avançar para o Financeiro ➡️", use_container_width=True, type="primary"):
            st.session_state.staff_step = 3
            st.rerun()

    # TELA 3 — Financeiro
    elif step == 3:
        st.markdown(f"<h2>💳 Tela 3/4: Informações Financeiras</h2>", unsafe_allow_html=True)
        
        card_amt = st.number_input("Valor final da maquininha (R$)", min_value=0.0, step=0.50, value=float(st.session_state.form_fin["card_amount"]))
        card_ph = st.file_uploader("Anexar foto do comprovante da maquininha (opcional)", type=["jpg", "jpeg", "png", "webp"])
        cash_amt = st.number_input("Total em dinheiro em espécie (R$)", min_value=0.0, step=0.50, value=float(st.session_state.form_fin["cash_amount"]))

        st.session_state.form_fin["card_amount"] = card_amt
        if card_ph:
            st.session_state.form_fin["card_photo"] = card_ph
        st.session_state.form_fin["cash_amount"] = cash_amt

        c_vol, c_av = st.columns(2)
        if c_vol.button("⬅️ Voltar", use_container_width=True):
            st.session_state.staff_step = 2
            st.rerun()
        if c_av.button("Ir para Conferência ➡️", use_container_width=True, type="primary"):
            st.session_state.staff_step = 4
            st.rerun()

    # TELA 4 — Conferência e Envio
    elif step == 4:
        st.markdown(f"<h2>📋 Tela 4/4: Conferência Geral</h2>", unsafe_allow_html=True)
        st.markdown("Confira se os dados abaixo estão corretos antes de enviar:")

        st.markdown("### 📦 Estoque Informado:")
        for prod, q in st.session_state.form_qtys.items():
            st.write(f"- **{prod}**: {q} un.")

        st.markdown("### 💰 Financeiro Informado:")
        st.write(f"- Maquininha: **R$ {st.session_state.form_fin['card_amount']:.2f}**")
        st.write(f"- Dinheiro em Espécie: **R$ {st.session_state.form_fin['cash_amount']:.2f}**")

        st.divider()

        c_vol, c_env = st.columns(2)
        if c_vol.button("⬅️ Voltar e Editar", use_container_width=True):
            st.session_state.staff_step = 3
            st.rerun()
        
        if c_env.button("✅ Finalizar e Enviar", use_container_width=True, type="primary"):
            try:
                save_complete_record(client, profile, st.session_state.form_qtys, st.session_state.form_photos, st.session_state.form_fin)
                st.success("🎉 Lançamento enviado e salvo com sucesso!")
                # Limpa o estado
                st.session_state.staff_step = 1
                st.session_state.form_qtys = {p: 0 for p in PRODUCTS}
                st.session_state.form_photos = {p: None for p in PRODUCTS}
                st.session_state.form_fin = {"card_amount": 0.0, "card_photo": None, "cash_amount": 0.0}
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


# Painel do Administrador (Com Auto-atualização de 5 min e Botão de Atualizar)
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

    # Controles de Atualização do Admin (Botão de Atualizar e Auto 5 minutos)
    col_ctrl1, col_ctrl2 = st.columns([1, 3])
    with col_ctrl1:
        if st.button("🔄 Atualizar Agora"):
            st.rerun()
    with col_ctrl2:
        auto_refresh = st.toggle("⏱️ Ativar Auto-atualização (a cada 5 minutos)", value=False)

    # Se o auto-refresh estiver ativo, usamos fragment com run_every=300 segundos
    if auto_refresh:
        @st.fragment(run_every=300)
        def render_live_admin_content():
            _load_and_render_admin_content(client, display_store_name, known_store_labels)
        render_live_admin_content()
    else:
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

    total_stores = len(stores)
    today = pd.Timestamp.now(tz="America/Sao_Paulo").date()
    total_latest_units = int(pd.to_numeric(latest.get("quantity_remaining", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not latest.empty else 0
    entries_today = int((df["dt_object"].dt.date == today).sum()) if not df.empty else 0

    total_value = 0
    if not latest.empty:
        for _, row in latest.iterrows():
            p_name = row["product"]
            p_qty = row["quantity_remaining"]
            total_value += p_qty * PRODUCT_PRICES.get(p_name, 0.0)

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi-card"><div class="kpi-title">Lojas Ativas</div><div class="kpi-value">{total_stores} Unidades</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi-card"><div class="kpi-title">Estoque Total</div><div class="kpi-value">{total_latest_units} un.</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-card"><div class="kpi-title">Valor Estimado</div><div class="kpi-value">R$ {total_value:,.2f}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi-card"><div class="kpi-title">Lançamentos Hoje</div><div class="kpi-value">{entries_today}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_overview, tab_stores, tab_carteirinhas, tab_history, tab_reports = st.tabs([
        "📌 Resumo de Marmitas", 
        "🏪 Gerenciar por Loja", 
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
        st.markdown("### Detalhes por Loja e Exclusão de Registros")
        options = {display_names[str(store["id"])]: str(store["id"]) for store in stores}
        selected_label = st.selectbox("Escolha a Loja para gerenciar", list(options.keys()))
        sid = options[selected_label]
        store_latest = latest[latest["store_id"] == sid] if not latest.empty else latest

        col_del_all, _ = st.columns([1, 2])
        with col_del_all:
            with st.popover("⚠️ Apagar TODOS os registros desta loja"):
                st.warning("Tem certeza? Esta ação apagará o histórico e lançamentos desta loja.")
                if st.button("Confirmar e Apagar Tudo", key=f"confirm_del_all_{sid}"):
                    try:
                        client.table("stock_entries").delete().eq("store_id", sid).execute()
                        st.success("Registros apagados com sucesso!")
                        st.rerun()
                    except Exception:
                        st.error("Erro ao apagar os registros.")

        st.markdown("<hr>", unsafe_allow_html=True)

        if not store_latest.empty:
            for _, row in store_latest.iterrows():
                c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
                c1.markdown(f"**{row['product']}**")
                c2.markdown(f"**{int(row['quantity_remaining'])} un.**")
                
                path = row.get("photo_path")
                url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                if url:
                    with c3.popover("📷 Ver Foto"):
                        st.image(url, use_container_width=True)
                else:
                    c3.caption("Sem foto")

                row_id = row.get("id")
                if c4.button("🗑️ Apagar", key=f"del_row_{row_id}"):
                    try:
                        client.table("stock_entries").delete().eq("id", row_id).execute()
                        st.success("Item apagado!")
                        st.rerun()
                    except Exception:
                        st.error("Erro ao apagar o item.")
                st.divider()
        else:
            st.info("Nenhum lançamento ativo para esta loja.")

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
                date_range = st.date_input("Filtrar por Período", value=[today, today])
            
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
                "notes": "Financeiro / Obs"
            })
            st.dataframe(renamed_df, use_container_width=True, hide_index=True)
            
            csv_data = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar Planilha (CSV)",
                data=csv_data,
                file_name=f"historico_cm_marmitaria_{today.strftime('%d_%m_%Y')}.csv",
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
