import ConfigParser
cp = ConfigParser.ConfigParser()
cp.read('setting.conf')
for i in cp.sections():
    for item in cp.items(i):
        print item[0], item[1]
        cp.set(i, item[0], 'jjjj')

with open('setting.conf', 'w+') as f:
    cp.write(f)
