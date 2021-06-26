from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client

class FDFSStorage(Storage):
    def __init__(self, base_url=None, client_conf=None):
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    def _open(self, name, mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self, name, content, max_length=None):
        '''存储文件时使用'''
        # 新建一个fdfs——client 对象
        # client = Fdfs_client('./util/fdfs/client.conf')
        client = Fdfs_client(self.client_conf)
        # 上传文件到fastdfs
        res = client.upload_by_buffer(content.read())
        #  成功上传，返回字典格式
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        print(res.get('Remote file_id'))
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件到 fastfds 失败')

        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        return False

    def url(self, name):
        return self.base_url + name



