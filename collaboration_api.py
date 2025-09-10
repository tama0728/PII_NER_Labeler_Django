"""
API endpoints for team collaboration
"""

from flask import Blueprint, request, jsonify, session
from backend.services.collaboration_service import CollaborationService
import os
import json
from werkzeug.utils import secure_filename

collab_bp = Blueprint("collab", __name__)
collab_service = CollaborationService()


@collab_bp.route("/workspaces", methods=["GET"])
def list_workspaces():
    """List all available workspaces"""
    workspaces = collab_service.list_workspaces()
    return jsonify(workspaces)


@collab_bp.route("/workspaces", methods=["POST"])
def create_workspace():
    """Create a new workspace with member name"""
    data = request.get_json()
    name = data.get("name")
    member_name = data.get("member_name")
    description = data.get("description", "")

    if not name:
        return jsonify({"error": "Workspace name is required"}), 400

    if not member_name:
        return jsonify({"error": "Member name is required"}), 400

    workspace_id = collab_service.create_workspace(name, description, member_name)
    return jsonify(
        {
            "workspace_id": workspace_id,
            "message": f'Workspace "{name}" created successfully for {member_name}',
        }
    )


@collab_bp.route("/workspaces/<workspace_id>", methods=["GET"])
def get_workspace(workspace_id):
    """Get workspace details"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404
    return jsonify(workspace)


@collab_bp.route("/workspaces/<workspace_id>", methods=["DELETE"])
def delete_workspace(workspace_id):
    """Delete a workspace"""
    success = collab_service.delete_workspace(workspace_id)
    if success:
        return jsonify({"message": "Workspace deleted successfully"})
    return jsonify({"error": "Workspace not found"}), 404


@collab_bp.route("/workspaces/<workspace_id>/join", methods=["POST"])
def join_workspace(workspace_id):
    """Join a workspace as a team member"""
    data = request.get_json()
    member_name = data.get("member_name")

    if not member_name:
        return jsonify({"error": "Member name is required"}), 400

    success = collab_service.add_member_to_workspace(workspace_id, member_name)
    if not success:
        return jsonify({"error": "Workspace not found"}), 404

    session["workspace_id"] = workspace_id
    session["member_name"] = member_name

    return jsonify(
        {
            "message": f"Joined workspace as {member_name}",
            "workspace_id": workspace_id,
            "member_name": member_name,
        }
    )


@collab_bp.route("/workspaces/<workspace_id>/enter", methods=["POST"])
def enter_workspace(workspace_id):
    """Enter a workspace (for 1-person workspaces)"""
    data = request.get_json()
    member_name = data.get("member_name")

    if not member_name:
        return jsonify({"error": "Member name is required"}), 400

    # Check if workspace exists
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    # Verify this member owns this workspace (skip for legacy workspaces without member_name)
    workspace_owner = workspace.get("member_name")
    if workspace_owner and workspace_owner != member_name:
        return (
            jsonify(
                {"error": "Access denied. This workspace belongs to a different user."}
            ),
            403,
        )

    # Set session data
    session["workspace_id"] = workspace_id
    session["member_name"] = member_name

    # Debug logging
    print(f"DEBUG enter_workspace: Setting session for {member_name}")
    print(f"DEBUG session keys after setting: {list(session.keys())}")
    print(f"DEBUG session['member_name']: {session.get('member_name')}")

    return jsonify(
        {
            "message": f"Entered workspace as {member_name}",
            "workspace_id": workspace_id,
            "member_name": member_name,
        }
    )


@collab_bp.route("/workspaces/test-session", methods=["POST"])
def test_session():
    """Debug session data"""
    return jsonify(
        {
            "workspace_id": session.get("workspace_id"),
            "member_name": session.get("member_name"),
            "session_keys": list(session.keys()),
        }
    )


@collab_bp.route("/workspaces/<workspace_id>/tasks", methods=["GET"])
def list_tasks(workspace_id):
    """List all tasks in a workspace"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    tasks = list(workspace.get("tasks", {}).values())
    return jsonify(tasks)


