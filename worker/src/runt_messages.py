"""Mensajes del modal SweetAlert tras enviar captcha en RUNT."""

CAPTCHA_RESPONSES = {
    "El captcha no es valido.": {
        "message": "Captcha mal ingresado",
        "retry": True,
    },
    "La imagen no coincide con el valor ingresado, por favor verifiquela e intente nuevamente.": {
        "message": "Captcha mal ingresado",
        "retry": True,
    },
    "Señor Usuario, para el vehículo consultado no hay información registrada en el sistema RUNT.": {
        "message": "Captcha OK — sin datos en RUNT",
        "retry": False,
        "success": False,
    },
    "Los datos registrados no corresponden con los propietarios activos para el vehículo consultado.": {
        "message": "Captcha OK — documento no coincide",
        "retry": False,
        "success": False,
    },
    "Señor Usuario: El vehículo consultado aún no ha sido registrado en el sistema RUNT por el organismo de tránsito donde se encuentra matriculado. Le sugerimos dirigirse al mismo a solicitar el envío de su información, de lo contrario no se podrá realizar trámite de tránsito sobre el automotor.": {
        "message": "Captcha OK — vehiculo no registrado en RUNT",
        "retry": False,
        "success": False,
    },
}
