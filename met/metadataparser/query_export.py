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

import csv
from xml.dom.minidom import Document
import hashlib

from django.http import HttpResponse, HttpResponseBadRequest
from django.template.defaultfilters import slugify
import simplejson as json


## Taken from http://djangosnippets.org/snippets/790/
def export_csv(qs, filename, fields=None):
    model = qs.model
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = ('attachment; filename=%s.csv'
                                       % slugify(filename))
    writer = csv.writer(response)
    # Write headers to CSV file
    if fields:
        headers = fields
    else:
        headers = []
        for field in model._meta.fields:
            headers.append(field.name)
        fields = headers
    _headers = []
    for header in headers:
        if header:
            _headers.append(header)
        else:
            _headers.append(unicode(model._meta.verbose_name))

    headers = _headers

    writer.writerow(headers)
    # Write data to CSV file
    for obj in qs:
        row = []
        for field in fields:
            if field == '':
                val = unicode(obj)
            else:
                val = getattr(obj, field)
                if getattr(val, 'all', None):
                    val = ', '.join([unicode(item) for item in val.all()])
                # work around csv unicode limitation
                elif type(val) == unicode:
                    val = val.encode("utf-8")
            row.append(val)
        writer.writerow(row)
    # Return CSV file to browser as download
    return response


def export_json(qs, filename, fields=None):
    model = qs.model

    if not fields:
        headers = []
        for field in model._meta.fields:
            headers.append(field.name)
        fields = headers
    objs = []
    for obj in qs:
        item = {}
        for field in fields:
            if field == '':
                field = unicode(obj._meta.verbose_name)
                val = unicode(obj)
            else:
                val = getattr(obj, field)
                if getattr(val, 'all', None):
                    val = [unicode(i) for i in val.all()]
                # work around csv unicode limitation
                elif type(val) == unicode:
                    val = val.encode("utf-8")
            item[field] = val
        objs.append(item)
    # Return JS file to browser as download
    serialized = json.dumps(objs)
    response = HttpResponse(serialized, content_type='application/json')
    response['Content-Disposition'] = ('attachment; filename=%s.json'
                                       % slugify(filename))
    return response


def export_xml(qs, filename, fields=None):
    model = qs.model
    xml = Document()
    root = xml.createElement(filename)
    xml.appendChild(root)
    if not fields:
        headers = []
        for field in model._meta.fields:
            headers.append(field.name)
        fields = headers
    for obj in qs:
        item = xml.createElement(model._meta.object_name)
        item.setAttribute("id", unicode(obj))
        for field in fields:
            if field != '':
                val = getattr(obj, field)
                if getattr(val, 'all', None):
                    for v in val.all():
                        element = xml.createElement(field)
                        xmlval = xml.createTextNode(unicode(v))
                        element.appendChild(xmlval)
                        item.appendChild(element)
                else:
                    if callable(val):
                        val = val()
                    # work around csv unicode limitation
                    elif type(val) == unicode:
                        val = val.encode("utf-8")

                    element = xml.createElement(field)
                    xmlval = xml.createTextNode(val)
                    element.appendChild(xmlval)
                    item.appendChild(element)
        root.appendChild(item)
    # Return xml file to browser as download
    response = HttpResponse(xml.toxml(), content_type='application/xml')
    response['Content-Disposition'] = ('attachment; filename=%s.xml'
                                       % slugify(filename))
    return response


export_modes = {
            'csv': export_csv,
            'json': export_json,
            'xml': export_xml,
        }


def export_query_set(mode, qs, filename, fields=None):
    if mode in export_modes:
        return export_modes[mode](qs, filename, fields)
    else:
        content = "Error 400, Format %s is not supported" % mode
        return HttpResponseBadRequest(content)
