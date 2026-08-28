from pathlib import Path

from fastapi import Depends, FastAPI, Request
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
    template = "books.html" if request.headers.get("HX-Request") else "books-page.html"
    return templates.TemplateResponse(request=request, name=template, context={"books": library})


@app.get("/autores", response_class=HTMLResponse)
def authors(request: Request, db: Session = Depends(get_db)):
    library_authors = db.query(Author).order_by(Author.name).all()
    return templates.TemplateResponse(request=request, name="authors.html", context={"authors": library_authors})