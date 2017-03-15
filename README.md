Inflaskart
==========

'Inflaskart' is a work-in-progress clone of Instacart. It is an online grocery
shopping application implemented using Django web framework.

It needs 2 servers and 2 databases to work properly:
- a Django-implemented server (that runs locally) associated with a relational
database (by default: SQLite) for products/stores and user information;
- another server associated with a non relational database (here: levelDB) for
cart persistence.

To configure another Django database, please read the following documentation:
https://docs.djangoproject.com/en/1.10/intro/tutorial02/
https://docs.djangoproject.com/en/1.10/topics/install/#database-installation


More about Django web framework: https://docs.djangoproject.com/en/1.10/


Repository content
------------------
+ manage.py: implements the Django command-line utility for administrative tasks

+ inflaskart = the Django project package containing the scripts below:
    - __init__.py
    - settings.py
    - urls.py
    - wsgi.py

+ grocerystore = the Django app package containing the scripts below:
    - __init__.py
    - admin.py
    - apps.py
    - forms.py
    - models.py
    - tests.py
    - urls.py
    - views.py
    - a migrations folder (containing only __init__.py)
    - a templates folder
    - inflaskart_api.py: module containing the class used to interact with the
    cart server (for cart persistence) and functions used in views.py

+ requirements.txt


How does it work
----------------
1. In order to be able to use Inflaskart (locally) to shop, you first need to
run the server used for cart persistence.
To do that you can clone one of the two repositories below and follow its README
instructions:
- Flask server: https://github.com/eugenielm/Inflaskart-backend-PY-.git
- JavaScript server: https://github.com/eugenielm/Inflaskart-backend-JS-.git

2. Clone this repository

3. Open the terminal and navigate to this repository. You can install the required
modules/applications using the following command:
    ```sh
    python requirements.txt
    ```

4. Create your database tables based on the application models (NB: the application
is 'grocerystore').
In another terminal window, navigate to this repository and create migrations:
    ```sh
    python manage.py makemigrations grocerystore
    ```
Then run the following command to apply the migrations to the database:
    ```sh
    python manage.py migrate
    ```

5. Then in the terminal navigate to the inflaskart project directory, and run
its server by typing in the following command:
    ```sh
    python manage.py runserver
    ```
By default, the server will run locally on port 8000.
Now you can access the index page of your web app in your browser with the URL:
'localhost:8000/grocerystore/‘

6. In order to be able to create products and stores instances to play with this
application, you need to create an admin profile:
    ```sh
    python manage.py createsuperuser
    ```
Then you will be prompted for your email address and password.
More info: https://docs.djangoproject.com/en/1.10/intro/tutorial02/#introducing-the-django-admin

7. You can access the admin page in your browser by typing in the following URL:
'localhost:8000/admin/‘
You need to create plenty of stores, products and availabilities.

8. Then access your index page in your browser on 'localhost:8000/grocerystore/‘,
and have fun!


Room for improvement
--------------------
This project is still under development:
- the templates need to be structured using proper HTML5 (+ style sheets);
- need to implement a way to verify a user's email address;
- need to implement a way to allow the user to change their password;
- need to implement a way to store the user's credit card information securely;
- need to properly implement the checkout process.


Requirements
------------
Django 1.10.6
levelDB 0.20 (for cart persistence)
requests 2.13.0 (for inflaskart_api)
Pillow 4.0.0 (for images)
