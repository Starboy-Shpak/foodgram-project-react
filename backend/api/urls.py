from foodgram.urls import urlpatterns as foodgram
from users.urls import urlpatterns as users

app_name = 'api'


urlpatterns = []

urlpatterns += users
urlpatterns += foodgram
