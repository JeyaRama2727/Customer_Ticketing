"""\nJeyaRamaDesk — Knowledge Base Admin\n"""

from django.contrib import admin
from .models import KBCategory, Article, ArticleAttachment


class ArticleAttachmentInline(admin.TabularInline):
    model = ArticleAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(KBCategory)
class KBCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'order', 'is_active', 'article_count']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'status', 'author',
        'views_count', 'is_featured', 'is_internal', 'published_at',
    ]
    list_filter = ['status', 'category', 'is_internal', 'is_featured']
    search_fields = ['title', 'body', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleAttachmentInline]
    readonly_fields = ['id', 'views_count', 'helpful_yes', 'helpful_no', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_editable = ['status', 'is_featured']
    raw_id_fields = ['author']

    fieldsets = (
        ('Content', {
            'fields': ('id', 'title', 'slug', 'category', 'body', 'excerpt'),
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_internal', 'is_featured', 'published_at'),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Engagement', {
            'fields': ('views_count', 'helpful_yes', 'helpful_no'),
        }),
        ('Metadata', {
            'fields': ('author', 'created_at', 'updated_at'),
        }),
    )

    actions = ['publish_articles', 'archive_articles']

    @admin.action(description='Publish selected articles')
    def publish_articles(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='published', published_at=timezone.now())

    @admin.action(description='Archive selected articles')
    def archive_articles(self, request, queryset):
        queryset.update(status='archived')
