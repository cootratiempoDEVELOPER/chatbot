from messages import welcome_message, info_servicios, horarios_atencion, pqrs, optionsPqrs, getBadWords, createPqrs, OPTIONS_LIST_WELCOME

buttons = [
    {
        "type": "reply",
        "reply": {
            "id": "accept_yes",
            "title": "Sí"
        }
    },
    {
        "type": "reply",
        "reply": {
            "id": "accept_no",
            "title": "No"
        }
    }
]

buttons_exit = [
    {
        "type": "reply",
        "reply": {
            "id": "asesor",
            "title": "Contactar asesor"
        }
    },
    {
        "type": "reply",
        "reply": {
            "id": "menu",
            "title": "Menu principal"
        }
    },
    {
        "type": "reply",
        "reply": {
            "id": "salir",
            "title": "Finalizar solicitud"
        }
    }
]
    

def handle_main_menu(text, session, phone_number, send, sendButtons, sendList):
    if text == "1":
        send(info_servicios, phone_number)
        sendButtons("Puede seleccionar una de las siguientes opciones. Si no selecciona ninguna, la solicitud finalizará automáticamente después de 15 minutos.", phone_number, buttons_exit)
        session["option"] = 1
    elif text == "2":
        send(horarios_atencion, phone_number)
        sendButtons("Puede seleccionar una de las siguientes opciones. Si no selecciona ninguna, la solicitud finalizará automáticamente después de 15 minutos.", phone_number, buttons_exit)
        session["option"] = 2
    elif text == "3":
        send(pqrs, phone_number)
        sendButtons(
            "¿Aceptas el tratamiento de datos?",
            phone_number,
            buttons
        )
        session["option"] = 3
        session["step"] = 1
    elif text == "4":
        send("Para comunicarte directamente con un asesor escribenos a este numero: https://wa.me/573144756457", phone_number)
        session["option"] = 4
    else:
        sendList(phone_number, "Por favor, ingresa una opción válida.", OPTIONS_LIST_WELCOME)
    return session

def handle_info_servicios(text, session, phone_number, send, sendButtons, sendList):
    if text in ["menu", "Menu", "menú", "Menú"]:
        session["option"] = 0
        send(welcome_message, phone_number)
    elif text == "asesor":
        session["option"] = 4
        send("Por favor, espera mientras te conectamos con un asesor.", phone_number)
    elif text == "salir":
        send("Gracias por contactarnos. ¡Hasta luego!", phone_number)
        return "end"
    else:
        sendButtons("Por favor, seleccione una de las siguientes opciones: ", phone_number, buttons_exit)
    return session

