from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from masquerade.forms import MaskForm
from django.contrib.auth.models import User
from masquerade.signals import start_masquerading, stop_masquerading

START_MASQUERADE_REDIRECT_VIEW = getattr(settings, 'START_MASQUERADE_REDIRECT_VIEW', None)
STOP_MASQUERADE_REDIRECT_VIEW = getattr(settings, 'STOP_MASQUERADE_REDIRECT_VIEW', None)

MASQUERADE_CAN_MASK = getattr(settings,
  'MASQUERADE_CAN_MASK', lambda u:u.is_staff)

def get_start_redirect_url():
    if START_MASQUERADE_REDIRECT_VIEW:
        return reverse(START_MASQUERADE_REDIRECT_VIEW)
    else: return '/'

def get_stop_redirect_url():
    if STOP_MASQUERADE_REDIRECT_VIEW:
        return reverse(STOP_MASQUERADE_REDIRECT_VIEW)
    else: return '/'

def mask(request, template_name='masquerade/mask_form.html'):
    if not MASQUERADE_CAN_MASK(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = MaskForm(request.POST)
        if form.is_valid():
            # turn on masquerading
            request.session['mask_user'] = form.cleaned_data['mask_user']
            start_masquerading.send(sender='Masquerade', request=request)
            return HttpResponseRedirect(get_start_redirect_url())
    else:
        form = MaskForm()

    return render_to_response(template_name, {'form': form},
      context_instance=RequestContext(request))

def unmask(request):
    # Turn off masquerading. Don't bother checking permissions.
    try:
        stop_masquerading.send(sender='Masquerade', request=request)
        del(request.session['mask_user']) 
    except KeyError:
        pass

    return HttpResponseRedirect(get_stop_redirect_url())

def mask_directly(request, user_id):
    if not MASQUERADE_CAN_MASK(request.user):
        return HttpResponseForbidden()

    user = get_object_or_404(User, pk=user_id)
    request.session['mask_user'] = user.username
    start_masquerading.send(sender='Masquerade', request=request)
    return HttpResponseRedirect(get_start_redirect_url())
