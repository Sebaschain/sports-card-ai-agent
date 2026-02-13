# Arquitectura del Proyecto: Streamlit vs Railway

## ¿Qué es cada componente?

| Componente | Tipo | Propósito |
|------------|------|-----------|
| **Streamlit** | Librería Python | Interfaz web (UI) de la aplicación |
| **Railway** | Plataforma de deployment | Hosting/cloud para ejecutar la app en internet |

## ¿Son necesarios?

### Streamlit (Necesario para la UI web)

- ✅ **Necesario** si quieres la interfaz web interactiva
- ❌ **No necesario** si solo usas las herramientas como biblioteca Python

### Railway (Opcional - es hosting)

- ✅ Necesario si quieres **publicar** la app en internet
- ❌ No necesario si ejecutas la app **localmente**

## Opciones de Ejecución

```
┌─────────────────────────────────────────────────────────┐
│ 1. Solo Python (sin UI)                                │
│    → Usar las tools directamente en scripts Python     │
│    → No requiere Streamlit ni Railway                  │
├─────────────────────────────────────────────────────────┤
│ 2. Streamlit Local                                     │
│    → pip install streamlit                             │
│    → streamlit run app.py                              │
│    → UI web en tu computadora                          │
├─────────────────────────────────────────────────────────┤
│ 3. Railway (producción)                                │
│    → Deployment en la nube                             │
│    → Accesible desde internet                          │
└─────────────────────────────────────────────────────────┘
```

## Ejemplo: Usar 130Point sin Streamlit

```python
# test_130point.py
from src.tools.one_thirty_point_tool import OneThirtyPointTool

tool = OneThirtyPointTool()
sales = tool.search_player_sales("LeBron James")

for sale in sales:
    print(f"{sale.year} {sale.brand} - ${sale.sale_price} ({sale.grade_raw})")
```

```bash
# Ejecutar
python test_130point.py
```

## Dependencias Requeridas

Para usar las herramientas sin Streamlit:

```bash
# requirements.txt mínimo
httpx>=0.27.0
beautifulsoup4>=4.12.0
python-dateutil>=2.8.0
```

Para UI web completa:

```bash
# requirements.txt completo
streamlit>=1.30.0
# ... todas las demás dependencias
```

## Resumen

| Escenario | Streamlit | Railway |
|-----------|----------|---------|
| Usar tools en scripts Python | ❌ | ❌ |
| UI local en tu PC | ✅ | ❌ |
| App accesible en internet | ✅ | ✅ |

**Streamlit** = Interfaz (lo que ves)
**Railway** = Hosting (donde se ejecuta)
