"""
Event form with server-side validation  [A03 / ASVS V5]. The banner field's
validators come from the model (the file-upload security pipeline).
"""

from django import forms
from django.utils import timezone

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        # Explicit allowlist of editable fields (never "__all__"); organizer is
        # set server-side in the view, never accepted from the client.
        fields = ["title", "description", "location", "start_at", "end_at",
                  "capacity", "banner", "status"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"},
                                            format="%Y-%m-%dT%H:%M"),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"},
                                          format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 4, "maxlength": 5000}),
            "title": forms.TextInput(attrs={"maxlength": 200}),
            "capacity": forms.NumberInput(attrs={"min": 1, "max": 100000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("start_at", "end_at"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + css).strip()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_at")
        end = cleaned.get("end_at")
        if start and end and end <= start:
            self.add_error("end_at", "End time must be after the start time.")
        if start and start < timezone.now():
            self.add_error("start_at", "Start time cannot be in the past.")
        return cleaned
