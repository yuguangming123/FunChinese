from django.shortcuts import render

# Create your views here.
def textbook(request):
    return render(request, 'textbook.html', {
        'active_menu': 'textbook-menu',
        'collapse_menu': 'collapse-std',
    })