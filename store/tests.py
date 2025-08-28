from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Order, OrderItem, Review

User = get_user_model()


class StoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.product = Product.objects.create(
            name="Test Product",
            description="A great product.",
            price=19.99,
            stock=5
        )

    def test_product_list_view(self):
        url = reverse('store:product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_detail_view(self):
        url = reverse('store:product_detail', args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.description)

    def test_order_creation(self):
        order = Order.objects.create(user=self.user, total_cents=1999, status='paid')
        OrderItem.objects.create(order=order, product=self.product, quantity=1, unit_price=self.product.price)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)

    def test_review_post(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('store:product_detail', args=[self.product.pk])
        data = {'rating': 5, 'comment': 'Excellent!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent!')

    def test_add_to_cart(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('store:cart_add', args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertIn(str(self.product.pk), session.get('cart', {}))

    def test_cart_update_and_remove(self):
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        update_url = reverse('store:cart_update', args=[self.product.pk])
        response = self.client.post(update_url, {'quantity': 3})
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.pk)], 3)
        remove_url = reverse('store:cart_remove', args=[self.product.pk])
        response = self.client.post(remove_url)
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertNotIn(str(self.product.pk), session.get('cart', {}))

    def test_checkout_requires_login(self):
        url = reverse('store:checkout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_clear_cart(self):
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        clear_url = reverse('store:cart_clear')
        response = self.client.post(clear_url)
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(session.get('cart', {}), {})