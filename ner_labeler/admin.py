"""
Django Admin interface for KDPII NER Labeler
Enhanced admin interface for managing projects, tasks, annotations, and labels
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.http import HttpResponse
from django.conf import settings
import json
import csv

from .models import Project, Task, Annotation, Label


class LabelInline(admin.TabularInline):
    """Inline interface for Labels in Project admin"""
    model = Label
    extra = 1
    fields = ('value', 'background', 'hotkey', 'category', 'is_active', 'sort_order')
    readonly_fields = ('usage_count_display',)
    
    def usage_count_display(self, obj):
        if obj.pk:
            return obj.get_usage_count()
        return 0
    usage_count_display.short_description = "Usage Count"


class AnnotationInline(admin.TabularInline):
    """Inline interface for Annotations in Task admin"""
    model = Annotation
    extra = 0
    fields = ('start', 'end', 'text', 'labels_display', 'confidence', 'identifier_type', 'overlapping')
    readonly_fields = ('labels_display', 'uuid', 'span_length_display')
    can_delete = True
    
    def labels_display(self, obj):
        if obj.labels:
            labels_html = []
            for label in obj.labels:
                # Get the label color if it exists
                try:
                    label_obj = Label.objects.filter(value=label, project=obj.task.project).first()
                    if label_obj:
                        color = label_obj.background
                        labels_html.append('<span style="background-color: {}; padding: 2px 6px; border-radius: 3px; margin-right: 3px; color: white; font-size: 11px;">{}</span>'.format(color, label))
                    else:
                        labels_html.append('<span style="background-color: #666; padding: 2px 6px; border-radius: 3px; margin-right: 3px; color: white; font-size: 11px;">{}</span>'.format(label))
                except:
                    labels_html.append('<span style="background-color: #666; padding: 2px 6px; border-radius: 3px; margin-right: 3px; color: white; font-size: 11px;">{}</span>'.format(label))
            return mark_safe(''.join(labels_html))
        return "-"
    labels_display.short_description = "Labels"

    def span_length_display(self, obj):
        return obj.span_length if obj.pk else 0
    span_length_display.short_description = "Length"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Project model"""
    
    list_display = ('name', 'owner_id', 'task_count_display', 'completed_task_count_display', 
                   'completion_percentage_display', 'annotation_count_display', 'is_active', 'updated_at')
    list_filter = ('is_active', 'allow_overlapping_annotations', 'require_all_labels', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('-updated_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner_id')
        }),
        ('Project Settings', {
            'fields': ('is_active', 'allow_overlapping_annotations', 'require_all_labels')
        }),
        ('Statistics', {
            'fields': ('stats_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'stats_display')
    
    inlines = [LabelInline]
    
    actions = ['export_project_data', 'duplicate_project', 'reset_project_stats']
    
    def task_count_display(self, obj):
        count = obj.task_count
        if count > 0:
            url = reverse('admin:ner_labeler_task_changelist') + '?project__id__exact={}'.format(obj.id)
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    task_count_display.short_description = "Tasks"
    task_count_display.admin_order_field = 'task_count'
    
    def completed_task_count_display(self, obj):
        count = obj.completed_task_count
        if count > 0:
            url = reverse('admin:ner_labeler_task_changelist') + '?project__id__exact={}&is_completed__exact=1'.format(obj.id)
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    completed_task_count_display.short_description = "Completed"
    
    def completion_percentage_display(self, obj):
        percentage = obj.completion_percentage
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 50 else '#dc3545'
        percentage_str = "{:.1f}".format(percentage)
        return format_html(
            '<div style="width: 100px; background: #f8f9fa; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; padding: 2px; text-align: center; color: white; font-size: 11px;">{}%</div>'
            '</div>',
            percentage, color, percentage_str
        )
    completion_percentage_display.short_description = "Progress"
    
    def annotation_count_display(self, obj):
        count = obj.annotation_count
        if count > 0:
            url = reverse('admin:ner_labeler_annotation_changelist') + '?task__project__id__exact={}'.format(obj.id)
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    annotation_count_display.short_description = "Annotations"
    
    def stats_display(self, obj):
        if obj.pk:
            distribution = obj.get_label_distribution()
            stats_html = []
            stats_html.append('<p><strong>Tasks:</strong> {} total, {} completed</p>'.format(obj.task_count, obj.completed_task_count))
            stats_html.append('<p><strong>Annotations:</strong> {} total</p>'.format(obj.annotation_count))
            if distribution:
                stats_html.append('<p><strong>Label Distribution:</strong></p>')
                stats_html.append('<ul>')
                for label, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
                    stats_html.append('<li>{}: {}</li>'.format(label, count))
                stats_html.append('</ul>')
            return mark_safe(''.join(stats_html))
        return "Statistics will be available after saving."
    stats_display.short_description = "Project Statistics"
    
    def export_project_data(self, request, queryset):
        """Export project data as JSON"""
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="projects_export.json"'
        
        data = []
        for project in queryset:
            project_data = project.to_dict(include_stats=True)
            # Include tasks and annotations
            project_data['tasks'] = []
            for task in project.tasks.all():
                task_data = task.to_dict(include_annotations=True)
                project_data['tasks'].append(task_data)
            data.append(project_data)
        
        response.write(json.dumps(data, indent=2, ensure_ascii=False))
        return response
    export_project_data.short_description = "Export selected projects as JSON"
    
    def duplicate_project(self, request, queryset):
        """Duplicate selected projects"""
        for project in queryset:
            # Create duplicate
            project.pk = None
            project.name = "{} (Copy)".format(project.name)
            project.save()
        
        count = queryset.count()
        self.message_user(request, "{} project(s) duplicated successfully.".format(count))
    duplicate_project.short_description = "Duplicate selected projects"
    
    def reset_project_stats(self, request, queryset):
        """Reset completion status for all tasks in selected projects"""
        total_tasks = 0
        for project in queryset:
            tasks = project.tasks.filter(is_completed=True)
            total_tasks += tasks.count()
            tasks.update(is_completed=False, completion_time=None)
        
        self.message_user(request, "Reset completion status for {} task(s).".format(total_tasks))
    reset_project_stats.short_description = "Reset project completion stats"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Task model"""
    
    list_display = ('uuid_short', 'text_preview', 'project', 'is_completed', 'completion_time', 
                   'annotation_count_display', 'entity_count_display', 'identifier_type', 'updated_at')
    list_filter = ('is_completed', 'identifier_type', 'project', 'created_at', 'updated_at')
    search_fields = ('uuid', 'text', 'original_filename')
    list_editable = ('is_completed', 'identifier_type')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Task Content', {
            'fields': ('text', 'original_filename', 'line_number')
        }),
        ('Task Status', {
            'fields': ('is_completed', 'completion_time', 'identifier_type')
        }),
        ('Relationships', {
            'fields': ('project', 'annotator_id')
        }),
        ('Metadata', {
            'fields': ('uuid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('task_stats_display',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'task_stats_display')
    
    inlines = [AnnotationInline]
    
    actions = ['mark_completed', 'mark_incomplete', 'export_label_studio', 'export_conll']
    
    def uuid_short(self, obj):
        return "{}...".format(obj.uuid[:8])
    uuid_short.short_description = "UUID"
    
    def text_preview(self, obj):
        preview = obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
        return format_html('<span title="{}">{}</span>', obj.text, preview)
    text_preview.short_description = "Text"
    
    def annotation_count_display(self, obj):
        count = obj.annotation_count
        if count > 0:
            url = reverse('admin:ner_labeler_annotation_changelist') + '?task__id__exact={}'.format(obj.id)
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    annotation_count_display.short_description = "Annotations"
    
    def entity_count_display(self, obj):
        return obj.entity_count
    entity_count_display.short_description = "Entities"
    
    def task_stats_display(self, obj):
        if obj.pk:
            stats_html = []
            stats_html.append('<p><strong>Annotations:</strong> {}</p>'.format(obj.annotation_count))
            stats_html.append('<p><strong>Unique Entities:</strong> {}</p>'.format(obj.entity_count))
            
            overlapping = obj.get_overlapping_annotations()
            if overlapping:
                stats_html.append('<p><strong>Overlapping Annotations:</strong> {}</p>'.format(len(overlapping)))
            
            return mark_safe(''.join(stats_html))
        return "Statistics will be available after saving."
    task_stats_display.short_description = "Task Statistics"
    
    def mark_completed(self, request, queryset):
        """Mark selected tasks as completed"""
        updated = queryset.update(is_completed=True)
        self.message_user(request, "{} task(s) marked as completed.".format(updated))
    mark_completed.short_description = "Mark selected tasks as completed"
    
    def mark_incomplete(self, request, queryset):
        """Mark selected tasks as incomplete"""
        updated = queryset.update(is_completed=False, completion_time=None)
        self.message_user(request, "{} task(s) marked as incomplete.".format(updated))
    mark_incomplete.short_description = "Mark selected tasks as incomplete"
    
    def export_label_studio(self, request, queryset):
        """Export selected tasks in Label Studio format"""
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="tasks_label_studio.json"'
        
        data = []
        for task in queryset:
            data.append(task.export_label_studio_format())
        
        response.write(json.dumps(data, indent=2, ensure_ascii=False))
        return response
    export_label_studio.short_description = "Export as Label Studio format"
    
    def export_conll(self, request, queryset):
        """Export selected tasks in CoNLL format"""
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="tasks_conll.txt"'
        
        output = []
        for task in queryset:
            output.append("# Task: {}".format(task.uuid))
            output.append(task.export_conll_format())
            output.append("")  # Empty line between tasks
        
        response.write('\n'.join(output))
        return response
    export_conll.short_description = "Export as CoNLL format"


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Annotation model"""
    
    list_display = ('uuid_short', 'text_preview', 'task_link', 'labels_display', 'confidence', 
                   'identifier_type', 'span_info', 'overlapping', 'updated_at')
    list_filter = ('confidence', 'identifier_type', 'overlapping', 'task__project', 'created_at')
    search_fields = ('uuid', 'text', 'task__uuid', 'labels')
    list_editable = ('confidence', 'identifier_type', 'overlapping')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Annotation Content', {
            'fields': ('text', 'start', 'end', 'labels')
        }),
        ('Classification', {
            'fields': ('confidence', 'identifier_type', 'overlapping')
        }),
        ('Relationships', {
            'fields': ('task', 'entity_id', 'related_annotations', 'relationships')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uuid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    
    actions = ['set_high_confidence', 'set_medium_confidence', 'set_low_confidence', 'mark_overlapping', 'export_csv']
    
    def uuid_short(self, obj):
        return "{}...".format(obj.uuid[:8])
    uuid_short.short_description = "UUID"
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Text"
    
    def task_link(self, obj):
        url = reverse('admin:ner_labeler_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.uuid[:8] + "...")
    task_link.short_description = "Task"
    
    def labels_display(self, obj):
        if obj.labels:
            labels_html = []
            for label in obj.labels:
                # Get the label color if it exists
                try:
                    label_obj = Label.objects.filter(value=label, project=obj.task.project).first()
                    if label_obj:
                        color = label_obj.background
                        labels_html.append('<span style="background-color: {}; padding: 2px 6px; border-radius: 3px; margin-right: 3px; color: white; font-size: 11px;">{}</span>'.format(color, label))
                    else:
                        labels_html.append('<span style="background-color: #666; padding: 2px 6px; border-radius: 3px; margin-right: 3px; color: white; font-size: 11px;">{}</span>'.format(label))
                except:
                    labels_html.append('<span style="background-color: #666; padding: 2px 6px; border-radius: 3px; margin-right: 3px; color: white; font-size: 11px;">{}</span>'.format(label))
            return mark_safe(''.join(labels_html))
        return "-"
    labels_display.short_description = "Labels"
    
    def span_info(self, obj):
        return "{}-{} ({})".format(obj.start, obj.end, obj.span_length)
    span_info.short_description = "Span"
    
    def set_high_confidence(self, request, queryset):
        updated = queryset.update(confidence='high')
        self.message_user(request, "{} annotation(s) set to high confidence.".format(updated))
    set_high_confidence.short_description = "Set confidence to High"
    
    def set_medium_confidence(self, request, queryset):
        updated = queryset.update(confidence='medium')
        self.message_user(request, "{} annotation(s) set to medium confidence.".format(updated))
    set_medium_confidence.short_description = "Set confidence to Medium"
    
    def set_low_confidence(self, request, queryset):
        updated = queryset.update(confidence='low')
        self.message_user(request, "{} annotation(s) set to low confidence.".format(updated))
    set_low_confidence.short_description = "Set confidence to Low"
    
    def mark_overlapping(self, request, queryset):
        updated = queryset.update(overlapping=True)
        self.message_user(request, "{} annotation(s) marked as overlapping.".format(updated))
    mark_overlapping.short_description = "Mark as overlapping"
    
    def export_csv(self, request, queryset):
        """Export selected annotations as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="annotations_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Task UUID', 'Text', 'Start', 'End', 'Labels', 'Confidence', 
                        'Identifier Type', 'Overlapping', 'Created'])
        
        for annotation in queryset:
            writer.writerow([
                annotation.task.uuid,
                annotation.text,
                annotation.start,
                annotation.end,
                ', '.join(annotation.labels),
                annotation.confidence,
                annotation.identifier_type,
                annotation.overlapping,
                annotation.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_csv.short_description = "Export selected annotations as CSV"


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Label model"""
    
    list_display = ('value_display', 'project', 'category', 'background_preview', 'hotkey', 
                   'is_active', 'sort_order', 'usage_count_display', 'updated_at')
    list_filter = ('is_active', 'category', 'project', 'created_at')
    search_fields = ('value', 'category', 'description', 'example')
    list_editable = ('is_active', 'sort_order', 'hotkey')
    ordering = ('project', 'sort_order', 'value')
    
    fieldsets = (
        ('Label Definition', {
            'fields': ('value', 'background', 'hotkey', 'project')
        }),
        ('Categorization', {
            'fields': ('category', 'description', 'example')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Usage Statistics', {
            'fields': ('usage_stats_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'usage_stats_display')
    
    actions = ['activate_labels', 'deactivate_labels', 'export_label_config']
    
    def value_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold;">{}</span>',
            obj.background, obj.value
        )
    value_display.short_description = "Label"
    value_display.admin_order_field = 'value'
    
    def background_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.background
        )
    background_preview.short_description = "Color"
    
    def usage_count_display(self, obj):
        count = obj.get_usage_count()
        if count > 0:
            url = reverse('admin:ner_labeler_annotation_changelist') + '?labels__contains="{}"'.format(obj.value)
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    usage_count_display.short_description = "Usage"
    
    def usage_stats_display(self, obj):
        if obj.pk:
            usage_count = obj.get_usage_count()
            can_delete = obj.can_be_deleted()
            
            stats_html = []
            stats_html.append('<p><strong>Usage Count:</strong> {}</p>'.format(usage_count))
            stats_html.append('<p><strong>Can be deleted:</strong> {}</p>'.format("Yes" if can_delete else "No"))
            
            if not can_delete:
                stats_html.append('<p style="color: #dc3545;"><strong>Warning:</strong> This label is in use and cannot be safely deleted.</p>')
            
            return mark_safe(''.join(stats_html))
        return "Usage statistics will be available after saving."
    usage_stats_display.short_description = "Usage Statistics"
    
    def activate_labels(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, "{} label(s) activated.".format(updated))
    activate_labels.short_description = "Activate selected labels"
    
    def deactivate_labels(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, "{} label(s) deactivated.".format(updated))
    deactivate_labels.short_description = "Deactivate selected labels"
    
    def export_label_config(self, request, queryset):
        """Export Label Studio configuration for selected labels"""
        response = HttpResponse(content_type='text/xml')
        response['Content-Disposition'] = 'attachment; filename="label_studio_config.xml"'
        
        config = ['<View>', '  <Text name="text" value="$text"/>', '  <Labels name="label" toName="text">']
        
        for label in queryset.filter(is_active=True).order_by('sort_order', 'value'):
            line = '    <Label value="{}" background="{}"'.format(label.value, label.background)
            if label.hotkey:
                line += ' hotkey="{}"'.format(label.hotkey)
            line += '/>'
            config.append(line)
        
        config.extend(['  </Labels>', '</View>'])
        response.write('\n'.join(config))
        return response
    export_label_config.short_description = "Export Label Studio config"


# Customize admin site
admin.site.site_header = "KDPII NER Labeler 관리자"
admin.site.site_title = "KDPII NER Labeler"
admin.site.index_title = "데이터베이스 관리"
