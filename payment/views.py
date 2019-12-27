import braintree
from django.shortcuts import render, get_object_or_404, redirect
from orders.models import Order
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import weasyprint
from io import BytesIO


def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # token nonce
        nonce = request.POST.get('payment_method_nonce', None)
        # stworzenie i wysyłka transakcji
        result = braintree.Transaction.sale({
            'amount': '{:.2f}'.format(order.get_total_cost()),
            'payment_method_nonce': nonce,
            'options': {'submit_for_settelment': True}
        })

        if result.is_success:
            # oznaczenie jako opłacone
            order.paid = True
            order.braintree_id = result.transaction.id
            order.save()
            # emil message
            subject = 'Mój sklep - rachunek nr {}'.format(order.id)
            message = 'W załączeniu rachunek do ostatniego zakupu.'
            emil = EmailMessage(subject, message, 'admin@djangoshop.pl',
                                [order.email])
            # pdf generator
            html = render_to_string('orders/order/pdf.html', {'order': order})
            out = BytesIO()
            stylesheets = [weasyprint.CSS(
                settings.STATIC_ROOT + 'css/pdf.css')]
            weasyprint.HTML(string=html).write_pdf(
                out, stylesheets=stylesheets)
            # plik pdf
            email.attach('order_{}.pdf'.format(order.id), out.getvalue(),
                         'application/pdf')
            email.send()
            return redirect('payment:done')
        else:
            return redirect('payment:canceled')
    else:
        client_token = braintree.ClientToken.generate()
        return render(request,
                      'payment/process.html',
                      {'order': order, 'client_token': client_token})


def payment_done(request):
    return render(request, 'payment/done.html')


def payment_canceled(request):
    return render(request, 'payment/canceled.html')
