from django.http import JsonResponse
import os


# 上传文件
def upload(request):
    if request.method == 'POST':
        files = request.FILES.getlist('file',None)
        print(files)
        if not files:
            return JsonResponse({'result':'failure'})
        destination = open(os.path.join("D:\\upload",files[0].name), 'wb+')
        for chunk in files[0].chunks():
            destination.write(chunk)
        destination.close()
        return JsonResponse({'result':'success'})
    else:
        return JsonResponse({'result':'failure'})