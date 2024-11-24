# app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    is_borrowed = db.Column(db.Boolean, default=False)
    history = db.relationship('BorrowingHistory', backref='book', cascade='all, delete-orphan', lazy=True)

class BorrowingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)



@app.route('/')
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        category = request.form['category']
        year = request.form['year']
        isbn = request.form['isbn']
        book = Book(title=title, author=author, category=category, year=year, isbn=isbn)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_book.html')

@app.route('/borrow/<int:book_id>')
def borrow(book_id):
    book = Book.query.get_or_404(book_id)
    if not book.is_borrowed:
        book.is_borrowed = True
        history = BorrowingHistory(book_id=book_id)
        db.session.add(history)
        db.session.commit()
        flash('Book borrowed successfully!', 'success')
    else:
        flash('Book is already borrowed.', 'danger')
    return redirect(url_for('index'))

@app.route('/return/<int:book_id>')
def return_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.is_borrowed:
        book.is_borrowed = False
        history = BorrowingHistory.query.filter_by(book_id=book_id, return_date=None).first()
        if history:
            history.return_date = datetime.utcnow()
            db.session.commit()
        flash('Book returned successfully!', 'success')
    else:
        flash('Book is not currently borrowed.', 'danger')
    return redirect(url_for('index'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q', '')
    results = []
    if query:
        results = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%')) |
            (Book.isbn.ilike(f'%{query}%'))
        ).all()
    return render_template('search.html', query=query, results=results)


@app.route('/categories')
def categories():
    categories = db.session.query(Book.category).distinct().all()
    return render_template('categories.html', categories=[cat[0] for cat in categories])

@app.route('/category/<string:category>')
def books_by_category(category):
    books = Book.query.filter_by(category=category).all()
    return render_template('category_books.html', category=category, books=books)

@app.route('/history')
def history():
    history_records = BorrowingHistory.query.order_by(BorrowingHistory.borrow_date.desc()).all()
    return render_template('history.html', history_records=history_records)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash(f'Book "{book.title}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting the book: {e}', 'danger')
    return redirect(url_for('index'))