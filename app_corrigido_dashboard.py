import os
import uuid
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Configuração de Página Nível Corporativo
st.set_page_config(
    page_title="CM Marmitaria | Sistema de Gestão de Estoque",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")
PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerante pequeno", "Refrigerante lata", "Pudim", "Água"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# CSS Corporativo Premium (Inspirado em Dashboards de Grandes Empresas)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background-color: #F8FAFC !important;
}

.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Sidebar Corporativa */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E120A 0%, #2A180D 100%) !important;
    border-right: 1px solid #3F2313 !important;
}
[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

/* Botões do Menu Lateral */
[data-testid="stSidebar"] div.stButton > button {
    background-color: rgba(255, 255, 255, 0.05) !important;
    color: #F8FAFC !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    margin-bottom: 0.4rem !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #F59E0B !important;
    color: #1E120A !important;
    border-color: #F59E0B !important;
}

/* Banner da Logo na Sidebar */
.logo-container {
    text-align: center;
    padding: 0.5rem 0 1rem 0;
}
.logo-container img {
    width: 140px;
    height: auto;
    border-radius: 50%;
    border: 3px solid #F59E0B;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

/* Cards das Métricas Principais */
.executive-metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.metric-title-exec {
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value-exec {
    font-size: 1.8rem;
    font-weight: 800;
    color: #0F172A;
    margin-top: 0.2rem;
}
.metric-badge-exec {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
}

/* Cards Individuais das Lojas */
.corp-store-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.corp-store-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.75rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid #F1F5F9;
}
.corp-store-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.corp-store-resp {
    font-size: 0.8rem;
    font-weight: 600;
    color: #B45309;
    background: #FEF3C7;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
}

/* Tabela Interna de Produtos dos Cards */
.corp-product-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.75rem;
    background: #F8FAFC;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    border: 1px solid #F1F5F9;
}
.corp-product-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: #334155;
}
.corp-product-qty {
    font-size: 0.95rem;
    font-weight: 800;
    color: #0F172A;
}

/* Botões Primários do Sistema */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background-color: #F59E0B !important;
    color: #1E120A !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2) !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:hover {
    background-color: #D97706 !important;
    color: #FFFFFF !important;
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
        <div style='text-align: center; background: #FFFFFF; border: 1px solid #E2E8F0; padding: 2.5rem; border-radius: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);'>
            <h1 style='color: #0F172A; font-size: 2rem; font-weight: 800; margin-bottom: 0.2rem;'>CM MARMITARIA</h1>
            <p style='color: #B45309; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px;'>SISTEMA DE GESTÃO E CONTROLE DE ESTOQUE</p>
            <hr style='border: 0; height: 1px; background: #E2E8F0; margin: 1.5rem 0;'>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            login = st.text_input("Usuário ou e-mail", placeholder="Ex.: bia.loja1")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Acessar Painel Executivo", type="primary", use_container_width=True)
            
        if submitted:
            login_value = login.strip()
            if not login_value or not password:
                st.warning("Preencha o usuário e a senha.")
                return
            auth_email = login_value if "@" in login_value else f"{login_value.lower()}@{USERNAME_EMAIL_DOMAIN}"
            try:
                response = client.auth.sign_in_with_password({"email": auth_email, "password": password})
                if not response.user or not response.session:
                    st.error("Credenciais inválidas. Tente novamente.")
                    return
                st.session_state.supabase_user_id = str(response.user.id)
                st.session_state.supabase_email = response.user.email or auth_email
                st.session_state.supabase_access_token = response.session.access_token
                st.session_state.supabase_refresh_token = response.session.refresh_token
                st.rerun()
            except Exception:
                st.error("Falha no login. Verifique seus dados.")


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
        return "Todas as Unidades"
    try:
        result = client.table("stores").select("name").eq("id", store_id).single().execute()
        return result.data["name"]
    except Exception:
        return "Unidade Registrada"


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


