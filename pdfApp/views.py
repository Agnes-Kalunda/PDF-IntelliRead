from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest


def index(request):
    return render(request, 'index.html')
