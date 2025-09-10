"""
Django REST Framework serializers for NER Labeler
"""

from rest_framework import serializers
from .models import Project, Task, Annotation, Label


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.ReadOnlyField()
    completed_task_count = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()
    annotation_count = serializers.ReadOnlyField()
    label_distribution = serializers.ReadOnlyField(source="get_label_distribution")
    owner = serializers.ReadOnlyField(source="get_owner_name")  # For frontend compatibility

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class LabelSerializer(serializers.ModelSerializer):
    usage_count = serializers.ReadOnlyField(source="get_usage_count")
    can_be_deleted = serializers.ReadOnlyField()

    class Meta:
        model = Label
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate_background(self, value):
        """Validate hex color format"""
        if not value.startswith("#") or len(value) != 7:
            raise serializers.ValidationError(
                "Color must be in hex format (e.g., #FF5733)"
            )
        try:
            int(value[1:], 16)
        except ValueError:
            raise serializers.ValidationError("Invalid hex color format")
        return value

    def validate_hotkey(self, value):
        """Validate hotkey format"""
        if value and (
            len(value) != 1 or not (value.isalnum() or value in "!@#$%^&*()")
        ):
            raise serializers.ValidationError(
                "Hotkey must be a single alphanumeric character or symbol"
            )
        return value


class AnnotationSerializer(serializers.ModelSerializer):
    span_length = serializers.ReadOnlyField()

    class Meta:
        model = Annotation
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "uuid")

    def validate(self, data):
        """Validate annotation span"""
        if data.get("start", 0) >= data.get("end", 1):
            raise serializers.ValidationError(
                "Start position must be less than end position"
            )
        return data


class TaskSerializer(serializers.ModelSerializer):
    annotations = AnnotationSerializer(many=True, read_only=True)
    annotation_count = serializers.ReadOnlyField()
    entity_count = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "uuid")


class TaskListSerializer(serializers.ModelSerializer):
    """Simplified task serializer for list views"""

    annotation_count = serializers.ReadOnlyField()
    project_id = serializers.ReadOnlyField()  # Include project_id for filtering

    class Meta:
        model = Task
        fields = [
            "id",
            "uuid",
            "text",
            "is_completed",
            "completion_time",
            "identifier_type",
            "annotation_count",
            "project_id",  # Add project_id to fields
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at", "uuid")


class AnnotationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating annotations"""

    class Meta:
        model = Annotation
        fields = [
            "start",
            "end",
            "text",
            "labels",
            "confidence",
            "notes",
            "identifier_type",
            "overlapping",
            "entity_id",
        ]

    def create(self, validated_data):
        """Create annotation with task from context"""
        task = self.context["task"]
        validated_data["task"] = task
        return super().create(validated_data)


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""

    class Meta:
        model = Task
        fields = ["text", "original_filename", "line_number", "identifier_type"]

    def create(self, validated_data):
        """Create task with project from context"""
        project = self.context["project"]
        validated_data["project"] = project
        return super().create(validated_data)
