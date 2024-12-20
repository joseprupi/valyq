from flask import jsonify
from werkzeug.exceptions import HTTPException
from domain.exceptions.validation_exceptions import ValidationError

def init_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        print(e)
        return jsonify({'error': str(e)}), 400

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        print(e)
        return jsonify({'error': str(e)}), e.code

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        print(e)
        return jsonify({'error': 'Internal server error'}), 500