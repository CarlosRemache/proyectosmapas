from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario, Vehiculo
from django.utils.timezone import now


def login_usuario(request):
    #validar el inicio de cesion de usuario
    if request.session.get('usuario_id'):
        return redirect('/inicio')

    if request.method == 'POST':
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')

        try:
            #busca en la base de datos con sus datos correspondientes
            usuario = Usuario.objects.get(correo_usuario=correo, contrasena_usuario=contrasena)
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nombre'] = usuario.nombre_usuario
            request.session['usuario_apellido'] = usuario.apellido_usuario
            messages.success(request, "Inicio de sesión exitoso")
            return redirect('/inicio')
        except Usuario.DoesNotExist:
            messages.error(request, "Correo o contraseña incorrectos")

    return render(request, 'login.html')








#sirve para cerrar la cesion 
def logout_usuario(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente")
    return redirect('/login') #devuelve la pantalla en login





def inicio(request):
    # Proteger el inicio: solo usuarios logueados
    if not request.session.get('usuario_id'):
        return redirect('/login')
    return render(request, 'inicio.html')



def nuevousuario(request):
    return render(request, 'nuevousuario.html')


def guardarusuario(request):
    nombre_usuario = request.POST['txt_nombre']
    apellido_usuario = request.POST['txt_apellido']
    correo_usuario = request.POST['txt_correo']
    contrasena_usuario = request.POST['txt_contrasena']
    nuevousuario=Usuario.objects.create(nombre_usuario=nombre_usuario,apellido_usuario=apellido_usuario,correo_usuario=correo_usuario,contrasena_usuario=contrasena_usuario)
    messages.success(request, "Usuario creado correctamente. Inicia sesión.")
    return redirect('/login')




def editarusuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)
    return render(request, 'editarusuario.html', {'usuario': usuario})




def procesareditarusuario(request):
    usuario = Usuario.objects.get(id_usuario=request.POST['id_usuario'])
    usuario.nombre_usuario = request.POST['txt_nombre']
    usuario.apellido_usuario = request.POST['txt_apellido']
    usuario.correo_usuario = request.POST['txt_correo']

    nueva_contra = request.POST['txt_contrasena']
    if nueva_contra != "":
        usuario.contrasena_usuario = nueva_contra
        
    usuario.save()

    messages.success(request, "Usuario actualizado correctamente")
    return redirect('/perfilusuario/')




def perfilusuario(request):
    usuario_id = request.session.get('usuario_id') #obtiene el id del usuario creado
    usuario = Usuario.objects.get(id_usuario=usuario_id) #busca el usuario en la base de datos
    return render(request, 'perfilusuario.html', {'usuario': usuario})




#---------------------------------------------------------------------------------------------------------------
# Vehiculo

def nuevovehiculo(request):
    id_usuario = request.session.get('usuario_id')  #obtiene el usuario que se inicio secion
    usuario = Usuario.objects.get(id_usuario=id_usuario) #Busca en la base de datos al usuario
    return render(request, 'nuevovehiculo.html', {'usuario': usuario})#envia al usuario a la pagina 




def guardarvehiculo(request):
    id_usuario = request.POST['usuario']
    tipovehi = request.POST['txt_tipo_vehiculo']
    tipocomb = request.POST['txt_tipo_combustible']
    matricula = request.POST['txt_matricula']
    modelo = request.POST['txt_modelo']
    usuario = Usuario.objects.get(id_usuario=id_usuario)
    Vehiculo.objects.create(
        usuario=usuario,
        tipovehiculo_vehiculo=tipovehi,
        tipocombustible_vehiculo=tipocomb,
        matricula_vehiculo=matricula,
        modelo_vehiculo=modelo
    )

    messages.success(request, "Vehículo guardado")
    return redirect('/listadovehiculo')


def listadovehiculo(request):
    vehiculos = Vehiculo.objects.all()
    return render(request, 'listadovehiculo.html', {'vehiculos': vehiculos})


def eliminarvehiculo(request, id):
    vehiculo = Vehiculo.objects.get(id_vehiculo=id)
    vehiculo.delete()
    messages.success(request, "Vehículo eliminado")
    return redirect('/inicio')


def editarvehiculo(request, id):
    id_usuario = request.session.get('usuario_id') 
    vehiculo = Vehiculo.objects.get(id_vehiculo=id)
    usuarios = Usuario.objects.get(id_usuario=id_usuario) #Busca en la base de datos al usuario
    return render(request, 'editarvehiculo.html', {'vehiculo': vehiculo, 'usuarios': usuarios})


def procesareditarvehiculo(request):
    vehiculo = Vehiculo.objects.get(id_vehiculo=request.POST['id'])
    vehiculo.usuario = Usuario.objects.get(id_usuario=request.POST['usuario'])
    vehiculo.tipovehiculo_vehiculo = request.POST['txt_tipo_vehiculo']
    vehiculo.tipocombustible_vehiculo = request.POST['txt_tipo_combustible']
    vehiculo.matricula_vehiculo = request.POST['txt_matricula']
    vehiculo.modelo_vehiculo = request.POST['txt_modelo']
    vehiculo.save()

    messages.success(request, "Vehículo editado exitosamente")
    return redirect('/listadovehiculo')
