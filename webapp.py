"""
Flask web application serving the whoistel user interface, 
handling number lookups and community spam reporting.
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_wtf import CSRFProtect
import history_manager
import whoistel

csrf = CSRFProtect()
MAX_COMMENT_LENGTH = 1024

def create_app(test_config=None):
    """
    Application factory for the Flask web UI.
    Initializes configuration, CSRF protection, and database schema.
    """
    app = Flask(__name__)
    
    if test_config:
        app.config.update(test_config)
    else:
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
        if not app.config['SECRET_KEY']:
            # In production, this is mandatory.
            raise ValueError("Environment variable SECRET_KEY must be set.")

    csrf.init_app(app)

    # Note: Template filters, error handlers, and routes are registered here
    # to avoid import-time side effects (like DB initialization).

    @app.template_filter('format_datetime')
    def format_datetime(value, format='%d/%m/%Y %H:%M'):
        """Jinja2 filter to format datetime objects or ISO strings."""
        if not value:
            return ""

        dt_obj = None
        if isinstance(value, datetime):
            dt_obj = value
        elif isinstance(value, str):
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    dt_obj = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    pass
            else:
                app.logger.warning(f"Could not parse datetime string: '{value}'")

        return dt_obj.strftime(format) if dt_obj else ""

    def _get_db(name, connect_func):
        """
        Retrieves or creates a database connection for the current request context.
        Uses Flask's g object to cache connections and registers them for teardown.
        """
        db = getattr(g, name, None)
        if db is None:
            db = connect_func()
            setattr(g, name, db)
            # Scalable registry for teardown
            if not hasattr(g, 'db_connections'):
                g.db_connections = []
            g.db_connections.append(db)
        return db

    @app.teardown_appcontext
    def close_dbs(_error):
        """Closes all database connections at the end of the request."""
        for conn in getattr(g, 'db_connections', []):
            try:
                conn.close()
            except Exception:
                app.logger.error("Error closing database connection during teardown.")

    @app.errorhandler(whoistel.DatabaseError)
    def handle_db_error(e):
        """Global handler for DatabaseError exceptions."""
        app.logger.error(f"Database error: {e}")
        return render_template('error.html', message="Database error occurred"), 500

    @app.route('/', methods=['GET'])
    def index():
        """Renders the landing page with the search form."""
        return render_template('index.html')

    @app.route('/check', methods=['POST'])
    def check():
        """Validates the input number and redirects to the view page."""
        raw_tel = request.form.get('number')
        if not raw_tel:
            flash("Veuillez saisir un numéro.", "error")
            return redirect(url_for('index'))

        tel = whoistel.clean_phone_number(raw_tel)
        if not whoistel.is_valid_phone_format(tel):
            flash("Le numéro de téléphone est invalide. Il doit contenir exactement 10 chiffres (ex: 0123456789).", "error")
            return redirect(url_for('index'))

        return redirect(url_for('view_number', number=tel))

    @app.route('/view/<number>', methods=['GET'])
    def view_number(number):
        """Displays information and history for a specific phone number."""
        cleaned_number = whoistel.clean_phone_number(number)
        
        if not whoistel.is_valid_phone_format(cleaned_number):
            return render_template('error.html', message="Le format du numéro est invalide."), 400

        if cleaned_number != number:
            return redirect(url_for('view_number', number=cleaned_number))

        conn = _get_db('main_db', whoistel.setup_db_connection)
        result = whoistel.get_full_info(conn, cleaned_number)
        spam_count = history_manager.get_spam_count(cleaned_number, conn=_get_db('history_db', history_manager.get_db_connection))

        return render_template('result.html', result=result, spam_count=spam_count, number=cleaned_number)

    @app.route('/report', methods=['POST'])
    def report():
        """Handles submission of spam reports and comments."""
        number = whoistel.clean_phone_number(request.form.get('number'))
        if not number:
             flash("Veuillez saisir un numéro.", "error")
             return redirect(url_for('index'))

        # Validate number format early to fail fast
        if not whoistel.is_valid_phone_format(number):
            flash("Erreur interne : Numéro de téléphone invalide lors du signalement.", "error")
            return redirect(url_for('view_number', number=number))

        date = request.form.get('date')
        is_spam = request.form.get('is_spam') == 'on'
        
        raw_comment = (request.form.get('comment') or '').strip()
        if len(raw_comment) > MAX_COMMENT_LENGTH:
            flash(f"Votre commentaire a été tronqué à {MAX_COMMENT_LENGTH} caractères.", "info")
        comment = raw_comment[:MAX_COMMENT_LENGTH]

        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                flash(f"Le format de la date '{date}' est invalide (attendu: AAAA-MM-JJ).", "error")
                return redirect(url_for('view_number', number=number))
        else:
            date = None

        if not is_spam and not comment and not date:
            flash("Veuillez cocher la case spam, ajouter un commentaire ou une date.", "error")
            return redirect(url_for('view_number', number=number))

        history_manager.add_report(number, date, is_spam, comment, conn=_get_db('history_db', history_manager.get_db_connection))
        flash("Signalement enregistré.", "success")
        return redirect(url_for('view_number', number=number))

    @app.route('/history', methods=['GET'])
    def history():
        """Displays the list of recent spam reports."""
        reports = history_manager.get_recent_reports(conn=_get_db('history_db', history_manager.get_db_connection))
        return render_template('history.html', reports=reports)

    # Initialize history database schema if needed
    with app.app_context():
        history_manager.init_history_db()

    return app

if __name__ == '__main__':
    app = create_app()
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)
