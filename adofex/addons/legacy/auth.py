# Jurgen's proposition on auth

import hashlib
from adofex import settings
import adofex.legacy.models as legacy

class IBFBackend:
    """
    Django authentication backend for Invision Power Board user database.
    Also fetches e-mail address from IPB user profile and updates Django user profile on every login.
    """
    def authenticate(self, username=None, password=None):
        valid = False
        email = None

        if username and password:

            from django.db import connection
            cursor = connection.cursor()
            db = MySQLdb.connect(user=MYSQL_USER, passwd=MYSQL_PASSWD, db=MYSQL_DB)
            cursor = db.cursor()
            cursor.execute("select member_id, member_group_id, email, members_pass_hash, members_pass_salt from %smembers where members_l_username = '%s' and member_banned = '0'" % (settings.IBF_PREFIX, lower(username)))
            row = cursor.fetchone()
            email = row[2]
            hash = hashlib.md5(hashlib.md5(row[4]).hexdigest() + hashlib.md5(password).hexdigest()).hexdigest()
            if row[3] == hash:
                valid = True

        if valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(username=username)
                user.is_staff = False
                user.is_superuser = False
                user.set_unusable_password() # disable login through Model backend
                user.save()
            if not email is None:
                user.email = email
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None