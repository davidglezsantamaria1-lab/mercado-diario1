# Informe Diario de Mercado

Aplicación Streamlit para generar un dashboard diario con:

1. Resumen de la jornada anterior.
2. Noticias económicas relevantes.
3. Top acciones con mayores subidas.
4. Top acciones con mayores bajadas.
5. Análisis y recomendaciones tácticas.
6. ETFs/fondos clave para Trade Republic.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Despliegue en Streamlit Community Cloud

1. Crea un repositorio en GitHub.
2. Sube estos archivos:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`
3. Entra en https://share.streamlit.io
4. Conecta tu cuenta de GitHub.
5. Selecciona el repositorio.
6. En `Main file path`, escribe: `app.py`
7. Pulsa `Deploy`.

## Notas

- La app usa `yfinance`, por lo que algunos datos pueden retrasarse o no estar disponibles temporalmente.
- Las noticias se cargan desde RSS públicos.
- Las recomendaciones son análisis informativo, no asesoramiento financiero personalizado.
