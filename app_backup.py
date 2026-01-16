"""
Aplicación web para análisis de tarjetas deportivas
Interfaz interactiva con Streamlit
"""
import streamlit as st
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

from src.agents.price_analyzer_agent import PriceAnalyzerAgent
from src.tools.ebay_tool import EBayTool, EBaySearchParams
from src.models.card import (
    Card, Player, Sport, CardCondition, PricePoint
)


# Configuración de la página
st.set_page_config(
    page_title="Sports Card AI Agent",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_agent():
    """Obtiene instancia del agente (cacheada)"""
    return PriceAnalyzerAgent(verbose=False)


@st.cache_resource
def get_ebay_tool():
    """Obtiene instancia de herramienta eBay (cacheada)"""
    return EBayTool()


def create_price_chart(prices: list, title: str = "Historial de Precios"):
    """Crea gráfico de precios con Plotly"""
    df = pd.DataFrame([
        {
            'Fecha': p.timestamp,
            'Precio': p.price,
            'Estado': 'Vendido' if p.sold else 'Listado'
        }
        for p in prices
    ])
    
    fig = go.Figure()
    
    # Línea de precios
    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Precio'],
        mode='lines+markers',
        name='Precio',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=8)
    ))
    
    # Línea de promedio
    avg_price = df['Precio'].mean()
    fig.add_hline(
        y=avg_price,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Promedio: ${avg_price:.2f}",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=title,
        xaxis_title="Fecha",
        yaxis_title="Precio (USD)",
        hovermode='x unified',
        height=400
    )
    
    return fig


