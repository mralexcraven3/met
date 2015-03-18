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

import re, time
import pytz
import simplejson as json
from urllib import unquote
from datetime import datetime
from dateutil import tz

from django.conf import settings
from django.db.models import Max, Count
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from chartit import DataPool, Chart

from met.metadataparser.decorators import user_can_edit
from met.metadataparser.models import Federation, Entity, EntityStat, TOP_LENGTH, FEDERATION_TYPES
from met.metadataparser.forms import (FederationForm, EntityForm, EntityCommentForm,
                                      EntityProposalForm, ServiceSearchForm, ChartForm)

from met.metadataparser.summary_export import export_summary
from met.metadataparser.query_export import export_query_set
from met.metadataparser.entity_export import export_entity
from met.metadataparser.xmlparser import DESCRIPTOR_TYPES
from met.metadataparser.utils import sendMail

if settings.PROFILE:
    from silk.profiling.profiler import silk_profile as profile
else:
    from met.metadataparser.templatetags.decorators import noop_decorator as profile

RESCUE_SLASH = re.compile(r"^(http(?:|s):/)([^/])")

def increment_current_toplength(request):
    currentTopLength = request.session.get('currentTopLength', TOP_LENGTH)
    currentTopLength += TOP_LENGTH

    if currentTopLength > Entity.objects.all().count():
        currentTopLength -= TOP_LENGTH

    request.session['currentTopLength'] = currentTopLength
    return HttpResponseRedirect(reverse('index'))
    
def decrement_current_toplength(request):
    currentTopLength = request.session.get('currentTopLength', TOP_LENGTH)
    currentTopLength -= TOP_LENGTH

    if currentTopLength <= 0:
        currentTopLength = TOP_LENGTH

    request.session['currentTopLength'] = currentTopLength
    return HttpResponseRedirect(reverse('index'))
    
@profile(name='Index page')
def index(request):
    ff = Federation.objects.all()
    federations = []
    interfederations = []
    for f in ff:
        if f.is_interfederation:
            interfederations.append(f)
        else:
            federations.append(f)

    cc = Entity.objects.values('federations__id', 'types__xmlname').annotate(Count('federations__id'), Count('types__xmlname'))
    counts = {}
    for curtype in DESCRIPTOR_TYPES:
        counts[curtype] = []
        for c in cc:
            if c['types__xmlname'] == curtype:
                counts[curtype].append(c)
    counts['All'] = Entity.objects.values('federations__id').annotate(Count('federations__id'))

    # Entities with count how many federations belongs to, and sorted by most first
    currentTopLength = request.session.get('currentTopLength', TOP_LENGTH)
    most_federated_entities = Entity.get_most_federated_entities(maxlength=currentTopLength, cache_expire=(24 * 60 * 60))

    export = request.GET.get('export', None)
    format = request.GET.get('format', None)
    if export and format:
        counters = (
                    ('all', {}),
                    ('IDPSSO', {'types__xmlname': 'IDPSSODescriptor'}),
                    ('SPSSO', {'types__xmlname': 'SPSSODescriptor'}),
                   )
        if export == 'interfederations':
            return export_summary(request.GET.get('format'), interfederations,
                                  'entity_set', 'interfederations_summary',
                                  counters)

        elif export == 'federations':
            return export_summary(request.GET.get('format'), federations,
                                  'entity_set', 'federations_summary',
                                  counters)
        elif export == 'most_federated_entities':
            return export_query_set(request.GET.get('format'), most_federated_entities,
                                'most_federated_entities', ('', 'types', 'displayName', 'federations', 'federationsCount'))
        else:
            return HttpResponseBadRequest('Not valid export query')
    
    return render_to_response('metadataparser/index.html', {
           'interfederations': interfederations,
           'federations': federations,
           'entity_types': DESCRIPTOR_TYPES,
           'federation_path': request.path,
           'counts': counts,
           'most_federated_entities': most_federated_entities,
           }, context_instance=RequestContext(request))


