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

@login_required
@require_POST
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    # Add the product to the cart
    cart, created = Cart.objects.get_or_create(user=user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if request.method == 'POST':
        if 'buy_now' in request.POST:
            form = AddToCartForm(request.POST)
            if form.is_valid():
                quantity = int(request.POST.get('quantity', 1))  # Default quantity to 1 if not specified
                if item_created:
                    cart_item.quantity = quantity
                else:
                    cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, 'Product added to cart successfully.')
    # Increment quantity if the product already exists in the cart
    cart_item.save()

    # Redirect to the checkout page
    return redirect('view_cart')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not Profile.objects.filter(user=instance).exists():
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()



@login_required
def user_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    visit_count = request.session.get('visit_count', 0)
    visit_count += 1
    request.session['visit_count'] = visit_count

    user_history = request.session.get('user_history', [])
    current_visit = {
        'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'visit_count': visit_count
    }
    user_history.append(current_visit)
    request.session['user_history'] = user_history


    if request.method == 'POST':
        if 'remove_photo' in request.POST:
            profile.profile_image.delete()
            messages.success(request, 'Profile photo removed successfully.')
            return redirect('user_profile')
        form = ProfileImageForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile image updated successfully.')
            return redirect('user_profile')
    else:
        form = ProfileImageForm(instance=profile)
    last_visit = user_history[-2]['date'] if len(user_history) > 1 else "No previous visits"

    context = {
        'last_visit': last_visit,
        'visit_count': visit_count,
        'user_history': user_history,
        'orders': orders,
        'form': form
    }

    return render(request, 'myapp/user_profile.html', context)
def get_cart_count(user):
    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        return sum(item.quantity for item in cart_items)
    return 0





def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until it is verified
            user.save()

            # Email verification
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('myapp/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html"  # Specify the email content as HTML
            email.send()

            messages.success(request,
                             'Please confirm your email address to complete the registration. A verification link has been sent to your email.')
            return redirect('login')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{field.label}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'myapp/signup.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. You can now log in to your account.')
        return redirect('login')
    else:
        messages.warning(request, 'Activation link is invalid!')
        return redirect('signup')


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                if user.is_active:
                    # Ensure the user has a profile
                    if not hasattr(user, 'profile'):
                        Profile.objects.create(user=user)
                    login(request, user)
                    messages.success(request, 'Logged in successfully.')
                    return redirect('home')
                else:
                    messages.warning(request, 'Your account is not active. Please check your email for the activation link.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'myapp/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')

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
class HomeView(View):
    def get(self, request, *args, **kwargs):
        if request.COOKIES.get('cookiesAccepted'):
            if request.user.is_authenticated:
                visit_count = request.session.get('visit_count', 0)
                visit_count += 1
                request.session['visit_count'] = visit_count
            else:
                visit_count = request.COOKIES.get('visit_count', '0')
                visit_count = int(visit_count) + 1
                response = render(request, 'myapp/home.html', {'visit_count': visit_count, 'cart_count': get_cart_count(request.user)})
                response.set_cookie('visit_count', visit_count)
                return response

            return render(request, 'myapp/home.html', {'visit_count': visit_count, 'cart_count': get_cart_count(request.user)})
        else:
            return render(request, 'myapp/home.html', {'visit_count': 0, 'cart_count': get_cart_count(request.user)})


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



@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    # Calculate total price
    total_price = 0
    for item in cart_items:
        item.total_price = item.product.price * item.quantity
        total_price += item.total_price
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        cart_item = get_object_or_404(CartItem, id=cart_item_id)

        if 'add_quantity' in request.POST:
            cart_item.quantity += 1
            cart_item.save()
        elif 'remove_quantity' in request.POST:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                cart_items = CartItem.objects.filter(cart=cart)  # update cart_items after possible deletion

        # Recalculate total price after updates
        total_price = 0
        for item in cart_items:
            item.total_price = item.product.price * item.quantity
            total_price += item.total_price
    context = {
        'cart_items': cart_items,
        'cart_count': get_cart_count(request.user),
        'total_price': total_price,
        'is_empty': not cart_items.exists()

    }
    return render(request, 'myapp/view_cart.html', context)


@login_required
def checkout(request):
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


@login_required
def order_confirmation(request):
    order = Order.objects.filter(user=request.user).order_by('-created_at').first()  # Get the latest order for the user
    return render(request, 'myapp/order_confirmation.html',
                  {'order': order, 'cart_count': get_cart_count(request.user)})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('orderitem_set__product')

    if not orders.exists():
        print(f"No orders found for user: {request.user}")
    else:
        print(f"Orders found for user: {request.user}")
        for order in orders:
            print(f"Order {order.id}:")
            for item in order.orderitem_set.all():
                print(f"  - {item.product.name} x {item.quantity}")

    order_details = [
        {
            'order': order,
            'items': [
                {
                    'product': item.product,
                    'quantity': item.quantity
                }
                for item in order.orderitem_set.all()
            ]
        }
        for order in orders
    ]
    return render(request, 'myapp/order_history.html', {'order_details': order_details})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully. We will contact you soon!')
            return redirect('contact_success')
    else:
        form = ContactForm()
    return render(request, 'myapp/contact.html', {'form': form})


def contact_success_view(request):
    return render(request, 'myapp/contact_success.html')


def faq_view(request):
    faqs = FAQ.objects.all()
    return render(request, 'myapp/faq.html', {'faqs': faqs})


def add_faq_view(request):
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ has been added successfully!')
            return redirect('faq')
    else:
        form = FAQForm()
    return render(request, 'myapp/add_faq.html', {'form': form})
def about(request):
    return render(request, 'myapp/about.html')


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
