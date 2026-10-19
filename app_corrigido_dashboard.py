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

# Estilização CSS Baseada na Identidade Visual da CM Marmitaria
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* Fundo Geral Amarelo Suave */
.stApp {
    background-color: #FFFDF0 !important;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Menu Lateral (Sidebar) Amarelo Ouro com Texto Marrom */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFCC00 0%, #F5B800 100%) !important;
    border-right: 2px solid #E6A100;
}
[data-testid="stSidebar"] * {
    color: #2A1200 !important;
}

/* Cabeçalho Principal (Hero) */
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

/* Cartões de Métricas (KPIs) */
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

/* Badges / Status */
.badge {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-success { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
.badge-warning { background-color: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; }

/* Estilização dos Botões */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background-color: #FFB300 !important;
    color: #2A1200 !important;
    font-weight: 700 !important;
    border: 2px solid #E69900 !important;
    border-radius: 12px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
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


def add_stock_entries(client: Client, profile: dict, quantities: dict, photos: dict, notes: str):
    user_id = str(profile["user_id"])
    store_id = str(profile["store_id"])
    created_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for product in PRODUCTS:
        raw = quantities.get(product)
        if raw is None or str(raw).strip() == "":
            raise ValueError(f"Informe a quantidade de {product.lower()}.")
        quantity = int(raw)
        if quantity < 0:
            raise ValueError("As quantidades não podem ser negativas.")
        photo_path = upload_photo(client, photos.get(product), store_id, user_id)
        rows.append({
            "store_id": store_id,
            "user_id": user_id,
            "product": product,
            "quantity_remaining": quantity,
            "photo_path": photo_path,
            "notes": notes.strip() or None,
            "created_at": created_at,
        })
    return client.table("stock_entries").insert(rows).execute()


# Interface das Funcionárias (Mobile Otimizado em Amarelo/Marrom)
def staff_screen(client: Client, profile: dict):
    store_name = get_store_name(client, profile.get("store_id"))
    display_name = profile.get("display_name") or "Funcionária"
    
    st.markdown(f"""
    <div class="hero-header">
        <div style="font-size: 0.85rem; font-weight: 700; color: #8C4A00; text-transform: uppercase;">CM MARMITARIA</div>
        <h1>👋 Olá, {display_name}</h1>
        <p>Lançamento de Estoque · <strong>{store_name}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 Digite a quantidade restante de cada produto hoje. Adicione fotos se necessário.")

    with st.form("stock_entry_form", clear_on_submit=False):
        quantities = {}
        photos = {}
        
        for idx, product in enumerate(PRODUCTS):
            st.markdown(f"#### 🍲 {product}")
            c1, c2 = st.columns([1.2, 1])
            with c1:
                quantities[product] = st.number_input(
                    "Quantidade restante", min_value=0, step=1, value=0, key=f"qty_{idx}"
                )
            with c2:
                with st.expander("📷 Foto (opcional)"):
                    photos[product] = st.file_uploader(
                        "Anexar foto",
                        type=["jpg", "jpeg", "png", "webp"],
                        key=f"photo_{idx}",
                        label_visibility="collapsed"
                    )
            st.divider()

        notes = st.text_area("Observações da loja (opcional)", placeholder="Ex.: Chegou reposição de bebidas às 11h...")
        submitted = st.form_submit_button("✅ Salvar Lançamento no Sistema", type="primary", use_container_width=True)

    if submitted:
        try:
            add_stock_entries(client, profile, quantities, photos, notes)
            st.success("🎉 Lançamento salvo com sucesso no banco de dados!")
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Não foi possível salvar o lançamento. Verifique a conexão.")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


# Painel do Administrador (Dashboard CM Marmitaria)
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
        <p>Acompanhamento das 7 unidades comerciais em tempo real</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        stores = client.table("stores").select("id, name").execute().data or []
        entries = client.table("stock_entries").select(
            "id, store_id, user_id, product, quantity_remaining, photo_path, notes, created_at"
        ).order("created_at", desc=True).limit(2000).execute().data or []
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
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        df["Data e hora"] = df["created_at"].dt.tz_convert("America/Sao_Paulo").dt.strftime("%d/%m/%Y %H:%M:%S")
        latest = df.dropna(subset=["created_at"]).sort_values("created_at").groupby(["store_id", "product"], as_index=False).tail(1)
    else:
        latest = pd.DataFrame(columns=["store_id", "product", "quantity_remaining", "created_at", "Loja", "Data e hora", "Funcionária", "photo_path", "notes"])

    # Indicadores Gerais
    total_stores = len(stores)
    today = pd.Timestamp.now(tz="America/Sao_Paulo").date()
    total_latest_units = int(pd.to_numeric(latest.get("quantity_remaining", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not latest.empty else 0
    entries_today = int((df["created_at"].dt.tz_convert("America/Sao_Paulo").dt.date == today).sum()) if not df.empty else 0

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

    # Abas atualizadas com o que você pediu
    tab_overview, tab_stores, tab_carteirinhas, tab_history, tab_reports = st.tabs([
        "📌 Resumo de Marmitas", 
        "🏪 Gerenciar por Loja", 
        "🏷️ Carteirinhas de Estoque", 
        "📜 Histórico Geral", 
        "📊 Relatório"
    ])

    with tab_overview:
        st.markdown("### 🍲 Resumo de Marmitas por Responsável")
        st.caption("Visão focada na quantidade de marmitas pequenas e grandes de cada unidade.")
        
        cards = st.columns(3)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else latest
            
            # Pega especificamente a quantidade de marmitas pequenas e grandes
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
                st.warning("Tem certeza? Esta ação apagará todo o histórico e lançamentos desta loja.")
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
        st.caption("Visão geral simultânea com o estoque de cada produto por unidade, sem precisar usar filtros.")
        
        for store in stores:
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()
            
            # Monta um dicionário com os produtos daquela loja
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
        st.markdown("### Histórico Geral de Lançamentos")
        if not df.empty:
            st.dataframe(
                df[["Loja", "product", "quantity_remaining", "Data e hora", "Funcionária", "notes"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum lançamento registrado até o momento.")

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
