
__author__ = 'ed'
from flask import g, render_template, flash, redirect, url_for, abort

from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import app.models
from app import forms, models
from app import app, db
from .forms import LoginForm, EditForm
from .models import User




app.secret_key = 'Bacon'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except ValueError:
        return None


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()




@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        flash("Yay, you registered", "Success")
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=('GET', 'POSt'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password or name dont work", 'error')
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("youve been logged in", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password or name dont work", 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("you have been logged out")
    return redirect(url_for('index'))


@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(user=g.user._get_current_object(),
                           content=form.content.data.strip())
        flash("Posted!")
        return redirect(url_for('index'))
    return render_template('post.html', form=form)

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    posts = [
        {
            'author': {'nickname': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'nickname': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html',
                           title='Home',
                           user=user,
                           posts=posts)




@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
    template = 'stream.html'

    if current_user.is_anonymous():
        return redirect(url_for('register'))

    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username**username).get()


        except models.DoesNotExist:
            abort(404)
        else:
            stream = user.posts


    else:
        user = current_user
        stream = current_user.posts


    if username != current_user:
        template = 'user_stream.html'

    return render_template(template, stream=stream, user=user)


@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        pass
    else:
        try:
            models.Releationship.create(
                from_user=g.user._get_current_object(),
                to_user=to_user
            )
        except models.IntegrityError:
            print("messed up")
        else:
            flash("your now follow {}!".format(to_user.username), "success")
        return redirect(url_for('stream', username=to_user.username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Releationship.get(
                from_user=g.user._get_current_object(),
                to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            abort(404)
        else:
            flash("your now dont like or follow {}!".format(to_user.username), "success")
        return redirect(url_for('stream', username=to_user.username))



@app.route('/post/<int:post_id>')
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template('stream.html', stream=posts)



@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404





if __name__ == '__main__':
    models.initiliaze()
    try:
        models.User.create_user(
            username='Edwin',
            email='edwin@gmail.com',
            password='password',
            admin=True
        )
    except ValueError:
        pass