@profile(name='Federation view')
def federation_view(request, federation_slug=None):
    if federation_slug:
        request.session['%s_process_done' % federation_slug] = False
        request.session['%s_num_entities' % federation_slug] = 0
        request.session['%s_cur_entities' % federation_slug] = 0
        request.session.save()

    federation = get_object_or_404(Federation, slug=federation_slug)

    entity_type = None
    if (request.GET and 'entity_type' in request.GET):
        entity_type = request.GET['entity_type']
        ob_entities = Entity.objects.filter(types__xmlname=entity_type)
    else:
        ob_entities = Entity.objects.filter(federations__id=federation.id)
    
    ob_entities = ob_entities.prefetch_related('types', 'federations')
    paginator = Paginator(ob_entities, 20)

    try:
        ob_entities = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        ob_entities = paginator.page(1)
    except EmptyPage:
        ob_entities = paginator.page(paginator.num_pages)

    adjacent_pages = 5
    page_range = [n for n in \
                  range(ob_entities.number - adjacent_pages, ob_entities.number + adjacent_pages + 1) \
                  if n > 0 and n <= ob_entities.paginator.num_pages]

    pagination = {
        'page_range': page_range,
        'cur_page_number': ob_entities.number,
        'num_pages': ob_entities.paginator.num_pages,
    }

    entities = []
    for entity in ob_entities:
        entities.append({
            'entityid': entity.entityid,
            'name': entity.name,
            'absolute_url': entity.get_absolute_url(),
            'types': [unicode(item) for item in entity.types.all()],
            'federations': [(unicode(item.name), item.get_absolute_url()) for item in entity.federations.all()],
        })

    if 'format' in request.GET:
        return export_query_set(request.GET.get('format'), entities,
                                'entities_search_result', ('', 'types', 'federations'))

    context = RequestContext(request)
    user = context.get('user', None)
    add_entity = user and user.has_perm('metadataparser.add_federation')
    pie_chart = fed_pie_chart(request, federation.id)

    return render_to_response('metadataparser/federation_view.html',
            {'federation': federation,
             'entity_types': DESCRIPTOR_TYPES,
             'entity_type': entity_type or 'All',
             'fed_types': dict(FEDERATION_TYPES),
             'entities': entities,
             'show_filters': True,
             'add_entity': add_entity,
             'lang': request.GET.get('lang', 'en'),
             'update_entities': request.GET.get('update', 'false'),
             'statcharts': [pie_chart],
             'pagination': pagination,
            }, context_instance=context)


@user_can_edit(Federation)
def federation_edit(request, federation_slug=None):
    if federation_slug is None:
        federation = None
    else:
        federation = get_object_or_404(Federation, slug=federation_slug)

    if request.method == 'POST':
        form = FederationForm(request.POST, request.FILES, instance=federation)
        if form.is_valid():
            form.save()
            if not federation:
                form.instance.editor_users.add(request.user)
            if 'file' in form.changed_data or 'file_url' in form.changed_data:
                form.instance.process_metadata()
                #form.instance.process_metadata_entities(request=request)
            if federation:
                messages.success(request, _('Federation modified successfully'))
            else:
                messages.success(request, _('Federation created successfully'))

            return HttpResponseRedirect(form.instance.get_absolute_url() + '?update=true')

        else:
            messages.error(request, _('Please correct the errors indicated'
                                      ' below'))
    else:
        form = FederationForm(instance=federation)

    context = RequestContext(request)
    user = context.get('user', None)
    delete_federation = user and user.has_perm('metadataparser.delete_federation')
    return render_to_response('metadataparser/federation_edit.html',
                              {'form': form,
                               'delete_federation': delete_federation},
                              context_instance=RequestContext(request))


@user_can_edit(Federation)
def federation_update_entities(request, federation_slug=None):
    federation = get_object_or_404(Federation, slug=federation_slug)
    federation.process_metadata_entities(request=request, federation_slug=federation_slug)

    messages.success(request, _('Federation entities updated succesfully'))
    return HttpResponse("Done. All entities updated.", content_type='text/plain')


def entityupdate_progress(request, federation_slug=None):
    data = { 'done': False }
    if federation_slug:
        data = { 'done': request.session.get('%s_process_done' % federation_slug, False),
                 'tot': request.session.get('%s_num_entities' % federation_slug, 0),
                 'num': request.session.get('%s_cur_entities' % federation_slug, 0) }

    return HttpResponse(json.dumps(data), content_type='application/javascript')


