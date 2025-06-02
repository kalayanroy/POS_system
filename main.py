from app import app, db
from app.models import User, Product, Purchase, Sale # Add Sale

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'Purchase': Purchase, 'Sale': Sale} # Add Sale
