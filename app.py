import os
from functools import lru_cache
from time import time

import requests
import streamlit as st

from src.utils.config import settings


# ===============================
# Consulta info de jugador (multideporte)
# ===============================
@st.cache_data(ttl=3600, show_spinner=False)
def get_player_info_multisource(player_name, sport="Soccer"):
    """
    Busca información de un jugador en TheSportsDB, Sportsdata.io y SportMonks.
    Retorna el primer resultado encontrado (dict) o None.
    """
    # 1. TheSportsDB (gratuita, sin API key para info básica)
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/1/searchplayers.php?p={player_name}"
        resp = requests.get(url, timeout=10)
        if resp.ok and resp.json().get("player"):
            player = resp.json()["player"][0]
            return {
                "fuente": "TheSportsDB",
                "nombre": player.get("strPlayer"),
                "deporte": player.get("strSport"),
                "equipo": player.get("strTeam"),
                "activo": player.get("strStatus", ""),
                "pais": player.get("strNationality"),
                "foto": player.get("strCutout") or player.get("strThumb"),
                "descripcion": player.get("strDescriptionEN", "")[:300],
            }
    except Exception:
        pass

    # 2. Sportsdata.io (requiere API key, ejemplo con requests)
    # Puedes obtener una API key gratuita limitada en https://sportsdata.io/developers
    api_key = os.getenv("SPORTSDATAIO_API_KEY")
    if api_key:
        try:
            # Ejemplo para NBA, cambiar endpoint según deporte
            url = f"https://api.sportsdata.io/v3/nba/scores/json/Players?key={api_key}"
            resp = requests.get(url, timeout=10)
            if resp.ok:
                for player in resp.json():
                    if (
                        player_name.lower()
                        in player.get("FirstName", "").lower()
                        + " "
                        + player.get("LastName", "").lower()
                    ):
                        return {
                            "fuente": "Sportsdata.io",
                            "nombre": f"{player.get('FirstName')} {player.get('LastName')}",
                            "deporte": "Basketball",
                            "equipo": player.get("Team"),
                            "activo": "Active" if player.get("Status") == "Active" else "Retirado",
                            "pais": player.get("Nationality"),
                            "foto": player.get("PhotoUrl"),
                            "descripcion": player.get("Experience", ""),
                        }
        except Exception:
            pass

    # 3. SportMonks (requiere API key, ejemplo con requests)
    # Puedes obtener una API key gratuita limitada en https://www.sportmonks.com/
    api_key2 = os.getenv("SPORTMONKS_API_KEY")
    if api_key2:
        try:
            # Ejemplo para fútbol
            url = f"https://soccer.sportmonks.com/api/v2.0/players/search/{player_name}?api_token={api_key2}"
            resp = requests.get(url, timeout=10)
            if resp.ok and resp.json().get("data"):
                player = resp.json()["data"][0]
                return {
                    "fuente": "SportMonks",
                    "nombre": player.get("display_name"),
                    "deporte": "Soccer",
                    "equipo": player.get("team_id"),
                    "activo": "Activo" if player.get("active") else "Retirado",
                    "pais": player.get("nationality"),
                    "foto": player.get("image_path"),
                    "descripcion": player.get("common_name", ""),
                }
        except Exception:
            pass

    return None


import json

# Utilidades para respaldo local de ventas
LOCAL_SALES_FILE = "data/ebay_sales_backup.json"


