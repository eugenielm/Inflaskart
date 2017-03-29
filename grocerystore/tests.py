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
The following tests are implemented:
- SearchItemTest
- GetFlaskcartTest
- IndexViewTest
- StartViewTest
- StoreViewTest
- SubcategoriesListTest
- InstockListTest
- UserRegisterViewTest
- UserLoginViewTest
- SearchViewTest
- ProductDetailViewTest
- ProfileViewTest
- ProfileUpdateViewTest
- CheckoutViewTest
"""


class SearchItemTest(TestCase):
    def setUp(self):
        # create 1 state
        self.test_state = State.objects.create(state_name="Brittany")
        # create 1 store
        self.test_store = Store.objects.create(store_name='Leclerc',
                                               store_location='ZAC',
                                               store_city='Loudéac',
                                               store_zipcode=22600,
                                               store_state=self.test_state)
        # create 2 products
        self.test_category = ProductCategory.objects.create(top_category='Alcohol')
        self.test_subcategory = ProductSubCategory.objects.create(
                                parent=self.test_category,
                                sub_category_name='Beer')
        self.test_product1 = Product.objects.create(
                             product_name='Lager beer',
                             product_category=self.test_subcategory,
                             product_brand_or_variety='Anchor steam',
                             user_id_required=True)
        self.test_product2 = Product.objects.create(
                             product_name='Non alcoholic beer',
                             product_category=self.test_subcategory)
        # create 2 availabilities in store1
        self.test_availability1 = Availability.objects.create(
                                  product=self.test_product1,
                                  store=self.test_store,
                                  product_unit='6x12floz',
                                  product_price=7.89)
        self.test_availability2 = Availability.objects.create(
                                  product=self.test_product2,
                                  store=self.test_store,
                                  product_unit='8x12floz',
                                  product_price=10.49)

    def test_search_item(self):
        """Checks if it returns a list of Availability instances."""
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
        """Checks if it returns an InflaskartClient instance"""
        test_flaskcart = get_flaskcart(self.test_username, self.test_host)
        self.assertIsInstance(test_flaskcart, InflaskartClient)


class IndexViewTest(TestCase):

    def setUp(self):
        # create 1 inflauser
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_address = Address.objects.create(street_adress1="2, Quilliampe",
                                                   city="Loudéac",
                                                   zip_code=22600,
                                                   state=self.test_state)
        self.test_inflauser = Inflauser.objects.create(infla_user=self.test_user,
                                                       inflauser_address=self.test_address)

    def test_get_with_authenticated_user(self):
        """Checks redirection if the user is authenticated."""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:index'))
        self.assertContains(response, "Welcome, toto!")
        self.assertContains(response, 'id="authenticated"')
        self.assertContains(response, "Start shopping")

    def test_get_with_anonymous_user(self):
        """Checks if there's a form to choose a zipcode and login/register links."""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/index.html')
        self.assertContains(response, 'enter a ZIP code')
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, 'Welcome to Inflaskart!')

    def post(self):
        """Checks URL redirection if the zipcode entered is valid or not."""
        response1 = self.client.post(reverse('grocerystore:index'),
                                     {'zipcode': 22600}, format='json')
        self.assertRedirects(response1, reverse('grocerystore:start',
                                                kwargs={'zipcode': 22600}))
        # if the user enters an invalid zipcode
        response2 = self.client.post(reverse('grocerystore:index'),
                                     {'zipcode': 333}, format='json')
        self.assertRedirects(response2, reverse('grocerystore:index'))
        response3 = self.client.post(reverse('grocerystore:index'),
                                     {'zipcode': "abcde"}, format='json')
        self.assertRedirects(response3, reverse('grocerystore:index'))


class StartViewTest(TestCase):

    def setUp(self):
        # create 1 inflauser
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany",
                                               state_postal_code="BZ")
        self.test_address = Address.objects.create(street_adress1="2, Quilliampe",
                                                   city="Loudéac",
                                                   zip_code=22600,
                                                   state=self.test_state)
        self.test_inflauser = Inflauser.objects.create(infla_user=self.test_user,
                                                       inflauser_address=self.test_address)
        # create store1
        self.test_store1 = Store.objects.create(store_name='Leclerc',
                                                store_location='ZAC',
                                                store_city='Loudéac',
                                                store_zipcode=22600,
                                                store_state=self.test_state)
        self.test_store1.delivery_area.add(self.test_zipcode)
        # create store2 that delivers in the same zipcode area than store1
        self.test_store2 = Store.objects.create(store_name='SuperU',
                                                store_location='centre',
                                                store_city='Lamballe',
                                                store_zipcode=22400,
                                                store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)

    def test_get(self):
        """Checks the list of all stores available in the zipcode area."""
        response1 = self.client.get(reverse('grocerystore:start',
                                            kwargs={'zipcode': self.test_zipcode.zipcode}))
        response2 = self.client.get(reverse('grocerystore:start',
                                            kwargs={'zipcode': self.test_store2.store_zipcode}))
        # response1
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.templates[0].name, 'grocerystore/start.html')
        self.assertEqual(int(response1.context['zipcode']), self.test_zipcode.zipcode)
        self.assertEqual(response1.context['available_stores'][0], self.test_store1)
        self.assertEqual(response1.context['available_stores'][1], self.test_store2)
        self.assertContains(response1, reverse('grocerystore:store',
                                               kwargs={'zipcode': self.test_zipcode.zipcode,
                                                       'store_id': self.test_store1.pk}))
        self.assertContains(response1, reverse('grocerystore:store',
                                               kwargs={'zipcode': self.test_zipcode.zipcode,
                                                       'store_id': self.test_store2.pk}))
        self.assertContains(response1, "---Stores in 22600---")
        self.assertContains(response1, 'class="horiz-top-nav"')
        # response2
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "Sorry, there's no store available in the "\
                                       "ZIP code area you've chosen")
        self.assertEqual(response2.context.get('available_stores'), None)
        self.assertContains(response2, 'class="horiz-top-nav"')

    def test_get_with_authenticated_user(self):
        """Checks if there's a logout and a profile link."""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:start',
                                           kwargs={'zipcode': self.test_zipcode.zipcode}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_get_with_anonymous_user(self):
        """Checks if there's an index, a login and a register link."""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:start',
                                           kwargs={'zipcode': self.test_zipcode.zipcode}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, reverse('grocerystore:index'))


class StoreViewTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_store = Store.objects.create(store_name='Leclerc',
                                               store_location='ZAC',
                                               store_city='Loudéac',
                                               store_zipcode=22600,
                                               store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        # creating a second store that delivers in the same area than test_store
        self.test_store2 = Store.objects.create(store_name='SuperU',
                                                store_location='centre',
                                                store_city='Lamballe',
                                                store_zipcode=22400,
                                                store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        # creating an available product
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory = ProductSubCategory.objects.create(
                                        parent=self.test_product_category,
                                        sub_category_name="Fruits")
        self.test_product = Product.objects.create(product_name="avocado",
                                                   product_category=self.test_product_subcategory)
        self.test_product_availability = Availability.objects.create(
                                         product=self.test_product,
                                         store=self.test_store,
                                         product_unit='ea',
                                         product_price=2.29)

    def test_get(self):
        """Checks if there's a navigation bar, the search tool and a form to
        choose a product category."""
        # response = self.client.get(reverse('grocerystore:store', args=[1])) ***this works as well
        response = self.client.get(reverse('grocerystore:store',
                                   kwargs={'zipcode': self.test_zipcode.zipcode,
                                           'store_id': self.test_store.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/store.html')
        # context
        self.assertEqual(int(response.context['zipcode']), self.test_zipcode.zipcode)
        self.assertEqual(int(response.context['store_id']), self.test_store.pk)
        self.assertEqual(response.context['store'], self.test_store)
        self.assertEqual(response.context['available_stores'][0], self.test_store2)
        self.assertIsInstance(response.context['category_form'], SelectCategory)
        # content
        self.assertContains(response, 'Shopping at Leclerc (ZAC)')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="category_form"')
        self.assertContains(response, 'id="search_tool"')
        self.assertContains(response, 'id="messages"')
        self.assertContains(response, "---Stores in 22600---")
        # links
        self.assertContains(response, reverse('grocerystore:store',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store2.pk}))
        self.assertContains(response, reverse('grocerystore:cart',
                                              kwargs={'zipcode': self.test_zipcode.zipcode}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk}))

    def test_get_with_non_existent_store(self):
        """Redirection to the start page if the user tries to get to a non-existent store."""
        response = self.client.get(reverse('grocerystore:store',
                                           kwargs={'zipcode': self.test_zipcode.zipcode,
                                                   'store_id': 3}))
        self.assertRedirects(response, reverse('grocerystore:start',
                                               kwargs={'zipcode': self.test_zipcode.zipcode}))

    def test_get_with_authenticated_user(self):
        """Checks that there's a logout and a profile link."""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:store',
                                           kwargs={'zipcode': self.test_zipcode.zipcode,
                                                   'store_id': self.test_store.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_get_with_anonymous_user(self):
        """Checks that there's a login, a register and an index link."""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:store',
                                           kwargs={'zipcode': self.test_zipcode.zipcode,
                                                   'store_id': self.test_store.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, reverse('grocerystore:index'))

    def test_post_with_authorized_characters_in_search_tool(self):
        """Checks url redirection if search is correct."""
        # if there's at least one match (and less than 30 matches) in the chosen store
        url = reverse('grocerystore:store', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                    'store_id': self.test_store.pk})
        data = {'search': 'organic avocado'}
        response = self.client.post(url, data, format='json')
        searched_item = 'organic avocado'
        url2 = reverse('grocerystore:search', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk,
                                                      'searched_item': urllib.quote(searched_item.encode('utf8'))})
        self.assertRedirects(response, url2, status_code=302, target_status_code=200)
        # if there's no match in the chosen store
        url3 = reverse('grocerystore:store', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                     'store_id': self.test_store2.pk})
        response2 = self.client.post(url3, data, format='json')
        self.assertRedirects(response2, url3, status_code=302, target_status_code=200)

    def test_post_with_unauthorized_characters_in_search_tool(self):
        """Checks url redirection if the user enters unauthorized characters."""
        url = reverse('grocerystore:store', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                    'store_id': self.test_store.pk})
        data1 = {'search': '3'}
        data2 = {'search': 'chic/'}
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        url3 = reverse('grocerystore:store', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                     'store_id': self.test_store.pk,})
        self.assertRedirects(response1, url3, status_code=302, target_status_code=200)
        self.assertRedirects(response2, url3, status_code=302, target_status_code=200)

    def test_post_with_drop_down_menu_tool(self):
        """Checks url redirection if the user uses the drop down menu."""
        url = reverse('grocerystore:store', kwargs={'zipcode': 22600, 'store_id': self.test_store.pk})
        data1 = {'category': self.test_product_category.pk,}
        data2 = {'category': "",} #if the user selects --Choose below-- in the drop down menu
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        url1 = reverse('grocerystore:subcategories',
                       kwargs={'zipcode': self.test_zipcode.zipcode,
                               'store_id': self.test_store.pk,
                               'category_id': self.test_product_category.pk})
        url2 = reverse('grocerystore:store',
                       kwargs={'zipcode': self.test_zipcode.zipcode,
                               'store_id': self.test_store.pk})
        self.assertRedirects(response1, url1, status_code=302, target_status_code=200)
        self.assertRedirects(response2, url2, status_code=302, target_status_code=200)


class SubcategoriesListTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='toto', password='azertyui')
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_store = Store.objects.create(store_name='Leclerc',
                                               store_location='ZAC',
                                               store_city='Loudéac',
                                               store_zipcode=22600,
                                               store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        # creating a second store that delivers in the same area than test_store
        self.test_store2 = Store.objects.create(store_name='SuperU',
                                                store_location='centre',
                                                store_city='Lamballe',
                                                store_zipcode=22400,
                                                store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        # creating a category and 2 sub-categories
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory1 = ProductSubCategory.objects.create(
                                         parent=self.test_product_category,
                                         sub_category_name="Fruits")
        self.test_product_subcategory2 = ProductSubCategory.objects.create(
                                         parent=self.test_product_category,
                                         sub_category_name="Vegetables")

    def test_get(self):
        """Checks that there's a list of available sub-categories and a navigation menu"""
        response = self.client.get(reverse('grocerystore:subcategories',
                                           kwargs={'zipcode': self.test_zipcode.zipcode,
                                                   'store_id': self.test_store.pk,
                                                   'category_id': self.test_product_category.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/subcategories_list.html')
        # context
        self.assertEqual(int(response.context['zipcode']), self.test_zipcode.zipcode)
        self.assertIsInstance(response.context['subcategories'][0], ProductSubCategory)
        self.assertEqual(int(response.context['store_id']), self.test_store.pk)
        self.assertEqual(response.context['store'], self.test_store)
        self.assertEqual(int(response.context['category_id']), self.test_product_category.pk)
        self.assertEqual(response.context['available_stores'][0], self.test_store2)
        # content
        self.assertContains(response, 'Shopping at Leclerc (ZAC)')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'class="subcat_list"')
        self.assertContains(response, 'id="messages"')
        self.assertContains(response, "---Stores in 22600---")
        # links
        self.assertContains(response, reverse('grocerystore:store',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store2.pk}))
        self.assertContains(response, reverse('grocerystore:cart',
                                              kwargs={'zipcode': self.test_zipcode.zipcode}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk}))
        self.assertContains(response, reverse('grocerystore:instock',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk,
                                                      'category_id': self.test_product_category.pk,
                                                      'subcategory_id': self.test_product_subcategory1.pk,}))
        self.assertContains(response, reverse('grocerystore:instock',
                                              kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk,
                                                      'category_id': self.test_product_category.pk,
                                                      'subcategory_id': self.test_product_subcategory2.pk,}))

    def test_get_with_non_existent_category_or_store(self):
        """Proper redirection if the user tries to get to a non-existent category or store"""
        #non-existent category
        response1 = self.client.get(reverse('grocerystore:subcategories',
                                            kwargs={'zipcode': self.test_zipcode.zipcode,
                                                    'store_id': self.test_store.pk,
                                                    'category_id': 3}))
        self.assertRedirects(response1, reverse('grocerystore:store',
                                                kwargs={'zipcode': self.test_zipcode.zipcode,
                                                        'store_id': self.test_store.pk}),)
        #non-existent store
        response2 = self.client.get(reverse('grocerystore:subcategories',
                                            kwargs={'zipcode': self.test_zipcode.zipcode,
                                                    'store_id': 3,
                                                    'category_id': self.test_product_category.pk}))
        self.assertRedirects(response2, reverse('grocerystore:start',
                                                kwargs={'zipcode': self.test_zipcode.zipcode,}))

    def test_get_with_authenticated_user(self):
        """Checks that there's a logout and a profile link"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:subcategories',
                                           kwargs={'zipcode': self.test_zipcode.zipcode,
                                                   'store_id': self.test_store.pk,
                                                   'category_id': self.test_product_category.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:profile'))
        self.assertContains(response, reverse('grocerystore:logout'))

    def test_get_with_anonymous_user(self):
        """Checks that there's a login, a register and an index link"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:subcategories',
                                           kwargs={'zipcode': self.test_zipcode.zipcode,
                                                   'store_id': self.test_store.pk,
                                                   'category_id': self.test_product_category.pk,}))
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
        self.test_product_subcategory = ProductSubCategory.objects.create(
                                        parent=self.test_product_category,
                                        sub_category_name="Fruits")
        self.test_product = Product.objects.create(product_name="Avocado",
                            product_category=self.test_product_subcategory)
        self.test_availability = Availability.objects.create(
                                product=self.test_product,
                                store=self.test_store,
                                product_unit='ea',
                                product_price=1.89)
        self.CART_HOST = "http://localhost:5000"

    def test_get_with_products_list(self):
        """Checks that there's a list of available products and a navigation menu"""
        response = self.client.get(reverse('grocerystore:instock',
                                   kwargs={'zipcode': self.test_zipcode.zipcode,
                                           'store_id': self.test_store.pk,
                                           'category_id': self.test_product_category.pk,
                                           'subcategory_id': self.test_product_subcategory.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/instock_list.html')
        # context
        self.assertEqual(int(response.context['zipcode']), self.test_zipcode.zipcode)
        self.assertIsInstance(response.context['subcategory'], ProductSubCategory)
        self.assertEqual(int(response.context['store_id']), self.test_store.pk)
        self.assertEqual(response.context['store'], self.test_store)
        self.assertEqual(int(response.context['category_id']), self.test_product_category.pk)
        self.assertEqual(response.context['quantity_set'], range(1, 21))
        self.assertEqual(response.context['available_stores'][0], self.test_store2)
        # content
        self.assertContains(response, "'Produce / Fruits' section at Leclerc (ZAC)")
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'class="available_products"')
        self.assertContains(response, 'id="messages"')
        self.assertContains(response, "---Stores in 22600---")
        # links
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.test_zipcode.zipcode,
                                              'store_id': self.test_store.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.test_zipcode.zipcode,
                                              'store_id': self.test_store2.pk}))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.test_zipcode.zipcode}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                      kwargs={'zipcode': self.test_zipcode.zipcode,
                                              'store_id': self.test_store.pk}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.test_zipcode.zipcode,
                                              'store_id': self.test_store.pk,
                                              'product_id': self.test_product.pk}))

    def test_get_with_non_existent_subcategory_or_category_or_store(self):
        """Proper redirection if the user tries to get to a non-existent category,
        sub-category or store."""
        #non-existent sub-category
        response1 = self.client.get(reverse('grocerystore:instock',
                                    kwargs={'zipcode': self.test_zipcode.zipcode,
                                            'store_id': self.test_store.pk,
                                            'category_id': self.test_product_category.pk,
                                            'subcategory_id': 2}))
        self.assertRedirects(response1, reverse('grocerystore:subcategories',
                                        kwargs={'zipcode': self.test_zipcode.zipcode,
                                                'store_id': self.test_store.pk,
                                                'category_id': self.test_product_category.pk,}))
        #non-existent category
        response2 = self.client.get(reverse('grocerystore:instock',
                                    kwargs={'zipcode': self.test_zipcode.zipcode,
                                            'store_id': self.test_store.pk,
                                            'category_id': 2,
                                            'subcategory_id': self.test_product_subcategory.pk}))
        self.assertRedirects(response2, reverse('grocerystore:store',
                                        kwargs={'zipcode': self.test_zipcode.zipcode,
                                                'store_id': self.test_store.pk}))
        #non-existent store
        response3 = self.client.get(reverse('grocerystore:instock',
                                    kwargs={'zipcode': self.test_zipcode.zipcode,
                                            'store_id': 3,
                                            'category_id': self.test_product_category.pk,
                                            'subcategory_id': self.test_product_subcategory.pk}))
        self.assertRedirects(response3, reverse('grocerystore:start',
                                        kwargs={'zipcode': self.test_zipcode.zipcode}))

    def test_get_with_authenticated_user(self):
        """Checks that there's a logout and a profile link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:instock',
                                   kwargs={'zipcode': self.test_zipcode.zipcode,
                                           'store_id': self.test_store.pk,
                                           'category_id': self.test_product_category.pk,
                                           'subcategory_id': self.test_product_subcategory.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_get_with_anonymous_user(self):
        """Checks that there's a login, a register, and an index link if the user
        isn't logged in."""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:instock',
                                   kwargs={'zipcode': self.test_zipcode.zipcode,
                                           'store_id': self.test_store.pk,
                                           'category_id': self.test_product_category.pk,
                                           'subcategory_id': self.test_product_subcategory.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def test_post_with_anonymous_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.logout()
        self.assertEqual(len(self.client.session.keys()), 0)
        url = reverse('grocerystore:instock', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk,
                                                      'category_id': self.test_product_category.pk,
                                                      'subcategory_id': self.test_product_subcategory.pk})
        data = {str(self.test_availability.pk): 4}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store',
                                       kwargs={'zipcode': self.test_zipcode.zipcode,
                                               'store_id': self.test_store.pk}))
        self.assertEqual(len(self.client.session.keys()), 1)

    def test_post_with_authenticated_user(self):
        """Checks url redirection when logged in user adds an item to their cart"""
        self.client.login(username='toto', password='azertyui')
        flask_cart = get_flaskcart(self.test_user.username, self.CART_HOST)
        flask_cart.empty_cart()
        url = reverse('grocerystore:instock', kwargs={'zipcode': self.test_zipcode.zipcode,
                                                      'store_id': self.test_store.pk,
                                                      'category_id': self.test_product_category.pk,
                                                      'subcategory_id': self.test_product_subcategory.pk})
        data = {str(self.test_availability.pk): 7,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(flask_cart.list()['items']), 1)
        self.assertIs(int(flask_cart.list()['items'][0]['name']), self.test_availability.pk)
        self.assertIs(flask_cart.list()['items'][0]['qty'], 7)
        self.assertRedirects(response, reverse('grocerystore:store',
                                       kwargs={'zipcode': self.test_zipcode.zipcode,
                                               'store_id': self.test_store.pk}))