@user_can_edit(Federation, True)
def federation_delete(request, federation_slug):
    federation = get_object_or_404(Federation, slug=federation_slug)

    for entity in federation.entity_set.all():
        if len(entity.federations.all()) == 1:
            #messages.success(request,
            #                 _(u"%(entity)s entity was deleted succesfully"
            #                 % {'entity': unicode(entity)}))
            entity.delete()

    messages.success(request,
                     _(u"%(federation)s federation was deleted successfully"
                     % {'federation': unicode(federation)}))
    federation.delete()
    return HttpResponseRedirect(reverse('index'))


@profile(name='Index charts')
def federation_charts(request, federation_slug=None):
    if federation_slug is None:
        federation = None
    else:
        federation = get_object_or_404(Federation, slug=federation_slug)

    if request.method == 'POST':
        form = ChartForm(request.POST, request.FILES, instance=federation)

        if form.is_valid():
            statsConfigDict = getattr(settings, "STATS")
            service_terms = statsConfigDict['statistics']['entity_by_type']['terms']
            service_title = statsConfigDict['statistics']['entity_by_type']['title']
            service_x_title = statsConfigDict['statistics']['entity_by_type']['x_title']
            service_y_title = statsConfigDict['statistics']['entity_by_type']['y_title']
            
            protocol_terms = statsConfigDict['statistics']['entity_by_protocol']['terms']
            protocol_title = statsConfigDict['statistics']['entity_by_protocol']['title']
            protocol_x_title = statsConfigDict['statistics']['entity_by_protocol']['x_title']
            protocol_y_title = statsConfigDict['statistics']['entity_by_protocol']['y_title']
            
            term_names = statsConfigDict['feature_names']
            time_format = statsConfigDict['time_format']
            protocols = statsConfigDict['protocols']

            from_time = datetime.fromordinal(form.cleaned_data['fromDate'].toordinal())
            if timezone.is_naive(from_time): from_time = pytz.utc.localize(from_time)
            to_time = datetime.fromordinal(form.cleaned_data['toDate'].toordinal() + 1)
            if timezone.is_naive(to_time): to_time = pytz.utc.localize(to_time)

            service_stats = EntityStat.objects.filter(  federation=federation \
                                              , feature__in = service_terms \
                                              , time__gte = from_time \
                                              , time__lte = to_time).order_by("time")

            protocol_stats = EntityStat.objects.filter(  federation=federation \
                                              , feature__in = protocol_terms \
                                              , time__gte = from_time \
                                              , time__lte = to_time).order_by("time")

            s_chart = stats_chart(request, service_stats, service_terms, service_title, service_x_title, service_y_title, 'column', True, term_names, time_format)

            p_chart = stats_chart(request, protocol_stats, protocol_terms, protocol_title, protocol_x_title, protocol_y_title, 'column', True, term_names, time_format, protocols)

            return render_to_response('metadataparser/federation_chart.html',
                                      {'form': form,
                                       'statcharts': [s_chart, p_chart],
                                      },
                                      context_instance=RequestContext(request))

        else:
            messages.error(request, _('Please correct the errors indicated'
                                      ' below'))
    else:
        form = ChartForm(instance=federation)

    return render_to_response('metadataparser/federation_chart.html',
                              {'form': form,
                              },
                              context_instance=RequestContext(request))


def fed_pie_chart(request, federation_id):
    statsConfigDict = getattr(settings, "STATS")
    terms = statsConfigDict['statistics']['entity_by_type']['terms']
    stats = model=EntityStat.objects.filter(federation = federation_id, \
                                            feature__in = terms).order_by('-time')[0:len(terms)]
    term_names = statsConfigDict['feature_names']

    #Step 1: Create a DataPool with the data we want to retrieve.
    statdata = \
        DataPool(
           series=[{'options': { 'source': stats },
                    'legend_by': 'feature',
                    'terms': ['feature', 'value'],
                  }]
        )

    #Step 2: Create the Chart object
    series_options = \
          [{'options': { 'type': 'pie', 'stacking': False, 'size': '70%' },
            'terms':{ 'feature': [ 'value' ] }}]

    cht = Chart(
            datasource = statdata,
            series_options = series_options,
            chart_options = {
               'title': { 'text': ' ' },
               'credits': { 'enabled': False}
            },
    )

    #Step 3: Send the chart object to the template.
    return cht

