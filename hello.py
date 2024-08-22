import os
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests

basedir = os.path.abspath(os.path.dirname(__file__))

API_KEY = os.getenv("API_KEY")
MAILGUN_DOMAIN = os.getenv("DOMAIN")
MAILGUN_API_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
RECIPIENTS = ['flaskaulasweb@zohomail.com', 'freitas.alves@aluno.ifsp.edu.br', 'daniel.a49.freitas@gmail.com']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


def send_email(username):


    print(f"API KEY: {API_KEY}", flush=True)
    print(f"DOMAIN: {MAILGUN_DOMAIN}", flush=True)
    print(f"MAILGUN_API_URL: {MAILGUN_API_URL}", flush=True)

    return requests.post(
        MAILGUN_API_URL,
        auth=("api", API_KEY),
        data={
            "from": f"Flasky App <mailgun@{MAILGUN_DOMAIN}>",
            "to": RECIPIENTS,
            "subject": "Novo usuário registrado!",
            "text": f"Um novo usuário foi registrado: {username}"
        }
    )


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username=form.name.data).first()

        if user is None:

            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False

        else:

            session['known'] = True

        session['name'] = form.name.data

        send_email(user.username)

        return redirect(url_for('index'))

    users = User.query.all()

    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False), users=users)