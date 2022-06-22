from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm, PasswordResetForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordReset(CreateView):
    form_class = PasswordResetForm
    template_name = 'users/password_reset_form.html'
