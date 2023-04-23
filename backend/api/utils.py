from typing import Dict

from rest_framework import exceptions, status
from rest_framework.response import Response

from recipes.models import RecipeIngredient


def get_end_letter(value):
    end_lib: Dict[int, str] = {5: '', 2: 'а', 0: ''}

    for my_key in end_lib:

        if value % 10 >= my_key:
            return end_lib[my_key]

    return ''


def create_or_delete_record(request, record, serializer_data, params):
    if request.method == 'POST':

        if record.exists():
            raise exceptions.ValidationError('records already exists.')

        record.create(user=request.user, **params)
        return Response(serializer_data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        if not record.exists():
            raise exceptions.ValidationError('records does not exists.')
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def get_recipe_serializer():
    from api.serializers import FavoritListSerializer

    return FavoritListSerializer
