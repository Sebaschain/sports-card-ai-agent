"""
Aplicación web para análisis de tarjetas deportivas
Interfaz interactiva con Streamlit
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import time
import streamlit_authenticator as stauth

from src.utils.auth_utils import hash_password

from src.agents.price_analyzer_agent import PriceAnalyzerAgent

# from src.agents.supervisor_agent import SupervisorAgent # Moved inside getter to avoid ImportError
from src.tools.ebay_tool import EBayTool, EBaySearchParams
from src.models.card import Card, Player, Sport, CardCondition, PricePoint


# Configuración de la página
st.set_page_config(
    page_title="Sports Card AI Agent",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos personalizados
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_agent():
    """Obtiene instancia del agente (cacheada)"""
    return PriceAnalyzerAgent(verbose=False)


@st.cache_resource
def get_supervisor_agent():
    """Obtiene instancia del supervisor (cacheada)"""
    from src.agents.supervisor_agent import SupervisorAgent

    return SupervisorAgent()


@st.cache_resource
def get_ebay_tool():
    """Obtiene instancia de herramienta eBay (cacheada)"""
    return EBayTool()


@st.cache_resource
def get_market_agent():
    """Obtiene instancia del agente de mercado (cacheada)"""
    from src.agents.market_research_agent import MarketResearchAgent

    return MarketResearchAgent()


@st.cache_resource
def get_vision_tool():
    """Obtiene instancia de herramienta Vision (cacheada)"""
    from src.tools.card_vision_tool import CardVisionTool

    return CardVisionTool()


def create_price_chart(prices: list, title: str = "Historial de Precios"):
    """Crea gráfico de precios con Plotly"""
    df = pd.DataFrame(
        [
            {
                "Fecha": p.timestamp,
                "Precio": p.price,
                "Estado": "Vendido" if p.sold else "Listado",
            }
            for p in prices
        ]
    )

    fig = go.Figure()

    # Línea de precios
    fig.add_trace(
        go.Scatter(
            x=df["Fecha"],
            y=df["Precio"],
            mode="lines+markers",
            name="Precio",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=8),
        )
    )

    # Línea de promedio
    avg_price = df["Precio"].mean()
    fig.add_hline(
        y=avg_price,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Promedio: ${avg_price:.2f}",
        annotation_position="right",
    )

    fig.update_layout(
        title=title,
        xaxis_title="Fecha",
        yaxis_title="Precio (USD)",
        hovermode="x unified",
        height=400,
    )

    return fig


def main():
    """Función principal de la app"""
    from src.utils.database import get_db, init_db
    from src.utils.repository import CardRepository
    from src.models.db_models import UserDB

    # Initialize database on first run
    try:
        init_db()
    except Exception:
        pass

    # 1. Configuración de Autenticación
    with get_db() as db:
        users = db.query(UserDB).all()
        # Mapeo para stauth
        credentials = {
            "usernames": {
                u.username: {
                    "name": u.full_name,
                    "password": u.hashed_password,
                    "email": u.email,
                }
                for u in users
            }
        }

    authenticator = stauth.Authenticate(
        credentials,
        "sports_card_agent_cookie",
        "sports_card_agent_key",
        cookie_expiry_days=30,
    )

    # Sidebar Login/Logout
    st.sidebar.title("🔐 Acceso")

    # Manejar Registro si no hay usuarios
    if not users:
        st.info("👋 ¡Bienvenido! Crea tu primer usuario para empezar.")
        with st.expander("📝 Registro", expanded=True):
            with st.form("register_form"):
                new_user = st.text_input("Usuario")
                new_email = st.text_input("Email")
                new_pass = st.text_input("Password", type="password")
                new_name = st.text_input("Nombre Completo")
                reg_btn = st.form_submit_button("Registrarse")

                if reg_btn:
                    with get_db() as db:
                        # Check if username or email already exists
                        existing_user = CardRepository.get_user_by_username(
                            db, new_user
                        )
                        existing_email = CardRepository.get_user_by_email(db, new_email)

                        if existing_user:
                            st.error(
                                f"❌ El usuario '{new_user}' ya existe. Por favor elige otro."
                            )
                        elif existing_email:
                            st.error(
                                f"❌ El email '{new_email}' ya está registrado. Por favor usa otro."
                            )
                        else:
                            new_user_db = CardRepository.create_user(
                                db,
                                new_user,
                                new_email,
                                hash_password(new_pass),
                                new_name,
                            )
                            db.commit()

                        # Migración automática: Vincular tarjetas existentes (user_id IS NULL) al primer usuario
                        with get_db() as db:
                            from src.models.db_models import (
                                PortfolioItemDB,
                                WatchlistDB,
                            )

                            orphaned_portfolio = (
                                db.query(PortfolioItemDB)
                                .filter(PortfolioItemDB.user_id.is_(None))
                                .all()
                            )
                            for item in orphaned_portfolio:
                                item.user_id = new_user_db.id

                            orphaned_watchlist = (
                                db.query(WatchlistDB)
                                .filter(WatchlistDB.user_id.is_(None))
                                .all()
                            )
                            for item in orphaned_watchlist:
                                item.user_id = new_user_db.id

                            db.commit()

                        st.success(
                            "¡Usuario creado y datos vinculados! Por favor inicia sesión."
                        )
                        st.rerun()

    authenticator.login(location="sidebar")

    authentication_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")
    username = st.session_state.get("username")

    if authentication_status is False:
        st.error("Usuario/password incorrecto")
        return
    elif authentication_status is None:
        st.warning("Por favor inicia sesión para continuar")
        st.image(
            "https://images.unsplash.com/photo-1540747913346-19e3adca174f?auto=format&fit=crop&q=80&w=1000",
            caption="Sports Card AI Agent",
        )
        # Mostrar también opción de registro para nuevos usuarios si ya hay usuarios
        if users:
            with st.expander("📝 ¿No tienes cuenta? Regístrate"):
                with st.form("register_form_new"):
                    new_user = st.text_input("Nuevo Usuario")
                    new_email = st.text_input("Email")
                    new_pass = st.text_input("Password", type="password")
                    new_name = st.text_input("Nombre Completo")
                    reg_btn = st.form_submit_button("Crear Cuenta")
                    if reg_btn:
                        with get_db() as db:
                            # Check if username or email already exists
                            existing_user = CardRepository.get_user_by_username(
                                db, new_user
                            )
                            existing_email = CardRepository.get_user_by_email(
                                db, new_email
                            )

                            if existing_user:
                                st.error(f"❌ El usuario '{new_user}' ya existe.")
                            elif existing_email:
                                st.error(
                                    f"❌ El email '{new_email}' ya está registrado."
                                )
                            else:
                                CardRepository.create_user(
                                    db,
                                    new_user,
                                    new_email,
                                    hash_password(new_pass),
                                    new_name,
                                )
                                db.commit()
                                st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                                st.rerun()
        return

    # Usuario autenticado
    st.sidebar.success(f"Sesión iniciada: {name}")
    authenticator.logout("Logout (Cerrar Sesión)", "sidebar")

    with get_db() as db:
        current_user = CardRepository.get_user_by_username(db, username)

        # Safety check: if user not found in DB but authenticated by stauth (sync issue)
        if current_user is None:
            st.error(
                f"⚠️ El usuario '{username}' no se encontró en la base de datos local."
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Instrucciones"):
                    st.info(
                        "Para reiniciar completamente, usa el botón 'Logout' en la barra lateral (sidebar) a la izquierda."
                    )

                # Optional: Force clear if possible
                if st.button("🧹 Limpiar Estado Local"):
                    # Clear stauth session state
                    st.session_state["authentication_status"] = None
                    st.session_state["username"] = None
                    st.session_state["name"] = None
                    if "logout" in st.session_state:
                        del st.session_state["logout"]
                    st.rerun()

            with col2:
                # Add option to register this user directly if it's missing (helps sync)
                with st.expander("🛠️ Reparar cuenta"):
                    with st.form("fix_account_form"):
                        fix_email = st.text_input(
                            "Confirmar Email", value=st.session_state.get("email", "")
                        )
                        fix_name = st.text_input("Confirmar Nombre", value=name)
                        fix_pass = st.text_input(
                            "Nueva Password (temporal)", type="password"
                        )
                        if st.form_submit_button("Crear usuario en base de datos"):
                            # Safety validation before fixing
                            existing_user = CardRepository.get_user_by_username(
                                db, username
                            )
                            existing_email = CardRepository.get_user_by_email(
                                db, fix_email
                            )

                            if existing_user:
                                st.error(
                                    f"❌ El usuario '{username}' ya existe en la base de datos."
                                )
                            elif existing_email:
                                st.error(
                                    f"❌ El email '{fix_email}' ya está registrado."
                                )
                            else:
                                CardRepository.create_user(
                                    db,
                                    username,
                                    fix_email,
                                    hash_password(fix_pass),
                                    fix_name,
                                )
                                db.commit()
                                st.success("¡Usuario restaurado! Recargando...")
                                st.rerun()
            return

        user_id = current_user.id

    # (Logout button moved up to enable it during safety check)

    # Header
    st.markdown(
        '<h1 class="main-header">🏀 Sports Card AI Agent</h1>', unsafe_allow_html=True
    )
    st.markdown(
        f"### Análisis inteligente de tarjetas deportivas - Usuario: {username}"
    )

    # Sidebar
    st.sidebar.title("⚙️ Configuración")

    # Selección de deporte
    sport = st.sidebar.selectbox(
        "Deporte", options=["NBA", "NHL", "MLB", "NFL", "Soccer"], index=0
    )

    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Búsqueda en eBay",
            "Análisis de Tarjeta",
            "My Portfolio",
            "History",
            "Dashboard",
        ]
    )

    # ============================================================
    # TAB 1: Búsqueda en eBay
    # ============================================================
    with tab1:
        st.header("Buscar Tarjetas en eBay")

        col1, col2 = st.columns([2, 1])

        with col1:
            search_query = st.text_input(
                "Buscar tarjeta",
                placeholder="Ej: LeBron James 2003 Topps Rookie",
                help="Ingresa el nombre del jugador, año, fabricante, etc.",
            )

        with col2:
            max_results = st.number_input(
                "Máximo de resultados", min_value=5, max_value=50, value=10, step=5
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            sold_only = st.checkbox("Solo vendidos", value=False)
        with col2:
            min_price = st.number_input(
                "Precio mínimo ($)", min_value=0.0, value=0.0, step=10.0
            )
        with col3:
            max_price = st.number_input(
                "Precio máximo ($)", min_value=0.0, value=0.0, step=100.0
            )

        if st.button("Buscar", type="primary", use_container_width=True):
            if not search_query:
                st.warning("Por favor ingresa un término de búsqueda")
            else:
                with st.spinner("Buscando en eBay..."):
                    try:
                        tool = get_ebay_tool()
                        params = EBaySearchParams(
                            keywords=search_query,
                            max_results=max_results,
                            sold_items_only=sold_only,
                            min_price=min_price if min_price > 0 else None,
                            max_price=max_price if max_price > 0 else None,
                        )

                        # Ejecutar búsqueda
                        listings = asyncio.run(tool.search_cards(params))

                        if not listings:
                            st.warning("No se encontraron resultados")
                        else:
                            st.success(f"Encontrados {len(listings)} resultados")

                            # Mostrar resultados
                            for i, listing in enumerate(listings, 1):
                                with st.expander(f"#{i} - {listing.title[:80]}..."):
                                    col1, col2 = st.columns([1, 2])

                                    with col1:
                                        if listing.image_url:
                                            st.image(listing.image_url, width=200)

                                    with col2:
                                        st.markdown(f"**Título:** {listing.title}")
                                        st.markdown(
                                            f"**Precio:** ${listing.price:.2f} {listing.currency}"
                                        )
                                        st.markdown(
                                            f"**Condición:** {listing.condition}"
                                        )
                                        st.markdown(
                                            f"**Estado:** {'VENDIDO' if listing.sold else 'A LA VENTA'}"
                                        )
                                        st.markdown(
                                            f"**Vendedor:** {listing.seller_username}"
                                        )
                                        st.markdown(
                                            f"**Ubicación:** {listing.location}"
                                        )
                                        if (
                                            listing.shipping_cost
                                            and listing.shipping_cost > 0
                                        ):
                                            st.markdown(
                                                f"**Envío:** ${listing.shipping_cost:.2f}"
                                            )
                                        st.markdown(
                                            f"[Ver en eBay]({listing.listing_url})"
                                        )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # ============================================================
    # TAB 2: Análisis de Tarjeta
    # ============================================================
    with tab2:
        st.header("Análisis Inteligente de Tarjeta")

        st.info(
            "💡 Esta sección usa el agente de IA para analizar precios y generar recomendaciones"
        )

        # Reconocimiento de Imagen
        st.subheader("📸 Identificación por Imagen")
        uploaded_file = st.file_uploader(
            "Sube una foto de tu tarjeta para autocompletar el formulario",
            type=["jpg", "jpeg", "png"],
            key="vision_analysis",
        )

        if uploaded_file is not None:
            if st.button("🔍 Identificar con Vision AI", key="btn_vision_analysis"):
                with st.spinner("🤖 Analizando imagen con Vision AI..."):
                    try:
                        vision_tool = get_vision_tool()
                        image_bytes = uploaded_file.read()
                        card_data = asyncio.run(vision_tool.identify_card(image_bytes))

                        if card_data.get("success"):
                            st.success("✅ Tarjeta identificada correctamente!")
                            # Guardar en session_state para pre-llenar el formulario
                            st.session_state["vision_data"] = card_data
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {card_data.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")

        # Obtener valores predeterminados de session_state si existen
        v_data = st.session_state.get("vision_data", {})

        # Formulario para ingresar datos de la tarjeta
        with st.form("card_analysis_form"):
            col1, col2 = st.columns(2)

            with col1:
                player_name = st.text_input(
                    "Nombre del jugador",
                    value=v_data.get("player_name", "LeBron James"),
                )
                year = st.number_input(
                    "Año",
                    min_value=1900,
                    max_value=2025,
                    value=int(v_data.get("year", 2003)) if v_data.get("year") else 2003,
                )
                manufacturer = st.text_input(
                    "Fabricante", value=v_data.get("manufacturer", "Topps")
                )
                set_name = st.text_input(
                    "Nombre del set", value=v_data.get("set_name", "Topps Chrome")
                )

            with col2:
                card_number = st.text_input(
                    "Número de tarjeta", value=v_data.get("card_number", "221")
                )
                variant = st.text_input(
                    "Variante", value=v_data.get("variant", "Rookie Card")
                )
                grade = st.number_input(
                    "Grado (si está graduada)",
                    min_value=1.0,
                    max_value=10.0,
                    value=float(v_data.get("grade", 9.5))
                    if v_data.get("grade")
                    else 9.5,
                    step=0.5,
                )
                grading_company = st.text_input(
                    "Compañía de graduación", value=v_data.get("grading_company", "PSA")
                )

            player_performance = st.text_area(
                "Rendimiento reciente del jugador",
                value="El jugador está en excelente forma, promediando 28 puntos por partido",
                height=100,
            )

            # Seleccionar tipo de análisis
            analysis_type = st.radio(
                "Tipo de análisis",
                options=["Avanzado (IA Multi-Agente)", "Básico (Reglas)"],
                index=0,
                help="El análisis avanzado usa múltiples agentes para investigar mercado y jugador en tiempo real",
            )

            # Seleccionar tendencia de precios para demostración (solo para análisis básico)
            price_trend = "Estable"
            if analysis_type == "Básico (Reglas)":
                price_trend = st.selectbox(
                    "Tendencia de precios (demo)",
                    options=["Bajando", "Subiendo", "Estable"],
                    help="Para demostración, selecciona cómo han estado los precios",
                )

            submitted = st.form_submit_button(
                "🤖 Analizar con IA", type="primary", use_container_width=True
            )

        if submitted:
            with st.spinner("🤖 El agente está analizando la tarjeta..."):
                try:
                    # Crear modelo de tarjeta
                    player = Player(
                        id=player_name.lower().replace(" ", "-"),
                        name=player_name,
                        sport=Sport[sport],
                        team="Unknown",
                        position="Unknown",
                    )

                    card = Card(
                        id=f"{player.id}-{year}",
                        player=player,
                        year=year,
                        manufacturer=manufacturer,
                        set_name=set_name,
                        card_number=card_number,
                        variant=variant,
                        condition=CardCondition.MINT,
                        graded=True,
                        grade=grade,
                        grading_company=grading_company,
                    )

                    if analysis_type == "Básico (Reglas)":
                        # Generar precios de ejemplo basados en tendencia
                        base_price = 1000.0
                        prices = []

                        for i in range(30):
                            date = datetime.now() - timedelta(days=30 - i)

                            if price_trend == "Subiendo":
                                price = base_price + (i * 20)
                            elif price_trend == "Bajando":
                                price = base_price - (i * 15)
                            else:
                                price = base_price + ((-1) ** i * 50)

                            price_point = PricePoint(
                                card_id=card.id,
                                price=max(price, 100),
                                marketplace="ebay",
                                listing_url="https://ebay.com/item/demo",
                                timestamp=date,
                                sold=True,
                            )
                            prices.append(price_point)

                        # Analizar con el agente básico
                        agent = get_agent()
                        recommendation = agent.analyze_card(
                            card=card,
                            price_history=prices,
                            player_performance=player_performance,
                        )

                        # Mostrar resultados (Básico)
                        st.success("Análisis básico completado")

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Señal", recommendation.signal.value.upper())
                        with col2:
                            st.metric("Confianza", f"{recommendation.confidence:.0%}")
                        with col3:
                            st.metric(
                                "Precio Actual", f"${recommendation.current_price:.2f}"
                            )
                        with col4:
                            avg_price = sum(p.price for p in prices) / len(prices)
                            diff = recommendation.current_price - avg_price
                            st.metric(
                                "vs. Promedio",
                                f"${diff:+.2f}",
                                f"{(diff / avg_price) * 100:+.1f}%",
                            )

                        st.plotly_chart(
                            create_price_chart(prices, "Historial de Precios (Demo)"),
                            use_container_width=True,
                        )
                        st.subheader("📝 Razonamiento")
                        st.info(recommendation.reasoning)
                        st.subheader("📌 Factores")
                        for factor in recommendation.factors:
                            st.markdown(f"• {factor}")

                    else:
                        # Análisis Avanzado
                        supervisor = get_supervisor_agent()
                        result = asyncio.run(
                            supervisor.analyze_investment_opportunity(
                                player_name=player_name,
                                year=year,
                                manufacturer=manufacturer,
                                sport=sport,
                            )
                        )

                        st.success("Análisis avanzado multi-agente completado")

                        # Resultados Multi-Agente
                        rec = result["recommendation"]
                        detailed = result["detailed_analysis"]

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Señal", rec["signal"])
                        with col2:
                            st.metric("Confianza", f"{rec['confidence']:.0%}")
                        with col3:
                            st.metric("Riesgo/Recompensa", rec["risk_reward"]["ratio"])

                        # Mostrar detalles por agente
                        tabs = st.tabs(["📉 Mercado", "🏀 Jugador", "📈 Estrategia"])

                        with tabs[0]:
                            market = detailed["market"]["market_analysis"]
                            st.subheader("Análisis de Mercado (eBay)")
                            st.write(f"Ítems vendidos: {market['sold_items']['count']}")
                            st.write(
                                f"Precio promedio: ${market['sold_items']['average_price']:.2f}"
                            )
                            st.write(f"Insight: {market['market_insight']}")

                        with tabs[1]:
                            player_ana = detailed["player"]
                            st.subheader("Rendimiento del Jugador")

                            # Mostrar si los datos son reales o simulados
                            stats_info = player_ana.get("real_stats", {})
                            if stats_info.get("simulated"):
                                st.warning(
                                    "⚠️ Utilizando datos simulados (API no configurada)"
                                )
                            elif stats_info.get("note"):
                                st.info(f"ℹ️ {stats_info['note']}")

                            st.write(
                                f"**Outlook:** {player_ana['analysis']['future_outlook']}"
                            )
                            st.write(
                                f"**Score:** {player_ana['analysis']['performance_score']['overall_score']}/100"
                            )

                            if player_ana.get("sentiment") and player_ana[
                                "sentiment"
                            ].get("sentiment"):
                                st.write(
                                    f"Sentimiento: {player_ana['sentiment']['sentiment']}"
                                )

                        with tabs[2]:
                            st.subheader("Estrategia Detallada")
                            st.write(result["reasoning"])
                            st.write("**Acciones Recomendadas:**")
                            for item in result["action_items"]:
                                st.markdown(f"• {item}")

                            st.write("**Precios Objetivo:**")
                            targets = rec["price_targets"]
                            st.write(f"- Entrada: ${targets['entry_price']:.2f}")
                            st.write(f"- Venta: ${targets['target_sell_price']:.2f}")
                            st.write(f"- Stop Loss: ${targets['stop_loss']:.2f}")

                except Exception as e:
                    st.error(f"Error en el análisis: {str(e)}")
                    import traceback

                    st.code(traceback.format_exc())

    # ============================================================
    # TAB 3: My Portfolio
    # ============================================================
    with tab3:
        st.header("Mi Portfolio de Tarjetas")

        st.info("📊 Administra tu colección y trackea el valor de tus inversiones")

        # Dos columnas: Formulario y Portfolio
        col_form, col_portfolio = st.columns([1, 2])

        with col_form:
            st.subheader("➕ Añadir Tarjeta")

            # Vision AI para Portfolio
            st.markdown("---")
            st.markdown("#### 📸 Autocompletar con Foto")
            uploaded_port = st.file_uploader(
                "Sube una foto de tu tarjeta",
                type=["jpg", "jpeg", "png"],
                key="vision_port",
            )

            if uploaded_port is not None:
                if st.button("🔍 Identificar", key="btn_vision_port"):
                    with st.spinner("🤖 Analizando..."):
                        try:
                            vision_tool = get_vision_tool()
                            image_bytes = uploaded_port.read()
                            card_data = asyncio.run(
                                vision_tool.identify_card(image_bytes)
                            )

                            if card_data.get("success"):
                                st.success("✅ Identificada!")
                                st.session_state["port_vision_data"] = card_data
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {card_data.get('error')}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

            # Obtener valores de vision si existen
            vp_data = st.session_state.get("port_vision_data", {})

            with st.form("add_portfolio_form"):
                player_name_port = st.text_input(
                    "Jugador", value=vp_data.get("player_name", "LeBron James")
                )

                col1, col2 = st.columns(2)
                with col1:
                    year_port = st.number_input(
                        "Año",
                        min_value=1900,
                        max_value=2025,
                        value=int(vp_data.get("year", 2003))
                        if vp_data.get("year")
                        else 2003,
                    )
                with col2:
                    available_sports = ["NBA", "NHL", "MLB", "NFL", "Soccer"]
                    sport_index = 0
                    if vp_data.get("sport") in available_sports:
                        sport_index = available_sports.index(vp_data["sport"])

                    sport_port = st.selectbox(
                        "Deporte",
                        available_sports,
                        index=sport_index,
                        key="portfolio_sport",
                    )

                manufacturer_port = st.text_input(
                    "Fabricante", value=vp_data.get("manufacturer", "Topps")
                )

                # Campos de Rareza
                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    is_rookie = st.checkbox(
                        "Rookie Card",
                        value=vp_data.get("variant") == "Rookie Card"
                        or vp_data.get("is_rookie", False),
                    )
                with col_r2:
                    is_auto = st.checkbox(
                        "Autógrafo", value=vp_data.get("is_auto", False)
                    )
                with col_r3:
                    is_numbered = st.checkbox(
                        "Numerada", value=vp_data.get("is_numbered", False)
                    )

                if is_numbered:
                    col_n1, col_n2 = st.columns(2)
                    with col_n1:
                        seq_num = st.number_input(
                            "Número (Ej: 10)", min_value=1, value=1
                        )
                    with col_n2:
                        max_print = st.number_input(
                            "De un total de (Ej: 99)", min_value=1, value=99
                        )
                else:
                    seq_num, max_print = None, None

                col1, col2 = st.columns(2)
                with col1:
                    purchase_price = st.number_input(
                        "Precio de Compra ($)", min_value=0.0, value=100.0, step=10.0
                    )
                with col2:
                    quantity = st.number_input("Cantidad", min_value=1, value=1, step=1)

                purchase_date = st.date_input("Fecha de Compra", value=datetime.now())

                notes = st.text_area(
                    "Notas", placeholder="Ej: PSA 9, comprada en eBay", height=80
                )

                acquisition_source = st.selectbox(
                    "Fuente de Adquisición",
                    ["eBay", "Tienda Local", "Convención", "Intercambio", "Otro"],
                    index=0,
                )

                submitted = st.form_submit_button(
                    "➕ Añadir al Portfolio", type="primary", use_container_width=True
                )

            if submitted:
                try:
                    from src.utils.database import get_db
                    from src.utils.repository import CardRepository

                    with st.spinner("Añadiendo al portfolio..."):
                        with get_db() as db:
                            # Get or create player
                            player_id = f"{player_name_port.lower().replace(' ', '-')}-{sport_port.lower()}"
                            player = CardRepository.get_or_create_player(
                                db=db,
                                player_id=player_id,
                                name=player_name_port,
                                sport=sport_port,
                            )
                            print(f"DEBUG: Player created - {player.name}")

                            # Get or create card
                            card_id = (
                                f"{player_id}-{year_port}-{manufacturer_port.lower()}"
                            )
                            card = CardRepository.get_or_create_card(
                                db=db,
                                card_id=card_id,
                                player_db=player,
                                year=year_port,
                                manufacturer=manufacturer_port,
                                is_rookie=is_rookie,
                                is_auto=is_auto,
                                is_numbered=is_numbered,
                                max_print=max_print,
                                sequence_number=seq_num,
                            )
                            print(f"DEBUG: Card created - {card.card_id}")

                            # Add to portfolio
                            portfolio_item = CardRepository.add_to_portfolio(
                                db=db,
                                card=card,
                                user_id=user_id,
                                purchase_price=purchase_price,
                                purchase_date=datetime.combine(
                                    purchase_date, datetime.min.time()
                                ),
                                quantity=quantity,
                                notes=notes,
                                acquisition_source=acquisition_source,
                            )
                            print(
                                f"DEBUG: Portfolio item created - ID {portfolio_item.id}"
                            )

                            # Commit explicitly
                            db.commit()
                            print("DEBUG: Transaction committed")

                            st.success(f"{player_name_port} añadido al portfolio!")
                            st.cache_data.clear()
                            time.sleep(0.5)
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al añadir: {str(e)}")
                    print("ERROR COMPLETO:")
                    import traceback

                    traceback.print_exc()

        with col_portfolio:
            col_title, col_refresh = st.columns([3, 1])
            with col_title:
                st.subheader("Tu Portfolio")
            with col_refresh:
                if st.button("🔄 Actualizar", key="refresh_portfolio"):
                    st.rerun()

                if st.button(
                    "🤖 Sync IA",
                    key="sync_portfolio_ia",
                    help="Actualiza los precios usando IA (tardará unos segundos)",
                ):
                    with st.spinner(
                        "🤖 El agente está investigando precios actuales..."
                    ):
                        try:
                            from src.utils.database import get_db
                            from src.utils.repository import CardRepository

                            agent = get_market_agent()
                            with get_db() as db:
                                results = asyncio.run(
                                    CardRepository.update_all_portfolio_prices(
                                        db, user_id, agent
                                    )
                                )
                                db.commit()

                                if results["updated"] > 0:
                                    st.success(
                                        f"✅ Actualizados {results['updated']} precios"
                                    )
                                    for detail in results["details"]:
                                        if "✅" in detail:
                                            st.toast(detail)
                                else:
                                    st.info("No se encontraron cambios significativos")

                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error en sync: {str(e)}")

            try:
                from src.utils.database import get_db
                from src.utils.repository import CardRepository

                with get_db() as db:
                    # Get portfolio stats
                    stats = CardRepository.get_portfolio_stats(db, user_id)

                    # Display stats
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "Tarjetas",
                            stats["total_items"],
                            help="Total de tarjetas en portfolio",
                        )

                    with col2:
                        st.metric(
                            "Invertido",
                            f"${stats['total_invested']:.2f}",
                            help="Total invertido",
                        )

                    with col3:
                        st.metric(
                            "Valor Actual",
                            f"${stats['current_value']:.2f}",
                            help="Valor actual del portfolio",
                        )

                    with col4:
                        delta_color = (
                            "normal" if stats["total_gain_loss"] >= 0 else "inverse"
                        )
                        st.metric(
                            "Ganancia/Pérdida",
                            f"${stats['total_gain_loss']:.2f}",
                            f"{stats['total_gain_loss_pct']:+.1f}%",
                            delta_color=delta_color,
                            help="Ganancia o pérdida total",
                        )

                    refresh_key = st.empty()
                    with refresh_key:
                        st.write(
                            f"Última actualización: {datetime.now().strftime('%H:%M:%S')}"
                        )

                    # Get portfolio items
                    portfolio_items = CardRepository.get_portfolio(
                        db, user_id, active_only=True
                    )

                    if not portfolio_items:
                        st.info(
                            "📭 Tu portfolio está vacío. Añade tu primera tarjeta arriba."
                        )
                    else:
                        # Display items
                        st.divider()

                        for item in portfolio_items:
                            with st.expander(
                                f"{item['player_name']} - {item['year']} {item['manufacturer']} "
                                f"({('+' if item['gain_loss'] >= 0 else '')}"
                                f"${abs(item['gain_loss']):.2f})"
                            ):
                                col1, col2, col3 = st.columns([2, 2, 1])

                                with col1:
                                    st.markdown(f"**Jugador:** {item['player_name']}")
                                    st.markdown(f"**Deporte:** {item['sport']}")
                                    st.markdown(
                                        f"**Tarjeta:** {item['year']} {item['manufacturer']}"
                                    )
                                    st.markdown(f"**Cantidad:** {item['quantity']}")

                                with col2:
                                    st.metric(
                                        "Precio Compra",
                                        f"${item['purchase_price']:.2f}",
                                    )
                                    st.metric(
                                        "Valor Actual",
                                        f"${item['current_value']:.2f}",
                                        f"{item['gain_loss_pct']:+.1f}%",
                                    )
                                    st.markdown(
                                        f"**Valor Total:** ${item['total_value']:.2f}"
                                    )
                                    st.markdown(
                                        f"**Comprado:** {item['purchase_date'].strftime('%Y-%m-%d')}"
                                    )

                                with col3:
                                    # Update value
                                    new_value = st.number_input(
                                        "Actualizar valor",
                                        min_value=0.0,
                                        value=float(item["current_value"]),
                                        step=10.0,
                                        key=f"update_{item['id']}",
                                    )

                                    if st.button(
                                        "💾 Actualizar", key=f"btn_update_{item['id']}"
                                    ):
                                        CardRepository.update_portfolio_value(
                                            db=db,
                                            user_id=user_id,
                                            portfolio_item_id=item["id"],
                                            new_value=new_value,
                                        )
                                        st.success("Actualizado")
                                        st.rerun()

                                    if st.button(
                                        "Vender", key=f"btn_sell_{item['id']}"
                                    ):
                                        CardRepository.remove_from_portfolio(
                                            db=db,
                                            user_id=user_id,
                                            portfolio_item_id=item["id"],
                                            sell_price=item["current_value"],
                                        )
                                        st.success("✅ Vendido")
                                        st.rerun()

                                if item["notes"]:
                                    st.markdown(f"**Notas:** {item['notes']}")

                        # Distribution chart
                        if len(portfolio_items) > 1:
                            st.divider()
                            st.subheader("📊 Distribución del Portfolio")

                            import plotly.express as px

                            df_portfolio = pd.DataFrame(portfolio_items)

                            fig = px.pie(
                                df_portfolio,
                                values="total_value",
                                names="player_name",
                                title="Distribución por Valor",
                                hole=0.4,
                            )

                            st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback

                st.code(traceback.format_exc())

    # ============================================================
    # TAB 4: History
    # ============================================================
    with tab4:
        st.header("📜 Análisis Guardados")

        st.info("💾 Historial de todos los análisis realizados con el sistema")

        # Filtros
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_sport = st.selectbox(
                "Filtrar por deporte",
                options=["Todos", "NBA", "NHL", "MLB", "NFL", "Soccer"],
                key="history_sport",
            )

        with col2:
            filter_signal = st.selectbox(
                "Filtrar por señal",
                options=["Todas", "BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"],
                key="history_signal",
            )

        with col3:
            limit = st.number_input(
                "Número de resultados", min_value=10, max_value=100, value=20, step=10
            )

        if st.button("🔄 Cargar Análisis", type="primary", use_container_width=True):
            try:
                from src.utils.database import get_db
                from src.utils.repository import CardRepository

                with st.spinner("Cargando análisis..."):
                    with get_db() as db:
                        # Aplicar filtros
                        sport_filter = None if filter_sport == "Todos" else filter_sport
                        signal_filter = (
                            None if filter_signal == "Todas" else filter_signal
                        )

                        analyses = CardRepository.get_all_analyses(
                            db, limit=limit, sport=sport_filter, signal=signal_filter
                        )

                        if not analyses:
                            st.warning("No se encontraron análisis con esos filtros")
                        else:
                            st.success(f"Encontrados {len(analyses)} análisis")

                            # Mostrar en tarjetas
                            for i, analysis in enumerate(analyses):
                                with st.expander(
                                    f"#{i + 1} - {analysis['player_name']} {analysis['year']} "
                                    f"({analysis['sport']}) - {analysis['signal']}"
                                ):
                                    col1, col2 = st.columns([1, 2])

                                    with col1:
                                        # Métricas
                                        st.metric(
                                            "Señal",
                                            analysis["signal"],
                                            help="Recomendación del agente",
                                        )
                                        st.metric(
                                            "Confianza",
                                            f"{analysis['confidence']:.0%}",
                                            help="Nivel de confianza",
                                        )
                                        if analysis["current_price"]:
                                            st.metric(
                                                "Precio",
                                                f"${analysis['current_price']:.2f}",
                                                help="Precio de entrada",
                                            )

                                    with col2:
                                        # Detalles
                                        st.markdown(
                                            f"**Jugador:** {analysis['player_name']}"
                                        )
                                        st.markdown(
                                            f"**Tarjeta:** {analysis['year']} {analysis['manufacturer']}"
                                        )
                                        st.markdown(
                                            f"**Tipo:** {analysis['analysis_type']}"
                                        )
                                        st.markdown(
                                            f"**Fecha:** {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}"
                                        )

                                        if analysis["reasoning"]:
                                            st.markdown("**Razonamiento:**")
                                            st.text_area(
                                                "reasoning",
                                                analysis["reasoning"],
                                                height=100,
                                                key=f"reasoning_{analysis['id']}",
                                                label_visibility="collapsed",
                                            )

                        # Estadísticas
                        st.divider()
                        st.subheader("Estadísticas del Sistema")

                        stats = CardRepository.get_statistics(db)

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("Jugadores", stats["total_players"])
                        with col2:
                            st.metric("Tarjetas", stats["total_cards"])
                        with col3:
                            st.metric("Análisis Totales", stats["total_analyses"])
                        with col4:
                            st.metric("Esta semana", stats["recent_analyses"])

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback

                st.code(traceback.format_exc())

    # ============================================================
    # TAB 5: Dashboard
    # ============================================================
    # ============================================================
    # TAB 5: Dashboard
    # ============================================================
    with tab5:
        st.header("📊 Dashboard de Rendimiento Avanzado")

        try:
            from src.utils.database import get_db
            from src.utils.repository import CardRepository
            import plotly.express as px

            with get_db() as db:
                # 1. KPIs del Portfolio Personal
                p_stats = CardRepository.get_portfolio_stats(db, user_id)

                st.subheader("🏦 Mi Inversión")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Inversión Total", f"${p_stats['total_invested']:,.2f}")
                with col2:
                    st.metric("Valor de Mercado", f"${p_stats['current_value']:,.2f}")
                with col3:
                    color = "normal" if p_stats["total_gain_loss"] >= 0 else "inverse"
                    st.metric(
                        "P&L Total",
                        f"${p_stats['total_gain_loss']:+,.2f}",
                        delta_color=color,
                    )
                with col4:
                    st.metric("ROI Portfolio", f"{p_stats['total_gain_loss_pct']:.1f}%")

                st.divider()

                # 2. Visualizaciones Avanzadas
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader("🏀 Distribución y ROI por Deporte")
                    dist_data = p_stats["sport_distribution"]
                    if dist_data:
                        df_dist = pd.DataFrame(
                            [
                                {"Deporte": k, "Valor": v["current"], "ROI": v["roi"]}
                                for k, v in dist_data.items()
                            ]
                        )
                        fig_dist = px.bar(
                            df_dist,
                            x="Deporte",
                            y="Valor",
                            color="ROI",
                            color_continuous_scale="RdYlGn",
                            text_auto=".2s",
                            title="Valor Actual y ROI %",
                        )
                        st.plotly_chart(fig_dist, use_container_width=True)
                    else:
                        st.info("Añade tarjetas a tu portfolio para ver este análisis")

                with col_right:
                    st.subheader("🏆 Mejores Rendimientos")
                    if p_stats["items_performance"]:
                        df_perf = pd.DataFrame(
                            p_stats["items_performance"][:5]
                        )  # Top 5
                        fig_perf = px.bar(
                            df_perf,
                            x="gain_pct",
                            y="name",
                            orientation="h",
                            color="gain_pct",
                            color_continuous_scale="Viridis",
                            labels={"gain_pct": "ROI %", "name": "Tarjeta"},
                            title="Top 5 Cartas por Crecimiento",
                        )
                        fig_perf.update_layout(
                            yaxis={"categoryorder": "total ascending"}
                        )
                        st.plotly_chart(fig_perf, use_container_width=True)
                    else:
                        st.info("Sin datos de rendimiento disponibles")

                st.divider()

                # 3. Estadísticas de Mercado (Integradas)
                st.subheader("🌐 Actividad Global del Mercado")
                m_stats = CardRepository.get_statistics(db)

                col_m1, col_m2 = st.columns(2)

                with col_m1:
                    st.markdown("**Tendencia de Análisis**")
                    df_trend = pd.DataFrame(m_stats["daily_trend"])
                    fig_trend = px.line(df_trend, x="date", y="count", markers=True)
                    fig_trend.update_layout(
                        height=300, margin=dict(l=0, r=0, t=20, b=0)
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

                with col_m2:
                    st.markdown("**Oportunidades IA Detectadas**")
                    sig_dist = m_stats["signals_distribution"]
                    if sig_dist:
                        df_sig = pd.DataFrame(
                            [{"Señal": k, "Cantidad": v} for k, v in sig_dist.items()]
                        )
                        fig_sig = px.pie(
                            df_sig, names="Señal", values="Cantidad", hole=0.5
                        )
                        fig_sig.update_layout(
                            height=300, margin=dict(l=0, r=0, t=20, b=0)
                        )
                        st.plotly_chart(fig_sig, use_container_width=True)

                # Notas del Agente
                if p_stats["best_performer"]:
                    st.toast(
                        f"🌟 Tu mejor inversión: {p_stats['best_performer']['name']}"
                    )

        except Exception as e:
            st.error(f"❌ Error al cargar dashboard: {str(e)}")
            import traceback

            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
