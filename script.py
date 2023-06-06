import subprocess

packages_to_uninstall = [
    'pchardet',
    'pchardet',
    'click',
    'deptry',
    'packaging',
    'pathspec',
    'pip-check-reqs'
]

for package in packages_to_uninstall:
    subprocess.run(['pip', 'uninstall', '-y', package])
