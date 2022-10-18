from flask import Flask, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from markdown import markdown
import os
import re
from .utils import *
from PyQt5.QtCore import QStandardPaths, QCoreApplication, QObject
from pathlib import Path
# The following import is to avoid cxfreeze error
import sqlalchemy.sql.default_comparator
DEBUGGING = None
if os.environ.get("VOCABSIEVE_DEBUG"):
    DEBUGGING = True
    QCoreApplication.setApplicationName(
        "VocabSieve" + os.environ.get("VOCABSIEVE_DEBUG", ""))
else:
    QCoreApplication.setApplicationName("VocabSieve")
QCoreApplication.setOrganizationName("FreeLanguageTools")

datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
Path(datapath).mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER = os.path.join(datapath, "uploads")
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


def create_flaskapp():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['SECRET_KEY'] = "abc"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{datapath}/reader.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    return app

app = create_flaskapp()


with app.app_context():
    db = SQLAlchemy(app)

    class Text(db.Model):  # type: ignore[name-defined]
        added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        last = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        id = db.Column(db.Integer, primary_key=True)
        archived = db.Column(db.Boolean, nullable=False, default=False)
        title = db.Column(db.String(180), nullable=False)
        author = db.Column(db.String(180))
        content = db.Column(db.Text, nullable=False)
        progress = db.Column(db.Integer, nullable=False, default=0)
        length = db.Column(db.Integer, nullable=False)

        def __repr__(self):
            return f"Text(ID={self.id}, Title={self.title})"

    db.create_all()

class ReaderServer(QObject):
    def __init__(self, parent, host, port):
        super(ReaderServer, self).__init__()
        self.host = host
        self.port = port
        self.parent = parent

    def start_api(self):
        """ Main server application """

        @app.route("/home")
        @app.route("/")
        def home():
            texts = Text.query.all()
            return render_template('home.html', texts=texts)

        @app.route("/read/<int:id>")
        def read(id):
            text = Text.query.get(id)
            return render_template("page.html",
                                   text=text,
                                   font=self.parent.settings.value("reader_font", 'serif'),
                                   size=self.parent.settings.value("reader_fontsize", 14, type=int),
                                   color=self.parent.settings.value("reader_hlcolor", '#66bb77')
                                   )

        @app.route("/update/<int:id>", methods=['POST'])
        def update_progress(id):
            if request.form and request.form.get('progress'):
                # keep values between 0 and 1 million
                prog = min(int(float(request.form.get('progress'))), 1_000_000)
                prog = max(prog, 0)
                text = Text.query.get(id)
                text.progress = int(prog)
                db.session.commit()
                return "ok"
            return "bad"

        @app.route("/upload", methods=['GET', 'POST'])
        def upload():
            if request.method == 'POST':
                # check if the post request has the file part
                if 'file' not in request.files:
                    if request.form.get('title') and request.form.get('text'):
                        new_item = Text(
                            title=request.form.get('title'),
                            content="\n".join([
                                f"<p>{item}</p>"
                                for item in
                                request.form.get('text').splitlines()
                            ]),
                            length=len(
                                re.findall(
                                    r'\w+',
                                    request.form.get('text'))))
                        db.session.add(new_item)
                        db.session.commit()
                        return redirect(url_for('home'))
                    else:
                        return redirect(request.url)

                file = request.files['file']
                # If the user does not select a file, the browser submits an
                # empty file without a filename.
                if file.filename == '':
                    flash('No selected file')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(
                        fpath := os.path.join(
                            app.config['UPLOAD_FOLDER'],
                            filename))
                    add_book(parseBook(fpath))
                    return redirect(url_for('home'))
                else:
                    flash('Extension not allowed.')
            return render_template('upload.html')

        @app.route("/delete/<int:id>", methods=['DELETE'])
        def delete(id):
            Text.query.filter_by(id=id).delete()
            db.session.commit()
            return ('', 204)

        app.run(
            debug=False,
            use_reloader=False,
            host=self.host,
            port=self.port)


def add_book(book_obj):
    chapters = (("\n" * 16).join(book_obj['chapters']))  # .replace(r"<h2>", r'<h2 class="title is-2">')
    new_item = Text(title=book_obj['title'],
                    author=book_obj['author'],
                    content=chapters,
                    length=len(re.findall(r'\w+', chapters)))
    db.session.add(new_item)
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
