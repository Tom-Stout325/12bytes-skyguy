import os
from django import template

register = template.Library()

@register.filter
def is_pdf(file_url):
    return str(file_url).lower().endswith('.pdf')



@register.filter
def file_icon(file_url):
    ext = os.path.splitext(file_url)[1].lower()
    return {
        '.pdf':  'fa-solid fa-file-pdf text-danger',
        '.doc':  'fa-solid fa-file-word text-primary',
        '.docx': 'fa-solid fa-file-word text-primary',
        '.xls':  'fa-solid fa-table text-success',
        '.xlsx': 'fa-solid fa-table text-success',
        '.jpg':  'fa-solid fa-image text-info',
        '.jpeg': 'fa-solid fa-file-image text-info',
        '.png':  'fa-regular fa-file-image text-info',
        '.zip':  'fa-solid fa-file-zipper text-warning',
        '.txt':  'fa-regular fa-file-lines text-muted',
    }.get(ext, 'fas fa-file')

