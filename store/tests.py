from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Order, OrderItem, Review

User = get_user_model()


class StoreTests(TestCase):
    """Tests for store app: Products, cart, orders, reviews."""
    def setUp(self):
        # Create a reusable test user and a sample product used across tests
        self.user = User.objects.create_user(
            username='testuser',
            password='pass'
        )
        self.product = Product.objects.create(
            name="Test Product",
            description="A great product.",
            price=19.99,
            stock=5
        )

    def test_product_list_view(self):
        # The product list view should load (200) and include the product name
        url = reverse('store:product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_detail_view(self):
        # The product detail view should load and show the product description
        url = reverse('store:product_detail', args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.description)

    def test_order_creation(self):
        # Create an order and associated order item; they should link
        # products correctly.
        order = Order.objects.create(
            user=self.user,
            total_cents=1999,
            status='paid'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price
        )
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)

    def test_review_post(self):
        # Logged-in users should be able to post review on product detail POST
        self.client.login(username='testuser', password='pass')
        url = reverse('store:product_detail', args=[self.product.pk])
        data = {'rating': 5, 'comment': 'Excellent!'}
        response = self.client.post(url, data)
        # Expect redirect after successful review post
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent!')

    def test_add_to_cart(self):
        # Adding a product to cart should update seession cart data
        self.client.login(username='testuser', password='pass')
        url = reverse('store:cart_add', args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        # Cart keys stored as string product pks
        self.assertIn(str(self.product.pk), session.get('cart', {}))

    def test_cart_update_and_remove(self):
        # Update quantity in cart and then remove the product
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        update_url = reverse('store:cart_update', args=[self.product.pk])
        response = self.client.post(update_url, {'quantity': 3})
        # Update should redirect on success
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.pk)], 3)
        remove_url = reverse('store:cart_remove', args=[self.product.pk])
        response = self.client.post(remove_url)
        # Removing should redirect and product not present in session cart
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertNotIn(str(self.product.pk), session.get('cart', {}))

    def test_checkout_requires_login(self):
        # Checkout page must require authentication (redirects when anonymous)
        url = reverse('store:checkout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_clear_cart(self):
        # Clear cart endpoint should empt the session cart
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        clear_url = reverse('store:cart_clear')
        response = self.client.post(clear_url)
        # Expect OK response and empty cart in session
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(session.get('cart', {}), {})
