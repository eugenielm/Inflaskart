#-*- coding: UTF-8 -*-
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser, User
from .models import Product, Store, Availability, Address, ProductCategory,\
                    ProductSubCategory, Dietary, Inflauser
from .views import IndexView, StoreView, SubcategoriesList, InstockList,\
                   UserRegisterView, UserLoginView, CartView, CheckoutView,\
                   get_flaskcart, search_item
from inflaskart_api import InflaskartClient
import urllib
# from rest_framework.test import APIRequestFactory, APITestCase


class SearchItemTest(TestCase):
    def setUp(self):
        self.test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
        self.test_category = ProductCategory.objects.create(top_category='Alcohol')
        self.test_subcategory = ProductSubCategory.objects.create(parent=self.test_category, sub_category_name='Beer')
        self.test_product1 = Product.objects.create(product_name='Lager beer', product_category=self.test_subcategory, product_brand_or_variety='Anchor steam', user_id_required=True)
        self.test_product2 = Product.objects.create(product_name='Non alcoholic beer', product_category=self.test_subcategory)
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

    def test_get_flaskuser(self):
        """Checks if it returns the right InflaskartClient instance"""
        test_flaskcart = get_flaskcart(self.test_username)
        self.assertIsInstance(test_flaskcart, InflaskartClient)


