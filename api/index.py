from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'biblioteca.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    genre: Mapped[str] = mapped_column(String(80), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=False)
    author: Mapped[Author] = relationship(back_populates="books")


SEED_DATA = [
    ("Gabriel García Márquez", "Colombia", "Cien años de soledad", 1967, "Realismo mágico"),
    ("Jane Austen", "Reino Unido", "Orgullo y prejuicio", 1813, "Novela"),
    ("Jorge Luis Borges", "Argentina", "Ficciones", 1944, "Cuento"),
    ("Virginia Woolf", "Reino Unido", "La señora Dalloway", 1925, "Modernismo"),
    ("Haruki Murakami", "Japón", "Kafka en la orilla", 2002, "Ficción"),
    ("Isabel Allende", "Chile", "La casa de los espíritus", 1982, "Realismo mágico"),
    ("Fyodor Dostoevsky", "Rusia", "Crimen y castigo", 1866, "Clásico"),
    ("Toni Morrison", "Estados Unidos", "Beloved", 1987, "Ficción histórica"),
    ("Julio Cortázar", "Argentina", "Rayuela", 1963, "Novela"),
    ("Mary Shelley", "Reino Unido", "Frankenstein", 1818, "Gótico"),
]


def seed_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.scalar(select(Book.id).limit(1)):
            return
        authors: dict[str, Author] = {}
        for author_name, country, title, year, genre in SEED_DATA:
            author = authors.setdefault(author_name, Author(name=author_name, country=country))
            author.books.append(Book(title=title, year=year, genre=genre))
            session.add(author)
        session.commit()


seed_database()
app = FastAPI(title="Biblioteca")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def get_db():
    with SessionLocal() as session:
        yield session


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"book_count": db.query(Book).count(), "author_count": db.query(Author).count()},
    )


@app.get("/libros", response_class=HTMLResponse)
def books(request: Request, db: Session = Depends(get_db)):
    library = db.query(Book).join(Author).order_by(Book.id).all()
    library_authors = db.query(Author).order_by(Author.name).all()
    template = "books.html" if request.headers.get("HX-Request") else "books-page.html"
    return templates.TemplateResponse(request=request, name=template, context={"books": library, "authors": library_authors})


@app.post("/libros", response_class=HTMLResponse)
def create_book(
    request: Request,
    titulo: str = Form(...),
    autor_id: int = Form(...),
    anio: int = Form(...),
    genero: str = Form(...),
    db: Session = Depends(get_db),
):
    author = db.get(Author, autor_id)
    if author is None:
        return HTMLResponse("<div class='alert alert-danger'>Selecciona un autor válido.</div>", status_code=400)
    db.add(Book(title=titulo.strip(), author_id=autor_id, year=anio, genre=genero.strip()))
    db.commit()
    return books(request, db)


@app.delete("/libros/{book_id}", response_class=HTMLResponse)
def delete_book(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        return HTMLResponse("<div class='alert alert-danger'>Libro no encontrado.</div>", status_code=404)
    db.delete(book)
    db.commit()
    return books(request, db)


@app.get("/autores", response_class=HTMLResponse)
def authors(request: Request, db: Session = Depends(get_db)):
    library_authors = db.query(Author).order_by(Author.name).all()
    template = "authors-table.html" if request.headers.get("HX-Request") else "authors.html"
    return templates.TemplateResponse(request=request, name=template, context={"authors": library_authors})


@app.post("/autores", response_class=HTMLResponse)
def create_author(request: Request, nombre: str = Form(...), pais: str = Form(...), db: Session = Depends(get_db)):
    author = Author(name=nombre.strip(), country=pais.strip())
    db.add(author)
    db.commit()
    return authors(request, db)


@app.get("/autores/{author_id}/editar", response_class=HTMLResponse)
def edit_author(request: Request, author_id: int, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        return HTMLResponse("<tr><td colspan='5'>Autor no encontrado</td></tr>", status_code=404)
    return templates.TemplateResponse(request=request, name="author-edit.html", context={"author": author})


@app.post("/autores/{author_id}/editar", response_class=HTMLResponse)
def update_author(request: Request, author_id: int, nombre: str = Form(...), pais: str = Form(...), db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        return HTMLResponse("<tr><td colspan='5'>Autor no encontrado</td></tr>", status_code=404)
    author.name, author.country = nombre.strip(), pais.strip()
    db.commit()
    return templates.TemplateResponse(request=request, name="author-row.html", context={"author": author})


@app.delete("/autores/{author_id}", response_class=HTMLResponse)
def delete_author(request: Request, author_id: int, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is not None:
        db.delete(author)
        db.commit()
    return authors(request, db)


@app.get("/autores/{author_id}/libros", response_class=HTMLResponse)
def author_books(request: Request, author_id: int, db: Session = Depends(get_db)):
    author = db.get(Author, author_id)
    if author is None:
        return HTMLResponse("<tr><td colspan='5'>Autor no encontrado</td></tr>", status_code=404)
    return templates.TemplateResponse(request=request, name="author-books.html", context={"author": author})