def stats_chart(request, stats, terms, title, x_title, y_title, chart_type, stacking, term_names, time_format, protocols = None):
    #Step 1: Create a DataPool with the data we want to retrieve.
    statdata = \
        DataPool(
           series=[{'options': {
                       'source': stats.filter(feature=term)},
                       'legend_by': 'feature',
                       'terms': [{'time_%s' %term :'time'}, 
                                 {term_names[term] : 'value', 'name': 'feature'}]}
                  for term in terms
                  ]
        )

    #Step 2: Create the Chart object
    if protocols:
        series_options = []
        for stack in range(len(protocols)):
            protocol = protocols[stack]
            for term in terms:
                if term.endswith(protocol):
                    series_options += \
                      [{'options':{
                          'type': chart_type,
                          'stacking': stacking,
                          'stack': stack,
                          },
                        'terms':{
                          'time_%s' %term: [{term_names[term]: {'stack': stack,}}],
                          }}]
    else:
        series_options = \
          [{'options':{
              'type': chart_type,
              'stacking': stacking},
            'terms':{
              'time_%s' %term: [term_names[term]]
              for term in terms
              }}]
          

    cht = Chart(
            datasource = statdata,
            series_options = series_options,
            chart_options =
              {'title': {
                   'text': title},
               'xAxis': {
                    'title': {
                       'text': x_title},
                    'labels': {
                       'rotation': -45,
                       'align': 'right'},
                       'max': 10,
                         },
               'yAxis': {
                    'title': {
                       'text': y_title},
                    'minorTickInterval': 'auto'
                         },
               'credits': {
                       'enabled': False},
               'scrollbar': {
                       'enabled': True},
               'zoomType': 'xy',
               },
            x_sortf_mapf_mts=(None, lambda i: datetime.fromtimestamp(time.mktime(i.replace(tzinfo=tz.gettz('UTC')).astimezone(tz.tzlocal()).timetuple())).strftime(time_format), False)
    )

    #Step 3: Send the chart object to the template.
    return cht


@profile(name='Entity view')
def entity_view(request, entityid):
    entityid = unquote(entityid)
    entityid = RESCUE_SLASH.sub("\\1/\\2", entityid)

    entity = get_object_or_404(Entity, entityid=entityid)

    if 'format' in request.GET:
        return export_entity(request.GET.get('format'), entity)

    if 'viewxml' in request.GET:
        serialized = entity.xml
        response = HttpResponse(serialized, content_type='application/xml')
        #response['Content-Disposition'] = ('attachment; filename=%s.xml'
        #                               % slugify(entity))
        return response

    return render_to_response('metadataparser/entity_view.html',
            {'entity': entity,
             'lang': request.GET.get('lang', 'en') 
            }, context_instance=RequestContext(request))


@user_can_edit(Entity)
def entity_edit(request, federation_slug=None, entity_id=None):
    entity = None
    federation = None
    if federation_slug:
        federation = get_object_or_404(Federation, slug=federation_slug)
        if entity_id:
            entity = get_object_or_404(Entity, id=entity_id,
                                       federations__id=federation.id)
    if entity_id and not federation_slug:
        entity = get_object_or_404(Entity, id=entity_id)

    if request.method == 'POST':
        form = EntityForm(request.POST, request.FILES, instance=entity)
        if form.is_valid():
            form.save()
            if (federation and
               not federation in form.instance.federations.all()):
                form.instance.federations.add(federation)
                form.instance.save()
            if entity:
                messages.success(request, _('Entity modified successfully'))
            else:
                messages.success(request, _('Entity created successfully'))
            return HttpResponseRedirect(form.instance.get_absolute_url())

        else:
            messages.error(request, _('Please correct the errors indicated'
                                      ' below'))
    else:
        form = EntityForm(instance=entity)

    return render_to_response('metadataparser/entity_edit.html',
                              {'form': form,
                               'federation': federation},
                              context_instance=RequestContext(request))


@user_can_edit(Entity, True)
def entity_delete(request, entity_id):
    entity = get_object_or_404(Entity, id=entity_id)
    messages.success(request,
                     _(u"%(entity)s entity was deleted successfully"
                     % {'entity': unicode(entity)}))
    entity.delete()
    return HttpResponseRedirect(reverse('index'))


