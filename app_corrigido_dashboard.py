import os
import uuid
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="CM MARMITARIA | Sistema de Gestão",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")
PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerante pequeno", "Refrigerante lata", "Pudim", "Água"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# CSS Avançado - Design Compacto, Cores da Marca CM e Zero Desperdício de Espaço
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background-color: #12161F !important; /* Fundo Escuro Nobre */
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1600px !important;
}

/* Sidebar Amarelada com Cores Oficiais da Marca */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFC800 0%, #E6B200 100%) !important;
    border-right: 2px solid #3F1D0B !important;
}
[data-testid="stSidebar"] * {
    color: #3F1D0B !important;
}

/* Botões do Menu Lateral */
[data-testid="stSidebar"] div.stButton > button {
    background-color: #3F1D0B !important;
    color: #FFC800 !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
    border: none !important;
    margin-bottom: 0.2rem !important;
    padding: 0.4rem 0.8rem !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #261106 !important;
    color: #FFFFFF !important;
}

/* Cards de Métricas Compactos */
.metric-mini-card {
    background: #1E2430;
    border: 1px solid #2A3245;
    border-left: 5px solid #FFC800;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.metric-title {
    font-size: 0.75rem;
    font-weight: 800;
    color: #94A3B8;
    text-transform: uppercase;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: 900;
    color: #FFFFFF;
    margin-top: 0.1rem;
}

/* Cards das Lojas Compactos e Densos */
.store-card-dense {
    background: #1E2430;
    border: 1px solid #2A3245;
    border-radius: 12px;
    padding: 0.9rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.25);
}
.store-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.6rem;
    border-bottom: 1px solid #2A3245;
}
.store-card-title {
    font-size: 1rem;
    font-weight: 900;
    color: #FFC800;
}
.store-card-badge {
    background: #3F1D0B;
    color: #FFC800;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
    border: 1px solid #FFC800;
}

/* Linhas dos Produtos dentro da Loja */
.product-row-compact {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #161B26;
    border: 1px solid #242B3B;
    border-radius: 6px;
    padding: 0.35rem 0.6rem;
    margin-bottom: 0.3rem;
}
.product-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: #E2E8F0;
}
.product-count {
    font-size: 0.88rem;
    font-weight: 900;
    color: #FFC800;
    background: #2A1D0B;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
}