# Interface Limpa para Operação de Funcionários
def staff_screen(client: Client, profile: dict):
    store_id = str(profile.get("store_id", ""))
    store_name = get_store_name(client, store_id)
    display_name = profile.get("display_name") or "Operador"

    st.markdown(f"## 🏢 Lançamento de Fechamento · **{store_name}**")
    st.caption(f"Operador responsável: **{display_name}**")

    with st.form("single_staff_form", clear_on_submit=True):
        st.markdown("### 📦 1. Quantidades de Estoque")
        
        form_data = {}
        photos_data = {}
        notes_data = {}

        for product in PRODUCTS:
            st.markdown(f"**🍲 {product}**")
            c1, c2, c3 = st.columns([1, 1.5, 2])
            with c1:
                form_data[product] = st.number_input("Quantidade Restante", min_value=0, step=1, value=0, key=f"q_{product}")
            with c2:
                photos_data[product] = st.file_uploader("Foto da Contagem", type=["jpg", "jpeg", "png", "webp"], key=f"photo_{product}")
            with c3:
                notes_data[product] = st.text_input("Observação", placeholder="Ex: Contagem realizada às 15h...", key=f"note_{product}")
            st.divider()

        st.markdown("### 💰 2. Fechamento Financeiro")
        fc1, fc2 = st.columns(2)
        with fc1:
            card_val = st.number_input("Valor Maquininha / Cartão (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val_in")
            card_photo = st.file_uploader("Foto Comprovante Cartão", type=["jpg", "jpeg", "png", "webp"], key="card_ph_in")
            card_note = st.text_input("Obs Cartão", key="card_note_in")
            
        with fc2:
            cash_val = st.number_input("Valor Dinheiro na Gaveta (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val_in")
            cash_photo = st.file_uploader("Foto Envelope Dinheiro", type=["jpg", "jpeg", "png", "webp"], key="cash_ph_in")
            cash_note = st.text_input("Obs Dinheiro", key="cash_note_in")

        submitted = st.form_submit_button("✅ CONFIRMAR E ENVIAR FECHAMENTO", type="primary", use_container_width=True)

    if submitted:
        try:
            fin_data = {"card": card_val, "cash": cash_val}
            fin_photos = {"card": card_photo, "cash": cash_photo}
            fin_notes = {"card": card_note, "cash": cash_note}
            save_complete_form(client, profile, form_data, photos_data, notes_data, fin_data, fin_photos, fin_notes)
            st.success("✅ Fechamento enviado e confirmado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro no salvamento: {e}")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


