from ast import parse
from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory
from gevent.pywsgi import WSGIServer
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import re
from ..global_names import datapath
from .utils import getEpubMetadata, allowed_file
from PyQt5.QtCore import QStandardPaths, QCoreApplication, QObject
from pathlib import Path
import ebooklib
DEBUGGING = None
if os.environ.get("VOCABSIEVE_DEBUG"):
    DEBUGGING = True
    QCoreApplication.setApplicationName(
        "VocabSieve" + os.environ.get("VOCABSIEVE_DEBUG", ""))
else:
    QCoreApplication.setApplicationName("VocabSieve")
QCoreApplication.setOrganizationName("FreeLanguageTools")

Path(datapath).mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER = os.path.join(datapath, "uploads")
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

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
            books_dir = self.parent.settings.value("books_dir")
            book_files = []
            books = []
            if books_dir:
                for file in os.listdir(books_dir):
                    if file.endswith(".epub"):
                        book_files.append(file)
            for book in book_files:
                metadata = getEpubMetadata(os.path.join(books_dir, book))
                metadata['path'] = book
                books.append(metadata)
            return render_template('home.html', books=books)
        
        @app.route('/read/<path:path>')
        def read_epub(path):
            book_url = url_for('send_epub', path=path)
            return render_template('read.html', book_url=book_url)
        
        @app.route('/books/<path:path>')
        def send_epub(path):
            books_dir = self.parent.settings.value("books_dir")
            if not books_dir:
                return "No books directory set"
            return send_from_directory(books_dir, path)

        
        http_server = WSGIServer((self.host, self.port), app)
        http_server.serve_forever()



if __name__ == '__main__':
    http_server = WSGIServer(("127.0.0.1", "8000"), app)
    http_server.serve_forever()
    