/* Ajuste Geral nos Botões */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background: #FFC800 !important;
    color: #3F1D0B !important;
    font-weight: 900 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.8rem !important;
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
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 0.9, 1])
    with c2:
        st.markdown("""
        <div style='text-align: center; background: #FFC800; border: 3px solid #3F1D0B; padding: 2rem; border-radius: 16px;'>
            <h1 style='color: #3F1D0B; font-size: 2.2rem; font-weight: 900; margin: 0;'>CM MARMITARIA</h1>
            <p style='color: #3F1D0B; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px;'>QUALIDADE | SABOR | TRADIÇÃO</p>
            <hr style='border: 1px solid #3F1D0B; margin: 1rem 0;'>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Usuário ou e-mail", placeholder="Ex.: bia.loja1")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("ACESSAR SISTEMA", type="primary", use_container_width=True)
            
        if submitted:
            login_value = login.strip()
            if not login_value or not password:
                st.warning("Preencha o usuário e a senha.")
                return
            auth_email = login_value if "@" in login_value else f"{login_value.lower()}@{USERNAME_EMAIL_DOMAIN}"
            try:
                response = client.auth.sign_in_with_password({"email": auth_email, "password": password})
                if not response.user or not response.session:
                    st.error("Dados de acesso incorretos.")
                    return
                st.session_state.supabase_user_id = str(response.user.id)
                st.session_state.supabase_email = response.user.email or auth_email
                st.session_state.supabase_access_token = response.session.access_token
                st.session_state.supabase_refresh_token = response.session.refresh_token
                st.rerun()
            except Exception:
                st.error("Erro ao autenticar no banco de dados.")


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


# Interface Limpa e Direta para Funcionárias
def staff_screen(client: Client, profile: dict):
    store_id = str(profile.get("store_id", ""))
    store_name = get_store_name(client, store_id)
    display_name = profile.get("display_name") or "Funcionária"

    st.markdown(f"<h2 style='color:#FFC800;'>🍲 Fechamento de Estoque · {store_name}</h2>", unsafe_allow_html=True)
    st.caption(f"Operador: {display_name}")

    with st.form("single_staff_form", clear_on_submit=True):
        st.markdown("<h4 style='color:#FFFFFF;'>📦 1. Quantidade dos Produtos</h4>", unsafe_allow_html=True)
        
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

        st.markdown("<h4 style='color:#FFFFFF;'>💰 2. Fechamento Financeiro</h4>", unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            card_val = st.number_input("Maquininha (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val_in")
            card_photo = st.file_uploader("Foto Comprovante Maquininha", type=["jpg", "jpeg", "png", "webp"], key="card_ph_in")
            card_note = st.text_input("Obs Maquininha", key="card_note_in")
            
        with fc2:
            cash_val = st.number_input("Dinheiro na Gaveta (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val_in")
            cash_photo = st.file_uploader("Foto Dinheiro / Envelope", type=["jpg", "jpeg", "png", "webp"], key="cash_ph_in")
            cash_note = st.text_input("Obs Dinheiro", key="cash_note_in")

        submitted = st.form_submit_button("✅ ENVIAR FECHAMENTO", type="primary", use_container_width=True)

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


# Painel Administrador Ultra Compacto
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
        return (raw or "Unidade", "Cadastro Pk")

    now_time = datetime.now(TZ_BR).strftime("%d/%m/%Y · %H:%M")

    # Header de Topo Direto e Compacto
    c_top_l, c_top_r = st.columns([3, 1])
    with c_top_l:
        st.markdown("""
        <div>
            <h2 style='color: #FFC800; font-weight: 900; margin: 0;'>CM MARMITARIA · Painel de Controle</h2>
            <p style='color: #94A3B8; font-size: 0.85rem; margin: 0;'>Acompanhamento em tempo real das unidades</p>
        </div>
        """, unsafe_allow_html=True)
    with c_top_r:
        st.markdown(f"""
        <div style="background: #1E2430; padding: 0.4rem 0.8rem; border-radius: 8px; border: 1px solid #2A3245; text-align: right;">
            <span style="font-size: 0.8rem; font-weight: 800; color: #FFC800;">📅 {now_time}</span>
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

    # 4 Cartões Super Compactos no Topo
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-mini-card">
            <div class="metric-title">Lojas Ativas</div>
            <div class="metric-value">🏪 {total_stores}</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="metric-mini-card" style="border-left-color: #EF4444;">
            <div class="metric-title">Sem Registro Hoje</div>
            <div class="metric-value" style="color:#EF4444;">⚠️ {stores_pending_today}</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-mini-card" style="border-left-color: #3B82F6;">
            <div class="metric-title">Marmitas no Estoque</div>
            <div class="metric-value">📦 {total_marmitas}</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="metric-mini-card" style="border-left-color: #10B981;">
            <div class="metric-title">Fechamentos Hoje</div>
            <div class="metric-value">💳 {total_financial}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Navegação entre Abas do Menu
    menu = st.session_state.get("menu_page", "lojas")

    if menu in ["lojas", "inicio"]:
        st.markdown("<h3 style='color:#FFFFFF;'>🏪 Visão por Unidade</h3>", unsafe_allow_html=True)

        grid_cols = st.columns(3)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            with grid_cols[idx % 3]:
                st.markdown(f"""
                <div class="store-card-dense">
                    <div class="store-card-header">
                        <span class="store-card-title">{name}</span>
                        <span class="store-card-badge">Resp: {resp}</span>
                    </div>
                """, unsafe_allow_html=True)

                prod_dict = {p: 0 for p in PRODUCTS}
                if not store_latest.empty:
                    for _, r in store_latest.iterrows():
                        p_n = r["product"]
                        if p_n in prod_dict:
                            prod_dict[p_n] = int(r["quantity_remaining"])

                for p_name in PRODUCTS:
                    qty_val = prod_dict[p_name]
                    st.markdown(f"""
                    <div class="product-row-compact">
                        <span class="product-label">{p_name}</span>
                        <span class="product-count">{qty_val} un</span>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("👁️ Observações / Fotos"):
                    if not store_latest.empty:
                        for _, r in store_latest.iterrows():
                            p_n = r["product"]
                            path = r.get("photo_path")
                            notes_raw = r.get("notes") or ""
                            
                            obs_item = notes_raw.split("||")[0].replace("Obs Item:", "").strip() if "||" in notes_raw else notes_raw
                            url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                            
                            st.write(f"• **{p_n}**: {obs_item}")
                            if url:
                                st.image(url, width=130)
                            st.divider()

                        first_note = store_latest["notes"].iloc[0] if not store_latest.empty else ""
                        if "[FECHAMENTO FINANCEIRO" in first_note:
                            fin_part = first_note.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1]
                            st.info(f"💰 {fin_part}")

                        if st.button(f"🗑️ Zerar registros", key=f"del_st_{sid}"):
                            client.table("stock_entries").delete().eq("store_id", sid).execute()
                            st.success("Registros zerados!")
                            st.rerun()
                    else:
                        st.caption("Sem registros ativos hoje.")

                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "produtos":
        st.markdown("<h3 style='color:#FFFFFF;'>📦 Inventário Consolidado</h3>", unsafe_allow_html=True)
        if not latest.empty:
            st.dataframe(
                latest[["Loja", "product", "quantity_remaining"]].rename(columns={
                    "product": "Produto", "quantity_remaining": "Quantidade Restante"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhum registro ativo.")

    elif menu == "financeiro":
        st.markdown("<h3 style='color:#FFFFFF;'>💳 Fechamento Financeiro</h3>", unsafe_allow_html=True)
        if not df.empty:
            fin_entries = df[df["notes"].str.contains("FECHAMENTO FINANCEIRO", na=False)]
            if not fin_entries.empty:
                for _, r in fin_entries.groupby("store_id").first().iterrows():
                    st.markdown(f"#### 🏪 {r['Loja']} (Enviado por: {r['Funcionária']})")
                    notes = r["notes"]
                    fin_part = notes.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1] if "[FECHAMENTO FINANCEIRO DA LOJA] |" in notes else notes
                    st.success(f"💰 {fin_part}")
                    st.divider()
            else:
                st.info("Nenhum fechamento registrado hoje.")
        else:
            st.info("Sem dados até o momento.")

    elif menu == "historico":
        st.markdown("<h3 style='color:#FFFFFF;'>📜 Histórico Geral</h3>", unsafe_allow_html=True)
        if not df.empty:
            st.dataframe(
                df[["Data", "Hora", "Loja", "Funcionária", "product", "quantity_remaining", "notes"]].rename(columns={
                    "product": "Produto", "quantity_remaining": "Qtd", "notes": "Observações & Financeiro"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Histórico vazio.")

    elif menu == "relatorios":
        st.markdown("<h3 style='color:#FFFFFF;'>📊 Relatórios</h3>", unsafe_allow_html=True)
        if not latest.empty:
            st.bar_chart(latest.groupby("product")["quantity_remaining"].sum())
        else:
            st.info("Sem dados suficientes.")

    elif menu == "configuracoes":
        st.markdown("<h3 style='color:#FFFFFF;'>⚙️ Configurações</h3>", unsafe_allow_html=True)
        st.success("Conexão ativa com o Supabase · Fuso Horário de Brasília.")


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
    
    # Menu Lateral com Cores Oficiais da CM Marmitaria
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0;">
            <h2 style="color: #3F1D0B; font-weight: 900; margin: 0; font-size: 1.5rem;">CM MARMITARIA</h2>
            <p style="color: #3F1D0B; font-size: 0.65rem; font-weight: 800; margin-top: 0.1rem;">QUALIDADE | SABOR | TRADIÇÃO</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        if st.button("📌 Página Inicial", use_container_width=True):
            st.session_state.menu_page = "lojas"
            st.rerun()
        if st.button("🏪 Lojas", use_container_width=True):
            st.session_state.menu_page = "lojas"
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
        if st.button("🚪 Sair da Conta", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)


if __name__ == "__main__":
    main()
