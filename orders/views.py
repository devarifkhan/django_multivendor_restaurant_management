from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from marketplace.models import Cart, Tax
from marketplace.context_processors import get_cart_amounts
from menu.models import FoodItem
from .forms import OrderForm
from .models import Order, OrderedFood, Payment
import simplejson as json
from .utils import generate_order_number, order_total_by_vendor
from accounts.utils import send_notification
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
import stripe
import requests


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required(login_url='login')
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    vendors_ids = []
    for i in cart_items:
        if i.fooditem.vendor.id not in vendors_ids:
            vendors_ids.append(i.fooditem.vendor.id)

    # {"vendor_id":{"subtotal":{"tax_type": {"tax_percentage": "tax_amount"}}}}
    get_tax = Tax.objects.filter(is_active=True)
    subtotal = 0
    total_data = {}
    k = {}
    for i in cart_items:
        fooditem = FoodItem.objects.get(pk=i.fooditem.id, vendor_id__in=vendors_ids)
        v_id = fooditem.vendor.id
        if v_id in k:
            subtotal = k[v_id]
            subtotal += (fooditem.price * i.quantity)
            k[v_id] = subtotal
        else:
            subtotal = (fooditem.price * i.quantity)
            k[v_id] = subtotal

        # Calculate the tax_data
        tax_dict = {}
        for i in get_tax:
            tax_type = i.tax_type
            tax_percentage = i.tax_percentage
            tax_amount = round((tax_percentage * subtotal)/100, 2)
            tax_dict.update({tax_type: {str(tax_percentage) : str(tax_amount)}})
        # Construct total data
        total_data.update({fooditem.vendor.id: {str(subtotal): str(tax_dict)}})

    subtotal = get_cart_amounts(request)['subtotal']
    total_tax = get_cart_amounts(request)['tax']
    grand_total = get_cart_amounts(request)['grand_total']
    tax_data = get_cart_amounts(request)['tax_dict']

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.pin_code = form.cleaned_data['pin_code']
            order.user = request.user
            order.total = grand_total
            order.tax_data = json.dumps(tax_data)
            order.total_data = json.dumps(total_data)
            order.total_tax = total_tax
            order.payment_method = request.POST['payment_method']
            order.save()  # order id/ pk is generated
            order.order_number = generate_order_number(order.id)
            order.vendors.add(*vendors_ids)
            order.save()

            context = {
                'order': order,
                'cart_items': cart_items,
            }

            if order.payment_method == 'Stripe':
                # Create Stripe Checkout Session
                line_items = []
                for item in cart_items:
                    line_items.append({
                        'price_data': {
                            'currency': 'bdt',
                            'product_data': {
                                'name': item.fooditem.food_title,
                            },
                            'unit_amount': int(item.fooditem.price * 100),  # Stripe uses smallest currency unit
                        },
                        'quantity': item.quantity,
                    })

                # Add tax as a line item
                if total_tax > 0:
                    line_items.append({
                        'price_data': {
                            'currency': 'bdt',
                            'product_data': {
                                'name': 'Tax',
                            },
                            'unit_amount': int(total_tax * 100),
                        },
                        'quantity': 1,
                    })

                domain = get_current_site(request)
                protocol = 'https' if request.is_secure() else 'http'
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url=f'{protocol}://{domain}/orders/stripe_success/?order_no={order.order_number}&session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{protocol}://{domain}/orders/stripe_cancel/?order_no={order.order_number}',
                    metadata={
                        'order_number': order.order_number,
                    },
                )
                context['stripe_session_id'] = checkout_session.id
                context['STRIPE_PUBLIC_KEY'] = settings.STRIPE_PUBLIC_KEY

            elif order.payment_method == 'SSLCommerz':
                # SSLCommerz Payment
                domain = get_current_site(request)
                protocol = 'https' if request.is_secure() else 'http'
                base_url = f'{protocol}://{domain}'

                sslcz_data = {
                    'store_id': settings.SSLCOMMERZ_STORE_ID,
                    'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
                    'total_amount': str(order.total),
                    'currency': 'BDT',
                    'tran_id': order.order_number,
                    'success_url': f'{base_url}/orders/sslcommerz_success/',
                    'fail_url': f'{base_url}/orders/sslcommerz_fail/',
                    'cancel_url': f'{base_url}/orders/sslcommerz_cancel/',
                    'ipn_url': f'{base_url}/orders/sslcommerz_ipn/',
                    'cus_name': order.name,
                    'cus_email': order.email,
                    'cus_phone': order.phone,
                    'cus_add1': order.address,
                    'cus_city': order.city,
                    'cus_country': order.country,
                    'cus_postcode': order.pin_code,
                    'shipping_method': 'NO',
                    'product_name': 'Food Order',
                    'product_category': 'Food',
                    'product_profile': 'non-physical-goods',
                }

                if settings.SSLCOMMERZ_SANDBOX:
                    sslcz_url = 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php'
                else:
                    sslcz_url = 'https://securepay.sslcommerz.com/gwprocess/v4/api.php'

                response = requests.post(sslcz_url, data=sslcz_data)
                response_data = response.json()

                if response_data.get('status') == 'SUCCESS':
                    return redirect(response_data['GatewayPageURL'])
                else:
                    context['sslcommerz_error'] = 'Payment gateway initialization failed. Please try again.'

            return render(request, 'orders/place_order.html', context)
        else:
            print(form.errors)
    return render(request, 'orders/place_order.html')


