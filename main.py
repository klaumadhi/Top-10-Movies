
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

MOVIE_DB_API_KEY = "c6bce38c9b9ddfcfe4fd6868382fd841"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjNmJjZTM4YzliOWRkZmNmZTRmZDY4NjgzODJmZDg0MSIsInN1YiI6IjY0NzljODJlMTc0OTczMDExODcwMzAwZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vKQAxHKZIjVm9IXEt9Dq1Xwr_Fs9e0_VsDN_HYjWIog"
}





app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

##CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-10-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()


##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
db.create_all()


@app.route("/")
def home():
    # Retrieve all movies from the database and order them by rating
    all_movies = Movie.query.order_by(Movie.rating).all()
    # Update the ranking of each movie based on its position in the ordered list
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    # Commit the session to save the updated rankings in the database
    db.session.commit()
    # Render the "index.html" template and pass the retrieved movies as a variable
    return render_template("index.html", movies=all_movies)

#Create Form
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    #Get movie ID
    movie_id = request.args.get("id")
    #Get the row same as  SELECT * FROM movies WHERE id = movie_id
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        #Get the input from form in edit.html by user
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete")
def delete():
    # Get the row same as  SELECT * FROM movies WHERE id = movie_id
    movie_id = request.args.get("id")
    # Delete the row with the same id
    Movie.query.filter_by(id=movie_id).delete()
    db.session.commit()
    return redirect(url_for('home'))

#Create Form
class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title}, headers=headers)
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        # Construct the URL to fetch movie information from the API
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        # Make a GET request to the movie API
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"}, headers=headers)
        # Parse the response JSON data
        data = response.json()
        # Create a new Movie object with the retrieved data
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        # Add the new movie to the database session
        db.session.add(new_movie)
        # Commit the session to save the new movie in the database
        db.session.commit()
        # Redirect to the "rate_movie" route, passing the new movie's ID as a parameter
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=7001)
