"""
Django management command to load tags from tag.json into the database
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ner_labeler.models import Label, Project


class Command(BaseCommand):
    help = 'Load tags from tag.json file into database labels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Project ID to associate labels with (default: all projects)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing labels before loading new ones',
        )

    def handle(self, *args, **options):
        # Find tag.json file
        tag_json_path = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'tag.json')
        
        if not os.path.exists(tag_json_path):
            self.stdout.write(
                self.style.ERROR('tag.json not found at {}'.format(tag_json_path))
            )
            return

        # Load tags from JSON
        try:
            with open(tag_json_path, 'r', encoding='utf-8') as f:
                tags_data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Error reading tag.json: {}'.format(e))
            )
            return

        # Get projects to associate labels with
        if options['project_id']:
            try:
                projects = [Project.objects.get(id=options['project_id'])]
            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Project with ID {} not found'.format(options["project_id"]))
                )
                return
        else:
            projects = Project.objects.all()
            if not projects.exists():
                self.stdout.write(
                    self.style.ERROR('No projects found. Please create a project first.')
                )
                return

        # Clear existing labels if requested
        if options['clear']:
            for project in projects:
                deleted_count = project.labels.count()
                project.labels.all().delete()
                self.stdout.write(
                    self.style.WARNING('Deleted {} existing labels from project "{}"'.format(deleted_count, project.name))
                )

        # Create labels for each project
        total_created = 0
        for project in projects:
            created_count = 0
            
            for i, tag in enumerate(tags_data):
                value = tag.get('value', '')
                color = tag.get('background', '#007bff')
                
                # Ensure color is in proper hex format
                if not color.startswith('#'):
                    color = '#' + color
                
                # Create label if it doesn't exist
                label, created = Label.objects.get_or_create(
                    project=project,
                    value=value,
                    defaults={
                        'background': color,
                        'sort_order': i + 1,
                        'hotkey': str(i + 1) if i < 9 else None,  # Assign hotkeys 1-9
                        'description': 'KDPII label for {}'.format(value),
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write('  ✓ Created label: {} ({})'.format(value, color))
                else:
                    self.stdout.write('  → Label already exists: {}'.format(value))
            
            total_created += created_count
            self.stdout.write(
                self.style.SUCCESS('Project "{}": {} new labels created'.format(project.name, created_count))
            )

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Successfully processed {} tags'.format(len(tags_data)))
        )
        self.stdout.write(
            self.style.SUCCESS('📊 Total new labels created: {}'.format(total_created))
        )
        self.stdout.write(
            self.style.SUCCESS('📁 Projects updated: {}'.format(len(projects)))
        )