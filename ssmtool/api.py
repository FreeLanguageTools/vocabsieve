from flask import Flask, request
from PyQt5.QtCore import *
from .dictionary import *
from .db import Record
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

class LanguageServer(QObject):
    note_signal = pyqtSignal(str, str, str, list)
    def __init__(self, parent, host, port):
        super(LanguageServer, self).__init__()
        self.host = host
        self.port = port
        self.parent = parent
        
    def start_api(self):
        """ Main server application """
        self.app = Flask(__name__)
        self.settings = QSettings("FreeLanguageTools", "SimpleSentenceMining")
        @self.app.route("/healthcheck")
        def healthcheck():
            return "Hello, World!"

        @self.app.route("/version")
        def version():
            return str(1)

        @self.app.route("/define/<string:word>")
        def lookup(word):
            use_lemmatize = str2bool(request.args.get("lemmatize", "True")) 
            return self.parent.lookup(word, use_lemmatize)
            
        @self.app.route("/translate", methods=["POST"])
        def translate():
            lang = request.args.get("src") or code[self.settings.value("target_language")]
            gtrans_lang = request.args.get("dst") or code[self.settings.value("gtrans_lang")]
            return {
                    "translation": googletranslate(request.json.get("text"), lang, gtrans_lang)['definition'], 
                    "src": lang, 
                    "dst": gtrans_lang}

        @self.app.route("/createNote", methods=["POST"])
        def createNote():
            data = request.json
            self.note_signal.emit(data['sentence'], data['word'], data['definition'], data['tags'])
            return "success"
        
        @self.app.route("/stats")
        def stats():
            rec = Record()
            return str(f"Today: {rec.countLookupsToday()} lookups, {rec.countNotesToday()} notes")

        @self.app.route("/lemmatize/<string:word>")
        def lemmatize(word):
            return lem_word(word, code[self.settings.value("target_language")])

        @self.app.route("/logs")
        def logs():
            rec = Record()
            return "\n".join([" ".join([str(i) for i in item]) for item in rec.getAll()][::-1])


        self.app.run(debug=False, use_reloader=False, host=self.host, port=self.port)

if __name__ == "__main__":
    server = LanguageServer()
    server.start_api()