class IndexViewTest(TestCase):

    def setUp(self):
        test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')

    def test_get_with_form(self):
        """Checks that there's a form to choose a store"""
        response = self.client.get(reverse('grocerystore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="store_form"')

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:log_out'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def test_post_with_drop_down_menu_tool(self):
        """Checks url redirection when the user uses the drop down menu"""
        response1 = self.client.post(reverse('grocerystore:index'), {'stores': 1}, format='json')
        self.assertRedirects(response1, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)
        #if the user selects --Choose below-- in the drop down menu
        response2 = self.client.post(reverse('grocerystore:index'), {'stores': ""}, format='json')
        self.assertRedirects(response2, reverse('grocerystore:index'), status_code=302, target_status_code=200)


class StoreViewTest(TestCase):
    def setUp(self):
        test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
        product_category = ProductCategory.objects.create(top_category='Meat')

    def test_get_with_form(self):
        """Checks if there's a drop down menu form to choose a product category"""
        # response = self.client.get(reverse('grocerystore:store', args=[1])) ***this works as well
        response = self.client.get(reverse('grocerystore:store', kwargs={'store_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to Leclerc (ZAC) in Loudéac')
        self.assertContains(response, 'id="category_form"')
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': 1}))

    def test_get_with_non_existent_store_id(self):
        """Redirection to the index page if the user tries to get to a non-existent store"""
        response1 = self.client.get(reverse('grocerystore:store', kwargs={'store_id': 2}))
        response2 = self.client.get(reverse('grocerystore:store', kwargs={'store_id': "a"}))
        self.assertRedirects(response1, reverse('grocerystore:index'), status_code=302, target_status_code=200)
        self.assertRedirects(response2, reverse('grocerystore:index'), status_code=302, target_status_code=200)

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:store', kwargs={'store_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:log_out'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:store', kwargs={'store_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def test_post_with_authorized_characters_in_search_tool(self):
        """Checks url redirection if search is correct"""
        pass

    def test_post_with_unauthorized_characters_in_search_tool(self):
        """Checks url redirection if the user enters unauthorized characters in """
        pass

    def test_post_with_drop_down_menu_tool(self):
        """Checks url redirection if the user uses the drop down menu"""
        url = reverse('grocerystore:store', kwargs={'store_id': 1,})
        data1 = {'category': 1,}
        data2 = {'category': "",} #if the user selects --Choose below-- in the drop down menu
        response1 = self.client.post(url, data1, format='json')
        response2 = self.client.post(url, data2, format='json')
        url1 = reverse('grocerystore:subcategories', kwargs={'store_id': 1, 'category_id': 1})
        url2 = reverse('grocerystore:store', kwargs={'store_id': 1})
        self.assertRedirects(response1, url1, status_code=302, target_status_code=200)
        self.assertRedirects(response2, url2, status_code=302, target_status_code=200)


class SubcategoriesListTest(TestCase):
    def setUp(self):
        test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
        product_category = ProductCategory.objects.create(top_category='Meat')
        product_subcategory = ProductSubCategory.objects.create(parent=product_category,
                                                                sub_category_name='Beef')

    def test_get_with_subcategories_list(self):
        """Checks that there's a list of available sub-categories and a bunch of links"""
        response = self.client.get(reverse('grocerystore:subcategories', kwargs={'store_id': 1, 'category_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'store')
        self.assertContains(response, "You're shopping at Leclerc (ZAC) in Loudéac")
        self.assertContains(response, reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1, 'subcategory_id': 1,}))
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:checkout', kwargs={'store_id': 1}))

    def test_get_with_non_existent_category_or_store(self):
        """Proper redirection if the user tries to get to a non-existent category or store"""
        #non-existent category
        response1 = self.client.get(reverse('grocerystore:subcategories', kwargs={'store_id': 1, 'category_id': 2}))
        self.assertRedirects(response1, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)
        #non-existent store
        response2 = self.client.get(reverse('grocerystore:subcategories', kwargs={'store_id': 2, 'category_id': 1}))
        self.assertRedirects(response2, reverse('grocerystore:index'), status_code=302, target_status_code=200)

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:subcategories', kwargs={'store_id': 1, 'category_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:log_out'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:subcategories', kwargs={'store_id': 1, 'category_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))


class InstockListTest(TestCase):
    def setUp(self):
        test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
        test_category = ProductCategory.objects.create(top_category='Meat')
        test_subcategory = ProductSubCategory.objects.create(parent=test_category,
                                                                sub_category_name='Beef')
        test_product = Product.objects.create(product_name='Ground beef',
                                              product_category=test_subcategory,)
                                            #   product_store=test_store)
        availabilty = Availability.objects.create(product=test_product,
                                                 store=test_store,
                                                 product_unit='lbs',
                                                 product_price=7.89)

    def test_get_with_products_list(self):
        """Checks that there's a list of available products and a bunch of links"""
        response = self.client.get(reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1, 'subcategory_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="available_products"')
        self.assertContains(response, "You're shopping at Leclerc (ZAC) in Loudéac")
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:checkout', kwargs={'store_id': 1}))

    def test_get_with_non_existent_subcategory_or_category_or_store(self):
        """Proper redirection if the user tries to get to a non-existent category, sub-category or store"""
        #non-existent sub-category
        response1 = self.client.get(reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1, 'subcategory_id': 2}))
        self.assertRedirects(response1, reverse('grocerystore:subcategories', kwargs={'store_id': 1, 'category_id': 1,}), status_code=302, target_status_code=200)
        #non-existent category
        response2 = self.client.get(reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 2, 'subcategory_id': 1}))
        self.assertRedirects(response2, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)
        #non-existent store
        response3 = self.client.get(reverse('grocerystore:instock', kwargs={'store_id': 2, 'category_id': 1, 'subcategory_id': 1}))
        self.assertRedirects(response3, reverse('grocerystore:index'), status_code=302, target_status_code=200)

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1, 'subcategory_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:log_out'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1,'subcategory_id': 1,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def test_post_when_anonymous_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.logout()
        url = reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1,'subcategory_id': 1,})
        data = {'1': 4,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)

    def test_post_when_active_logged_in_user(self):
        """Checks url redirection when logged in user adds an item to their cart"""
        self.client.login(username='toto', password='azertyui')
        url = reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1,'subcategory_id': 1,})
        data = {'1': 7,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)

    def test_post_when_inactive_logged_in_user(self):
        """Checks url redirection when logged in user adds an item to their cart"""
        pass
        # self.client.login(username='toto', password='azertyui')
        # need to set the test_user as inactive in the setUp() definition.....
        # url = reverse('grocerystore:instock', kwargs={'store_id': 1, 'category_id': 1,'subcategory_id': 1,})
        # data = {'1': 7,}
        # response = self.client.post(url, data, format='json')
        # self.assertEqual(response.status_code, 302)
        # self.assertRedirects(response, reverse('grocerystore:index'), status_code=302, target_status_code=200)


