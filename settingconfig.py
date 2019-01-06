import ConfigParser
class SettingConfig():
    def __init__(self):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read('setting.conf')
    def get(self,section,option):
        return self.cf.get(section,option)

if __name__=='__main__':
    print SettingConfig().get('redis','redis_host')