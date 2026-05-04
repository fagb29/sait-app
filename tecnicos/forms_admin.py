# Formularios para administración de usuarios
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


class CrearUsuarioForm(UserCreationForm):
    """
    Formulario para crear un nuevo usuario con todos los campos necesarios.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        }),
        label='Apellidos'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@movistar.cl'
        }),
        label='Correo Electrónico'
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Grupos / Permisos'
    )

    is_staff = forms.BooleanField(
        required=False,
        initial=False,
        label='Acceso al Panel de Administración',
        help_text='Permite acceso al panel de administración de Django'
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Usuario Activo',
        help_text='Desmarcar para desactivar la cuenta sin eliminarla'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'password1', 'password2', 'groups', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nombre.apellido'
            }),
        }
        labels = {
            'username': 'Nombre de Usuario',
        }
        help_texts = {
            'username': 'Requerido. 150 caracteres o menos. Solo letras, dígitos y @/./+/-/_',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar widgets de contraseñas
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar Contraseña'


class EditarUsuarioForm(forms.ModelForm):
    """
    Formulario para editar un usuario existente.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        }),
        label='Apellidos'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@movistar.cl'
        }),
        label='Correo Electrónico'
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Grupos / Permisos'
    )

    is_staff = forms.BooleanField(
        required=False,
        label='Acceso al Panel de Administración',
        help_text='Permite acceso al panel de administración de Django'
    )

    is_active = forms.BooleanField(
        required=False,
        label='Usuario Activo',
        help_text='Desmarcar para desactivar la cuenta sin eliminarla'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'groups', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
        }
        labels = {
            'username': 'Nombre de Usuario',
        }


class CambiarContrasenaForm(forms.Form):
    """
    Formulario para cambiar la contraseña de un usuario.
    """
    new_password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        })
    )

    new_password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")

        return cleaned_data
