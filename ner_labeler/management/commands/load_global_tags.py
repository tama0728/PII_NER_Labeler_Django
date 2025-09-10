"""
Django management command to load global tags from tag.json into the database
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ner_labeler.models import Label


class Command(BaseCommand):
    help = 'Load global tags from tag.json file into database labels (not project-specific)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing global labels before loading new ones',
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

        # Clear existing global labels if requested
        if options['clear']:
            deleted_count = Label.objects.filter(project__isnull=True).count()
            Label.objects.filter(project__isnull=True).delete()
            self.stdout.write(
                self.style.WARNING('Deleted {} existing global labels'.format(deleted_count))
            )

        # Create global labels
        created_count = 0
        
        for i, tag in enumerate(tags_data):
            value = tag.get('value', '')
            color = tag.get('background', '#007bff')
            
            # Ensure color is in proper hex format
            if not color.startswith('#'):
                color = '#' + color
            
            # Create global label if it doesn't exist
            label, created = Label.objects.get_or_create(
                project__isnull=True,  # Global label
                value=value,
                defaults={
                    'background': color,
                    'sort_order': i + 1,
                    'hotkey': str(i + 1) if i < 9 else None,  # Assign hotkeys 1-9
                    'description': 'KDPII global label for {}'.format(value),
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write('  ✓ Created global label: {} ({})'.format(value, color))
            else:
                self.stdout.write('  → Global label already exists: {}'.format(value))

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Successfully processed {} tags'.format(len(tags_data)))
        )
        self.stdout.write(
            self.style.SUCCESS('📊 Total new global labels created: {}'.format(created_count))
        )