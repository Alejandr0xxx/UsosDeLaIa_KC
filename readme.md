# Workflow para determinar si un pedido es apto o no para devolución

Hice uso del modelo gpt-4o, el cual primero recibe el mensaje de inicio de devolución del cliente, extrae la información del cliente, del pedido y además la razón de la devolución.
LLuego lamamos nuevamente al modelo y le pasamos en un prompt tanto la razón de la devolución y las reglas para determinar si aplica o no, esta llamada nos devolverá un booleano que nos dice True si aplica y Falso en caso de que no, además de devolvernos la razón de porque lo aceptamos o rechazamos.
Finalmente en la última llamada se le pasa la información del usuario, del pedido, el booleano con la confirmación de aceptación de la devolución y la razón, lo que nos devolverá el correo final.
Considero que primero tomar esta información importante y luego pasar esto al modelo con las directrices, a pesar de que de buenos resultados, no es un método muy eficiente en términos de costo, ya que cada vez pasar las reglas de devolución puede realizar un gran consumo de tokens, pero para fines de la practica creo que es correcto, aún así buscaré mejores formas de realizarlo.
