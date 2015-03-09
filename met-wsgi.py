import os
import sys

current_directory = os.path.dirname(__file__)
module_name = os.path.basename(current_directory)
home_directory = os.environ.get('HOME', current_directory)

activate_this = os.path.join(home_directory, '..', 'met-venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.append(current_directory)
sys.path.append(os.path.join(current_directory, 'met'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'met.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# If you want to enable a profiler, you can use repoze.profile
# from here: https://pypi.python.org/pypi/repoze.profile/0.8.
# 
# Please, install repoze.profile in met-venv with:
# $ easy_install repoze.profile
# and then uncomment the following part of the file.

#from repoze.profile.profiler import AccumulatingProfileMiddleware
#application = AccumulatingProfileMiddleware(
#    application,
#    log_filename='/tmp/met-profile.log',
#    discard_first_request=False,
#    flush_at_shutdown=True,
#    path='/_profile'
#)
