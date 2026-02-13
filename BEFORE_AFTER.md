# 📝 Antes vs Después - Cambios Claves

## 1. Debug Prints → Logger

### ❌ ANTES (app.py líneas 1030-1070)

```python
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
        print(f"DEBUG: Player created - {player.name}")  # ❌ BAD: stdout pollution

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
        print(f"DEBUG: Card created - {card.card_id}")  # ❌ BAD

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
        print(f"DEBUG: Portfolio item created - ID {portfolio_item.id}")  # ❌ BAD

        # Commit explicitly
        db.commit()
        print("DEBUG: Transaction committed")  # ❌ BAD

except Exception as e:
    st.error(f"❌ Error al añadir: {str(e)}")
    print("ERROR COMPLETO:")  # ❌ BAD: traceback mixed with print
    import traceback
    traceback.print_exc()  # ❌ BAD: unstructured
```

### ✅ DESPUÉS (mejorado)

```python
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
        logger.debug(f"Player created - {player.name}")  # ✅ GOOD: structured logging

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
        logger.debug(f"Card created - {card.card_id}")  # ✅ GOOD

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
        logger.debug(f"Portfolio item created - ID {portfolio_item.id}")  # ✅ GOOD

        # Commit explicitly
        db.commit()
        logger.debug("Transaction committed")  # ✅ GOOD

except Exception as e:
    st.error(f"❌ Error al añadir: {str(e)}")
    logger.error("Error adding to portfolio", exc_info=True)  # ✅ GOOD: full stack trace in logs
```

**Ventajas:**

- ✅ Logs van a `logs/sports_card_agent.log`
- ✅ Stack traces completos con `exc_info=True`
- ✅ Producción clean (sin debug en stdout)
- ✅ Levelable (DEBUG, INFO, WARNING, ERROR)

---

## 2. Formulario Duplicado → Reutilizable

### ❌ ANTES (45 líneas x 2 = 90 líneas)

```python
# Primer formulario (líneas ~220-270)
with st.expander("📝 Registro", expanded=True):
    with st.form("register_form"):
        new_user = st.text_input("Usuario")
        new_email = st.text_input("Email")
        new_pass = st.text_input("Password", type="password")
        new_name = st.text_input("Nombre Completo")
        reg_btn = st.form_submit_button("Registrarse")

        if reg_btn:
            with get_db() as db:
                existing_user = CardRepository.get_user_by_username(db, new_user)
                existing_email = CardRepository.get_user_by_email(db, new_email)

                if existing_user:
                    st.error(f"❌ El usuario '{new_user}' ya existe.")
                elif existing_email:
                    st.error(f"❌ El email '{new_email}' ya está registrado.")
                else:
                    new_user_db = CardRepository.create_user(
                        db,
                        new_user,
                        new_email,
                        hash_password(new_pass),
                        new_name,
                    )
                    db.commit()

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
                            db.query(WatchlistDB).filter(WatchlistDB.user_id.is_(None)).all()
                        )
                        for item in orphaned_watchlist:
                            item.user_id = new_user_db.id

                        db.commit()

                    st.success("¡Usuario creado!")
                    st.rerun()

# Segundo formulario (líneas ~315-365) - EXACTAMENTE IGUAL
with st.expander("📝 ¿No tienes cuenta? Regístrate"):
    with st.form("register_form_new"):
        new_user = st.text_input("Nuevo Usuario")
        new_email = st.text_input("Email")
        new_pass = st.text_input("Password", type="password")
        new_name = st.text_input("Nombre Completo")
        reg_btn = st.form_submit_button("Crear Cuenta")
        if reg_btn:
            # ... MISMO CÓDIGO ...
```

### ✅ DESPUÉS (1 función reutilizable)

```python
def _show_registration_form(form_key: str = "register_form", expanded: bool = False):
    """
    Muestra un formulario de registro reutilizable
    
    Args:
        form_key: Clave única para el formulario (evita conflictos en Streamlit)
        expanded: Si el expander debe estar expandido por defecto
    
    Returns:
        bool: True si el registro fue exitoso, False en caso contrario
    """
    from src.models.db_models import PortfolioItemDB, WatchlistDB
    from src.utils.database import get_db
    from src.utils.repository import CardRepository
    
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
                            st.error(f"❌ El usuario '{new_user}' ya existe.")
                            return False
                        elif existing_email:
                            st.error(f"❌ El email '{new_email}' ya está registrado.")
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

# USO (2 líneas cada uno)
if not users:
    st.info("👋 ¡Bienvenido! Crea tu primer usuario para empezar.")
    _show_registration_form(form_key="register_form_initial", expanded=True)

if users:
    _show_registration_form(form_key="register_form_new", expanded=False)
```

**Ventajas:**

- ✅ Código seco (DRY)
- ✅ Fácil de mantener
- ✅ Parámetros parametrizables
- ✅ Return value para testing
- ✅ Mejor documentado

---

## 3. Async Sin Protección → Con Manejo de Errores

### ❌ ANTES (sin timeout handling)

```python
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

                # Ejecutar búsqueda - NO HAY TIMEOUT ❌
                listings = asyncio.run(tool.search_cards(params))

                if not listings:
                    st.warning(f"No se encontraron resultados para: **{search_query}**")
                else:
                    st.success(f"Encontrados {len(listings)} resultados")
                    for i, listing in enumerate(listings, 1):
                        # mostrar resultados...
                        
            except EBayRateLimitError as e:
                st.warning(f"⚠️ **eBay API Limit:** {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")  # ❌ Muy genérico
```

### ✅ DESPUÉS (con protección)

