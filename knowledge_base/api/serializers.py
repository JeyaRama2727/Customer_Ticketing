"""
JeyaRamaDesk — Knowledge Base API Serializers
"""

from rest_framework import serializers
from knowledge_base.models import KBCategory, Article


class KBCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = KBCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'parent', 'order', 'is_active', 'article_count',
        ]
        read_only_fields = ['id']


class ArticleListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    author_name = serializers.CharField(source='author.full_name', read_only=True, default='')
    reading_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'category', 'category_name',
            'excerpt', 'status', 'views_count', 'is_featured',
            'is_internal', 'author', 'author_name', 'reading_time',
            'published_at', 'updated_at',
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    author_name = serializers.CharField(source='author.full_name', read_only=True, default='')
    helpfulness_rate = serializers.IntegerField(read_only=True)
    reading_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'category', 'category_name',
            'body', 'excerpt', 'status', 'meta_title', 'meta_description',
            'views_count', 'helpful_yes', 'helpful_no', 'helpfulness_rate',
            'is_internal', 'is_featured', 'author', 'author_name',
            'reading_time', 'created_at', 'updated_at', 'published_at',
        ]
        read_only_fields = ['id', 'views_count', 'helpful_yes', 'helpful_no', 'created_at', 'updated_at']
