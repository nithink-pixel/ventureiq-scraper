with open('README.md', 'r') as f:
    content = f.read()

img = '![Dashboard](screenshot1.png)\n![Dashboard](screenshot2.png)\n\n'
content = content.replace('**Live Dashboard', img + '**Live Dashboard')

with open('README.md', 'w') as f:
    f.write(content)
print('Done')
