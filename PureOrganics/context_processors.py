from .models import Category, Brand, Product
from .utils import get_cart_count

def common_context(request):
    categories = Category.objects.all()
    brands = Brand.objects.all()
    products = Product.objects.all()
    cart_count = get_cart_count(request.user) if request.user.is_authenticated else 0
    return {
        'categories': categories,
        'brands': brands,
        'products': products,
        'cart_count': cart_count,
    }