def main():
    """Función principal de la aplicación"""
    
    # Header
    st.markdown('<h1 class="main-header">🏀 Sports Card AI Agent</h1>', unsafe_allow_html=True)
    st.markdown("### Análisis inteligente de tarjetas deportivas con IA")
    
    # Sidebar
    st.sidebar.title("⚙️ Configuración")
    
    # Selección de deporte
    sport = st.sidebar.selectbox(
        "Deporte",
        options=["NBA", "NHL", "MLB"],
        index=0
    )
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Búsqueda en eBay", 
    "📊 Análisis de Tarjeta", 
    "💼 My Portfolio",
    "📜 History", 
    "📈 Dashboard"
])
    
    # ============================================================
    # TAB 1: Búsqueda en eBay
    # ============================================================
    with tab1:
        st.header("🔍 Buscar Tarjetas en eBay")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "Buscar tarjeta",
                placeholder="Ej: LeBron James 2003 Topps Rookie",
                help="Ingresa el nombre del jugador, año, fabricante, etc."
            )
        
        with col2:
            max_results = st.number_input(
                "Máximo de resultados",
                min_value=5,
                max_value=50,
                value=10,
                step=5
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sold_only = st.checkbox("Solo vendidos", value=False)
        with col2:
            min_price = st.number_input("Precio mínimo ($)", min_value=0.0, value=0.0, step=10.0)
        with col3:
            max_price = st.number_input("Precio máximo ($)", min_value=0.0, value=0.0, step=100.0)
        
        if st.button("🔍 Buscar", type="primary", use_container_width=True):
            if not search_query:
                st.warning("⚠️ Por favor ingresa un término de búsqueda")
            else:
                with st.spinner("Buscando en eBay..."):
                    try:
                        tool = get_ebay_tool()
                        params = EBaySearchParams(
                            keywords=search_query,
                            max_results=max_results,
                            sold_items_only=sold_only,
                            min_price=min_price if min_price > 0 else None,
                            max_price=max_price if max_price > 0 else None
                        )
                        
                        # Ejecutar búsqueda
                        listings = asyncio.run(tool.search_cards(params))
                        
                        if not listings:
                            st.warning("❌ No se encontraron resultados")
                        else:
                            st.success(f"✅ Encontrados {len(listings)} resultados")
                            
                            # Mostrar resultados
                            for i, listing in enumerate(listings, 1):
                                with st.expander(f"#{i} - {listing.title[:80]}..."):
                                    col1, col2 = st.columns([1, 2])
                                    
                                    with col1:
                                        if listing.image_url:
                                            st.image(listing.image_url, width=200)
                                    
                                    with col2:
                                        st.markdown(f"**Título:** {listing.title}")
                                        st.markdown(f"**Precio:** ${listing.price:.2f} {listing.currency}")
                                        st.markdown(f"**Condición:** {listing.condition}")
                                        st.markdown(f"**Estado:** {'✅ VENDIDO' if listing.sold else '🔵 A LA VENTA'}")
                                        st.markdown(f"**Vendedor:** {listing.seller_username}")
                                        st.markdown(f"**Ubicación:** {listing.location}")
                                        if listing.shipping_cost and listing.shipping_cost > 0:
                                            st.markdown(f"**Envío:** ${listing.shipping_cost:.2f}")
                                        st.markdown(f"[🔗 Ver en eBay]({listing.listing_url})")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    # ============================================================
    # TAB 2: Análisis de Tarjeta
    # ============================================================
    with tab2:
        st.header("📊 Análisis Inteligente de Tarjeta")
        
        st.info("💡 Esta sección usa el agente de IA para analizar precios y generar recomendaciones")
        
        # Formulario para ingresar datos de la tarjeta
        with st.form("card_analysis_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                player_name = st.text_input("Nombre del jugador", value="LeBron James")
                year = st.number_input("Año", min_value=1900, max_value=2025, value=2003)
                manufacturer = st.text_input("Fabricante", value="Topps")
                set_name = st.text_input("Nombre del set", value="Topps Chrome")
            
            with col2:
                card_number = st.text_input("Número de tarjeta", value="221")
                variant = st.text_input("Variante", value="Rookie Card")
                grade = st.number_input("Grado (si está graduada)", min_value=1.0, max_value=10.0, value=9.5, step=0.5)
                grading_company = st.text_input("Compañía de graduación", value="PSA")
            
            player_performance = st.text_area(
                "Rendimiento reciente del jugador",
                value="El jugador está en excelente forma, promediando 28 puntos por partido",
                height=100
            )
            
            # Seleccionar tendencia de precios para demostración
            price_trend = st.selectbox(
                "Tendencia de precios (demo)",
                options=["Bajando", "Subiendo", "Estable"],
                help="Para demostración, selecciona cómo han estado los precios"
            )
            
            submitted = st.form_submit_button("🤖 Analizar con IA", type="primary", use_container_width=True)
        
        if submitted:
            with st.spinner("🤖 El agente está analizando la tarjeta..."):
                try:
                    # Crear modelo de tarjeta
                    player = Player(
                        id=player_name.lower().replace(" ", "-"),
                        name=player_name,
                        sport=Sport[sport],
                        team="Unknown",
                        position="Unknown"
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
                        grading_company=grading_company
                    )
                    
                    # Generar precios de ejemplo basados en tendencia
                    base_price = 1000.0
                    prices = []
                    
                    for i in range(30):
                        date = datetime.now() - timedelta(days=30-i)
                        
                        if price_trend == "Subiendo":
                            price = base_price + (i * 20)
                        elif price_trend == "Bajando":
                            price = base_price - (i * 15)
                        else:
                            price = base_price + ((-1)**i * 50)
                        
                        price_point = PricePoint(
                            card_id=card.id,
                            price=max(price, 100),
                            marketplace="ebay",
                            listing_url="https://ebay.com/item/demo",
                            timestamp=date,
                            sold=True
                        )
                        prices.append(price_point)
                    
                    # Analizar con el agente
                    agent = get_agent()
                    recommendation = agent.analyze_card(
                        card=card,
                        price_history=prices,
                        player_performance=player_performance
                    )
                    
                    # Mostrar resultados
                    st.success("✅ Análisis completado")
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Señal",
                            recommendation.signal.value.upper(),
                            help="Recomendación del agente"
                        )
                    
                    with col2:
                        st.metric(
                            "Confianza",
                            f"{recommendation.confidence:.0%}",
                            help="Nivel de confianza del análisis"
                        )
                    
                    with col3:
                        st.metric(
                            "Precio Actual",
                            f"${recommendation.current_price:.2f}",
                            help="Último precio registrado"
                        )
                    
                    with col4:
                        avg_price = sum(p.price for p in prices) / len(prices)
                        diff = recommendation.current_price - avg_price
                        st.metric(
                            "vs. Promedio",
                            f"${diff:+.2f}",
                            f"{(diff/avg_price)*100:+.1f}%",
                            help="Diferencia con precio promedio"
                        )
                    
                    # Gráfico de precios
                    st.plotly_chart(
                        create_price_chart(prices, "Historial de Precios (últimos 30 días)"),
                        use_container_width=True
                    )
                    
                    # Razonamiento
                    st.subheader("📝 Razonamiento del Agente")
                    st.info(recommendation.reasoning)
                    
                    # Factores considerados
                    st.subheader("📌 Factores Considerados")
                    for factor in recommendation.factors:
                        st.markdown(f"• {factor}")
                    
                    # Precios objetivo
                    if recommendation.target_buy_price or recommendation.target_sell_price:
                        st.subheader("🎯 Precios Objetivo")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if recommendation.target_buy_price:
                                st.success(f"💰 Comprar a: ${recommendation.target_buy_price:.2f}")
                        
                        with col2:
                            if recommendation.target_sell_price:
                                st.warning(f"💸 Vender a: ${recommendation.target_sell_price:.2f}")
                
                except Exception as e:
                    st.error(f"❌ Error en el análisis: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    # ============================================================
    # TAB 3: My Portfolio
    # ============================================================
    with tab3:
        st.header("💼 Mi Portfolio de Tarjetas")
        
        st.info("📊 Administra tu colección y trackea el valor de tus inversiones")
        
        # Dos columnas: Formulario y Portfolio
        col_form, col_portfolio = st.columns([1, 2])
        
        with col_form:
            st.subheader("➕ Añadir Tarjeta")
            
            with st.form("add_portfolio_form"):
                player_name_port = st.text_input("Jugador", value="LeBron James")
                
                col1, col2 = st.columns(2)
                with col1:
                    year_port = st.number_input("Año", min_value=1900, max_value=2025, value=2003)
                with col2:
                    sport_port = st.selectbox("Deporte", ["NBA", "NHL", "MLB"], key="portfolio_sport")
                
                manufacturer_port = st.text_input("Fabricante", value="Topps")
                
                col1, col2 = st.columns(2)
                with col1:
                    purchase_price = st.number_input(
                        "Precio de Compra ($)", 
                        min_value=0.0, 
                        value=100.0, 
                        step=10.0
                    )
                with col2:
                    quantity = st.number_input("Cantidad", min_value=1, value=1, step=1)
                
                purchase_date = st.date_input("Fecha de Compra", value=datetime.now())
                
                notes = st.text_area("Notas", placeholder="Ej: PSA 9, comprada en eBay", height=80)
                
                submitted = st.form_submit_button("➕ Añadir al Portfolio", type="primary", use_container_width=True)
            
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
                                sport=sport_port
                            )
                            
                            # Get or create card
                            card_id = f"{player_id}-{year_port}-{manufacturer_port.lower()}"
                            card = CardRepository.get_or_create_card(
                                db=db,
                                card_id=card_id,
                                player_db=player,
                                year=year_port,
                                manufacturer=manufacturer_port
                            )
                            
                            # Add to portfolio
                            CardRepository.add_to_portfolio(
                                db=db,
                                card=card,
                                purchase_price=purchase_price,
                                purchase_date=datetime.combine(purchase_date, datetime.min.time()),
                                quantity=quantity,
                                notes=notes
                            )
                            
                            st.success(f"✅ {player_name_port} añadido al portfolio!")
                            st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col_portfolio:
            st.subheader("📊 Tu Portfolio")
            
            try:
                from src.utils.database import get_db
                from src.utils.repository import CardRepository
                
                with get_db() as db:
                    # Get portfolio stats
                    stats = CardRepository.get_portfolio_stats(db)
                    
                    # Display stats
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Tarjetas",
                            stats['total_items'],
                            help="Total de tarjetas en portfolio"
                        )
                    
                    with col2:
                        st.metric(
                            "Invertido",
                            f"${stats['total_invested']:.2f}",
                            help="Total invertido"
                        )
                    
                    with col3:
                        st.metric(
                            "Valor Actual",
                            f"${stats['current_value']:.2f}",
                            help="Valor actual del portfolio"
                        )
                    
                    with col4:
                        delta_color = "normal" if stats['total_gain_loss'] >= 0 else "inverse"
                        st.metric(
                            "Ganancia/Pérdida",
                            f"${stats['total_gain_loss']:.2f}",
                            f"{stats['total_gain_loss_pct']:+.1f}%",
                            delta_color=delta_color,
                            help="Ganancia o pérdida total"
                        )
                    
                    # Get portfolio items
                    portfolio_items = CardRepository.get_portfolio(db, active_only=True)
                    
                    if not portfolio_items:
                        st.info("📭 Tu portfolio está vacío. Añade tu primera tarjeta arriba.")
                    else:
                        # Display items
                        st.divider()
                        
                        for item in portfolio_items:
                            with st.expander(
                                f"{item['player_name']} - {item['year']} {item['manufacturer']} "
                                f"({'✅ +' if item['gain_loss'] >= 0 else '❌ '}"
                                f"${abs(item['gain_loss']):.2f})"
                            ):
                                col1, col2, col3 = st.columns([2, 2, 1])
                                
                                with col1:
                                    st.markdown(f"**Jugador:** {item['player_name']}")
                                    st.markdown(f"**Deporte:** {item['sport']}")
                                    st.markdown(f"**Tarjeta:** {item['year']} {item['manufacturer']}")
                                    st.markdown(f"**Cantidad:** {item['quantity']}")
                                
                                with col2:
                                    st.metric(
                                        "Precio Compra",
                                        f"${item['purchase_price']:.2f}"
                                    )
                                    st.metric(
                                        "Valor Actual",
                                        f"${item['current_value']:.2f}",
                                        f"{item['gain_loss_pct']:+.1f}%"
                                    )
                                    st.markdown(f"**Valor Total:** ${item['total_value']:.2f}")
                                    st.markdown(f"**Comprado:** {item['purchase_date'].strftime('%Y-%m-%d')}")
                                
                                with col3:
                                    # Update value
                                    new_value = st.number_input(
                                        "Actualizar valor",
                                        min_value=0.0,
                                        value=float(item['current_value']),
                                        step=10.0,
                                        key=f"update_{item['id']}"
                                    )
                                    
                                    if st.button("💾 Actualizar", key=f"btn_update_{item['id']}"):
                                        CardRepository.update_portfolio_value(
                                            db=db,
                                            portfolio_item_id=item['id'],
                                            new_value=new_value
                                        )
                                        st.success("✅ Actualizado")
                                        st.rerun()
                                    
                                    if st.button("🗑️ Vender", key=f"btn_sell_{item['id']}"):
                                        CardRepository.remove_from_portfolio(
                                            db=db,
                                            portfolio_item_id=item['id'],
                                            sell_price=item['current_value']
                                        )
                                        st.success("✅ Vendido")
                                        st.rerun()
                                
                                if item['notes']:
                                    st.markdown(f"**Notas:** {item['notes']}")
                        
                        # Distribution chart
                        if len(portfolio_items) > 1:
                            st.divider()
                            st.subheader("📊 Distribución del Portfolio")
                            
                            import plotly.express as px
                            
                            df_portfolio = pd.DataFrame(portfolio_items)
                            
                            fig = px.pie(
                                df_portfolio,
                                values='total_value',
                                names='player_name',
                                title='Distribución por Valor',
                                hole=0.4
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
                options=["Todos", "NBA", "NHL", "MLB"],
                key="history_sport"
            )
        
        with col2:
            filter_signal = st.selectbox(
                "Filtrar por señal",
                options=["Todas", "BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"],
                key="history_signal"
            )
        
        with col3:
            limit = st.number_input(
                "Número de resultados",
                min_value=10,
                max_value=100,
                value=20,
                step=10
            )
        
        if st.button("🔄 Cargar Análisis", type="primary", use_container_width=True):
            try:
                from src.utils.database import get_db
                from src.utils.repository import CardRepository
                
                with st.spinner("Cargando análisis..."):
                    with get_db() as db:
                        # Aplicar filtros
                        sport_filter = None if filter_sport == "Todos" else filter_sport
                        signal_filter = None if filter_signal == "Todas" else filter_signal
                        
                        analyses = CardRepository.get_all_analyses(
                            db,
                            limit=limit,
                            sport=sport_filter,
                            signal=signal_filter
                        )
                        
                        if not analyses:
                            st.warning("⚠️ No se encontraron análisis con esos filtros")
                        else:
                            st.success(f"✅ Encontrados {len(analyses)} análisis")
                            
                            # Mostrar en tarjetas
                            for i, analysis in enumerate(analyses):
                                with st.expander(
                                    f"#{i+1} - {analysis['player_name']} {analysis['year']} "
                                    f"({analysis['sport']}) - {analysis['signal']}"
                                ):
                                    col1, col2 = st.columns([1, 2])
                                    
                                    with col1:
                                        # Métricas
                                        st.metric(
                                            "Señal",
                                            analysis['signal'],
                                            help="Recomendación del agente"
                                        )
                                        st.metric(
                                            "Confianza",
                                            f"{analysis['confidence']:.0%}",
                                            help="Nivel de confianza"
                                        )
                                        if analysis['current_price']:
                                            st.metric(
                                                "Precio",
                                                f"${analysis['current_price']:.2f}",
                                                help="Precio de entrada"
                                            )
                                    
                                    with col2:
                                        # Detalles
                                        st.markdown(f"**Jugador:** {analysis['player_name']}")
                                        st.markdown(f"**Tarjeta:** {analysis['year']} {analysis['manufacturer']}")
                                        st.markdown(f"**Tipo:** {analysis['analysis_type']}")
                                        st.markdown(f"**Fecha:** {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                                        
                                        if analysis['reasoning']:
                                            st.markdown("**Razonamiento:**")
                                            st.text_area(
                                                "reasoning",
                                                analysis['reasoning'],
                                                height=100,
                                                key=f"reasoning_{analysis['id']}",
                                                label_visibility="collapsed"
                                            )
                        
                        # Estadísticas
                        st.divider()
                        st.subheader("📊 Estadísticas")
                        
                        stats = CardRepository.get_statistics(db)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Jugadores", stats['total_players'])
                        with col2:
                            st.metric("Tarjetas", stats['total_cards'])
                        with col3:
                            st.metric("Análisis", stats['total_analyses'])
                        with col4:
                            st.metric("Esta semana", stats['recent_analyses'])
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # ============================================================
    # TAB : Dashboard
    # ============================================================
    with tab4:
        st.header("📈 Dashboard de Mercado")
        st.info("🚧 Próximamente: Estadísticas del mercado, comparaciones, y más")
        
        # Placeholder para futuras funcionalidades
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tarjetas Analizadas", "0", help="Total de tarjetas analizadas hoy")
        
        with col2:
            st.metric("Señales de Compra", "0", help="Oportunidades de compra detectadas")
        
        with col3:
            st.metric("Señales de Venta", "0", help="Oportunidades de venta detectadas")


if __name__ == "__main__":
    main()