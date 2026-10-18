import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Controle de Estoque | 7 Lojas", page_icon="📦", layout="wide")

PRODUCTS = ["Marmitex pequena", "Marmitex grande", "Refrigerantes Peq", "Pudim", "Refrigerante lata", "Água"]
PRODUCT_PRICES = {"Marmitex pequena": 11.99, "Marmitex grande": 15.00, "Refrigerantes Peq": 4.00, "Pudim": 5.00, "Refrigerante lata": 7.00, "Água": 4.00}
PRODUCT_COLORS = ["#2563EB", "#7C3AED", "#0891B2", "#DB2777", "#EA580C", "#059669"]
BUCKET = "stock-photos"
USERNAME_EMAIL_DOMAIN = "estoque.invalid"

st.markdown("""
<style>
:root { --gold:#f5c400; --gold-dark:#8a6500; --ink:#201b08; --cream:#fff9df; }
.block-container { padding-top:1rem; padding-bottom:1.5rem; max-width:1600px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#ffd600 0%,#f5bd00 100%); }
[data-testid="stSidebar"] * { color:#201b08; }
[data-testid="stMetric"] { background:linear-gradient(135deg,#fff8d6,#ffed91); padding:14px; border:1px solid #f0d66b; border-radius:15px; }
.hero { padding:1.1rem 1.35rem; border-radius:18px; color:#201b08; background:linear-gradient(120deg,#ffdf55,#f5c400,#ffe994); margin-bottom:1rem; border:1px solid #e8bd18; }
.hero h1 { color:#201b08; margin:0; font-size:1.8rem; }
.hero p { color:#594600; margin:.25rem 0 0; }
.store-card { border:1px solid #f0d66b; border-radius:15px; padding:.85rem; background:#fffdf4; box-shadow:0 3px 12px rgba(70,50,0,.07); margin-bottom:.45rem; }
.pill { display:inline-block; border-radius:999px; padding:.15rem .5rem; font-size:.75rem; font-weight:700; }
.product-line { display:flex; align-items:center; justify-content:space-between; gap:.5rem; padding:.55rem .2rem; border-bottom:1px solid #f2e6b8; }
.product-line:last-child { border-bottom:0; }
.qty-pill { background:#fff0a8; color:#765700; border-radius:9px; padding:.25rem .55rem; font-weight:800; white-space:nowrap; }
div.stButton > button, [data-testid="stFormSubmitButton"] button { border-radius:10px; }
@media(max-width:700px) { .block-container {padding-left:.7rem;padding-right:.7rem;} .hero h1 {font-size:1.35rem;} }
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
    st.title("📦 Controle de Estoque — 7 Lojas")
    st.write("Funcionárias: entrem com seu nome de usuário e senha. Administração: use o e-mail cadastrado.")
    with st.form("login_form"):
        login = st.text_input("Usuário ou e-mail", placeholder="Ex.: ana.loja1")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
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
            st.error("Não foi possível entrar. Confira o usuário e a senha ou fale com a pessoa administradora.")
    st.caption("Cada funcionária deve ter seu próprio usuário e senha. Não compartilhe sua senha com outras pessoas.")


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


def staff_screen(client: Client, profile: dict):
    store_name = get_store_name(client, profile.get("store_id"))
    st.title("Registrar estoque")
    st.caption(f"Loja: **{store_name}** · Acesso de lançamento")
    st.info("Preencha a quantidade que ainda existe de cada produto. As fotos são opcionais.")

    with st.form("stock_entry_form", clear_on_submit=False):
        quantities = {}
        photos = {}
        for idx, product in enumerate(PRODUCTS):
            st.subheader(product)
            col1, col2 = st.columns([1, 1.4])
            with col1:
                quantities[product] = st.number_input(
                    f"Quantidade restante — {product}", min_value=0, step=1, value=0, key=f"qty_{idx}"
                )
            with col2:
                photos[product] = st.file_uploader(
                    f"Foto de {product} (opcional)",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=False,
                    key=f"photo_{idx}",
                    help="Você pode tirar uma foto com a câmera do celular ou escolher uma imagem. Máximo 8 MB.",
                )
            st.divider()
        notes = st.text_area("Observações (opcional)", placeholder="Ex.: chegou uma reposição às 11h.")
        submitted = st.form_submit_button("Salvar lançamento", type="primary", use_container_width=True)

    if submitted:
        try:
            add_stock_entries(client, profile, quantities, photos, notes)
            st.success("Lançamento salvo! Seus pais poderão acompanhar as informações no painel administrativo.")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error("Não foi possível salvar o lançamento.")
            st.caption(f"Detalhe técnico: {type(exc).__name__}: {str(exc)[:500]}")
            st.info("Se aparecer 'row-level security policy', o bloqueio está nas regras do Supabase e precisa ser corrigido nelas; não desative o RLS.")


def signed_photo_url(client: Client, path: str):
    try:
        response = client.storage.from_(BUCKET).create_signed_url(path, 60 * 30)
        return response.get("signedURL") or response.get("signedUrl")
    except Exception:
        return None


def admin_dashboard(client: Client, profile: dict):
    # Os nomes exibidos aqui são apenas rótulos de interface; não alteram IDs nem dados do Supabase.
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
    <div class="hero">
      <h1>⌂ MARMITEX · CONTROLE DE ESTOQUE</h1>
      <p>Visão geral das unidades · atualização automática a cada 5 minutos</p>
    </div>
    """, unsafe_allow_html=True)

    @st.fragment(run_every=300)
    def live_panel():
        try:
            stores = client.table("stores").select("id, name").execute().data or []
            entries = client.table("stock_entries").select(
                "id, store_id, user_id, product, quantity_remaining, photo_path, notes, created_at"
            ).order("created_at", desc=True).limit(2000).execute().data or []
            profiles = client.table("profiles").select("user_id, display_name").execute().data or []
        except Exception as exc:
            st.error("Não foi possível carregar o painel. Confira a conexão e as permissões do Supabase.")
            st.caption(f"Detalhe técnico: {type(exc).__name__}: {str(exc)[:300]}")
            return

        if not stores:
            st.warning("Nenhuma unidade foi encontrada na tabela stores do Supabase.")
            return

        store_names = {str(x["id"]): str(x.get("name") or "Unidade sem nome") for x in stores}
        display_names = {key: display_store_name(value)[0] for key, value in store_names.items()}
        staff_by_store = {key: display_store_name(value)[1] for key, value in store_names.items()}
        profile_names = {str(x["user_id"]): x.get("display_name") or "Usuário" for x in profiles}
        df = pd.DataFrame(entries)
        if not df.empty:
            df["store_id"] = df["store_id"].astype(str)
            df["Loja"] = df["store_id"].map(display_names).fillna("Unidade não identificada")
            df["Funcionária"] = df["user_id"].astype(str).map(profile_names).fillna("Usuário")
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
            df["Data e hora"] = df["created_at"].dt.tz_convert("America/Sao_Paulo").dt.strftime("%d/%m/%Y %H:%M")
            latest = df.dropna(subset=["created_at"]).sort_values("created_at").groupby(["store_id", "product"], as_index=False).tail(1)
        else:
            latest = pd.DataFrame(columns=["store_id", "product", "quantity_remaining", "created_at", "Loja", "Data e hora", "Funcionária", "photo_path", "notes"])

        # Indicadores gerais
        total_stores = len(stores)
        stores_with_entries = set(df["store_id"].astype(str)) if not df.empty else set()
        stores_without_entries = total_stores - len(stores_with_entries)
        total_latest_units = int(pd.to_numeric(latest.get("quantity_remaining", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not latest.empty else 0
        today = pd.Timestamp.now(tz="America/Sao_Paulo").date()
        entries_today = int((df["created_at"].dt.tz_convert("America/Sao_Paulo").dt.date == today).sum()) if not df.empty else 0
        photos_count = int(df["photo_path"].fillna("").astype(str).str.strip().ne("").sum()) if not df.empty else 0
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Unidades cadastradas", total_stores, help="Total de lojas cadastradas no Supabase")
        k2.metric("Unidades sem registro", stores_without_entries, help="Lojas sem nenhum lançamento no histórico carregado")
        k3.metric("Unidades em estoque*", total_latest_units, help="Soma das últimas quantidades registradas por produto e loja")
        k4.metric("Registros de hoje", entries_today)
        st.caption(f"Fotos anexadas no histórico carregado: {photos_count} · *A quantidade é calculada a partir do último registro de cada produto, não de entradas/saídas automáticas.")

        # Sidebar navigation and selected store
        with st.sidebar:
            st.markdown("<div style='text-align:center;font-size:2.2rem'>🍲</div><h2 style='text-align:center;margin-top:0'>MARMITEX</h2><p style='text-align:center;font-size:.8rem'>CONTROLE DE ESTOQUE</p>", unsafe_allow_html=True)
            page = st.radio("NAVEGAÇÃO", ["Visão Geral", "Lojas", "Produtos", "Histórico", "Relatórios", "Configurações"], key="admin_nav", label_visibility="collapsed")
            st.divider()
            st.caption("Acesso administrativo")

        # Latest row for each store/product
        if not latest.empty:
            latest["quantity_remaining"] = pd.to_numeric(latest["quantity_remaining"], errors="coerce").fillna(0)
        marmitas = latest[latest["product"].isin(["Marmitex pequena", "Marmitex grande"])] if not latest.empty else latest
        marmita_totals = marmitas.groupby("store_id")["quantity_remaining"].sum().to_dict() if not marmitas.empty else {}
        sorted_low = sorted(stores, key=lambda x: marmita_totals.get(str(x["id"]), 0))
        low_store = sorted_low[0] if sorted_low else None

        if page == "Visão Geral":
            st.markdown("### Status das unidades")
            st.caption("Clique no nome de uma unidade no menu Lojas para ver quantidades e fotos ao lado de cada produto.")
            cards = st.columns(3)
            for idx, store in enumerate(stores):
                sid = str(store["id"])
                name = display_names[sid]
                store_latest = latest[latest["store_id"] == sid] if not latest.empty else latest
                store_rows = df[df["store_id"] == sid] if not df.empty else df
                last_time = store_rows["created_at"].max() if not store_rows.empty else pd.NaT
                has_today = pd.notna(last_time) and last_time.tz_convert("America/Sao_Paulo").date() == today
                qty = int(pd.to_numeric(store_latest.get("quantity_remaining", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not store_latest.empty else 0
                low = sid == str(low_store["id"]) if low_store else False
                with cards[idx % 3]:
                    st.markdown('<div class="store-card">', unsafe_allow_html=True)
                    st.markdown(f"#### 🏪 {name}")
                    st.caption(f"Responsável: {staff_by_store[sid]}")
                    st.markdown(f"**{qty} unidades registradas**")
                    if pd.notna(last_time):
                        local_time = last_time.tz_convert("America/Sao_Paulo").strftime("%d/%m · %H:%M")
                        st.caption(f"Último registro: {local_time}")
                    else:
                        st.caption("Ainda sem registros")
                    if not has_today:
                        st.warning("Aguardando atualização de hoje")
                    elif low:
                        st.error("Menor quantidade de marmitas")
                    else:
                        st.success("Atualizada hoje")
                    st.markdown('</div>', unsafe_allow_html=True)
                    if st.button(f"Ver {name}", key=f"overview_{sid}", use_container_width=True):
                        st.session_state["selected_store_id"] = sid
                        st.session_state["admin_nav"] = "Lojas"
                        st.rerun()

            st.markdown("### ⚠️ Lojas que precisam de atenção")
            low_rows = []
            for store in sorted_low[:5]:
                sid = str(store["id"])
                low_rows.append({"Unidade": display_names[sid], "Marmitas registradas": int(marmita_totals.get(sid, 0)), "Responsável": staff_by_store[sid]})
            if low_rows:
                st.dataframe(pd.DataFrame(low_rows), use_container_width=True, hide_index=True)
            left, right = st.columns(2)
            with left:
                st.markdown("### Produtos por quantidade")
                if not latest.empty:
                    totals = latest.groupby("product", as_index=False)["quantity_remaining"].sum().rename(columns={"product":"Produto", "quantity_remaining":"Unidades"})
                    st.bar_chart(totals.set_index("Produto"), color="#E9B923", use_container_width=True)
                else:
                    st.info("Os gráficos aparecerão quando houver lançamentos.")
            with right:
                st.markdown("### Resumo rápido")
                st.metric("Produtos monitorados", len(PRODUCTS))
                st.metric("Lojas com registro hoje", sum(1 for store in stores if not df.empty and ((df[df["store_id"] == str(store["id"])]["created_at"].dt.tz_convert("America/Sao_Paulo").dt.date == today).any())))
                st.metric("Sem registro no histórico", stores_without_entries)

        elif page == "Lojas":
            st.markdown("### 🏪 Visão individual das lojas")
            options = {display_names[str(store["id"])]: str(store["id"]) for store in stores}
            labels = list(options.keys())
            default_sid = st.session_state.get("selected_store_id")
            default_index = next((i for i, label in enumerate(labels) if options[label] == default_sid), 0)
            selected_label = st.selectbox("Escolha a loja", labels, index=default_index)
            sid = options[selected_label]
            selected_store = next(x for x in stores if str(x["id"]) == sid)
            store_latest = latest[latest["store_id"] == sid] if not latest.empty else latest
            store_history = df[df["store_id"] == sid].copy() if not df.empty else df.copy()
            store_last = store_history["created_at"].max() if not store_history.empty else pd.NaT
            st.markdown(f"<div class='hero'><h1>🏪 {selected_label}</h1><p>Responsável: {staff_by_store[sid]} · Estoque registrado nesta unidade</p></div>", unsafe_allow_html=True)
            a, b, c = st.columns(3)
            a.metric("Unidades registradas", int(pd.to_numeric(store_latest.get("quantity_remaining", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not store_latest.empty else 0)
            a_marm = store_latest[store_latest["product"].isin(["Marmitex pequena", "Marmitex grande"])] if not store_latest.empty else store_latest
            b.metric("Marmitas registradas", int(pd.to_numeric(a_marm.get("quantity_remaining", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not a_marm.empty else 0)
            c.metric("Último registro", store_last.tz_convert("America/Sao_Paulo").strftime("%d/%m %H:%M") if pd.notna(store_last) else "Sem registro")
            st.markdown("#### Estoque por produto · foto junto do registro")
            for product in PRODUCTS:
                rows = store_latest[store_latest["product"] == product] if not store_latest.empty else store_latest
                if rows.empty:
                    st.markdown(f"<div class='store-card'><b>{product}</b><br><span style='color:#8a6500'>Ainda sem registro</span></div>", unsafe_allow_html=True)
                    continue
                row = rows.iloc[-1]
                cols = st.columns([4, 1, 1])
                with cols[0]:
                    st.markdown(f"**{product}**  ")
                    st.caption(f"Último registro: {row.get('Data e hora', '—')} · {row.get('Funcionária', 'Usuário')}")
                    if row.get("notes"):
                        st.caption(f"Observação: {row.get('notes')}")
                with cols[1]:
                    st.markdown(f"<div class='qty-pill'>{int(row['quantity_remaining'])} un.</div>", unsafe_allow_html=True)
                with cols[2]:
                    path = row.get("photo_path")
                    url = signed_photo_url(client, path) if isinstance(path, str) and path.strip() else None
                    if url:
                        with st.popover("📷 Foto"):
                            st.image(url, use_container_width=True)
                    else:
                        st.caption("Sem foto")
                st.divider()
            st.markdown("#### Histórico desta loja")
            if store_history.empty:
                st.info("Esta loja ainda não tem lançamentos.")
            else:
                hist_view = store_history[["product", "quantity_remaining", "Data e hora", "Funcionária", "notes"]].rename(columns={"product":"Produto", "quantity_remaining":"Quantidade", "Data e hora":"Data e hora", "Funcionária":"Funcionária", "notes":"Observações"})
                st.dataframe(hist_view.head(100), use_container_width=True, hide_index=True)

        elif page == "Produtos":
            st.markdown("### 📦 Produtos cadastrados")
            for product in PRODUCTS:
                qty = int(pd.to_numeric(latest.loc[latest["product"] == product, "quantity_remaining"], errors="coerce").fillna(0).sum()) if not latest.empty else 0
                st.markdown(f"<div class='store-card'><b>{product}</b><span style='float:right' class='qty-pill'>{qty} un.</span><br><small>Preço cadastrado: R$ {PRODUCT_PRICES[product]:.2f}</small></div>", unsafe_allow_html=True)

        elif page == "Histórico":
            st.markdown("### 🕘 Histórico de registros")
            if df.empty:
                st.info("Ainda não existem lançamentos.")
            else:
                f1, f2 = st.columns(2)
                store_filter = f1.selectbox("Filtrar loja", ["Todas as lojas"] + list(display_names.values()))
                product_filter = f2.selectbox("Filtrar produto", ["Todos os produtos"] + PRODUCTS)
                hist = df.copy()
                if store_filter != "Todas as lojas": hist = hist[hist["Loja"] == store_filter]
                if product_filter != "Todos os produtos": hist = hist[hist["product"] == product_filter]
                view = hist[["Loja", "product", "quantity_remaining", "Data e hora", "Funcionária", "notes"]].rename(columns={"product":"Produto", "quantity_remaining":"Quantidade", "notes":"Observações"})
                st.dataframe(view, use_container_width=True, hide_index=True)
                csv = view.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ Exportar histórico (CSV para Excel)", data=csv, file_name="historico_estoque.csv", mime="text/csv", use_container_width=True)

        elif page == "Relatórios":
            st.markdown("### 📊 Relatórios")
            if not latest.empty:
                report = latest.groupby(["Loja", "product"], as_index=False)["quantity_remaining"].sum().rename(columns={"Loja":"Unidade", "product":"Produto", "quantity_remaining":"Quantidade registrada"})
                st.dataframe(report, use_container_width=True, hide_index=True)
                st.download_button("Exportar relatório CSV", data=report.to_csv(index=False).encode("utf-8-sig"), file_name="relatorio_estoque.csv", mime="text/csv")
            else:
                st.info("Não há dados suficientes para montar o relatório.")

        else:
            st.markdown("### ⚙️ Configurações")
            st.info("As configurações de contas, permissões e cadastro de unidades continuam sendo gerenciadas no Supabase. Esta tela não altera configurações do banco.")
            st.caption("Para manter a segurança, não desative as políticas RLS do Supabase.")

    live_panel()

def main():
    client = get_client()
    if client is None:
        st.title("📦 Controle de Estoque — 7 Lojas")
        st.error("O sistema ainda não está conectado ao Supabase.")
        st.markdown("Abra o arquivo `README.md` do projeto e configure `SUPABASE_URL` e `SUPABASE_ANON_KEY`.")
        st.stop()

    user_id = st.session_state.get("supabase_user_id")
    if not user_id:
        login_screen(client)
        st.stop()

    if not restore_auth_session(client):
        st.warning("Sua sessão expirou. Entre novamente.")
        st.rerun()

    profile = load_profile(client, user_id)
    if not profile:
        st.error("Seu login existe, mas ainda não está associado a um perfil de acesso. Peça à administração para concluir seu cadastro.")
        if st.button("Sair"):
            sign_out()
        st.stop()

    st.session_state.profile = profile
    display_name = profile.get("display_name") or st.session_state.get("supabase_email", "Usuário")
    with st.sidebar:
        st.title("📦 Controle de Estoque")
        st.write(f"Olá, **{display_name}**")
        st.caption("Perfil: Administrador" if profile.get("role") == "admin" else f"Loja: {get_store_name(client, profile.get('store_id'))}")
        st.divider()
        if st.button("Sair da conta", use_container_width=True):
            sign_out()

    if profile.get("role") == "admin":
        admin_dashboard(client, profile)
    elif profile.get("role") == "staff" and profile.get("store_id"):
        staff_screen(client, profile)
    else:
        st.error("Este perfil está incompleto. Peça à administração para conferir o papel e a loja vinculada.")


if __name__ == "__main__":
    main()