def handle_pqrs(text, session, phone_number, send, sendButtons, sendList):
    step = session.get("step", 0)
    
    if step == "1":
        yes_no = text.lower()
        if yes_no == "accept_yes":
            session["step"] = 2
            send("Ingresa el numero de documento, sin puntos ni espacios\n", phone_number)
        elif yes_no == "accept_no":
            session["step"] = 1
            session["opcion"] = 0
            send("Debido a que no aceptas las políticas de tratamiento de datos, no podemos ayudarte a registrar tu PQRS.\nInicia una nueva comunicación.", phone_number)
            return "end"
        else:
            send("Seleccione una opción válida.\n", phone_number)
            
            sendButtons(
                "¿Aceptas el tratamiento de datos?",
                phone_number,
                buttons
            )
                

    if step == "2":
        try:
            documento = int(text)
            if documento <= 0:
                raise ValueError("El número de documento debe ser positivo.")
            if len(str(documento)) < 6 or len(str(documento)) > 11:
                raise ValueError("El número de documento debe tener entre 6 y 11 digitos.")
            session["document"] = documento
            session["step"] = 3
            send("Por favor, ingresa tu nombre completo", phone_number)
        except ValueError:
            send("Número de documento inválido. Ingresa un valor numerico", phone_number)

    elif step == "3":
        nombre = text.strip()

        # 1. Verifica si está vacío
        if not nombre:
            send("El nombre no puede estar vacío.", phone_number)
            return session
        # 2. Verifica que tenga al menos dos palabras
        palabras = nombre.split()
        if len(palabras) < 2:
            send("Debes ingresar al menos nombre y apellido.", phone_number)
            return session
        # 3. Verifica que solo contenga letras y espacios
        if not all(palabra.isalpha() for palabra in palabras):
            send("El nombre solo debe contener letras. No uses números ni símbolos.", phone_number)
            return session

        # 4. Verifica que cada palabra tenga al menos 2 letras
        if any(len(palabra) < 3 for palabra in palabras):
            send("Cada parte del nombre debe tener al menos 3 letras.", phone_number)
            return session

        # 5. Verifica que no sea excesivamente largo
        if len(nombre) > 60:
            send("El nombre es demasiado largo. Intente abreviarlo.", phone_number)
            return session

        # ✅ Si pasa todas las validaciones, guarda en la sesión
        session["name"] = nombre
        session["step"] = 4
        send("Por favor, ingresa tu correo electrónico", phone_number)

    elif step == "4":
        email = text.strip()
        if "@" not in email or "." not in email:
            send("Correo electrónico inválido. Por favor, ingresa un correo válido.", phone_number)
            return session
        if len(email) > 50:
            send("El correo electrónico es demasiado largo. Intente abreviarlo.", phone_number)
            return session
        splitEmail = email.split("@")
        if len(splitEmail[0]) < 3:
            send("El nombre de usuario del correo debe tener al menos 3 caracteres.", phone_number)
            return session
        session["email"] = email
        session["step"] = 5
        send("Su correo es valido, espere unos segundos...", phone_number)
        
        successOptions, options = optionsPqrs()
        
    if successOptions:

        for i in range(0, len(options), 10):

            options_chunk = options[i:i + 10]

            if i == 0:
                message = "Selecciona el tipo de PQRS que deseas crear:"
            else:
                message = "Más tipos de PQRS. Selecciona una opción:"

            sendList(
                phone_number,
                message,
                options_chunk,
                pqrs=True
            )
        else:
            send("En este momento no se pueden crear PQRS, por favor comunicate al Whatsapp https://wa.me/573144756457.")

    elif step == "5":
        successOptions, options = optionsPqrs()
        correctOption = [str(option['id']) for option in options]
        if successOptions and text in correctOption:
            # send("Por favor, ingresa una descripcion de tu pqrs, en caso de no requerir ingresa, *No*\n", phone_number)
            sendButtons(
                "Deseas registrar una descripción?",
                phone_number,
                buttons
            )
            # send("Desea registrar una descripción? *Si/No*", phone_number)
            findOption = [i["id"] for i in options if i['id'] == int(text)][0]
            session["pqrs"] = findOption
            session["step"] = 6
            return session
        else:
            if successOptions:
                for i in range(0, len(options), 10):

                    options_chunk = options[i:i + 10]

                    if i == 0:
                        message = "Selecciona el tipo de PQRS que deseas crear:"
                    else:
                        message = "Más tipos de PQRS. Selecciona una opción:"

                    sendList(
                        phone_number,
                        message,
                        options_chunk,
                        pqrs=True
                    )
                    sendList(phone_number, "Por favor, selecciona una de las opciones: ", options, pqrs=True)

    elif step == "6":
        text = text.strip().lower()
        if text not in ["si", "no"]:
            sendButtons(
                "Debes seleccionar una de las siguientes opciones: ",
                phone_number,
                buttons
            )
            return session

        text = text.strip().lower()
        if text.lower() == "no":
            session["description"] = "No se proporcionó descripción."
            succesCreated, created = createPqrs(session, phone_number)
            numPqrs = created['num']
            if not succesCreated:
                send("Hubo un error al crear la PQRS. Por favor, inténtalo de nuevo más tarde.", phone_number)
                return session
            send(f"PQRS creada exitosamente, tu numero de solicitud es *{numPqrs}*", phone_number)
            
            send("Gracias por registrar tu PQRS. Nos pondremos en contacto contigo pronto.", phone_number)
            return "end"
        
        send("Ingresa la descripción de tu PQRS.", phone_number)
        session["step"] = 7
        return session
        
    elif step == "7":
        badWords = getBadWords()
        descripcion = text.strip()
        palabras = text.split()
        
        if len(descripcion) < 10:
            send("La descripción debe tener al menos 10 caracteres.", phone_number)
            return session
        elif not all(palabra.isalnum() for palabra in palabras):
            send("La description no puede contener caracteres especiales.", phone_number)
            return session
        elif any(word in text for word in badWords):
            send("Por favor no incluya lenguaje inapropiado", phone_number)
            return session

        session["description"] = descripcion

        succesCreated, created = createPqrs(session, phone_number)
        numPqrs = created['num']
        if not succesCreated:
            send("Hubo un error al crear la PQRS. Por favor, inténtalo de nuevo más tarde.", phone_number)
            return session
        send(f"PQRS creada exitosamente, tu numero de solicitud es *{numPqrs}*", phone_number)
        
        send("Gracias por registrar tu PQRS. Nos pondremos en contacto contigo pronto.", phone_number)

        return "end"

    return session

# Mapa de handlers
handlers = {
    0: handle_main_menu,
    1: handle_info_servicios,
    2: handle_info_servicios,
    3: handle_pqrs,
}
