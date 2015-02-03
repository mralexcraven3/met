from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import CheckboxSelectMultiple

from met.metadataparser.models import Federation, Entity


class FederationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FederationForm, self).__init__(*args, **kwargs)
        editor_users_choices = self.fields['editor_users'].widget.choices
        self.fields['editor_users'].widget = CheckboxSelectMultiple(
                                                choices=editor_users_choices)
        self.fields['editor_users'].help_text = _("These users can edit this "
                                                 "federation and his entities")

    class Meta:
        model = Federation
        fields = ['file_url', 'file', 'editor_users', 'name', 'url', 'logo', 'is_interfederation']


class EntityForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EntityForm, self).__init__(*args, **kwargs)
        editor_users_choices = self.fields['editor_users'].widget.choices
        self.fields['editor_users'].widget = CheckboxSelectMultiple(
                                                choices=editor_users_choices)
        self.fields['editor_users'].help_text = _("These users can edit only "
                                                  "this entity")

    class Meta:
        model = Entity
        fields = ['file_url', 'file', 'editor_users']

class ServiceSearchForm(forms.Form):
    entityid = forms.CharField(max_length=200, label=_(u"Search service ID"),
                             help_text=_(u"Enter a full or partial entityid"),
                             widget=forms.TextInput(attrs={'size': '200'}))
