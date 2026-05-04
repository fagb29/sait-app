# Formularios para la aplicación
from django import forms
from django.forms import inlineformset_factory
from .models import InformeMejora, ImagenInforme


class InformeForm(forms.ModelForm):
    """
    Formulario para crear un informe de mejora.
    Incluye comentarios y nombre de quien crea el informe.
    """
    class Meta:
        model = InformeMejora
        fields = ['comentarios', 'creado_por', 'email_inspector']
        widgets = {
            'comentarios': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Ingrese observaciones y comentarios sobre la orden de trabajo...'
            }),
            'creado_por': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su nombre completo',
                'required': True
            }),
            'email_inspector': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
        }
        labels = {
            'comentarios': 'Comentarios y Observaciones',
            'creado_por': 'Creado por (Nombre completo) *',
            'email_inspector': 'Correo del Inspector *',
        }


class ImagenInformeForm(forms.ModelForm):
    """
    Formulario para subir imágenes a un informe.
    """
    class Meta:
        model = ImagenInforme
        fields = ['imagen', 'descripcion', 'orden']
        widgets = {
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la imagen (opcional)'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
        }
        labels = {
            'imagen': 'Seleccionar imagen',
            'descripcion': 'Descripción',
            'orden': 'Orden de visualización'
        }


# Formset para manejar múltiples imágenes en un solo formulario
ImagenInformeFormSet = inlineformset_factory(
    InformeMejora,
    ImagenInforme,
    form=ImagenInformeForm,
    extra=3,  # Número de formularios vacíos a mostrar
    can_delete=True,
    max_num=10  # Máximo de imágenes permitidas
)


class InformeGeneralForm(forms.Form):
    """
    Formulario para crear un informe general sin estar ligado a una orden específica.
    """
    numero_peticion = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el número de petición'
        }),
        label='Número de Petición'
    )

    tecnico = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del técnico',
            'list': 'tecnicos-list'
        }),
        label='Técnico'
    )

    direccion = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la dirección'
        }),
        label='Dirección'
    )

    comuna = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la comuna'
        }),
        label='Comuna'
    )

    empresa = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la empresa'
        }),
        label='Empresa'
    )

    agencia = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la agencia'
        }),
        label='Agencia'
    )

    imagenes = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Subir Imágenes del Hallazgo (Máximo 20)',
        required=False,
        help_text='Puede seleccionar hasta 20 imágenes. Formatos: JPG, PNG, GIF'
    )

    comentarios = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Ingrese comentarios del hallazgo...'
        }),
        label='Comentario del Hallazgo'
    )

    creado_por = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nombre completo',
            'required': True
        }),
        label='Creado por (Nombre completo) *'
    )

    email_inspector = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
        }),
        label='Correo del Inspector *',
        help_text='Se enviará una copia del informe PDF a este correo.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ya no necesitamos inicializar queryset porque ahora es un CharField


class InformeAccesibleForm(forms.Form):
    """
    Formulario accesible para personas con discapacidad visual.
    Cumple con la Ley 21.015 de Inclusión Laboral.
    """
    # Información del técnico
    tecnico = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_tecnico',
            'placeholder': 'Nombre completo del técnico',
            'aria-describedby': 'ayuda-tecnico',
            'autocomplete': 'off'
        }),
        label='Técnico Responsable'
    )

    # Fecha del hallazgo
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'id_fecha',
            'type': 'date',
            'aria-describedby': 'ayuda-fecha'
        }),
        label='Fecha del Hallazgo'
    )

    # Agencia
    agencia = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_agencia',
            'placeholder': 'Nombre de la agencia',
            'aria-describedby': 'ayuda-agencia'
        }),
        label='Agencia'
    )

    # Zona
    ZONAS_CHOICES = [
        ('', 'Seleccione una zona'),
        ('RM', 'Región Metropolitana'),
        ('NORTE', 'Norte'),
        ('SUR', 'Sur'),
        ('CENTRO', 'Centro'),
    ]
    zona = forms.ChoiceField(
        choices=ZONAS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_zona',
            'aria-describedby': 'ayuda-zona'
        }),
        label='Zona'
    )

    # Tipo de hallazgo
    TIPOS_HALLAZGO = [
        ('', 'Seleccione un tipo'),
        ('seguridad', 'Seguridad'),
        ('calidad', 'Calidad'),
        ('eficiencia', 'Eficiencia'),
        ('infraestructura', 'Infraestructura'),
        ('otro', 'Otro'),
    ]
    tipo_hallazgo = forms.ChoiceField(
        choices=TIPOS_HALLAZGO,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tipo_hallazgo',
            'aria-describedby': 'ayuda-tipo'
        }),
        label='Tipo de Hallazgo'
    )

    # Descripción del hallazgo (con dictado por voz)
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'id_descripcion',
            'rows': 6,
            'placeholder': 'Describa detalladamente el hallazgo encontrado',
            'aria-describedby': 'ayuda-descripcion'
        }),
        label='Descripción del Hallazgo'
    )

    # Comentarios adicionales (con dictado por voz)
    comentarios = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'id_comentarios',
            'rows': 4,
            'placeholder': 'Información adicional o comentarios (opcional)',
            'aria-describedby': 'ayuda-comentarios'
        }),
        label='Comentarios Adicionales'
    )

    # Dirección
    direccion = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_direccion',
            'placeholder': 'Dirección completa del lugar',
            'aria-describedby': 'ayuda-direccion'
        }),
        label='Dirección'
    )

    # Comuna
    comuna = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_comuna',
            'placeholder': 'Comuna',
            'aria-describedby': 'ayuda-comuna'
        }),
        label='Comuna'
    )

    # Creado por
    creado_por = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_creado_por',
            'placeholder': 'Su nombre completo',
            'aria-describedby': 'ayuda-creado-por'
        }),
        label='Creado por (Nombre completo)'
    )

    # Imágenes del hallazgo (hasta 20)
    imagenes = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'id_imagenes',
            'accept': 'image/*',
            'aria-describedby': 'ayuda-imagenes'
        }),
        label='Evidencia Fotográfica (Opcional)',
        required=False,
        help_text='Puede seleccionar hasta 20 imágenes. Use el botón de ayuda para instrucciones'
    )
