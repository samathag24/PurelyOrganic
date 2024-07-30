from .models import Cart, CartItem

def get_cart_count(user):
    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        return sum(item.quantity for item in cart_items)
    return 0
