import os

from flask import Flask

def create_app(test_config = None): 

    app = Flask(__name__, instance_relative_config = True)
    app.config.from_mapping(
        SECRET_KEY = 'dev',
        # DATABASE = "/var/local/temp-logger/temps.db"
        DATABASE = os.path.join(app.instance_path, 'logger_data.db')
    )

    app.config.from_prefixed_env()
    
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else: 
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import logger_server
    logger_server.run_server_in_background()
    
    from . import plot
    app.register_blueprint(plot.bp)
    app.add_url_rule('/', endpoint='index')

    return app