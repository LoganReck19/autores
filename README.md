# Biblioteca

Aplicación web de biblioteca construida con **FastAPI**, **HTMX**, **Jinja2**, **Bootstrap** y **SQLAlchemy**. Permite consultar libros y autores, crear registros, editar y borrar autores, y borrar libros sin recargar la página.

## Funcionalidades

- Panel de bienvenida con resumen de libros y autores.
- Catálogo inicial con 10 libros reales y sus autores.
- Sección de autores con tabla Bootstrap.
- Crear autores mediante formulario HTMX.
- Editar autores directamente desde su fila.
- Borrar autores con confirmación.
- Sección de libros con formulario para crear libros.
- Selector de autores conectado a la base de datos.
- Borrar libros con confirmación y actualización parcial.
- SQLite creada automáticamente al iniciar la aplicación.
- Configuración incluida para desplegar en Vercel.

## Requisitos

- Python 3.10 o superior.
- `pip`.

## Instalación

Desde la raíz del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows, activar el entorno virtual con:

```powershell
.venv\Scripts\Activate.ps1
```

## Ejecución local

```bash
uvicorn api.index:app --reload
```

Después, abrir [http://127.0.0.1:8000](http://127.0.0.1:8000).

La base de datos `biblioteca.db` se crea automáticamente en el primer arranque. Está excluida de Git porque contiene datos locales.

## Rutas principales

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Panel de bienvenida |
| `GET` | `/autores` | Lista y formulario de autores |
| `POST` | `/autores` | Crea un autor |
| `GET` | `/autores/{id}/editar` | Muestra la fila editable |
| `POST` | `/autores/{id}/editar` | Guarda los cambios del autor |
| `DELETE` | `/autores/{id}` | Borra un autor |
| `GET` | `/autores/{id}/libros` | Muestra sus libros en la fila |
| `GET` | `/libros` | Lista y formulario de libros |
| `POST` | `/libros` | Crea un libro |
| `DELETE` | `/libros/{id}` | Borra un libro |

Las peticiones que incluyen la cabecera `HX-Request` reciben fragmentos HTML. HTMX los inserta en la tabla correspondiente sin recargar el documento completo.

## Estructura del proyecto

```text
autores/
├── api/
│   └── index.py           # Aplicación FastAPI, modelos, seed y rutas
├── static/
│   └── styles.css         # Estilos del panel inicial
├── templates/
│   ├── home.html          # Página de inicio
│   ├── authors.html       # Página de autores
│   ├── authors-table.html
│   ├── author-row.html
│   ├── author-edit.html
│   ├── author-books.html
│   ├── books-page.html    # Página completa de libros
│   ├── books.html         # Tabla parcial de libros
│   └── book-row.html
├── requirements.txt
├── vercel.json
└── biblioteca.db          # Generada localmente, no versionada
```

## Modelo de datos

La tabla `authors` contiene `id`, `name` y `country`. La tabla `books` contiene `id`, `title`, `year`, `genre` y `author_id`. La relación es uno a muchos: un autor puede tener varios libros.

## Despliegue en Vercel

1. Subir el proyecto a un repositorio Git.
2. Importar el repositorio desde Vercel.
3. Mantener `api/index.py` como función Python mediante el `vercel.json` incluido.
4. Desplegar.

> SQLite es adecuada para desarrollo y demostraciones. Para producción con datos persistentes en Vercel se recomienda cambiar `DATABASE_URL` por una base externa como PostgreSQL o Vercel Postgres.

## Validación

Prueba rápida de sintaxis:

```bash
python -m py_compile api/index.py
```

También se puede usar `TestClient` de FastAPI para comprobar las rutas y los formularios HTMX.