# Painel Principal do Administrador (Corporativo)
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
        return (raw or "Unidade Comercial", "Pendente")

    now_time = datetime.now(TZ_BR).strftime("%d/%m/%Y · %H:%M:%S")

    c_top_l, c_top_r = st.columns([3, 1.2])
    with c_top_l:
        st.markdown("""
        <div>
            <h1 style='font-size: 2rem; font-weight: 800; color: #0F172A; margin:0;'>Painel Consolidado de Unidades</h1>
            <p style='font-size: 0.95rem; font-weight: 500; color: #64748B; margin-top: 0.2rem;'>Acompanhamento operacional e financeiro em tempo real</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c_top_r:
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 0.8rem 1.2rem; border-radius: 12px; border: 1px solid #E2E8F0; text-align: right; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Última Sincronização</div>
            <div style="font-size: 0.9rem; font-weight: 800; color: #0F172A; margin-top: 0.1rem;">{now_time}</div>
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
        st.error("Erro ao carregar os dados das unidades.")
        return

    if not stores:
        st.warning("Nenhuma unidade comercial cadastrada no banco de dados.")
        return

    store_names = {str(x["id"]): str(x.get("name") or "Unidade") for x in stores}
    display_names = {key: display_store_name(value)[0] for key, value in store_names.items()}
    staff_by_store = {key: display_store_name(value)[1] for key, value in store_names.items()}
    profile_names = {str(x["user_id"]): x.get("display_name") or "Operador" for x in profiles}
    
    df = pd.DataFrame(entries)
    if not df.empty:
        df["store_id"] = df["store_id"].astype(str)
        df["Loja"] = df["store_id"].map(display_names).fillna("Unidade")
        df["Funcionária"] = df["user_id"].astype(str).map(profile_names).fillna("Operador")
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

    # Métricas Executivas do Topo
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="executive-metric-card">
            <div>
                <div class="metric-title-exec">Unidades Operacionais</div>
                <div class="metric-value-exec">{total_stores}</div>
            </div>
            <span class="metric-badge-exec" style="background:#ECFDF5; color:#047857;">Ativas</span>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        badge_bg = "#FEF2F2" if stores_pending_today > 0 else "#ECFDF5"
        badge_fg = "#B91C1C" if stores_pending_today > 0 else "#047857"
        st.markdown(f"""
        <div class="executive-metric-card">
            <div>
                <div class="metric-title-exec">Pendentes de Envio Hoje</div>
                <div class="metric-value-exec">{stores_pending_today}</div>
            </div>
            <span class="metric-badge-exec" style="background:{badge_bg}; color:{badge_fg};">Atenção</span>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="executive-metric-card">
            <div>
                <div class="metric-title-exec">Estoque de Marmitex</div>
                <div class="metric-value-exec">{total_marmitas}</div>
            </div>
            <span class="metric-badge-exec" style="background:#EFF6FF; color:#1D4ED8;">Unidades</span>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="executive-metric-card">
            <div>
                <div class="metric-title-exec">Fechamentos Concluídos</div>
                <div class="metric-value-exec">{total_financial} / {total_stores}</div>
            </div>
            <span class="metric-badge-exec" style="background:#FEF3C7; color:#B45309;">Hoje</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Navegação Funcional por Páginas
    menu = st.session_state.get("menu_page", "lojas")

    if menu in ["lojas", "inicio"]:
        st.markdown("### 🏪 Visão Consolidada por Unidade")
        st.caption("Detalhamento em tempo real do estoque e observações registradas pelos operadores.")

        grid_cols = st.columns(3)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            with grid_cols[idx % 3]:
                st.markdown(f"""
                <div class="corp-store-card">
                    <div class="corp-store-header">
                        <span class="corp-store-title">🏪 {name}</span>
                        <span class="corp-store-resp">Resp: {resp}</span>
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
                    <div class="corp-product-row">
                        <span class="corp-product-name">{p_name}</span>
                        <span class="corp-product-qty">{qty_val} un.</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("🔎 Auditoria, Observações e Comprovantes"):
                    if not store_latest.empty:
                        for _, r in store_latest.iterrows():
                            p_n = r["product"]
                            path = r.get("photo_path")
                            notes_raw = r.get("notes") or ""
                            
                            obs_item = notes_raw.split("||")[0].replace("Obs Item:", "").strip() if "||" in notes_raw else notes_raw
                            url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                            
                            st.write(f"• **{p_n}**: {obs_item}")
                            if url:
                                st.image(url, width=160)
                            st.divider()

                        first_note = store_latest["notes"].iloc[0] if not store_latest.empty else ""
                        if "[FECHAMENTO FINANCEIRO" in first_note:
                            fin_part = first_note.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1]
                            st.info(f"💰 **Demonstrativo Financeiro:** {fin_part}")

                        if st.button(f"🗑️ Zerar Registros da {name}", key=f"del_st_{sid}"):
                            client.table("stock_entries").delete().eq("store_id", sid).execute()
                            st.success("Registros zerados com sucesso!")
                            st.rerun()
                    else:
                        st.info("Nenhum lançamento ativo para esta unidade.")

                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "produtos":
        st.markdown("### 📦 Inventário Geral de Produtos")
        if not latest.empty:
            st.dataframe(
                latest[["Loja", "product", "quantity_remaining"]].rename(columns={
                    "Loja": "Unidade Comercial", "product": "Item de Produto", "quantity_remaining": "Estoque Atual"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Inventário sem registros ativos.")

    elif menu == "financeiro":
        st.markdown("### 💳 Demonstrativo Financeiro das Unidades")
        if not df.empty:
            fin_entries = df[df["notes"].str.contains("FECHAMENTO FINANCEIRO", na=False)]
            if not fin_entries.empty:
                for _, r in fin_entries.groupby("store_id").first().iterrows():
                    st.markdown(f"#### 🏪 {r['Loja']} (Enviado por: **{r['Funcionária']}**)")
                    notes = r["notes"]
                    fin_part = notes.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1] if "[FECHAMENTO FINANCEIRO DA LOJA] |" in notes else notes
                    st.success(f"💰 {fin_part}")
                    st.divider()
            else:
                st.info("Nenhum fechamento financeiro registrado na data de hoje.")
        else:
            st.info("Sem dados de fechamento no sistema.")

    elif menu == "historico":
        st.markdown("### 📜 Histórico Geral de Operações")
        if not df.empty:
            st.dataframe(
                df[["Data", "Hora", "Loja", "Funcionária", "product", "quantity_remaining", "notes"]].rename(columns={
                    "product": "Produto", "quantity_remaining": "Qtd", "notes": "Observações Auditoria"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Histórico de operações vazio.")

    elif menu == "relatorios":
        st.markdown("### 📊 Relatório Gráfico Consolidado")
        if not latest.empty:
            st.bar_chart(latest.groupby("product")["quantity_remaining"].sum())
        else:
            st.info("Dados insuficientes para consolidação gráfica.")

    elif menu == "configuracoes":
        st.markdown("### ⚙️ Configurações e Status da Infraestrutura")
        st.success("Conexão ativa com o banco de dados Supabase · Fuso Horário Oficial: America/Sao_Paulo (Brasília).")


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
        st.warning("Sessão expirada. Faça login novamente.")
        st.rerun()

    profile = load_profile(client, user_id)
    if not profile:
        st.error("Perfil de usuário não encontrado.")
        if st.button("Sair"):
            sign_out()
        st.stop()

    st.session_state.profile = profile
    display_name = profile.get("display_name") or "Usuário"
    
    # Sidebar Executiva com Logo e Menu Navegável
    with st.sidebar:
        # Exibe a logomarca no canto superior do menu
        st.markdown("""
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/streamlit/streamlit/main/docs/static/logo.png" style="display:none;">
            <h2 style="color: #F59E0B; font-weight: 900; margin:0; font-size: 1.6rem; letter-spacing: -0.5px;">CM MARMITARIA</h2>
            <p style="color: #D97706; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.5px; margin-top: 0.1rem;">QUALIDADE | SABOR | TRADIÇÃO</p>
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
        st.caption("Acesso Master" if profile.get("role") == "admin" else f"Unidade: {get_store_name(client, profile.get('store_id'))}")
        st.divider()
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)


if __name__ == "__main__":
    main()
