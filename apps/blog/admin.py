from django.contrib import admin
from .models import Article, Category, Comment

# Inline для отображения комментариев на странице статьи
class CommentInline(admin.TabularInline): # TabularInline для компактного вида
    model = Comment
    extra = 1 # Количество пустых форм для добавления новых комментариев
    readonly_fields = ('author', 'created_at', 'updated_at') # Автор не меняется, даты тоже
    fields = ('author', 'content', 'created_at', 'updated_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)} # Автозаполнение slug при создании

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'author')
    search_fields = ('title', 'content', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    # Если бы у Article был slug:
    # prepopulated_fields = {'slug': ('title',)}
    
    # Полезно для отображения автора и категории без доп. запросов
    list_select_related = ('author', 'category') 
    
    # Поля только для чтения
    readonly_fields = ('created_at', 'updated_at')

    # Добавляем инлайн для комментариев
    inlines = [CommentInline]

    # Можно настроить поля для редактирования
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author', 'category')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'article', 'content_preview', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'article__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_select_related = ('author', 'article')
    readonly_fields = ('created_at', 'updated_at')

    # Поле для предпросмотра контента в списке
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Предпросмотр"
