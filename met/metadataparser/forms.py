#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
# Current version of MET has been revised for performance improvements by Andrea Biancini,
# Consortium GARR, http://www.garr.it
#########################################################################################

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import CheckboxSelectMultiple
from django.forms.extras.widgets import SelectDateWidget
from django.forms.util import ErrorDict

from django.utils import timezone
from dateutil.relativedelta import relativedelta

from met.metadataparser.models import Federation, Entity


class FederationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FederationForm, self).__init__(*args, **kwargs)
        editor_users_choices = self.fields['editor_users'].widget.choices
        self.fields['editor_users'].widget = CheckboxSelectMultiple(
                                                choices=editor_users_choices)
        self.fields['editor_users'].help_text = _("This/these user(s) can edit this "
                                                 "federation and its entities")

    class Meta:
        model = Federation
        fields = ['name', 'url', 'registration_authority', 'logo', 'is_interfederation', 'type', 'fee_schedule_url', 'file_url', 'file', 'editor_users']


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
        fields = ['registration_authority', 'file_url', 'file', 'editor_users']

class ChartForm(forms.Form):
    fromDate = forms.DateField(label=_(u'Start date'),
                             help_text=_(u"Statistics start date."), initial=timezone.now()-relativedelta(months=1),
                             widget=SelectDateWidget(years=range(timezone.datetime.today().year, 2012, -1)))

    toDate = forms.DateField(label=_(u'End date'),
                             help_text=_(u"Statistics end date."), initial=timezone.now(),
                             widget=SelectDateWidget(years=range(timezone.datetime.today().year, 2012, -1)))

    def is_valid(self):
        result = super(ChartForm, self).is_valid()

        if result:
            result = self.cleaned_data['fromDate'] <= self.cleaned_data['toDate']
            if not result:
                errors = ErrorDict()
                errors['toDate'] = 'End date must not be before Start date'
                self._errors = errors

        return result
            
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super(ChartForm, self).__init__(*args, **kwargs)

    class Meta:
        exclude = []


class EntityCommentForm(forms.Form):
    email = forms.EmailField(label=_(u'Your email address'),
                             help_text=_(u"Please enter your email address here."))

    comment = forms.CharField(max_length=1000, label=_(u"Your comment"),
                             help_text=_(u"Please enter your comment here."),
                             widget=forms.Textarea(attrs={'cols': '100', 'rows': '10'}))

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super(EntityCommentForm, self).__init__(*args, **kwargs)

    class Meta:
        exclude = []


class EntityProposalForm(forms.Form):
    email = forms.EmailField(label=_(u'Your email address'),
                             help_text=_(u"Please enter your email address here."))

    federation_choices = []
    i = 0
    for federation in Federation.objects.all():
        i += i
        federation_choices.append(('%s' %federation, federation))

    federations = forms.MultipleChoiceField(label=_(u'Federations'), choices = federation_choices,
                             help_text=_(u"Please select the federation(s) you want to gather the entity in."))
    
    comment = forms.CharField(max_length=1000, label=_(u"Your comment"),
                             help_text=_(u"Please enter your comment here."),
                             widget=forms.Textarea(attrs={'cols': '100', 'rows': '10'}))
    

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super(EntityProposalForm, self).__init__(*args, **kwargs)

        gatherd_federations = self.instance.federations.all()
        federation_choices = []
        i = 0
        for federation in Federation.objects.all().order_by('name'):
            if federation not in gatherd_federations:
                i += i
                federation_choices.append(('%s' %federation, federation))
            
        self.fields['federations'].widget.choices = federation_choices
                             
 
    class Meta:
        exclude = []


class ServiceSearchForm(forms.Form):
    entityid = forms.CharField(max_length=200, label=_(u"Search service ID"),
                             help_text=_(u"Enter a full or partial entityid"),
                             widget=forms.TextInput(attrs={'size': '200'}))

    class Meta:
        exclude = []
