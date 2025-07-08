from django import template
import os

register = template.Library()

@register.filter
def file_icon(url):
    ext = os.path.splitext(url.lower())[1]
    if ext == '.pdf':
        return '<span class="badge bg-danger text-white"><i class="bi bi-file-earmark-pdf-fill"></i> PDF</span>'
    elif ext in ['.doc', '.docx']:
        return '<span class="badge bg-primary text-white"><i class="bi bi-file-earmark-word-fill"></i> DOC</span>'
    elif ext in ['.jpg', '.jpeg', '.png']:
        return '<span class="badge bg-info text-dark"><i class="bi bi-image-fill"></i> Image</span>'
    else:
        return '<span class="badge bg-secondary text-white"><i class="bi bi-file-earmark-fill"></i> File</span>'

@register.filter
def is_pdf(url):
    return url.lower().endswith('.pdf')