class UserRegisterViewTest(TestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='toto',
                                                  email='toto@gmail.com',
                                                  password='azertyui')
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        # create 1 store that delivers in 22600
        self.test_store = Store.objects.create(store_name='SuperU',
                                               store_location='centre',
                                               store_city='Lamballe',
                                               store_zipcode=22400,
                                               store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        # creating 1 product available in test_store
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory = ProductSubCategory.objects.create(
                                        parent=self.test_product_category,
                                        sub_category_name="Fruits")
        self.test_product = Product.objects.create(product_name="Avocado",
                            product_category=self.test_product_subcategory)
        self.test_availability = Availability.objects.create(
                                product=self.test_product,
                                store=self.test_store,
                                product_unit='ea',
                                product_price=1.89)
        self.test_host = 'http://localhost:5000'


    def test_get(self):
        """Checks if the registration form and links are displayed on the page"""
        response = self.client.get(reverse('grocerystore:register'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/registration.html')
        # context
        self.assertIsInstance(response.context['user_form'], UserForm)
        self.assertIsInstance(response.context['address_form'], AddressForm)
        # content
        self.assertContains(response, 'id="registration_form"')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')
        # links
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))

    def test_post(self):
        # adding an item in the anonymous user's cart
        self.client.session[self.test_availability.pk] = {'name': str(self.test_availability.pk), 'qty': 16}
        # existing username
        data1 = {'username': "toto",
                'password': "azertyui",
                'email': "toto@gmail.com",
                'first_name': "Roger",
                'last_name': "Moore",
                'street_adress1': "1, Bond blv",
                'street_adress2': "",
                'apt_nb': "",
                'other': "",
                'city': "Los Angeles",
                'zip_code': 22600,
                'state': "1"}
        # invalid form (zipcode should be an integer)
        data2 = {'username': "lili",
                'password': "azertyui",
                'email': "mimi@gmail.com",
                'first_name': "Roger",
                'last_name': "Moore",
                'street_adress1': "1, Bond blv",
                'street_adress2': "",
                'apt_nb': "",
                'other': "",
                'city': "Los Angeles",
                'zip_code': "abcd",
                'state': "1"}
        # unavailable zipcode (ie.: no store delivers in zipcode area)
        data3 = {'username': "lulu",
                'password': "azertyui",
                'email': "mimi@gmail.com",
                'first_name': "Roger",
                'last_name': "Moore",
                'street_adress1': "1, Bond blv",
                'street_adress2': "",
                'apt_nb': "",
                'other': "",
                'city': "Los Angeles",
                'zip_code': 92000,
                'state': "1"}
        # valid form
        data4 = {'username': "lolo",
                'password': "azertyui",
                'email': "mimi@gmail.com",
                'first_name': "Roger",
                'last_name': "Moore",
                'street_adress1': "1, Bond blv",
                'street_adress2': "",
                'apt_nb': "",
                'other': "",
                'city': "Los Angeles",
                'zip_code': 22600,
                'state': "1"}

        url = reverse('grocerystore:register')
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        response3 = self.client.post(url, data3, format='json')
        response4 = self.client.post(url, data4, format='json')
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertRedirects(response3, reverse('grocerystore:index'), status_code=302, target_status_code=200)
        self.assertRedirects(response4, reverse('grocerystore:start',
                                        kwargs={'zipcode': data4['zip_code']}))

        # check if authenticated user's cart is updated
        test_flaskcart = get_flaskcart(data4['username'], self.test_host)
        for item in test_flaskcart.list()['items']:
            if item['name'] == str(self.test_availability.pk):
                self.assertIs(int(item['qty']), 16)


class UserLoginViewTest(TestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='titi', password='qsdfghjk')
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_address = Address.objects.create(street_adress1="2, Quilliampe",
                                                   city="Loudéac",
                                                   zip_code=22600,
                                                   state=self.test_state)
        self.test_inflauser = Inflauser.objects.create(infla_user=self.test_user,
                                                       inflauser_address=self.test_address)
        # create 1 store
        self.test_store = Store.objects.create(store_name='SuperU',
                                               store_location='centre',
                                               store_city='Lamballe',
                                               store_zipcode=22400,
                                               store_state=self.test_state)
        self.test_store.delivery_area.add(self.test_zipcode)
        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory = ProductSubCategory.objects.create(
                                        parent=self.test_product_category,
                                        sub_category_name="Fruits")
        # creating 1 product available in test_store
        self.test_product = Product.objects.create(product_name="Avocado",
                            product_category=self.test_product_subcategory)
        self.test_availability = Availability.objects.create(
                                product=self.test_product,
                                store=self.test_store,
                                product_unit='ea',
                                product_price=1.89)
        self.test_host = 'http://localhost:5000'
        self.client.session[self.test_availability.pk] = {'name': str(self.test_availability.pk), 'qty': 15}

    def test_get(self):
        """Checks if the registration form and links are displayed on the page"""
        response = self.client.get(reverse('grocerystore:login'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/login_form.html')
        self.assertIsInstance(response.context['login_form'], LoginForm)
        self.assertContains(response, 'id="login_form"')
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')

    def test_post(self):
        data1 = {'username': "titi",
                'password': "qsdfghjk",}
        # wrong password
        data2 = {'username': "titi",
                'password': "aaaaaaaa",}
        # user does'n exist
        data3 = {'username': "tutu",
                'password': "qsdfghjk",}
        url = reverse('grocerystore:login')
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        response3 = self.client.post(url, data3, format='json')
        test_flaskcart = get_flaskcart(self.test_user.username, self.test_host)
        zipcode = self.test_inflauser.inflauser_address.zip_code
        self.assertRedirects(response1, reverse('grocerystore:start', kwargs={'zipcode': zipcode}))
        # check if authenticated user's cart is updated
        for item in test_flaskcart.list()['items']:
            if item['name'] == str(self.test_availability.pk):
                self.assertIs(int(item['qty']), 15)
        self.assertRedirects(response2, reverse('grocerystore:login'))
        self.assertRedirects(response3, reverse('grocerystore:login'))


class CartViewTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='tutu', password='azertyui')
        self.test_state = State.objects.create(state_name="Brittany", state_postal_code="BZ")
        self.test_zipcode = Zipcode.objects.create(zipcode=22600)
        self.test_zipcode2 = Zipcode.objects.create(zipcode=22400)
        self.test_address = Address.objects.create(street_adress1="2, Quilliampe",
                                                   city="Loudéac",
                                                   zip_code=22600,
                                                   state=self.test_state)
        self.test_inflauser = Inflauser.objects.create(infla_user=self.test_user,
                                                       inflauser_address=self.test_address)
        self.test_host = 'http://localhost:5000'
        self.test_flaskcart = get_flaskcart(self.test_user.username, self.test_host)
        # create store1 which is in 22600 and delivers only in 22600
        self.test_store1 = Store.objects.create(store_name='Leclerc',
                                                store_location='ZAC',
                                                store_city='Loudéac',
                                                store_zipcode=22600,
                                                store_state=self.test_state)
        self.test_store1.delivery_area.add(self.test_zipcode)
        # create store2 which is in 22400 and delivers in 22600 and 22600
        self.test_store2 = Store.objects.create(store_name='SuperU',
                                                store_location='centre',
                                                store_city='Lamballe',
                                                store_zipcode=22400,
                                                store_state=self.test_state)
        self.test_store2.delivery_area.add(self.test_zipcode)
        self.test_store2.delivery_area.add(self.test_zipcode2)

        self.test_product_category = ProductCategory.objects.create(top_category='Produce')
        self.test_product_subcategory = ProductSubCategory.objects.create(
                                        parent=self.test_product_category,
                                        sub_category_name="Fruits")
        # creating product1 available in store1
        self.test_product1 = Product.objects.create(product_name="Avocado",
                             product_category=self.test_product_subcategory)
        self.test_availability1 = Availability.objects.create(
                                 product=self.test_product1,
                                 store=self.test_store1,
                                 product_unit='ea',
                                 product_price=1.89)
        # creating product2 available in store2
        self.test_product2 = Product.objects.create(product_name="Orange",
                             product_category=self.test_product_subcategory)
        self.test_availability2 = Availability.objects.create(
                                 product=self.test_product2,
                                 store=self.test_store2,
                                 product_unit='ea',
                                 product_price=0.79)

    def test_get_and_post_with_anonymous_user(self):
        # testing get and post in the same method because to be able to interact
        # with self.client.session data
        session = self.client.session

        # testing get
        session[self.test_availability1.pk] = {'name': str(self.test_availability1.pk), 'qty': 11}
        session[self.test_availability2.pk] = {'name': str(self.test_availability2.pk), 'qty': 12}
        session.save()
        response = self.client.get(reverse('grocerystore:cart', kwargs={'zipcode': 22600,}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/cart.html')
        # checks the context
        self.assertEqual(len(response.context['available_stores']), 2)
        self.assertEqual(int(response.context['zipcode']), 22600)
        # checks the links displayed
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store1.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store2.pk}))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.test_zipcode}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store1.pk,
                                              'product_id': self.test_product1.pk}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store2.pk,
                                              'product_id': self.test_product2.pk}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store1.pk,}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store2.pk,}))
        # checks the content
        self.assertContains(response, "Shopping in the 22600 area")
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="all_carts"')
        self.assertContains(response, 'id="messages"')

        # testing post
        # changing the quantity of an item
        data1 = {unicode(self.test_availability2.pk): [u'5']}
        url = reverse('grocerystore:cart', kwargs={'zipcode': self.test_zipcode})
        response1 = self.client.post(url, data1, format='json')
        session = self.client.session
        for elt in session.values():
            if elt['name'] == unicode(self.test_availability2.pk):
                self.assertEqual(elt['qty'], 5)
        # removing an item from the cart
        self.assertEqual(len(session.items()), 2)
        data2 = {'empty ' + str(self.test_availability2.pk): "Empty cart"}
        response2 = self.client.post(url, data2, format='json')
        session = self.client.session
        self.assertEqual(len(session.items()), 1)
        self.assertEqual(session.values()[0]['name'], str(self.test_availability1.pk))
        self.assertEqual(session.values()[0]['qty'], 11)

    def test_get_with_authenticated_user(self):
        """Checks that there's a logout link if the user is logged in"""
        self.test_flaskcart.empty_cart()
        self.test_flaskcart.add(str(self.test_availability1.pk), 3)
        self.test_flaskcart.add(str(self.test_availability2.pk), 4)
        self.client.login(username='tutu', password='azertyui')
        response = self.client.get(reverse('grocerystore:cart', kwargs={'zipcode': 22600,}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/cart.html')
        # checks the context
        self.assertEqual(response.context['username'], self.test_user.username)
        self.assertEqual(response.context['quantity_set'], range(21))
        self.assertEqual(len(response.context['available_stores']), 2)
        self.assertEqual(int(response.context['zipcode']), 22600)
        # checks the links displayed
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store1.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store2.pk}))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.test_zipcode}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store1.pk,
                                              'product_id': self.test_product1.pk}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store2.pk,
                                              'product_id': self.test_product2.pk}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store1.pk,}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                      kwargs={'zipcode': self.test_zipcode,
                                              'store_id': self.test_store2.pk,}))
        # checks the content
        self.assertContains(response, "Shopping in the 22600 area")
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="all_carts"')
        self.assertContains(response, 'id="messages"')

    def test_post_with_authenticated_user(self):
        self.client.login(username='tutu', password='azertyui')
        self.test_flaskcart.empty_cart()
        self.test_flaskcart.add(str(self.test_availability1.pk), 5)
        self.test_flaskcart.add(str(self.test_availability2.pk), 6)

        data1 = {unicode(self.test_availability2.pk): [u'10']}
        url = reverse('grocerystore:cart', kwargs={'zipcode': self.test_zipcode,})
        response1 = self.client.post(url, data1, format='json')
        self.assertEqual(len(self.test_flaskcart.list()['items']), 2)
        for item in self.test_flaskcart.list()['items']:
            if item['name'] == str(self.test_availability2.pk):
                self.assertEqual(item['qty'], 10)

        data2 = {'empty ' + str(self.test_availability2.pk): "Empty cart"}
        response2 = self.client.post(url, data2, format='json')
        self.assertEqual(len(self.test_flaskcart.list()['items']), 1)
        self.assertEqual(self.test_flaskcart.list()['items'][0]['name'], str(self.test_availability1.pk))
        self.assertEqual(self.test_flaskcart.list()['items'][0]['qty'], 5)


class SearchViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        self.state = State.objects.create(state_name="Brittany", state_postal_code='BZ')
        self.zipcode = Zipcode.objects.create(zipcode=22600)
        self.store = Store.objects.create(store_name='Leclerc',
                                          store_location='ZAC',
                                          store_city='Loudéac',
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store.delivery_area.add(self.zipcode)
        self.store2 = Store.objects.create(store_name='SuperU',
                                          store_location='centre',
                                          store_city='Loudéac',
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store2.delivery_area.add(self.zipcode)
        # creating a product
        self.category = ProductCategory.objects.create(top_category='Produce')
        self.subcategory = ProductSubCategory.objects.create(parent=self.category, sub_category_name='Fruits')
        self.product = Product.objects.create(product_name='Tomato', product_category=self.subcategory)
        self.availability = Availability.objects.create(product=self.product, store=self.store, product_unit='ea', product_price=0.49)
        # creating an inflauser
        self.address = Address.objects.create(street_adress1="2, Quilliampe",
                                              city="Loudéac",
                                              zip_code=22600,
                                              state=self.state)
        self.inflauser = Inflauser.objects.create(infla_user=self.user,
                                                  inflauser_address=self.address)
        self.cart = get_flaskcart(self.user.username, 'http://localhost:5000')

    def test_get_with_anonymous_user(self):
        """If (a) result(s) match(es) the search, the result form must be displayed"""
        response = self.client.get(reverse('grocerystore:search',
                                   kwargs={'zipcode': self.address.zip_code,
                                           'store_id': self.store.pk,
                                           'searched_item': 'tomato'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/search.html')
        self.assertEqual(len(response.context['available_products']), 1)
        self.assertEqual(response.context['quantity_set'], range(1, 21))
        self.assertEqual(int(response.context['zipcode']), 22600)
        self.assertEqual(int(response.context['store_id']), self.store.pk)
        self.assertEqual(response.context['store'], self.store)
        self.assertEqual(response.context['searched_item'], 'tomato')
        self.assertContains(response, 'class="available_products"')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')
        # checks the links displayed
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store2.pk}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                              kwargs={'zipcode': self.address.zip_code,
                                                      'store_id': self.store.pk,}))
        self.assertContains(response, reverse('grocerystore:cart',
                                              kwargs={'zipcode': self.address.zip_code,}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk,
                                              'product_id': self.product.pk,}))
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def get_with_authenticated_user(self):
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:search',
                                   kwargs={'zipcode': self.address.zip_code,
                                           'store_id': self.store.pk,
                                           'searched_item': 'tomato'}))
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store2.pk}))

    def test_post_with_anonymous_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.logout()
        url = reverse('grocerystore:search', kwargs={'zipcode': self.address.zip_code,
                                                     'store_id': self.store.pk,
                                                     'searched_item': 'tomato'})
        data = {'1': 4,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store',
                                       kwargs={'zipcode': self.address.zip_code,
                                               'store_id': self.store.pk,}))

    def test_post_with_authenticated_user(self):
        self.client.login(username='toto', password='azertyui')
        url = reverse('grocerystore:search', kwargs={'zipcode': self.address.zip_code,
                                                     'store_id': self.store.pk,
                                                     'searched_item': 'tomato'})
        data = {'1': 4,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store',
                                       kwargs={'zipcode': self.address.zip_code,
                                               'store_id': self.store.pk,}))
        self.assertEqual(len(self.cart.list()['items']), 1)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        self.state = State.objects.create(state_name="Brittany", state_postal_code='BZ')
        self.zipcode = Zipcode.objects.create(zipcode=22600)
        self.store = Store.objects.create(store_name='Leclerc',
                                          store_location='ZAC',
                                          store_city='Loudéac',
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store.delivery_area.add(self.zipcode)
        self.store2 = Store.objects.create(store_name='SuperU',
                                          store_location='centre',
                                          store_city='Loudéac',
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store2.delivery_area.add(self.zipcode)
        # creating a product
        self.category = ProductCategory.objects.create(top_category='Produce')
        self.subcategory = ProductSubCategory.objects.create(parent=self.category, sub_category_name='Fruits')
        self.product = Product.objects.create(product_name='Tomato', product_category=self.subcategory)
        self.availability = Availability.objects.create(product=self.product,
                                                        store=self.store,
                                                        product_unit='ea',
                                                        product_price=0.49)
        self.availability2 = Availability.objects.create(product=self.product,
                                                         store=self.store2,
                                                         product_unit='ea',
                                                         product_price=0.59)
        # creating an inflauser
        self.address = Address.objects.create(street_adress1="2, Quilliampe",
                                              city="Loudéac",
                                              zip_code=22600,
                                              state=self.state)
        self.inflauser = Inflauser.objects.create(infla_user=self.user,
                                                  inflauser_address=self.address)
        self.cart = get_flaskcart(self.user.username, 'http://localhost:5000')

    def test_get_with_anonymous_user(self):
        """If (a) result(s) match(es) the search, the result form must be displayed"""
        response = self.client.get(reverse('grocerystore:detail',
                                   kwargs={'zipcode': self.address.zip_code,
                                           'store_id': self.store.pk,
                                           'product_id': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/detail.html')

        self.assertEqual(len(response.context['other_availabilities']), 1)
        self.assertEqual(int(response.context['zipcode']), 22600)
        self.assertEqual(int(response.context['store_id']), self.store.pk)
        self.assertEqual(response.context['store'], self.store)

        self.assertEqual(response.context['product'], self.product)
        self.assertEqual(response.context['product_availability'], self.availability)
        self.assertEqual(response.context['product_brand_or_variety'], "")
        self.assertEqual(response.context['product_description'], "")
        self.assertEqual(response.context['user_id_required'], False)
        self.assertEqual(response.context['quantity_set'], range(1, 21))

        self.assertContains(response, 'class="product_detail"')
        self.assertContains(response, 'class="product_availabilities"')
        self.assertContains(response, 'id="1"')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')

        # checks the links displayed
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store2.pk}))
        self.assertContains(response, reverse('grocerystore:checkout',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk,}))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.address.zip_code,}))
        self.assertContains(response, reverse('grocerystore:detail',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store2.pk,
                                              'product_id': self.product.pk,}))
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def get_with_authenticated_user(self):
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:detail',
                                   kwargs={'zipcode': self.address.zip_code,
                                           'store_id': self.store.pk,
                                           'product_id': self.product.pk}))
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))

    def test_post_with_anonymous_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.logout()
        self.assertEqual(len(self.client.session.keys()), 0)
        url = reverse('grocerystore:detail', kwargs={'zipcode': self.address.zip_code,
                                                     'store_id': self.store.pk,
                                                     'product_id': self.product.pk,})
        data = {str(self.product.pk): 9}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store',
                                               kwargs={'zipcode': self.address.zip_code,
                                                       'store_id': self.store.pk}))
        self.assertEqual(len(self.client.session.keys()), 1)
        self.assertEqual(self.client.session[str(self.availability.pk)], {'name': str(self.availability.pk), 'qty': 9})

    def test_post_with_authenticated_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.login(username='toto', password='azertyui')
        self.cart.empty_cart()
        url = reverse('grocerystore:detail', kwargs={'zipcode': self.address.zip_code,
                                                     'store_id': self.store.pk,
                                                     'product_id': self.product.pk,})
        data = {str(self.product.pk): 7}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store',
                                               kwargs={'zipcode': self.address.zip_code,
                                                       'store_id': self.store.pk}))
        self.assertEqual(len(self.cart.list()['items']), 1)
        self.assertEqual(self.cart.list()['items'][0]['qty'], 7)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='lulu', email='lulu@gmail.com', password='azertyui')
        self.state = State.objects.create(state_name="Brittany", state_postal_code='BZ')
        self.zipcode = Zipcode.objects.create(zipcode=22600)
        self.address = Address.objects.create(street_adress1="2, Quilliampe",
                                              city="Loudéac",
                                              zip_code=22600,
                                              state=self.state)
        self.inflauser = Inflauser.objects.create(infla_user=self.user,
                                                  inflauser_address=self.address)
        self.store = Store.objects.create(store_name="Leclerc",
                                          store_location="ZAC",
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store.delivery_area.add(self.zipcode)

    def test_get(self):
        self.client.login(username='lulu', password='azertyui')
        response = self.client.get(reverse('grocerystore:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/profile.html')
        # links
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.address.zip_code}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk}))
        # content
        self.assertContains(response, 'id="edit"')
        self.assertContains(response, 'id="user_info"')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')
        # context
        self.assertEqual(response.context['zipcode'], self.address.zip_code)
        self.assertEqual(response.context['user_address'], self.address)
        self.assertIsInstance(response.context['available_stores'][0], Store)

    def test_post(self):
        self.client.login(username='lulu', password='azertyui')
        url = reverse('grocerystore:profile')
        data = {'edit_profile': "Edit profile"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:profile_update'))


class ProfileUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='lulu',
                                             email='lulu@gmail.com',
                                             password='azertyui',
                                             first_name='Roger',
                                             last_name='Moore')
        self.state = State.objects.create(state_name="Brittany", state_postal_code='BZ')
        self.zipcode = Zipcode.objects.create(zipcode=22600)
        self.address = Address.objects.create(street_adress1="2, Quilliampe",
                                              city="Loudéac",
                                              zip_code=22600,
                                              state=self.state)
        self.inflauser = Inflauser.objects.create(infla_user=self.user,
                                                  inflauser_address=self.address)
        self.store = Store.objects.create(store_name="Leclerc",
                                          store_location="ZAC",
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store.delivery_area.add(self.zipcode)

    def test_get(self):
        self.client.login(username='lulu', password='azertyui')
        response = self.client.get(reverse('grocerystore:profile_update'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/profile_update.html')
        # links
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.address.zip_code}))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk}))
        # content
        self.assertContains(response, 'id="profile_form"')
        self.assertContains(response, 'class="field"')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')
        # context
        self.assertIsInstance(response.context['address_form'], AddressForm)
        self.assertEqual(response.context['zipcode'], self.address.zip_code)

    def test_post(self):
        self.client.login(username='lulu', password='azertyui')
        # valid information
        data1 = {'first_name': [u'Bill'], 'last_name': [u'Moore'],
                'street_adress1': [u'1200 Hollywood blv'],
                'street_adress2': [u''],
                'other': [u''],
                'apt_nb': [u''],
                'zip_code': [u'22600'],
                'city': [u'Loudéac'],
                'state': [u'1']}
        #invalid zipcode
        data2 = {'first_name': [u'Mike'], 'last_name': [u'Moore'],
                'street_adress1': [u'1200 Hollywood blv'],
                'street_adress2': [u''],
                'other': [u''],
                'apt_nb': [u''],
                'zip_code': [u'abcd'],
                'city': [u'Loudéac'],
                'state': [u'1']}
        # no store delivering in the area of the zipcode entered
        data3 = {'first_name': [u'Bill'], 'last_name': [u'Moore'],
                'street_adress1': [u'1200 Hollywood blv'],
                'street_adress2': [u''],
                'other': [u''],
                'apt_nb': [u''],
                'zip_code': [u'75020'],
                'city': [u'Loudéac'],
                'state': [u'1']}
        url = reverse('grocerystore:profile_update')
        # response1 (valid)
        response1 = self.client.post(url, data1, format='json')
        self.assertRedirects(response1, reverse('grocerystore:profile'))
        inflauser = Inflauser.objects.get(infla_user=User.objects.get(username='lulu'))
        self.assertEqual(inflauser.infla_user.first_name, 'Bill')
        self.assertEqual(inflauser.inflauser_address.street_adress1, '1200 Hollywood blv')
        self.assertEqual(inflauser.inflauser_address.city, u'Loudéac')
        # response2 (invalid zipcode)
        response2 = self.client.post(url, data2, format='json')
        self.assertEqual(response2.status_code, 200)
        inflauser = Inflauser.objects.get(infla_user=User.objects.get(username='lulu'))
        self.assertEqual(inflauser.inflauser_address.zip_code, 22600)
        self.assertEqual(inflauser.infla_user.first_name, u'Mike')
        # response3 (no delivery in zipcode area)
        response3 = self.client.post(url, data3, format='json')
        self.assertEqual(response2.status_code, 200)
        inflauser = Inflauser.objects.get(infla_user=User.objects.get(username='lulu'))
        self.assertEqual(inflauser.infla_user.first_name, u'Bill')
        self.assertEqual(inflauser.inflauser_address.zip_code, 22600)


