from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="list"),
    path("create/", views.EventCreateView.as_view(), name="create"),
    path("registrations/", views.MyRegistrationsListView.as_view(), name="my_registrations"),
    path("registrations/<uuid:pk>/cancel/", views.CancelRegistrationView.as_view(), name="cancel"),
    # <uuid:pk> converter validates the id shape at routing time (bad id -> 404).
    path("<uuid:pk>/", views.EventDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.EventUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.EventDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/register/", views.RegisterForEventView.as_view(), name="register"),
]
