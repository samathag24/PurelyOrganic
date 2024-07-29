import token

import stripe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail, EmailMessage
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from IADS import settings
from .models import Product, Category, Brand, Cart, CartItem, Order, OrderItem, Profile, UserVisit, FAQ
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AddToCartForm, CheckoutForm, ProfileImageForm, \
    ContactForm, FAQForm, ReviewForm
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.http import JsonResponse
from django.views.decorators.http import require_POST


 
def get_cart_count(user):
    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        return sum(item.quantity for item in cart_items)
    return 0

class CategoryListView(ListView):
    model = Category
    template_name = 'myapp/category_list.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_count'] = get_cart_count(self.request.user)
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'myapp/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.product_set.all()
        context['cart_count'] = get_cart_count(self.request.user)
        return context


class BrandListView(ListView):
    model = Brand
    template_name = 'myapp/brand_list.html'
    context_object_name = 'brands'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_count'] = get_cart_count(self.request.user)
        return context


class BrandDetailView(DetailView):
    model = Brand
    template_name = 'myapp/brand_detail.html'
    context_object_name = 'brand'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_count'] = get_cart_count(self.request.user)
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'myapp/product_list.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_count'] = get_cart_count(self.request.user)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'myapp/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()
        context['review_form'] = ReviewForm()
        context['review_count'] = context['reviews'].count()
        return context
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted.')
            return redirect('product_detail', pk=product_id)
    else:
        form = ReviewForm()
    return render(request, 'myapp/add_review.html', {'form': form, 'product': product})




@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Initialize the form variable
    form = AddToCartForm()
    if request.method == 'POST':
        if 'add_to_cart' in request.POST:
            form = AddToCartForm(request.POST)
            if form.is_valid():
                quantity = form.cleaned_data['quantity']
                if item_created:
                    cart_item.quantity = quantity
                else:
                    cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, 'Product added to cart successfully.')
                return redirect('product_detail', pk=product_id)
        elif 'remove_from_cart' in request.POST:
            cart_item.delete()
            messages.success(request, 'Product removed from cart successfully.')
            return redirect('product_detail', pk=product_id)
    else:
        form = AddToCartForm()

    context = {
        'form': form,
        'product': product,
        'cart_count': get_cart_count(request.user),
        'cart_item': cart_item if not item_created else None  # Include cart_item if it already exists in the cart
    }

    return render(request, 'myapp/add_to_cart.html', context)
 cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.error(request, 'Your cart is empty. Please add items to your cart before checking out.')
        return redirect('view_cart')

    if request.method == 'POST':
        token = request.POST.get('stripeToken')
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            order = Order.objects.create(user=request.user)

            try:
                charge = stripe.Charge.create(
                    amount=int(cart.total_price() * 100),  # Amount in cents
                    currency='cad',
                    description='Example charge',
                    source=token,
                )

                for item in cart_items:
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                        OrderItem.objects.create(order=order, product=product, quantity=item.quantity)
                    else:
                        messages.error(request, f'Not enough stock for {product.name}')
                        return redirect('view_cart')

                cart_items.delete()
                # Render the email message using the template
                subject = 'Order Confirmation'
                html_message = render_to_string('emails/order_confirmation_email.html', {
                    'user': request.user,
                    'order_details': order,
                })
                plain_message = 'Your order has been placed successfully.'

                # Use EmailMultiAlternatives to send the email
                email = EmailMultiAlternatives(subject, plain_message, 'your_email@gmail.com', [request.user.email])
                email.attach_alternative(html_message, "text/html")
                email.send()
                messages.success(request, 'Order placed successfully.')
                return redirect('order_confirmation')
            except stripe.error.StripeError as e:
                messages.error(request, f"Payment error: {str(e)}")
                return redirect('checkout')
    else:
        form = CheckoutForm()

    return render(request, 'myapp/checkout.html', {
        'form': form,
        'cart_count': get_cart_count(request.user),
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'cart_items': cart_items,
        'total_price': cart.total_price(),
    })


          for item in order.orderitem_set.all():
def about(request):
    return render(request, 'myapp/about.html')


def search(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    product_id = request.GET.get('product')

    products = Product.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query)).distinct()
    if category_id:
        products = products.filter(category_id=category_id)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    if product_id:
        products = products.filter(id=product_id)

    categories = Category.objects.filter(id__in=products.values_list('category_id', flat=True)).distinct()
    brands = Brand.objects.filter(id__in=products.values_list('brand_id', flat=True)).distinct()

    if not products.exists():
        categories = Category.objects.filter(Q(name__icontains=query)).distinct()
        brands = Brand.objects.filter(Q(name__icontains=query)).distinct()

    context = {
        'query': query,
        'products': products,
        'categories': categories,
        'brands': brands,
        'cart_count': get_cart_count(request.user),
    }
    return render(request, 'myapp/search_results.html', context)
@require_POST
@login_required
def ajax_add_to_cart(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    quantity = int(request.POST.get('quantity', 1))
    if item_created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()

    return JsonResponse({'message': 'Product added to cart successfully.', 'cart_count': get_cart_count(request.user)})


def ajax_add_to_cart_unauthenticated(request):
    return JsonResponse({'status': 'login_required'})
