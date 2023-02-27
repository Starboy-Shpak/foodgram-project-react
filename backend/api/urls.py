from django.urls import path, include

from api.spectacular.urls import urlpatterns as doc_urls
from users.urls import urlpatterns as users
from foodgram.urls import urlpatterns as foodgram

app_name = 'api'


urlpatterns = []

urlpatterns += doc_urls
urlpatterns += users
urlpatterns += foodgram
