from django.db.backends import BaseDatabaseClient

class DatabaseClient(BaseDatabaseClient):
    executable_name = 'nzodbcsql'

    def runshell(self):
        settings_dict = self.connection.settings_dict
        user = settings_dict['OPTIONS'].get('user', settings_dict['USER'])
        password = settings_dict['OPTIONS'].get('passwd', settings_dict['PASSWORD'])
        dsn = settings_dict['OPTIONS']['dsn']
        args = ['%s %s' % (self.executable_name, dsn)]

        # XXX: This works only with Python >= 2.4 because subprocess was added
        # in that release
        import subprocess
        try:
            subprocess.call(args, shell=True)
        except KeyboardInterrupt:
            pass
