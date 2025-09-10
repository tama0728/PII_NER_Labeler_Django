"""
Django models for KDPII NER Labeler
Migrated from SQLAlchemy to Django ORM
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import json


def generate_uuid():
    """Generate UUID string for model defaults"""
    return str(uuid.uuid4())


class Project(models.Model):
    """Project model for grouping related annotation tasks"""

    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)

    # Project settings
    is_active = models.BooleanField(default=True)
    allow_overlapping_annotations = models.BooleanField(default=True)
    require_all_labels = models.BooleanField(default=False)

    # Ownership and timestamps
    owner_id = models.IntegerField(default=1)  # Guest mode default
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-updated_at"]

    @property
    def task_count(self):
        """Get total number of tasks in this project"""
        return self.tasks.count()

    @property
    def completed_task_count(self):
        """Get number of completed tasks"""
        return self.tasks.filter(is_completed=True).count()

    @property
    def completion_percentage(self):
        """Get completion percentage"""
        total = self.task_count
        if not total:
            return 0.0
        return (self.completed_task_count / total) * 100.0

    @property
    def annotation_count(self):
        """Get total number of annotations in this project"""
        return sum(task.annotations.count() for task in self.tasks.all())

    def get_label_distribution(self):
        """Get distribution of labels across all tasks"""
        label_counts = {}
        for task in self.tasks.all():
            for annotation in task.annotations.all():
                try:
                    labels = (
                        json.loads(annotation.labels)
                        if isinstance(annotation.labels, str)
                        else annotation.labels
                    )
                    for label_value in labels:
                        label_counts[label_value] = label_counts.get(label_value, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
        return label_counts

    def get_owner_name(self):
        """Get owner name for frontend compatibility"""
        return f"User {self.owner_id}"

    def to_dict(self, include_stats=False):
        """Convert to dictionary representation"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "allow_overlapping_annotations": self.allow_overlapping_annotations,
            "require_all_labels": self.require_all_labels,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_stats:
            data.update(
                {
                    "task_count": self.task_count,
                    "completed_task_count": self.completed_task_count,
                    "completion_percentage": self.completion_percentage,
                    "annotation_count": self.annotation_count,
                    "label_distribution": self.get_label_distribution(),
                }
            )

        return data

    def __str__(self):
        return self.name


class Task(models.Model):
    """Task model representing individual annotation tasks"""

    uuid = models.CharField(max_length=36, unique=True, default=generate_uuid)

    # Task content
    text = models.TextField()
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    line_number = models.IntegerField(blank=True, null=True)

    # Task status
    is_completed = models.BooleanField(default=False)
    completion_time = models.DateTimeField(blank=True, null=True)

    # Identifier classification (for KDPII requirements)
    identifier_type = models.CharField(
        max_length=20,
        default="default",
        choices=[
            ("direct", "Direct Identifier"),
            ("quasi", "Quasi Identifier"),
            ("default", "Default"),
        ],
    )

    # Foreign keys
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    annotator_id = models.IntegerField(blank=True, null=True)  # Guest mode

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]

    def mark_completed(self, annotator_id=None):
        """Mark task as completed"""
        self.is_completed = True
        self.completion_time = timezone.now()
        if annotator_id:
            self.annotator_id = annotator_id
        self.save()

    def mark_incomplete(self):
        """Mark task as incomplete"""
        self.is_completed = False
        self.completion_time = None
        self.save()

    def set_identifier_type(self, identifier_type):
        """Set identifier classification type"""
        if identifier_type not in ["direct", "quasi", "default"]:
            raise ValueError(f"Invalid identifier type: {identifier_type}")
        self.identifier_type = identifier_type
        self.save()

    @property
    def annotation_count(self):
        """Get number of annotations for this task"""
        return self.annotations.count()

    @property
    def entity_count(self):
        """Get number of unique entities (annotations with different spans)"""
        unique_spans = set()
        for annotation in self.annotations.all():
            unique_spans.add((annotation.start, annotation.end))
        return len(unique_spans)

    def get_overlapping_annotations(self):
        """Get annotations that overlap with each other"""
        overlapping = []
        annotations = list(self.annotations.order_by("start"))

        for i, ann1 in enumerate(annotations):
            for ann2 in annotations[i + 1 :]:
                # Check if they overlap (not just touch at edges)
                if ann1.start < ann2.end and ann2.start < ann1.end:
                    if ann1 not in overlapping:
                        overlapping.append(ann1)
                    if ann2 not in overlapping:
                        overlapping.append(ann2)

        return overlapping

    def export_label_studio_format(self):
        """Export task in Label Studio format"""
        return {
            "id": self.id,
            "data": {"text": self.text},
            "annotations": [
                {
                    "id": ann.id,
                    "created_at": ann.created_at.isoformat(),
                    "result": [
                        {
                            "from_name": "label",
                            "to_name": "text",
                            "type": "labels",
                            "value": {
                                "start": ann.start,
                                "end": ann.end,
                                "text": ann.text,
                                "labels": (
                                    json.loads(ann.labels)
                                    if isinstance(ann.labels, str)
                                    else ann.labels
                                ),
                            },
                        }
                    ],
                }
                for ann in self.annotations.all()
            ],
            "predictions": [],
        }

    def export_conll_format(self):
        """Export annotations in CoNLL-2003 format"""
        tokens = self.text.split()
        token_labels = ["O"] * len(tokens)

        current_pos = 0
        for token_idx, token in enumerate(tokens):
            token_start = self.text.find(token, current_pos)
            token_end = token_start + len(token)

            # Check if token overlaps with any annotation
            for ann in self.annotations.all():
                if (
                    ann.start <= token_start < ann.end
                    or ann.start < token_end <= ann.end
                ):
                    try:
                        labels = (
                            json.loads(ann.labels)
                            if isinstance(ann.labels, str)
                            else ann.labels
                        )
                        # Use B-I-O tagging scheme
                        if token_start == ann.start:
                            token_labels[token_idx] = (
                                f"B-{labels[0]}" if labels else "B-MISC"
                            )
                        else:
                            token_labels[token_idx] = (
                                f"I-{labels[0]}" if labels else "I-MISC"
                            )
                        break
                    except (json.JSONDecodeError, TypeError, IndexError):
                        continue

            current_pos = token_end

        # Format as CoNLL
        conll_lines = []
        for token, label in zip(tokens, token_labels):
            conll_lines.append(f"{token}\t{label}")

        return "\n".join(conll_lines)

    def to_dict(self, include_annotations=True):
        """Convert to dictionary representation"""
        data = {
            "id": self.id,
            "uuid": self.uuid,
            "text": self.text,
            "original_filename": self.original_filename,
            "line_number": self.line_number,
            "is_completed": self.is_completed,
            "completion_time": (
                self.completion_time.isoformat() if self.completion_time else None
            ),
            "identifier_type": self.identifier_type,
            "project_id": self.project_id,
            "annotator_id": self.annotator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "annotation_count": self.annotation_count,
            "entity_count": self.entity_count,
        }

        if include_annotations:
            data["annotations"] = [ann.to_dict() for ann in self.annotations.all()]

        return data

    def __str__(self):
        return f'{self.uuid[:8]}... "{self.text[:50]}..."'


