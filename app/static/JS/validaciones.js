function validarNombre(){
    const formatoNombre = /^[a-zA-Z\s]+$/;
    const nombreInput = document.getElementById("nombre_personal");
    const nombre = nombreInput.value.trim();
    const largo = nombre.length;

    if (largo < 2){
        document.getElementById("alertaNombre").style.display = "block";
        return false;
    }
    else if(!formatoNombre.test(nombre)){
        document.getElementById("alertaNombre2").style.display = "block";
        return false;
    }
    else{
        document.getElementById("alertaNombre").style.display = "none";
        document.getElementById("alertaNombre2").style.display = "none";
        return true;
    }
}

function validarRut() {
    const rut = document.getElementById("rut_personal").value;
    // Expresión regular para validar el rut en formato xxxxxxxx-x
    const formatoRut = /^\d{1,8}-[\dkK]$/i;

    // Si no se respeta el formato, se retornará un mensaje de error
    if (!formatoRut.test(rut)) {
        document.getElementById("alertaRut").style.display = "block";
        return false;
    }

    // Eliminar puntos y guiones del rut
    const rutSinFormato = rut.replace(/\./g, '').replace(/-/g, '');

    // Separar el número base del dígito verificador
    const rutBase = rutSinFormato.slice(0, -1);
    const digitoVerificador = rutSinFormato.slice(-1).toUpperCase();

    // Calcular dígito verificador esperado
    let suma = 0;
    let multiplicador = 2;

    for (let i = rutBase.length - 1; i >= 0; i--) {
        suma += parseInt(rutBase[i]) * multiplicador;
        multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
    }

    const digitoEsperado = 11 - (suma % 11);
    const digitoEsperadoTexto = digitoEsperado === 11 ? '0' : (digitoEsperado === 10 ? 'K' : digitoEsperado.toString()).toUpperCase();

    if (digitoVerificador !== digitoEsperadoTexto) {
        document.getElementById("alertaRut2").style.display = "block";
        return false;
    }

    document.getElementById("alertaRut").style.display = "none";
    document.getElementById("alertaRut2").style.display = "none";
    return true;
}

function validarApellidoPaterno(){
    const formatoApellido = /^[a-zA-Z\s]+$/;
    const apellidoInput = document.getElementById("apellido_paterno");
    const apellido = apellidoInput.value.trim();
    const largo = apellido.length;

    if (largo < 2){
        document.getElementById("alertaAP").style.display = "block";
        return false;
    }
    else if(!formatoApellido.test(apellido)){
        document.getElementById("alertaAP2").style.display = "block";
        return false;
    }
    else{
        document.getElementById("alertaAP").style.display = "none";
        document.getElementById("alertaAP2").style.display = "none";
        return true;
    }
}

function validarApellidoMaterno(){
    const formatoApellido = /^[a-zA-Z\s]+$/;
    const apellidoInput = document.getElementById("apellido_materno");
    const apellido = apellidoInput.value.trim();
    const largo = apellido.length;

    if (largo < 2){
        document.getElementById("alertaAM").style.display = "block";
        return false;
    }
    else if(!formatoApellido.test(apellido)){
        document.getElementById("alertaAM2").style.display = "block";
        return false;
    }
    else{
        document.getElementById("alertaAM").style.display = "none";
        document.getElementById("alertaAM2").style.display = "none";
        return true;
    }
}

// Validación fecha.
function validarFecha() {
    const fechaInput = document.getElementById("fecha_contrato");
    const fechaSeleccionada = new Date(fechaInput.value);

    // Obtener la fecha actual
    const fechaActual = new Date();

    // Comparar las fechas
    if (fechaSeleccionada > fechaActual) {
        document.getElementById("alertaFecha").style.display = "block";
        return false;
    } else {
        document.getElementById("alertaFecha").style.display = "none";
        return true;
    }
}

// Validación número telefónico.
function validarNumero(){
    // Obtener la longitud y el valor del número ingresado por el usuario.
    const numeroInput = document.getElementById("fono");
    const numero = numeroInput.value.trim();
    const largo = numero.length;

    // Expresión regular para permitir solo dígitos y el signo "+" opcional.
    const formatoNumero = /^[\+0-9 ]*$/;

    // Si el número no cumple el formato permitido.
    if (!formatoNumero.test(numero)) {
        document.getElementById("alertaNumero2").style.display = "block";
        return false;
    }
    // Si el largo es menor a 9 números.
    else if(largo < 9){
        document.getElementById("alertaNumero").style.display = "block";
        return false;
    }
    // Si el largo es mayor o igual a 10 números.
    else if(largo >= 10){
        document.getElementById("alertaNumero3").style.display = "block";
        return false;
    }
    // Si el número cumple el formato y se ha ingresado al menos un número.
    else {
        document.getElementById("alertaNumero").style.display = "none";
        document.getElementById("alertaNumero2").style.display = "none";
        return true;
    }
}

function validarRegistro() {
    if (!validarRut() || !validarNombre() || !validarApellidoPaterno() || !validarApellidoMaterno() || !validarFecha() || !validarNumero()) {
        return false;
    }
    return true;
}