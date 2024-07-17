from django.shortcuts import render, get_object_or_404
from .models import Category

def home(request):
    return render(request,'myapp/home.html')
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'myapp/category_list.html', {'categories': categories})

def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return render(request, 'myapp/category_detail.html', {'category': category})
