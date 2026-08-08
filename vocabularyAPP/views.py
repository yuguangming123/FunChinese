from django.shortcuts import render

# Create your views here.
def vocabulary(request):
    return render(request, 'vocabulary.html', {
        'active_menu': 'vocabulary-menu',
        'collapse_menu': 'collapse-std',
    })