def save_sales_backup(player, listings):
    """Guarda ventas recientes en un archivo local por jugador."""
    if not listings:
        return
    os.makedirs(os.path.dirname(LOCAL_SALES_FILE), exist_ok=True)
    try:
        if os.path.exists(LOCAL_SALES_FILE):
            with open(LOCAL_SALES_FILE, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        # Guardar solo los 20 más recientes por jugador
        data[player] = [l.__dict__ for l in listings][:20]
        with open(LOCAL_SALES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar respaldo local: {e}")


def load_sales_backup(player):
    """Carga ventas locales guardadas para un jugador."""
    if not os.path.exists(LOCAL_SALES_FILE):
        return []
    try:
        with open(LOCAL_SALES_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get(player, [])
    except Exception as e:
        logger.warning(f"No se pudo cargar respaldo local: {e}")
        return []


"""
Aplicación web para análisis de tarjetas deportivas
Interfaz interactiva con Streamlit
"""

import asyncio
import time
import unicodedata
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_authenticator as stauth

from src.agents.market_research_agent import MarketResearchAgent
from src.agents.price_analyzer_agent import PriceAnalyzerAgent
from src.agents.supervisor_agent import SupervisorAgent
from src.models.card import Card, CardCondition, Player, PricePoint, Sport
from src.models.db_models import PortfolioItemDB, UserDB, WatchlistDB
from src.tools.card_vision_tool import CardVisionTool
from src.tools.ebay_tool import EBayRateLimitError, EBaySearchParams, EBayTool
from src.tools.tcgplayer_tool import TCGPlayerSearchParams, TCGPlayerTool
from src.utils.auth_utils import hash_password
from src.utils.database import get_db, init_db

# Setup logging and configuration
from src.utils.logging_config import get_logger, setup_logging
from src.utils.realtime_sync import RealtimeSync
from src.utils.repository import CardRepository
from src.utils.ui_components import (
    glass_card,
    listing_card_html,
    live_ticker_html,
    metric_grid,
)

# Initialize logging
setup_logging()

logger = get_logger(__name__)


# Cargar CSS personalizado
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


try:
    local_css("src/static/styles.css")
except Exception:
    pass


# Configuración de la página
st.set_page_config(
    page_title="Sports Card AI | Terminal Premium",
    page_icon="⚡",
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
    return SupervisorAgent()


@st.cache_resource
def get_ebay_tool():
    """Obtiene instancia de herramienta eBay (cacheada)"""
    return EBayTool()


@st.cache_resource
def get_market_agent():
    """Obtiene instancia del agente de mercado (cacheada)"""

    return MarketResearchAgent()


@st.cache_resource
def get_vision_tool():
    """Obtiene instancia de herramienta Vision (cacheada)"""

    return CardVisionTool()


def apply_custom_theme(fig, title=None):
    """Aplica el tema premium de la aplicación a un gráfico de Plotly"""
    fig.update_layout(
        title=title if title else (fig.layout.title.text if fig.layout.title else None),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white", "family": "Inter, sans-serif"},
        xaxis={"gridcolor": "rgba(255,255,255,0.05)", "zerolinecolor": "rgba(255,255,255,0.1)"},
        yaxis={"gridcolor": "rgba(255,255,255,0.05)", "zerolinecolor": "rgba(255,255,255,0.1)"},
    )
    return fig


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
            line={"color": "#00f2ff", "width": 2},
            marker={"size": 8},
        )
    )

    # Línea de promedio
    if not df.empty:
        avg_price = df["Precio"].mean()
        fig.add_hline(
            y=avg_price,
            line_dash="dash",
            line_color="rgba(255, 255, 255, 0.5)",
            annotation_text=f"Avg: ${avg_price:.2f}",
            annotation_position="right",
        )

    apply_custom_theme(fig, title)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Precio (USD)",
        hovermode="x unified",
        height=400,
    )

    return fig


async def _run_async_with_timeout(coro, timeout: int = 30):
    """
    Ejecuta una corrutina con timeout y mejor manejo de errores

    Args:
        coro: Corrutina a ejecutar
        timeout: Timeout en segundos (default: 30)

    Returns:
        Resultado de la corrutina o None si hay error
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        logger.error(f"Async operation timed out after {timeout}s")
        raise
    except Exception as e:
        logger.error(f"Async operation failed: {str(e)}", exc_info=True)
        raise


def _safe_async_run(coro, timeout: int = 30, error_msg: str = "Error en operación"):
    """
    Wrapper seguro para asyncio.run() con timeout y manejo de errores

    Args:
        coro: Corrutina a ejecutar
        timeout: Timeout en segundos
        error_msg: Mensaje personalizado en caso de error

    Returns:
        Resultado de la corrutina o None si hay error
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
    except TimeoutError:
        logger.error(f"{error_msg}: timeout después de {timeout}s")
        return None
    except Exception as e:
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        return None
    finally:
        loop.close()


def _cleanup_session_state(keys_to_clean: list = None):
    """
    Limpia keys específicas de session_state

    Args:
        keys_to_clean: Lista de keys a limpiar. Si es None, limpia todos los vision/upload keys
    """
    if keys_to_clean is None:
        keys_to_clean = [
            "vision_data",
            "port_vision_data",
            "vision_upload_key",
            "vision_port",
        ]

    for key in keys_to_clean:
        if key in st.session_state:
            del st.session_state[key]
            logger.debug(f"Cleaned session_state key: {key}")


def _show_registration_form(form_key: str = "register_form", expanded: bool = False):
    """
    Muestra un formulario de registro reutilizable

    Args:
        form_key: Clave única para el formulario (evita conflictos en Streamlit)
        expanded: Si el expander debe estar expandido por defecto

    Returns:
        bool: True si el registro fue exitoso, False en caso contrario
    """

    with st.expander("📝 Registro", expanded=expanded):
        with st.form(form_key):
            new_user = st.text_input("Usuario", key=f"{form_key}_user")
            new_email = st.text_input("Email", key=f"{form_key}_email")
            new_pass = st.text_input("Password", type="password", key=f"{form_key}_pass")
            new_name = st.text_input("Nombre Completo", key=f"{form_key}_name")
            reg_btn = st.form_submit_button("Registrarse")

            if reg_btn:
                # Validación básica
                if not all([new_user, new_email, new_pass, new_name]):
                    st.error("❌ Por favor completa todos los campos")
                    return False

                try:
                    with get_db() as db:
                        # Check if username or email already exists
                        existing_user = CardRepository.get_user_by_username(db, new_user)
                        existing_email = CardRepository.get_user_by_email(db, new_email)

                        if existing_user:
                            st.error(f"❌ El usuario '{new_user}' ya existe. Por favor elige otro.")
                            return False
                        elif existing_email:
                            st.error(
                                f"❌ El email '{new_email}' ya está registrado. Por favor usa otro."
                            )
                            return False

                        # Create the new user
                        new_user_db = CardRepository.create_user(
                            db,
                            new_user,
                            new_email,
                            hash_password(new_pass),
                            new_name,
                        )
                        db.commit()

                        # Migrate orphaned items to the first user
                        orphaned_portfolio = (
                            db.query(PortfolioItemDB)
                            .filter(PortfolioItemDB.user_id.is_(None))
                            .all()
                        )
                        for item in orphaned_portfolio:
                            item.user_id = new_user_db.id

                        orphaned_watchlist = (
                            db.query(WatchlistDB).filter(WatchlistDB.user_id.is_(None)).all()
                        )
                        for item in orphaned_watchlist:
                            item.user_id = new_user_db.id

                        db.commit()

                        st.success("¡Usuario creado correctamente! Por favor inicia sesión.")
                        logger.info(f"New user registered: {new_user}")
                        st.rerun()
                        return True

                except Exception as e:
                    st.error(f"❌ Error al registrar: {str(e)}")
                    logger.error(f"Registration error for user {new_user}", exc_info=True)
                    return False

    return False


def main():
    """Función principal de la app"""

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
                u.username.lower(): {
                    "name": u.full_name,
                    "password": u.hashed_password,
                    "email": u.email,
                }
                for u in users
            }
        }

    env_str = os.getenv("RAILWAY_ENVIRONMENT_NAME", "local")
    cookie_name = f"sports_card_agent_cookie_{env_str}"

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name,
        "sports_card_agent_key",
        cookie_expiry_days=30,
    )

    # Sidebar Login/Logout
    st.sidebar.title("🔐 Acceso")

    # Manejar Registro si no hay usuarios
    if not users:
        st.info("👋 ¡Bienvenido! Crea tu primer usuario para empezar.")
        _show_registration_form(form_key="register_form_initial", expanded=True)

    # Try to login, handle potential session/cookie errors gracefully
    try:
        if users:
            authenticator.login(location="sidebar")
    except Exception as e:
        # This often happens if a cookie exists for a user not in the current DB
        if "User not authorized" in str(e):
            st.session_state["authentication_status"] = None
            st.session_state["username"] = None
            st.session_state["name"] = None
            if "logout" in st.session_state:
                del st.session_state["logout"]
        else:
            logger.error(f"Authentication error: {e}")
            st.error(f"Error de autenticación: {e}")

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
            _show_registration_form(form_key="register_form_new", expanded=False)
        return

    # Usuario autenticado
    st.sidebar.success(f"Sesión iniciada: {name}")
    authenticator.logout("Logout (Cerrar Sesión)", "sidebar")

    with get_db() as db:
        current_user = CardRepository.get_user_by_username(db, username)

        # Safety check: if user not found in DB but authenticated by stauth (sync issue)
        if current_user is None:
            st.error(f"⚠️ El usuario '{username}' no se encontró en la base de datos local.")

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
                        fix_pass = st.text_input("Nueva Password (temporal)", type="password")
                        if st.form_submit_button("Crear usuario en base de datos"):
                            # Safety validation before fixing
                            existing_user = CardRepository.get_user_by_username(db, username)
                            existing_email = CardRepository.get_user_by_email(db, fix_email)

                            if existing_user:
                                st.error(
                                    f"❌ El usuario '{username}' ya existe en la base de datos."
                                )
                            elif existing_email:
                                st.error(f"❌ El email '{fix_email}' ya está registrado.")
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
    st.markdown('<h1 class="main-header">🏀 Sports Card AI Agent</h1>', unsafe_allow_html=True)
    st.markdown(f"### Análisis inteligente de tarjetas deportivas - Usuario: {username}")

    # Sidebar
    st.sidebar.title("⚙️ Configuración")

    # Selección de deporte
    sport = st.sidebar.selectbox("Deporte", options=["NBA", "NHL", "MLB", "NFL", "Soccer"], index=0)

    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Búsqueda en eBay",
            "Análisis de Tarjeta",
            "My Portfolio",
            "History",
            "Dashboard",
            "� Fuentes de Precios",
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
            min_price = st.number_input("Precio mínimo ($)", min_value=0.0, value=0.0, step=10.0)
        with col3:
            max_price = st.number_input("Precio máximo ($)", min_value=0.0, value=0.0, step=100.0)

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

                        # Ejecutar búsqueda con timeout
                        try:
                            listings = _safe_async_run(tool.search_cards(params), timeout=30)
                        except TimeoutError:
                            st.error(
                                "❌ La búsqueda tardó demasiado. Intenta con términos más específicos."
                            )

                        if not listings:
                            # Diagnóstico rápido: comprobar App ID
                            if not settings.EBAY_APP_ID:
                                st.warning(
                                    "EBAY_APP_ID no está configurado. Añade tus credenciales en el archivo .env o en Streamlit secrets."
                                )
                            else:
                                st.info(
                                    "No se encontraron resultados, intentando variaciones del nombre y fallback local..."
                                )

                                # Generar variantes del nombre (sin acentos, formas cortas)
                                def name_variants(name: str):
                                    variants = [name]
                                    # Sin acentos
                                    nfkd = unicodedata.normalize("NFKD", name)
                                    no_accents = "".join(
                                        [c for c in nfkd if not unicodedata.combining(c)]
                                    )
                                    if no_accents != name:
                                        variants.append(no_accents)
                                    # Primera inicial + apellido
                                    parts = name.split()
                                    if len(parts) >= 2:
                                        variants.append(f"{parts[0][0]}. {parts[-1]}")
                                        variants.append(f"{parts[-1]}")
                                    return list(dict.fromkeys(variants))

                                found = False
                                for var in name_variants(search_query):
                                    try:
                                        params_var = EBaySearchParams(
                                            keywords=var,
                                            max_results=max_results,
                                            sold_items_only=sold_only,
                                            min_price=min_price if min_price > 0 else None,
                                            max_price=max_price if max_price > 0 else None,
                                        )
                                        fallback_listings = _safe_async_run(
                                            tool.search_cards(params_var), timeout=30
                                        )
                                        if fallback_listings:
                                            st.info(f"Mostrando resultados para la variante: {var}")
                                            listings = fallback_listings
                                            found = True
                                            break
                                    except EBayRateLimitError as e:
                                        st.warning(f"⚠️ eBay API Limit detectado: {str(e)}")
                                        found = False
                                        break
                                    except Exception:
                                        continue

                                # Si no se encontraron resultados, intentar respaldo local
                                if not found or not listings:
                                    local_sales = load_sales_backup(search_query)
                                    if local_sales:
                                        st.info(
                                            "Mostrando ventas guardadas localmente para este jugador."
                                        )
                                        listings = [
                                            type("Listing", (), sale) for sale in local_sales
                                        ]
                                        found = True

                                if not found or not listings:
                                    # Intentar TCGPlayer como alternativa
                                    st.info("🔄 eBay no respondió, buscando en TCGPlayer...")
                                    try:
                                        tcg_tool = TCGPlayerTool()
                                        tcg_params = TCGPlayerSearchParams(
                                            keywords=search_query,
                                            max_results=max_results,
                                            min_price=min_price if min_price > 0 else None,
                                            max_price=max_price if max_price > 0 else None,
                                        )
                                        tcg_listings = _safe_async_run(
                                            tcg_tool.search_cards(tcg_params), timeout=30
                                        )
                                        if tcg_listings:
                                            st.success(
                                                f"🎉 Encontrados {len(tcg_listings)} resultados en TCGPlayer!"
                                            )
                                            for i, listing in enumerate(tcg_listings, 1):
                                                html = listing_card_html(
                                                    title=listing.title[:80],
                                                    price=f"${listing.price:.2f}",
                                                    img_url=listing.image_url,
                                                    url=listing.listing_url,
                                                    sold=False,
                                                )
                                                st.markdown(html, unsafe_allow_html=True)
                                            st.info(
                                                "💡 Estos resultados vienen de TCGPlayer (alternativa a eBay)"
                                            )
                                        else:
                                            raise Exception("No TCGPlayer results")
                                    except Exception:
                                        st.warning(
                                            f"No se encontraron resultados para: **{search_query}**."
                                        )
                                        st.info(
                                            "Opciones: prueba quitar filtros, verifica tu `EBAY_APP_ID`, espera unos minutos por cuota, o ejecuta el diagnóstico a continuación."
                                        )

                                    if st.button(
                                        "🔎 Ejecutar diagnóstico eBay (ver respuesta cruda)"
                                    ):
                                        try:
                                            tool_debug = EBayTool()
                                            api_params = {
                                                "OPERATION-NAME": "findCompletedItems"
                                                if sold_only
                                                else "findItemsAdvanced",
                                                "SERVICE-VERSION": "1.13.0",
                                                "SECURITY-APPNAME": tool_debug.app_id,
                                                "RESPONSE-DATA-FORMAT": "JSON",
                                                "GLOBAL-ID": "EBAY-US",
                                                "keywords": search_query,
                                                "paginationInput.entriesPerPage": max_results,
                                                "sortOrder": "BestMatch",
                                            }
                                            if min_price and min_price > 0:
                                                api_params["itemFilter(0).name"] = "MinPrice"
                                                api_params["itemFilter(0).value"] = str(min_price)
                                            if max_price and max_price > 0:
                                                idx = 1 if (min_price and min_price > 0) else 0
                                                api_params[f"itemFilter({idx}).name"] = "MaxPrice"
                                                api_params[f"itemFilter({idx}).value"] = str(
                                                    max_price
                                                )

                                            st.write(
                                                "Enviando request a eBay... (no muestro App ID completo)"
                                            )
                                            try:
                                                resp = requests.get(
                                                    tool_debug.base_url,
                                                    params=api_params,
                                                    timeout=20,
                                                )
                                                st.write(f"Status: {resp.status_code}")
                                                st.write("Headers relevantes:")
                                                st.json(
                                                    {
                                                        k: v
                                                        for k, v in dict(resp.headers).items()
                                                        if k.lower()
                                                        in ["content-type", "cache-control", "date"]
                                                    }
                                                )
                                                text_snippet = resp.text[:2000]
                                                st.code(text_snippet)
                                                if resp.status_code != 200:
                                                    st.warning(
                                                        "La API respondió con un status distinto de 200. Revisa tus credenciales o la cuota."
                                                    )
                                                else:
                                                    st.success(
                                                        "Request exitoso (revisa la respuesta cruda mostrada)."
                                                    )
                                            except Exception as e:
                                                st.error(f"Error realizando request a eBay: {e}")
                                        except Exception as e:
                                            st.error(f"Error preparando diagnóstico: {e}")
                        else:
                            st.success(f"Encontrados {len(listings)} resultados")

                            # Mostrar resultados
                            for _i, listing in enumerate(listings, 1):
                                html = listing_card_html(
                                    title=listing.title[:80],
                                    price=f"${listing.price:.2f} {listing.currency}",
                                    img_url=listing.image_url,
                                    url=listing.listing_url,
                                    sold=listing.sold,
                                )
                                st.markdown(html, unsafe_allow_html=True)

                    except EBayRateLimitError as e:
                        st.warning(f"⚠️ **eBay API Limit:** {str(e)}. Inténtalo de nuevo más tarde.")
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

                        try:
                            card_data = asyncio.run(vision_tool.identify_card(image_bytes))
                        except TimeoutError:
                            st.error(
                                "❌ La identificación tardó demasiado. Intenta con una imagen más clara."
                            )
                            card_data = None

                        if card_data and card_data.get("success"):
                            st.success("✅ Tarjeta identificada correctamente!")
                            # Guardar en session_state para pre-llenar el formulario
                            st.session_state["vision_data"] = card_data
                            # Limpiar archivo después del uso
                            st.session_state["vision_upload_key"] = (
                                st.session_state.get("vision_upload_key", 0) + 1
                            )
                            st.rerun()
                        elif card_data:
                            st.error(f"❌ Error: {card_data.get('error', 'Error desconocido')}")
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
                        logger.error("Vision analysis error", exc_info=True)

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
                variant = st.text_input("Variante", value=v_data.get("variant", "Rookie Card"))
                grade = st.number_input(
                    "Grado (si está graduada)",
                    min_value=1.0,
                    max_value=10.0,
                    value=float(v_data.get("grade", 9.5)) if v_data.get("grade") else 9.5,
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

                        avg_price = sum(p.price for p in prices) / len(prices)
                        diff = recommendation.current_price - avg_price

                        st.markdown(
                            metric_grid(
                                [
                                    {
                                        "label": "Señal",
                                        "value": recommendation.signal.value.upper(),
                                    },
                                    {
                                        "label": "Confianza",
                                        "value": f"{recommendation.confidence:.0%}",
                                    },
                                    {
                                        "label": "Precio Actual",
                                        "value": f"${recommendation.current_price:,.2f}",
                                    },
                                    {
                                        "label": "vs. Promedio",
                                        "value": f"${diff:+,.2f} ({(diff / avg_price) * 100:+.1f}%)",
                                    },
                                ]
                            ),
                            unsafe_allow_html=True,
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
                        try:
                            result = asyncio.run(
                                supervisor.analyze_investment_opportunity(
                                    player_name=player_name,
                                    year=year,
                                    manufacturer=manufacturer,
                                    sport=sport,
                                )
                            )
                        except TimeoutError:
                            st.error(
                                "❌ El análisis tardó demasiado. Intenta con menos players o esperando unos minutos."
                            )
                            result = {"error": "Timeout en análisis multi-agente", "strategy": None}
                        except Exception as e:
                            st.error(f"❌ Error inesperado en análisis: {str(e)}")
                            logger.error("Supervisor analysis error", exc_info=True)
                            result = {"error": str(e), "strategy": None}

                        st.success("Análisis avanzado multi-agente completado")

                        # Verificar si hay error en el resultado
                        if result.get("error") or result.get("strategy") is None:
                            st.error(
                                f"⚠️ Error en el análisis: {result.get('error', 'Error desconocido')}"
                            )
                            st.info(
                                "Esto puede ser debido a límites de API de eBay. Inténtalo de nuevo más tarde."
                            )
                        else:
                            # Resultados Multi-Agente
                            rec = result.get("recommendation", {})
                            detailed = result.get("detailed_analysis", {})

                            st.markdown(
                                metric_grid(
                                    [
                                        {"label": "Señal", "value": rec.get("signal", "N/A")},
                                        {
                                            "label": "Confianza",
                                            "value": f"{rec.get('confidence', 0):.0%}"
                                            if rec.get("confidence")
                                            else "N/A",
                                        },
                                        {
                                            "label": "Riesgo/Recompensa",
                                            "value": rec.get("risk_reward", {}).get("ratio", "N/A"),
                                        },
                                    ]
                                ),
                                unsafe_allow_html=True,
                            )

                            st.divider()
                            st.markdown(
                                glass_card(
                                    rec.get("reasoning", "No hay justificación disponible"),
                                    "🎯 Justificación del Agente",
                                ),
                                unsafe_allow_html=True,
                            )

                            # Mostrar detalles por agente
                            tabs = st.tabs(["📉 Mercado", "🏀 Jugador", "📈 Estrategia"])

                            with tabs[0]:
                                market = detailed["market"]["market_analysis"]
                            st.subheader("Análisis de Mercado (eBay)")
                            st.markdown(
                                metric_grid(
                                    [
                                        {
                                            "label": "Vendidos",
                                            "value": str(market["sold_items"]["count"]),
                                        },
                                        {
                                            "label": "Promedio",
                                            "value": f"${market['sold_items']['average_price']:,.2f}",
                                        },
                                    ]
                                ),
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                glass_card(market["market_insight"], "💡 Insight del Mercado"),
                                unsafe_allow_html=True,
                            )

                            with tabs[1]:
                                if "player" in detailed:
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

                                    if (
                                        "analysis" in player_ana
                                        and "future_outlook" in player_ana["analysis"]
                                    ):
                                        st.markdown(
                                            glass_card(
                                                player_ana["analysis"]["future_outlook"],
                                                "📊 Outlook",
                                            ),
                                            unsafe_allow_html=True,
                                        )

                                    st.markdown(
                                        metric_grid(
                                            [
                                                {
                                                    "label": "Score General",
                                                    "value": f"{player_ana['analysis']['performance_score']['overall_score']}/100",
                                                },
                                                {
                                                    "label": "Sentimiento",
                                                    "value": player_ana.get("sentiment", {}).get(
                                                        "sentiment", "N/A"
                                                    ),
                                                },
                                            ]
                                        ),
                                        unsafe_allow_html=True,
                                    )

                                    # Mostrar estadísticas reales en una grilla si están disponibles
                                    if stats_info.get("success"):
                                        st.write("**Estadísticas Reales:**")
                                        stats_metrics = []
                                        exclude = [
                                            "success",
                                            "simulated",
                                            "player_name",
                                            "provider",
                                            "from_cache",
                                            "note",
                                            "season",
                                        ]
                                        for k, v in stats_info.items():
                                            if k not in exclude and isinstance(v, (int, float)):
                                                label = k.replace("_", " ").title()
                                                stats_metrics.append(
                                                    {"label": label, "value": str(v)}
                                                )

                                        if stats_metrics:
                                            st.markdown(
                                                metric_grid(stats_metrics),
                                                unsafe_allow_html=True,
                                            )
                                else:
                                    st.info("Datos del jugador no disponibles")

                                with tabs[2]:
                                    st.subheader("Estrategia Detallada")
                                    st.markdown(
                                        glass_card(
                                            result["reasoning"], "📈 Razonamiento Estratégico"
                                        ),
                                        unsafe_allow_html=True,
                                    )

                                    st.write("**Acciones Recomendadas:**")
                                    for item in result["action_items"]:
                                        st.markdown(f"• {item}")

                                    st.divider()
                                    st.write("**Precios Objetivo:**")
                                    targets = rec["price_targets"]
                                    st.markdown(
                                        metric_grid(
                                            [
                                                {
                                                    "label": "Entrada",
                                                    "value": f"${targets['entry_price']:,.2f}",
                                                },
                                                {
                                                    "label": "Venta",
                                                    "value": f"${targets['target_sell_price']:,.2f}",
                                                },
                                                {
                                                    "label": "Stop Loss",
                                                    "value": f"${targets['stop_loss']:,.2f}",
                                                },
                                            ]
                                        ),
                                        unsafe_allow_html=True,
                                    )

                except Exception as e:
                    st.error(f"Error en el análisis: {str(e)}")
                    import traceback

                    st.code(traceback.format_exc())

            # Limpiar vision data después del análisis
            _cleanup_session_state(["vision_data"])

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

                            try:
                                card_data = asyncio.run(vision_tool.identify_card(image_bytes))
                            except TimeoutError:
                                st.error("❌ La identificación tardó demasiado. Intenta de nuevo.")
                                card_data = None

                            if card_data and card_data.get("success"):
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
                        value=int(vp_data.get("year", 2003)) if vp_data.get("year") else 2003,
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
                    is_auto = st.checkbox("Autógrafo", value=vp_data.get("is_auto", False))
                with col_r3:
                    is_numbered = st.checkbox("Numerada", value=vp_data.get("is_numbered", False))

                if is_numbered:
                    col_n1, col_n2 = st.columns(2)
                    with col_n1:
                        seq_num = st.number_input("Número (Ej: 10)", min_value=1, value=1)
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

                notes = st.text_area("Notas", placeholder="Ej: PSA 9, comprada en eBay", height=80)

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
                    with st.spinner("Añadiendo al portfolio..."):
                        with get_db() as db:
                            # Get or create player
                            player_id = (
                                f"{player_name_port.lower().replace(' ', '-')}-{sport_port.lower()}"
                            )
                            player = CardRepository.get_or_create_player(
                                db=db,
                                player_id=player_id,
                                name=player_name_port,
                                sport=sport_port,
                            )
                            logger.debug(f"Player created - {player.name}")

                            # Get or create card
                            card_id = f"{player_id}-{year_port}-{manufacturer_port.lower()}"
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
                            logger.debug(f"Card created - {card.card_id}")

                            # Add to portfolio
                            portfolio_item = CardRepository.add_to_portfolio(
                                db=db,
                                card=card,
                                user_id=user_id,
                                purchase_price=purchase_price,
                                purchase_date=datetime.combine(purchase_date, datetime.min.time()),
                                quantity=quantity,
                                notes=notes,
                                acquisition_source=acquisition_source,
                            )
                            logger.debug(f"Portfolio item created - ID {portfolio_item.id}")

                            # Commit explicitly
                            db.commit()
                            logger.debug("Transaction committed")

                            st.success(f"{player_name_port} añadido al portfolio!")
                            st.cache_data.clear()
                            time.sleep(0.5)
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al añadir: {str(e)}")
                    logger.error("Error adding to portfolio", exc_info=True)

                # Limpiar vision data después del uso
                _cleanup_session_state(["port_vision_data"])

        with col_portfolio:
            col_title, col_refresh = st.columns([3, 1])
            with col_title:
                st.subheader("Tu Portfolio")
            with col_refresh:
                if st.button("🔄 Actualizar", key="refresh_portfolio"):
                    st.rerun()

                if st.button(
                    "🤖 Sync Real-Time",
                    key="sync_portfolio_realtime",
                    help="Actualiza los precios en tiempo real desde el mercado (eBay)",
                ):
                    with st.spinner("🤖 Sincronizando precios en tiempo real..."):
                        try:
                            sync_tool = RealtimeSync()
                            try:
                                results = asyncio.run(sync_tool.sync_portfolio(user_id))
                            except TimeoutError:
                                st.error(
                                    "❌ La sincronización tardó demasiado. Intenta de nuevo más tarde."
                                )
                                logger.warning("Portfolio sync timeout")
                                return

                            if results.get("updated", 0) > 0:
                                st.success(f"✅ Actualizados {results['updated']} precios")
                                for detail in results.get("details", []):
                                    if "✅" in detail:
                                        st.toast(detail)
                            else:
                                st.info("No se encontraron cambios en el mercado")

                            time.sleep(1)
                            st.rerun()
                        except TimeoutError:
                            st.error("❌ Timeout en sincronización. Intenta de nuevo.")
                            logger.warning("Portfolio sync timeout")
                        except Exception as e:
                            st.error(f"❌ Error en sync: {str(e)}")
                            logger.error("Portfolio sync error", exc_info=True)

            try:
                with get_db() as db:
                    # Get portfolio stats
                    stats = CardRepository.get_portfolio_stats(db, user_id)

                    # Display stats
                    st.markdown(
                        metric_grid(
                            [
                                {
                                    "label": "Tarjetas",
                                    "value": str(stats["total_items"]),
                                },
                                {
                                    "label": "Invertido",
                                    "value": f"${stats['total_invested']:,.2f}",
                                },
                                {
                                    "label": "Valor Actual",
                                    "value": f"${stats['current_value']:,.2f}",
                                },
                                {
                                    "label": "Ganancia/Pérdida",
                                    "value": f"${stats['total_gain_loss']:,.2f} ({stats['total_gain_loss_pct']:+.1f}%)",
                                },
                            ]
                        ),
                        unsafe_allow_html=True,
                    )

                    refresh_key = st.empty()
                    with refresh_key:
                        st.write(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

                    # Get portfolio items
                    portfolio_items = CardRepository.get_portfolio(db, user_id, active_only=True)

                    if not portfolio_items:
                        st.info("📭 Tu portfolio está vacío. Añade tu primera tarjeta arriba.")
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
                                    st.markdown(f"**Valor Total:** ${item['total_value']:.2f}")
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

                                    if st.button("💾 Actualizar", key=f"btn_update_{item['id']}"):
                                        CardRepository.update_portfolio_value(
                                            db=db,
                                            user_id=user_id,
                                            portfolio_item_id=item["id"],
                                            new_value=new_value,
                                        )
                                        st.success("Actualizado")
                                        st.rerun()

                                    if st.button("Vender", key=f"btn_sell_{item['id']}"):
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
                with st.spinner("Cargando análisis..."):
                    with get_db() as db:
                        # Aplicar filtros
                        sport_filter = None if filter_sport == "Todos" else filter_sport
                        signal_filter = None if filter_signal == "Todas" else filter_signal

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
                                        st.markdown(f"**Jugador:** {analysis['player_name']}")
                                        st.markdown(
                                            f"**Tarjeta:** {analysis['year']} {analysis['manufacturer']}"
                                        )
                                        st.markdown(f"**Tipo:** {analysis['analysis_type']}")
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
                        apply_custom_theme(fig_dist)
                        st.plotly_chart(fig_dist, use_container_width=True)
                    else:
                        st.info("Añade tarjetas a tu portfolio para ver este análisis")

                with col_right:
                    st.subheader("🏆 Mejores Rendimientos")
                    if p_stats["items_performance"]:
                        df_perf = pd.DataFrame(p_stats["items_performance"][:5])  # Top 5
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
                        apply_custom_theme(fig_perf)
                        fig_perf.update_layout(yaxis={"categoryorder": "total ascending"})
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
                    fig_trend.update_layout(height=300, margin={"l": 0, "r": 0, "t": 20, "b": 0})
                    st.plotly_chart(fig_trend, use_container_width=True)

                with col_m2:
                    st.markdown("**Oportunidades IA Detectadas**")
                    sig_dist = m_stats["signals_distribution"]
                    if sig_dist:
                        df_sig = pd.DataFrame(
                            [{"Señal": k, "Cantidad": v} for k, v in sig_dist.items()]
                        )
                        fig_sig = px.pie(df_sig, names="Señal", values="Cantidad", hole=0.5)
                        fig_sig.update_layout(height=300, margin={"l": 0, "r": 0, "t": 20, "b": 0})
                st.plotly_chart(fig_sig, use_container_width=True)

                # 4. Live Market Ticker
                st.divider()
                st.subheader("⚡ Live Market Ticker")
                recent_prices = CardRepository.get_latest_price_points(db, limit=5)

                if recent_prices:
                    for pp, card, player in recent_prices:
                        html = live_ticker_html(
                            player=player.name,
                            card=f"{card.year} {card.manufacturer}",
                            price=f"${pp.price:.2f}",
                            time_str=pp.timestamp.strftime("%H:%M:%S"),
                        )
                        st.markdown(html, unsafe_allow_html=True)
                else:
                    st.info("No hay actividad de precios reciente")

                # Notas del Agente
                if p_stats["best_performer"]:
                    st.toast(f"🌟 Tu mejor inversión: {p_stats['best_performer']['name']}")

        except Exception as e:
            st.error(f"❌ Error al cargar dashboard: {str(e)}")
            import traceback

            st.code(traceback.format_exc())

    # ============================================================
    # ============================================================
    # TAB 6: Fuentes de Precios Históricos
    # ============================================================
    with tab6:
        st.header("📈 Fuentes de Precios Históricos")

        st.info(
            "💡 Obtén datos históricos de precios de tarjetas graded desde múltiples fuentes confiables."
        )

        # Tabs con diferentes fuentes
        source_tab1, source_tab2, source_tab3 = st.tabs(
            ["🔍 eBay (Recomendado)", "ℹ️ Fuentes Disponibles", "📊 Análisis de Precios"]
        )

        with source_tab1:
            st.subheader("Buscar Precios en eBay")
            st.markdown(
                """
                **eBay es la fuente más confiable y actualizada** para precios de tarjetas deportivas graded y no graded.
                
                ✅ **Ventajas:**
                - Datos en tiempo real
                - Transparencia de precios
                - Información de ventas completadas
                - Cobertura global
                """
            )

            col1, col2 = st.columns(2)
            with col1:
                player = st.text_input(
                    "Nombre del jugador",
                    placeholder="Ej: LeBron James, Michael Jordan",
                    key="price_history_player",
                )
                # Mostrar info en tiempo real del jugador si existe
                if player:
                    player_info = get_player_info_multisource(player)
                    if player_info:
                        st.markdown(f"### ℹ️ Información en tiempo real de {player_info['nombre']}")
                        cols = st.columns([1, 3])
                        with cols[0]:
                            if player_info.get("foto"):
                                st.image(player_info["foto"], width=120)
                        with cols[1]:
                            st.write(f"**Deporte:** {player_info.get('deporte', '')}")
                            st.write(f"**Equipo:** {player_info.get('equipo', '')}")
                            st.write(f"**País:** {player_info.get('pais', '')}")
                            st.write(f"**Estado:** {player_info.get('activo', '')}")
                            st.caption(f"Fuente: {player_info['fuente']}")
                            if player_info.get("descripcion"):
                                st.write(player_info["descripcion"])
                    else:
                        st.info("No se encontró información en tiempo real para este jugador.")
            with col2:
                card_year = st.number_input(
                    "Año de tarjeta (opcional)",
                    min_value=1900,
                    max_value=2025,
                    value=2020,
                    key="price_history_year",
                )

            col1, col2, col3 = st.columns(3)
            with col1:
                grade = st.selectbox(
                    "Grade (si aplica)",
                    ["Todas", "PSA 10", "PSA 9", "PSA 8", "BGS 9.5", "SGC 10"],
                    key="price_history_grade",
                )
            with col2:
                min_price = st.number_input(
                    "Precio mínimo ($)", min_value=0.0, value=0.0, key="price_history_min"
                )
            with col3:
                max_price = st.number_input(
                    "Precio máximo ($)", min_value=0.0, value=99999.0, key="price_history_max"
                )

            # Rate limiting para eBay API
            if "last_ebay_search" not in st.session_state:
                st.session_state.last_ebay_search = 0

            current_time = time.time()
            time_since_last_search = current_time - st.session_state.last_ebay_search
            rate_limit_seconds = 5

            # Mostrar aviso si está en cooldown
            if time_since_last_search < rate_limit_seconds:
                remaining = int(rate_limit_seconds - time_since_last_search)
                st.warning(
                    f"⏳ Espera {remaining} segundos antes de otra búsqueda (límite de eBay)"
                )
                st.button(
                    "📊 Ver Historial de Precios en eBay",
                    type="primary",
                    use_container_width=True,
                    disabled=True,
                )
            else:
                if st.button(
                    "📊 Ver Historial de Precios en eBay", type="primary", use_container_width=True
                ):
                    st.session_state.last_ebay_search = current_time
                    if not player:
                        st.warning("Por favor ingresa un nombre de jugador")
                    else:
                        with st.spinner("Buscando historial de precios..."):
                            try:
                                tool = get_ebay_tool()
                                params = EBaySearchParams(
                                    keywords=f"{player} {card_year if card_year > 0 else ''} graded"
                                    if grade != "Todas"
                                    else player,
                                    max_results=30,
                                    sold_items_only=True,
                                    min_price=min_price if min_price > 0 else None,
                                    max_price=max_price if max_price < 99999 else None,
                                )

                                try:
                                    listings = _safe_async_run(
                                        tool.search_cards(params), timeout=30
                                    )
                                except TimeoutError:
                                    st.error(
                                        "❌ La búsqueda tardó demasiado. Intenta con términos más específicos."
                                    )
                                    listings = None

                                # Búsqueda progresiva automática
                                fallback_attempts = [
                                    {
                                        "desc": "sin año",
                                        "params": dict(
                                            keywords=player,
                                            max_results=30,
                                            sold_items_only=True,
                                            min_price=min_price if min_price > 0 else None,
                                            max_price=max_price if max_price < 99999 else None,
                                        ),
                                    },
                                    {
                                        "desc": "sin grade",
                                        "params": dict(
                                            keywords=f"{player} {card_year if card_year > 0 else ''}",
                                            max_results=30,
                                            sold_items_only=True,
                                            min_price=min_price if min_price > 0 else None,
                                            max_price=max_price if max_price < 99999 else None,
                                        ),
                                    },
                                    {
                                        "desc": "solo nombre",
                                        "params": dict(
                                            keywords=player, max_results=30, sold_items_only=True
                                        ),
                                    },
                                ]
                                if listings is None or not listings:
                                    found = False
                                    for attempt in fallback_attempts:
                                        try:
                                            fallback_listings = _safe_async_run(
                                                tool.search_cards(
                                                    EBaySearchParams(**attempt["params"])
                                                ),
                                                timeout=30,
                                            )
                                            if fallback_listings:
                                                st.info(
                                                    f"No se encontraron ventas exactas. Mostrando resultados {attempt['desc']}."
                                                )
                                                listings = fallback_listings
                                                found = True
                                                break
                                        except Exception:
                                            continue
                                    if not found:
                                        # Buscar ventas similares (otros años, marcas, grades)
                                        st.info(
                                            "Buscando ventas similares de otros años, marcas o grades..."
                                        )
                                        try:
                                            similar_params = dict(
                                                keywords=player,
                                                max_results=30,
                                                sold_items_only=True,
                                            )
                                            similar_listings = _safe_async_run(
                                                tool.search_cards(
                                                    EBaySearchParams(**similar_params)
                                                ),
                                                timeout=30,
                                            )
                                            if similar_listings:
                                                st.info(
                                                    "Mostrando ventas similares encontradas (otros años, marcas o grades)."
                                                )
                                                listings = similar_listings
                                            else:
                                                # Mostrar ventas locales guardadas si existen
                                                local_sales = load_sales_backup(player)
                                                if local_sales:
                                                    st.info(
                                                        "Mostrando ventas históricas guardadas localmente (pueden no ser recientes)."
                                                    )
                                                    listings = [
                                                        type("Listing", (), sale)
                                                        for sale in local_sales
                                                    ]
                                                else:
                                                    st.warning(
                                                        f"No se encontraron ventas de {player} (ni quitando filtros, ni buscando similares, ni en respaldo local). Prueba con otro nombre o sin filtros."
                                                    )
                                                    listings = []
                                        except Exception:
                                            local_sales = load_sales_backup(player)
                                            if local_sales:
                                                st.info(
                                                    "Mostrando ventas históricas guardadas localmente (pueden no ser recientes)."
                                                )
                                                listings = [
                                                    type("Listing", (), sale)
                                                    for sale in local_sales
                                                ]
                                            else:
                                                st.warning(
                                                    f"No se encontraron ventas de {player} (ni quitando filtros, ni buscando similares, ni en respaldo local). Prueba con otro nombre o sin filtros."
                                                )
                                                st.info(
                                                    "Sugerencias: \n- Quita el filtro de año o grade.\n- Intenta solo con el nombre del jugador.\n- Prueba con otro jugador popular."
                                                )
                                                # Mostrar promedio general del mercado si existe en respaldo local
                                                try:
                                                    with open(
                                                        LOCAL_SALES_FILE, encoding="utf-8"
                                                    ) as f:
                                                        data = json.load(f)
                                                    all_prices = []
                                                    for sales in data.values():
                                                        for sale in sales:
                                                            if "price" in sale:
                                                                all_prices.append(sale["price"])
                                                    if all_prices:
                                                        avg_market = sum(all_prices) / len(
                                                            all_prices
                                                        )
                                                        st.info(
                                                            f"Promedio general del mercado (todas las ventas guardadas): ${avg_market:,.2f}"
                                                        )
                                                except Exception:
                                                    pass
                                                listings = []
                                if listings:
                                    st.success(f"Encontradas {len(listings)} ventas")
                                    # Guardar respaldo local si los datos vienen de eBay
                                    if hasattr(listings[0], "listing_url"):
                                        save_sales_backup(player, listings)
                                    prices = [listing.price for listing in listings]
                                    if prices:
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric(
                                                "Promedio", f"${sum(prices) / len(prices):,.2f}"
                                            )
                                        with col2:
                                            st.metric("Máximo", f"${max(prices):,.2f}")
                                        with col3:
                                            st.metric("Mínimo", f"${min(prices):,.2f}")
                                        with col4:
                                            st.metric("Muestras", len(listings))
                                    else:
                                        st.info(
                                            "No hay datos suficientes para calcular el promedio de precios. Prueba ampliando tu búsqueda o quitando filtros."
                                        )
                                    st.subheader("📋 Últimas Ventas")
                                    for i, listing in enumerate(listings[:10], 1):
                                        with st.expander(
                                            f"#{i} - {getattr(listing, 'title', 'Venta')} - ${getattr(listing, 'price', 0):.2f}"
                                        ):
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.write(
                                                    f"**Precio:** ${getattr(listing, 'price', 0):.2f}"
                                                )
                                                st.write(
                                                    f"**Condición:** {getattr(listing, 'condition', 'N/A')}"
                                                )
                                            with col2:
                                                st.write(
                                                    f"**Vendedor:** {getattr(listing, 'seller_username', 'N/A')}"
                                                )
                                                st.write(
                                                    f"**Ubicación:** {getattr(listing, 'location', 'N/A')}"
                                                )
                                            if getattr(listing, "image_url", None):
                                                st.image(listing.image_url, width=200)
                                            if getattr(listing, "listing_url", None):
                                                st.link_button("Ver en eBay", listing.listing_url)

                            except EBayRateLimitError as e:
                                st.warning(f"⚠️ eBay API Limit: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

        with source_tab2:
            st.subheader("Fuentes de Precios Disponibles")

            sources = {
                "🏆 eBay": {
                    "descripción": "Mercado más grande de tarjetas deportivas",
                    "ventajas": [
                        "Mejor cobertura",
                        "Precios en tiempo real",
                        "Transparencia total",
                    ],
                    "estado": "✅ Activa",
                },
                "🎯 Goldin Auctions": {
                    "descripción": "Casa de subastas especializada en sports memorabilia",
                    "ventajas": [
                        "Tarjetas premium",
                        "Precios históricos",
                        "Autenticación garantizada",
                    ],
                    "estado": "📋 Próximamente",
                },
                "⭐ Fanatics Collectibles": {
                    "descripción": "Plataforma oficial de tarjetas deportivas licenciadas",
                    "ventajas": ["Tarjetas oficiales", "Seguridad garantizada", "Precios premium"],
                    "estado": "📋 Próximamente",
                },
                "💎 PSA/BGS Price Guide": {
                    "descripción": "Guía de precios oficial de tarjetas graduadas",
                    "ventajas": ["Datos precisos", "Actualización frecuente", "Tarjetas graded"],
                    "estado": "📋 Próximamente",
                },
                "🎪 Heritage Auctions": {
                    "descripción": "Casa de subastas de coleccionables",
                    "ventajas": ["Tarjetas raras", "Historial completo", "Precios verificados"],
                    "estado": "📋 Próximamente",
                },
            }

            for source, info in sources.items():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"### {source}")
                    st.write(info["descripción"])
                    st.markdown("**Ventajas:**")
                    for ventaja in info["ventajas"]:
                        st.markdown(f"• {ventaja}")
                with col2:
                    st.markdown(f"**{info['estado']}**")

        with source_tab3:
            st.subheader("Análisis de Precios")
            st.info(
                "🔍 Usa el análisis avanzado en la pestaña 'Análisis de Tarjeta' para obtener "
                "predicciones de precios basadas en datos de mercado y rendimiento de jugadores."
            )

            st.markdown(
                """
                ### Cómo Interpretar los Datos de Precios
                
                **Tendencias:**
                - 📈 Precios subiendo → Demanda creciente
                - 📉 Precios bajando → Demanda decreciente
                - ➡️ Precios estables → Mercado equilibrado
                
                **Factores que Afectan Precios:**
                - 🏆 Rendimiento del jugador (estadísticas, premios)
                - 🎴 Rareza de la tarjeta (print runs bajos)
                - 📊 Condición de la tarjeta (PSA/BGS grade)
                - 👥 Oferta vs Demanda del mercado
                - 📅 Antigüedad de la tarjeta
                
                **Mejores Prácticas:**
                - Siempre verifica múltiples fuentes
                - Mira al menos 10-20 ventas recientes
                - Considera la condición exacta (grade)
                - Revisa el historial de precios a 30/60/90 días
                """
            )


# ===============================
# Health Check Endpoint
# ===============================
def health_check():
    """Endpoint de health check para producción"""
    import json
    from datetime import datetime

    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {},
    }

    try:
        health["checks"]["database"] = "ok"
    except Exception:
        health["checks"]["database"] = "error"
        health["status"] = "degraded"

    return health


# ===============================
# PWA Service Worker Registration
# ===============================
def register_pwa():
    """Registra el service worker para PWA"""
    st.markdown(
        """
        <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/src/static/service-worker.js')
                    .then(registration => {
                        console.log('SW registered:', registration.scope);
                    })
                    .catch(error => {
                        console.log('SW registration failed:', error);
                    });
            });
        }
        </script>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