@collab_bp.route("/workspaces/<workspace_id>/tasks", methods=["POST"])
def create_task(workspace_id):
    """Create a new task in workspace"""
    data = request.get_json()
    text = data.get("text")
    metadata = data.get("metadata", {})

    if not text:
        return jsonify({"error": "Task text is required"}), 400

    task_id = collab_service.add_task(workspace_id, text, metadata)
    if not task_id:
        return jsonify({"error": "Failed to create task"}), 500

    return jsonify({"task_id": task_id, "message": "Task created successfully"})


@collab_bp.route("/workspaces/<workspace_id>/tasks/<task_id>", methods=["GET"])
def get_task(workspace_id, task_id):
    """Get specific task details"""
    task = collab_service.get_task(workspace_id, task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@collab_bp.route(
    "/workspaces/<workspace_id>/tasks/<task_id>/annotate", methods=["POST"]
)
def annotate_task(workspace_id, task_id):
    """Add annotations to a task"""
    data = request.get_json()
    annotations = data.get("annotations", [])
    member_name = session.get("member_name") or data.get("member_name", "Anonymous")

    success = collab_service.add_annotation(
        workspace_id, task_id, member_name, annotations
    )

    if not success:
        return jsonify({"error": "Failed to save annotations"}), 500

    return jsonify(
        {"message": "Annotations saved successfully", "annotator": member_name}
    )


@collab_bp.route("/workspaces/<workspace_id>/tasks/<task_id>/merge", methods=["GET"])
def merge_annotations(workspace_id, task_id):
    """Get merged annotations for a task"""
    strategy = request.args.get("strategy", "union")

    merged = collab_service.merge_annotations(workspace_id, task_id, strategy)
    if merged is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(
        {"task_id": task_id, "merge_strategy": strategy, "merged_annotations": merged}
    )


@collab_bp.route("/workspaces/<workspace_id>/export", methods=["GET"])
def export_workspace(workspace_id):
    """Export workspace data with merged annotations"""
    strategy = request.args.get("strategy", "union")

    export_data = collab_service.export_workspace(workspace_id, strategy)
    if not export_data:
        return jsonify({"error": "Workspace not found"}), 404

    return jsonify(export_data)


@collab_bp.route("/workspaces/<workspace_id>/export/jsonl", methods=["GET"])
def export_workspace_jsonl(workspace_id):
    """Export all tasks in workspace as JSONL format"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    tasks = workspace.get("tasks", {})
    if not tasks:
        return jsonify({"error": "No tasks found in workspace"}), 404

    # Generate JSONL content
    jsonl_lines = []
    for task_id, task_data in tasks.items():
        # Get task text and metadata
        text = task_data.get("text", "")
        metadata = task_data.get("metadata", {})

        # Get all annotations for this task
        entities = []
        annotations = task_data.get("annotations", {})

        for member_name, member_annotations in annotations.items():
            for annotation in member_annotations:
                entities.append(
                    {
                        "start": annotation.get("start"),
                        "end": annotation.get("end"),
                        "entity_type": (
                            annotation.get("labels", [""])[0]
                            if annotation.get("labels")
                            else ""
                        ),
                        "span_id": annotation.get("span_id", ""),
                        "entity_id": annotation.get("entity_id", ""),
                        "identifier_type": annotation.get("identifier_type", "default"),
                        "annotator": member_name,
                        "span_text": (
                            text[annotation.get("start", 0) : annotation.get("end", 0)]
                            if text
                            else ""
                        ),
                    }
                )

        # Create JSONL line
        jsonl_line = {"text": text, "entities": entities, "metadata": metadata}

        jsonl_lines.append(jsonl_line)

    return jsonify({"jsonl_lines": jsonl_lines, "total_tasks": len(jsonl_lines)})


@collab_bp.route("/workspaces/<workspace_id>/statistics", methods=["GET"])
def get_statistics(workspace_id):
    """Get workspace statistics"""
    stats = collab_service.get_statistics(workspace_id)
    if not stats:
        return jsonify({"error": "Workspace not found"}), 404

    return jsonify(stats)


@collab_bp.route("/workspaces/<workspace_id>/labels", methods=["GET"])
def get_labels(workspace_id):
    """Get workspace labels"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    labels = workspace.get("labels", [])
    return jsonify(labels)


@collab_bp.route("/workspaces/<workspace_id>/labels", methods=["POST"])
def add_label(workspace_id):
    """Add a new label to workspace"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    data = request.get_json()
    label_name = data.get("name")
    label_color = data.get("color", "#808080")

    if not label_name:
        return jsonify({"error": "Label name is required"}), 400

    # Check if label already exists
    existing_labels = workspace.get("labels", [])
    for label in existing_labels:
        if label["name"] == label_name:
            return jsonify({"error": "Label already exists"}), 400

    # Add new label
    new_label = {"name": label_name, "color": label_color}
    workspace.setdefault("labels", []).append(new_label)
    collab_service.save_workspaces()

    return jsonify({"message": "Label added successfully", "label": new_label})


# File upload configuration
ALLOWED_EXTENSIONS = {"jsonl"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_file_content(file, filename):
    """Parse JSONL format and extract texts and labels"""
    texts = []
    labels = set()  # 추출된 entity_type들을 저장
    file_extension = filename.rsplit(".", 1)[1].lower()

    if file_extension != "jsonl":
        raise ValueError(
            f"Unsupported file format: {file_extension}. Only JSONL files are supported."
        )

    try:
        content = file.read().decode("utf-8")

        # JSON Lines format - each line is a separate JSON object
        lines = content.strip().split("\n")
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)

                if isinstance(data, str):
                    texts.append(data.strip())
                elif isinstance(data, dict):
                    # Check for KDPII NER format with entities
                    if "text" in data and "entities" in data:
                        texts.append(data["text"].strip())
                        # Extract entity_types from entities array
                        if isinstance(data["entities"], list):
                            for entity in data["entities"]:
                                if isinstance(entity, dict) and "entity_type" in entity:
                                    labels.add(entity["entity_type"])
                    else:
                        # Look for common text fields
                        text_found = False
                        for key in [
                            "text",
                            "content",
                            "sentence",
                            "document",
                            "message",
                            "data",
                        ]:
                            if (
                                key in data
                                and isinstance(data[key], str)
                                and data[key].strip()
                            ):
                                texts.append(data[key].strip())
                                text_found = True
                                break

                        # If no text field found, try to use the whole object as string
                        if not text_found:
                            # Look for any string value in the object
                            for value in data.values():
                                if isinstance(value, str) and len(value.strip()) > 5:
                                    texts.append(value.strip())
                                    break

            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON on line {line_num}: {e}")
                continue

    except Exception as e:
        raise ValueError(f"Error parsing JSONL file: {str(e)}")

    return texts, list(labels)


@collab_bp.route("/workspaces/<workspace_id>/upload", methods=["POST"])
def upload_file(workspace_id):
    """Upload file and create tasks from content"""
    # Check if workspace exists
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    # Check if file is present
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return (
            jsonify(
                {"error": "File type not allowed. Supported: txt, csv, json, jsonl"}
            ),
            400,
        )

    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Seek back to beginning

    if file_size > MAX_FILE_SIZE:
        return jsonify({"error": "File too large. Max size: 16MB"}), 400

    try:
        # Parse file content
        texts, extracted_labels = parse_file_content(file, file.filename)

        if not texts:
            return jsonify({"error": "No text content found in file"}), 400

        # Create tasks from parsed texts with duplicate tracking
        created_tasks = []
        duplicate_tasks = []
        failed_tasks = []
        processed_texts = set()  # Track texts processed in this upload

        for i, text in enumerate(texts):
            if len(text) < 5:  # Skip very short texts
                continue

            # Truncate very long texts
            if len(text) > 5000:
                text = text[:5000] + "..."

            # Check if we already processed this text in current upload
            import hashlib

            text_hash = hashlib.md5(text.strip().encode()).hexdigest()
            if text_hash in processed_texts:
                continue  # Skip duplicate within same file
            processed_texts.add(text_hash)

            # Get workspace state before adding task
            workspace_before = collab_service.get_workspace(workspace_id)
            existing_task_count = len(workspace_before["tasks"])

            task_id = collab_service.add_task(
                workspace_id,
                text,
                metadata={
                    "source": "file_upload",
                    "filename": file.filename,
                    "line_number": i + 1,
                },
            )

            if task_id:
                # Get workspace state after adding task
                workspace_after = collab_service.get_workspace(workspace_id)
                new_task_count = len(workspace_after["tasks"])

                # If task count didn't increase, it was a duplicate
                if new_task_count == existing_task_count:
                    duplicate_tasks.append(task_id)
                else:
                    created_tasks.append(task_id)
            else:
                failed_tasks.append(i + 1)

        return jsonify(
            {
                "message": f"File processed successfully",
                "filename": file.filename,
                "total_texts": len(texts),
                "created_tasks": len(created_tasks),
                "duplicate_tasks": len(duplicate_tasks),
                "failed_tasks": len(failed_tasks),
                "task_ids": created_tasks,
                "duplicate_task_ids": duplicate_tasks,
                "extracted_labels": extracted_labels,
            }
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@collab_bp.route("/workspaces/<workspace_id>/upload/batch", methods=["POST"])
def batch_upload(workspace_id):
    """Upload multiple files at once"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    if "files[]" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files[]")
    results = []
    total_created = 0
    total_duplicates = 0
    all_extracted_labels = set()  # 모든 파일에서 추출된 라벨들

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "message": "File type not allowed",
                }
            )
            continue

        try:
            texts, extracted_labels = parse_file_content(file, file.filename)
            # 추출된 라벨들을 전체 세트에 추가
            all_extracted_labels.update(extracted_labels)
            created_tasks = []
            duplicate_tasks = []
            processed_texts = set()  # Track texts processed for this file

            for i, text in enumerate(texts):
                if len(text) < 5:
                    continue

                if len(text) > 5000:
                    text = text[:5000] + "..."

                # Check if we already processed this text in current file
                import hashlib

                text_hash = hashlib.md5(text.strip().encode()).hexdigest()
                if text_hash in processed_texts:
                    continue  # Skip duplicate within same file
                processed_texts.add(text_hash)

                # Get workspace state before adding task
                workspace_before = collab_service.get_workspace(workspace_id)
                existing_task_count = len(workspace_before["tasks"])

                task_id = collab_service.add_task(
                    workspace_id,
                    text,
                    metadata={
                        "source": "batch_upload",
                        "filename": file.filename,
                        "line_number": i + 1,
                    },
                )

                if task_id:
                    # Get workspace state after adding task
                    workspace_after = collab_service.get_workspace(workspace_id)
                    new_task_count = len(workspace_after["tasks"])

                    # If task count didn't increase, it was a duplicate
                    if new_task_count == existing_task_count:
                        duplicate_tasks.append(task_id)
                    else:
                        created_tasks.append(task_id)

            results.append(
                {
                    "filename": file.filename,
                    "status": "success",
                    "created_tasks": len(created_tasks),
                    "duplicate_tasks": len(duplicate_tasks),
                    "total_texts": len(texts),
                }
            )

            total_created += len(created_tasks)
            total_duplicates += len(duplicate_tasks)

        except Exception as e:
            results.append(
                {"filename": file.filename, "status": "error", "message": str(e)}
            )

    return jsonify(
        {
            "message": f"Batch upload completed",
            "total_files": len(files),
            "total_created_tasks": total_created,
            "total_duplicate_tasks": total_duplicates,
            "results": results,
            "extracted_labels": list(all_extracted_labels),
        }
    )
