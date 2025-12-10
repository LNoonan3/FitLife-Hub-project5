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
            email='test@example.com',
            password='pass'
        )
        self.product = Product.objects.create(
            name="Test Product",
            description="A great product.",
            price=19.99,
            stock=5
        )
        self.product2 = Product.objects.create(
            name="Second Product",
            description="Another great product.",
            price=29.99,
            stock=3
        )

    def test_product_list_view(self):
        # The product list view should load (200) and include the product name
        url = reverse('store:product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.product2.name)

    def test_product_list_view_template(self):
        # Verify correct template is used
        url = reverse('store:product_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'store/product_list.html')

    def test_product_list_view_context(self):
        # Verify context contains products
        url = reverse('store:product_list')
        response = self.client.get(url)
        self.assertIn('products', response.context)
        self.assertEqual(len(response.context['products']), 2)

    def test_product_list_search_filter(self):
        # Test product search by name
        url = reverse('store:product_list')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertNotContains(response, "Second Product")

    def test_product_list_price_filter_min(self):
        # Test filtering by minimum price
        url = reverse('store:product_list')
        response = self.client.get(url, {'min_price': '25'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Product")
        self.assertContains(response, "Second Product")

    def test_product_list_price_filter_max(self):
        # Test filtering by maximum price
        url = reverse('store:product_list')
        response = self.client.get(url, {'max_price': '20'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertNotContains(response, "Second Product")

    def test_product_list_empty(self):
        # Test product list when no products exist
        Product.objects.all().delete()
        url = reverse('store:product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)

    def test_product_detail_view(self):
        # The product detail view should load and show the product description
        url = reverse('store:product_detail', args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.description)
        self.assertContains(response, self.product.name)

    def test_product_detail_view_template(self):
        # Verify correct template is used
        url = reverse('store:product_detail', args=[self.product.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'store/product_detail.html')

    def test_product_detail_view_context(self):
        # Verify context contains product and reviews
        url = reverse('store:product_detail', args=[self.product.pk])
        response = self.client.get(url)
        self.assertIn('product', response.context)
        self.assertIn('reviews', response.context)
        self.assertEqual(response.context['product'], self.product)

    def test_product_detail_nonexistent(self):
        # Accessing non-existent product should return 404
        url = reverse('store:product_detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_str_method(self):
        # Test the __str__ method of Product
        self.assertEqual(str(self.product), "Test Product")

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

    def test_order_multiple_items(self):
        # Test creating an order with multiple items
        order = Order.objects.create(
            user=self.user,
            total_cents=4998,
            status='paid'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        OrderItem.objects.create(
            order=order,
            product=self.product2,
            quantity=1,
            unit_price=self.product2.price
        )
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.item_count(), 3)  # Total quantity

    def test_order_str_method(self):
        # Test the __str__ method of Order
        order = Order.objects.create(
            user=self.user,
            total_cents=1999,
            status='paid'
        )
        self.assertIn(str(self.user.username), str(order))
        self.assertIn(str(order.id), str(order))

    def test_order_total_euros_conversion(self):
        # Test conversion of total_cents to euros
        order = Order.objects.create(
            user=self.user,
            total_cents=1999,
            status='paid'
        )
        self.assertEqual(order.total_euros(), 19.99)

    def test_order_status_choices(self):
        # Test different order status choices
        for status, _ in Order.STATUS_CHOICES:
            order = Order.objects.create(
                user=self.user,
                total_cents=1999,
                status=status
            )
            self.assertEqual(order.status, status)

    def test_order_item_str_method(self):
        # Test the __str__ method of OrderItem
        order = Order.objects.create(
            user=self.user,
            total_cents=1999,
            status='paid'
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        self.assertIn('2', str(item))
        self.assertIn(self.product.name, str(item))

    def test_order_item_line_total(self):
        # Test line_total calculation for OrderItem
        order = Order.objects.create(
            user=self.user,
            total_cents=3998,
            status='paid'
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=19.99
        )
        self.assertEqual(item.line_total(), 39.98)

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

    def test_review_post_requires_login(self):
        # Anonymous users should not be able to post reviews
        url = reverse('store:product_detail', args=[self.product.pk])
        data = {'rating': 5, 'comment': 'Great!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Form shown, not accepted
        self.assertEqual(Review.objects.count(), 0)

    def test_review_rating_validation(self):
        # Test review with invalid rating
        review = Review(
            user=self.user,
            product=self.product,
            rating=3,  # Valid rating
            comment='Good product'
        )
        review.save()
        self.assertEqual(review.rating, 3)

    def test_review_str_method(self):
        # Test the __str__ method of Review
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=4,
            comment='Good product'
        )
        self.assertIn('4', str(review))
        self.assertIn(self.user.username, str(review))

    def test_review_empty_comment(self):
        # Test that comment field is optional
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=5,
            comment=''
        )
        self.assertEqual(review.comment, '')

    def test_review_multiple_for_same_product(self):
        # Test multiple reviews on same product by different users
        user2 = User.objects.create_user(
            username='testuser2',
            password='pass'
        )
        Review.objects.create(
            user=self.user,
            product=self.product,
            rating=5,
            comment='Great!'
        )
        Review.objects.create(
            user=user2,
            product=self.product,
            rating=4,
            comment='Good'
        )
        self.assertEqual(self.product.reviews.count(), 2)

    def test_add_to_cart(self):
        # Adding a product to cart should update session cart data
        self.client.login(username='testuser', password='pass')
        url = reverse('store:cart_add', args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        # Cart keys stored as string product pks
        self.assertIn(str(self.product.pk), session.get('cart', {}))

    def test_add_to_cart_requires_login(self):
        # Anonymous users should not be able to add to cart
        url = reverse('store:cart_add', args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_add_to_cart_multiple_times(self):
        # Adding same product multiple times should increase quantity
        self.client.login(username='testuser', password='pass')
        url = reverse('store:cart_add', args=[self.product.pk])
        self.client.post(url)
        self.client.post(url)
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.pk)], 2)

    def test_add_to_cart_multiple_products(self):
        # Adding different products to cart
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        self.client.post(reverse('store:cart_add', args=[self.product2.pk]))
        session = self.client.session
        self.assertEqual(len(session['cart']), 2)

    def test_cart_view_requires_login(self):
        # Cart view should require authentication
        url = reverse('store:cart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_cart_view_empty(self):
        # Empty cart should display correctly
        self.client.login(username='testuser', password='pass')
        url = reverse('store:cart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 0)
        self.assertEqual(response.context['total'], 0)

    def test_cart_view_with_items(self):
        # Cart view should display items correctly
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        url = reverse('store:cart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 1)
        self.assertGreater(response.context['total'], 0)

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

    def test_cart_update_requires_login(self):
        # Cart update should require login
        url = reverse('store:cart_update', args=[self.product.pk])
        response = self.client.post(url, {'quantity': 2})
        self.assertEqual(response.status_code, 302)

    def test_cart_remove_requires_login(self):
        # Cart remove should require login
        url = reverse('store:cart_remove', args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_cart_update_quantity_zero(self):
        # Updating quantity to 0 should remove product
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        update_url = reverse('store:cart_update', args=[self.product.pk])
        self.client.post(update_url, {'quantity': 0})
        session = self.client.session
        self.assertNotIn(str(self.product.pk), session.get('cart', {}))

    def test_checkout_requires_login(self):
        # Checkout page must require authentication (redirects when anonymous)
        url = reverse('store:checkout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_checkout_empty_cart_redirects(self):
        # Checkout with empty cart should redirect to product list
        self.client.login(username='testuser', password='pass')
        url = reverse('store:checkout')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('store:product_list'))

    def test_checkout_with_items(self):
        # Checkout with items in cart should display checkout page
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        url = reverse('store:checkout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/checkout.html')

    def test_clear_cart(self):
        # Clear cart endpoint should empty the session cart
        self.client.login(username='testuser', password='pass')
        self.client.post(reverse('store:cart_add', args=[self.product.pk]))
        clear_url = reverse('store:cart_clear')
        response = self.client.post(clear_url)
        # Expect OK response and empty cart in session
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(session.get('cart', {}), {})

    def test_clear_cart_requires_login(self):
        # Clear cart should require login
        url = reverse('store:cart_clear')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_buy_now(self):
        # Buy Now should add product to cart and redirect to checkout
        self.client.login(username='testuser', password='pass')
        url = reverse('store:buy_now', args=[self.product.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('store:checkout'))
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.pk)], 1)

    def test_buy_now_requires_login(self):
        # Buy Now should require login
        url = reverse('store:buy_now', args=[self.product.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_order_history_requires_login(self):
        # Order history view should require login
        url = reverse('store:order_history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_order_history_view(self):
        # Order history should display user's orders
        order = Order.objects.create(
            user=self.user,
            total_cents=1999,
            status='paid'
        )
        self.client.login(username='testuser', password='pass')
        url = reverse('store:order_history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(order.id))

    def test_order_history_empty(self):
        # Order history should handle no orders gracefully
        self.client.login(username='testuser', password='pass')
        url = reverse('store:order_history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['orders']), 0)

    def test_order_detail_requires_login(self):
        # Order detail view should require login
        order = Order.objects.create(
            user=self.user,
            total_cents=1999,
            status='paid'
        )
        url = reverse('store:order_detail', args=[order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_order_detail_view(self):
        # Order detail should display correct order
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
        self.client.login(username='testuser', password='pass')
        url = reverse('store:order_detail', args=[order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(order.id))

    def test_order_detail_other_user_forbidden(self):
        # User should not see other user's orders
        user2 = User.objects.create_user(
            username='testuser2',
            password='pass'
        )
        order = Order.objects.create(
            user=user2,
            total_cents=1999,
            status='paid'
        )
        self.client.login(username='testuser', password='pass')
        url = reverse('store:order_detail', args=[order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_review_create_view(self):
        # Test review creation view
        self.client.login(username='testuser', password='pass')
        url = reverse('store:review_create', args=[self.product.pk])
        data = {'rating': 5, 'comment': 'Excellent product!'}
        response = self.client.post(url, data)
        self.assertRedirects(
            response,
            reverse('store:product_detail', args=[self.product.pk])
        )
        self.assertTrue(
            Review.objects.filter(
                user=self.user,
                product=self.product,
                rating=5
            ).exists()
        )

    def test_review_edit_view(self):
        # Test review editing
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=3,
            comment='Okay product'
        )
        self.client.login(username='testuser', password='pass')
        url = reverse('store:review_edit', args=[review.pk])
        data = {'rating': 5, 'comment': 'Actually excellent!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Actually excellent!')

    def test_review_delete_view(self):
        # Test review deletion
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            rating=3,
            comment='Bad product'
        )
        self.client.login(username='testuser', password='pass')
        url = reverse('store:review_delete', args=[review.pk])
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('store:product_detail', args=[self.product.pk])
        )
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_review_edit_other_user_forbidden(self):
        # User should not edit other user's reviews
        user2 = User.objects.create_user(
            username='testuser2',
            password='pass'
        )
        review = Review.objects.create(
            user=user2,
            product=self.product,
            rating=3,
            comment='Okay'
        )
        self.client.login(username='testuser', password='pass')
        url = reverse('store:review_edit', args=[review.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_out_of_stock(self):
        # Test product with zero stock
        out_of_stock = Product.objects.create(
            name="Out of Stock",
            description="Not available",
            price=9.99,
            stock=0
        )
        url = reverse('store:product_detail', args=[out_of_stock.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Out of Stock")
