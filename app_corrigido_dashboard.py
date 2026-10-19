import os
import uuid
import zoneinfo
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="MARMITEX | Controle de Estoque e Financeiro",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

TZ_BR = zoneinfo.ZoneInfo("America/Sao_Paulo")
PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerante pequeno", "Refrigerante lata", "Pudim", "Água"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

# CSS com Cores Vibrantes, Contraste Forte e Texto BEM Visível
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background-color: #E2E8F0 !important;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Sidebar Amarela Vibrante */
[data-testid="stSidebar"] {
    background-color: #FFCC00 !important;
    border-right: 3px solid #D97706 !important;
}
[data-testid="stSidebar"] * {
    color: #111827 !important;
}

/* Botões da Sidebar */
[data-testid="stSidebar"] div.stButton > button {
    background-color: #000000 !important;
    color: #FFCC00 !important;
    font-weight: 800 !important;
    border-radius: 10px !important;
    border: none !important;
    margin-bottom: 0.3rem !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #1F2937 !important;
}

/* Cartões das Métricas no Topo (Cores Fortes e Textos Escuros) */
.metric-card-1 {
    background: #FDE047;
    border: 3px solid #CA8A04;
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.metric-card-2 {
    background: #F87171;
    border: 3px solid #DC2626;
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.metric-card-3 {
    background: #38BDF8;
    border: 3px solid #0284C7;
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.metric-card-4 {
    background: #4ADE80;
    border: 3px solid #16A34A;
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.metric-value-vibrant {
    font-size: 2.2rem;
    font-weight: 900;
    color: #000000;
    line-height: 1;
}
.metric-label-vibrant {
    font-size: 0.9rem;
    font-weight: 800;
    color: #000000;
    margin-top: 0.3rem;
}

/* Card Container da Loja */
.store-container-vibrant {
    background: #FFFFFF;
    border: 3px solid #000000;
    border-radius: 20px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 6px 14px rgba(0,0,0,0.12);
}
.store-header-vibrant {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    background: #FFCC00;
    padding: 0.8rem;
    border-radius: 14px;
    border: 2px solid #000000;
}
.store-title-vibrant {
    font-size: 1.2rem;
    font-weight: 900;
    color: #000000;
    margin: 0;
}
.store-sub-vibrant {
    font-size: 0.85rem;
    font-weight: 700;
    color: #1F2937;
    margin: 0;
}

/* Items dos Produtos (Amarelo forte) */
.product-pill-vibrant {
    background: #FEF08A;
    border: 2px solid #CA8A04;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.product-name-vibrant {
    font-size: 0.95rem;
    font-weight: 800;
    color: #000000;
}
.product-qty-vibrant {
    font-size: 1.2rem;
    font-weight: 900;
    color: #000000;
    background: #FFCC00;
    padding: 0.2rem 0.6rem;
    border-radius: 8px;
    border: 1px solid #000000;
}

/* Botões Gerais */
div.stButton > button, [data-testid="stFormSubmitButton"] button {
    background-color: #FFCC00 !important;
    color: #000000 !important;
    font-weight: 900 !important;
    border: 2px solid #000000 !important;
    border-radius: 10px !important;
    padding: 0.5rem 1rem !important;
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
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
        <div style='text-align: center; background: #FFCC00; border: 3px solid #000000; padding: 2.5rem; border-radius: 20px; box-shadow: 0 6px 16px rgba(0,0,0,0.15);'>
            <h1 style='color: #000000; font-size: 2.5rem; font-weight: 900; margin-bottom: 0;'>🍲 MARMITEX</h1>
            <p style='color: #000000; font-size: 0.95rem; font-weight: 800;'>CONTROLE DE ESTOQUE E FINANCEIRO</p>
            <hr style='border: 1px solid #000000; margin: 1.5rem 0;'>
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
                    st.error("Não foi possível entrar. Confira seus dados.")
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

    st.markdown(f"## 🍲 Olá, {display_name} · **{store_name}**")
    st.caption("Preencha a contagem dos produtos e o fechamento financeiro no final.")

    with st.form("single_staff_form", clear_on_submit=True):
        st.markdown("### 📦 1. Quantidade de Produtos")
        
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

        st.markdown("### 💰 2. Fechamento Financeiro da Loja")
        fc1, fc2 = st.columns(2)
        with fc1:
            card_val = st.number_input("Maquininha / Cartão (R$)", min_value=0.0, step=0.50, value=0.0, key="card_val_in")
            card_photo = st.file_uploader("Foto do comprovante cartão", type=["jpg", "jpeg", "png", "webp"], key="card_ph_in")
            card_note = st.text_input("Obs Maquininha", key="card_note_in")
            
        with fc2:
            cash_val = st.number_input("Dinheiro na Gaveta (R$)", min_value=0.0, step=0.50, value=0.0, key="cash_val_in")
            cash_photo = st.file_uploader("Foto Envelope / Dinheiro", type=["jpg", "jpeg", "png", "webp"], key="cash_ph_in")
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


# Dashboard do Administrador
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
        return (raw or "Unidade sem nome", "Cadastro pendente")

    now_time = datetime.now(TZ_BR).strftime("%d/%m/%Y · %H:%M")

    # Top Bar
    c_top_l, c_top_r = st.columns([3, 1.5])
    with c_top_l:
        st.markdown("""
        <div>
            <h1 style='font-size: 2.2rem; font-weight: 900; color: #000000; margin:0;'>Olá, Admin!</h1>
            <p style='font-size: 1rem; font-weight: 700; color: #374151; margin:0;'>Aqui está o resumo de todas as lojas.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c_top_r:
        st.markdown(f"""
        <div style="background: #FFCC00; padding: 0.75rem 1rem; border-radius: 12px; border: 2px solid #000000; text-align: right; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <span style="font-size: 0.95rem; font-weight: 900; color: #000000;">📅 {now_time}</span><br>
            <span style="font-size: 0.85rem; color: #047857; font-weight: 800;">🟢 Sistema Online</span>
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

    # 4 CARDS MÉTRICAS COM CORES FORTES E VIBRANTES
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card-1">
            <div class="metric-value-vibrant">🏪 {total_stores}</div>
            <div class="metric-label-vibrant">Lojas Ativas</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="metric-card-2">
            <div class="metric-value-vibrant">⚠️ {stores_pending_today}</div>
            <div class="metric-label-vibrant">Lojas Sem Registro Hoje</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-card-3">
            <div class="metric-value-vibrant">📦 {total_marmitas}</div>
            <div class="metric-label-vibrant">Total de Marmitex</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="metric-card-4">
            <div class="metric-value-vibrant">💳 {total_financial}</div>
            <div class="metric-label-vibrant">Fechamentos Hoje</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # MENU LATERAL NAVEGÁVEL (PÁGINAS)
    menu = st.session_state.get("menu_page", "lojas")

    if menu in ["lojas", "inicio"]:
        st.markdown("## 🏪 Lojas e Lançamentos")
        st.caption("Visão individual de cada loja com as quantidades atualizadas e observações enviadas.")

        grid_cols = st.columns(3)
        for idx, store in enumerate(stores):
            sid = str(store["id"])
            name = display_names[sid]
            resp = staff_by_store[sid]
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else pd.DataFrame()

            with grid_cols[idx % 3]:
                st.markdown(f"""
                <div class="store-container-vibrant">
                    <div class="store-header-vibrant">
                        <div>
                            <div class="store-title-vibrant">🏪 {name}</div>
                            <div class="store-sub-vibrant">Responsável: {resp}</div>
                        </div>
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
                    <div class="product-pill-vibrant">
                        <span class="product-name-vibrant">{p_name}</span>
                        <span class="product-qty-vibrant">{qty_val} un.</span>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("👁️ Ver Observações e Fotos"):
                    if not store_latest.empty:
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
                            st.warning(f"💰 **Financeiro:** {fin_part}")

                        if st.button(f"🗑️ Apagar registros da {name}", key=f"del_st_{sid}"):
                            client.table("stock_entries").delete().eq("store_id", sid).execute()
                            st.success("Registros apagados com sucesso!")
                            st.rerun()
                    else:
                        st.info("Sem lançamentos ativos para esta loja.")

                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "produtos":
        st.markdown("## 📦 Consolidado por Produto")
        if not latest.empty:
            st.dataframe(
                latest[["Loja", "product", "quantity_remaining"]].rename(columns={
                    "product": "Produto", "quantity_remaining": "Quantidade Restante"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhum produto com estoque no momento.")

    elif menu == "financeiro":
        st.markdown("## 💳 Fechamentos Financeiros das Lojas")
        if not df.empty:
            fin_entries = df[df["notes"].str.contains("FECHAMENTO FINANCEIRO", na=False)]
            if not fin_entries.empty:
                for _, r in fin_entries.groupby("store_id").first().iterrows():
                    st.markdown(f"### 🏪 {r['Loja']} (Enviado por: {r['Funcionária']})")
                    notes = r["notes"]
                    fin_part = notes.split("[FECHAMENTO FINANCEIRO DA LOJA] |")[1] if "[FECHAMENTO FINANCEIRO DA LOJA] |" in notes else notes
                    st.success(f"💰 {fin_part}")
                    st.divider()
            else:
                st.info("Nenhum fechamento financeiro hoje.")
        else:
            st.info("Nenhum registro até o momento.")

    elif menu == "historico":
        st.markdown("## 📜 Histórico Geral de Lançamentos")
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
        st.markdown("## 📊 Relatório Gráfico")
        if not latest.empty:
            st.bar_chart(latest.groupby("product")["quantity_remaining"].sum())
        else:
            st.info("Sem dados suficientes.")

    elif menu == "configuracoes":
        st.markdown("## ⚙️ Configurações do Sistema")
        st.success("Sistema conectado ao Supabase com fuso horário ajustado para Brasília.")


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
    
    # Sidebar com Links Funcionais
    with st.sidebar:
        st.markdown("<h2 style='text-align:center; color: #000000; font-weight: 900;'>🍲 MARMITEX</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size: 0.8rem; color: #000000; font-weight: 800;'>Controle de Estoque e Financeiro</p>", unsafe_allow_html=True)
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
        st.caption("Acesso Total" if profile.get("role") == "admin" else f"Loja: {get_store_name(client, profile.get('store_id'))}")
        st.divider()
        if st.button("🚪 Sair da Conta", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)


if __name__ == "__main__":
    main()
