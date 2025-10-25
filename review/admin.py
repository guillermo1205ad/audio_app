from django.contrib import admin
from .models import Audio, Segment

class SegmentInline(admin.TabularInline):
    """
    Inline display of Segments within the Audio admin page.
    """
    model = Segment
    extra = 0
    fields = ('start', 'end', 'revisado', 'version', 'locked_by', 'locked_at')
    readonly_fields = ('locked_by', 'locked_at')

@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    """
    Admin configuration for Audio model.
    """
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title',)
    inlines = [SegmentInline]

@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Segment model.
    """
    list_display = ('audio', 'start', 'end', 'revisado', 'version', 'locked_by', 'locked_at')
    list_filter = ('revisado', 'version', 'locked_by')
    search_fields = ('audio__title',)
    readonly_fields = ('locked_by', 'locked_at')