@login_required(login_url='login')
def payments(request):
    # Check if the request is ajax or not
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        # STORE THE PAYMENT DETAILS IN THE PAYMENT MODEL
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

        order = Order.objects.get(user=request.user, order_number=order_number)
        payment = Payment(
            user=request.user,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=order.total,
            status=status
        )
        payment.save()

        # UPDATE THE ORDER MODEL
        order.payment = payment
        order.is_ordered = True
        order.save()

        # MOVE THE CART ITEMS TO ORDERED FOOD MODEL
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.payment = payment
            ordered_food.user = request.user
            ordered_food.fooditem = item.fooditem
            ordered_food.quantity = item.quantity
            ordered_food.price = item.fooditem.price
            ordered_food.amount = item.fooditem.price * item.quantity
            ordered_food.save()

        # SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER
        mail_subject = 'Thank you for ordering with us.'
        mail_template = 'orders/order_confirmation_email.html'

        ordered_food = OrderedFood.objects.filter(order=order)
        customer_subtotal = 0
        for item in ordered_food:
            customer_subtotal += (item.price * item.quantity)
        tax_data = json.loads(order.tax_data)
        context = {
            'user': request.user,
            'order': order,
            'to_email': order.email,
            'ordered_food': ordered_food,
            'domain': get_current_site(request),
            'customer_subtotal': customer_subtotal,
            'tax_data': tax_data,
        }
        send_notification(mail_subject, mail_template, context)

        # SEND ORDER RECEIVED EMAIL TO THE VENDOR
        mail_subject = 'You have received a new order.'
        mail_template = 'orders/new_order_received.html'
        to_emails = []
        for i in cart_items:
            if i.fooditem.vendor.user.email not in to_emails:
                to_emails.append(i.fooditem.vendor.user.email)

                ordered_food_to_vendor = OrderedFood.objects.filter(order=order, fooditem__vendor=i.fooditem.vendor)

                context = {
                    'order': order,
                    'to_email': i.fooditem.vendor.user.email,
                    'ordered_food_to_vendor': ordered_food_to_vendor,
                    'vendor_subtotal': order_total_by_vendor(order, i.fooditem.vendor.id)['subtotal'],
                    'tax_data': order_total_by_vendor(order, i.fooditem.vendor.id)['tax_dict'],
                    'vendor_grand_total': order_total_by_vendor(order, i.fooditem.vendor.id)['grand_total'],
                }
                send_notification(mail_subject, mail_template, context)

        # CLEAR THE CART IF THE PAYMENT IS SUCCESS
        # cart_items.delete()

        # RETURN BACK TO AJAX WITH THE STATUS SUCCESS OR FAILURE
        response = {
            'order_number': order_number,
            'transaction_id': transaction_id,
        }
        return JsonResponse(response)
    return HttpResponse('Payments view')


