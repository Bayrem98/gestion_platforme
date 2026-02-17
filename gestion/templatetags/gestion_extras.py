from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return []