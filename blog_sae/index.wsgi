import sae
from blog_sae import wsgi

application = sae.create_wsgi_app(wsgi.application)