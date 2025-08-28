from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProgressUpdate
from .forms import ProgressUpdateForm, NewsletterForm


def progress_list(request):
    """Display all community progress updates."""
    updates = ProgressUpdate.objects.all().order_by('-created_at')
    return render(request, 'core/progress_list.html', {'updates': updates})


@login_required
def progress_create(request):
    """Allow logged-in users to post a new progress update."""
    form = ProgressUpdateForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        update = form.save(commit=False)
        update.user = request.user
        update.save()
        messages.success(request, "Your update was posted!")
        return redirect('core:progress_list')
    return render(request, 'core/progress_form.html', {'form': form})


@login_required
def progress_delete(request, pk):
    """Allow users to delete their own progress update."""
    update = get_object_or_404(ProgressUpdate, pk=pk, user=request.user)
    if request.method == 'POST':
        update.delete()
        messages.success(request, "Your progress update was deleted.")
        return redirect('core:progress_list')
    return render(
        request,
        'core/progress_confirm_delete.html',
        {'update': update}
    )


def newsletter_subscribe(request):
    """Handle newsletter signup form in footer."""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscribed to newsletter!")
        else:
            messages.error(request, "Invalid email address.")
    return redirect(request.META.get('HTTP_REFERER', '/'))
