import os
import argparse
import secrets


def generate_secret_key(length=50):
    return secrets.token_urlsafe(length)[:length]


def create_templates(project_name: str, secret_key: str, frameworks: list):
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)

    for framework in frameworks:
        framework_dir = os.path.join(templates_dir, framework)
        os.makedirs(framework_dir, exist_ok=True)

        if framework == 'react':
            with open(os.path.join(framework_dir, 'package.json'), 'w') as f:
                f.write('{\n  "name": "%s",\n  "version": "0.1.0"\n}' % project_name)
            os.makedirs(os.path.join(framework_dir, 'src'), exist_ok=True)
            with open(os.path.join(framework_dir, 'src', 'App.js'), 'w') as f:
                f.write("""import React from 'react';

function App() {
  return (
    <div>
      <h1>Hello, %s!</h1>
    </div>
  );
}

export default App;""" % project_name)
            os.makedirs(os.path.join(framework_dir, 'public'), exist_ok=True)
            with open(os.path.join(framework_dir, 'public', 'index.html'), 'w') as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
  <title>%s</title>
</head><body>
  <div id=\"root\"></div>
</body>
</html>""" % project_name)

        elif framework == 'django':
            manage_py_content = """#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
""" % project_name
            with open(os.path.join(framework_dir, 'manage.py'), 'w') as f:
                f.write(manage_py_content)

            project_settings_dir = os.path.join(framework_dir, project_name)
            os.makedirs(project_settings_dir, exist_ok=True)
            with open(os.path.join(project_settings_dir, '__init__.py'), 'w') as f:
                f.write('')
            with open(os.path.join(project_settings_dir, 'settings.py'), 'w') as f:
                f.write("SECRET_KEY = '%s'\nDEBUG = True\nALLOWED_HOSTS = []" % secret_key)
            with open(os.path.join(project_settings_dir, 'urls.py'), 'w') as f:
                f.write('from django.contrib import admin\nfrom django.urls import path\n\nurlpatterns = [\n    path(\'admin/\', admin.site.urls),\n]')
            with open(os.path.join(framework_dir, 'wsgi.py'), 'w') as f:
                f.write("import os\n\nfrom django.core.wsgi import get_wsgi_application\n\nos.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"%s.settings\")\n\napplication = get_wsgi_application()" % project_name)
            with open(os.path.join(framework_dir, 'asgi.py'), 'w') as f:
                f.write("import os\n\nfrom django.core.asgi import get_asgi_application\n\nos.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"%s.settings\")\n\napplication = get_asgi_application()" % project_name)

        elif framework == 'flutter':
            with open(os.path.join(framework_dir, 'pubspec.yaml'), 'w') as f:
                f.write("""name: %s
description: A new Flutter project.
version: 1.0.0+1
environment:
  sdk: \">=2.12.0 <3.0.0\"\ndependencies:\n  flutter:\n    sdk: flutter\n  cupertino_icons: ^1.0.2\ndev_dependencies:\n  flutter_test:\n    sdk: flutter\nflutter:\n  uses-material-design: true""" % project_name)
            os.makedirs(os.path.join(framework_dir, 'lib'), exist_ok=True)
            with open(os.path.join(framework_dir, 'lib', 'main.dart'), 'w') as f:
                f.write("""import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '%s',
      home: Scaffold(
        appBar: AppBar(
          title: Text('%s'),
        ),
        body: Center(
          child: Text('Hello, %s!'),
        ),
      ),
    );
  }
}""" % (project_name, project_name, project_name))


def parse_args():
    parser = argparse.ArgumentParser(description='Orix — multi-framework project templater')
    parser.add_argument('--project-name', '-n', default='my_project', help='Project name to use in templates')
    parser.add_argument('--secret-key', '-s', default=None, help='Secret key to use for Django settings')
    parser.add_argument('--frameworks', '-f', default='react,django,flutter', help='Comma-separated frameworks to scaffold')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    project_name = args.project_name
    secret_key = args.secret_key or generate_secret_key(50)
    frameworks = [fw.strip() for fw in args.frameworks.split(',') if fw.strip()]

    create_templates(project_name, secret_key, frameworks)
    print('Templates created for %s in "templates/" (%s)' % (project_name, ', '.join(frameworks)))
