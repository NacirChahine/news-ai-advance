from django import forms
from .models import NewsArticle, NewsSource


class ArticleForm(forms.ModelForm):
    """Form for reporters to create and edit their own articles"""
    
    class Meta:
        model = NewsArticle
        fields = ['title', 'content', 'summary', 'image_url', 'source', 'published_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter article title',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Enter article content',
                'required': True
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter a brief summary (optional)'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image URL (optional)'
            }),
            'source': forms.Select(attrs={
                'class': 'form-select'
            }),
            'published_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        help_texts = {
            'source': 'Leave blank if this is your original article',
            'summary': 'A brief summary of the article (optional)',
            'image_url': 'URL to an image for this article (optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make source optional
        self.fields['source'].required = False
        self.fields['source'].empty_label = "-- Original Article (No Source) --"
        
        # Format the published_date for datetime-local input
        if self.instance and self.instance.pk and self.instance.published_date:
            self.initial['published_date'] = self.instance.published_date.strftime('%Y-%m-%dT%H:%M')

