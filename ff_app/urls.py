from django.conf.urls import url
from ff_app import views

urlpatterns = [
    #url('^$', views.index, name='index')
    url(r'^hsd/$', views.hindsight_daily, name='hindsight_daily'),
    url(r'^.*$', views.index, name='index')
]
