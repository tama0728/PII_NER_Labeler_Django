"""
URL configuration for NER Labeler app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create router for the API
router = DefaultRouter()
router.register(r"projects", views.ProjectViewSet, basename="project")
router.register(r"tasks", views.TaskViewSet, basename="task")
router.register(r"annotations", views.AnnotationViewSet, basename="annotation")
router.register(r"labels", views.LabelViewSet, basename="label")
router.register(r"workspaces", views.ProjectViewSet, basename="workspace")  # Alias for projects
router.register(r"upload", views.FileUploadViewSet, basename="upload")
router.register(r"uploaded-files", views.UploadedFileViewSet, basename="uploaded-files")

app_name = "ner_labeler"

urlpatterns = [
    # Template views
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("collaborate/", views.collaborate, name="collaborate"),
    path("workspace/", views.workspace_ner_interface, name="workspace"),
    # RESTful API endpoints
    path("api/v1/", include(router.urls)),
    # Additional compatibility endpoints for frontend
    path("api/", include(router.urls)),  # Frontend expects this path
    # Legacy API endpoints (for compatibility with existing frontend)
    path("api/tasks", views.create_task, name="create_task_legacy"),
    path("api/tasks/<str:task_id>/", views.get_task, name="get_task_legacy"),
    path(
        "api/tasks/<str:task_id>/annotations/",
        views.add_annotation,
        name="add_annotation_legacy",
    ),
    path(
        "api/tasks/<str:task_id>/export/", views.export_task, name="export_task_legacy"
    ),
    path(
        "api/tasks/<str:task_id>/conll/", views.export_conll, name="export_conll_legacy"
    ),
    path("api/statistics/", views.get_statistics, name="statistics_legacy"),
    path("api/config/", views.get_config, name="config_legacy"),
    # Legacy tag/label endpoints
    path("api/tags/", views.get_tags, name="get_tags_legacy"),
    path("api/tags", views.create_tag, name="create_tag_legacy"),  # POST
    path("api/tags/<int:label_id>/", views.get_tag, name="get_tag_legacy"),
    path("api/tags/<int:label_id>", views.update_tag, name="update_tag_legacy"),  # PUT
    path("api/tags/<int:label_id>/delete/", views.delete_tag, name="delete_tag_legacy"),
    # Export and file management
    path("api/exports/", views.get_exports, name="get_exports_legacy"),
    path(
        "api/save-completed-file/",
        views.save_completed_file,
        name="save_completed_file_legacy",
    ),
    # NER-specific API endpoints (for compatibility)
    path("api/ner/tasks", views.create_task, name="ner_create_task"),
    path("api/ner/tasks/<str:task_id>/", views.get_task, name="ner_get_task"),
    path(
        "api/ner/tasks/<str:task_id>/annotations/",
        views.add_annotation,
        name="ner_add_annotation",
    ),
    path(
        "api/ner/tasks/<str:task_id>/export/", views.export_task, name="ner_export_task"
    ),
    path(
        "api/ner/tasks/<str:task_id>/conll/",
        views.export_conll,
        name="ner_export_conll",
    ),
    path("api/ner/statistics/", views.get_statistics, name="ner_statistics"),
    path("api/ner/config/", views.get_config, name="ner_config"),
    path("api/ner/tags/", views.get_tags, name="ner_get_tags"),
    path("api/ner/tags", views.create_tag, name="ner_create_tag"),  # POST
    path("api/ner/tags/<int:label_id>/", views.get_tag, name="ner_get_tag"),
    path("api/ner/tags/<int:label_id>", views.update_tag, name="ner_update_tag"),  # PUT
    path(
        "api/ner/tags/<int:label_id>/delete/", views.delete_tag, name="ner_delete_tag"
    ),
]
