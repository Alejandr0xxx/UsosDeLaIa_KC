# Importamos librerias necesarias
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

# Cargamos las variables de entorno
load_dotenv(dotenv_path='.env')

# Correo de prueba
mock_email = """
Hola,
Estoy muy decepcionado con la compra que hice la semana pasada. Pedí un reloj inteligente el 3 de mayo y lo recibí el 5. Desde que lo abrí me di cuenta de que no era lo que esperaba. La interfaz es confusa y no cumple con las funciones que se mencionaban en la descripción del producto, especialmente el monitoreo de sueño, que era mi principal interés.

No lo he usado más allá de encenderlo y navegar por los menús. El empaque original está intacto y tengo todo tal como llegó. Honestamente, me siento frustrado porque confié en la información publicada y no se ajusta en nada a lo que necesito.

Quiero hacer uso de mi derecho de desistimiento y devolver el producto. Espero una respuesta rápida para tramitar esto cuanto antes.

Gracias,
Marcos Hernández
"""
# Parametros del modelo
model_params =  {
    'model': 'gpt-4o'
}

# Instancia del modelo
model = ChatOpenAI(**model_params)

################################# Sección de recopilación de información #################################
# Esquema para obtener el nombre
email_name_schema = ResponseSchema(
    name='email_name',
    description="""¿Cuál es el nombre y apellido de la persona que envió el correo? 
    Si no está presente, responde con 'Desconocido'."""
)

# Obtener el número del pedido
num_order_schema = ResponseSchema(
    name='order_number',
    description="""¿Cuál es el número de pedido al que hace referencia el correo? 
    Extrae el número exacto del formato, como por ejemplo '#D347-STELLA'. 
    Si no se encuentra, responde con 'Desconocido'."""
)

# Obtener fecha de compra
purchase_date = ResponseSchema(
    name='purchase_date',
    description="""¿Cuál es la fecha de compra del producto? 
    Si se menciona explícitamente (como: 'hace dos semanas', 'el lunes', '12-04-2025', etc.), extrae exactamente lo que dice. 
    Si no se menciona, responde con 'Desconocido'."""
)

# Obtener razón d ela devolución
issue_summary_schema = ResponseSchema(
    name='issue_summary',
    description="""Resume de manera objetiva y clara cuál es el motivo de la devolución descrito en el correo. 
    Usa 1 o 2 frases claras."""
)

# Creamos una lista con los esquemas
info_response_schemas = [email_name_schema, num_order_schema, purchase_date, issue_summary_schema]

# Le pasamos los esquemas al objeto
info_output_parser = StructuredOutputParser.from_response_schemas(info_response_schemas)

# Tomamos las instrucciones
info_format_instructions = info_output_parser.get_format_instructions()

# El template para obtener la info
info_template = """
    Email: {email}
    
    {format_instructions}
"""

# Ahora instanciamos el objeto para crear el prompt 
get_info_prompt = ChatPromptTemplate.from_template(info_template)

# Le pasamos las variables
message = get_info_prompt.format_messages(email=mock_email, format_instructions=info_format_instructions)

# Hacemos el llamado al modelo y le pasamos el prompt
info_res = model.invoke(message)

# Parseamos el resultado
info_parsed = info_output_parser.parse(info_res.content)

################################## Resolución de la devolución########################################

# Creamos el esquema que devolverá True o False de acuerdo a las reglas de devolución
accept_reason_schema = ResponseSchema(
    name='accept_reason',
    description="""Según la descripción del problema, ¿esto corresponde a un motivo válido para 
    aceptar la devolución? 
    Responde True o False de acuerdo a las directrices de devolución
    """
)

# Esquema para la razón de la aceptación o negación de la devolución
accept_reason_detail_schema = ResponseSchema(
    name='accept_reason_detail',
    description="""Explica el motivo sí cumple o no con las políticas de devolución. 
    Por ejemplo: 'Fue dañado durante el transporte, lo cual no está cubierto por garantía' o 'Se entregó el producto defectuoso de fábrica'."""
)

