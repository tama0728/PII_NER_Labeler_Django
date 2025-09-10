"""
Django views for KDPII NER Labeler API
Migrated from Flask to Django REST Framework
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
from django.contrib.sessions.models import Session
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import json
import os
from datetime import datetime

from .models import Project, Task, Annotation, Label
from .serializers import (
    ProjectSerializer,
    TaskSerializer,
    TaskListSerializer,
    AnnotationSerializer,
    AnnotationCreateSerializer,
    TaskCreateSerializer,
    LabelSerializer,
)


# Template Views
def dashboard(request):
    """Dashboard view"""
    return render(request, "dashboard.html")


def collaborate(request):
    """Collaboration workspace view"""
    return render(request, "collaborate.html")


def workspace_ner_interface(request):
    """NER annotation workspace"""
    return render(request, "workspace_ner_interface.html")


# API ViewSets
@method_decorator(csrf_exempt, name='dispatch')
class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project CRUD operations"""

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        """Filter projects by owner_id from session"""
        owner_id = self.request.session.get("owner_id", 1)
        return Project.objects.filter(owner_id=owner_id)

    def perform_create(self, serializer):
        """Set owner_id from session when creating project"""
        owner_id = self.request.session.get("owner_id", 1)
        serializer.save(owner_id=owner_id)


@method_decorator(csrf_exempt, name='dispatch')
class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task CRUD operations"""

    serializer_class = TaskSerializer

    def get_queryset(self):
        """Filter tasks by project"""
        project_id = self.kwargs.get("project_pk")
        
        # Check for project filter in query parameters
        if not project_id:
            project_id = self.request.query_params.get('project')
        
        if project_id:
            return Task.objects.filter(project_id=project_id)
        return Task.objects.all()

    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == "list":
            return TaskListSerializer
        elif self.action == "create":
            return TaskCreateSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        """Set project when creating task"""
        project_id = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_id)
        serializer.save(project=project)

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None, project_pk=None):
        """Mark task as completed"""
        task = self.get_object()
        annotator_id = request.data.get("annotator_id")
        task.mark_completed(annotator_id)
        return Response({"status": "completed"})

    @action(detail=True, methods=["post"])
    def mark_incomplete(self, request, pk=None, project_pk=None):
        """Mark task as incomplete"""
        task = self.get_object()
        task.mark_incomplete()
        return Response({"status": "incomplete"})

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None, project_pk=None):
        """Export task in Label Studio format"""
        task = self.get_object()
        return Response(task.export_label_studio_format())

    @action(detail=True, methods=["get"])
    def annotations(self, request, pk=None, project_pk=None):
        """Get annotations for this task"""
        task = self.get_object()
        annotations = task.annotations.all()
        serializer = AnnotationSerializer(annotations, many=True)
        return Response({"results": serializer.data})

    @action(detail=True, methods=["get"])
    def conll(self, request, pk=None, project_pk=None):
        """Export task in CoNLL format"""
        task = self.get_object()
        return Response({"conll": task.export_conll_format()})


@method_decorator(csrf_exempt, name='dispatch')
class AnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for Annotation CRUD operations"""

    serializer_class = AnnotationSerializer

    def get_queryset(self):
        """Filter annotations by task"""
        task_id = self.kwargs.get("task_pk")
        if task_id:
            return Annotation.objects.filter(task_id=task_id)
        return Annotation.objects.all()

    def get_serializer_class(self):
        """Use create serializer for POST requests"""
        if self.action == "create":
            return AnnotationCreateSerializer
        return AnnotationSerializer

    def get_serializer_context(self):
        """Add task to serializer context"""
        context = super().get_serializer_context()
        task_id = self.kwargs.get("task_pk")
        if task_id:
            context["task"] = get_object_or_404(Task, pk=task_id)
        return context


@method_decorator(csrf_exempt, name='dispatch')
class LabelViewSet(viewsets.ModelViewSet):
    """ViewSet for Label CRUD operations"""

    serializer_class = LabelSerializer

    def get_queryset(self):
        """Filter labels by project and include global labels"""
        project_id = self.kwargs.get("project_pk")
        if not project_id:
            project_id = self.request.query_params.get('project')
        
        if project_id:
            # Return both project-specific and global labels
            from django.db.models import Q
            return Label.objects.filter(
                Q(project_id=project_id) | Q(project__isnull=True)
            ).order_by('sort_order', 'value')
        
        # Return all labels if no project specified
        return Label.objects.all().order_by('sort_order', 'value')

    def perform_create(self, serializer):
        """Set project when creating label"""
        project_id = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_id)
        serializer.save(project=project)


