Inflaskart
==========

'Inflaskart' is a work-in-progress clone of Instacart implemented using Django,
ie. it is an online grocery shopping application.

An SQLite database (sqlite3) is used to store the model instances.

The display is implemented using Bootstrap, plus an external style sheet.

To configure another database, please read the following documentation:
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
    - a static folder (containing a very basic style sheet)

+ requirements.txt


How does it work
----------------
In order to be able to use Inflaskart (locally) to shop, you need to:

1. Clone this repository

2. Open the terminal and navigate to this repository. You can install the required
modules/applications using the following command:
    ```sh
    pip install -r requirements.txt
    ```

3. Create your database tables based on the application models (NB: the application
is called 'grocerystore').
In order to do that, navigate to this repository and create your database migrations:
    ```sh
    python manage.py makemigrations grocerystore
    ```
Then run the following command to apply the migrations to the database:
    ```sh
    python manage.py migrate
    ```

4. In the terminal, navigate to the inflaskart project directory, and run its
server by typing in the following command:
    ```sh
    python manage.py runserver
    ```
By default, the server will run locally on port 8000.
Now you can access the index page of your web app in your browser with the URL:
'localhost:8000/grocerystore/‘

5. In order to be able to create products and stores instances to play with this
application, you need to create an admin profile:
    ```sh
    python manage.py createsuperuser
    ```
Then you will be prompted for your email address and password.
More info: https://docs.djangoproject.com/en/1.10/intro/tutorial02/#introducing-the-django-admin

6. You can access the admin page in your browser by typing in the following URL:
'localhost:8000/admin/‘
The more stores, products and availabilities you create, the better!
(don't forget to create state instances as well)

7. Then access the Inflaskart index page in your browser on
'localhost:8000/grocerystore/‘, and have fun!


How to run the tests
--------------------
In the command line, navigate to the project directory (not the app one), then
enter the following command:
  ```sh
  python manage.py test
  ```


Room for improvement
--------------------
This project is still under development:
- the style sheet is still a little basic
- need to implement a way to verify a user's email address;
- need to implement a way to allow the user to check their password when signing
up (ie: entering it twice);
- need to implement a way to allow the user to change their password;
- need to implement a way to store the user's credit card information securely;
- need to implement orders history;
- need to properly implement the checkout process.

Nota Bene: The user's cart is meant to hold ALL the items the user puts in their
cart, ie. items from different stores if the user shops in different stores.
Should the users put larger quantities of items than expected in their cart, it
would be necessary to have a cart per store and hence change the URL distribution,
and the models and views files accordingly.


Requirements
------------
Django 1.10.6
Pillow 4.0.0 (for images)
