#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
#########################################################################################

from django.conf.urls import patterns, url


urlpatterns = patterns('met.metadataparser.views',
    url(r'^federation/add/$', 'federation_edit', name='federation_add'),
    url(r'^federation/(?P<federation_slug>[-\w]+)/edit/$', 'federation_edit',
        name='federation_edit'),
    url(r'^federation/(?P<federation_slug>[-\w]+)/delete/$', 'federation_delete',
        name='federation_delete'),
    url(r'^federation/(?P<federation_slug>[-\w]+)/$', 'federation_view',
        name='federation_view'),
    url(r'^federation/(?P<federation_slug>[-\w]+)/entityadd/$', 'entity_edit',
        name='entity_add'),

    url(r'^federation/(?P<federation_slug>[-\w]+)/charts/$', 'federation_charts',
        name='federation_charts'),
    url(r'^saml2/login/$', 'federation_login', name='federation_login'),
    url(r'^saml2/logout/$', 'federation_logout', name='federation_logout'),

    url(r'^entity/(?P<entity_id>.+)/edit/$', 'entity_edit', name='entity_edit'),
    url(r'^entity/(?P<entity_id>.+)/delete/$', 'entity_delete', name='entity_delete'),

    url(r'^entity/(?P<entity_id>.+)/comment/$', 'entity_comment', name='entity_comment'),
    url(r'^entity/(?P<entity_id>.+)/proposal/$', 'entity_proposal', name='entity_proposal'),

    url(r'^entity/(?P<entityid>.+)/$', 'entity_view', name='entity_view'),

    url(r'^search_service/$', 'search_service', name='search_service'),
    
    url(r'^show_less_entries/$', 'decrement_current_toplength', name='show_less_entries'),
    url(r'^show_more_entries/$', 'increment_current_toplength', name='show_more_entries'),

    )
