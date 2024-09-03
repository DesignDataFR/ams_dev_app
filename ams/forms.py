from django import forms
from .models import AmsListStatus

class StatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=[])
    comment = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(StatusUpdateForm, self).__init__(*args, **kwargs)
        self.fields['status'].choices = self.get_status_choices()

    def get_status_choices(self):
        choices = [(status.StatusCode, status.StatusName) for status in AmsListStatus.objects.all()]
        return choices

class MessageForm(forms.Form):
    USER_OR_MAH_CHOICES = [
        ('user', 'User'),
        ('mah', 'MAH'),
        ('both', 'User & MAH'),
    ]
    text = forms.CharField(widget=forms.Textarea, required=True)
    user_or_mah_choice = forms.ChoiceField(choices=USER_OR_MAH_CHOICES, widget=forms.RadioSelect, required=True)

class BulkStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super(BulkStatusUpdateForm, self).__init__(*args, **kwargs)
        self.fields['status'].choices = self.get_status_choices()

    def get_status_choices(self):
        choices = [(status.StatusCode, status.StatusName) for status in AmsListStatus.objects.all()]
        return choices
    

class BulkMessageForm(forms.Form):
    USER_OR_MAH_CHOICES = [
        ('user', 'User'),
        ('mah', 'MAH'),
        ('both', 'User & MAH'),
    ]
    text = forms.CharField(widget=forms.Textarea, required=True, label="Message")
    user_or_mah_choice = forms.ChoiceField(choices=USER_OR_MAH_CHOICES, widget=forms.RadioSelect, required=True, label="Send to")

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text')
        user_or_mah_choice = cleaned_data.get('user_or_mah_choice')

        if not text:
            self.add_error('text', "Please enter a message.")
        if not user_or_mah_choice:
            self.add_error('user_or_mah_choice', "Please select a recipient.")
        
        return cleaned_data