# Directrices para la devolución
return_guidelines = """
Motivos para ACEPTAR una solicitud de devolución: 
- Defecto de fabricación confirmado: El producto presenta fallos 
internos o de funcionamiento no atribuibles al transporte ni a un mal 
uso. 
- Error en el suministro: Se han entregado componentes incorrectos 
en cuanto a modelo, cantidad o especificación respecto al pedido 
original. 
- Producto incompleto o con elementos faltantes de fábrica: Falta 
documentación técnica, piezas necesarias o embalaje original desde 
el origen. 

Motivos para RECHAZAR una solicitud de devolución: 
- Daños ocasionados durante el transporte: Si el transporte no 
estaba asegurado o contratado directamente por la empresa, no se 
asume responsabilidad por los daños ocurridos durante el envío. 
- Manipulación indebida por parte del cliente: Instalación incorrecta, 
modificaciones o uso inapropiado del componente. 
- Superación del plazo máximo para devoluciones: La solicitud se 
presenta fuera del periodo establecido por la política de devoluciones 
(por ejemplo, 14 días naturales). 
"""

# Lista con los esquemas
accept_reason_schema = [accept_reason_schema, accept_reason_detail_schema]

# Le pasamos los esquemas al objeto
accept_parser = StructuredOutputParser.from_response_schemas(accept_reason_schema)

# Tomamos las instrucciones
accept_format_instructions = accept_parser.get_format_instructions()

# Plantilla del problema con las directrices
accept_template = """
    Resumen del problema: {issue_summary}
    
    Directrices de devolución:
    {return_guidelines}
    
    {accept_format_instructions}
"""

# Creamos el prompt
accept_prompt = ChatPromptTemplate.from_template(accept_template)

# Le pasamos las variables
accept_msg = accept_prompt.format_messages(issue_summary= info_parsed['issue_summary'], 
                            return_guidelines= return_guidelines, 
                            accept_format_instructions= accept_format_instructions)

# Llamamos al modelo y pasamos el prompt
accept_res = model.invoke(accept_msg)

# Parseamos la info que nos devuelve
accept_parsed = accept_parser.parse(accept_res.content)

# Escribimos el prompt para la respuesta
email_reply_template = """
Eres un agente de atención al cliente de Componentes Intergalácticos Industriales S.A
Debes redactar un correo formal en respuesta a un cliente que solicitó la devolución de un producto.

Contexto del caso:
- Nombre del cliente: {client_name}
- Número de pedido: {order_number}
- Resumen del problema: {issue_summary}
- ¿Se acepta la devolución?: {accept_decision}
- Motivo de decisión: {accept_reason_detail}

Redacta un mensaje profesional, cortés y objetivo.
No inventes información que no se te haya proporcionado.
"""

# Le pasamos el prompt al objeto 
reply_prompt = ChatPromptTemplate.from_template(email_reply_template)

# Le pasamos las variables
reply_msg = reply_prompt.format_messages(
    client_name=info_parsed['email_name'],
    order_number=info_parsed['order_number'],
    issue_summary=info_parsed['issue_summary'],
    accept_decision=accept_parsed['accept_reason'],
    accept_reason_detail=accept_parsed['accept_reason_detail'],
)

# Llamamos al modelo
reply = model.invoke(reply_msg)

# Imprimo el resultado
print(reply.content)

# Resultado:
# Asunto: Confirmación de Devolución de Producto
# Estimado Sr. Hernández:
# Le agradecemos por ponerse en contacto con nosotros y lamentamos sinceramente los inconvenientes que ha experimentado con su reciente compra.
# Tras revisar su solicitud de devolución, nos gustaría ofrecerle nuestras más sinceras disculpas por los problemas que ha encontrado con el reloj inteligente, en particular, con la funcionalidad de monitoreo de sueño y la confusión de la interfaz. Hemos determinado que el producto presenta un defecto de funcionamiento interno que no es atribuible a un mal uso y se alinea con un defecto de fabricación.     
# Por lo tanto, aceptamos su solicitud de devolución en ejercicio de su derecho de desistimiento. A continuación, le comunicaremos los pasos a seguir para completar el proceso de devolución. Le rogamos que proporcione su número de pedido para agilizar los trámites administrativos. Una vez recibido, le enviaremos una etiqueta prepagada para el envío del producto defectuoso.
# Valoramos su paciencia y comprensión en este asunto y estamos comprometidos a asegurar que su experiencia con Componentes Intergalácticos Industriales S.A. sea positiva. Quedamos a su entera disposición para cualquier pregunta o inquietud adicional que pueda tener.
# Atentamente,
# [Su Nombre]
# Servicio de Atención al Cliente
# Componentes Intergalácticos Industriales S.A.
# [Teléfono de contacto]
# [Correo electrónico de contacto]