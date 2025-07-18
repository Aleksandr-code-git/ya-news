import pytest
from datetime import datetime

from pytest_django.asserts import assertRedirects
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from http import HTTPStatus

from news.forms import BAD_WORDS, WARNING
from news.models import News, Comment

pytestmark = pytest.mark.django_db

HOME_URL = reverse('news:home')

OLD_COMMENT_TEXT = 'Текст Коментария'

NEW_COMMENT_TEXT = 'TEXT'

today = datetime.today()

now = timezone.now()


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
        title='Title',
        text='text'
    )
    return news


@pytest.fixture
def comment(author, news):
    comment = Comment.objects.create(
        text=OLD_COMMENT_TEXT,
        author=author,
        news=news
    )
    return comment


@pytest.fixture
def form_data(db):
    return {
        'text': NEW_COMMENT_TEXT,
    }


@pytest.mark.parametrize(
    'parametrized_client, expected_comments',
    [('client', 0), ('author_client', 1)]
)
def test_availability_to_create_comments(
    parametrized_client,
    form_data,
    news,
    request,
    expected_comments
):
    url = reverse('news:detail', args=(news.id,))
    client = request.getfixturevalue(parametrized_client)
    response = client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == expected_comments
    if expected_comments == 1:
        assertRedirects(response, f'{url}#comments')
        comment = Comment.objects.get()
        assert comment.text == form_data['text']
        assert comment.news == news
        assert comment.author == request.getfixturevalue('author')


def test_user_cant_use_bad_words(author_client, news):
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    form = response.context['form']
    TestCase().assertFormError(
        form=form,
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.parametrize(
    'parametrized_client, expected_comments, expected_status',
    [
        ('not_author_client', 1, HTTPStatus.NOT_FOUND),
        ('author_client', 0, HTTPStatus.FOUND)
    ]
)
def test_availability_to_delete_comments(
    parametrized_client,
    news,
    request,
    expected_comments,
    comment,
    expected_status,
):
    delete_url = reverse('news:delete', args=(comment.id,))
    client = request.getfixturevalue(parametrized_client)
    response = client.delete(delete_url)
    comments_count = Comment.objects.count()
    assert comments_count == expected_comments
    assert response.status_code == expected_status
    if comments_count == 0:
        news_url = reverse('news:detail', args=(news.id,))
        url_to_comments = news_url + '#comments'
        assertRedirects(response, url_to_comments)


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    [
        ('not_author_client', HTTPStatus.NOT_FOUND),
        ('author_client', HTTPStatus.FOUND)
    ]
)
def test_availability_to_edit_comments(
    parametrized_client,
    news,
    request,
    form_data,
    comment,
    expected_status,
):
    edit_url = reverse('news:edit', args=(comment.id,))
    client = request.getfixturevalue(parametrized_client)
    response = client.post(edit_url, data=form_data)
    assert response.status_code == expected_status
    if expected_status == HTTPStatus.NOT_FOUND:
        comment.refresh_from_db()
        assert comment.text == OLD_COMMENT_TEXT
    else:
        news_url = reverse('news:detail', args=(news.id,))
        url_to_comments = news_url + '#comments'
        assertRedirects(response, url_to_comments)
        comment.refresh_from_db()
        assert comment.text == form_data['text']
