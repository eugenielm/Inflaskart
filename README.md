Inflaskart
==========

'Inflaskart' is a clone of Instacart. It is an online grocery shopping application
implemented using Django web framework. An external server and a levelDB database
are used for cart persistence.
This project is still under development especially the templates (there aren't
any style sheets yet either).

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
    - a migrations folder
    - a templates folder - work in progress!
    - inflaskart_api.py: module containing the class whose instances are used
    to interact with the cart server (for cart persistence)

+ requirements.txt


How does it work
----------------
1. In order to be able to use Inflaskart to shop (locally), you first need to
run a(n) (external) server for cart persistence.
To do that you can clone one of the 2 repositories below and follow its README
instructions:
- Flask server: https://github.com/eugenielm/Inflaskart-backend-PY-.git
- JavaScript server: https://github.com/eugenielm/Inflaskart-backend-JS-.git

2. Clone this repository

3. Navigate to this repository in the terminal. You can install the required
modules or applications using the following command:
    ```sh
    python requirements.txt
    ```

4. Then in the terminal navigate to the inflaskart project directory, and run
its server by typing in the following command:
    ```sh
    python manage.py runserver
    ```
By default, the server will run locally on port 8000.


Now you can access the index page of your web app in your browser with the URL:
'localhost:8000/grocerystore/‘
The admin page is accessible via the following URL: 'localhost:8000/admin/‘


Requirements
------------
Django 1.10.6
levelDB 0.20 (for cart persistence)
requests 2.13.0 (for inflaskart_api)
Pillow 4.0.0 (for images)
