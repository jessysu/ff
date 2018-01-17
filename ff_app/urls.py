from django.conf.urls import url
from ff_app import views

urlpatterns = [
    #url('^$', views.index, name='index')
    url(r'^sym/(?P<ss>.*)/(?P<d>.*)/$', views.symbol_landing, name='symbol_landing'),
    url(r'^sym/(?P<ss>.*)/', views.symbol_landing, name='symbol_landing'),
    url(r'^hsd/(?P<ds>\d{2}\/\d{2}\/\d{4})/(?P<de>\d{2}\/\d{2}\/\d{4})/(?P<ss>.*)/$', views.hindsight_daily, name='hindsight_daily'),
    url(r'^hsd/(?P<ds>\d{2}\/\d{2}\/\d{4})/(?P<de>\d{2}\/\d{2}\/\d{4})/$', views.hindsight_daily, name='hindsight_daily'),
    url(r'^hsd/(?P<ss>.*)/$', views.hindsight_daily, name='hindsight_daily'),
    url(r'^hsd/$', views.hindsight_daily, name='hindsight_daily'),
    url(r'^hsm/(?P<ds>\d{2}\/\d{4})/(?P<de>\d{2}\/\d{4})/(?P<ss>.*)/$', views.hindsight_monthly, name='hindsight_monthly'),
    url(r'^hsm/(?P<ds>\d{2}\/\d{4})/(?P<de>\d{2}\/\d{4})/$', views.hindsight_monthly, name='hindsight_monthly'),
    url(r'^hsm/(?P<ss>.*)/$', views.hindsight_monthly, name='hindsight_monthly'),
    url(r'^hsm/$', views.hindsight_monthly, name='hindsight_monthly'),
    url(r'^about/$', views.about, name='about'),
    url(r'^.*$', views.index, name='index')
]