@login_required(login_url='login')
def stripe_success(request):
    """Handle successful Stripe payment"""
    order_number = request.GET.get('order_no')
    session_id = request.GET.get('session_id')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            order = Order.objects.get(order_number=order_number, user=request.user)

            # Create payment record
            payment = Payment(
                user=request.user,
                transaction_id=session.payment_intent,
                payment_method='Stripe',
                amount=order.total,
                status='Completed'
            )
            payment.save()

            # Update order
            order.payment = payment
            order.is_ordered = True
            order.save()

            # Move cart items to ordered food
            cart_items = Cart.objects.filter(user=request.user)
            for item in cart_items:
                ordered_food = OrderedFood()
                ordered_food.order = order
                ordered_food.payment = payment
                ordered_food.user = request.user
                ordered_food.fooditem = item.fooditem
                ordered_food.quantity = item.quantity
                ordered_food.price = item.fooditem.price
                ordered_food.amount = item.fooditem.price * item.quantity
                ordered_food.save()

            # Send emails
            _send_order_emails(request, order, cart_items)

            # Clear cart
            cart_items.delete()

            return redirect(f'/orders/order_complete/?order_no={order_number}&trans_id={session.payment_intent}')
    except Exception as e:
        print(e)

    return redirect('home')


@login_required(login_url='login')
def stripe_cancel(request):
    """Handle cancelled Stripe payment"""
    order_number = request.GET.get('order_no')
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        order.status = 'Cancelled'
        order.save()
    except Order.DoesNotExist:
        pass
    return redirect('checkout')


@csrf_exempt
def sslcommerz_success(request):
    """Handle successful SSLCommerz payment"""
    if request.method == 'POST':
        data = request.POST
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')
        status = data.get('status')

        if status == 'VALID':
            # Validate the transaction with SSLCommerz
            if _validate_sslcommerz(val_id):
                try:
                    order = Order.objects.get(order_number=tran_id)
                    user = order.user

                    # Create payment record
                    payment = Payment(
                        user=user,
                        transaction_id=val_id,
                        payment_method='SSLCommerz',
                        amount=order.total,
                        status='Completed'
                    )
                    payment.save()

                    # Update order
                    order.payment = payment
                    order.is_ordered = True
                    order.save()

                    # Move cart items to ordered food
                    cart_items = Cart.objects.filter(user=user)
                    for item in cart_items:
                        ordered_food = OrderedFood()
                        ordered_food.order = order
                        ordered_food.payment = payment
                        ordered_food.user = user
                        ordered_food.fooditem = item.fooditem
                        ordered_food.quantity = item.quantity
                        ordered_food.price = item.fooditem.price
                        ordered_food.amount = item.fooditem.price * item.quantity
                        ordered_food.save()

                    # Send emails
                    _send_order_emails(request, order, cart_items)

                    # Clear cart
                    cart_items.delete()

                    return redirect(f'/orders/order_complete/?order_no={tran_id}&trans_id={val_id}')
                except Order.DoesNotExist:
                    pass

    return redirect('home')


@csrf_exempt
def sslcommerz_fail(request):
    """Handle failed SSLCommerz payment"""
    if request.method == 'POST':
        tran_id = request.POST.get('tran_id')
        try:
            order = Order.objects.get(order_number=tran_id)
            order.status = 'Cancelled'
            order.save()
        except Order.DoesNotExist:
            pass
    return redirect('checkout')