class Annotation(models.Model):
    """Annotation model for named entity annotations"""

    uuid = models.CharField(max_length=36, unique=True, default=generate_uuid)

    # Annotation span
    start = models.IntegerField()
    end = models.IntegerField()
    text = models.TextField()

    # Labels (JSON field for multiple labels)
    labels = models.JSONField(default=list)

    # Confidence and metadata
    confidence = models.CharField(
        max_length=10,
        default="high",
        choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")],
    )
    notes = models.TextField(blank=True, null=True)

    # Advanced NER features
    identifier_type = models.CharField(
        max_length=20,
        default="default",
        choices=[
            ("direct", "Direct Identifier"),
            ("quasi", "Quasi Identifier"),
            ("default", "Default"),
        ],
    )
    overlapping = models.BooleanField(default=False)

    # Relationships and entities
    related_annotations = models.JSONField(default=list)
    entity_id = models.CharField(max_length=36, blank=True, null=True)
    relationships = models.JSONField(default=list)

    # Foreign keys
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="annotations")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "annotations"
        ordering = ["start", "end"]

    def clean(self):
        """Validation"""
        if self.start >= self.end:
            raise ValidationError(
                f"Invalid annotation span: start={self.start}, end={self.end}"
            )

    def set_confidence(self, confidence):
        """Set annotation confidence level"""
        if confidence not in ["high", "medium", "low"]:
            raise ValueError(f"Invalid confidence level: {confidence}")
        self.confidence = confidence
        self.save()

    def add_label(self, label):
        """Add a label to this annotation"""
        if label not in self.labels:
            self.labels.append(label)
            self.save()

    def remove_label(self, label):
        """Remove a label from this annotation"""
        if label in self.labels:
            self.labels.remove(label)
            self.save()

    def set_labels(self, labels):
        """Set all labels for this annotation"""
        self.labels = labels
        self.save()

    def link_to_annotation(self, other_annotation_id):
        """Create relationship link to another annotation"""
        if other_annotation_id not in self.related_annotations:
            self.related_annotations.append(other_annotation_id)
            self.save()

    def unlink_from_annotation(self, other_annotation_id):
        """Remove relationship link to another annotation"""
        if other_annotation_id in self.related_annotations:
            self.related_annotations.remove(other_annotation_id)
            self.save()

    def set_entity_id(self, entity_id):
        """Set entity identifier for relationship tracking"""
        self.entity_id = entity_id
        self.save()

    def set_identifier_type(self, identifier_type):
        """Set privacy identifier type (direct/quasi/default)"""
        if identifier_type not in ["direct", "quasi", "default"]:
            raise ValueError(f"Invalid identifier type: {identifier_type}")
        self.identifier_type = identifier_type
        self.save()

    def set_overlapping(self, overlapping):
        """Set overlapping annotation flag"""
        self.overlapping = overlapping
        self.save()

    def add_relationship(self, entity_id, relationship_type):
        """Add entity relationship"""
        relationship = {
            "entity_id": entity_id,
            "type": relationship_type,
            "created_at": timezone.now().isoformat(),
        }
        if relationship not in self.relationships:
            self.relationships.append(relationship)
            self.save()

    @property
    def span_length(self):
        """Get length of annotated text span"""
        return self.end - self.start

    def overlaps_with(self, other):
        """Check if this annotation overlaps with another"""
        return not (self.end <= other.start or self.start >= other.end)

    def contains(self, other):
        """Check if this annotation completely contains another"""
        return self.start <= other.start and self.end >= other.end

    def is_contained_by(self, other):
        """Check if this annotation is completely contained by another"""
        return other.contains(self)

    def to_dict(self, include_relationships=True):
        """Convert to dictionary representation"""
        data = {
            "id": self.id,
            "uuid": self.uuid,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "labels": self.labels,
            "confidence": self.confidence,
            "notes": self.notes,
            "entity_id": self.entity_id,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "span_length": self.span_length,
            "identifier_type": self.identifier_type,
            "overlapping": self.overlapping,
            "relationships": self.relationships,
        }

        if include_relationships:
            data["related_annotations"] = self.related_annotations

        return data

    def to_label_studio_result(self):
        """Convert to Label Studio result format"""
        return {
            "from_name": "label",
            "to_name": "text",
            "type": "labels",
            "value": {
                "start": self.start,
                "end": self.end,
                "text": self.text,
                "labels": self.labels,
            },
        }

    def __str__(self):
        labels_str = ",".join(self.labels) if self.labels else "no-labels"
        return f'{self.uuid[:8]}... "{self.text}" [{labels_str}]'


