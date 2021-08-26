from django import forms


class StartNfsMitmForm(forms.Form):
    server_ip = forms.CharField(max_length=15)
    arpspoof = forms.BooleanField(initial=False, required=False)
    popout = forms.BooleanField(initial=True, required=False)


class GetFileForm(forms.Form):
    name = forms.CharField(max_length=200)


class ListDirForm(forms.Form):
    directory = forms.CharField(max_length=200, initial='.')


class FileStatsForm(forms.Form):
    name = forms.CharField(max_length=200)


class CreateFileForm(forms.Form):
    name = forms.CharField(max_length=200)


class ClearFileForm(forms.Form):
    name = forms.CharField(max_length=200)


class DeleteFileForm(forms.Form):
    name = forms.CharField(max_length=200)