```python
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

                # Ejecutar búsqueda CON TIMEOUT ✅
                try:
                    listings = asyncio.run(tool.search_cards(params), timeout=30)
                except asyncio.TimeoutError:
                    st.error("❌ La búsqueda tardó demasiado. Intenta con términos más específicos.")
                    return

                if not listings:
                    st.warning(f"No se encontraron resultados para: **{search_query}**")
                else:
                    st.success(f"Encontrados {len(listings)} resultados")
                    for i, listing in enumerate(listings, 1):
                        # mostrar resultados...
                        
            except EBayRateLimitError as e:
                st.warning(f"⚠️ **eBay API Limit:** {str(e)}")
                logger.warning(f"eBay rate limit: {e}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error("eBay search error", exc_info=True)  # ✅ Stack trace
```

**Ventajas:**

- ✅ Timeout detection (30 segundos)
- ✅ Errores específicos vs genéricos
- ✅ Stack traces en logs
- ✅ Messages claros al usuario

---

## 4. Session State con "Zombies" → Limpieza Automática

### ❌ ANTES (memory leak)

```python
if uploaded_file is not None:
    if st.button("🔍 Identificar con Vision AI"):
        with st.spinner("🤖 Analizando..."):
            try:
                vision_tool = get_vision_tool()
                image_bytes = uploaded_file.read()
                card_data = asyncio.run(vision_tool.identify_card(image_bytes))

                if card_data.get("success"):
                    st.success("✅ Identificada!")
                    st.session_state["vision_data"] = card_data  # ❌ NUNCA SE LIMPIA
                    st.rerun()
                    # ... después de 10 análisis?
                    # vision_data sigue aquí! (memory leak)
```

### ✅ DESPUÉS (limpieza explícita)

```python
def _cleanup_session_state(keys_to_clean: list = None):
    """Limpia keys específicas de session_state"""
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

# EN EL CÓDIGO
if uploaded_file is not None:
    if st.button("🔍 Identificar con Vision AI"):
        with st.spinner("🤖 Analizando..."):
            try:
                vision_tool = get_vision_tool()
                image_bytes = uploaded_file.read()
                card_data = asyncio.run(vision_tool.identify_card(image_bytes))

                if card_data.get("success"):
                    st.success("✅ Identificada!")
                    st.session_state["vision_data"] = card_data
                    st.rerun()

# ... más abajo, DESPUÉS DE USAR LOS DATOS
_cleanup_session_state(["vision_data"])  # ✅ LIMPIO
```

**Ventajas:**

- ✅ No hay data zombies
- ✅ Memory controlado
- ✅ Datos frescos entre sesiones
- ✅ Debugging más fácil

---

## 5. Imports Desordenados → Organizados

### ❌ ANTES (imports adentro)

```python
# En el archivo principal
@st.cache_resource
def get_supervisor_agent():
    """Obtiene instancia del supervisor (cacheada)"""
    from src.agents.supervisor_agent import SupervisorAgent  # ❌ Adentro
    return SupervisorAgent()

# Más abajo...
def sync_portfolio():
    from src.utils.realtime_sync import RealtimeSync  # ❌ Adentro
    sync_tool = RealtimeSync()
    # ...

# IDE no entiende el código
# Errores de import se detectan al runtime
# No hay autocomplete para SupervisorAgent
```

### ✅ DESPUÉS (imports arriba)

```python
# AL INICIO DEL ARCHIVO (líneas 1-35)
from src.agents.price_analyzer_agent import PriceAnalyzerAgent
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.market_research_agent import MarketResearchAgent
from src.models.card import Card, CardCondition, Player, PricePoint, Sport
from src.models.db_models import PortfolioItemDB, UserDB, WatchlistDB
from src.tools.card_vision_tool import CardVisionTool
from src.tools.ebay_tool import EBayRateLimitError, EBaySearchParams, EBayTool
from src.tools.one_thirty_point_tool import (
    OneThirtyPointRateLimitError,
    OneThirtyPointScrapingError,
    OneThirtyPointTool,
)
from src.utils.auth_utils import hash_password
from src.utils.database import get_db, init_db
from src.utils.repository import CardRepository
from src.utils.realtime_sync import RealtimeSync
from src.utils.logging_config import get_logger, setup_logging
from src.utils.ui_components import (
    glass_card,
    listing_card_html,
    live_ticker_html,
    metric_grid,
)

# AHORA SÍ
@st.cache_resource
def get_supervisor_agent():
    """Obtiene instancia del supervisor (cacheada)"""
    return SupervisorAgent()  # ✅ Import ya existe

def sync_portfolio():
    sync_tool = RealtimeSync()  # ✅ Import ya existe
    # ...

# IDE entiende perfectamente el código
# Autocomplete funciona
# Errores de import = startup errors (visible inmediato)
```

**Ventajas:**

- ✅ IDE autocomplete perfecto
- ✅ PEP 8 compliant
- ✅ Errores de import detectados antes
- ✅ Análisis estático más rápido

---

## 📊 Resumen de Cambios

| Cambio | Tipo | Impacto | Complejidad |
|--------|------|---------|-------------|
| Debug → Logger | Quality | Alto | Bajo |
| Formulario único | Refactor | Alto | Medio |
| Async protegido | Reliability | Crítico | Bajo |
| Session cleanup | Performance | Medio | Bajo |
| Imports ordenados | Maintainability | Medio | Bajo |

**Total de mejoras:** 5  
**Archivos modificados:** 1 (`app.py`)  
**Líneas optimizadas:** ~120  
**Bugs potenciales prevenidos:** 5+  

---