def entity_comment(request, federation_slug=None, entity_id=None):
    entity = None
    federation = None
    if federation_slug:
        federation = get_object_or_404(Federation, slug=federation_slug)
        if entity_id:
            entity = get_object_or_404(Entity, id=entity_id,
                                       federations__id=federation.id)
    if entity_id and not federation_slug:
        entity = get_object_or_404(Entity, id=entity_id)

    if request.method == 'POST':
        form = EntityCommentForm(request.POST, request.FILES, instance=entity)
        if form.is_valid():
            mailConfigDict = getattr(settings, "MAIL_CONFIG")
            try:
                subject = mailConfigDict['comment_subject'] %entity
                sendMail(form.data['email'], subject, form.data['comment'])
                messages.success(request, _('Comment posted successfully'))
            except Exception, errorMessage:
                messages.error(request, _('Comment could not be posted successfully: %s' %errorMessage))

            return HttpResponseRedirect(form.instance.get_absolute_url())

        else:
            messages.error(request, _('Please correct the errors indicated'
                                      ' below'))
    else:
        form = EntityCommentForm(instance=entity)

    return render_to_response('metadataparser/entity_comment.html',
                              {'form': form,
                              },
                              context_instance=RequestContext(request))


def entity_proposal(request, federation_slug=None, entity_id=None):
    entity = None
    federation = None
    if federation_slug:
        federation = get_object_or_404(Federation, slug=federation_slug)
        if entity_id:
            entity = get_object_or_404(Entity, id=entity_id,
                                       federations__id=federation.id)
    if entity_id and not federation_slug:
        entity = get_object_or_404(Entity, id=entity_id)

    if request.method == 'POST':
        form = EntityProposalForm(request.POST, request.FILES, instance=entity)
     
        if form.is_valid():
            mailConfigDict = getattr(settings, "MAIL_CONFIG")
            try:
                subject = mailConfigDict['proposal_subject'] %entity
                body = ''
                myDict = dict(form.data.iterlists())
                for f in myDict['federations']:
                    if body:
                        body += ', %s' %f
                    else:
                        body += ' %s' %f
                body = mailConfigDict['proposal_body'] %(entity, body, form.data['comment'])
                sendMail(form.data['email'], subject, body)
                messages.success(request, _('Proposal posted successfully'))
            except Exception, errorMessage:
                messages.error(request, _('Proposal could not be posted successfully: %s' %errorMessage))

            return HttpResponseRedirect(form.instance.get_absolute_url())

        else:
            messages.error(request, _('Please correct the errors indicated'
                                      ' below'))
    else:
        form = EntityProposalForm(instance=entity)

    return render_to_response('metadataparser/entity_proposal.html',
                              {'form': form,
                              },
                              context_instance=RequestContext(request))
        
#     else:
#         messages.warning(request, _('This entity is already in all federations.'))


## Querys
def search_service(request):
    filters = {}
    objects = []
    if request.method == 'GET':
        if 'entityid' in request.GET:
            form = ServiceSearchForm(request.GET)
            if form.is_valid():
                entityid = form.cleaned_data['entityid']
                entityid = entityid.strip()
                filters['entityid__icontains'] = entityid

        else:
            form = ServiceSearchForm()
        entity_type = request.GET.get('entity_type', None)
        if entity_type:
            filters['entity_type'] = entity_type
        if filters:
            objects = Entity.objects.filter(**filters)

    if objects and 'format' in request.GET.keys():
        return export_query_set(request.GET.get('format'), objects,
                                'entities_search_result', ('', 'types', 'federations'))

    entities = []
    for entity in objects:
        entities.append({
            'entityid': entity.entityid,
            'name': entity.name,
            'absolute_url': entity.get_absolute_url(),
            'types': [unicode(item) for item in entity.types.all()],
            'federations': [(unicode(item.name), item.get_absolute_url()) for item in entity.federations.all()],
        })

    return render_to_response('metadataparser/service_search.html',
        {'searchform': form,
         'object_list': entities,
         'show_filters': False,
        }, context_instance=RequestContext(request))

def met_logout(request):
    logout(request)
    return HttpResponseRedirect(request.GET.get("next", "/"))
