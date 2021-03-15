from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import CreateUserForm, LoginUserForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from secret import secret_key

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = secret_key
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    return redirect("/register")


@app.route('/register', methods=["GET", "POST"])
def register_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name,
                                 last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append(
                "Username or Email taken, please pick another")
            return render_template("register.html", form=form)
        session['username'] = new_user.username
        flash('Welcome!')
        return redirect(f'/users/{new_user.username}')

    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login_user():
    form = LoginUserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}")
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password']

    return render_template('login.html', form=form)


@app.route('/users/<username>')
def user_home(username):
    if "username" not in session:
        flash("Please login first!")
        return redirect("/")

    user = User.query.filter_by(username=username).first()
    feedback = Feedback.query.filter_by(username=username).all()

    if user:
        return render_template("user.html", user=user, feedback=feedback)
    else:
        flash("That User does not exist!!")
        return redirect('/')


@app.route('/users/<username>/delete')
def delete_user(username):
    if "username" not in session:
        flash("Please login first!")
        return redirect("/")

    if session['username'] != username:
        flash("Wrong user")
        return redirect("/")

    User.query.filter_by(username=username).delete()
    db.session.commit()
    flash("User deleted!")
    return redirect('/')


@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    if "username" not in session:
        flash("Please login first!")
        return redirect("/")

    if session['username'] != username:
        flash("Wrong user")
        return redirect("/")

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(username=username, title=title, content=content)

        db.session.add(feedback)
        db.session.commit()
        flash("Feedback added!")
        return redirect(f'/users/{username}')
    elif request.method == 'POST':
        flash("Double check feedback and send again")
    return render_template("feedback.html", form=form)


@app.route('/feedback/<feedback_id>/update', methods=["GET", "POST"])
def edit_feedback(feedback_id):
    if "username" not in session:
        flash("Please login first!")
        return redirect("/")

    feedback = Feedback.query.get_or_404(feedback_id)

    if session['username'] != feedback.username:
        flash("Wrong user")
        return redirect("/")

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()
        flash("Feedback edited!")
        return redirect(f'/users/{feedback.username}')
    elif request.method == 'POST':
        flash("Double check feedback and send again")
    return render_template("edit_feedback.html", form=form)


@app.route('/feedback/<feedback_id>/delete', methods=["GET", "POST"])
def delete_feedback(feedback_id):
    if "username" not in session:
        flash("Please login first!")
        return redirect("/")

    feedback = Feedback.query.get_or_404(feedback_id)

    if session['username'] != feedback.username:
        flash("Wrong user")
        return redirect("/")

    Feedback.query.filter_by(id=feedback_id).delete()
    db.session.commit()
    flash("Feedback deleted!")
    return redirect(f"/users/{session['username']}")


@app.route('/logout', methods=["POST"])
def logoout_user():
    session.pop('username')
    flash('Goodbye!')
    return redirect('/')