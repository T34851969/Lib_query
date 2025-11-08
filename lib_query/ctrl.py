from .db.core import LibraryDatabase
from .db.search import TitleSearch, CallNumberPieceSearch, CallNumberSearch, ISBNSearch

class CentreCrtl:
    def __init__(self, db_path):
        self.db_path = LibraryDatabase.return_path()

    def on_title_single(self, title, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return TitleSearch.search(conn, title, fmt)

    def on_title_batch(self, key, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return TitleSearch.batch_search(conn, key, fmt)

    def on_ISBN_single(self, ISBN, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return ISBNSearch.search(conn, ISBN, fmt)

    def on_ISBN_batch(self, key, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return ISBNSearch.batch_search(conn, key, fmt)

    def on_call_num_piece_single(self, piece, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return CallNumberPieceSearch.search(conn, piece, fmt)

    def on_call_num_piece_batch(self, key, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return CallNumberPieceSearch.batch_search(conn, key, fmt)

    def on_call_num_single(self, call_num, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return CallNumberSearch.search(conn, call_num, fmt)

    def on_call_num_batch(self, key, fmt):
        with LibraryDatabase(self.db_path) as conn:
            return CallNumberSearch.batch_search(conn, key, fmt)
    
    def get_recs(self):
        return LibraryDatabase.all_records()
    
    def get_path(self):
        return self.db_path