from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import ReviewForm


def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        return redirect('store:product_detail', pk=pk)
    return render(request, 'store/product_detail.html', {
        'product': product, 'form': form
    })
