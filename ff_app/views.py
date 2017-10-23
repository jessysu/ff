import MySQLdb

from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    ds = request.POST.get('ds', '')
    de = request.POST.get('de', '')
    print("ds = " + ds)
    print("de = " + de)
    rs = {}
    return render(request, 'home.html', rs)
    
