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
        if name not in g:
            setattr(g, name, connect_func())
        return getattr(g, name)

    @app.teardown_appcontext
    def close_dbs(_error):
        """Closes all database connections at the end of the request."""
        history_db = g.pop('history_db', None)
        if history_db is not None:
            history_db.close()
        
        main_db = g.pop('main_db', None)
        if main_db is not None:
            main_db.close()

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
        if not tel.isdigit():
            flash("Le numéro de téléphone est invalide. Il ne doit contenir que des chiffres.", "error")
            return redirect(url_for('index'))

        return redirect(url_for('view_number', number=tel))

    @app.route('/view/<number>', methods=['GET'])
    def view_number(number):
        """Displays information and history for a specific phone number."""
        cleaned_number = whoistel.clean_phone_number(number)
        
        if not cleaned_number.isdigit():
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
        date = request.form.get('date')
        is_spam = request.form.get('is_spam') == 'on'
        comment = (request.form.get('comment') or '').strip()[:MAX_COMMENT_LENGTH]

        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                flash(f"Le format de la date '{date}' est invalide (attendu: AAAA-MM-JJ).", "error")
                return redirect(url_for('view_number', number=number))
        else:
            date = None

        if number:
            if not is_spam and not comment and not date:
                flash("Veuillez cocher la case spam, ajouter un commentaire ou une date.", "error")
                return redirect(url_for('view_number', number=number))

            history_manager.add_report(number, date, is_spam, comment, conn=_get_db('history_db', history_manager.get_db_connection))
            flash("Signalement enregistré.", "success")
            return redirect(url_for('view_number', number=number))
        return redirect(url_for('index'))

    @app.route('/history', methods=['GET'])
    def history():
        """Displays the list of recent spam reports."""
        reports = history_manager.get_recent_reports(conn=_get_db('history_db', history_manager.get_db_connection))
        return render_template('history.html', reports=reports)

    # Initialize history database schema if needed
    with app.app_context():
        history_manager.init_history_db()

    return app

# Legacy global app object for backward compatibility with tools and tests
# This now triggers create_app() which is safe if called through a runner.
# However, to avoid the side-effect on import entirely, tests should use create_app().
# We'll keep 'app' here but wrap it so it's not accidental?
# Actually, if we want NO side effects, we should remove it.
# But Gunicorn might need it.

if __name__ == '__main__':
    app = create_app()
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)
