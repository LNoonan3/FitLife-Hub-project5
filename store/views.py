import stripe
import ast
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from .models import Product, Order, OrderItem, Review
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import ReviewForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST


def product_list(request):
    """Display all products."""
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all()
    can_review = request.user.is_authenticated

    if request.method == 'POST' and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return redirect('store:product_detail', pk=product.pk)
    else:
        form = ReviewForm()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'can_review': can_review,
    })


@login_required
def cart_view(request):
    """Display the user's cart stored in session."""
    cart = request.session.get('cart', {})  # {product_id: qty}
    items = []
    total = 0
    for prod_id, qty in cart.items():
        product = get_object_or_404(Product, pk=prod_id)
        line_total = product.price * qty
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
@require_POST
def cart_update(request, pk):
    """Update the quantity of a product in the cart."""
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart[str(pk)] = quantity
    else:
        cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('store:cart')


@login_required
@require_POST
def cart_remove(request, pk):
    """Remove a product from the cart."""
    cart = request.session.get('cart', {})
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('store:cart')


@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('store:product_list')

    items = []
    line_items = []
    total = 0
    for prod_id, qty in cart.items():
        product = get_object_or_404(Product, pk=prod_id)
        line_total = product.price * qty
        items.append({
            'product': product,
            'quantity': qty,
            'line_total': line_total,
        })
        total += line_total
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': product.name},
                'unit_amount': int(product.price * 100),
            },
            'quantity': qty,
        })

    if request.method == 'POST':
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=request.user.email,
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('store:checkout_success')),
            cancel_url=request.build_absolute_uri(reverse('store:checkout_cancel')),
            metadata={'user_id': request.user.id, 'cart': str(cart)},
        )
        return redirect(session.url, code=303)

    return render(request, 'store/checkout.html', {
        'items': items,
        'total': total,
    })


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def oneoff_checkout(request, pk):
    product = get_object_or_404(Product, pk=pk)
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer_email=request.user.email,
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': product.name},
                'unit_amount': int(product.price * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse('store:checkout_success')
        ),
        cancel_url=request.build_absolute_uri(
            reverse('store:checkout_cancel')
        ),
        metadata={'product_id': product.id, 'user_id': request.user.id}
    )
    return redirect(session.url, code=303)


@login_required
def checkout_success(request):
    request.session['cart'] = {}
    return render(request, 'store/checkout_success.html')


@login_required
def checkout_cancel(request):
    return render(request, 'store/checkout_cancel.html')


@csrf_exempt
def oneoff_webhook(request):
    payload = request.body
    sig = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        sess = event['data']['object']
        user_id = sess['metadata'].get('user_id')
        cart_str = sess['metadata'].get('cart')
        if cart_str:
            cart = ast.literal_eval(cart_str)
            user = User.objects.get(id=user_id)
            total = 0
            for prod_id, qty in cart.items():
                product = Product.objects.get(pk=prod_id)
                line_total = product.price * qty
                total += line_total
            order = Order.objects.create(user=user, total_cents=int(total * 100), status='paid')
            for prod_id, qty in cart.items():
                product = Product.objects.get(pk=prod_id)
                OrderItem.objects.create(
                    order=order, product=product, quantity=qty, unit_price=product.price
                )
        else:
            product_id = sess['metadata'].get('product_id')
            user = User.objects.get(id=user_id)
            product = Product.objects.get(pk=product_id)
            order = Order.objects.create(
                user=user, total_cents=int(product.price * 100), status='paid'
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=1,
                unit_price=product.price
            )
    return HttpResponse(status=200)