class UserRegisterViewTest(TestCase):
    def test_get_with_registration_form(self):
        """Checks the registration form is displayed on the page"""
        response = self.client.get(reverse('grocerystore:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="registration_form"')

    def test_get_with_links(self):
        """Checks that the index page and login links are displayed"""
        response = self.client.get(reverse('grocerystore:register'))
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:login'))


class UserLoginViewTest(TestCase):
    def test_get_with_login_form(self):
        """Checks the login form is displayed on the page"""
        response = self.client.get(reverse('grocerystore:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="login_form"')

    def test_get_with_links(self):
        """Checks that the index page and login links are displayed"""
        response = self.client.get(reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:register'))


class SearchViewTest(TestCase):
    def setUp(self):
        test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        test_store = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
        test_category = ProductCategory.objects.create(top_category='Alcohol')
        test_subcategory = ProductSubCategory.objects.create(parent=test_category, sub_category_name='Beer')
        test_product = Product.objects.create(product_name='Lager beer', product_category=test_subcategory)
        test_availability = Availability.objects.create(product=test_product, store=test_store, product_unit='6x12floz', product_price=7.89)

    def test_get_with_products_list(self):
        """If (a) result(s) match(es) the search, the result form must be displayed"""
        response = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="product_selection"')
        #if the user types in /grocerystore/store/1/search/<searched_item> whereas there's no product matching the search_item
        response2 = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'avocado'}))
        self.assertRedirects(response2, reverse('grocerystore:store', kwargs={'store_id': 1,}), status_code=302, target_status_code=200)
        #all the links below should be displayed on this page
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': 1}))
        self.assertContains(response, reverse('grocerystore:checkout', kwargs={'store_id': 1}))

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:log_out'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))

    def test_post_when_anonymous_user(self):
        """Checks url redirection when anonymous user adds an item to their cart"""
        self.client.logout()
        url = reverse('grocerystore:search', kwargs={'store_id': 1, 'searched_item': 'beer'})
        data = {'1': 4,}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('grocerystore:store', kwargs={'store_id': 1}), status_code=302, target_status_code=200)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='toto', email='tata@gmail.com', password='azertyui')
        self.test_store1 = Store.objects.create(store_name='Leclerc', store_location='ZAC', store_city='Loudéac', store_state='Brittany')
        self.test_store2 = Store.objects.create(store_name='Safeway', store_location='California & Broderick', store_city='San Francisco', store_state='California')
        self.test_category = ProductCategory.objects.create(top_category='Alcohol')
        self.test_subcategory = ProductSubCategory.objects.create(parent=self.test_category, sub_category_name='Beer')
        self.test_product1 = Product.objects.create(product_name='Lager beer', product_category=self.test_subcategory, product_brand_or_variety='Anchor steam', user_id_required=True)
        self.test_availability1 = Availability.objects.create(product=self.test_product1, store=self.test_store1, product_unit='6x12floz', product_price=7.89)
        self.test_availability2 = Availability.objects.create(product=self.test_product1, store=self.test_store2, product_unit='6x12floz', product_price=8.19)

    def test_get_with_context(self):
        """Must display all information about the product"""
        product_id1 = self.test_product1.pk
        store_id1 = self.test_store1.pk
        store_id2 = self.test_store2.pk
        response = self.client.get(reverse('grocerystore:detail', kwargs={'store_id': store_id1, 'product_id': product_id1}))
        self.assertContains(response, "Price: $7.89 / 6x12floz")
        self.assertContains(response, "Category: Alcohol / Beer")
        self.assertContains(response, "Brand / variety: Anchor steam")
        self.assertContains(response, "The customer must be over 21 to buy this product.")
        self.assertContains(response, "also available in the store(s) below:")
        self.assertContains(response, reverse('grocerystore:instock', kwargs={'store_id': store_id2, 'category_id': self.test_category.pk, 'subcategory_id': self.test_subcategory.pk}))
        #and all the links in the bottom of the page
        self.assertContains(response, reverse('grocerystore:cart', kwargs={'store_id': store_id1}))
        self.assertContains(response, reverse('grocerystore:store', kwargs={'store_id': store_id1}))
        self.assertContains(response, reverse('grocerystore:index'))
        self.assertContains(response, reverse('grocerystore:checkout', kwargs={'store_id': store_id1}))

    def test_get_when_user_logged_in(self):
        """Checks that there's a logout link if the user is logged in"""
        self.client.login(username='toto', password='azertyui')
        response = self.client.get(reverse('grocerystore:detail', kwargs={'store_id': 1, 'product_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:log_out'))

    def test_get_when_anonymous_user(self):
        """Checks that there's a login and a register link if the user isn't logged in"""
        self.client.logout()
        response = self.client.get(reverse('grocerystore:detail', kwargs={'store_id': 1, 'product_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('grocerystore:login'))
        self.assertContains(response, reverse('grocerystore:register'))