# Legacy API Views (for compatibility with existing frontend)
@api_view(["POST"])
def create_task(request):
    """Create a new NER annotation task (legacy endpoint)"""
    text = request.data.get("text", "")

    if not text:
        return Response(
            {"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Get or create default project
    project, created = Project.objects.get_or_create(
        name="Default Project",
        defaults={"description": "Default project for NER tasks"},
    )

    task = Task.objects.create(text=text, project=project)

    return Response({"task_id": task.uuid, "text": text})


@api_view(["GET"])
def get_task(request, task_id):
    """Get NER task details (legacy endpoint)"""
    task = get_object_or_404(Task, uuid=task_id)
    return Response(task.to_dict())


@api_view(["POST"])
def add_annotation(request, task_id):
    """Add annotation to NER task (legacy endpoint)"""
    task = get_object_or_404(Task, uuid=task_id)

    try:
        annotation = Annotation.objects.create(
            task=task,
            start=request.data["start"],
            end=request.data["end"],
            text=request.data.get("text", ""),
            labels=request.data["labels"],
        )
        return Response({"annotation_id": annotation.uuid})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def export_task(request, task_id):
    """Export NER task in Label Studio format (legacy endpoint)"""
    task = get_object_or_404(Task, uuid=task_id)
    return Response(task.export_label_studio_format())


@api_view(["GET"])
def export_conll(request, task_id):
    """Export NER task in CoNLL format (legacy endpoint)"""
    task = get_object_or_404(Task, uuid=task_id)
    return Response({"conll": task.export_conll_format()})


@api_view(["GET"])
def get_statistics(request):
    """Get NER annotation statistics (legacy endpoint)"""
    total_projects = Project.objects.count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(is_completed=True).count()
    total_annotations = Annotation.objects.count()

    # Get label distribution
    label_distribution = {}
    for annotation in Annotation.objects.all():
        for label in annotation.labels:
            label_distribution[label] = label_distribution.get(label, 0) + 1

    return Response(
        {
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "total_annotations": total_annotations,
            "completion_rate": (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            ),
            "label_distribution": label_distribution,
        }
    )


@api_view(["GET"])
def get_config(request):
    """Get NER Label Studio XML configuration (legacy endpoint)"""
    # Get all labels from all projects (for compatibility)
    labels = Label.objects.filter(is_active=True)

    basic_config = """
    <View>
        <Text name="text" value="$text"/>
        <Labels name="label" toName="text">
    """

    for label in labels:
        basic_config += (
            f'    <Label value="{label.value}" background="{label.background}"'
        )
        if label.hotkey:
            basic_config += f' hotkey="{label.hotkey}"'
        basic_config += "/>\n"

    basic_config += """
        </Labels>
    </View>
    """

    enhanced_config = basic_config  # For now, same as basic

    return Response(
        {
            "basic_config": basic_config,
            "enhanced_config": enhanced_config,
            "labels": [label.to_label_studio_format() for label in labels],
        }
    )


# Tag/Label CRUD API endpoints (legacy)
@api_view(["GET"])
def get_tags(request):
    """Get all NER tags/labels (legacy endpoint)"""
    labels = Label.objects.filter(is_active=True)
    return Response([label.to_dict() for label in labels])


@api_view(["POST"])
def create_tag(request):
    """Create a new NER tag/label (legacy endpoint)"""
    if not request.data or not request.data.get("value"):
        return Response(
            {"error": "Tag value is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get or create default project
        project, created = Project.objects.get_or_create(
            name="Default Project",
            defaults={"description": "Default project for NER tasks"},
        )

        label = Label.objects.create(
            project=project,
            value=request.data["value"],
            background=request.data.get("background", "#999999"),
            hotkey=request.data.get("hotkey"),
            category=request.data.get("category"),
            description=request.data.get("description"),
            example=request.data.get("example"),
        )
        return Response(label.to_dict(), status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_tag(request, label_id):
    """Get a specific NER tag/label by ID (legacy endpoint)"""
    label = get_object_or_404(Label, pk=label_id)
    return Response(label.to_dict())


@api_view(["PUT"])
def update_tag(request, label_id):
    """Update an existing NER tag/label (legacy endpoint)"""
    label = get_object_or_404(Label, pk=label_id)

    if not request.data:
        return Response(
            {"error": "Request body is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        for field in [
            "value",
            "background",
            "hotkey",
            "category",
            "description",
            "example",
        ]:
            if field in request.data:
                setattr(label, field, request.data[field])

        label.save()
        return Response(label.to_dict())
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_tag(request, label_id):
    """Delete a NER tag/label (legacy endpoint)"""
    label = get_object_or_404(Label, pk=label_id)

    if not label.can_be_deleted():
        return Response(
            {"error": "Cannot delete label that is in use"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    label.delete()
    return Response({"message": "Label deleted successfully"})


# Export and file management endpoints
@api_view(["GET"])
def get_exports(request):
    """Get list of exported files (legacy endpoint)"""
    try:
        files = []
        exports_dir = os.path.join(settings.BASE_DIR.parent, "exports")

        # Hardcoded workspace names for compatibility
        workspace_names = {"297048ca": "test1", "12f6dd45": "test2"}

        # Check both modified and completed directories
        for subdir in ["modified", "completed"]:
            subdir_path = os.path.join(exports_dir, subdir)
            if os.path.exists(subdir_path):
                for filename in os.listdir(subdir_path):
                    if filename.endswith(".jsonl"):
                        file_path = os.path.join(subdir_path, filename)
                        stat = os.stat(file_path)

                        workspace_name = subdir.capitalize()
                        annotator_name = "unknown_user"

                        # Parse filename format
                        if filename.count("_") >= 4:
                            parts = filename.replace(".jsonl", "").split("_")
                            if len(parts) >= 5 and "completed" in parts:
                                workspace_name = parts[0]
                                annotator_name = parts[1]
                        else:
                            for ws_id, ws_name in workspace_names.items():
                                if (
                                    ws_id in filename
                                    or ws_name.lower() in filename.lower()
                                ):
                                    workspace_name = ws_name
                                    break

                        files.append(
                            {
                                "id": f"{subdir}_{filename}",
                                "name": filename,
                                "workspace": workspace_name,
                                "annotator": annotator_name,
                                "created_at": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                                "size": stat.st_size,
                                "format": "jsonl",
                                "record_count": "N/A",
                            }
                        )

        files.sort(key=lambda x: x["created_at"], reverse=True)
        return Response({"files": files})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Additional API endpoints for frontend compatibility
@api_view(['GET'])
def get_all_tasks(request):
    """Get all tasks (frontend compatibility endpoint)"""
    tasks = Task.objects.all()
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['GET'])  
def get_all_annotations(request):
    """Get all annotations (frontend compatibility endpoint)"""
    annotations = Annotation.objects.all()
    serializer = AnnotationSerializer(annotations, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def save_completed_file(request):
    """Save completed/labeled file to server (legacy endpoint)"""
    try:
        filename = request.data.get("filename", "completed_file.jsonl")
        content = request.data.get("content", "")

        if not content:
            return Response(
                {"error": "No content provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get workspace info from session
        workspace_id = request.session.get("workspace_id", "unknown")
        member_name = request.session.get("member_name", "unknown_user")

        # Create workspace_data directory
        exports_dir = os.path.join(settings.BASE_DIR.parent, "workspace_data")
        os.makedirs(exports_dir, exist_ok=True)

        # Generate filename
        save_filename = f"{workspace_id}.jsonl"
        file_path = os.path.join(exports_dir, save_filename)

        # Save file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return Response(
            {
                "success": True,
                "filename": save_filename,
                "filepath": file_path,
                "workspace": workspace_id,
                "annotator": member_name,
                "message": f"완성된 파일이 서버에 저장되었습니다: {save_filename}",
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Additional API endpoints for frontend compatibility
@api_view(['GET'])
def get_all_tasks(request):
    """Get all tasks (frontend compatibility endpoint)"""
    tasks = Task.objects.all()
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['GET'])  
def get_all_annotations(request):
    """Get all annotations (frontend compatibility endpoint)"""
    annotations = Annotation.objects.all()
    serializer = AnnotationSerializer(annotations, many=True)
    return Response(serializer.data)
