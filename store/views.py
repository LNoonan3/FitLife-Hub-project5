from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem
from .forms import ReviewForm


def product_list(request):
    """Display all products."""
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})


def product_detail(request, pk):
    """Show a single product, its reviews, and allow posting a review."""
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if not request.user.is_authenticated:
            return redirect('login')
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        return redirect('store:product_detail', pk=pk)
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'review_form': form,
    })


@login_required
def cart_view(request):
    """Display the user's cart stored in session."""
    cart = request.session.get('cart', {})  # {product_id: qty}
    items = []
    total = 0
    for prod_id, qty in cart.items():
        product = get_object_or_404(Product, pk=prod_id)
        line_total = product.price_cents * qty
        items.append({
            'product': product,
            'quantity': qty,
            'line_total': line_total,
        })
        total += line_total
    return render(request, 'store/cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, pk):
    """AJAX endpoint to add a product to the session cart."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart[str(pk)] = cart.get(str(pk), 0) + 1
        request.session['cart'] = cart
        return JsonResponse({'message': 'Added to cart!'}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def checkout_view(request):
    """
    Create an Order from session cart and render a confirmation page.
    (For Pass grade, you can skip real payments here or integrate Stripe.)
    """
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('store:product_list')

    # Create order
    total = 0
    order = Order.objects.create(user=request.user, total_cents=0)
    for prod_id, qty in cart.items():
        product = get_object_or_404(Product, pk=prod_id)
        line_total = product.price_cents * qty
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            unit_price=product.price_cents
        )
        total += line_total
    order.total_cents = total
    order.status = 'paid'
    order.save()

    # Clear cart
    request.session['cart'] = {}

    return render(request, 'store/checkout_success.html', {'order': order})
