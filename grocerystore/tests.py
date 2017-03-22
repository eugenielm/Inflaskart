#-*- coding: UTF-8 -*-
import sys
import urllib
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser, User
from .models import State, Address, Inflauser, Zipcode,  Store, ProductCategory,\
                    ProductSubCategory, Dietary, Product, Availability
from .views import UserRegisterView, UserLoginView, logout, ProfileView,\
                   ProfileUpdateView, IndexView, StartView, StoreView, \
                   SubcategoriesList, InstockList, SearchView, CartView,\
                   ProductDetailView, CheckoutView
from .forms import LoginForm, PaymentForm, SelectCategory, UserForm, AddressForm
from inflaskart_api import InflaskartClient, get_flaskcart, search_item, remove_old_items


"""
The following class tests need to be updated/implemented:
- UserRegisterViewTest
- UserLoginViewTest
- CartViewTest
- SearchViewTest
- ProductDetailViewTest
- ProfileViewTest
- ProfileUpdateViewTest

To be checked:
- InstockListTest: url redirection in test_post_when_inactive_logged_in_user()
"""


class SearchItemTest(TestCase):

    def setUp(self):
        # create 1 state
        self.test_state = State.objects.create(state_name="Brittany")
        # create 1 store
        self.test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_zipcode=22600, store_state=self.test_state)
        # create 2 products
        self.test_category = ProductCategory.objects.create(top_category='Alcohol')
        self.test_subcategory = ProductSubCategory.objects.create(parent=self.test_category, sub_category_name='Beer')
        self.test_product1 = Product.objects.create(product_name='Lager beer', product_category=self.test_subcategory, product_brand_or_variety='Anchor steam', user_id_required=True)
        self.test_product2 = Product.objects.create(product_name='Non alcoholic beer', product_category=self.test_subcategory)
        # create 2 availabilities in store1
        self.test_availability1 = Availability.objects.create(product=self.test_product1, store=self.test_store, product_unit='6x12floz', product_price=7.89)
        self.test_availability2 = Availability.objects.create(product=self.test_product2, store=self.test_store, product_unit='8x12floz', product_price=10.49)

    def test_search_item(self):
        """Checks if it returns a list of Availability instances"""
        res1 = search_item('BEeR', self.test_store.pk)
        res2 = search_item('anchor', self.test_store.pk)
        self.assertIs(type(res1), list)
        self.assertIs(len(res1), 2)
        self.assertIsInstance(res1[0], Availability)
        self.assertIs(len(res2), 0)


class GetFlaskcartTest(TestCase):
    def setUp(self):
        self.test_username = 'Eugénie'
        self.test_host = 'http://localhost:5000'

    def test_get_flaskuser(self):
        """Checks if it returns the right InflaskartClient instance"""
        test_flaskcart = get_flaskcart(self.test_username, self.test_host)
        self.assertIsInstance(test_flaskcart, InflaskartClient)


class IndexViewTest(TestCase):

    def setUp(self):
        # create 1 inflauser
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_address = Address.objects.create(street_adress1="2, Quilliampe", city="Loudéac", zip_code=22600, state=self.test_state)
        self.test_inflauser = Inflauser.objects.create(infla_user=self.test_user, inflauser_address=self.test_address)
        self.client = Client()

    def test_get_with_authenticated_user(self):
        """Checks redirection if the user is authenticated"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:index'))
        self.assertRedirects(response, reverse('grocerystore:start', kwargs={'zipcode': 22600}), status_code=302, target_status_code=200)

    def test_get_with_anonymous_user(self):
        """Checks that there's a form to choose a zipcode"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/index.html')

        self.assertContains(response, 'enter a ZIP code')
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, 'Welcome to Inflaskart!')
        self.assertContains(response, 'Inflaskart is a revolutionary app')

    def post(self):
        response1 = self.client.post(reverse('grocerystore:index'), {'zipcode': 22600}, format='json')
        self.assertRedirects(response, reverse('grocerystore:start', kwargs={'zipcode': 22600}, status_code=302, target_status_code=200))
        # if the user enters an invalid zipcode
        response2 = self.client.post(reverse('grocerystore:index'), {'zipcode': 333}, format='json')
        self.assertRedirects(response2, reverse('grocerystore:index', status_code=302, target_status_code=200))
        response3 = self.client.post(reverse('grocerystore:index'), {'zipcode': "abcde"}, format='json')
        self.assertRedirects(response3, reverse('grocerystore:index', status_code=302, target_status_code=200))


