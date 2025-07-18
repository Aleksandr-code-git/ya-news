import pytest

from django.test.client import Client
from django.urls import reverse
from http import HTTPStatus
from pytest_django.asserts import assertRedirects

from news.models import News, Comment


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def news(db):
    news = News.objects.create(
        title='Заголовок',
        text='Текст',
    )
    return news


@pytest.fixture
def comment(author, news):
    comment = Comment.objects.create(
        text='Текст Коментария',
        author=author,
        news=news
    )
    return comment


@pytest.mark.parametrize(
    'name',
    ('news:detail', 'news:home', 'users:login', 'users:logout', 'users:signup')
)
def test_pages_availability(
    client,
    name,
    news
):
    if name == 'news:detail':
        url = reverse(name, args=(news.id,))
    else:
        url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    [
        ('not_author_client', HTTPStatus.NOT_FOUND),
        ('author_client', HTTPStatus.OK)
    ],
)
@pytest.mark.parametrize(
    'name',
    ('news:delete', 'news:edit')
)
def test_availability_for_comment_edit_delete(
    parametrized_client,
    name,
    comment,
    expected_status,
    request
):
    client = request.getfixturevalue(parametrized_client)
    url = reverse(name, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name',
    ('news:delete', 'news:edit')
)
def test_redirect_for_anonymous(
    client,
    name,
    comment,
):
    login_url = reverse('users:login')
    url = reverse(name, args=(comment.id,))
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
