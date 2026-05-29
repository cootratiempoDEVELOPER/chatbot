from messages import welcome_message, info_servicios, horarios_atencion, pqrs, optionsPqrs, getBadWords, createPqrs



def handle_main_menu(text, session, phone_number, send, sendButtons):
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
    
    if text == "1":
        send(info_servicios, phone_number)
        session["option"] = 1
    elif text == "2":
        send(horarios_atencion, phone_number)
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
        send("Por favor, ingresa una opción válida.", phone_number)
    return session

def handle_info_servicios(text, session, phone_number, send, sendButtons):
    if text == "menu":
        session["option"] = 0
        send(welcome_message, phone_number)
    elif text == "asesor":
        session["option"] = 4
        send("Por favor, espera mientras te conectamos con un asesor.", phone_number)
    elif text == "salir":
        send("Gracias por contactarnos. ¡Hasta luego!", phone_number)
        return "end"
    else:
        send("Por favor, escribe 'menu', 'asesor' o 'salir'.", phone_number)
    return session

def handle_pqrs(text, session, phone_number, send, sendButtons):
    step = session.get("step", 0)
    
    if step == "1":
        yes_no = text.lower()
        print(yes_no)
        if yes_no == "accept_yes":
            session["step"] = 2
            send("Ingrese su numero de documento:\n", phone_number)
        else:
            send("Debido a que no aceptas las politicas de datos, no podemos ayudarte a registrar tu PQRS.", phone_number)
            session["step"] = 1
            session["opcion"] = 0
            
            send(welcome_message, phone_number)
            
            return session
    if step == "2":
        try:
            documento = int(text)
            if documento <= 0:
                raise ValueError("El número de documento debe ser positivo.")
            if len(str(documento)) < 6 or len(str(documento)) > 11:
                raise ValueError("El número de documento debe tener entre 6 y 11 digitos.")
            session["document"] = documento
            session["step"] = 3
            send("Por favor, ingrese su nombre completo:", phone_number)
        except ValueError:
            send("Número de documento inválido. Ingrese un valor numerico", phone_number)

    elif step == "3":
        nombre = text.strip()

        # 1. Verifica si está vacío
        if not nombre:
            send("El nombre no puede estar vacío.", phone_number)
            return session
        # 2. Verifica que tenga al menos dos palabras
        palabras = nombre.split()
        if len(palabras) < 2:
            send("Debe ingresar al menos nombre y apellido.", phone_number)
            return session
        # 3. Verifica que solo contenga letras y espacios
        if not all(palabra.isalpha() for palabra in palabras):
            send("El nombre solo debe contener letras. No use números ni símbolos.", phone_number)
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
        send("Por favor, ingrese su correo electrónico:", phone_number)

    elif step == "4":
        email = text.strip()
        if "@" not in email or "." not in email:
            send("Correo electrónico inválido. Por favor, ingrese un correo válido.", phone_number)
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

        optionsText, successOptions, options = optionsPqrs()
        
        send(optionsText, phone_number)

    elif step == "5":
        optionsText, successOptions, options = optionsPqrs()
        if text in successOptions:
            # send("Por favor, ingresa una descripcion de tu pqrs, en caso de no requerir ingresa, *No*\n", phone_number)
            send("Desea registrar una descripción? *Si/No*", phone_number)
            findOption = [i["id"] for i in options if i['index'] == int(text)][0]
            session["pqrs"] = findOption
            session["step"] = 6
            return session
        else:
            send(f"Por favor, selecciona un número válido.\n {optionsText}", phone_number)

    elif step == "6":
        text = text.strip().lower()
        if text not in ["si", "no"]:
            send("Por favor, responde con *Si* o *No*.", phone_number)
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