class CheckoutViewTest(TestCase):
    def setUp(self):
        # creating a user
        self.user = User.objects.create_user(username='toto',
                                             email='toto@gmail.com',
                                             password='azertyui',
                                             first_name='Roger',
                                             last_name='Moore')
        self.state = State.objects.create(state_name="Brittany", state_postal_code='BZ')
        self.zipcode = Zipcode.objects.create(zipcode=22600)
        self.address = Address.objects.create(street_adress1="2, Quilliampe",
                                              city="Loudéac",
                                              zip_code=22600,
                                              state=self.state)
        self.inflauser = Inflauser.objects.create(infla_user=self.user,
                                                  inflauser_address=self.address)
        self.cart = get_flaskcart(self.user.username, 'http://localhost:5000')
        # creating a store
        self.store = Store.objects.create(store_name="Leclerc",
                                          store_location="ZAC",
                                          store_zipcode=22600,
                                          store_state=self.state)
        self.store.delivery_area.add(self.zipcode)
        # creating a product available in that store
        self.category = ProductCategory.objects.create(top_category='Produce')
        self.subcategory = ProductSubCategory.objects.create(parent=self.category, sub_category_name='Fruits')
        self.product = Product.objects.create(product_name='Tomato', product_category=self.subcategory)
        self.availability = Availability.objects.create(product=self.product,
                                                        store=self.store,
                                                        product_unit='ea',
                                                        product_price=0.49)

    def test_get(self):
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:checkout',
                                           kwargs={'zipcode': self.address.zip_code,
                                                   'store_id': self.store.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'grocerystore/checkout.html')
        # links
        self.assertContains(response, reverse('grocerystore:logout'))
        self.assertContains(response, reverse('grocerystore:profile'))
        self.assertContains(response, reverse('grocerystore:store',
                                      kwargs={'zipcode': self.address.zip_code,
                                              'store_id': self.store.pk}))
        self.assertContains(response, reverse('grocerystore:cart',
                                      kwargs={'zipcode': self.address.zip_code}))
        # content
        self.assertContains(response, 'id="payment_form"')
        self.assertContains(response, 'class="horiz-top-nav"')
        self.assertContains(response, 'id="messages"')
        # context
        self.assertIsInstance(response.context['payment_form'], PaymentForm)
        self.assertEqual(response.context['username'], self.user.username)
        self.assertEqual(response.context['zipcode'], str(self.address.zip_code))
        self.assertEqual(response.context['store_id'], str(self.store.pk))
        self.assertEqual(response.context['amount_to_pay'], str(1.96))
        self.assertEqual(response.context['store'], self.store)

    def test_post(self):
        self.client.login(username='toto', password='azertyui')
        self.cart.add(str(self.availability.pk), 4)
        data = {'first_name': [u'Eugenie'],
                'last_name': [u'Le Moulec'],
                'expire_month': [u'6'],
                'number': [u'4959999999999999'],
                'cvv_number': [u'123'],
                'expire_year': [u'2018']}
        url = reverse('grocerystore:checkout', kwargs={'zipcode': self.address.zip_code,
                                                       'store_id': self.store.pk})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:start', kwargs={'zipcode': self.address.zip_code}))