class Label(models.Model):
    """Label model for NER label definitions"""

    # Label definition
    value = models.CharField(max_length=50)
    background = models.CharField(max_length=7, default="#999999")  # Hex color
    hotkey = models.CharField(max_length=1, blank=True, null=True)

    # Label metadata
    category = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    example = models.TextField(blank=True, null=True)

    # Display settings
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    # Project association (None for global labels)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="labels", null=True, blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "labels"
        unique_together = [
            ("project", "value"),
            ("project", "hotkey"),
        ]
        ordering = ["sort_order", "value"]

    def validate_hotkey(self, hotkey):
        """Validate hotkey format"""
        if not hotkey:
            return True
        return len(hotkey) == 1 and (hotkey.isalnum() or hotkey in "!@#$%^&*()")

    def validate_color(self, color):
        """Validate hex color format"""
        if not color.startswith("#") or len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False

    def set_hotkey(self, hotkey):
        """Set hotkey with validation"""
        if hotkey and not self.validate_hotkey(hotkey):
            raise ValueError(f"Invalid hotkey format: {hotkey}")
        self.hotkey = hotkey
        self.save()

    def set_background_color(self, color):
        """Set background color with validation"""
        if not self.validate_color(color):
            raise ValueError(
                f"Invalid color format: {color}. Must be hex format like #FF5733"
            )
        self.background = color
        self.save()

    def deactivate(self):
        """Deactivate this label"""
        self.is_active = False
        self.save()

    def activate(self):
        """Activate this label"""
        self.is_active = True
        self.save()

    def get_usage_count(self):
        """Get count of annotations using this label"""
        count = 0
        if self.project:
            # Project-specific label
            for task in self.project.tasks.all():
                for annotation in task.annotations.all():
                    if self.value in annotation.labels:
                        count += 1
        else:
            # Global label - count across all projects
            from .models import Task
            for task in Task.objects.all():
                for annotation in task.annotations.all():
                    if self.value in annotation.labels:
                        count += 1
        return count

    def can_be_deleted(self):
        """Check if label can be safely deleted"""
        return self.get_usage_count() == 0

    @classmethod
    def create_default_labels(cls, project_id):
        """Create default NER labels for a project"""
        # No default labels - user will create their own
        return []

    def to_dict(self, include_usage=False):
        """Convert to dictionary representation"""
        data = {
            "id": self.id,
            "value": self.value,
            "background": self.background,
            "hotkey": self.hotkey,
            "category": self.category,
            "description": self.description,
            "example": self.example,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_usage:
            data["usage_count"] = self.get_usage_count()
            data["can_be_deleted"] = self.can_be_deleted()

        return data

    def to_label_studio_format(self):
        """Convert to Label Studio format"""
        result = {"value": self.value, "background": self.background}
        if self.hotkey:
            result["hotkey"] = self.hotkey
        return result

    def __str__(self):
        return f"{self.value} ({self.background})"