@csrf_exempt
def sslcommerz_cancel(request):
    """Handle cancelled SSLCommerz payment"""
    if request.method == 'POST':
        tran_id = request.POST.get('tran_id')
        try:
            order = Order.objects.get(order_number=tran_id)
            order.status = 'Cancelled'
            order.save()
        except Order.DoesNotExist:
            pass
    return redirect('checkout')


@csrf_exempt
def sslcommerz_ipn(request):
    """SSLCommerz Instant Payment Notification"""
    if request.method == 'POST':
        data = request.POST
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')
        status = data.get('status')

        if status == 'VALID':
            if _validate_sslcommerz(val_id):
                try:
                    order = Order.objects.get(order_number=tran_id)
                    if not order.is_ordered:
                        user = order.user
                        payment = Payment(
                            user=user,
                            transaction_id=val_id,
                            payment_method='SSLCommerz',
                            amount=order.total,
                            status='Completed'
                        )
                        payment.save()
                        order.payment = payment
                        order.is_ordered = True
                        order.save()
                except Order.DoesNotExist:
                    pass

    return HttpResponse('IPN received')


def _validate_sslcommerz(val_id):
    """Validate SSLCommerz transaction"""
    if settings.SSLCOMMERZ_SANDBOX:
        validation_url = 'https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php'
    else:
        validation_url = 'https://securepay.sslcommerz.com/validator/api/validationserverAPI.php'

    params = {
        'val_id': val_id,
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        'format': 'json',
    }
    response = requests.get(validation_url, params=params)
    result = response.json()
    return result.get('status') == 'VALID'


def _send_order_emails(request, order, cart_items):
    """Send order confirmation emails to customer and vendors"""
    # SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER
    mail_subject = 'Thank you for ordering with us.'
    mail_template = 'orders/order_confirmation_email.html'

    ordered_food = OrderedFood.objects.filter(order=order)
    customer_subtotal = 0
    for item in ordered_food:
        customer_subtotal += (item.price * item.quantity)
    tax_data = json.loads(order.tax_data)
    context = {
        'user': order.user,
        'order': order,
        'to_email': order.email,
        'ordered_food': ordered_food,
        'domain': get_current_site(request),
        'customer_subtotal': customer_subtotal,
        'tax_data': tax_data,
    }
    send_notification(mail_subject, mail_template, context)

    # SEND ORDER RECEIVED EMAIL TO THE VENDOR
    mail_subject = 'You have received a new order.'
    mail_template = 'orders/new_order_received.html'
    to_emails = []
    for i in cart_items:
        if i.fooditem.vendor.user.email not in to_emails:
            to_emails.append(i.fooditem.vendor.user.email)
            ordered_food_to_vendor = OrderedFood.objects.filter(order=order, fooditem__vendor=i.fooditem.vendor)
            context = {
                'order': order,
                'to_email': i.fooditem.vendor.user.email,
                'ordered_food_to_vendor': ordered_food_to_vendor,
                'vendor_subtotal': order_total_by_vendor(order, i.fooditem.vendor.id)['subtotal'],
                'tax_data': order_total_by_vendor(order, i.fooditem.vendor.id)['tax_dict'],
                'vendor_grand_total': order_total_by_vendor(order, i.fooditem.vendor.id)['grand_total'],
            }
            send_notification(mail_subject, mail_template, context)


def order_complete(request):
    order_number = request.GET.get('order_no')
    transaction_id = request.GET.get('trans_id')

    try:
        order = Order.objects.get(order_number=order_number, payment__transaction_id=transaction_id, is_ordered=True)
        ordered_food = OrderedFood.objects.filter(order=order)

        subtotal = 0
        for item in ordered_food:
            subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)
        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
            'tax_data': tax_data,
        }
        return render(request, 'orders/order_complete.html', context)
    except:
        return redirect('home')
