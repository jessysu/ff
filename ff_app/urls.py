from django.conf.urls import url
from ff_app import views

urlpatterns = [
    url('^$', views.index, name='index')
]