class StartViewTest(TestCase):

    def setUp(self):
        # create 1 inflauser
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_address = Address.objects.create(street_adress1="2, Quilliampe", city="Loudéac", zip_code=22600, state=self.test_state)
        self.test_inflauser = Inflauser.objects.create(infla_user=self.test_user, inflauser_address=self.test_address)
        # create store1
        self.test_store1 = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_zipcode=22600, store_state=self.test_state)
        self.test_store1.delivery_area.add(self.test_zipcode)
        # create store2 that delivers in the same zipcode area than store1
        self.test_store2 = Store.objects.create(store_name='SuperU', store_location='centre', store_city='Lamballe', store_zipcode=22400, store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        self.client = Client()

    def test_get(self):
        """Checks if there's a list of all stores available in the zipcode area"""
        response1 = self.client.get(reverse('grocerystore:start', kwargs={'zipcode': 22600}))
        response2 = self.client.get(reverse('grocerystore:start', kwargs={'zipcode': 22400}))

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.templates[0].name, 'grocerystore/start.html')
        self.assertEqual(int(response1.context['zipcode']), 22600)
        self.assertEqual(response1.context['available_stores'][0], Store.objects.get(pk=1))
        self.assertEqual(response1.context['available_stores'][1], Store.objects.get(pk=2))
        self.assertContains(response1, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertContains(response1, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 2}))
        self.assertContains(response1, "---Stores in 22600---")
        self.assertContains(response1, 'class="horiz-top-nav"')

        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "Sorry, there's no store available in the ZIP code area you've chosen")
        self.assertEqual(response2.context.get('available_stores'), None)
        self.assertContains(response2, 'class="horiz-top-nav"')

    def test_get_with_authenticated_user(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:start', kwargs={'zipcode': 22600}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_get_with_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:start', kwargs={'zipcode': 22600}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, reverse('grocerystore:index'))


class StoreViewTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_zipcode=22600, store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        # creating a second store that delivers in the same area than test_store
        self.test_store2 = Store.objects.create(store_name='SuperU', store_location='centre', store_city='Lamballe', store_zipcode=22400, store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        # creating an available product
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory = ProductSubCategory.objects.create(parent=self.test_product_category, sub_category_name="Fruits")
        self.test_product = Product.objects.create(product_name="avocado", product_category=self.test_product_subcategory)
        self.test_product_availability = Availability.objects.create(product=self.test_product, store=self.test_store, product_unit='ea', product_price=2.29)
        self.client = Client()

    def test_get(self):
        """Checks if there's a navigation bar, the search tool and a form to choose a product category"""
        # response = self.client.get(reverse('grocerystore:store', args=[1])) ***this works as well
        response = self.client.get(reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/store.html')
        self.assertEqual(int(response.context['zipcode']), 22600)
        self.assertEqual(int(response.context['store_id']), 1)
        self.assertIsInstance(response.context['store'], Store)
        self.assertEqual(response.context['available_stores'][0], Store.objects.get(pk=2))
        self.assertIsInstance(response.context['category_form'], SelectCategory)

        self.assertContains(response, 'Shopping at Leclerc (ZAC)')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="category_form"')
        self.assertContains(response, 'id="search_tool"')
        self.assertContains(response, 'id="messages"')
        self.assertContains(response, "---Stores in 22600---")
        self.assertContains(response, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 2}))
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'zipcode': 22600}))
        self.assertContains(response, reverse('grocerystore:checkout', kwargs={'zipcode': 22600, 'store_id': 1}))

    def test_get_with_non_existent_store(self):
        """Redirection to the start page if the user tries to get to a non-existent store"""
        response = self.client.get(reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 3}))
        self.assertRedirects(response, reverse('grocerystore:start', kwargs={'zipcode': 22600}), status_code=302, target_status_code=200)

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout and a profile link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login, a register and an index link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, reverse('grocerystore:index'))

    def test_post_with_authorized_characters_in_search_tool(self):
        """Checks url redirection if search is correct"""
        # if there's at least one match (and less than 30 matches) in the chosen store
        url = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1})
        data = {'search': 'organic avocado'}
        response = self.client.post(url, data, format='json')
        searched_item = 'organic avocado'
        url2 = reverse('grocerystore:search', kwargs={'zipcode': 22600, 'store_id': 1, 'searched_item': urllib.quote(searched_item.encode('utf8'))})
        self.assertRedirects(response, url2, status_code=302, target_status_code=200)
        # if there's no match in the chosen store
        url3 = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 2})
        response2 = self.client.post(url3, data, format='json')
        self.assertRedirects(response2, url3, status_code=302, target_status_code=200)

    def test_post_with_unauthorized_characters_in_search_tool(self):
        """Checks url redirection if the user enters unauthorized characters in"""
        url = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1})
        data1 = {'search': '3'}
        data2 = {'search': 'chic/'}
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        url3 = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1,})
        self.assertRedirects(response1, url3, status_code=302, target_status_code=200)
        self.assertRedirects(response2, url3, status_code=302, target_status_code=200)

    def test_post_with_drop_down_menu_tool(self):
        """Checks url redirection if the user uses the drop down menu"""
        url = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1})
        data1 = {'category': 1,}
        data2 = {'category': "",} #if the user selects --Choose below-- in the drop down menu
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        url1 = reverse('grocerystore:subcategories', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1})
        url2 = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1})
        self.assertRedirects(response1, url1, status_code=302, target_status_code=200)
        self.assertRedirects(response2, url2, status_code=302, target_status_code=200)


class SubcategoriesListTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_zipcode=22600, store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        # creating a second store that delivers in the same area than test_store
        self.test_store2 = Store.objects.create(store_name='SuperU', store_location='centre', store_city='Lamballe', store_zipcode=22400, store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        # creating a category and 2 sub-categories
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory1 = ProductSubCategory.objects.create(parent=self.test_product_category, sub_category_name="Fruits")
        self.test_product_subcategory2 = ProductSubCategory.objects.create(parent=self.test_product_category, sub_category_name="Vegetables")

    def test_get_with_subcategories_list(self):
        """Checks that there's a list of available sub-categories and a navigation menu"""
        response = self.client.get(reverse('grocerystore:subcategories', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/subcategories_list.html')
        self.assertEqual(int(response.context['zipcode']), 22600)
        self.assertIsInstance(response.context['subcategories'][0], ProductSubCategory)
        self.assertEqual(int(response.context['store_id']), 1)
        self.assertIsInstance(response.context['store'], Store)
        self.assertEqual(int(response.context['category_id']), 1)
        self.assertEqual(response.context['available_stores'][0], Store.objects.get(pk=2))

        self.assertContains(response, 'Shopping at Leclerc (ZAC)')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'class="subcat_list"')
        self.assertContains(response, 'id="messages"')
        self.assertContains(response, "---Stores in 22600---")
        self.assertContains(response, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 2}))
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'zipcode': 22600}))
        self.assertContains(response, reverse('grocerystore:checkout', kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1, 'subcategory_id': 1,}))
        self.assertContains(response, reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1, 'subcategory_id': 2,}))

    def test_get_with_non_existent_category_or_store(self):
        """Proper redirection if the user tries to get to a non-existent category or store"""
        #non-existent category
        response1 = self.client.get(reverse('grocerystore:subcategories', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 3}))
        self.assertRedirects(response1, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}), status_code=302, target_status_code=200)
        #non-existent store
        response2 = self.client.get(reverse('grocerystore:subcategories', kwargs={'zipcode': 22600, 'store_id': 3, 'category_id': 1}))
        self.assertRedirects(response2, reverse('grocerystore:start', kwargs={'zipcode': 22600,}), status_code=302, target_status_code=200)

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout and a profile link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:subcategories', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:profile'))
        self.assertContains(response, reverse('grocerystore:logout'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login, a register and an index link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:subcategories', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))


class InstockListTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        # creating store1
        self.test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC',
                          store_city='Loudéac', store_zipcode=22600, store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        # creating store2 that delivers in the same area than test_store
        self.test_store2 = Store.objects.create(store_name='SuperU', store_location='centre',
                           store_city='Lamballe', store_zipcode=22400, store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        # creating 1 product
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory = ProductSubCategory.objects.create(parent=self.test_product_category,
                                        sub_category_name="Fruits")
        self.test_product = Product.objects.create(product_name="Avocado",
                            product_category=self.test_product_subcategory)
        self.test_availabilty = Availability.objects.create(product=self.test_product,
                                                 store=self.test_store,
                                                 product_unit='ea',
                                                 product_price=1.89)
        self.CART_HOST = "http://localhost:5000"
        self.client = Client()

    def test_get_with_products_list(self):
        """Checks that there's a list of available products and a navigation menu"""
        response = self.client.get(reverse('grocerystore:instock',
                   kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1, 'subcategory_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/instock_list.html')
        self.assertEqual(int(response.context['zipcode']), 22600)
        self.assertIsInstance(response.context['subcategory'], ProductSubCategory)
        self.assertEqual(int(response.context['store_id']), 1)
        self.assertIsInstance(response.context['store'], Store)
        self.assertEqual(int(response.context['category_id']), 1)
        self.assertEqual(response.context['quantity_set'], range(1, 21))
        self.assertEqual(response.context['available_stores'][0], Store.objects.get(pk=2))

        self.assertContains(response, "'Produce / Fruits' section at Leclerc (ZAC)")
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'class="available_products"')
        self.assertContains(response, 'id="messages"')
        self.assertContains(response, "---Stores in 22600---")
        self.assertContains(response, reverse('grocerystore:store',
                            kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:store',
                            kwargs={'zipcode': 22600, 'store_id': 2}))
        self.assertContains(response, reverse('grocerystore:cart',
                            kwargs={'zipcode': 22600}))
        self.assertContains(response, reverse('grocerystore:checkout',
                            kwargs={'zipcode': 22600, 'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:detail',
                            kwargs={'zipcode': 22600, 'store_id': 1, 'product_id': 1,}))

    def test_get_with_non_existent_subcategory_or_category_or_store(self):
        """Proper redirection if the user tries to get to a non-existent category, sub-category or store"""
        #non-existent sub-category
        response1 = self.client.get(reverse('grocerystore:instock',
                    kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1, 'subcategory_id': 2}))
        self.assertRedirects(response1, reverse('grocerystore:subcategories',
                            kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1,}),
                            status_code=302, target_status_code=200)
        #non-existent category
        response2 = self.client.get(reverse('grocerystore:instock',
                    kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 2, 'subcategory_id': 1}))
        self.assertRedirects(response2, reverse('grocerystore:store',
                             kwargs={'zipcode': 22600, 'store_id': 1}), status_code=302, target_status_code=200)
        #non-existent store
        response3 = self.client.get(reverse('grocerystore:instock',
                    kwargs={'zipcode': 22600, 'store_id': 3, 'category_id': 1, 'subcategory_id': 1}))
        self.assertRedirects(response3, reverse('grocerystore:start',
                             kwargs={'zipcode': 22600}), status_code=302, target_status_code=200)

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout and a profile link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1, 'subcategory_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login, a register, and an index link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1,'subcategory_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def test_post_when_anonymous_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.logout()
        self.assertEqual(len(self.client.session.keys()), 0)
        url = reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1,
              'category_id': 1,'subcategory_id': 1,})
        data = {'1': 4}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}), status_code=302, target_status_code=200)
        self.assertEqual(len(self.client.session.keys()), 1)

    def test_post_when_active_logged_in_user(self):
        """Checks url redirection when logged in user adds an item to their cart"""
        self.client.login(username='toto', password='azertyui')
        flask_cart = get_flaskcart(self.test_user.username, self.CART_HOST)
        # self.assertEqual(len(flask_cart.list()['items']), 0)
        url = reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1,'subcategory_id': 1,})
        data = {'1': 7,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(flask_cart.list()['items']), 1)
        self.assertIs(int(flask_cart.list()['items'][0]['name']), 1)
        self.assertIs(flask_cart.list()['items'][0]['qty'], 7)
        self.assertRedirects(response, reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': 1}), status_code=302, target_status_code=200)

    def test_post_when_inactive_logged_in_user(self): # trouble with redirection
        """Checks url redirection when logged in user adds an item to their cart"""
        self.test_user.is_active = False
        self.test_user.save()
        self.client.login(username='toto', password='azertyui')
        url = reverse('grocerystore:instock', kwargs={'zipcode': 22600, 'store_id': 1, 'category_id': 1,'subcategory_id': 1,})
        data = {'1': 7,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        # the following doesn't redirect correctly (redirect to 'grocerystore:store' instead)
        # self.assertRedirects(response, reverse('grocerystore:start', kwargs={'zipcode': 22600}), status_code=302, target_status_code=200)

#
# class UserRegisterViewTest(TestCase):
#     def test_get_with_registration_form(self):
#         """Checks the registration form is displayed on the page"""
#         response = self.client.get(reverse('grocerystore:register'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'id="registration_form"')
#
#     def test_get_with_links(self):
#         """Checks that the index page and login links are displayed"""
#         response = self.client.get(reverse('grocerystore:register'))
#         self.assertContains(response, reverse('grocerystore:index'))
#         self.assertContains(response, reverse('grocerystore:login'))
#
#
# class UserLoginViewTest(TestCase):
#     def test_get_with_login_form(self):
#         """Checks the login form is displayed on the page"""
#         response = self.client.get(reverse('grocerystore:login'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'id="login_form"')
#
#     def test_get_with_links(self):
#         """Checks that the index page and login links are displayed"""
#         response = self.client.get(reverse('grocerystore:login'))
#         self.assertContains(response, reverse('grocerystore:index'))
#         self.assertContains(response, reverse('grocerystore:register'))
#
#
# class CartViewTest(TestCase):
#     def setUp(self):
#         test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
#         test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
#         test_category = ProductCategory.objects.create(top_category='Alcohol')
#         test_subcategory = ProductSubCategory.objects.create(parent=test_category, sub_category_name='Beer')
#         test_product = Product.objects.create(product_name='Lager beer', product_category=test_subcategory)
#         test_availability = Availability.objects.create(product=test_product, store=test_store, product_unit='6x12floz', product_price=7.89)
#
#     def test_get(self):
#         """Checks if all elements are displayed"""
#         response = self.client.get(reverse('grocerystore:cart', kwargs={'store_id': 1}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "You're shopping at Leclerc (ZAC)")
#         self.assertContains(response, "Hi, here is your cart")
#         self.assertContains(response, reverse('grocerystore:index'))
#         self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': 1}))
#         self.assertContains(response, reverse('grocerystore:checkout', kwargs={'store_id': 1}))
#
#     def test_get_when_user_logged_in(self):
#         """Checks that there's a logout link if the user is logged in"""
#         self.client.login(username='toto', password='azertyui')
#         response = self.client.get(reverse('grocerystore:cart', kwargs={'store_id': 1,}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "Hi toto, here is your cart")
#         self.assertContains(response, reverse('grocerystore:logout'))
#         #adding a product to the cart
#         flask_cart = get_flaskcart('toto')
#         flask_cart.add(str(1), 3)
#         self.assertContains(response, reverse('grocerystore:detail', kwargs={'store_id': 1, 'product_id': 1}))
#
#     def test_get_when_anonymous_user(self):
#         """Checks that there's a login and a register link if the user isn't logged in"""
#         self.client.logout()
#         response = self.client.get(reverse('grocerystore:cart', kwargs={'store_id': 1,}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, reverse('grocerystore:login'))
#         self.assertContains(response, reverse('grocerystore:register'))
#
# class SearchViewTest(TestCase):
#     def setUp(self):
#         test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
#         test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
#         test_category = ProductCategory.objects.create(top_category='Alcohol')
#         test_subcategory = ProductSubCategory.objects.create(parent=test_category, sub_category_name='Beer')
#         test_product = Product.objects.create(product_name='Lager beer', product_category=test_subcategory)
#         test_availability = Availability.objects.create(product=test_product, store=test_store, product_unit='6x12floz', product_price=7.89)
#
#     def test_get_with_products_list(self):
#         """If (a) result(s) match(es) the search, the result form must be displayed"""
#         response = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'id="product_selection"')
#         #if the user types in /grocerystore/store/1/search/<searched_item> whereas there's no product matching the search_item
#         response2 = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'avocado'}))
#         self.assertRedirects(response2, reverse('grocerystore:store', kwargs={'store_id': 1,}), status_code=302, target_status_code=200)
#         #all the links below should be displayed on this page
#         self.assertContains(response, reverse('grocerystore:index'))
#         self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': 1}))
#         self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': 1}))
#
#     def test_get_when_user_logged_in(self):
#         """Checks that there's a logout link if the user is logged in"""
#         self.client.login(username='toto', password='azertyui')
#         response = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, reverse('grocerystore:logout'))
#
#     def test_get_when_anonymous_user(self):
#         """Checks that there's a login and a register link if the user isn't logged in"""
#         self.client.logout()
#         response = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, reverse('grocerystore:login'))
#         self.assertContains(response, reverse('grocerystore:register'))
#
#     def test_post_when_anonymous_user(self):
#         """Checks url redirection when anonymous user adds an item to their cart"""
#         self.client.logout()
#         url = reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'})
#         data = {'1': 4,}
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, 302)
#         self.assertRedirects(response, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)
#
#
# class ProductDetailViewTest(TestCase):
#     def setUp(self):
#         # create 2 zipcodes
#         self.test_zipcode1 = Zipcode.objects.create(zipcode=22600)
#         self.test_zipcode1.save()
#         self.test_zipcode2 = Zipcode.objects.create(zipcode=22400)
#         self.test_zipcode2.save()
#         # create 1 state
#         self.test_state = State(state_name="Brittany")
#         self.test_state.save()
#         # create one user
#         self.test_user = User(username='toto', email='tata@gmail.com', password='azertyui')
#         self.test_address = Address()
#         self.inflauser = Inflauser(infla_user=self.test.user, inflauser_address=self.test.address)
#         # create store1
#         self.test_store1 = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_zipcode=22600, store_state=self.test_state)
#         self.test_store1.save()
#         self.test_store1.delivery_area.add(self.test_zipcode1)
#         # create store2
#         self.test_store2 = Store.objects.create(store_name='SuperU', store_location='Centre', store_city='Lamballe', store_zipcode=22400, store_state=self.test_state)
#         self.test_store2.save()
#         self.test_store2.delivery_area.add(self.test_zipcode2)
#         self.test_category = ProductCategory.objects.create(top_category='Alcohol')
#         self.test_subcategory = ProductSubCategory.objects.create(parent=self.test_category, sub_category_name='Beer')
#         self.test_product1 = Product.objects.create(product_name='Lager beer', product_category=self.test_subcategory, product_brand_or_variety='Anchor steam', user_id_required=True)
#         self.test_availability1 = Availability.objects.create(product=self.test_product1, store=self.test_store1, product_unit='6x12floz', product_price=7.89)
#         self.test_availability2 = Availability.objects.create(product=self.test_product1, store=self.test_store2, product_unit='6x12floz', product_price=8.19)
#
#     def test_get_with_context(self):
#         """Must display all information about the product"""
#         product_id1 = self.test_product1.pk
#         store_id1 = self.test_store1.pk
#         store_id2 = self.test_store2.pk
#         response = self.client.get(reverse('grocerystore:detail', kwargs={'store_id': store_id1, 'product_id': product_id1}))
#         self.assertContains(response, "Price: $7.89 / 6x12floz")
#         self.assertContains(response, "Category: Alcohol / Beer")
#         self.assertContains(response, "Brand / variety: Anchor steam")
#         self.assertContains(response, "The customer must be over 21 to buy this product.")
#         self.assertContains(response, "also available in the store(s) below:")
#         self.assertContains(response, reverse('grocerystore:instock', kwargs={'store_id': store_id2, 'category_id': self.test_category.pk, 'subcategory_id': self.test_subcategory.pk}))
#         #and all the links in the bottom of the page
#         self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': store_id1}))
#         self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': store_id1}))
#         self.assertContains(response, reverse('grocerystore:index'))
#
#     def test_get_when_user_logged_in(self):
#         """Checks that there's a logout link if the user is logged in"""
#         self.client.login(username='toto', password='azertyui')
#         response = self.client.get(reverse('grocerystore:detail', kwargs={'store_id': 1, 'product_id': 1}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, reverse('grocerystore:logout'))
#
#     def test_get_when_anonymous_user(self):
#         """Checks that there's a login and a register link if the user isn't logged in"""
#         self.client.logout()
#         response = self.client.get(reverse('grocerystore:detail', kwargs={'store_id': 1, 'product_id': 1}))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, reverse('grocerystore:login'))
#         self.assertContains(response, reverse('grocerystore:register'))

class ProfileViewTest(TestCase):
    def setUp(self):
        pass

class ProfileUpdateViewTest(TestCase):
    def setUp(self):
        pass
