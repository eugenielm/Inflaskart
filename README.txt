HOW TO USE INFLASKART GROCERY SHOPPING APP

In order for a user to be able to use Inflaskart to shop, you must first run the flask server.
To do that, in the parent directory there's a directory named inflaskart-backend: follow its readme file instructions.
Then the backend server is gonna run on '127.0.0.1:5000'.

Second step: in the terminal make the project inflaskart directory the cwd, and then you can run its server by typing:
python manage.py runserver
By default, it runs on '127.0.0.1:8000'.

And then access the index page in your webrowser by typing '127.0.0.1:8000/grocerystore/'

Room for improvement:
- improve the search engine: if some characters match + accept " "
- login required mixin in the views.CheckoutView : how does the next request query parameter works, so that the redirection is effective?
