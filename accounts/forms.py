from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentRegistrationForm(UserCreationForm):
    first_name=forms.CharField(max_length=150, required=True)
    last_name=forms.CharField(max_length=150, required=True)
    email = forms.EmailField( required=True)

    class Meta:
        model=User
        fields=['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email=self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists')
        return email

    def save(self, commit=True):
        user=super().save(commit=False)
        user.role=User.Role.STUDENT
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    pass
